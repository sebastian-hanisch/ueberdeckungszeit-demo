"""Jede Zahl der README (und der Verdikte, die sie nennt) wird hier nachgerechnet: ohne Zufall neu gerechnet oder aus den gespeicherten Messungen gelesen;
eine Stichprobe der gespeicherten Messzellen wird mit demselben Zufalls-Seed neu gerechnet (Band 1 %, nicht bitgleich verlangt)."""

import pytest

import udz_atlas as AT
import udz_constants as C
import udz_daten as D
import udz_evaluation as E
import udz_exakt as X
import udz_messung as M
import udz_netze as N
import udz_plan as P
import udz_szenario as Z
import udz_trefferzeit as T

DATEN = D.laden()


def kurve(netz, groesse, start):
    return {z["k"]: z for z in E.kurve(netz, groesse, start)}


def saele(n, typ):
    m = (n - 1) // 2
    return kurve(C.NETZ_SAELE, n, {"F": m, "i": 0, "a": m - 1}[typ])


def hallen(a, start):
    return kurve(C.NETZ_HALLEN, a, N.tuerknoten(a) if start == "tuer" else 0)


def rund(x, n=2):
    return round(x + 1e-12, n)


# ----------------------------------------------------------------------------------------------------------------------------------
# Stichprobe der gespeicherten Messungen
# ----------------------------------------------------------------------------------------------------------------------------------

@pytest.mark.parametrize("netz,groesse,start,k", [("hallen", 4, 11, 2), ("hallen", 4, 0, 32), ("saele", 17, 8, 1), ("saele", 33, 0, 4), ("stichgang", None, 13, 8)])
def test_stichprobe_der_gespeicherten_kurven_wird_neu_gerechnet(netz, groesse, start, k):
    key = Z.netz_schluessel(netz, groesse)
    gespeichert = DATEN["kurven"][key][str(start)][str(k)]
    neu = M.wert(key, Z.baue(netz, groesse), start, k)
    assert neu["laeufe"] == gespeichert["laeufe"] == C.R_WERT
    assert neu["runden"] == pytest.approx(gespeichert["runden"], rel=0.01)
    assert neu["median"] == pytest.approx(gespeichert["median"], rel=0.02, abs=1)


def test_stichprobe_der_sichtung_wird_neu_gerechnet():
    g = Z.baue(C.NETZ_HALLEN, 4)
    d = DATEN["hallen"]["4"]
    for s in (0, 11, 20):
        neu = M.zelle("sicht", "hallen4", g, s, 1, C.R_SICHTEN)
        assert neu["runden"] == pytest.approx(d["sicht_mittel"][s], rel=0.01)


def test_gemessene_laeufer_treffen_die_rechnung_ohne_zufall_wo_beides_vorliegt():
    """C_1 der Simulation gegen die zusammengefasste Kette (Säle) und den Zustandsraum (Hallen 3×3, Netze bis 14 Plätze): Band 4 Standardfehler."""
    paare = [(C.NETZ_SAELE, n) for n in C.SAELE_GROESSEN] + [(C.NETZ_HALLEN, 3)] + [(x, None) for x in (C.NETZ_STICH, C.NETZ_SAAL14, C.NETZ_STERN14, C.NETZ_KREIS14, C.NETZ_WEG14)]
    for netz, groesse in paare:
        exakt = E.je_start(netz, groesse)["werte"]
        for _, s, _ in Z.vergleichsstarts(netz, groesse):
            z = DATEN["kurven"][Z.netz_schluessel(netz, groesse)][str(s)]["1"]
            assert abs(z["runden"] - exakt[s]) < 4 * z["se"], (netz, groesse, s)


# ----------------------------------------------------------------------------------------------------------------------------------
# Experiment 1
# ----------------------------------------------------------------------------------------------------------------------------------

def test_handnetz_zahlen():
    c = E.je_start(C.NETZ_HAND)["werte"]
    assert rund(c[0]) == 20.82 and rund(c[2]) == 22.32
    m = E.matthews(C.NETZ_HAND)
    assert rund(m["unten"]) == 4.57 and rund(m["oben"]) == 37.29 and rund(m["menge_wert"]) == 16.33


def test_saele_c1_ohne_zufall():
    werte = {17: (187.2, 184.9), 33: (664.0, 661.9), 65: (2423.2, 2421.1), 129: (9084.3, 9082.2)}
    for n, (f, i) in werte.items():
        c = E.je_start(C.NETZ_SAELE, n)["werte"]
        assert round(c[(n - 1) // 2], 1) == f and round(c[0], 1) == i


def test_matthews_tabelle_mit_14_plaetzen():
    z = {x["netz"]: x for x in E.tabelle_vergleich()}
    soll = {C.NETZ_SAAL14: (41.34, 1.00, 1.00, 1.00), C.NETZ_STERN14: (81.68, 1.01, 25.69, 1.01), C.NETZ_KREIS14: (91.00, 1.71, 2.20, 1.50),
            C.NETZ_WEG14: (211.00, 2.55, 66.35, 1.25), C.NETZ_STICH: (395.22, 3.16, 124.28, 11.22)}
    for netz, (t, o, u, m) in soll.items():
        x = z[netz]
        assert (rund(x["t_cov"]), rund(x["oben_faktor"]), rund(x["unten_faktor"]), rund(x["menge_faktor"])) == (t, o, u, m), netz


def test_matthews_auf_den_gitterhallen():
    faktoren = {a: E.matthews(C.NETZ_HALLEN, a) for a in range(3, 9)}
    oben = [round(m["oben_faktor"], 2) for m in faktoren.values()]
    unten = [round(m["unten_faktor"], 1) for m in faktoren.values()]
    assert oben == [2.08, 2.33, 2.40, 2.53, 2.57, 2.67]
    assert unten == [6.9, 8.1, 6.3, 6.9, 6.4, 6.8]
    assert round(faktoren[3]["t_cov"], 2) == 141.58 and round(faktoren[8]["t_cov"]) == 2451


def test_verdikt_hallen_8x8():
    m = E.matthews(C.NETZ_HALLEN, 8)
    kind, text = E.verdict_matthews("Zwei Hallen 8×8", m["oben_faktor"], m["unten_faktor"], m["t_art"])
    assert kind == "warning" and "2,7-Fachen" in text and "1/6,8-Fachen" in text and "gemessenen" in text


def test_nachgemessene_starts_der_gitterhallen():
    d = DATEN["hallen"]["8"]
    g = Z.baue(C.NETZ_HALLEN, 8)
    assert g.knoten[d["schlechtester"]] == "R(6,2)"
    werte = {g.knoten[int(s)]: round(c["runden"]) for s, c in d["bestaetigt"].items()}
    assert werte["R(6,2)"] == 2451 and werte["L(4,7)"] == 2444 and werte["L(0,0)"] == 2409
    for a in range(4, 9):
        assert len(DATEN["hallen"][str(a)]["sicht_mittel"]) == 2 * a * a
        assert DATEN["hallen"][str(a)]["sicht_laeufe"] == 4000


def test_weg_schlechtester_start_im_inneren():
    assert [round(X.zustandsraum(N.weg(n)).max()) for n in (4, 6, 8, 10)] == [11, 31, 61, 101]
    assert [round(X.zustandsraum(N.weg(n))[0]) for n in (4, 6, 8, 10)] == [9, 25, 49, 81]


def test_handnetz_brueche():
    c = E.je_start(C.NETZ_HAND)["werte"]
    assert c[0] == pytest.approx(812 / 39, rel=1e-12) and c[2] == pytest.approx(1741 / 78, rel=1e-12)


# ----------------------------------------------------------------------------------------------------------------------------------
# Experiment 2
# ----------------------------------------------------------------------------------------------------------------------------------

def test_atlas_zaehlung_neue_kante_wird_vollstaendig_neu_gerechnet():
    pytest.importorskip("networkx")
    z = AT.zaehle_neue_kante()
    assert (z["graphen"], z["nicht_vollstaendig"], z["mit_verlaengernder_kante"]) == (994, 989, 848)
    assert (z["laenger"], z["ergaenzungen"]) == (2790, 9182) and round(100 * z["laenger"] / z["ergaenzungen"], 1) == 30.4
    assert (z["bahnen_laenger"], z["bahnen"]) == (1926, 5832) and round(100 * z["bahnen_laenger"] / z["bahnen"], 1) == 33.0
    assert (z["beschriftet_laenger"], z["beschriftet"]) == (6153454, 19116131) and round(100 * z["beschriftet_laenger"] / z["beschriftet"], 1) == 32.2
    assert round(z["groesster_faktor"], 2) == 1.18
    assert z["kleinste"]["knoten"] == 4 and z["kleinste"]["vorher"] == pytest.approx(6.0) and z["kleinste"]["nachher"] == pytest.approx(6.8)
    for key in ("graphen", "nicht_vollstaendig", "mit_verlaengernder_kante", "laenger", "ergaenzungen", "bahnen", "bahnen_laenger", "beschriftet", "beschriftet_laenger"):
        assert DATEN["atlas_kante"][key] == z[key]


def test_vierkreis_pendelzeit_und_ueberdeckung():
    vk = N.vierkreis()
    mit = N.mit_kante(vk, 0, 2)
    assert (T.pendelzeit(T.treffer_matrix(vk), 1, 3), T.pendelzeit(T.treffer_matrix(mit), 1, 3)) == pytest.approx((8, 10))
    assert (X.zustandsraum(vk).max(), X.zustandsraum(mit).max()) == pytest.approx((6, 6.8))


def test_handnetz_und_2x2_hallen_neue_kanten():
    z = E.zaehle_laenger(E.alle_neuen_kanten(C.NETZ_HAND))
    assert z == {"alle": 8, "laenger": 0, "kuerzer": 8}
    nach = [x["nachher"] for x in E.alle_neuen_kanten(C.NETZ_HAND)]
    assert (rund(min(nach)), rund(max(nach))) == (16.24, 19.13)
    z = E.zaehle_laenger(E.alle_neuen_kanten(C.NETZ_HALLEN, 2), 2)
    assert (z["alle"], z["innen"], z["innen_laenger"], z["zwischen"], z["zwischen_kuerzer"]) == (19, 4, 4, 15, 15)
    basis = X.zustandsraum(Z.baue(C.NETZ_HALLEN, 2)).max()
    assert rund(basis) == 36.66 and rund(max(x["nachher"] for x in E.alle_neuen_kanten(C.NETZ_HALLEN, 2))) == 40.06


def test_hallen_3x3_alle_128_verbindungen():
    z = E.zaehle_laenger(E.alle_neuen_kanten(C.NETZ_HALLEN, 3), 3)
    assert (z["alle"], z["innen"], z["innen_laenger"], z["innen_kuerzer"], z["zwischen"], z["zwischen_laenger"], z["zwischen_kuerzer"]) == (128, 48, 44, 4, 80, 0, 80)


def test_hallen_3x3_stichprobe_der_vorgerechneten_liste_neu():
    g = Z.baue(C.NETZ_HALLEN, 3)
    liste = DATEN["tuer3x3"]["kanten"]
    assert DATEN["tuer3x3"]["basis"] == pytest.approx(X.zustandsraum(g).max(), rel=1e-10)
    for u, v, w in liste[::11]:
        assert X.zustandsraum(N.mit_kante(g, u, v)).max() == pytest.approx(w, rel=1e-10)


def test_weitere_tueren_auf_den_hallen():
    t3 = DATEN["tuer"]["3"]
    assert [rund(max(t3[k])) for k in ("basis", "0", "alle")] == [141.58, 125.61, 115.36]
    basis = hallen(8, "ecke")[1]["runden"]
    assert round(basis) == 2409
    assert round(DATEN["tuer"]["8"]["0"]["ecke"]["runden"]) == 2104
    assert round(DATEN["tuer"]["8"]["alle"]["ecke"]["runden"]) == 1842
    # in jedem gemessenen Fall kürzer, nach nicht überschneidenden Intervallen
    faelle = 0
    for a in range(4, 9):
        for r in [x for x in range(a) if x != a // 2] + ["alle"]:
            for name in ("tuer", "ecke"):
                z = E.tuer_zeile(a, r, name)
                assert E.vergleiche(z["nachher"], z["nachher_se"], z["vorher"], z["vorher_se"]) == "weniger", (a, r, name)
                faelle += 1
    assert faelle == 60


# ----------------------------------------------------------------------------------------------------------------------------------
# Experiment 3
# ----------------------------------------------------------------------------------------------------------------------------------

def test_kleine_netze_mehrere_laeufer_ohne_zufall():
    hand = E.kurve(C.NETZ_HAND, None, 2)
    tuer = {z["k"]: z for z in hand}
    ecke = kurve(C.NETZ_HAND, None, 0)
    assert rund(tuer[2]["runden"]) == 10.51 and rund(tuer[2]["gesamt"]) == 21.02 and rund(ecke[2]["gesamt"]) == 22.68
    r3 = X.reihe(N.handnetz(), [3])[3]
    assert rund(r3[2]) == 7.09 and rund(3 * r3[2]) == 21.27 and rund(r3[0]) == 8.59 and rund(3 * r3[0]) == 25.76
    w = kurve(C.NETZ_WEG3, None, 1)
    assert w[2]["runden"] == pytest.approx(7 / 3, rel=1e-8) and 2 * w[2]["runden"] < 5
    mitte = kurve(C.NETZ_FLUR, None, 6)
    ecke = kurve(C.NETZ_FLUR, None, 0)
    assert rund(mitte[1]["runden"]) == 34.86 and rund(mitte[2]["gesamt"]) == 29.79 and rund(mitte[4]["gesamt"]) == 25.91 and rund(ecke[2]["gesamt"]) == 34.93


def test_saele_hauptzahlen():
    for n, f8, i8, a8, f32 in ((65, 5.57, 0.79, 0.85, 6.65), (129, 8.63, 0.85, 0.89, 11.51)):        # 65, k = 32: 2423,19 / (32 · 11,380) = 6,654
        assert rund(saele(n, "F")[8]["s_je_k"]) == f8
        assert rund(saele(n, "i")[8]["s_je_k"]) == i8
        assert rund(saele(n, "a")[8]["s_je_k"]) == a8
        assert rund(saele(n, "F")[32]["s_je_k"]) == f32
    # von den drei Arten von Starts spart k = 8 bei n = 65 und 129 nur ab der Mitte
    for n in (65, 129):
        assert [saele(n, t)[8]["s_je_k"] > 1 for t in ("F", "i", "a")] == [True, False, False]


def test_saele_k_zwei_ab_der_mitte_ist_schief():
    z = saele(65, "F")[2]
    assert round(z["gesamt"], -1) == 1470 and round(z["gesamt_median"], -1) == 510
    assert z["gesamt"] > 2.5 * z["gesamt_median"]


def test_saele_verdikt_mitte_und_innen():
    kind, text = E.verdict_viele("N", "Flurmitte", saele(65, "F")[8])
    assert kind == "success" and "weniger als ein Fünftel" in text
    kind, text = E.verdict_viele("N", "Saal-Innenplatz", saele(65, "i")[8])
    assert kind == "warning" and "**mehr**" in text


def test_hallen_8x8_tuer_und_ferne_ecke():
    tuer, ecke = hallen(8, "tuer"), hallen(8, "ecke")
    assert [rund(tuer[k]["s_je_k"]) for k in (2, 4, 8, 32)] == [1.02, 1.06, 1.06, 0.86]
    assert [rund(ecke[k]["s_je_k"]) for k in (2, 4, 8, 32)] == [0.99, 0.88, 0.69, 0.35]
    assert all(ecke[k]["s_je_k"] < 1 for k in (2, 4, 8, 16, 32))
    assert rund(1 / ecke[32]["s_je_k"], 1) == 2.8


def test_gewinn_auf_den_gitterhallen_bleibt_klein():
    werte = [z["s_je_k"] for a in range(3, 9) for s in ("tuer", "ecke") for z in hallen(a, s).values()]
    assert max(werte) < 1.07 and max(werte) > 1.05


def test_gegenpole():
    z = {(x["netz"], x["k"]): round(x["s_je_k"], 2) for x in E.gegenpole()}
    # Kreis und Weg: C_1 aus der bekannten Formel (8 128 bzw. 16 129), also 8128 / 11533,3 = 0,705
    assert z == {("Kreis (128)", 8): 0.70, ("Kreis (128)", 32): 0.33, ("Weg (128), Start am Ende", 8): 0.47, ("Weg (128), Start am Ende", 32): 0.20,
                 ("Gitter 11×11, Start in der Mitte", 8): 0.98, ("Gitter 11×11, Start in der Mitte", 32): 0.88}


def test_start_nach_pi_auf_den_hallen_8x8():
    z = {x["k"]: x for x in E.pi_start()}
    assert [rund(z[k]["s_je_k"]) for k in (2, 8, 32)] == [1.03, 1.22, 1.55]
    assert round(z[2]["c1"]) == 2429


def test_weg_mit_15_plaetzen_schlechtester_start_je_laeuferzahl():
    c = X.reihe(N.weg(15), [1, 2])
    assert rund(c[1].max() / c[2].max(), 3) == 2.117 == rund(DATEN["weg15"]["s2"], 3)


GEGNER_SOLL = {
    # Fall: (ein Läufer, halbe Breite), (k, Gesamtschritte, halbe Breite), (tau, Schritte, halbe Breite) wie in der README (gerundet)
    # ein Läufer: Säle und Weg ohne Zufall (Breite 0), Hallen die Messung aus Experiment 3, Barbell eigene Bewertung
    "saele65_F": ((2423, 0), (24, 360.3, 1.0), (16, 343.8, 0.9)),
    "saele129_F": ((9084, 0), (40, 788.3, 1.9), (20, 763.9, 1.8)),
    "barbell": ((76324, 732), (10, 2864, 51), (512, 2029, 12)),
    "weg128": ((20161, 0), (4, 17378, 79), (3072, 16889, 70)),
    "hallen8_tuer": ((2444, 7), (7, 2303, 6), (448, 2302, 7)),
    "hallen8_ecke": ((2409, 7), (2, 2440, 7), (16384, 2413, 7)),
    "saele65_i": ((2421, 0), (2, 2429, 21), (4096, 2424, 22)),
}


def test_ein_laeufer_hat_auf_jeder_seite_denselben_wert():
    assert E.gegner("hallen8_tuer")["zeilen"][0]["gesamt"] == hallen(8, "tuer")[1]["gesamt"]
    assert E.gegner("saele65_F")["zeilen"][0]["gesamt"] == saele(65, "F")[1]["gesamt"]
    g, s = Z.gegner_fall("weg128")
    d = DATEN["gegner"]["weg128"]["ein"]
    assert abs(d["runden"] - E.gegner("weg128")["zeilen"][0]["gesamt"]) < 4 * d["se"]         # Messung gegen die Formel


@pytest.mark.parametrize("fall", list(GEGNER_SOLL))
def test_gegner_tabelle(fall):
    (e, es), (k, kg, ks), (tau, tg, ts) = GEGNER_SOLL[fall]
    g = E.gegner(fall)
    ein, kz, tz = g["zeilen"]
    assert (g["k"], g["tau"]) == (k, tau)
    for zeile, wert, breite in ((ein, e, es), (kz, kg, ks), (tz, tg, ts)):
        assert zeile["gesamt"] == pytest.approx(wert, abs=0.6 if wert > 100 else 0.06) or round(zeile["gesamt"], 1) == wert
        assert 1.96 * zeile["gesamt_se"] == pytest.approx(breite, abs=0.6)


def test_gegner_ohne_zufall():
    soll = {"flur_mitte": (34.86, 5, 25.55, 4, 21.0), "hand_tuer": (22.32, 2, 21.02, 7, 20.97), "hand_ecke": (20.82, 2, 22.68, 80, 20.83)}
    for fall, (e, k, kg, tau, tg) in soll.items():
        g = E.gegner(fall)
        ein, kz, tz = g["zeilen"]
        assert (rund(ein["gesamt"]), g["k"], rund(kz["gesamt"]), g["tau"], rund(tz["gesamt"])) == (e, k, kg, tau, tg), fall


def test_fuenf_netze_vier_weniger_eines_gleichauf_nach_intervallen():
    z = {x["fall"]: x for x in E.fuenf_netze()}
    assert {f: x["tau_gegen_k"] for f, x in z.items()} == {"saele65_F": "weniger", "saele129_F": "weniger", "barbell": "weniger", "weg128": "weniger", "hallen8_tuer": "gleichauf"}
    assert all(x["k_gegen_ein"] == "weniger" for x in z.values())
    tuer = z["hallen8_tuer"]
    assert 0.05 < 1 - tuer["k_gesamt"] / tuer["ein"] < 0.07 and 0.05 < 1 - tuer["tau_gesamt"] / tuer["ein"] < 0.07
    text = E.satz_fuenf_netze(E.fuenf_netze())
    assert "auf 4 weniger Gesamtschritte" in text and "auf 1 nicht unterscheidbar viele" in text and "mehr (um" not in text


def test_erste_auswahlrunde_an_der_hallentuer_war_um_0_6_prozent_teurer():
    """Die README nennt die erste Auswahlrunde (4 000 Läufe je Rasterwert): dort wurden k = 5 und tau = 320 gewählt. Beide werden mit den Bewertungs-Seeds jener
    Runde neu gerechnet (100 000 Läufe)."""
    g, s = Z.gegner_fall("hallen8_tuer")
    k5, t320 = M.wert("hallen8", g, s, 5), M.wert("hallen8", g, s, 1, tau=320)
    assert 100 * (t320["runden"] / (5 * k5["runden"]) - 1) == pytest.approx(0.6, abs=0.1)
    assert E.vergleiche(t320["runden"], t320["se"], 5 * k5["runden"], 5 * k5["se"]) == "mehr"


def test_kein_gewinn_ferne_ecke_saalinnen_und_handnetzecke():
    for fall in ("hallen8_ecke", "saele65_i", "hand_ecke"):
        u = E.gegner_urteil(E.gegner(fall))
        assert u["k_gegen_ein"] != "weniger" and u["tau_gegen_ein"] != "weniger", fall
        assert "weder eine getestete Läuferzahl noch ein getesteter Rücksprung" in E.verdict_gegner(C.GEGNER_TEXT[fall], E.gegner(fall))[1]


def test_readme_nennt_rasterrand_nur_am_rand_des_rasters():
    """„(Rasterrand)“ in der Gegnertabelle nur, wenn das gewählte τ der kleinste oder größte gerechnete Rasterwert ist."""
    from pathlib import Path
    zeilen = (Path(__file__).resolve().parent.parent / "README.md").read_text(encoding="utf-8").splitlines()
    kopf = {"hallen8_ecke": "| Zwei Hallen 8×8, ferne Ecke", "hand_ecke": "| Handnetz, Hallenecke"}
    for fall in C.GEGNER_FAELLE:
        assert DATEN["gegner"][fall]["tau_wahl"][-1]["tau"] == C.GEGNER_TAU[fall][-1], fall
    for fall, anfang in kopf.items():
        zeile = next(z for z in zeilen if z.startswith(anfang))
        am_rand = E.gegner(fall)["tau_am_rand"]
        assert ("(Rasterrand)" in zeile) == am_rand, (fall, zeile)
    assert sum("(Rasterrand)" in z for z in zeilen) == sum(E.gegner(f)["tau_am_rand"] for f in C.GEGNER_FAELLE) == 1
    ecke = C.GEGNER_TAU["hallen8_ecke"]
    assert E.gegner("hallen8_ecke")["tau"] == ecke[-2] == 16384 and ecke[-1] == 32768
    assert any("τ = 16 384 (zweitgrößter Rasterwert, das Raster reicht bis 32 768): 2 413 ± 7" in z for z in zeilen)


def test_ferne_ecke_8x8_keine_getestete_laeuferzahl_spart_gesamtschritte():
    """Getestet sind k = 2 bis 16 (Auswahlläufe des Gegners) und die Läuferzahlen aus Experiment 3 (2, 4, 8, 16, 32): jede braucht nach nicht
    überschneidenden Intervallen mehr Gesamtschritte als ein Läufer."""
    ein = DATEN["kurven"]["hallen8"]["0"]["1"]
    wahl = DATEN["gegner"]["hallen8_ecke"]["k_wahl"]
    assert [p["k"] for p in wahl] == list(range(2, 17))
    for p in wahl:
        assert E.vergleiche(p["k"] * p["runden"], p["k"] * p["se"], ein["runden"], ein["se"]) == "mehr", p["k"]
    for k, z in hallen(8, "ecke").items():
        if k > 1:
            assert E.vergleiche(z["gesamt"], z["gesamt_se"], ein["runden"], ein["se"]) == "mehr", k
    assert sorted({p["k"] for p in wahl} | {k for k in C.K_WERTE if k > 1}) == list(range(2, 17)) + [32]


def test_stichprobe_gegner_bewertung_wird_neu_gerechnet():
    g, s = Z.gegner_fall("saele65_F")
    d = DATEN["gegner"]["saele65_F"]
    tau = d["bestes_tau"]["tau"]
    neu = M.zelle("bewertung-2", "saele65", g, s, 1, d["bestes_tau"]["laeufe"], tau=tau)
    assert neu["runden"] == pytest.approx(d["bestes_tau"]["runden"], rel=0.01)


def test_karten_plan_zahlen_auf_ferner_ecke():
    karte = {z["k"]: z for z in E.karte_gegen_zufall("hallen8_ecke")}
    assert [round(karte[k]["faktor"], 1) for k in (1, 2, 8)] == [17.8, 16.3, 15.6]
    assert round(karte[32]["faktor"], 1) == 9.3
    tuer = {z["k"]: z for z in E.karte_gegen_zufall("hallen8_tuer")}
    assert [round(tuer[k]["zufall"]) for k in (1, 2, 8, 32)] == [2444, 1194, 289, 89]
    assert [round(tuer[k]["faktor"]) for k in (1, 2, 8, 32)] == [19, 19, 16, 7]
    assert [tuer[k]["untere"] for k in (1, 2, 8, 32)] == [127, 64, 16, 12]
    s = {z["k"]: z for z in E.karte_gegen_zufall("saele65_F")}
    assert [round(s[2]["zufall"]), round(s[8]["zufall"]), round(s[32]["zufall"], 1)] == [736, 54, 11.4]


def test_karten_plan_auf_dem_handnetz_ist_der_kuerzeste():
    for s, soll_runden, irrfahrer in ((2, 3, 10.51), (0, 4, 11.34)):
        g = N.handnetz()
        assert P.plane(g, s, [2])[2]["runden"] == P.kuerzester_plan_exakt(g, s, 2) == soll_runden
        assert rund(kurve(C.NETZ_HAND, None, s)[2]["runden"]) == irrfahrer


def test_karten_plan_zahlen():
    """Plan-Runden je Gegner-Fall (obere Schranke), nachgelaufen; Vergleich mit den Irrfahrern aus Experiment 3."""
    plaene = {fall: P.plane(*Z.gegner_fall(fall), [1, 2, 8, 32]) for fall in ("hallen8_tuer", "hallen8_ecke", "saele65_F")}
    assert [plaene["hallen8_tuer"][k]["runden"] for k in (1, 2, 8, 32)] == [130, 64, 18, 12]
    assert plaene["hallen8_tuer"][8]["unten"] == 16
    assert [plaene["saele65_F"][k]["runden"] for k in (2, 8, 32)] == [32, 9, 3]
    karte = {z["k"]: z for z in E.karte_gegen_zufall("saele65_F")}
    assert [round(karte[k]["faktor"]) for k in (2, 8, 32)] == [23, 6, 4]
    for fall in C.GEGNER_FAELLE:
        for z in E.karte_gegen_zufall(fall):
            assert z["plan"] < z["zufall"] and z["plan"] >= z["untere"], (fall, z)


def test_atlas_viele_laeufer_und_ruecksprung():
    pytest.importorskip("networkx")
    z = AT.zaehle_laeufer_und_ruecksprung(C.ATLAS_K_MAX, C.ATLAS_TAU_MAX)
    assert z["graphen"] == 994 and z["graphen_bis6"] == 141
    assert z["an_allen"] == {"2": 0, "3": 0, "4": 0}
    assert (z["an_teil"]["2"], z["an_keinem"]["2"]) == (704, 290)
    assert (z["paare_mit_gewinn"], z["ruecksprung_hoechstens"], len(z["ruecksprung_mehr"])) == (1077, 1058, 19)
    assert round(100 * z["groesster_ueberschuss"], 1) == 2.1
    d = DATEN["atlas_laeufer"]
    assert len(d["ruecksprung_mehr"]) == len(z["ruecksprung_mehr"])
    for alt, neu in zip(d["ruecksprung_mehr"], z["ruecksprung_mehr"]):
        assert (alt["knoten"], alt["start"], alt["k"], alt["tau"]) == (neu["knoten"], neu["start"], neu["k"], neu["tau"])
        assert alt["tau_gesamt"] == pytest.approx(neu["tau_gesamt"], rel=1e-8)
    assert AT.zwei_laeufer_nie(N.saal(8)) and AT.zwei_laeufer_nie(N.kreis(10))
    assert d["k8_nie"] and d["kreis10_nie"]
