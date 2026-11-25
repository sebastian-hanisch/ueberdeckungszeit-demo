"""Presets und Permalink-Regeln: Vollständigkeit, gültige Werte, Standard-Preset = Standardeinstellungen, Einrasten."""

import udz_constants as C
import udz_presets as P
import udz_szenario as S


def test_jedes_preset_hat_hilfe_und_alle_schluessel():
    assert set(C.PRESETS) == set(C.PRESET_HELP)
    for name, preset in C.PRESETS.items():
        assert set(preset) == set(P.PRESET_KEYS), name
        assert C.PRESET_HELP[name]


def test_preset_werte_sind_gueltig():
    for name, preset in C.PRESETS.items():
        assert preset["netz"] in C.NETZE and preset["k"] in C.K_WERTE and preset["nsaele"] in C.SAELE_GROESSEN
        assert C.A_MIN <= preset["a"] <= C.A_MAX and 0 <= preset["seed"] <= C.SEED_MAX
        assert 0 <= preset["start"] < S.netz_fuer(preset["netz"], preset["a"], preset["nsaele"]).n, name


def test_preset_starts_sind_die_benannten_plaetze():
    assert C.PRESETS["Handnetz zwei Hallen"]["start"] == 2
    assert S.baue(C.NETZ_HALLEN, 8).knoten[C.TUERPLATZ_8] == "L(4,7)"
    assert S.baue(C.NETZ_SAELE, 65).knoten[32] == "F"
    assert S.baue(C.NETZ_SAELE, 65).knoten[0] == "A0"


def test_standard_ist_das_erste_preset():
    erstes = next(iter(C.PRESETS.values()))
    assert {k: spec.default for k, spec in P.SETTING_SPECS.items()} == erstes


def test_einrasten_begrenzt_zahlen_und_verwirft_unbekannte_auswahl():
    spec = P.SETTING_SPECS
    assert P._eingerastet(spec["a"], 99) == C.A_MAX and P._eingerastet(spec["a"], -1) == C.A_MIN
    assert P._eingerastet(spec["netz"], "nirgends") is None and P._eingerastet(spec["k"], 3) is None and P._eingerastet(spec["k"], 16) == 16
    assert P._eingerastet(spec["nsaele"], 65) == 65 and P._eingerastet(spec["nsaele"], 64) is None


def test_standardstart_je_netz():
    assert S.standardstart(C.NETZ_HALLEN, 8, 65) == C.TUERPLATZ_8
    assert S.standardstart(C.NETZ_SAELE, 8, 129) == 64
    for netz in C.NETZE:
        assert 0 <= S.standardstart(netz, 3, 17) < S.netz_fuer(netz, 3, 17).n
