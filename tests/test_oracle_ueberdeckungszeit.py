"""Orakel-Tests: jede Kerngröße gegen einen unabhängigen Rechenweg (tests/orakel_hilfen.py: Brüche, je gemiedene Menge ein System; Zustandsraum mit Phase;
Symmetrieklassen; Aufzählung). Auswahl der Netze fest über den SplitMix64-Generator."""

from itertools import combinations

import pytest

import udz_exakt as X
import udz_hantel as H
import udz_irrfahrt_sim as S
import udz_matthews as MT
import udz_netze as N
import udz_plan as P
import udz_trefferzeit as T
from orakel_hilfen import einausschluss_bruch, nachbarlisten, ruecksprung_zustandsraum, saele_einausschluss, zufallsnetz


def nb_von(g):
    return nachbarlisten(g.n, g.kanten)


@pytest.mark.parametrize("seed", range(25))
def test_zustandsraum_und_reihe_stimmen_mit_ein_ausschluss_in_bruechen(seed):
    g = zufallsnetz(seed)
    erwartet = [float(x) for x in einausschluss_bruch(nb_von(g))]
    assert X.zustandsraum(g) == pytest.approx(erwartet, rel=1e-10)
    assert X.reihe(g, [1])[1] == pytest.approx(erwartet, rel=1e-8)


@pytest.mark.parametrize("seed", range(12))
def test_zwei_laeufer_reihe_stimmt_mit_bruechen(seed):
    g = zufallsnetz(100 + seed, 3, 5)
    erwartet = [float(x) for x in einausschluss_bruch(nb_von(g), 2)]
    assert X.reihe(g, [2])[2] == pytest.approx(erwartet, rel=1e-8)


@pytest.mark.parametrize("seed", range(15))
def test_fester_ruecksprung_formel_gegen_zustandsraum_mit_phase(seed):
    g = zufallsnetz(200 + seed, 3, 5)
    s = seed % g.n
    werte = X.ruecksprung(g, s, 9)
    for tau in range(1, 10):
        erwartet = ruecksprung_zustandsraum(nb_von(g), s, tau)
        if erwartet is None:
            assert werte[tau - 1] is None
        else:
            assert werte[tau - 1] == pytest.approx(erwartet, rel=1e-8)


@pytest.mark.parametrize("n", [9, 11])
def test_saele_zusammengefasste_kette_gegen_volle_aufzaehlung(n):
    g = N.saele_mit_flurknoten(n)
    voll = X.zustandsraum(g)
    w = H.ueberdeckung(n)
    for platz in range(n):
        assert w[H.typ_von(n, platz)] == pytest.approx(voll[platz], rel=1e-10)


@pytest.mark.parametrize("n", [9, 11, 13, 17, 33])
def test_saele_zusammengefasste_kette_gegen_symmetrieklassen_in_bruechen(n):
    w = H.ueberdeckung(n)
    for typ in ("F", "a", "i"):
        assert w[typ] == pytest.approx(float(saele_einausschluss(n, typ)), rel=1e-9)


def test_symmetrieklassen_sind_selbst_gegen_die_volle_mengensumme_geprueft():
    g = N.saele_mit_flurknoten(9)
    voll = einausschluss_bruch(nb_von(g))
    for typ, platz in (("F", 4), ("a", 3), ("i", 0)):
        assert saele_einausschluss(9, typ) == voll[platz]


@pytest.mark.parametrize("seed", range(10))
def test_trefferzeiten_und_matthews_gegen_zweiten_weg_und_mengenschranke_gegen_aufzaehlung(seed):
    g = zufallsnetz(300 + seed, 4, 8)
    H1, H2 = T.treffer_matrix(g), T.treffer_je_ziel(g)
    assert H1 == pytest.approx(H2, rel=1e-9)
    k = MT.klammer(H1)
    werte = [H2[u, v] for u in range(g.n) for v in range(g.n) if u != v]
    h = sum(1 / i for i in range(1, g.n))
    assert k["oben"] == pytest.approx(max(werte) * h) and k["unten"] == pytest.approx(min(werte) * h)
    beste = max(min(H2[u, v] for u in A for v in A if u != v) * sum(1 / i for i in range(1, r)) for r in range(2, g.n + 1) for A in combinations(range(g.n), r))
    wert, menge = MT.mengenschranke(H1)
    assert wert == pytest.approx(beste, rel=1e-9)
    assert min(H2[u, v] for u in menge for v in menge if u != v) * sum(1 / i for i in range(1, len(menge))) == pytest.approx(wert, rel=1e-9)


@pytest.mark.parametrize("seed", range(8))
def test_simulation_trifft_die_rechnung_ohne_zufall(seed):
    g = zufallsnetz(400 + seed, 4, 7)
    s, k = seed % g.n, 1 + seed % 3
    erwartet = float(X.reihe(g, [k])[k][s])
    z = S.kennzahlen(S.simuliere_ueberdeckung(g, s, k, 20000, 1234 + seed), k)
    assert abs(z["runden"] - erwartet) < 4 * z["se"] + 1e-9
    tau = N.exzentrizitaet(g, s) + 2
    exakt = X.ruecksprung(g, s, tau)[tau - 1]
    z = S.kennzahlen(S.simuliere_ueberdeckung(g, s, 1, 20000, 999 + seed, tau=tau), 1)
    assert abs(z["runden"] - exakt) < 4 * z["se"] + 1e-9


def test_simulation_trifft_die_zusammengefasste_kette_auf_den_saelen():
    g = N.saele_mit_flurknoten(33)
    w = H.ueberdeckung(33)
    for platz, typ in ((16, "F"), (0, "i"), (15, "a")):
        z = S.kennzahlen(S.simuliere_ueberdeckung(g, platz, 1, 8000, 77 + platz), 1)
        assert abs(z["runden"] - w[typ]) < 4 * z["se"]


def _naiv_simulation(g, starts, k, laeufe, seed, tau=None):
    """Schleifenfassung mit der Klasse SplitMix64 aus udz_rng: je Runde je laufender Lauf je Läufer ein Wert, aufsteigend."""
    from udz_rng import SplitMix64

    rng = SplitMix64(seed)
    nb = N.nachbarn(g)
    orte = [list(starts) for _ in range(laeufe)] if tau is not None or isinstance(starts[0], int) else [list(x) for x in starts]
    besucht = [set(o) for o in orte]
    runden = [0 if len(b) == g.n else None for b in besucht]
    r = 0
    while any(x is None for x in runden):
        r += 1
        for i in range(laeufe):
            if runden[i] is not None:
                continue
            for j in range(k):
                liste = nb[orte[i][j]]
                orte[i][j] = liste[((rng.next_u64() >> 32) * len(liste)) >> 32]
                besucht[i].add(orte[i][j])
            if len(besucht[i]) == g.n:
                runden[i] = r
            if tau is not None and r % tau == 0:
                orte[i] = list(starts)
    return runden


@pytest.mark.parametrize("seed", range(6))
def test_vektorisierte_simulation_ist_bitgleich_mit_der_schleife(seed):
    g = zufallsnetz(500 + seed, 4, 8)
    k = 1 + seed % 4
    s = seed % g.n
    assert list(S.simuliere_ueberdeckung(g, s, k, 60, 31 + seed)) == _naiv_simulation(g, [s] * k, k, 60, 31 + seed)
    tau = N.exzentrizitaet(g, s) + 1
    assert list(S.simuliere_ueberdeckung(g, s, 1, 40, 99 + seed, tau=tau)) == _naiv_simulation(g, [s], 1, 40, 99 + seed, tau=tau)


@pytest.mark.parametrize("seed", range(6))
def test_ein_gezeigter_lauf_ist_derselbe_wie_in_der_simulation(seed):
    g = zufallsnetz(600 + seed, 4, 8)
    k = 1 + seed % 3
    spur, erste, fertig = S.verlauf(g, 0, k, 5 + seed)
    assert fertig and len(spur) - 1 == S.simuliere_ueberdeckung(g, 0, k, 1, 5 + seed)[0]
    gesehen = {}
    for r, orte in enumerate(spur):
        for o in orte:
            gesehen.setdefault(int(o), r)
    assert [gesehen[i] for i in range(g.n)] == list(erste)


@pytest.mark.parametrize("seed", range(20))
def test_karten_plan_ist_gueltig_und_nie_besser_als_der_kuerzeste_aus_der_aufzaehlung(seed):
    g = zufallsnetz(700 + seed, 3, 7)
    for k in (1, 2, 3):
        plan = P.plane(g, 0, [k])[k]
        assert P.pruefe_plan(g, 0, plan["wege"], plan["runden"], k)
        exakt = P.kuerzester_plan_exakt(g, 0, k)
        assert plan["unten"] <= exakt <= plan["runden"]


def test_aufzaehlung_aller_wege_bestaetigt_die_exakte_plan_suche_auf_dem_handnetz():
    """Zweiter Weg zur Breitensuche: alle Wege (mit Stehenbleiben) einzeln aufzählen."""
    g = N.handnetz()
    nb = N.nachbarn(g)

    def mengen(s, L):
        menge = {(s, 1 << s)}
        for _ in range(L):
            menge = {(w, m | (1 << w)) for u, m in menge for w in [u] + nb[u]}
        return {m for _, m in menge}

    for s, k, L in ((0, 1, 5), (2, 1, 6), (2, 2, 3), (0, 2, 4)):
        for laenge, soll in ((L, True), (L - 1, False)):
            m = mengen(s, laenge)
            ok = (63 in m) if k == 1 else any(a | b == 63 for a in m for b in m)
            assert ok == soll
        assert P.kuerzester_plan_exakt(g, s, k) == L


def test_zerlegung_ist_fuer_die_reihenfolge_optimal_gegen_alle_schnitte():
    """Zerlegung in höchstens k Stücke: gegen alle möglichen Schnittstellen auf kleinen Netzen."""
    for seed in range(25):
        g = zufallsnetz(800 + seed, 4, 8)
        D = P.entfernungen(g)
        weg = P.zwei_opt(D, P.naechster_nachbar(D, 0))
        rest = weg[1:]
        for k in (1, 2, 3):
            beste = 10**9
            for anzahl in range(1, k + 1):
                for schnitte in combinations(range(1, len(rest)), anzahl - 1):
                    grenzen = [0, *schnitte, len(rest)]
                    kosten = max(min(D[0, rest[a]], D[0, rest[b - 1]]) + sum(D[rest[i], rest[i + 1]] for i in range(a, b - 1)) for a, b in zip(grenzen, grenzen[1:]))
                    beste = min(beste, int(kosten))
            assert P.zerlege(D, 0, weg, k)[0] == beste


def test_zwei_opt_verlaengert_nie_und_bleibt_eine_permutation():
    for seed in range(30):
        g = zufallsnetz(900 + seed, 4, 12)
        D = P.entfernungen(g)
        start = P.naechster_nachbar(D, 0)
        nachher = P.zwei_opt(D, start)
        assert sorted(nachher) == list(range(g.n)) and nachher[0] == 0
        assert P.weglaenge(D, nachher) <= P.weglaenge(D, start)
