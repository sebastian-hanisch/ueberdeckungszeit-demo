"""AppTest: Standard, jeder Button, jedes Preset mit Verdikt, Permalink, wirksame Regler an den Rändern, alle vier Experimente, jedes Netz."""

import os

import pytest
from streamlit.testing.v1 import AppTest

import udz_constants as C

APP_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "app.py")
TIMEOUT = int(os.environ.get("APPTEST_TIMEOUT", "300"))
EXPERIMENTE = ["🔬 Experiment 1: Bis alle besucht sind", "🔬 Experiment 2: Eine Verbindung mehr", "🔬 Experiment 3: Viele Läufer vom selben Start",
               "🔬 Experiment 4: Gegner mit mehr Wissen – fester Rücksprung und Karte"]


def _fresh(**query) -> AppTest:
    at = AppTest.from_file(APP_PATH)
    for k, v in query.items():
        at.query_params[k] = str(v)
    at.run(timeout=TIMEOUT)
    assert not at.exception, [str(e) for e in at.exception]
    return at


def _texte(at) -> str:
    teile = [e.value for art in ("success", "info", "warning") for e in getattr(at, art)]
    return "\n".join(teile)


def test_standard_zeigt_alle_vier_experimente_und_abschnitte():
    at = _fresh()
    assert [s.value for s in at.subheader if s.value.startswith("🔬")] == EXPERIMENTE
    labels = [e.label for e in at.expander]
    for titel in ("So funktioniert die Überdeckungszeit", "⚠️ Annahmen, Grenzen und bekannte Probleme", "📐 Mathematische Formulierung"):
        assert titel in labels
    assert not at.error


def test_jeder_button_laeuft_ohne_fehler():
    labels = [b.label for b in _fresh().button]
    assert labels
    for index, label in enumerate(labels):
        at = _fresh()
        at.button[index].click().run(timeout=TIMEOUT)
        assert not at.exception, (label, [str(e) for e in at.exception])


ERWARTET = {
    "Handnetz zwei Hallen": ["Auf dem Netz „Handnetz zwei Hallen“ liegt", "Die neue Verbindung 0 – 5 verkürzt",
                             "Auf dem Netz „Handnetz zwei Hallen“ verkürzt jede der 8 möglichen neuen Verbindungen die Überdeckungszeit des schlechtesten Starts."],
    "4-Kreis plus Diagonale": ["Die neue Verbindung 0 – 2 **verlängert** die Überdeckungszeit des schlechtesten Starts: 6,00 → 6,80"],
    "Zwei Hallen 8×8, viele Läufer an der Tür": ["Auf dem Netz „Zwei Hallen 8×8“ liegt die obere Schranke beim 2,7-Fachen","Start Türplatz: S_8/8 = 1,0", "Start ferne Ecke: S_8/8 = 0,69", "Negativbefund",
                                                 "Zwei Hallen 8×8, Start Türplatz: "],
    "Zwei Säle mit Flurknoten, Start in der Mitte": ["Start Flurmitte: S_8/8 = 5,5", "weniger als ein Fünftel", "Start Saal-Innenplatz: S_8/8 = 0,79"],
    "Dieselben Säle, Start im Saal": ["Start Saal-Innenplatz: S_8/8 = 0,79", "mehr** Schritte", "Zwei Säle mit Flurknoten (65), Start Saal-Innenplatz"],
}


@pytest.mark.parametrize("name", list(C.PRESETS))
def test_jedes_preset_zeigt_die_erwartete_verdikt_zeile(name):
    at = _fresh()
    at.sidebar.button(key=f"preset_{name}").click().run(timeout=TIMEOUT)
    assert not at.exception, [str(e) for e in at.exception]
    alles = _texte(at) + "\n" + "\n".join(w.value for w in at.warning)
    for teil in ERWARTET[name]:
        assert teil in alles, (name, teil, alles)
    assert not at.error


def test_permalink_stellt_netz_start_und_laeufer_ein():
    at = _fresh(netz="saele", n=33, k=16)
    assert at.sidebar.selectbox(key="netz").value == "saele" and at.sidebar.selectbox(key="nsaele").value == 33
    assert at.sidebar.selectbox(key="start").value == 16               # Standardstart (Flurmitte) von n = 33
    assert at.sidebar.select_slider(key="k").value == 16
    at = _fresh(netz="unbekannt", a=99, start=5000, k=3)
    assert at.sidebar.selectbox(key="netz").value == C.PRESETS[next(iter(C.PRESETS))]["netz"]
    assert at.sidebar.select_slider(key="k").value == 1


@pytest.mark.parametrize("netz", C.NETZE)
def test_jedes_netz_laeuft(netz):
    at = _fresh(netz=netz, a=3, n=17, k=4)
    assert not at.error


@pytest.mark.parametrize("a", [C.A_MIN, 3, 4, C.A_MAX])
def test_hallengroessen_mit_experiment_2(a):
    at = _fresh(netz="hallen", a=a, k=2)
    assert not at.error


@pytest.mark.parametrize("n", C.SAELE_GROESSEN)
def test_saalgroessen(n):
    _fresh(netz="saele", n=n, k=32)


def test_ein_lauf_nach_einer_runde_steht_in_der_einzahl():
    at = _fresh(netz="weg3", start=1, k=32)
    assert any("alle 3 Plätze nach **1 Runde** (32 Gesamtschritten)" in s.value for s in at.success), [s.value for s in at.success]


@pytest.mark.parametrize("query,teil", [
    ({"netz": "weg3"}, "Auf dem Netz „Weg a–m–b“ verkürzt die einzige mögliche neue Verbindung die Überdeckungszeit des schlechtesten Starts."),
    ({"netz": "hallen", "a": 3}, "Auf zwei 3×3-Hallen verlängern 44 der 48 neuen Verbindungen innerhalb einer Halle die Überdeckungszeit"),
    ({"netz": "hallen", "a": 2}, "Auf zwei 2×2-Hallen verlängert jede der 4 neuen Verbindungen innerhalb einer Halle die Überdeckungszeit"),
    ({"netz": "kreis4"}, "Auf dem Netz „4-Kreis“ verlängert jede der 2 möglichen neuen Verbindungen die Überdeckungszeit"),
])
def test_alle_neuen_verbindungen_als_ganzer_satz(query, teil):
    assert teil in _texte(_fresh(**query))


def test_negativbefund_ab_der_fernen_ecke_nennt_die_getesteten_laeuferzahlen():
    text = _texte(_fresh(netz="hallen", a=8, k=8))
    assert "Ab der fernen Ecke sparte keine der getesteten Läuferzahlen (k = 2 bis 16 und 32) Gesamtschritte." in text
    assert "bringen mehr Läufer nichts ein" not in text


def test_freier_start_auf_grossem_netz_zeigt_probelaeufe():
    at = _fresh(netz="hallen", a=8, start=5, k=4)
    assert any("Probeläufe mit Ihrem Zufalls-Seed" in c.value for c in at.caption)


def test_netzwechsel_setzt_den_standardstart():
    at = _fresh()
    at.sidebar.selectbox(key="netz").set_value("hallen").run(timeout=TIMEOUT)
    assert at.sidebar.selectbox(key="start").value == C.TUERPLATZ_8
    at.sidebar.slider(key="a").set_value(4).run(timeout=TIMEOUT)
    assert at.sidebar.selectbox(key="start").value == 4 * 2 + 3           # Türplatz bei a = 4
    assert not at.exception


def test_runde_regler_und_zufalls_seed():
    at = _fresh()
    runde = next(s for s in at.slider if s.label == "Runde")
    runde.set_value(runde.max).run(timeout=TIMEOUT)
    assert not at.exception and any("alle 6 Plätze" in s.value for s in at.success)
    runde = next(s for s in at.slider if s.label == "Runde")
    runde.set_value(0).run(timeout=TIMEOUT)
    assert at.metric[2].value == "1 von 6"
    at.sidebar.number_input(key="seed").set_value(7).run(timeout=TIMEOUT)
    assert not at.exception


def test_jeder_gegner_fall_im_experiment_4():
    at = _fresh()
    for fall in C.GEGNER_FAELLE:
        box = next(s for s in at.selectbox if s.label == "Fall")
        box.set_value(fall).run(timeout=TIMEOUT)
        assert not at.exception, (fall, [str(e) for e in at.exception])
        assert any(e.value.startswith(C.GEGNER_TEXT[fall] + ":") for art in ("success", "info", "warning") for e in getattr(at, art)), fall


def test_auswahl_der_tuer_und_der_neuen_verbindung():
    at = _fresh(netz="hallen", a=8)
    box = next(s for s in at.selectbox if s.label.startswith("Eine Tür mehr"))
    box.set_value("alle").run(timeout=TIMEOUT)
    assert not at.exception and any("mit einer Tür in jeder Zeile" in e.value for art in ("success", "info", "warning") for e in getattr(at, art))
    at = _fresh(netz="hallen", a=2)
    box = next(s for s in at.selectbox if s.label == "Neue Verbindung")
    box.select_index(0).run(timeout=TIMEOUT)
    assert not at.exception
    assert any("jede der 4 neuen Verbindungen innerhalb einer Halle" in w.value for w in at.warning)


def test_kernfragen_und_footer():
    at = _fresh()
    markdown = "\n".join(m.value for m in at.markdown)
    assert "Auf den 5 größeren Netzen" in markdown
    for frage in ("Wann nützt die Matthews-Klammer?", "Kann eine neue Verbindung die Zeit verlängern?", "Sparen viele Läufer Schritte, und von wo?",
                  "Was leisten fester Rücksprung und Karte?"):
        assert frage in markdown
    assert "sebastianhanisch.net" in "\n".join(c.value for c in at.caption)
