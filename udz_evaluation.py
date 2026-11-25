"""Kennzahlen der Experimente und Verdikte als reine Funktionen (ohne Streamlit).

Quellen der Zahlen: ohne Zufall gerechnet (`udz_exakt`, `udz_hantel`, `udz_matthews`, Karten-Pläne aus `udz_plan`) oder gemessen und gespeichert (`udz_daten`).
Gemessene Mittel haben ein 95-%-Intervall (Mittel ± 1,96 Standardfehler). Zwei gemessene Werte gelten als unterscheidbar, wenn sich ihre Intervalle nicht überschneiden.
"""

import math
from functools import lru_cache

import numpy as np

import udz_constants as C
import udz_daten as D
import udz_exakt as X
import udz_hantel as H
import udz_irrfahrt_sim as S
import udz_matthews as MT
import udz_netze as N
import udz_plan as P
import udz_szenario as Z
import udz_trefferzeit as T

Z95 = 1.96


# ----------------------------------------------------------------------------------------------------------------------------------
# Formate
# ----------------------------------------------------------------------------------------------------------------------------------

def de(x: float, stellen: int = 2) -> str:
    """Zahl mit Dezimalkomma, Tausender mit Leerzeichen."""
    return f"{x:,.{stellen}f}".replace(",", " ").replace(".", ",")


def ganz(x) -> str:
    return f"{int(round(x)):,}".replace(",", " ")


def runden_wort(n: int) -> str:
    """„1 Runde“, sonst „n Runden“."""
    return f"{ganz(n)} {'Runde' if int(round(n)) == 1 else 'Runden'}"


def zeit(t: float) -> str:
    """Eine Zeit in Schritten oder Runden: unter 100 mit zwei, unter 1 000 mit einer Nachkommastelle, darüber ganz."""
    return de(t, 2 if abs(t) < 99.995 else (1 if abs(t) < 999.95 else 0))


def prozent(x: float, stellen: int = 0) -> str:
    return f"{de(100 * x, stellen)} %"


def mit_intervall(wert: float, se: float) -> str:
    """Wert mit halber Breite des 95-%-Intervalls; ohne Streuung nur der Wert."""
    if not se:
        return zeit(wert)
    return f"{zeit(wert)} ± {zeit(Z95 * se)}"


def vergleiche(x: float, se_x: float, y: float, se_y: float) -> str:
    """'weniger', 'mehr' oder 'gleichauf': x gegen y, nach nicht überschneidenden 95-%-Intervallen (ohne Streuung: Toleranz 1e-9 relativ)."""
    tol = 1e-9 * max(abs(x), abs(y), 1.0)
    if x + Z95 * se_x < y - Z95 * se_y - tol:
        return "weniger"
    if x - Z95 * se_x > y + Z95 * se_y + tol:
        return "mehr"
    return "gleichauf"


# ----------------------------------------------------------------------------------------------------------------------------------
# Experiment 1: Überdeckungszeit je Start und Matthews-Klammer
# ----------------------------------------------------------------------------------------------------------------------------------

@lru_cache(maxsize=32)
def je_start(netz: str, groesse=None) -> dict:
    """E[Schritte eines Läufers] je Startplatz. art: 'exakt' (Zustandsraum bzw. zusammengefasste Kette) oder 'gemessen' (Sichtung aller Starts)."""
    g = Z.baue(netz, groesse)
    if g.n <= C.EXAKT_START_MAX:
        return {"art": "exakt", "werte": X.zustandsraum(g), "se": np.zeros(g.n), "laeufe": None}
    if netz == C.NETZ_SAELE:
        w = H.ueberdeckung(g.n)
        return {"art": "exakt", "werte": np.array([w[H.typ_von(g.n, i)] for i in range(g.n)]), "se": np.zeros(g.n), "laeufe": None}
    if netz == C.NETZ_HALLEN:
        d = D.laden()["hallen"][str(groesse)]
        werte, se = np.array(d["sicht_mittel"]), np.array(d["sicht_se"])
        laeufe = np.full(g.n, d["sicht_laeufe"])
        for s, c in d["bestaetigt"].items():
            werte[int(s)], se[int(s)], laeufe[int(s)] = c["runden"], c["se"], c["laeufe"]
        return {"art": "gemessen", "werte": werte, "se": se, "laeufe": laeufe}
    raise ValueError(f"für {netz} sind keine Werte je Start vorhanden")


def schlechtester_start(netz: str, groesse=None) -> dict:
    """Überdeckungszeit des schlechtesten Starts (bei Gleichstand die kleinste Platznummer; gemessen: größter nachgemessener Wert)."""
    js = je_start(netz, groesse)
    if js["art"] == "exakt":
        w = js["werte"]
        s = int(np.flatnonzero(w >= w.max() * (1 - 1e-9))[0])
        return {"start": s, "wert": float(w[s]), "se": 0.0, "art": "exakt"}
    s = int(D.laden()["hallen"][str(groesse)]["schlechtester"])
    return {"start": s, "wert": float(js["werte"][s]), "se": float(js["se"][s]), "art": "gemessen"}


@lru_cache(maxsize=32)
def treffer(netz: str, groesse=None) -> np.ndarray:
    return T.treffer_matrix(Z.baue(netz, groesse))


@lru_cache(maxsize=32)
def matthews(netz: str, groesse=None) -> dict:
    """Matthews-Klammer, bei kleinen Netzen die Mengenschranke, und die Verhältnisse zur Überdeckungszeit des schlechtesten Starts."""
    Hm = treffer(netz, groesse)
    k = MT.klammer(Hm)
    t = schlechtester_start(netz, groesse)
    erg = dict(k, t_cov=t["wert"], t_se=t["se"], t_art=t["art"], t_start=t["start"], oben_faktor=k["oben"] / t["wert"], unten_faktor=t["wert"] / k["unten"])
    if len(Hm) <= C.MENGEN_MAX:
        wert, menge = MT.mengenschranke(Hm)
        erg.update(menge_wert=wert, menge=menge, menge_faktor=t["wert"] / wert)
    return erg


def tabelle_vergleich() -> list:
    """Die Netze der Matthews-Tabelle (je 14 Plätze), ohne Zufall."""
    zeilen = []
    for netz in C.TABELLE_NETZE:
        m = matthews(netz)
        zeilen.append({"netz": netz, "t_cov": m["t_cov"], "oben_faktor": m["oben_faktor"], "unten_faktor": m["unten_faktor"], "menge_faktor": m["menge_faktor"]})
    return zeilen


def verdict_matthews(name: str, oben_faktor: float, unten_faktor: float, art: str):
    """Wie weit liegen die beiden Schranken von der Zeit des schlechtesten Starts entfernt?"""
    wort = "gemessenen" if art == "gemessen" else "berechneten"
    anfang = f"Auf dem Netz „{name}“"
    if oben_faktor < 1.005 and unten_faktor < 1.005:
        return "success", f"{anfang} sind beide Schranken genau: Sie fallen mit der {wort} Überdeckungszeit des schlechtesten Starts zusammen."
    if oben_faktor < 1.05:
        text = (f"{anfang} ist die obere Schranke fast genau (das {de(oben_faktor, 2)}-Fache), die untere liegt beim 1/{de(unten_faktor, 1)}-Fachen der {wort} "
                "Überdeckungszeit des schlechtesten Starts.")
    else:
        text = (f"{anfang} liegt die obere Schranke beim {de(oben_faktor, 1)}-Fachen, die untere beim 1/{de(unten_faktor, 1)}-Fachen der {wort} "
                "Überdeckungszeit des schlechtesten Starts.")
    kind = "success" if max(oben_faktor, unten_faktor) < 1.2 else "warning"
    return kind, text


# ----------------------------------------------------------------------------------------------------------------------------------
# Experiment 2: eine Verbindung mehr
# ----------------------------------------------------------------------------------------------------------------------------------

def laenger(nachher: float, vorher: float) -> bool:
    return nachher > vorher * (1 + 1e-9)


@lru_cache(maxsize=64)
def kante_exakt(netz: str, groesse, kante: tuple) -> dict:
    """Je Start vor und nach der neuen Verbindung (ohne Zufall)."""
    g = Z.baue(netz, groesse)
    vorher = X.zustandsraum(g)
    nachher = X.zustandsraum(N.mit_kante(g, *kante))
    return {"vorher": vorher, "nachher": nachher}


@lru_cache(maxsize=32)
def alle_neuen_kanten(netz: str, groesse=None) -> list:
    """Für jede fehlende Verbindung: Zeit des schlechtesten Starts danach (kleine Netze live, zwei 3×3-Hallen vorgerechnet)."""
    g = Z.baue(netz, groesse)
    if netz == C.NETZ_HALLEN and groesse == 3:
        d = D.laden()["tuer3x3"]
        return [{"kante": (u, v), "vorher": d["basis"], "nachher": w} for u, v, w in d["kanten"]]
    if g.n > C.ALLE_KANTEN_MAX:
        raise ValueError("alle neuen Verbindungen nur auf kleinen Netzen")
    basis = float(X.zustandsraum(g).max())
    return [{"kante": e, "vorher": basis, "nachher": float(X.zustandsraum(N.mit_kante(g, *e)).max())} for e in N.fehlende_kanten(g)]


def hat_alle_kanten(netz: str, groesse=None) -> bool:
    g = Z.baue(netz, groesse)
    return g.n <= C.ALLE_KANTEN_MAX or (netz == C.NETZ_HALLEN and groesse == 3)


def zaehle_laenger(zeilen: list, halle_groesse: int = None) -> dict:
    """Zahl der verlängernden Verbindungen; auf Gitterhallen getrennt nach „innerhalb einer Halle“ und „zwischen den Hallen“."""
    erg = {"alle": len(zeilen), "laenger": sum(laenger(z["nachher"], z["vorher"]) for z in zeilen),
           "kuerzer": sum(laenger(z["vorher"], z["nachher"]) for z in zeilen)}
    if halle_groesse is not None:
        halb = halle_groesse * halle_groesse
        for name, drin in (("innen", True), ("zwischen", False)):
            teil = [z for z in zeilen if ((z["kante"][0] < halb) == (z["kante"][1] < halb)) == drin]
            erg[name] = len(teil)
            erg[f"{name}_laenger"] = sum(laenger(z["nachher"], z["vorher"]) for z in teil)
            erg[f"{name}_kuerzer"] = sum(laenger(z["vorher"], z["nachher"]) for z in teil)
    return erg


def verdict_neue_kante(beschreibung: str, vorher: float, nachher: float):
    """Eine Verbindung: Zeit des schlechtesten Starts vorher und nachher (ohne Zufall)."""
    if laenger(nachher, vorher):
        return "warning", f"{beschreibung} **verlängert** die Überdeckungszeit des schlechtesten Starts: {zeit(vorher)} → {zeit(nachher)} Schritte."
    if laenger(vorher, nachher):
        return "success", f"{beschreibung} verkürzt die Überdeckungszeit des schlechtesten Starts: {zeit(vorher)} → {zeit(nachher)} Schritte."
    return "info", f"{beschreibung} lässt die Überdeckungszeit des schlechtesten Starts gleich: {zeit(vorher)} Schritte."


def verlaengern(teil: int, alle: int, einzige: str, mehrere: str) -> tuple:
    """(Verb, Satzglied) für „teil von alle neuen Verbindungen verlängern“ mit passender Einzahl und Mehrzahl. `einzige`: Wortlaut bei alle = 1,
    `mehrere`: das Hauptwort in der Mehrzahl („neuen Verbindungen …“)."""
    if alle == 1:
        return "verlängert", einzige
    if teil == alle:
        return "verlängert", f"jede der {alle} {mehrere}"
    if teil == 0:
        return "verlängert", f"keine der {alle} {mehrere}"
    return ("verlängert" if teil == 1 else "verlängern"), f"{teil} der {alle} {mehrere}"


def verdict_alle_kanten(name: str, z: dict):
    """Zusammenfassung über alle möglichen neuen Verbindungen eines Netzes."""
    ziel = "die Überdeckungszeit des schlechtesten Starts"
    if "innen" in z:
        if z["innen"] == 0:
            return "info", f"Auf {name} gibt es keine neue Verbindung innerhalb einer Halle."
        verb, wer = verlaengern(z["innen_laenger"], z["innen"], "die einzige neue Verbindung innerhalb einer Halle",
                                "neuen Verbindungen innerhalb einer Halle")
        nicht = " nicht" if z["innen"] == 1 and z["innen_laenger"] == 0 else ""
        n, laenger_z = z["zwischen"], z["zwischen_laenger"]
        if laenger_z == 0 and z["zwischen_kuerzer"] == n:
            zwischen = (f"jede der {n} neuen Verbindungen zwischen den Hallen verkürzt sie" if n > 1
                        else "die einzige neue Verbindung zwischen den Hallen verkürzt sie")
        elif laenger_z == 0:
            zwischen = (f"keine der {n} neuen Verbindungen zwischen den Hallen verlängert sie" if n > 1
                        else "die einzige neue Verbindung zwischen den Hallen verlängert sie nicht")
        elif n == 1:
            zwischen = "die einzige neue Verbindung zwischen den Hallen verlängert sie"
        else:
            zwischen = f"von den {n} neuen Verbindungen zwischen den Hallen {'verlängert' if laenger_z == 1 else 'verlängern'} sie {laenger_z}"
        return "warning" if z["laenger"] else "success", f"Auf {name} {verb} {wer}{nicht} {ziel}; {zwischen}."
    einzige, mehrere = "die einzige mögliche neue Verbindung", "möglichen neuen Verbindungen"
    if z["laenger"] == 0:
        if z["kuerzer"] == z["alle"]:
            wer = einzige if z["alle"] == 1 else f"jede der {z['alle']} {mehrere}"
            return "success", f"Auf {name} verkürzt {wer} {ziel}."
        verb, wer = verlaengern(0, z["alle"], einzige, mehrere)
        return "success", f"Auf {name} {verb} {wer} {ziel}{' nicht' if z['alle'] == 1 else ''}."
    verb, wer = verlaengern(z["laenger"], z["alle"], einzige, mehrere)
    return "warning", f"Auf {name} {verb} {wer} {ziel}."


def tuer_zeile(a: int, r, startname: str) -> dict:
    """„Eine Tür mehr“ (r = Zeile oder 'alle'): vorher und nachher ab Türplatz bzw. ferner Ecke."""
    start = dict((k, s) for k, s, _ in Z.vergleichsstarts(C.NETZ_HALLEN, a))[startname]
    if a == 3:
        d = D.laden()["tuer"]["3"]
        return {"vorher": d["basis"][start], "vorher_se": 0.0, "nachher": d[str(r)][start], "nachher_se": 0.0, "art": "exakt"}
    basis = D.laden()["kurven"][f"hallen{a}"][str(start)]["1"]
    neu = D.laden()["tuer"][str(a)][str(r)][startname]
    return {"vorher": basis["runden"], "vorher_se": basis["se"], "nachher": neu["runden"], "nachher_se": neu["se"], "art": "gemessen"}


def verdict_tuer(a: int, r, startname: str, z: dict):
    was = "mit einer Tür in jeder Zeile" if r == "alle" else f"mit einer zweiten Tür in Zeile {r} (die vorhandene in Zeile {a // 2} bleibt)"
    ort = "ab dem Türplatz" if startname == "tuer" else "ab der fernen Ecke"
    e = vergleiche(z["nachher"], z["nachher_se"], z["vorher"], z["vorher_se"])
    paar = f"{mit_intervall(z['vorher'], z['vorher_se'])} → {mit_intervall(z['nachher'], z['nachher_se'])} Schritte"
    if e == "weniger":
        return "success", f"Zwei Hallen {a}×{a} {was}: {ort} kürzer, {paar}."
    if e == "mehr":
        return "warning", f"Zwei Hallen {a}×{a} {was}: {ort} länger, {paar}."
    return "info", f"Zwei Hallen {a}×{a} {was}: {ort} **nicht unterscheidbar**, {paar}."


# ----------------------------------------------------------------------------------------------------------------------------------
# Experiment 3: viele Läufer
# ----------------------------------------------------------------------------------------------------------------------------------

def _netz_key(netz: str, groesse=None) -> str:
    return Z.netz_schluessel(netz, groesse)


@lru_cache(maxsize=64)
def kurve(netz: str, groesse, start: int) -> list:
    """Je Läuferzahl k aus K_WERTE: Runden (Mittel, Median), Gesamtschritte, S_k = C_1 / C_k und S_k / k mit Intervall. Nur für Netze bis 8 Plätze oder benannte Starts."""
    g = Z.baue(netz, groesse)
    if g.n <= C.EXAKT_K_MAX:
        r = X.reihe(g, C.K_WERTE)
        zellen = {k: {"runden": float(r[k][start]), "se": 0.0, "median": float(X.median_runden(g, start, k))} for k in C.K_WERTE}
        art = "exakt"
    else:
        gespeichert = D.laden()["kurven"].get(_netz_key(netz, groesse), {}).get(str(start))
        if gespeichert is None:
            raise KeyError("für diesen Start nicht vorgerechnet")
        zellen = {k: gespeichert[str(k)] for k in C.K_WERTE}
        art = "gemessen"
    c1, c1_se = zellen[1]["runden"], zellen[1]["se"]
    c1_art = "gemessen"
    if netz == C.NETZ_SAELE or g.n <= C.EXAKT_START_MAX:
        c1, c1_se, c1_art = float(je_start(netz, groesse)["werte"][start]), 0.0, "exakt"
    zeilen = []
    for k in C.K_WERTE:
        z = zellen[k]
        runden, se, median = z["runden"], z["se"], z["median"]
        if k == 1 and c1_art == "exakt":
            runden, se = c1, 0.0
        gesamt, gesamt_se = k * runden, k * se
        s = c1 / runden
        rel = c1 / gesamt
        if k == 1:
            s_se = rel_se = 0.0
        else:
            relf = math.sqrt((c1_se / c1) ** 2 + (se / runden) ** 2)
            s_se, rel_se = s * relf, rel * relf
        zeilen.append({"k": k, "runden": runden, "se": se, "median": median, "gesamt": gesamt, "gesamt_se": gesamt_se, "gesamt_median": k * median,
                       "s": s, "s_se": s_se, "s_je_k": rel, "s_je_k_se": rel_se, "c1": c1, "c1_art": c1_art, "art": art})
    return zeilen


def hat_kurve(netz: str, groesse, start: int) -> bool:
    g = Z.baue(netz, groesse)
    return g.n <= C.EXAKT_K_MAX or str(start) in D.laden()["kurven"].get(_netz_key(netz, groesse), {})


def bruchwort(x: float) -> str:
    """Wörtliche Einordnung eines Anteils x < 1 („weniger als ein Fünftel“)."""
    for grenze, wort in ((1 / 5, "weniger als ein Fünftel"), (1 / 4, "weniger als ein Viertel"), (1 / 3, "weniger als ein Drittel"), (1 / 2, "weniger als die Hälfte")):
        if x < grenze:
            return wort
    return "weniger"


def verdict_viele(netzname: str, startname: str, z: dict):
    """Sparen k Läufer zusammen Schritte gegenüber einem? z: eine Zeile aus `kurve`."""
    k = z["k"]
    if k == 1:
        return "info", f"{netzname}, Start {startname}: ein Läufer braucht {mit_intervall(z['runden'], z['se'])} Schritte. Für den Vergleich k ≥ 2 wählen."
    kopf = f"{netzname}, Start {startname}: S_{k}/{k} = {de(z['s_je_k'], 2)}"
    if z["s_je_k_se"]:
        breite = Z95 * z["s_je_k_se"]
        kopf += f" ± {de(breite, 2)}" if breite >= 0.005 else " (Intervall schmaler als ± 0,01)"
    if z["s_je_k"] - Z95 * z["s_je_k_se"] > 1 + 1e-9:
        anteil = 1 / z["s_je_k"]
        return "success", (f"{kopf}: {k} Läufer brauchen zusammen {bruchwort(anteil)} {'der Schritte' if anteil < 0.5 else 'Schritte als'} "
                           f"{'eines einzelnen' if anteil < 0.5 else 'einer'} ({zeit(z['gesamt'])} gegen {zeit(z['c1'])} Schritte, {prozent(anteil)}).")
    if z["s_je_k"] + Z95 * z["s_je_k_se"] < 1 - 1e-9:
        return "warning", f"{kopf}: {k} Läufer brauchen zusammen **mehr** Schritte als einer ({zeit(z['gesamt'])} gegen {zeit(z['c1'])})."
    return "info", f"{kopf}: bei den Gesamtschritten **nicht unterscheidbar** von einem Läufer ({zeit(z['gesamt'])} gegen {zeit(z['c1'])})."


def gegenpole() -> list:
    d = D.laden()["pole"]
    namen = {"kreis128": ("Kreis (128)", 127 * 128 / 2), "weg128_ende": ("Weg (128), Start am Ende", 127 ** 2), "gitter11": ("Gitter 11×11, Start in der Mitte", None)}
    zeilen = []
    for key, (name, formel) in namen.items():
        c1 = formel if formel is not None else d[key]["1"]["runden"]
        for k in (8, 32):
            c = d[key][str(k)]
            zeilen.append({"netz": name, "k": k, "c1": c1, "gesamt": k * c["runden"], "s_je_k": c1 / (k * c["runden"])})
    return zeilen


def pi_start() -> list:
    d = D.laden()["pi"]
    c1 = d["1"]["runden"]
    return [{"k": k, "runden": d[str(k)]["runden"], "gesamt": k * d[str(k)]["runden"], "s_je_k": c1 / (k * d[str(k)]["runden"]), "c1": c1} for k in (2, 8, 32)]


# ----------------------------------------------------------------------------------------------------------------------------------
# Experiment 4: Gegner
# ----------------------------------------------------------------------------------------------------------------------------------

WISSEN_EIN = "nur die Nachbarn des Platzes"
WISSEN_K = "nur die Nachbarn; die Zahl k ist je Netz und Start gewählt"
WISSEN_TAU = "nur die Nachbarn; muss zum Start springen können; τ ist je Netz und Start gewählt"
WISSEN_PLAN = "die ganze Karte und Absprache"


@lru_cache(maxsize=32)
def karten_plan(fall: str, ks: tuple) -> dict:
    g, s = Z.gegner_fall(fall)
    return P.plane(g, s, ks)


def ein_laeufer_referenz(fall: str, gespeichert: dict) -> dict:
    """Die Zeit eines Läufers: derselbe Wert wie in den anderen Experimenten, also ohne Zufall, wo das geht (Säle, kleine Netze, Weg nach der bekannten Formel
    i(L − i) + L² mit L = n − 1), sonst die gespeicherte Messung (zwei Hallen 8×8: die Messung aus Experiment 3; Barbell: eigene Bewertung)."""
    g, s = Z.gegner_fall(fall)
    exakt = None
    if fall.startswith("saele"):
        exakt = float(je_start(C.NETZ_SAELE, g.n)["werte"][s])
    elif fall == "weg128":
        L = g.n - 1
        exakt = float(s * (L - s) + L * L)
    if exakt is not None:
        return {"k": 1, "tau": None, "runden": exakt, "se": 0.0, "median": gespeichert.get("median"), "art": "ohne Zufall"}
    if fall.startswith("hallen8"):
        return dict(D.laden()["kurven"]["hallen8"][str(s)]["1"], k=1, tau=None, art="gemessen")
    return dict(gespeichert, art="ohne Zufall" if fall in C.EXAKTE_FAELLE else "gemessen")


@lru_cache(maxsize=16)
def gegner(fall: str) -> dict:
    """Messwerte eines Gegner-Falls in Gesamtschritten, dazu der Karten-Plan mit k = 1 und dem besten getesteten k."""
    d = D.laden()["gegner"][fall]
    ein, kz, tz = ein_laeufer_referenz(fall, d["ein"]), d["bestes_k"], d["bestes_tau"]
    k = kz["k"]
    plan = karten_plan(fall, (1, k))

    def zeile(art, z, name, wissen):
        faktor = z["k"]
        return {"art": art, "name": name, "k": z["k"], "tau": z["tau"], "gesamt": faktor * z["runden"], "gesamt_se": faktor * z["se"],
                "gesamt_median": None if z.get("median") is None else faktor * z["median"], "runden": z["runden"], "runden_se": z["se"], "wissen": wissen}

    zeilen = [zeile("ein", ein, f"ein Läufer ({ein['art']})", WISSEN_EIN),zeile("k", kz, f"beste getestete Läuferzahl k = {k}", WISSEN_K),
              zeile("tau", tz, f"ein Läufer mit festem Rücksprung, τ = {tz['tau']}", WISSEN_TAU)]
    return {"zeilen": zeilen, "plan": plan, "k": k, "tau": tz["tau"], "exakt": d["exakt"], "k_wahl": d["k_wahl"], "tau_wahl": d["tau_wahl"],
            "tau_am_rand": tz["tau"] in (d["tau_wahl"][0]["tau"], d["tau_wahl"][-1]["tau"]),
            "k_am_rand": k == d["k_wahl"][-1]["k"] or (k == d["k_wahl"][0]["k"] and k > 2)}   # k = 2 am unteren Rand heißt: davor steht nur ein Läufer


def gegner_urteil(g: dict) -> dict:
    """Vergleiche aus den Intervallen: bestes k gegen einen Läufer, Rücksprung gegen einen Läufer und gegen bestes k."""
    ein, kz, tz = g["zeilen"]
    paar = lambda x, y: vergleiche(x["gesamt"], x["gesamt_se"], y["gesamt"], y["gesamt_se"])  # noqa: E731
    return {"k_gegen_ein": paar(kz, ein), "tau_gegen_ein": paar(tz, ein), "tau_gegen_k": paar(tz, kz)}


def verdict_gegner(fallname: str, g: dict):
    """Fester Rücksprung gegen die beste getestete Läuferzahl, dazu der Karten-Plan in Runden."""
    u = gegner_urteil(g)
    ein, kz, tz = g["zeilen"]
    plan = g["plan"][g["k"]]
    karte = (f" Abgesprochene Läufer mit Karte sind bei k = {g['k']} nach {plan['runden']} Runden fertig, Irrfahrer im Mittel nach {zeit(kz['runden'])} Runden "
             f"(das {de(kz['runden'] / plan['runden'], 1)}-Fache).")
    if u["k_gegen_ein"] != "weniger" and u["tau_gegen_ein"] != "weniger":
        return "info", f"{fallname}: Hier spart weder eine getestete Läuferzahl noch ein getesteter Rücksprung Gesamtschritte gegenüber einem Läufer." + karte
    zahlen = f"{zeit(tz['gesamt'])} gegen {zeit(kz['gesamt'])} Gesamtschritte beim besten getesteten k = {g['k']} (ein Läufer: {zeit(ein['gesamt'])})"
    if u["tau_gegen_k"] == "weniger":
        return "success", f"{fallname}: Den Gewinn holt auch ein Läufer mit festem Rücksprung, mit **weniger** Gesamtschritten: {zahlen}." + karte
    if u["tau_gegen_k"] == "gleichauf":
        return "success", f"{fallname}: Ein Läufer mit festem Rücksprung liegt **gleichauf**: {zahlen}." + karte
    return "warning", f"{fallname}: Hier braucht der feste Rücksprung **mehr** Gesamtschritte als die beste getestete Läuferzahl: {zahlen}." + karte


def karte_gegen_zufall(fall: str) -> list:
    """Karten-Plan gegen Irrfahrer in Runden für k = 1, 2, 8, 32 (nur wo die Irrfahrer-Runden vorliegen)."""
    g, s = Z.gegner_fall(fall)
    netz_start = {"saele65_F": (C.NETZ_SAELE, 65), "saele129_F": (C.NETZ_SAELE, 129), "saele65_i": (C.NETZ_SAELE, 65), "hallen8_tuer": (C.NETZ_HALLEN, 8),
                  "hallen8_ecke": (C.NETZ_HALLEN, 8), "flur_mitte": (C.NETZ_FLUR, None), "hand_tuer": (C.NETZ_HAND, None), "hand_ecke": (C.NETZ_HAND, None)}
    if fall not in netz_start:
        return []
    netz, gr = netz_start[fall]
    werte = {z["k"]: z for z in kurve(netz, gr, s)}
    ks = (1, 2, 8, 32)
    plan = karten_plan(fall, ks)
    return [{"k": k, "plan": plan[k]["runden"], "untere": plan[k]["unten"], "zufall": werte[k]["runden"], "faktor": werte[k]["runden"] / plan[k]["runden"]} for k in ks]


def fuenf_netze() -> list:
    """Die fünf größeren Netze mit Gewinn: Rücksprung gegen beste getestete Läuferzahl."""
    zeilen = []
    for fall in C.FUENF_NETZE:
        g = gegner(fall)
        u = gegner_urteil(g)
        ein, kz, tz = g["zeilen"]
        zeilen.append({"fall": fall, "ein": ein["gesamt"], "k": g["k"], "k_gesamt": kz["gesamt"], "tau": g["tau"], "tau_gesamt": tz["gesamt"], **u})
    return zeilen


def satz_fuenf_netze(zeilen: list) -> str:
    """Zusammenfassung Rücksprung gegen beste getestete Läuferzahl auf den größeren Netzen, aus den Intervallen gezählt; Abweichungen mit ihrer Größe."""
    n = len(zeilen)
    teile = []
    weniger = [z for z in zeilen if z["tau_gegen_k"] == "weniger"]
    gleich = [z for z in zeilen if z["tau_gegen_k"] == "gleichauf"]
    mehr = [z for z in zeilen if z["tau_gegen_k"] == "mehr"]
    if weniger:
        teile.append(f"auf {len(weniger)} weniger Gesamtschritte")
    if gleich:
        rest = max(abs(z["tau_gesamt"] / z["k_gesamt"] - 1) for z in gleich)
        teile.append(f"auf {len(gleich)} nicht unterscheidbar viele (Unterschied der Mittel höchstens {prozent(rest, 1)})")
    if mehr:
        ueber = max(z["tau_gesamt"] / z["k_gesamt"] - 1 for z in mehr)
        teile.append(f"auf {len(mehr)} mehr (um höchstens {prozent(ueber, 1)})")
    return (f"Auf den {n} größeren Netzen, auf denen mehrere Läufer Gesamtschritte sparen, brauchte ein Läufer mit festem Rücksprung, verglichen mit der besten getesteten "
            f"Läuferzahl, {', '.join(teile)}.")


# ----------------------------------------------------------------------------------------------------------------------------------
# Hauptansicht: ein Lauf und die erwartete Zeit
# ----------------------------------------------------------------------------------------------------------------------------------

@lru_cache(maxsize=16)
def lauf(netz: str, groesse, start: int, k: int, seed: int):
    return S.verlauf(Z.baue(netz, groesse), start, k, seed, C.VERLAUF_MAX)


@lru_cache(maxsize=32)
def erwartung(netz: str, groesse, start: int, k: int, seed: int) -> dict:
    """Erwartete Runden: exakt, aus den vorgerechneten Messungen oder (freier Start auf großem Netz) aus wenigen Probeläufen mit dem Zufalls-Seed des Nutzers."""
    g = Z.baue(netz, groesse)
    if k == 1 and (netz == C.NETZ_SAELE or g.n <= C.EXAKT_START_MAX):
        return {"runden": float(je_start(netz, groesse)["werte"][start]), "se": 0.0, "quelle": "exakt"}
    if hat_kurve(netz, groesse, start):
        z = {z["k"]: z for z in kurve(netz, groesse, start)}[k]
        return {"runden": z["runden"], "se": z["se"], "quelle": z["art"]}
    if k == 1:
        js = je_start(netz, groesse)
        return {"runden": float(js["werte"][start]), "se": float(js["se"][start]), "quelle": js["art"]}
    r = S.simuliere_ueberdeckung(g, start, k, C.LIVE_LAEUFE, Z.zell_seed("live", netz, groesse, start, k, seed))
    kz = S.kennzahlen(r, k)
    return {"runden": kz["runden"], "se": kz["se"], "quelle": "probelaeufe", "laeufe": C.LIVE_LAEUFE}
