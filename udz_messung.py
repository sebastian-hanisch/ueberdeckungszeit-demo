"""Eine Messzelle (Netz, Start, Läuferzahl oder Rücksprung) mit festem Zufalls-Seed: dieselbe Funktion für das Vorrechnen und für die Stichproben der Tests."""

import udz_constants as C
import udz_irrfahrt_sim as S
import udz_netze as N
import udz_szenario as Z

GROSS_ZELLEN = ("weg128", "hallen8")


def laeufe_wert(netz_key: str) -> int:
    """Zahl der Läufe je bewerteter Zelle."""
    return C.R_WERT_GROSS if netz_key in GROSS_ZELLEN else C.R_WERT


def zelle(zweck: str, netz_key: str, g: N.Netz, start: int, k: int, laeufe: int, tau: int = None, max_runden: int = 3_000_000) -> dict:
    """Mittel, Standardfehler und Median der Runden. zweck ('wahl', 'wert', 'sicht', …) trennt die Zufalls-Seeds von Auswahl und Bewertung."""
    seed = Z.zell_seed(zweck, netz_key, start, k, 0 if tau is None else tau)
    runden = S.simuliere_ueberdeckung(g, start, k, laeufe, seed, tau=tau, max_runden=max_runden)
    ergebnis = {"k": k, "tau": tau, "laeufe": laeufe, "fertig": bool((runden >= 0).all())}
    if ergebnis["fertig"]:
        ergebnis.update({kk: v for kk, v in S.kennzahlen(runden, k).items() if kk in ("runden", "se", "median")})
    return ergebnis


def wert(netz_key: str, g: N.Netz, start: int, k: int = 1, tau: int = None) -> dict:
    """Bewertete Zelle (Bewertungs-Seed, Standard-Zahl der Läufe)."""
    return zelle("wert", netz_key, g, start, k, laeufe_wert(netz_key), tau)
