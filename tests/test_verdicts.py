"""Verdikte als reine Funktionen (udz_evaluation.verdict_*): Schwellen und jede Zahl im Text an handgesetzten Werten."""

import pytest

import udz_evaluation as ev


def test_intervall_vergleich():
    assert ev.vergleiche(10.0, 0.5, 12.0, 0.5) == "weniger"             # 10,98 < 11,02
    assert ev.vergleiche(10.0, 0.52, 12.0, 0.52) == "gleichauf"
    assert ev.vergleiche(12.0, 0.1, 10.0, 0.1) == "mehr"
    assert ev.vergleiche(21.0, 0.0, 21.0, 0.0) == "gleichauf"
    assert ev.vergleiche(21.0, 0.0, 25.554, 0.0) == "weniger"


def test_matthews_genau_und_weit():
    kind, text = ev.verdict_matthews("Saal 5", 1.0, 1.0, "exakt")
    assert kind == "success" and "beide Schranken genau" in text and "berechneten" in text
    kind, text = ev.verdict_matthews("zwei Hallen", 2.66, 6.84, "gemessen")
    assert kind == "warning" and "2,7-Fachen" in text and "1/6,8-Fachen" in text and "gemessenen" in text
    kind, text = ev.verdict_matthews("Stern", 1.01, 25.69, "exakt")
    assert kind == "warning" and "fast genau (das 1,01-Fache)" in text and "1/25,7-Fachen" in text and text.startswith("Auf dem Netz „Stern“")
    assert ev.verdict_matthews("x", 1.1, 1.1, "exakt")[0] == "success"


def test_neue_kante_laenger_kuerzer_gleich():
    kind, text = ev.verdict_neue_kante("K", 6.0, 6.8)
    assert kind == "warning" and "verlängert" in text and "6,00 → 6,80" in text
    assert ev.verdict_neue_kante("K", 22.32, 16.24)[0] == "success"
    assert ev.verdict_neue_kante("K", 5.0, 5.0 + 1e-12)[0] == "info"


def test_alle_kanten_text_fuer_hallen_und_andere_netze():
    z = {"alle": 19, "laenger": 4, "kuerzer": 15, "innen": 4, "innen_laenger": 4, "innen_kuerzer": 0, "zwischen": 15, "zwischen_laenger": 0, "zwischen_kuerzer": 15}
    kind, text = ev.verdict_alle_kanten("zwei 2×2-Hallen", z)
    assert kind == "warning" and "jede der 4 neuen Verbindungen innerhalb einer Halle" in text and "jede der 15 neuen Verbindungen zwischen den Hallen verkürzt sie" in text
    z.update(innen=48, innen_laenger=44, zwischen=80, zwischen_kuerzer=79)
    kind, text = ev.verdict_alle_kanten("H", z)
    assert "44 der 48" in text and "keine der 80 neuen Verbindungen zwischen den Hallen verlängert sie" in text
    z.update(zwischen_laenger=2)
    assert "verlängern sie 2" in ev.verdict_alle_kanten("H", z)[1]
    kind, text = ev.verdict_alle_kanten("N", {"alle": 8, "laenger": 0, "kuerzer": 8})
    assert kind == "success" and text == "Auf N verkürzt jede der 8 möglichen neuen Verbindungen die Überdeckungszeit des schlechtesten Starts."
    assert "verlängert keine der 8 möglichen neuen Verbindungen" in ev.verdict_alle_kanten("N", {"alle": 8, "laenger": 0, "kuerzer": 5})[1]
    assert ev.verdict_alle_kanten("N", {"alle": 8, "laenger": 3, "kuerzer": 5})[0] == "warning"
    assert ev.verdict_alle_kanten("N", {"alle": 1, "laenger": 0, "kuerzer": 0, "innen": 0, "innen_laenger": 0, "zwischen": 1, "zwischen_laenger": 0, "zwischen_kuerzer": 0})[0] == "info"


@pytest.mark.parametrize("alle,laenger,kuerzer,satz", [
    (1, 0, 1, "Auf N verkürzt die einzige mögliche neue Verbindung die Überdeckungszeit des schlechtesten Starts."),
    (1, 1, 0, "Auf N verlängert die einzige mögliche neue Verbindung die Überdeckungszeit des schlechtesten Starts."),
    (1, 0, 0, "Auf N verlängert die einzige mögliche neue Verbindung die Überdeckungszeit des schlechtesten Starts nicht."),
    (8, 0, 8, "Auf N verkürzt jede der 8 möglichen neuen Verbindungen die Überdeckungszeit des schlechtesten Starts."),
    (8, 0, 5, "Auf N verlängert keine der 8 möglichen neuen Verbindungen die Überdeckungszeit des schlechtesten Starts."),
    (8, 1, 7, "Auf N verlängert 1 der 8 möglichen neuen Verbindungen die Überdeckungszeit des schlechtesten Starts."),
    (77, 28, 49, "Auf N verlängern 28 der 77 möglichen neuen Verbindungen die Überdeckungszeit des schlechtesten Starts."),
    (2, 2, 0, "Auf N verlängert jede der 2 möglichen neuen Verbindungen die Überdeckungszeit des schlechtesten Starts."),
])
def test_alle_kanten_satzbau_in_einzahl_und_mehrzahl(alle, laenger, kuerzer, satz):
    art, text = ev.verdict_alle_kanten("N", {"alle": alle, "laenger": laenger, "kuerzer": kuerzer})
    assert text == satz and art == ("warning" if laenger else "success")


@pytest.mark.parametrize("innen,innen_laenger,teil", [
    (48, 44, "Auf H verlängern 44 der 48 neuen Verbindungen innerhalb einer Halle die Überdeckungszeit des schlechtesten Starts;"),
    (48, 1, "Auf H verlängert 1 der 48 neuen Verbindungen innerhalb einer Halle die"),
    (48, 0, "Auf H verlängert keine der 48 neuen Verbindungen innerhalb einer Halle die"),
    (4, 4, "Auf H verlängert jede der 4 neuen Verbindungen innerhalb einer Halle die"),
    (1, 1, "Auf H verlängert die einzige neue Verbindung innerhalb einer Halle die"),
    (1, 0, "Auf H verlängert die einzige neue Verbindung innerhalb einer Halle nicht die"),
])
def test_alle_kanten_satzbau_innerhalb_der_hallen(innen, innen_laenger, teil):
    z = {"alle": innen + 5, "laenger": innen_laenger, "kuerzer": 5, "innen": innen, "innen_laenger": innen_laenger, "zwischen": 5, "zwischen_laenger": 0,
         "zwischen_kuerzer": 5}
    assert teil in ev.verdict_alle_kanten("H", z)[1]


@pytest.mark.parametrize("zwischen,laenger,kuerzer,teil", [
    (15, 0, 15, "; jede der 15 neuen Verbindungen zwischen den Hallen verkürzt sie."),
    (1, 0, 1, "; die einzige neue Verbindung zwischen den Hallen verkürzt sie."),
    (80, 0, 79, "; keine der 80 neuen Verbindungen zwischen den Hallen verlängert sie."),
    (80, 1, 79, "; von den 80 neuen Verbindungen zwischen den Hallen verlängert sie 1."),
    (80, 2, 78, "; von den 80 neuen Verbindungen zwischen den Hallen verlängern sie 2."),
    (1, 1, 0, "; die einzige neue Verbindung zwischen den Hallen verlängert sie."),
])
def test_alle_kanten_satzbau_zwischen_den_hallen(zwischen, laenger, kuerzer, teil):
    z = {"alle": 4 + zwischen, "laenger": 4 + laenger, "kuerzer": kuerzer, "innen": 4, "innen_laenger": 4, "zwischen": zwischen,
         "zwischen_laenger": laenger, "zwischen_kuerzer": kuerzer}
    assert ev.verdict_alle_kanten("H", z)[1].endswith(teil)


def test_runden_in_einzahl_und_mehrzahl():
    assert ev.runden_wort(1) == "1 Runde" and ev.runden_wort(2) == "2 Runden" and ev.runden_wort(12345) == "12 345 Runden"


def test_tuer_verdikt_trennt_nach_intervallen():
    nah = {"vorher": 2400.0, "vorher_se": 10.0, "nachher": 2370.0, "nachher_se": 10.0}
    kind, text = ev.verdict_tuer(8, 0, "ecke", nah)
    assert kind == "info" and "nicht unterscheidbar" in text and "Zeile 0" in text and "Zeile 4" in text
    kind, text = ev.verdict_tuer(8, 0, "tuer", dict(nah, nachher=2100.0))
    assert kind == "success" and "kürzer" in text and "ab dem Türplatz" in text
    kind, _ = ev.verdict_tuer(8, "alle", "ecke", dict(nah, nachher=2600.0))
    assert kind == "warning"


def _zeile(k, s_je_k, se, gesamt, c1):
    return {"k": k, "s_je_k": s_je_k, "s_je_k_se": se, "gesamt": gesamt, "c1": c1, "runden": gesamt / k, "se": 1.0}


def test_viele_laeufer_schwellen_und_zahlen():
    kind, text = ev.verdict_viele("N", "S", _zeile(8, 5.5, 0.1, 440.6, 2423.0))
    assert kind == "success" and "weniger als ein Fünftel" in text and "S_8/8 = 5,50 ± 0,20" in text and "441" not in text and "440,6" in text
    kind, text = ev.verdict_viele("N", "S", _zeile(8, 0.79, 0.005, 3060.0, 2421.0))
    assert kind == "warning" and "mehr" in text
    kind, text = ev.verdict_viele("N", "S", _zeile(2, 1.01, 0.02, 100.0, 101.0))
    assert kind == "info" and "nicht unterscheidbar" in text
    kind, text = ev.verdict_viele("N", "S", _zeile(2, 1.059, 0.005, 2300.0, 2436.0))
    assert kind == "success" and "weniger Schritte als einer" in text
    assert ev.verdict_viele("N", "S", _zeile(1, 1.0, 0.0, 22.3, 22.3))[0] == "info"


def test_bruchwort():
    assert ev.bruchwort(0.19) == "weniger als ein Fünftel" and ev.bruchwort(0.2) == "weniger als ein Viertel"
    assert ev.bruchwort(0.3) == "weniger als ein Drittel" and ev.bruchwort(0.45) == "weniger als die Hälfte" and ev.bruchwort(0.9) == "weniger"


def _geg(ein, kz, tz, se=1.0):
    def z(art, gesamt, kk=1, tau=None):
        return {"art": art, "gesamt": gesamt, "gesamt_se": se, "runden": gesamt / kk, "runden_se": se / kk, "k": kk, "tau": tau}

    return {"zeilen": [z("ein", ein), z("k", kz, 4), z("tau", tz, 1, 9)], "k": 4, "tau": 9, "plan": {4: {"runden": 10, "unten": 9}}}


def test_gegner_verdikt_je_fall():
    kind, text = ev.verdict_gegner("F", _geg(100, 70, 60))
    assert kind == "success" and "weniger" in text and "60,00 gegen 70,00" in text and "10 Runden" in text and "1,8-Fache" in text
    kind, text = ev.verdict_gegner("F", _geg(100, 70, 71))
    assert kind == "success" and "gleichauf" in text
    kind, text = ev.verdict_gegner("F", _geg(100, 70, 80))
    assert kind == "warning" and "**mehr**" in text
    kind, text = ev.verdict_gegner("F", _geg(100, 101, 99.5))
    assert kind == "info" and "weder eine getestete Läuferzahl noch ein getesteter Rücksprung" in text


def test_satz_ueber_die_groesseren_netze_zaehlt_jede_art():
    def z(art, tau, kk):
        return {"tau_gegen_k": art, "tau_gesamt": tau, "k_gesamt": kk}

    text = ev.satz_fuenf_netze([z("weniger", 90, 100)] * 3 + [z("gleichauf", 99.8, 100), z("mehr", 100.6, 100)])
    assert "Auf den 5 größeren Netzen" in text and "auf 3 weniger Gesamtschritte" in text and "auf 1 nicht unterscheidbar viele (Unterschied der Mittel höchstens 0,2 %)" in text
    assert "auf 1 mehr (um höchstens 0,6 %)" in text
    nur = ev.satz_fuenf_netze([z("weniger", 90, 100)] * 5)
    assert "mehr (um" not in nur and "unterscheidbar" not in nur


def test_formate():
    assert ev.de(1234567.891, 1) == "1 234 567,9" and ev.ganz(12345.4) == "12 345"
    assert ev.zeit(22.321) == "22,32" and ev.zeit(300.04) == "300,0" and ev.zeit(2423.2) == "2 423"
    assert ev.prozent(0.304, 1) == "30,4 %" and ev.mit_intervall(100.0, 0.0) == "100,0" and ev.mit_intervall(100.0, 1.0) == "100,0 ± 1,96"
