"""Netze der Demo: Kantenzahlen, Grade, Türregeln und Nummern der Sondernetze."""

import numpy as np
import pytest

import udz_netze as N


def test_netz_weist_ungueltige_kanten_ab():
    for kanten in ([(0, 0)], [(0, 1), (1, 0)], [(0, 3)]):
        with pytest.raises(ValueError):
            N.netz("x", 3, kanten)


def test_handnetz_und_flurnetz():
    g = N.handnetz()
    assert g.n == 6 and len(g.kanten) == 7 and list(N.grade(g)) == [2, 2, 3, 3, 2, 2]
    assert N.handnetz(2).kanten == tuple(sorted(g.kanten + ((0, 5),)))
    f = N.flurnetz()
    assert f.n == 7 and len(f.kanten) == 8 and N.nachbarn(f)[6] == [2, 3] and not N.hat_kante(f, 2, 3)


def test_hallen_tuerplatz_ferne_ecke_und_eine_tuer_mehr():
    a = 8
    g = N.zwei_hallen(a)
    assert g.n == 128 and len(g.kanten) == 2 * 2 * a * (a - 1) + 1
    assert N.tuerknoten(a) == 39 and g.knoten[39] == "L(4,7)"
    assert N.hat_kante(g, 39, N.hallenknoten(a, 1, 4, 0))
    d = N.abstaende(g, 39)
    assert d[N.ferne_ecke(a)] == max(d[: a * a])                       # die fernste Ecke der linken Halle
    mehr = N.eine_tuer_mehr(a, 0)
    assert set(mehr.kanten) - set(g.kanten) == {(N.hallenknoten(a, 0, 0, a - 1), N.hallenknoten(a, 1, 0, 0))}
    assert set(g.kanten) <= set(mehr.kanten)
    with pytest.raises(ValueError):
        N.eine_tuer_mehr(a, a // 2)
    assert len(N.alle_tueren(a).kanten) == len(g.kanten) + a - 1


def test_saele_mit_flurknoten():
    for n in (5, 17, 65, 129):
        g = N.saele_mit_flurknoten(n)
        m = (n - 1) // 2
        d = N.grade(g)
        assert len(g.kanten) == m * (m - 1) + 2
        assert d[m] == 2 and d[m - 1] == m and d[m + 1] == m and d[0] == m - 1
        assert N.exzentrizitaet(g, m) == (1 if m == 1 else 2)
    with pytest.raises(ValueError):
        N.saele_mit_flurknoten(8)


def test_barbell_und_stichgang():
    g = N.barbell(48, 32)
    assert g.n == 128 and len(g.kanten) == 48 * 47 + 33
    s = N.barbell_mitte(48, 32)
    assert s == 63 and N.nachbarn(g)[s] == [62, 64] and N.exzentrizitaet(g, s) == 18
    h = N.saal_mit_stichgang(9, 5)
    assert h.n == 14 and len(h.kanten) == 36 + 5 and N.grade(h)[8] == 9 and N.grade(h)[13] == 1


def test_stern_kreis_saal_weg():
    assert list(N.grade(N.stern(14))) == [13] + [1] * 13
    assert (N.grade(N.kreis(14)) == 2).all()
    assert len(N.saal(14).kanten) == 91
    assert N.exzentrizitaet(N.weg(14), 0) == 13


def test_abstaende_und_zusammenhang():
    g = N.netz("zwei", 4, [(0, 1), (2, 3)])
    assert list(N.abstaende(g, 0)) == [0, 1, -1, -1]
    assert not N.ist_zusammenhaengend(g)
    assert N.ist_zusammenhaengend(N.weg(5))
    assert np.array_equal(N.adjazenz(N.weg(3)), np.array([[0, 1, 0], [1, 0, 1], [0, 1, 0]]))
