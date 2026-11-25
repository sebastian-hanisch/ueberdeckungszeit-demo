"""Simulation der einfachen Irrfahrt bis alle Plätze besucht sind, vektorisiert, mit SplitMix64 (ohne Streamlit, nur numpy). Braucht `udz_netze`.

`BlockZufall` stammt aus dem gemeinsamen Baustein `trz_irrfahrt_sim` der Demo „Trefferzeit“ und liefert exakt dieselbe Folge wie die Klasse `SplitMix64` in `udz_rng.py`
(Test: `tests/test_irrfahrt_sim.py`). Neu in dieser Demo: mehrere Läufer, fester Rücksprung, Verlauf eines einzelnen Laufs.

**Wahl des Nachbarn:** aus den oberen 32 Bit w des gezogenen u64 wird (w · Grad) >> 32 gebildet (Multiplizieren und Schieben, nur Ganzzahlen). Die Abweichung von
der Gleichverteilung ist höchstens Grad / 2^32. Gezogen wird nur ganzzahlig, die Läufe sind damit plattformgleich.

**Reihenfolge der Ziehungen:** in jeder Runde bekommt jeder Läufer jedes noch laufenden Laufs genau einen Wert: erst alle Läufer des ersten laufenden Laufs, dann
die des nächsten (aufsteigende Laufnummer). Der Nachbar ist der Eintrag mit dieser Nummer in der aufsteigend sortierten Nachbarliste.

**Zählweise:** In einer Runde geht jeder Läufer einen Schritt. Die Startplätze zählen als besucht. Beim festen Rücksprung alle tau Schritte steht der Läufer nach den
Schritten tau, 2·tau, … wieder auf dem Start; dieser Sprung zählt nicht als Schritt.
"""

import numpy as np

import udz_netze as N

GAMMA = np.uint64(0x9E3779B97F4A7C15)
_M1 = np.uint64(0xBF58476D1CE4E5B9)
_M2 = np.uint64(0x94D049BB133111EB)
_S30, _S27, _S31, _S32 = np.uint64(30), np.uint64(27), np.uint64(31), np.uint64(32)
MASK = (1 << 64) - 1


class BlockZufall:
    """SplitMix64 blockweise: `u64(m)` sind die nächsten m Werte der Folge."""

    def __init__(self, seed: int):
        self.seed = int(seed) & MASK
        self.gezogen = 0

    def u64(self, m: int) -> np.ndarray:
        z = np.arange(self.gezogen + 1, self.gezogen + m + 1, dtype=np.uint64)
        self.gezogen += m
        z *= GAMMA                                                    # uint64-Felder rechnen modulo 2^64
        z += np.uint64(self.seed)
        z ^= z >> _S30
        z *= _M1
        z ^= z >> _S27
        z *= _M2
        z ^= z >> _S31
        return z


def waehle(werte: np.ndarray, grad: np.ndarray) -> np.ndarray:
    """Nachbarnummer 0 … Grad−1 aus den oberen 32 Bit: (w · Grad) >> 32."""
    return ((werte >> _S32) * grad) >> _S32


def nachbar_tabelle(g: N.Netz):
    """(Tabelle n × Höchstgrad der sortierten Nachbarn, Grade als uint64)."""
    nb = N.nachbarn(g)
    grad = np.array([len(x) for x in nb], dtype=np.uint64)
    tabelle = np.zeros((g.n, max(1, int(grad.max(initial=0)))), dtype=np.int64)
    for u, liste in enumerate(nb):
        tabelle[u, : len(liste)] = liste
    return tabelle, grad


def _startfeld(g: N.Netz, start, k: int, laeufe: int) -> np.ndarray:
    """Startplätze als Feld (laeufe × k): ein gemeinsamer Platz oder ein vorgegebenes Feld."""
    if np.isscalar(start):
        feld = np.full((laeufe, k), int(start), dtype=np.int64)
    else:
        feld = np.array(start, dtype=np.int64).reshape(laeufe, k)
    if feld.size and (feld.min() < 0 or feld.max() >= g.n):
        raise ValueError("Startplatz außerhalb des Netzes")
    return feld


def simuliere_ueberdeckung(g: N.Netz, start, k: int, laeufe: int, seed: int, tau: int = None, max_runden: int = 20_000_000) -> np.ndarray:
    """Runden je Lauf, bis jeder Platz von mindestens einem der k Läufer besucht ist. −1 = nach `max_runden` Runden nicht fertig.

    start: gemeinsamer Startplatz (Zahl) oder Feld laeufe × k (dann ohne Rücksprung). tau: fester Rücksprung alle tau Schritte zum gemeinsamen Startplatz."""
    if not N.ist_zusammenhaengend(g):
        raise ValueError("Simulation nur auf zusammenhängenden Netzen")
    if k < 1 or laeufe < 0:
        raise ValueError("mindestens ein Läufer, Zahl der Läufe nicht negativ")
    if tau is not None:
        if not np.isscalar(start):
            raise ValueError("fester Rücksprung nur mit einem gemeinsamen Startplatz")
        if tau < N.exzentrizitaet(g, int(start)):
            raise ValueError("tau kleiner als die Entfernung zum fernsten Platz: dieser wird nie erreicht")
    feld = _startfeld(g, start, k, laeufe)
    runden = np.zeros(laeufe, dtype=np.int64)
    if laeufe == 0:
        return runden
    tabelle, grad = nachbar_tabelle(g)
    breite = tabelle.shape[1]
    flach = tabelle.ravel()
    n = g.n
    besucht = np.zeros(laeufe * n, dtype=bool)
    basis = np.arange(laeufe, dtype=np.int64) * n
    for j in range(k):
        besucht[basis + feld[:, j]] = True
    rest = n - besucht.reshape(laeufe, n).sum(axis=1, dtype=np.int64)
    lauf = np.flatnonzero(rest > 0)
    orte = np.ascontiguousarray(feld[lauf])
    basis = lauf * n
    rest = rest[lauf]
    rng = BlockZufall(seed)
    runde = 0
    while lauf.size and runde < max_runden:
        runde += 1
        hier = orte.ravel()
        wahl = waehle(rng.u64(hier.size), grad.take(hier)).view(np.int64)
        hier *= breite
        hier += wahl
        neu = flach.take(hier).reshape(orte.shape)
        for j in range(k):
            idx = basis + neu[:, j]
            frisch = ~besucht.take(idx)
            besucht[idx] = True
            rest -= frisch
        fertig = rest == 0
        if tau is not None and runde % tau == 0:
            neu[:] = int(start)
        orte = neu
        if fertig.any():
            runden[lauf[fertig]] = runde
            bleibt = ~fertig
            lauf, orte, basis, rest = lauf[bleibt], np.ascontiguousarray(orte[bleibt]), basis[bleibt], rest[bleibt]
    runden[lauf] = -1
    return runden


def zieh_stationaer(g: N.Netz, anzahl: int, seed: int) -> np.ndarray:
    """`anzahl` Plätze unabhängig nach π (Anteil je Platz proportional zur Nachbarzahl): ein zufälliges Kantenende, nur ganzzahlig."""
    enden = np.array([x for kante in g.kanten for x in kante], dtype=np.int64)
    wahl = waehle(BlockZufall(seed).u64(anzahl), np.full(anzahl, len(enden), dtype=np.uint64)).view(np.int64)
    return enden[wahl]


def verlauf(g: N.Netz, start: int, k: int, seed: int, max_runden: int = 300_000):
    """Ein einzelner Lauf, Runde für Runde: (orte (Runden+1) × k, erste_runde je Platz, −1 = nicht besucht; fertig)."""
    nb = N.nachbarn(g)
    erste = np.full(g.n, -1, dtype=np.int64)
    erste[start] = 0
    offen = g.n - 1
    rng = BlockZufall(seed)
    orte = [int(start)] * k
    spur = [list(orte)]
    block, i = [], 0
    runde = 0
    while offen and runde < max_runden:
        runde += 1
        if i + k > len(block):
            block = (rng.u64(4096 * k) >> _S32).tolist()
            i = 0
        for j in range(k):
            liste = nb[orte[j]]
            ziel = liste[(block[i] * len(liste)) >> 32]
            i += 1
            orte[j] = ziel
            if erste[ziel] < 0:
                erste[ziel] = runde
                offen -= 1
        spur.append(list(orte))
    return np.array(spur, dtype=np.int64), erste, offen == 0


def kennzahlen(runden: np.ndarray, k: int) -> dict:
    """Mittel, Standardfehler und Median der Runden eines Satzes von Läufen (alle fertig)."""
    if (runden < 0).any():
        raise ValueError("nicht alle Läufe fertig")
    n = len(runden)
    mittel = float(runden.mean())
    se = float(runden.std(ddof=1) / np.sqrt(n)) if n > 1 else 0.0
    return {"k": int(k), "laeufe": int(n), "runden": mittel, "se": se, "median": float(np.median(runden))}
