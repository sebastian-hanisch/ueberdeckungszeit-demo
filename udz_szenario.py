"""Netzwahl der App: aus Netz und Größe das Netz, die benannten Vergleichsstarts und die Netze der Gegner-Fälle (ohne Streamlit)."""

import hashlib
from functools import lru_cache

import udz_constants as C
import udz_netze as N


def groesse_von(netz: str, a: int, nsaele: int):
    """Die Größe, die für dieses Netz zählt: a (Gitterhallen), n (Säle), sonst None."""
    if netz == C.NETZ_HALLEN:
        return int(a)
    if netz == C.NETZ_SAELE:
        return int(nsaele)
    return None


@lru_cache(maxsize=64)
def baue(netz: str, groesse=None) -> N.Netz:
    if netz == C.NETZ_HAND:
        return N.handnetz()
    if netz == C.NETZ_KREIS4:
        return N.vierkreis()
    if netz == C.NETZ_WEG3:
        return N.weg_amb()
    if netz == C.NETZ_FLUR:
        return N.flurnetz()
    if netz == C.NETZ_HALLEN:
        return N.zwei_hallen(groesse)
    if netz == C.NETZ_SAELE:
        return N.saele_mit_flurknoten(groesse)
    if netz == C.NETZ_STICH:
        return N.saal_mit_stichgang(9, 5)
    if netz == C.NETZ_SAAL14:
        return N.saal(14)
    if netz == C.NETZ_STERN14:
        return N.stern(14)
    if netz == C.NETZ_KREIS14:
        return N.kreis(14)
    if netz == C.NETZ_WEG14:
        return N.weg(14)
    raise ValueError(f"unbekanntes Netz {netz}")


def netz_fuer(netz: str, a: int, nsaele: int) -> N.Netz:
    return baue(netz, groesse_von(netz, a, nsaele))


def vergleichsstarts(netz: str, groesse=None) -> list:
    """[(Kürzel, Platznummer, Name)] der benannten Starts; die ersten zwei stehen in Experiment 3 nebeneinander, der erste ist der Standardstart."""
    if netz == C.NETZ_HAND:
        return [("tuer", 2, "Türplatz 2"), ("ecke", 0, "Hallenecke 0")]
    if netz == C.NETZ_KREIS4:
        return [("p0", 0, "Platz 0 (alle Plätze sind gleichwertig)")]
    if netz == C.NETZ_WEG3:
        return [("m", 1, "Mitte m"), ("ende", 0, "Ende a")]
    if netz == C.NETZ_FLUR:
        return [("mitte", 6, "Flurmitte"), ("ecke", 0, "Hallenecke 0")]
    if netz == C.NETZ_HALLEN:
        return [("tuer", N.tuerknoten(groesse), "Türplatz"), ("ecke", N.ferne_ecke(groesse), "ferne Ecke")]
    if netz == C.NETZ_SAELE:
        m = (groesse - 1) // 2
        return [("F", m, "Flurmitte"), ("i", 0, "Saal-Innenplatz"), ("a", m - 1, "Anschlussplatz")]
    if netz == C.NETZ_STICH:
        return [("saal", 0, "Saalplatz S0"), ("ende", 13, "Ende des Stichgangs")]
    if netz == C.NETZ_SAAL14:
        return [("p0", 0, "ein Saalplatz (alle gleichwertig)")]
    if netz == C.NETZ_STERN14:
        return [("mitte", 0, "Mitte"), ("blatt", 1, "Blatt")]
    if netz == C.NETZ_KREIS14:
        return [("p0", 0, "ein Platz (alle gleichwertig)")]
    if netz == C.NETZ_WEG14:
        return [("innen", 7, "innerer Platz 7"), ("ende", 0, "Ende 0")]
    raise ValueError(f"unbekanntes Netz {netz}")


def standardstart(netz: str, a: int, nsaele: int) -> int:
    return vergleichsstarts(netz, groesse_von(netz, a, nsaele))[0][1]


def netz_schluessel(netz: str, groesse=None) -> str:
    return netz if groesse is None else f"{netz}{groesse}"


def zell_seed(*teile) -> int:
    """Fester Zufalls-Seed je Messzelle, aus den Bezeichnungen abgeleitet (SHA-256, plattformgleich)."""
    text = "|".join(str(t) for t in ("udz-2026",) + teile)
    return int.from_bytes(hashlib.sha256(text.encode("utf-8")).digest()[:8], "big")


def gegner_fall(fall: str):
    """(Netz, Startplatz) eines Gegner-Falls."""
    if fall == "saele65_F":
        return baue(C.NETZ_SAELE, 65), 32
    if fall == "saele129_F":
        return baue(C.NETZ_SAELE, 129), 64
    if fall == "saele65_i":
        return baue(C.NETZ_SAELE, 65), 0
    if fall == "barbell":
        return N.barbell(48, 32), N.barbell_mitte(48, 32)
    if fall == "weg128":
        return N.weg(128), 63
    if fall == "hallen8_tuer":
        return baue(C.NETZ_HALLEN, 8), N.tuerknoten(8)
    if fall == "hallen8_ecke":
        return baue(C.NETZ_HALLEN, 8), N.ferne_ecke(8)
    if fall == "flur_mitte":
        return baue(C.NETZ_FLUR), 6
    if fall == "hand_tuer":
        return baue(C.NETZ_HAND), 2
    if fall == "hand_ecke":
        return baue(C.NETZ_HAND), 0
    raise ValueError(f"unbekannter Fall {fall}")


def fall_fuer_einstellung(netz: str, groesse, start: int):
    """Der Gegner-Fall, der zu Netz und Start der Seitenleiste passt, sonst None."""
    zuordnung = {
        (C.NETZ_SAELE, 65, 32): "saele65_F", (C.NETZ_SAELE, 129, 64): "saele129_F", (C.NETZ_SAELE, 65, 0): "saele65_i",
        (C.NETZ_HALLEN, 8, N.tuerknoten(8)): "hallen8_tuer", (C.NETZ_HALLEN, 8, 0): "hallen8_ecke",
        (C.NETZ_FLUR, None, 6): "flur_mitte", (C.NETZ_HAND, None, 2): "hand_tuer", (C.NETZ_HAND, None, 0): "hand_ecke",
    }
    return zuordnung.get((netz, groesse, start))
