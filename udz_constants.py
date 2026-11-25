"""Feste Annahmen, Reglergrenzen, Zufalls-Seeds und Messraster (Standardmuster aus dem Demo-Portfolio)."""

# --- Netze -----------------------------------------------------------------------------------------------------------------------------------

NETZ_HAND, NETZ_WEG3, NETZ_KREIS4, NETZ_FLUR = "hand", "weg3", "kreis4", "flur"
NETZ_HALLEN, NETZ_SAELE = "hallen", "saele"
NETZ_STICH, NETZ_SAAL14, NETZ_STERN14, NETZ_KREIS14, NETZ_WEG14 = "stichgang", "saal14", "stern14", "kreis14", "weg14"
NETZE = (NETZ_HAND, NETZ_KREIS4, NETZ_WEG3, NETZ_FLUR, NETZ_HALLEN, NETZ_SAELE, NETZ_STICH, NETZ_SAAL14, NETZ_STERN14, NETZ_KREIS14, NETZ_WEG14)
NETZ_TEXT = {
    NETZ_HAND: "Handnetz „zwei Hallen“ (6 Plätze)",
    NETZ_KREIS4: "4-Kreis (4 Plätze)",
    NETZ_WEG3: "Weg a–m–b (3 Plätze)",
    NETZ_FLUR: "Zwei Hallen mit Flurknoten (7 Plätze)",
    NETZ_HALLEN: "Zwei Gitterhallen a×a mit einer Tür",
    NETZ_SAELE: "Zwei Säle mit Flurknoten (Hantel nach Alon u. a.)",
    NETZ_STICH: "Saal mit Stichgang 9 + 5",
    NETZ_SAAL14: "Vollständiger Saal (14 Plätze)",
    NETZ_STERN14: "Stern (14 Plätze)",
    NETZ_KREIS14: "Kreis (14 Plätze)",
    NETZ_WEG14: "Weg (14 Plätze)",
}
TABELLE_NETZE = (NETZ_SAAL14, NETZ_STERN14, NETZ_KREIS14, NETZ_WEG14, NETZ_STICH)   # Netze der Matthews-Tabelle (je 14 Plätze)

A_MIN, A_MAX, DEFAULT_A = 2, 8, 8
SAELE_GROESSEN = (17, 33, 65, 129)
DEFAULT_SAELE = 65

EXAKT_START_MAX = 18           # Überdeckungszeit je Start exakt (Zustandsraum)
EXAKT_K_MAX = 8                # mehrere Läufer exakt (Ein-/Ausschluss) bis 8 Plätze
ALLE_KANTEN_MAX = 14           # Tabelle „alle neuen Kanten“ wird bis 14 Plätze live gerechnet
MENGEN_MAX = 18                # Mengenschranke durch Aufzählung aller Mengen

K_WERTE = (1, 2, 4, 8, 16, 32)
LIVE_LAEUFE = 200              # Probeläufe für freie Starts auf großen Netzen
VERLAUF_MAX = 300_000          # Deckel für den gezeigten Einzellauf (Runden)

SEED_MAX = 999999
DEFAULT_SEED = 41

# --- Vorrechnen: Läufe je Zelle ------------------------------------------------------------------------------------------------------------

R_SICHTEN = 4000               # Sichtung aller Startplätze (Gitterhallen a >= 4)
SICHTEN_BESTE = 5              # so viele der längsten Starts werden mit frischen Zufalls-Seeds nachgemessen
R_WERT = 40000                 # Standard je gemessener Zelle
R_WERT_GROSS = 100000          # zwei Hallen 8×8 (Türplatz, ferne Ecke) und Weg 128: enge Intervalle für die Gegner
R_WAHL = 20000                 # Auswahl von k und tau im Raster (eigene Zufalls-Seeds)
R_WAHL_LANG = {"weg128": 10000}   # Weg 128: die Läufe sind sehr lang, deshalb halb so viele je Rasterwert


def laeufe_wahl(fall: str) -> int:
    return R_WAHL_LANG.get(fall, R_WAHL)

R_POLE = 20000                 # Gegenpole
R_TUER = 40000                 # „eine Tür mehr“

# --- Gegner: Fälle und Raster ---------------------------------------------------------------------------------------------------------------

GEGNER_FAELLE = ("saele65_F", "saele129_F", "barbell", "weg128", "hallen8_tuer", "hallen8_ecke", "saele65_i", "flur_mitte", "hand_tuer", "hand_ecke")
GEGNER_TEXT = {
    "saele65_F": "Zwei Säle mit Flurknoten (65), Start Flurmitte",
    "saele129_F": "Zwei Säle mit Flurknoten (129), Start Flurmitte",
    "barbell": "Barbell 48/32/48, Start in der Mitte des Wegs",
    "weg128": "Weg mit 128 Plätzen, Start Platz 63",
    "hallen8_tuer": "Zwei Hallen 8×8, Start Türplatz",
    "hallen8_ecke": "Zwei Hallen 8×8, Start ferne Ecke",
    "saele65_i": "Zwei Säle mit Flurknoten (65), Start Saal-Innenplatz",
    "flur_mitte": "Zwei Hallen mit Flurknoten (7), Start Flurmitte (ohne Zufall)",
    "hand_tuer": "Handnetz „zwei Hallen“, Start Türplatz (ohne Zufall)",
    "hand_ecke": "Handnetz „zwei Hallen“, Start Hallenecke (ohne Zufall)",
}
EXAKTE_FAELLE = ("flur_mitte", "hand_tuer", "hand_ecke")
FUENF_NETZE = ("saele65_F", "saele129_F", "barbell", "weg128", "hallen8_tuer")       # die größeren Netze mit Gewinn der Kernbotschaft
GEGNER_K = {
    "saele65_F": (2, 4, 8, 12, 16, 20, 24, 28, 32, 40, 48, 56, 64),
    "saele129_F": (8, 12, 16, 24, 32, 40, 48, 56, 64, 80),
    "barbell": (2, 4, 6, 8, 10, 12, 14, 16, 20, 24),
    "weg128": (2, 3, 4, 5, 6, 7, 8, 10),
    "hallen8_tuer": tuple(range(2, 17)),
    "hallen8_ecke": tuple(range(2, 17)),
    "saele65_i": (2, 4, 8, 16, 32, 64),
    "flur_mitte": tuple(range(2, 25)),
    "hand_tuer": tuple(range(2, 17)),
    "hand_ecke": tuple(range(2, 17)),
}
GEGNER_TAU = {
    "saele65_F": (4, 6, 8, 10, 12, 14, 16, 20, 24, 28, 32, 40, 48, 64, 96),
    "saele129_F": (8, 12, 16, 20, 24, 28, 32, 40, 48, 64, 96, 128, 192),
    "barbell": (192, 256, 320, 384, 448, 512, 640, 768, 1024, 1536, 2048, 4096, 8192),
    "weg128": (1024, 1536, 2048, 3072, 4096, 5120, 6144, 8192, 12288, 16384, 32768),
    "hallen8_tuer": (64, 128, 192, 256, 320, 448, 640, 896, 1280, 1792, 2560, 4096, 8192, 16384, 32768),
    "hallen8_ecke": (64, 128, 192, 256, 320, 448, 640, 896, 1280, 1792, 2560, 4096, 8192, 16384, 32768),
    "saele65_i": (8, 16, 32, 64, 128, 256, 512, 1024, 2048, 4096, 8192, 16384),
    "flur_mitte": tuple(range(1, 81)),
    "hand_tuer": tuple(range(1, 81)),
    "hand_ecke": tuple(range(1, 81)),
}
ATLAS_TAU_MAX = 80
ATLAS_K_MAX = 12

# --- Presets --------------------------------------------------------------------------------------------------------------------------------

def _preset(netz, start, k, a=DEFAULT_A, nsaele=DEFAULT_SAELE, seed=DEFAULT_SEED):
    return {"netz": netz, "a": a, "nsaele": nsaele, "start": start, "k": k, "seed": seed}


TUERPLATZ_8 = 4 * 8 + 7        # linke Halle, Zeile 4, Spalte 7
PRESETS = {
    "Handnetz zwei Hallen": _preset(NETZ_HAND, 2, 1),
    "4-Kreis plus Diagonale": _preset(NETZ_KREIS4, 0, 1),
    "Zwei Hallen 8×8, viele Läufer an der Tür": _preset(NETZ_HALLEN, TUERPLATZ_8, 8),
    "Zwei Säle mit Flurknoten, Start in der Mitte": _preset(NETZ_SAELE, 32, 8),
    "Dieselben Säle, Start im Saal": _preset(NETZ_SAELE, 0, 8),
}
PRESET_HELP = {
    "Handnetz zwei Hallen": "Zwei Dreiecke mit einer Tür, Start am Türplatz 2, ein Läufer. Alles wird ohne Zufall gerechnet.",
    "4-Kreis plus Diagonale": "Der 4-Kreis; in Experiment 2 ist die Diagonale 0–2 als neue Verbindung eingestellt.",
    "Zwei Hallen 8×8, viele Läufer an der Tür": "Zwei Gitterhallen mit je 64 Plätzen, acht Läufer starten am Türplatz.",
    "Zwei Säle mit Flurknoten, Start in der Mitte": "65 Plätze: zwei vollständige Säle und ein Flurknoten; acht Läufer starten in der Flurmitte.",
    "Dieselben Säle, Start im Saal": "Dasselbe Netz, aber acht Läufer starten auf einem Innenplatz eines Saals.",
}

# --- Farben ------------------------------------------------------------------------------------------------------------------------------------

FARBE_BESUCHT = "#2F6B65"
FARBE_OFFEN = "#d5d9de"
FARBE_LAEUFER = "#d1495b"
FARBE_A = "#2F6B65"
FARBE_B = "#d1495b"
FARBE_C = "#e69f00"
FARBE_GRAU = "#9aa5b1"
