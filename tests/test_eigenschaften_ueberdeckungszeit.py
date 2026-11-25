"""Eigenschaftstests (je 20 bis 50 Netze, fester Zufalls-Seed): nur belegte Aussagen. Nicht geprüft werden „neue Verbindung verkürzt“, „S_k ≤ k“ und
„Rücksprung höchstens so teuer wie k Läufer“: alle drei sind falsch."""

import numpy as np
import pytest

import udz_exakt as X
import udz_matthews as MT
import udz_netze as N
import udz_plan as P
import udz_trefferzeit as T
from orakel_hilfen import zufallsnetz

NETZE = [zufallsnetz(2000 + i, 3, 8) for i in range(30)]


@pytest.mark.parametrize("g", NETZE[:30], ids=lambda g: g.name)
def test_matthews_und_mengenschranke_halten(g):
    t = X.zustandsraum(g).max()
    k = MT.klammer(T.treffer_matrix(g))
    wert, _ = MT.mengenschranke(T.treffer_matrix(g))
    assert k["unten"] <= t * (1 + 1e-9) and t <= k["oben"] * (1 + 1e-9)
    assert k["unten"] <= wert * (1 + 1e-9) <= t * (1 + 1e-8)


@pytest.mark.parametrize("g", NETZE, ids=lambda g: g.name)
def test_schranke_nach_aleliunas_u_a_von_jedem_start(g):
    assert (X.zustandsraum(g) <= 2 * len(g.kanten) * (g.n - 1) + 1e-9).all()


@pytest.mark.parametrize("g", NETZE[:20], ids=lambda g: g.name)
def test_mehr_laeufer_brauchen_nie_mehr_runden_und_zusammen_mindestens_n_minus_1_schritte(g):
    r = X.reihe(g, [1, 2, 3, 4, 8])
    ks = [1, 2, 3, 4, 8]
    for a, b in zip(ks, ks[1:]):
        assert (r[b] <= r[a] + 1e-8).all()
    for k in ks:
        assert (k * r[k] >= g.n - 1 - 1e-8).all()


@pytest.mark.parametrize("g", NETZE[:20], ids=lambda g: g.name)
def test_umnummerieren_aendert_nichts(g):
    perm = np.argsort([(i * 7919 + 13) % 101 for i in range(g.n)], kind="stable")
    neu = N.netz("p", g.n, [(int(perm[u]), int(perm[v])) for u, v in g.kanten])
    alt, jetzt = X.zustandsraum(g), X.zustandsraum(neu)
    assert jetzt[perm] == pytest.approx(alt, rel=1e-10)


@pytest.mark.parametrize("g", NETZE[:20], ids=lambda g: g.name)
def test_traege_irrfahrt_verdoppelt_die_zeit(g):
    """Eigener Zustandsraum für die träge Kette (mit ½ stehen bleiben) auf kleinem Netz, gegen das Doppelte der Rechnung der Demo."""
    if g.n > 6:
        g = zufallsnetz(2100 + g.n, 3, 5)
    nb = N.nachbarn(g)
    voll = (1 << g.n) - 1
    E = {}
    for S in sorted(range(1, voll + 1), key=lambda m: -bin(m).count("1")):
        orte = [u for u in range(g.n) if S >> u & 1]
        if S == voll:
            for u in orte:
                E[S, u] = 0.0
            continue
        ix = {u: i for i, u in enumerate(orte)}
        M, b = np.eye(len(orte)), np.ones(len(orte))
        for u in orte:
            M[ix[u], ix[u]] -= 0.5
            for w in nb[u]:
                p = 0.5 / len(nb[u])
                if S >> w & 1:
                    M[ix[u], ix[w]] -= p
                else:
                    b[ix[u]] += p * E.get((S | 1 << w, w), np.nan)
        x = np.linalg.solve(M, b)
        for u in orte:
            E[S, u] = x[ix[u]]
    assert [E[1 << s, s] for s in range(g.n)] == pytest.approx(2 * X.zustandsraum(g), rel=1e-9)


@pytest.mark.parametrize("i", range(30))
def test_kein_karten_plan_unter_der_unteren_schranke(i):
    g = zufallsnetz(2200 + i, 3, 20)
    s = i % g.n
    for k, plan in P.plane(g, s, [1, 2, 3, 5, 40]).items():
        assert plan["runden"] >= plan["unten"] >= max(N.exzentrizitaet(g, s), 0)
        assert plan["runden"] <= 2 * len(g.kanten) + g.n
