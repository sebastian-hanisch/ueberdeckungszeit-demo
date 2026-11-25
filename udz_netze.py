"""Netze: einfach, ungerichtet, mit Knotennamen und Koordinaten für die Karte (ohne Streamlit, nur numpy).

Grundlage ist der gemeinsame Baustein `trz_netze` der Demo „Trefferzeit“ (kopiert und erweitert): `Netz`, `netz`, Adjazenz, Handnetz, Gitterhallen mit beiden Türregeln,
Saal mit Stichgang, Weg. Neu in dieser Demo: Weg a–m–b, Kreis, Stern, vollständiger Saal, „zwei Hallen mit Flurknoten“, „zwei Säle mit Flurknoten“ (Hantel nach
Alon u. a.), Barbell mit langem Weg.

Gitterhallen: zwei Gitter a×a (Vierernachbarschaft) nebeneinander; eine Tür verbindet die rechte Spalte der linken Halle mit der linken Spalte der rechten in
derselben Zeile. Eine Tür liegt in Zeile a // 2. **Eine Tür mehr** (Ergänzung): die vorhandene bleibt, eine neue kommt in eine wählbare Zeile r.
"""

from dataclasses import dataclass

import numpy as np


@dataclass(frozen=True)
class Netz:
    name: str
    n: int
    kanten: tuple          # sortierte Paare (u, v) mit u < v
    knoten: tuple          # Name je Knoten
    pos: tuple             # (x, y) je Knoten, nur für die Karte


def netz(name: str, n: int, kanten, knoten=None, pos=None) -> Netz:
    """Netz aus einer Kantenliste; Schleifen, Doppelkanten und Knoten außerhalb 0 … n−1 werden abgewiesen."""
    paare = []
    for u, v in kanten:
        if u == v or not (0 <= u < n and 0 <= v < n):
            raise ValueError(f"ungültige Kante ({u}, {v}) bei {n} Knoten")
        paare.append((int(min(u, v)), int(max(u, v))))
    if len(set(paare)) != len(paare):
        raise ValueError("doppelte Kante")
    knoten = tuple(str(i) for i in range(n)) if knoten is None else tuple(knoten)
    if pos is None:
        winkel = 2 * np.pi * np.arange(n) / max(n, 1)
        pos = tuple((float(np.cos(w)), float(np.sin(w))) for w in winkel)
    return Netz(name, n, tuple(sorted(paare)), knoten, tuple(pos))


def adjazenz(g: Netz) -> np.ndarray:
    A = np.zeros((g.n, g.n))
    if g.kanten:
        k = np.array(g.kanten)
        A[k[:, 0], k[:, 1]] = 1.0
        A[k[:, 1], k[:, 0]] = 1.0
    return A


def grade(g: Netz) -> np.ndarray:
    d = np.zeros(g.n, dtype=np.int64)
    for u, v in g.kanten:
        d[u] += 1
        d[v] += 1
    return d


def nachbarn(g: Netz) -> list:
    """Sortierte Nachbarlisten (die Reihenfolge legt fest, welche Ziehung welchen Schritt bedeutet)."""
    nb = [[] for _ in range(g.n)]
    for u, v in g.kanten:
        nb[u].append(v)
        nb[v].append(u)
    return [sorted(x) for x in nb]


def abstaende(g: Netz, s: int) -> np.ndarray:
    """Kürzeste Entfernung (Zahl der Schritte) von s zu jedem Knoten, −1 = nicht erreichbar (Breitensuche)."""
    nb = nachbarn(g)
    d = np.full(g.n, -1, dtype=np.int64)
    d[s] = 0
    rand = [s]
    while rand:
        neu = []
        for u in rand:
            for w in nb[u]:
                if d[w] < 0:
                    d[w] = d[u] + 1
                    neu.append(w)
        rand = neu
    return d


def ist_zusammenhaengend(g: Netz) -> bool:
    if g.n == 0:
        return False
    return bool((abstaende(g, 0) >= 0).all())


def exzentrizitaet(g: Netz, s: int) -> int:
    """Entfernung vom Start s zum fernsten Knoten."""
    return int(abstaende(g, s).max())


def hat_kante(g: Netz, u: int, v: int) -> bool:
    return (min(u, v), max(u, v)) in g.kanten


def mit_kante(g: Netz, u: int, v: int) -> Netz:
    """Dasselbe Netz mit der neuen Kante u–v (nur zwischen zwei verschiedenen, noch nicht verbundenen Knoten)."""
    if u == v or hat_kante(g, u, v):
        raise ValueError("neue Kante nur zwischen zwei verschiedenen, bisher nicht verbundenen Knoten")
    return netz(g.name, g.n, list(g.kanten) + [(u, v)], g.knoten, g.pos)


def fehlende_kanten(g: Netz) -> list:
    vorhanden = set(g.kanten)
    return [(u, v) for u in range(g.n) for v in range(u + 1, g.n) if (u, v) not in vorhanden]


# ----------------------------------------------------------------------------------------------------------------------------------
# Handnetze
# ----------------------------------------------------------------------------------------------------------------------------------

HANDNETZ_POS = ((0.0, 1.4), (0.0, 0.0), (1.2, 0.7), (2.8, 0.7), (4.0, 0.0), (4.0, 1.4))


def handnetz(tueren: int = 1) -> Netz:
    """Dreiecke {0,1,2} und {3,4,5}; Tür 2–3, bei zwei Türen zusätzlich 5–0."""
    if tueren not in (1, 2):
        raise ValueError("Handnetz mit einer oder zwei Türen")
    kanten = [(0, 1), (1, 2), (0, 2), (3, 4), (4, 5), (3, 5), (2, 3)]
    if tueren == 2:
        kanten.append((0, 5))
    return netz("Handnetz zwei Hallen", 6, kanten, pos=HANDNETZ_POS)


def flurnetz() -> Netz:
    """Zwei Dreiecke {0,1,2} und {3,4,5}, verbunden nur über den Flurknoten 6 (Kanten 2–6 und 6–3, keine Tür 2–3)."""
    kanten = [(0, 1), (1, 2), (0, 2), (3, 4), (4, 5), (3, 5), (2, 6), (3, 6)]
    pos = ((0.0, 1.4), (0.0, 0.0), (1.2, 0.7), (3.6, 0.7), (4.8, 0.0), (4.8, 1.4), (2.4, 0.7))
    return netz("Zwei Hallen mit Flurknoten", 7, kanten, pos=pos)


def weg_amb() -> Netz:
    """Weg a–m–b."""
    return netz("Weg a–m–b", 3, [(0, 1), (1, 2)], ("a", "m", "b"), ((0.0, 0.0), (1.0, 0.0), (2.0, 0.0)))


def vierkreis() -> Netz:
    return netz("4-Kreis", 4, [(0, 1), (1, 2), (2, 3), (0, 3)], pos=((0.0, 1.0), (1.0, 1.0), (1.0, 0.0), (0.0, 0.0)))


# ----------------------------------------------------------------------------------------------------------------------------------
# Gitterhallen
# ----------------------------------------------------------------------------------------------------------------------------------

def hallenknoten(a: int, halle: int, zeile: int, spalte: int) -> int:
    """Knotennummer in den Gitterhallen: erst die linke Halle zeilenweise, dann die rechte."""
    if not (halle in (0, 1) and 0 <= zeile < a and 0 <= spalte < a):
        raise ValueError("Platz außerhalb der Halle")
    return halle * a * a + zeile * a + spalte


def gitterhallen(a: int, zeilen) -> Netz:
    """Zwei Gitter a×a, je eine Tür in jeder Zeile aus `zeilen`."""
    if a < 2:
        raise ValueError("a mindestens 2")
    zeilen = list(zeilen)
    if len(set(zeilen)) != len(zeilen) or not zeilen:
        raise ValueError("mindestens eine Tür, jede Zeile höchstens einmal")
    kanten, namen, pos = [], [], []
    for h, buchstabe in enumerate("LR"):
        for z in range(a):
            for s in range(a):
                u = hallenknoten(a, h, z, s)
                if z + 1 < a:
                    kanten.append((u, hallenknoten(a, h, z + 1, s)))
                if s + 1 < a:
                    kanten.append((u, hallenknoten(a, h, z, s + 1)))
                namen.append(f"{buchstabe}({z},{s})")
                pos.append((float(s + h * (a + 1)), float(a - 1 - z)))
    kanten += [(hallenknoten(a, 0, z, a - 1), hallenknoten(a, 1, z, 0)) for z in zeilen]
    return netz(f"Zwei Hallen {a}×{a}", 2 * a * a, kanten, namen, pos)


def zwei_hallen(a: int) -> Netz:
    """Zwei Hallen mit einer Tür in Zeile a // 2."""
    return gitterhallen(a, [a // 2])


def eine_tuer_mehr(a: int, r: int) -> Netz:
    """Ergänzung: die vorhandene Tür (Zeile a // 2) bleibt, die neue kommt in Zeile r ≠ a // 2."""
    if r == a // 2:
        raise ValueError("die neue Tür braucht eine andere Zeile als die vorhandene")
    return gitterhallen(a, [a // 2, r])


def alle_tueren(a: int) -> Netz:
    """Zwei Hallen mit einer Tür in jeder Zeile (die vorhandene eingeschlossen)."""
    return gitterhallen(a, list(range(a)))


def tuerknoten(a: int) -> int:
    """Platz der linken Halle an der Tür in Zeile a // 2."""
    return hallenknoten(a, 0, a // 2, a - 1)


def ferne_ecke(a: int) -> int:
    """Ecke L(0,0): in der linken Halle am weitesten von der Tür."""
    return 0


# ----------------------------------------------------------------------------------------------------------------------------------
# Kontrastnetze
# ----------------------------------------------------------------------------------------------------------------------------------

def gitter(a: int) -> Netz:
    """Ein einzelnes Gitter a×a."""
    kanten, namen, pos = [], [], []
    for z in range(a):
        for s in range(a):
            u = z * a + s
            if z + 1 < a:
                kanten.append((u, u + a))
            if s + 1 < a:
                kanten.append((u, u + 1))
            namen.append(f"({z},{s})")
            pos.append((float(s), float(a - 1 - z)))
    return netz(f"Gitter {a}×{a}", a * a, kanten, namen, pos)


def saal_mit_stichgang(saal: int = 9, gang: int = 5) -> Netz:
    """Vollständiger Saal mit `saal` Plätzen (jeder mit jedem verbunden), am letzten Saalplatz ein Gang mit `gang` Plätzen (Lutscher-Netz, lollipop)."""
    if saal < 2 or gang < 1:
        raise ValueError("Saal mit mindestens 2, Gang mit mindestens 1 Platz")
    kanten = [(i, j) for i in range(saal) for j in range(i + 1, saal)]
    kanten += [(i, i + 1) for i in range(saal - 1, saal + gang - 1)]
    namen = [f"S{i}" for i in range(saal)] + [f"G{i + 1}" for i in range(gang)]
    radius = 2.0
    winkel = [2 * np.pi * (i + 1) / saal for i in range(saal)]       # der letzte Saalplatz liegt rechts, am Gang
    pos = [(float(radius * np.cos(w)), float(radius * np.sin(w))) for w in winkel]
    pos += [(radius + 0.9 * (i + 1), 0.0) for i in range(gang)]
    return netz(f"Saal mit Stichgang {saal} + {gang}", saal + gang, kanten, namen, pos)


def saal(n: int) -> Netz:
    """Vollständiger Saal: jeder Platz mit jedem verbunden."""
    return netz(f"Vollständiger Saal {n}", n, [(i, j) for i in range(n) for j in range(i + 1, n)])


def stern(n: int) -> Netz:
    """Stern: Platz 0 in der Mitte, n − 1 Blätter."""
    winkel = [2 * np.pi * i / (n - 1) for i in range(n - 1)]
    pos = [(0.0, 0.0)] + [(float(np.cos(w)), float(np.sin(w))) for w in winkel]
    return netz(f"Stern {n}", n, [(0, i) for i in range(1, n)], pos=pos)


def kreis(n: int) -> Netz:
    if n < 3:
        raise ValueError("ein Kreis braucht mindestens 3 Knoten")
    winkel = [np.pi / 2 - 2 * np.pi * i / n for i in range(n)]
    return netz(f"Kreis {n}", n, [(i, i + 1) for i in range(n - 1)] + [(0, n - 1)], pos=[(float(np.cos(w)), float(np.sin(w))) for w in winkel])


def weg(n: int) -> Netz:
    """Weg (Pfad) mit n Knoten."""
    return netz(f"Weg {n}", n, [(i, i + 1) for i in range(n - 1)], pos=[(float(i), 0.0) for i in range(n)])


def _saal_auf_kreis(m: int, mitte_x: float, radius: float, ankerwinkel: float):
    """Positionen eines Saals auf einem Kreis; der letzte Platz (Anker) liegt im Winkel `ankerwinkel`."""
    return [(float(mitte_x + radius * np.cos(ankerwinkel + 2 * np.pi * (i + 1) / m)), float(radius * np.sin(ankerwinkel + 2 * np.pi * (i + 1) / m))) for i in range(m)]


def saele_mit_flurknoten(n: int) -> Netz:
    """„Zwei Säle mit Flurknoten“ (Hantel nach Alon u. a.): zwei vollständige Säle mit je (n−1)/2 Plätzen, verbunden über einen Weg der Länge 2.

    Nummern: Saal A = 0 … m−1 (Anschlussplatz m−1), Flurmitte = m, Saal B = m+1 … 2m (Anschlussplatz m+1)."""
    if n < 5 or n % 2 == 0:
        raise ValueError("n ungerade und mindestens 5")
    m = (n - 1) // 2
    kanten = [(i, j) for i in range(m) for j in range(i + 1, m)]
    kanten += [(m + 1 + i, m + 1 + j) for i in range(m) for j in range(i + 1, m)]
    kanten += [(m - 1, m), (m, m + 1)]
    namen = [f"A{i}" for i in range(m - 1)] + ["A·", "F"] + ["B·"] + [f"B{i}" for i in range(m - 1)]
    links = _saal_auf_kreis(m, -3.2, 1.8, 0.0)
    rechts = _saal_auf_kreis(m, 3.2, 1.8, np.pi)
    rechts = [rechts[-1]] + rechts[:-1]                              # Anker von B ist sein erster Platz
    pos = links + [(0.0, 0.0)] + rechts
    return netz(f"Zwei Säle mit Flurknoten {n}", n, kanten, namen, pos)


def barbell(saal_groesse: int = 48, weg_laenge: int = 32) -> Netz:
    """Zwei vollständige Säle, dazwischen ein langer Weg mit `weg_laenge` Plätzen (Barbell).

    Nummern: Saal A = 0 … s−1 (Anschluss s−1), Weg = s … s+w−1, Saal B = s+w … 2s+w−1 (Anschluss s+w)."""
    s, w = saal_groesse, weg_laenge
    kanten = [(i, j) for i in range(s) for j in range(i + 1, s)]
    kanten += [(s + w + i, s + w + j) for i in range(s) for j in range(i + 1, s)]
    kanten += [(i, i + 1) for i in range(s - 1, s + w)]
    return netz(f"Barbell {s}/{w}/{s}", 2 * s + w, kanten)


def barbell_mitte(saal_groesse: int = 48, weg_laenge: int = 32) -> int:
    """Mittlerer Platz des Wegs (bei gerader Weglänge der linke der beiden)."""
    return saal_groesse + (weg_laenge - 1) // 2
