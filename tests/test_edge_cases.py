"""Randfälle: n = 1, n = 2, ein Läufer, mehr Läufer als Plätze, Rücksprung kürzer als die Entfernung, Gleichstand beim schlechtesten Start, alle Netze der App."""

import numpy as np
import pytest

import udz_constants as C
import udz_evaluation as E
import udz_exakt as X
import udz_irrfahrt_sim as S
import udz_matthews as MT
import udz_netze as N
import udz_plan as P
import udz_szenario as Z
import udz_trefferzeit as T


def test_ein_platz_braucht_null_schritte():
    g = N.netz("eins", 1, [])
    assert X.zustandsraum(g)[0] == 0 and X.reihe(g, [1, 4])[4][0] == 0 and X.ruecksprung(g, 0, 3) == [0.0, 0.0, 0.0]
    assert (S.simuliere_ueberdeckung(g, 0, 3, 5, 1) == 0).all()
    spur, erste, fertig = S.verlauf(g, 0, 2, 1)
    assert fertig and len(spur) == 1 and erste[0] == 0
    assert P.untere_schranke(g, 0, 1) == 0


def test_zwei_plaetze_brauchen_einen_schritt():
    g = N.netz("zwei", 2, [(0, 1)])
    assert list(X.zustandsraum(g)) == [1.0, 1.0]
    assert X.reihe(g, [1, 2, 32])[32] == pytest.approx([1.0, 1.0])
    assert X.ruecksprung(g, 0, 2) == pytest.approx([1.0, 1.0])
    assert (S.simuliere_ueberdeckung(g, 0, 5, 20, 2) == 1).all()
    assert P.plane(g, 0, [1])[1]["runden"] == 1
    assert MT.klammer(T.treffer_matrix(g))["oben"] == pytest.approx(1.0)


def test_mehr_laeufer_als_plaetze():
    g = N.weg(3)
    r = X.reihe(g, [1, 8])
    assert r[8][1] == pytest.approx(1.0, abs=0.05) and r[8][1] >= 1.0
    plan = P.plane(g, 1, [7])[7]
    assert plan["runden"] == 1 and len(plan["wege"]) == 7


def test_ruecksprung_zu_kurz_gibt_none():
    r = X.ruecksprung(N.weg(6), 0, 6)
    assert r[:4] == [None] * 4 and r[4] is not None


def test_gleichstand_beim_schlechtesten_start_kleinste_nummer():
    s = E.schlechtester_start(C.NETZ_HAND)
    assert s["start"] == 2                                              # 2 und 3 sind Spiegelbilder
    assert E.schlechtester_start(C.NETZ_KREIS4)["start"] == 0
    assert E.schlechtester_start(C.NETZ_SAELE, 65)["start"] == 32


@pytest.mark.parametrize("netz", C.NETZE)
def test_jedes_netz_der_app_hat_werte_je_start_und_vergleichsstarts(netz):
    groessen = [None]
    if netz == C.NETZ_HALLEN:
        groessen = list(range(C.A_MIN, C.A_MAX + 1))
    if netz == C.NETZ_SAELE:
        groessen = list(C.SAELE_GROESSEN)
    for groesse in groessen:
        g = Z.baue(netz, groesse)
        js = E.je_start(netz, groesse)
        assert len(js["werte"]) == g.n and np.all(js["werte"] >= g.n - 1 - 1e-9)
        starts = Z.vergleichsstarts(netz, groesse)
        for _, s, _ in starts:
            assert 0 <= s < g.n and E.hat_kurve(netz, groesse, s)
            zeilen = E.kurve(netz, groesse, s)
            assert [z["k"] for z in zeilen] == list(C.K_WERTE)
        m = E.matthews(netz, groesse)
        assert m["unten"] <= m["t_cov"] * 1.01 and m["t_cov"] <= m["oben"] * 1.01


def test_freier_start_auf_grossem_netz_bekommt_probelaeufe():
    erg = E.erwartung(C.NETZ_HALLEN, 8, 5, 8, 3)
    assert erg["quelle"] == "probelaeufe" and erg["laeufe"] == C.LIVE_LAEUFE and erg["se"] > 0
    assert E.erwartung(C.NETZ_HALLEN, 8, 5, 1, 3)["quelle"] == "gemessen"
    assert E.erwartung(C.NETZ_SAELE, 65, 3, 1, 3)["quelle"] == "exakt"


def test_vollstaendiger_saal_hat_keine_neue_verbindung():
    assert N.fehlende_kanten(N.saal(14)) == []


def test_alle_neuen_kanten_auf_zu_grossem_netz_wird_abgewiesen():
    with pytest.raises(ValueError):
        E.alle_neuen_kanten(C.NETZ_SAELE, 33)
    with pytest.raises(ValueError):
        X.zustandsraum(N.weg(19))
    with pytest.raises(ValueError):
        X.reihe(N.weg(16), [2])
    with pytest.raises(ValueError):
        P.kuerzester_plan_exakt(N.weg(9), 0, 1)


def test_jeder_gegner_fall_hat_ein_ergebnis():
    for fall in C.GEGNER_FAELLE:
        g, s = Z.gegner_fall(fall)
        geg = E.gegner(fall)
        assert [z["art"] for z in geg["zeilen"]] == ["ein", "k", "tau"]
        assert geg["tau"] >= N.exzentrizitaet(g, s)
        for plan in geg["plan"].values():
            assert plan["unten"] <= plan["runden"]
