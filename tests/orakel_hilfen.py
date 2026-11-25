"""Unabhängige Rechenwege für die Orakel-Tests: eigene Gauß-Elimination in Brüchen, Ein-/Ausschluss mit einem Gleichungssystem je gemiedener Menge,
Zustandsraum mit Phase, Ein-/Ausschluss über Symmetrieklassen auf den Sälen mit Flurknoten. Nichts hiervon benutzt udz_exakt oder udz_hantel."""

import math
from fractions import Fraction as F
from itertools import combinations, product


def zufallsnetz(seed: int, nmin: int = 3, nmax: int = 6, extra: float = 0.35):
    """Zusammenhängendes Zufallsnetz (zufälliger Baum plus zusätzliche Kanten) mit eigenem, festem Zufall."""
    from udz_rng import SplitMix64

    import udz_netze as N

    rng = SplitMix64(7_000 + seed)
    n = nmin + rng.below(nmax - nmin + 1)
    kanten = {(rng.below(v), v) for v in range(1, n)}
    for u in range(n):
        for v in range(u + 1, n):
            if rng.random() < extra:
                kanten.add((u, v))
    return N.netz(f"Zufall {seed}", n, sorted(kanten))


def nachbarlisten(n, kanten):
    nb = [set() for _ in range(n)]
    for u, v in kanten:
        nb[u].add(v)
        nb[v].add(u)
    return [sorted(x) for x in nb]


def loese(M, b):
    """Gauß-Jordan (Brüche oder Gleitkomma mit Fraction-Eingaben)."""
    n = len(b)
    M = [list(r) + [x] for r, x in zip(M, b)]
    for c in range(n):
        p = next(r for r in range(c, n) if M[r][c] != 0)
        M[c], M[p] = M[p], M[c]
        for r in range(n):
            if r != c and M[r][c] != 0:
                f = M[r][c] / M[c][c]
                M[r] = [x - f * y if y else x for x, y in zip(M[r], M[c])]
    return [M[i][n] / M[i][i] for i in range(n)]


def einausschluss_bruch(nb, k=1):
    """E[T_k] je Start in Brüchen: Summe über A != leer von (-1)^(|A|+1) * E[erste Runde, in der einer der k Läufer A trifft]; je Menge ein System."""
    n = len(nb)
    tot = [F(0)] * n
    for r in range(1, n + 1):
        for A in combinations(range(n), r):
            A = set(A)
            frei = [u for u in range(n) if u not in A]
            if not frei:
                continue
            zust = list(product(frei, repeat=k))
            ix = {z: i for i, z in enumerate(zust)}
            M = [[F(int(i == j)) for j in range(len(zust))] for i in range(len(zust))]
            for z, i in ix.items():
                for ziel in product(*(nb[o] for o in z)):
                    if ziel in ix:
                        p = F(1)
                        for o in z:
                            p /= len(nb[o])
                        M[i][ix[ziel]] -= p
            h = loese(M, [F(1)] * len(zust))
            for s in frei:
                tot[s] += (-1) ** (r + 1) * h[ix[(s,) * k]]
    return tot


def ruecksprung_zustandsraum(nb, s, tau):
    """Erwartete Schritte mit festem Rücksprung aus der Kette über (besuchte Menge, Ort, Schritt im Abschnitt) in Brüchen; None, wenn nie fertig."""
    voll = (1 << len(nb)) - 1
    start = (1 << s, s, 0)
    ix, liste = {start: 0}, [start]
    uebergaenge = []
    i = 0
    while i < len(liste):
        S, u, r = liste[i]
        z = []
        for w in nb[u]:
            T = S | (1 << w)
            if T == voll:
                continue
            ziel = (T, w, r + 1) if r + 1 < tau else (T, s, 0)
            if ziel not in ix:
                ix[ziel] = len(liste)
                liste.append(ziel)
            z.append((ix[ziel], F(1, len(nb[u]))))
        uebergaenge.append(z)
        i += 1
    # dünn lösen: Gleichung x_i = 1 + Summe p x_j, iterativ mit exakter Elimination wäre teuer, also dicht in Gleitkomma
    import numpy as np

    M = np.eye(len(liste))
    for i, z in enumerate(uebergaenge):
        for j, p in z:
            M[i, j] -= float(p)
    try:
        x = np.linalg.solve(M, np.ones(len(liste)))
    except np.linalg.LinAlgError:
        return None
    if not np.isfinite(x[0]) or x[0] <= 0 or x[0] > 1e12:
        return None
    return float(x[0])


def saele_einausschluss(n: int, typ: str):
    """C_1 auf „zwei Säle mit Flurknoten“ (n Plätze) exakt in Brüchen: Ein-/Ausschluss über Symmetrieklassen gemiedener Mengen.

    Eine Menge A ist durch (Flur in A?, Anschluss A?, Anschluss B?, j1 = Zahl der Innenplätze aus Saal A, j2 = aus Saal B) bis auf Umbenennen bestimmt;
    je Klasse ein Gleichungssystem mit höchstens 5 Unbekannten (freie Typen F, a1, a2, i1, i2)."""
    m = (n - 1) // 2
    r = m - 1                                                  # Innenplätze je Saal
    total = F(0)
    for fA, a1, a2 in product((0, 1), repeat=3):
        for j1 in range(r + 1):
            for j2 in range(r + 1):
                groesse = fA + a1 + a2 + j1 + j2
                if groesse == 0:
                    continue
                frei = [t for t, da in (("F", not fA), ("a1", not a1), ("a2", not a2), ("i1", j1 < r), ("i2", j2 < r)) if da]
                ix = {t: i for i, t in enumerate(frei)}
                M = [[F(int(i == j)) for j in range(len(frei))] for i in range(len(frei))]

                def zu(zeile, ziel, p):
                    if ziel in ix and p:
                        M[zeile][ix[ziel]] -= p

                for t, i in ix.items():
                    if t == "F":
                        zu(i, "a1", F(1, 2))
                        zu(i, "a2", F(1, 2))
                    elif t in ("a1", "a2"):
                        s = t[1]
                        j = j1 if s == "1" else j2
                        zu(i, "F", F(1, m))
                        zu(i, "i" + s, F(r - j, m))
                    else:
                        s = t[1]
                        j = j1 if s == "1" else j2
                        zu(i, "a" + s, F(1, r))
                        zu(i, t, F(r - 1 - j, r))                 # andere freie Innenplätze desselben Saals
                h = loese(M, [F(1)] * len(frei)) if frei else []
                # Zahl der Mengen dieser Klasse, die den Startplatz nicht enthalten (sonst ist die Trefferzeit 0)
                if typ == "F":
                    if fA:
                        continue
                    anzahl, zustand = math.comb(r, j1) * math.comb(r, j2), "F"
                elif typ == "a":
                    if a1:
                        continue
                    anzahl, zustand = math.comb(r, j1) * math.comb(r, j2), "a1"
                else:
                    if j1 >= r:
                        continue
                    anzahl, zustand = math.comb(r - 1, j1) * math.comb(r, j2), "i1"
                total += (-1) ** (groesse + 1) * anzahl * h[ix[zustand]]
    return total
