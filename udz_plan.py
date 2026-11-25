"""Gegner mit Karte: k abgesprochene Läufer ab demselben Start (ohne Streamlit, nur numpy). Braucht `udz_netze`.

Ein **Plan** gibt jedem Läufer einen Weg auf dem Netz (jede Runde jeder Läufer ein Schritt, Stehenbleiben ist erlaubt). Gesucht: möglichst wenige Runden, bis jeder
Platz von mindestens einem Läufer besucht ist.

Verfahren (liefert eine obere Schranke, also einen gültigen, aber nicht bewiesen kürzesten Plan):
1. Reihenfolge aller Plätze ab dem Start nach der Regel „nächster Nachbar“ (kleinste Entfernung, bei Gleichstand kleinste Nummer),
2. 2-opt auf diesem offenen Weg (Start fest) mit den kürzesten Entfernungen im Netz,
3. Zerlegung in höchstens k zusammenhängende Stücke mit kleinstmöglicher Rundenzahl; ein Läufer geht vom Start auf kürzestem Weg zum näheren Ende seines Stücks und
   läuft es ab (Zerlegung optimal für die feste Reihenfolge: Binärsuche über die Rundenzahl und gierige Zuteilung).

`pruefe_plan` läuft den fertigen Plan nach. Untere Schranke für jeden Plan: max(Entfernung zum fernsten Platz, ⌈(n−1)/k⌉). `kuerzester_plan_exakt` sucht auf sehr
kleinen Netzen den kürzesten Plan durch Breitensuche über (besuchte Menge, Orte).
"""

from collections import deque
from itertools import product

import numpy as np

import udz_netze as N


def entfernungen(g: N.Netz) -> np.ndarray:
    return np.stack([N.abstaende(g, s) for s in range(g.n)])


def naechster_nachbar(D: np.ndarray, s: int) -> list:
    n = len(D)
    frei = np.ones(n, dtype=bool)
    frei[s] = False
    weg = [int(s)]
    for _ in range(n - 1):
        d = np.where(frei, D[weg[-1]], np.iinfo(np.int64).max)
        w = int(np.argmin(d))
        weg.append(w)
        frei[w] = False
    return weg


def zwei_opt(D: np.ndarray, weg: list) -> list:
    """2-opt auf einem offenen Weg mit festem ersten Platz: so lange Teilstücke umdrehen, wie der Weg kürzer wird."""
    w = np.array(weg, dtype=np.int64)
    n = len(w)
    besser = True
    while besser:
        besser = False
        for i in range(1, n - 1):
            a, b = w[i - 1], w[i]
            js = np.arange(i + 1, n)
            c = w[js]
            gewinn = D[a, c] - D[a, b]
            mit_nachfolger = js < n - 1
            d = w[np.minimum(js + 1, n - 1)]
            gewinn = gewinn + np.where(mit_nachfolger, D[b, d] - D[c, d], 0)
            j = int(np.argmin(gewinn))
            if gewinn[j] < 0:
                ende = int(js[j])
                w[i: ende + 1] = w[i: ende + 1][::-1].copy()
                besser = True
    return [int(x) for x in w]


def weglaenge(D: np.ndarray, weg: list) -> int:
    return int(sum(D[weg[i], weg[i + 1]] for i in range(len(weg) - 1)))


def _stuecke(D: np.ndarray, s: int, weg: list, runden: int):
    """Gierige Zerlegung von weg[1:] in Stücke, die jeweils in `runden` Runden zu schaffen sind; None, wenn ein einzelner Platz zu weit ist."""
    rest = weg[1:]
    stuecke = []
    i = 0
    while i < len(rest):
        if D[s, rest[i]] > runden:
            return None
        laenge, j = 0, i
        while j + 1 < len(rest):
            neu = laenge + D[rest[j], rest[j + 1]]
            if neu + min(D[s, rest[i]], D[s, rest[j + 1]]) > runden:
                break
            laenge, j = neu, j + 1
        stuecke.append(rest[i: j + 1])
        i = j + 1
    return stuecke


def zerlege(D: np.ndarray, s: int, weg: list, k: int):
    """(Rundenzahl, Stücke): kleinste Rundenzahl, mit der höchstens k Stücke genügen."""
    unten, oben = 0, int(weglaenge(D, weg) + D[s].max())
    while unten < oben:
        mitte = (unten + oben) // 2
        stuecke = _stuecke(D, s, weg, mitte)
        if stuecke is not None and len(stuecke) <= k:
            oben = mitte
        else:
            unten = mitte + 1
    return unten, _stuecke(D, s, weg, unten)


def _kuerzester_weg(nb: list, D: np.ndarray, u: int, v: int) -> list:
    pfad = [u]
    while pfad[-1] != v:
        pfad.append(min(w for w in nb[pfad[-1]] if D[w, v] == D[pfad[-1], v] - 1))
    return pfad


def laeufer_wege(g: N.Netz, D: np.ndarray, s: int, stuecke: list, k: int) -> list:
    """Je Läufer die Folge der Plätze (beginnt in s); Läufer ohne Stück bleiben stehen."""
    nb = N.nachbarn(g)
    wege = []
    for stueck in stuecke:
        folge = stueck if D[s, stueck[0]] <= D[s, stueck[-1]] else stueck[::-1]
        pfad = _kuerzester_weg(nb, D, s, folge[0])
        for x in folge[1:]:
            pfad += _kuerzester_weg(nb, D, pfad[-1], x)[1:]
        wege.append(pfad)
    wege += [[s] for _ in range(k - len(wege))]
    return wege


def pruefe_plan(g: N.Netz, s: int, wege: list, runden: int, k: int) -> bool:
    """Läuft den Plan nach: höchstens k Läufer, jeder startet in s, jeder Schritt entlang einer Kante (oder Stehenbleiben), höchstens `runden` Schritte, alles besucht."""
    if len(wege) > k or any(not w or w[0] != s or len(w) - 1 > runden for w in wege):
        return False
    kanten = set(g.kanten)
    for w in wege:
        for a, b in zip(w, w[1:]):
            if a != b and (min(a, b), max(a, b)) not in kanten:
                return False
    return len({x for w in wege for x in w}) == g.n


def untere_schranke(g: N.Netz, s: int, k: int) -> int:
    return int(max(N.exzentrizitaet(g, s), -(-(g.n - 1) // k)))


def plane(g: N.Netz, s: int, ks) -> dict:
    """{k: {'runden', 'unten', 'wege'}} für jede Läuferzahl k aus `ks`; jeder Plan ist nachgelaufen."""
    D = entfernungen(g)
    weg = zwei_opt(D, naechster_nachbar(D, s))
    ergebnis = {}
    for k in ks:
        runden, stuecke = zerlege(D, s, weg, k)
        wege = laeufer_wege(g, D, s, stuecke, k)
        if not pruefe_plan(g, s, wege, runden, k):
            raise AssertionError("Plan besteht die Nachlauf-Prüfung nicht")
        ergebnis[int(k)] = {"runden": int(runden), "unten": untere_schranke(g, s, k), "wege": wege}
    return ergebnis


def kuerzester_plan_exakt(g: N.Netz, s: int, k: int) -> int:
    """Kürzeste Rundenzahl durch Breitensuche über (besuchte Menge, Orte); nur für sehr kleine Netze und wenige Läufer."""
    if g.n > 8 or k > 3:
        raise ValueError("exakte Suche nur bis 8 Plätze und 3 Läufer")
    nb = N.nachbarn(g)
    voll = (1 << g.n) - 1
    start = (1 << s, (s,) * k)
    if start[0] == voll:
        return 0
    dist = {start: 0}
    q = deque([start])
    while q:
        S, orte = q.popleft()
        for ziel in product(*([o] + nb[o] for o in orte)):
            T = S
            for o in ziel:
                T |= 1 << o
            z = (T, tuple(sorted(ziel)))
            if z not in dist:
                dist[z] = dist[(S, orte)] + 1
                if T == voll:
                    return dist[z]
                q.append(z)
    raise ValueError("Netz nicht zusammenhängend")
