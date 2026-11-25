"""Permalink (Begrenzen), Presets, Netzwechsel und Zufalls-Seed-Button (Standardmuster aus dem Demo-Portfolio).

Jeder Regler der Seitenleiste hat einen Eintrag in SETTING_SPECS. Werte aus der Adresszeile werden begrenzt (Zahlen) oder verworfen (unbekannte Auswahl).
Der Startplatz hängt am Netz: bei einem Netzwechsel setzt ein Callback ihn auf den Standardstart, und `passe_start_an` hält ihn vor dem Zeichnen gültig."""

import random
from dataclasses import dataclass

import streamlit as st

import udz_constants as C
import udz_szenario as S


@dataclass(frozen=True)
class SettingSpec:
    url_param: str
    caster: type
    default: object
    lo: float | None = None
    hi: float | None = None
    options: tuple | None = None      # erlaubte Werte (Auswahllisten)


_STANDARD = C.PRESETS[next(iter(C.PRESETS))]
_KNOTEN_MAX = max(2 * C.A_MAX * C.A_MAX, max(C.SAELE_GROESSEN)) - 1

SETTING_SPECS = {
    "netz": SettingSpec("netz", str, _STANDARD["netz"], options=C.NETZE),
    "a": SettingSpec("a", int, _STANDARD["a"], C.A_MIN, C.A_MAX),
    "nsaele": SettingSpec("n", int, _STANDARD["nsaele"], options=C.SAELE_GROESSEN),
    "start": SettingSpec("start", int, _STANDARD["start"], 0, _KNOTEN_MAX),
    "k": SettingSpec("k", int, _STANDARD["k"], options=C.K_WERTE),
    "seed": SettingSpec("seed", int, _STANDARD["seed"], 0, C.SEED_MAX),
}
PRESET_KEYS = {key: key for key in SETTING_SPECS}


def init_session_state_defaults():
    for state_key, spec in SETTING_SPECS.items():
        if state_key not in st.session_state:
            st.session_state[state_key] = spec.default


def bounds(state_key):
    spec = SETTING_SPECS[state_key]
    return spec.lo, spec.hi


def _eingerastet(spec: SettingSpec, wert):
    """Wert auf die Grenzen begrenzt; unbekannte Auswahl gibt None."""
    if spec.options is not None:
        return wert if wert in spec.options else None
    if spec.lo is not None:
        wert = max(spec.lo, wert)
    if spec.hi is not None:
        wert = min(spec.hi, wert)
    return wert


def load_permalink_settings():
    """Einmal je Sitzung: Werte aus der Adresszeile übernehmen. Nennt die Adresszeile ein Netz oder eine Größe, aber keinen Start, gilt dessen Standardstart."""
    if "permalink_loaded" in st.session_state:
        return
    qp = st.query_params
    gelesen = {}
    for state_key, spec in SETTING_SPECS.items():
        if spec.url_param in qp:
            try:
                wert = _eingerastet(spec, spec.caster(qp[spec.url_param]))
            except (ValueError, TypeError):
                continue
            if wert is not None:
                gelesen[state_key] = wert
    st.session_state.update(gelesen)
    if gelesen.keys() & {"netz", "a", "nsaele"} and "start" not in gelesen:
        st.session_state["start"] = S.standardstart(gelesen.get("netz", SETTING_SPECS["netz"].default), gelesen.get("a", C.DEFAULT_A),
                                                    gelesen.get("nsaele", C.DEFAULT_SAELE))
    st.session_state["permalink_loaded"] = True


def passe_start_an():
    """Vor dem Zeichnen: gibt es den Startplatz im aktuellen Netz nicht, gilt der Standardstart."""
    netz, a, nsaele = st.session_state["netz"], int(st.session_state["a"]), int(st.session_state["nsaele"])
    n = S.netz_fuer(netz, a, nsaele).n
    wert = int(st.session_state["start"])
    st.session_state["start"] = wert if 0 <= wert < n else S.standardstart(netz, a, nsaele)


def netz_gewechselt():
    """Callback von Netz und Größe: Start auf den Standardstart des Netzes."""
    st.session_state["start"] = S.standardstart(st.session_state["netz"], int(st.session_state["a"]), int(st.session_state["nsaele"]))


def groesse_gewechselt(netz_der_groesse: str):
    """Callback eines Größenreglers: nur wenn er zum gewählten Netz gehört, ändert sich der Start."""
    if st.session_state["netz"] == netz_der_groesse:
        netz_gewechselt()


def sync_query_params(values):
    """`values`: {state_key: aktueller Wert}; die Adresszeile spiegelt die Konfiguration."""
    try:
        for state_key, value in values.items():
            st.query_params[SETTING_SPECS[state_key].url_param] = str(value)
    except Exception:
        pass


def apply_preset(name):
    for key, state_key in PRESET_KEYS.items():
        if key in C.PRESETS[name]:
            st.session_state[state_key] = C.PRESETS[name][key]


def aktives_preset():
    """Name des Presets, dessen Werte GENAU den aktuellen Einstellungen entsprechen, sonst None.

    Zustandslos: verglichen wird jeder Regler aus SETTING_SPECS (ein Preset ohne Eintrag für einen Regler meint dessen
    Standardwert) mit dem Session State. Ein später ergänzter Regler braucht nur seinen Eintrag in SETTING_SPECS,
    dann hebt auch seine Änderung die Markierung auf (tests/test_layout.py prüft das für jeden Regler)."""
    preset_key_of = {state_key: key for key, state_key in PRESET_KEYS.items()}
    for name, preset in C.PRESETS.items():
        if all(
            st.session_state.get(state_key, spec.default) == preset.get(preset_key_of.get(state_key), spec.default)
            for state_key, spec in SETTING_SPECS.items()
        ):
            return name
    return None


def sidebar_presets():
    """Schnellstart oben in der Seitenleiste; das aktive Preset ist hervorgehoben (`type="primary"`)."""
    if not C.PRESETS:
        return
    st.header("🎯 Schnellstart")
    st.caption("Ein Beispielszenario laden:")
    aktiv = aktives_preset()
    for name in C.PRESETS:
        st.button(
            name, width="stretch", on_click=apply_preset, args=(name,), help=C.PRESET_HELP.get(name, ""), key=f"preset_{name}",
            type="primary" if aktiv == name else "secondary",
        )


def randomize_seed():
    st.session_state["seed"] = random.randint(0, C.SEED_MAX)
