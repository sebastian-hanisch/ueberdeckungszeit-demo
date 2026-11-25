"""Handrechnungen: kleine Netze, an denen jede Einheit mit Brüchen geprüft ist (Handnetz „zwei Hallen“, Weg a–m–b, 4-Kreis, Flurknoten-Netz, Hallen 2×2)."""

from fractions import Fraction as F

import pytest

import udz_exakt as X
import udz_matthews as MT
import udz_netze as N
import udz_plan as P
import udz_trefferzeit as T


def test_handnetz_ueberdeckung_und_schlechtester_start():
    c = X.zustandsraum(N.handnetz())
    assert c[[0, 1, 4, 5]] == pytest.approx([float(F(812, 39))] * 4, rel=1e-12)
    assert c[[2, 3]] == pytest.approx([float(F(1741, 78))] * 2, rel=1e-12)
    assert c.argmax() in (2, 3)


def test_handnetz_matthews_und_mengenschranke():
    H = T.treffer_matrix(N.handnetz())
    k = MT.klammer(H)
    assert k["hmax"] == pytest.approx(float(F(49, 3))) and k["hmin"] == pytest.approx(2.0)
    assert k["unten"] == pytest.approx(float(F(137, 30))) and k["oben"] == pytest.approx(37.2944444, abs=1e-6)
    wert, menge = MT.mengenschranke(H)
    assert wert == pytest.approx(float(F(49, 3))) and menge == [0, 4]   # die kleinste Menge unter den Gleichständen


@pytest.mark.parametrize("n", [4, 5, 6])
def test_vollstaendiger_saal_beide_schranken_genau(n):
    g = N.saal(n)
    h = sum(F(1, i) for i in range(1, n))
    erwartet = float((n - 1) * h)
    assert X.zustandsraum(g)[0] == pytest.approx(erwartet, rel=1e-12)
    k = MT.klammer(T.treffer_matrix(g))
    assert k["oben"] == pytest.approx(erwartet) and k["unten"] == pytest.approx(erwartet)


@pytest.mark.parametrize("n,schlecht", [(4, 11), (6, 31), (8, 61), (10, 101)])
def test_weg_schlechtester_start_im_inneren(n, schlecht):
    c = X.zustandsraum(N.weg(n))
    assert c[0] == pytest.approx((n - 1) ** 2) and c.max() == pytest.approx(schlecht) and 0 < c.argmax() < n - 1
    L = n - 1
    assert c == pytest.approx([i * (L - i) + L * L for i in range(n)])


def test_kreis_und_weg_formeln():
    for n in (5, 10, 14):
        assert X.zustandsraum(N.kreis(n)) == pytest.approx([n * (n - 1) / 2] * n)


def test_weg_a_m_b_zwei_laeufer_sieben_drittel():
    """Von Hand: Runde 1 sind die zwei Läufer mit ½ fertig; sonst x = 3/4·1 + 1/4·(2 + x) = 5/3, E = 1 + ½·(1 + x) = 7/3."""
    p = F(3, 4)
    x = (p + 2 * (1 - p)) / p
    assert x == F(5, 3)
    assert 1 + F(1, 2) * (1 + x) == F(7, 3)
    g = N.weg_amb()
    r = X.reihe(g, [1, 2])
    assert r[1][1] == pytest.approx(5.0) and r[2][1] == pytest.approx(7 / 3, rel=1e-9)
    assert X.ruecksprung(g, 1, 1)[0] == pytest.approx(3.0)              # fester Rücksprung nach jedem Schritt
    assert 2 * r[2][1] < r[1][1]


def test_vierkreis_mit_diagonale_und_pendelzeit():
    c4 = N.vierkreis()
    mit = N.mit_kante(c4, 0, 2)
    assert X.zustandsraum(c4) == pytest.approx([6.0] * 4)
    assert X.zustandsraum(mit).max() == pytest.approx(34 / 5)
    for netz, soll in ((c4, 8.0), (mit, 10.0)):
        assert T.pendelzeit(T.treffer_matrix(netz), 1, 3) == pytest.approx(soll)


def test_zweite_tuer_und_alle_acht_neuen_kanten_verkuerzen():
    g = N.handnetz()
    basis = X.zustandsraum(g).max()
    zwei = X.zustandsraum(N.mit_kante(g, 0, 5))
    assert zwei[0] == pytest.approx(float(F(14318443, 881790))) and zwei.max() == pytest.approx(zwei[0])
    neue = [X.zustandsraum(N.mit_kante(g, *e)).max() for e in N.fehlende_kanten(g)]
    assert len(neue) == 8 and all(v < basis for v in neue)
    assert min(neue) == pytest.approx(16.24, abs=5e-3) and max(neue) == pytest.approx(19.13, abs=5e-3)


def test_zwei_hallen_2x2_nur_die_vier_diagonalen_verlaengern():
    g = N.zwei_hallen(2)
    basis = X.zustandsraum(g).max()
    assert basis == pytest.approx(36.6612, abs=1e-3)
    laenger = [e for e in N.fehlende_kanten(g) if X.zustandsraum(N.mit_kante(g, *e)).max() > basis * (1 + 1e-9)]
    assert len(N.fehlende_kanten(g)) == 19 and laenger == [(0, 3), (1, 2), (4, 7), (5, 6)]
    assert X.zustandsraum(N.mit_kante(g, 1, 2)).max() == pytest.approx(40.0556, abs=1e-3)


def test_handnetz_zwei_und_drei_laeufer():
    r = X.reihe(N.handnetz(), [2, 3])
    assert r[2][0] == pytest.approx(float(F(4098248144419, 361451951658)), rel=1e-8)
    assert r[2][2] == pytest.approx(float(F(523983597775, 49855441608)), rel=1e-8)
    assert r[3][0] == pytest.approx(8.5858, abs=1e-4) and r[3][2] == pytest.approx(7.0891, abs=1e-4)


def test_flurnetz_und_fester_ruecksprung():
    g = N.flurnetz()
    c = X.zustandsraum(g)
    assert c[6] == pytest.approx(float(F(1987, 57))) and c[0] == pytest.approx(float(F(1816, 57)))
    r = X.ruecksprung(g, 6, 30)
    assert r[0] is None and r[3] == pytest.approx(21.0)
    gueltig = {t + 1: v for t, v in enumerate(r) if v is not None}
    assert min(gueltig, key=gueltig.get) == 4
    reihe = X.reihe(g, range(1, 17))
    gesamt = {k: k * reihe[k][6] for k in range(1, 17)}
    assert min(range(2, 17), key=gesamt.get) == 5 and gesamt[5] == pytest.approx(25.554, abs=1e-3)
    for k, wert in ((2, 29.79), (3, 27.13), (4, 25.91), (8, 26.88)):
        assert gesamt[k] == pytest.approx(wert, abs=5e-3)


@pytest.mark.parametrize("s,k,soll", [(0, 1, 5), (2, 1, 6), (2, 2, 3), (0, 2, 4)])
def test_karten_plaene_auf_dem_handnetz(s, k, soll):
    g = N.handnetz()
    assert P.kuerzester_plan_exakt(g, s, k) == soll
    assert P.plane(g, s, [k])[k]["runden"] >= soll


def test_median_bruch_auf_dem_weg():
    """Weg a–m–b ab m, ein Läufer: ab Runde 3 ist die Hälfte der Läufe fertig (nach 2 Runden P(fertig) = 0, dann je 2 Runden die Hälfte)."""
    assert X.median_runden(N.weg_amb(), 1, 1) == 3
