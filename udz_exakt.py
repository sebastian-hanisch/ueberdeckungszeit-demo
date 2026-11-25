"""Überdeckungszeit ohne Zufall auf kleinen Netzen (ohne Streamlit, nur numpy).

Alle Zeiten sind erwartete Zahlen der einfachen, nicht trägen Irrfahrt; der Startplatz zählt als besucht.

1. `zustandsraum` (ein Läufer, bis 18 Plätze): Zustand = (besuchte Menge, Ort). Die besuchte Menge wächst nur, also wird von großen zu kleinen Mengen gerechnet,
   je Menge ein lineares Gleichungssystem.
2. `reihe` (k Läufer, bis 15 Plätze):Ein-/Ausschluss über gemiedene Mengen. Für unabhängige Läufer ab demselben Start ist
   P(T_k > t) = Σ über nichtleere Mengen A: (−1)^(|A|+1) · q_A(t)^k, q_A(t) = Wahrscheinlichkeit, dass ein Läufer in t Schritten keinen Platz aus A besucht.
   E[T_k] = Σ über t ≥ 0 von P(T_k > t), abgebrochen, sobald der Rest vernachlässigbar ist.
3. `ruecksprung` (ein Läufer, fester Rücksprung alle tau Schritte, bis 15 Plätze): geschlossen
   E = Σ_A (−1)^(|A|+1) · (Σ_{r<tau} q_A(r)) / (1 − q_A(tau)).

Der unabhängige zweite Weg (je gemiedene Menge ein Gleichungssystem, in Brüchen bzw. Gleitkomma, und der Zustandsraum mit Phase) steht in den Orakel-Tests.
"""

import numpy as np

import udz_netze as N

MAX_ZUSTAND = 18
MAX_REIHE = 15
MAX_EINZEL_MEDIAN = 12


def uebergang(g: N.Netz) -> np.ndarray:
    A = N.adjazenz(g)
    return A / A.sum(axis=1, keepdims=True)


def _pruefe(g: N.Netz, grenze: int) -> None:
    if g.n < 1 or not N.ist_zusammenhaengend(g):
        raise ValueError("nur zusammenhängende Netze")
    if g.n > grenze:
        raise ValueError(f"exakt nur bis {grenze} Plätze")


def zustandsraum(g: N.Netz) -> np.ndarray:
    """E[Schritte, bis alle besucht sind] je Startplatz (ein Läufer)."""
    _pruefe(g, MAX_ZUSTAND)
    n = g.n
    if n == 1:
        return np.zeros(1)
    P = uebergang(g)
    E = np.zeros((1 << n, n))
    alle = np.arange(1 << n, dtype=np.int64)
    bits = ((alle[:, None] >> np.arange(n)) & 1).astype(bool)
    anzahl = bits.sum(axis=1)
    knoten = np.arange(n)
    for c in range(n - 1, 0, -1):
        mengen = alle[anzahl == c]
        m = len(mengen)
        drin = np.nonzero(bits[mengen])[1].reshape(m, c)                  # Plätze jeder Menge, aufsteigend
        neu = mengen[:, None] | (1 << knoten)
        werte = np.where(bits[mengen], 0.0, E[neu, knoten])               # E nach dem Besuch eines neuen Platzes w
        b = 1.0 + np.einsum("mcw,mw->mc", P[drin], werte)
        M = np.eye(c) - P[drin[:, :, None], drin[:, None, :]]
        x = np.linalg.solve(M, b[:, :, None])[:, :, 0]
        E[mengen[:, None], drin] = x
    return E[1 << knoten, knoten]


def _mengen(n: int):
    """Alle nichtleeren Mengen A als Bitmasken, ihr Frei-Feld (Plätze außerhalb A) und das Vorzeichen (−1)^(|A|+1)."""
    A = np.arange(1, 1 << n, dtype=np.int64)
    frei = ((A[:, None] >> np.arange(n)) & 1) == 0
    vz = np.where((n - frei.sum(axis=1)) % 2 == 1, 1.0, -1.0)
    return frei, vz


def reihe(g: N.Netz, ks, tol: float = 1e-10, max_schritte: int = 400_000) -> dict:
    """{k: E[Runden] je gemeinsamem Startplatz} für alle k aus `ks` (Ein-/Ausschluss als Reihe); der abgeschnittene Rest ist kleiner als `tol`."""
    _pruefe(g, MAX_REIHE)
    ks = sorted(set(int(k) for k in ks))
    if not ks or ks[0] < 1:
        raise ValueError("mindestens ein Läufer")
    if g.n == 1:
        return {k: np.zeros(1) for k in ks}
    frei, vz = _mengen(g.n)
    PT = uebergang(g).T
    q = frei.astype(float)
    summe = {k: np.zeros(g.n) for k in ks}
    maske = frei.astype(float)
    einzel = (1 << np.arange(g.n)) - 1                                    # Zeilen der einelementigen Mengen {v}
    vorher = []
    for t in range(max_schritte):
        potenz, aktuell = None, 0
        for k in ks:
            if k > aktuell:
                faktor = q if k - aktuell == 1 else q ** (k - aktuell)
                potenz = faktor.copy() if potenz is None else potenz * faktor
                aktuell = k
            summe[k] += vz @ potenz
        if t % 10 == 0:
            # Abbruch über eine Schranke ohne Auslöschung: P(noch nicht fertig) <= Summe über die einzelnen Plätze v von q_{v}(t) (ein Läufer genügt als Schranke)
            vorher.append(float(q[einzel].sum(axis=0).max()))
            if len(vorher) > 2 and vorher[-1] < 1e-6:
                lam = (vorher[-1] / vorher[-3]) ** (1 / 20)
                if lam < 1 and vorher[-1] / (1 - lam) < tol:
                    return summe
        q = (q @ PT) * maske
    raise RuntimeError("Reihe nicht konvergiert")


def median_runden(g: N.Netz, s: int, k: int) -> int:
    """Median der Rundenzahl: kleinstes t mit P(T_k <= t) >= 1/2 (Ein-/Ausschluss, ab Start s)."""
    _pruefe(g, MAX_EINZEL_MEDIAN)
    if g.n == 1:
        return 0
    frei, vz = _mengen(g.n)
    PT = uebergang(g).T
    q = frei.astype(float)
    maske = frei.astype(float)
    for t in range(100_000):
        if float(vz @ q[:, s] ** k) <= 0.5 + 1e-12:
            return t
        q = (q @ PT) * maske
    raise RuntimeError("Median nicht gefunden")


def ruecksprung(g: N.Netz, s: int, tau_max: int) -> list:
    """Erwartete Schritte eines Läufers mit festem Rücksprung zum Start s für tau = 1 … tau_max. Eintrag None: mit diesem tau wird nie alles besucht."""
    _pruefe(g, MAX_REIHE)
    if g.n == 1:
        return [0.0] * tau_max
    grenze = N.exzentrizitaet(g, s)
    frei, vz = _mengen(g.n)
    PT = uebergang(g).T
    q = frei.astype(float)
    maske = frei.astype(float)
    kum = np.zeros(len(vz))
    ergebnis = []
    for tau in range(1, tau_max + 1):
        kum += q[:, s]
        q = (q @ PT) * maske
        if tau < grenze:
            ergebnis.append(None)
            continue
        nenner = 1.0 - q[:, s]
        ergebnis.append(float(np.dot(vz, kum / nenner)))
    return ergebnis
