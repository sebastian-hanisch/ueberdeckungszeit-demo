"""Rechnet alle gemessenen Zahlen der Demo vor und speichert sie in daten/vorgerechnet.json.

Aufruf (aus dem Demo-Ordner, mit dem Test-venv wegen networkx):  python tools/vorrechnen.py <abschnitt> [<abschnitt> …]
Abschnitte: hallen, kurven_hallen, kurven_saele, kurven_klein, pi, tuer, tuer3x3, pole, weg15, atlas_kante, atlas_laeufer, gegner_<fall>
(oder getrennt gegnerwahl_<fall> und gegnerwert_<fall>, für die langen Fälle), alle
Jeder Abschnitt schreibt nur seinen Teil neu. Mit OMP_NUM_THREADS=1 laufen lassen.
"""

import json
import sys
import time
from pathlib import Path

WURZEL = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(WURZEL))

import numpy as np  # noqa: E402

import udz_atlas as AT  # noqa: E402
import udz_constants as C  # noqa: E402
import udz_exakt as X  # noqa: E402
import udz_irrfahrt_sim as S  # noqa: E402
import udz_messung as M  # noqa: E402
import udz_netze as N  # noqa: E402
import udz_szenario as Z  # noqa: E402

DATEI = WURZEL / "daten" / "vorgerechnet.json"


def lade() -> dict:
    return json.loads(DATEI.read_text(encoding="utf-8")) if DATEI.exists() else {}


def schreibe(schluessel: str, wert, unter: str = None) -> None:
    daten = lade()
    if unter is None:
        daten[schluessel] = wert
    else:
        daten.setdefault(schluessel, {})[unter] = wert
    DATEI.parent.mkdir(exist_ok=True)
    DATEI.write_text(json.dumps(daten, ensure_ascii=False, indent=1, sort_keys=True) + "\n", encoding="utf-8", newline="\n")


def hallen():
    """Alle Startplätze der Gitterhallen a = 4 … 8 sichten, die längsten sowie Türplatz und ferne Ecke mit frischen Zufalls-Seeds nachmessen."""
    for a in range(4, C.A_MAX + 1):
        g = Z.baue(C.NETZ_HALLEN, a)
        key = f"hallen{a}"
        sicht = [M.zelle("sicht", key, g, s, 1, C.R_SICHTEN) for s in range(g.n)]
        mittel = np.array([c["runden"] for c in sicht])
        beste = [int(i) for i in np.argsort(-mittel, kind="stable")[: C.SICHTEN_BESTE]]
        namen = sorted(set(beste) | {N.tuerknoten(a), N.ferne_ecke(a)})
        bestaetigt = {str(s): M.wert(key, g, s, 1) for s in namen}
        schlecht = max(namen, key=lambda s: bestaetigt[str(s)]["runden"])
        schreibe("hallen", {"sicht_mittel": [c["runden"] for c in sicht], "sicht_se": [c["se"] for c in sicht], "sicht_laeufe": C.R_SICHTEN,
                            "beste_der_sichtung": beste, "bestaetigt": bestaetigt, "schlechtester": schlecht}, str(a))
        print("hallen", a, "schlechtester", g.knoten[schlecht], round(bestaetigt[str(schlecht)]["runden"], 1), flush=True)


def _kurve(key: str, g: N.Netz, starts) -> None:
    werte = {}
    for _, s, _ in starts:
        werte[str(s)] = {str(k): M.wert(key, g, s, k) for k in C.K_WERTE}
        print("kurve", key, s, [round(werte[str(s)][str(k)]["runden"] * k, 1) for k in C.K_WERTE], flush=True)
    schreibe("kurven", werte, key)


def kurven_hallen():
    for a in range(3, C.A_MAX + 1):
        _kurve(f"hallen{a}", Z.baue(C.NETZ_HALLEN, a), Z.vergleichsstarts(C.NETZ_HALLEN, a))


def kurven_saele():
    for n in C.SAELE_GROESSEN:
        _kurve(f"saele{n}", Z.baue(C.NETZ_SAELE, n), Z.vergleichsstarts(C.NETZ_SAELE, n))


def kurven_klein():
    for netz in (C.NETZ_STICH, C.NETZ_SAAL14, C.NETZ_STERN14, C.NETZ_KREIS14, C.NETZ_WEG14):
        _kurve(netz, Z.baue(netz), Z.vergleichsstarts(netz))


def pi():
    """Starts unabhängig nach π auf den Hallen 8×8 (jeder Läufer eigener Startplatz)."""
    g = Z.baue(C.NETZ_HALLEN, 8)
    werte = {}
    for k in (1, 2, 8, 32):
        starts = S.zieh_stationaer(g, C.R_WERT * k, Z.zell_seed("pi-start", k)).reshape(C.R_WERT, k)
        runden = S.simuliere_ueberdeckung(g, starts, k, C.R_WERT, Z.zell_seed("pi-lauf", k))
        werte[str(k)] = {kk: v for kk, v in S.kennzahlen(runden, k).items()}
        print("pi", k, round(werte[str(k)]["runden"] * k, 1), flush=True)
    schreibe("pi", werte)


def tuer():
    """„Eine Tür mehr“: a = 3 ohne Zufall (jeder Start), a = 4 … 8 gemessen ab Türplatz und ferner Ecke; dazu alle Zeilen auf einmal."""
    g = N.zwei_hallen(3)
    exakt = {"basis": [float(x) for x in X.zustandsraum(g)]}
    for r in (0, 2):
        exakt[str(r)] = [float(x) for x in X.zustandsraum(N.eine_tuer_mehr(3, r))]
    exakt["alle"] = [float(x) for x in X.zustandsraum(N.alle_tueren(3))]
    schreibe("tuer", exakt, "3")
    for a in range(4, C.A_MAX + 1):
        werte = {}
        for r in [x for x in range(a) if x != a // 2] + ["alle"]:
            netz = N.alle_tueren(a) if r == "alle" else N.eine_tuer_mehr(a, r)
            werte[str(r)] = {name: M.zelle("tuer", f"hallen{a}-r{r}", netz, s, 1, C.R_TUER) for name, s, _ in Z.vergleichsstarts(C.NETZ_HALLEN, a)}
        schreibe("tuer", werte, str(a))
        print("tuer", a, {r: round(v["ecke"]["runden"]) for r, v in werte.items()}, flush=True)


def tuer3x3():
    """Jede der 128 möglichen neuen Verbindungen auf zwei 3×3-Hallen (ohne Zufall): Zeit des schlechtesten Starts."""
    g = N.zwei_hallen(3)
    basis = float(X.zustandsraum(g).max())
    liste = []
    for u, v in N.fehlende_kanten(g):
        liste.append([u, v, float(X.zustandsraum(N.mit_kante(g, u, v)).max())])
    schreibe("tuer3x3", {"basis": basis, "kanten": liste})
    print("tuer3x3", basis, sum(w > basis * (1 + 1e-9) for _, _, w in liste), "länger von", len(liste))


def pole():
    """Gegenpole: Kreis, Weg ab Ende, einzelnes Gitter ab der Mitte."""
    werte = {}
    for key, g, s in (("kreis128", N.kreis(128), 0), ("weg128_ende", N.weg(128), 0), ("gitter11", N.gitter(11), 60)):
        werte[key] = {str(k): M.zelle("pol", key, g, s, k, C.R_POLE) for k in (1, 8, 32)}
        print("pole", key, [round(werte[key][str(k)]["runden"] * k, 1) for k in (1, 8, 32)], flush=True)
    schreibe("pole", werte)


def weg15():
    """Weg mit 15 Plätzen: S_2 auch mit dem schlechtesten Start je Läuferzahl."""
    c = X.reihe(N.weg(15), [1, 2])
    schreibe("weg15", {"t1": float(c[1].max()), "t2": float(c[2].max()), "s2": float(c[1].max() / c[2].max()), "start1": int(c[1].argmax()), "start2": int(c[2].argmax())})
    print("weg15", c[1].max(), c[2].max(), c[1].max() / c[2].max())


def atlas_kante():
    z = AT.zaehle_neue_kante()
    schreibe("atlas_kante", z)
    print("atlas_kante", {k: v for k, v in z.items() if k != "kleinste"}, z["kleinste"])


def atlas_laeufer():
    z = AT.zaehle_laeufer_und_ruecksprung(C.ATLAS_K_MAX, C.ATLAS_TAU_MAX)
    z["k8_nie"] = AT.zwei_laeufer_nie(N.saal(8))
    z["kreis10_nie"] = AT.zwei_laeufer_nie(N.kreis(10))
    schreibe("atlas_laeufer", z)
    print("atlas_laeufer", {k: (v if k != "ruecksprung_mehr" else len(v)) for k, v in z.items()})


def _netz_key(fall: str) -> str:
    return {"saele65_F": "saele65", "saele65_i": "saele65", "saele129_F": "saele129", "barbell": "barbell", "weg128": "weg128",
            "hallen8_tuer": "hallen8", "hallen8_ecke": "hallen8", "flur_mitte": "flur", "hand_tuer": "hand", "hand_ecke": "hand"}[fall]


ZWECK_WAHL = "wahl-2"            # Zufalls-Seeds der Auswahl (getrennt von der Bewertung und von den Läuferkurven)
ZWECK_BEWERTUNG = "bewertung-2"  # Zufalls-Seeds der Bewertung


def gegner(fall: str):
    """k und tau je Raster mit Auswahl-Seeds wählen, dann ein Läufer, bestes k und bestes tau mit frischen Bewertungs-Seeds (kleine Netze ohne Zufall)."""
    g, s = Z.gegner_fall(fall)
    ks, taus = C.GEGNER_K[fall], [t for t in C.GEGNER_TAU[fall] if t >= N.exzentrizitaet(g, s)]
    if fall in C.EXAKTE_FAELLE:
        reihe = X.reihe(g, [1] + list(ks))
        r = X.ruecksprung(g, s, max(taus))
        k_wahl = [{"k": k, "gesamt": float(k * reihe[k][s])} for k in ks]
        tau_wahl = [{"tau": t, "gesamt": r[t - 1]} for t in taus if r[t - 1] is not None]
        bk = min(k_wahl, key=lambda c: (c["gesamt"], c["k"]))["k"]
        bt = min(tau_wahl, key=lambda c: (c["gesamt"], c["tau"]))["tau"]
        schreibe("gegner", {"exakt": True, "start": s, "k_wahl": k_wahl, "tau_wahl": tau_wahl,
                            "ein": {"k": 1, "tau": None, "runden": float(reihe[1][s]), "se": 0.0},
                            "bestes_k": {"k": bk, "tau": None, "runden": float(reihe[bk][s]), "se": 0.0},
                            "bestes_tau": {"k": 1, "tau": bt, "runden": float(r[bt - 1]), "se": 0.0}}, fall)
        print(fall, "k", bk, bk * reihe[bk][s], "tau", bt, r[bt - 1], "ein", reihe[1][s])
        return
    gegner_wahl(fall)
    gegner_wert(fall)


def gegner_wahl(fall: str):
    """Auswahl: jedes k und jedes tau des Rasters mit C.R_WAHL Läufen und Auswahl-Seeds."""
    g, s = Z.gegner_fall(fall)
    key = _netz_key(fall)
    ks, taus = C.GEGNER_K[fall], [t for t in C.GEGNER_TAU[fall] if t >= N.exzentrizitaet(g, s)]
    t0 = time.perf_counter()
    laeufe = C.laeufe_wahl(fall)
    k_wahl = [M.zelle(ZWECK_WAHL, key, g, s, k, laeufe) for k in ks]
    tau_wahl = [M.zelle(ZWECK_WAHL, key, g, s, 1, laeufe, tau=t) for t in taus]
    fertig = lambda liste: [c for c in liste if c["fertig"]]  # noqa: E731
    bk = min(fertig(k_wahl), key=lambda c: (c["k"] * c["runden"], c["k"]))["k"]
    bt = min(fertig(tau_wahl), key=lambda c: (c["runden"], c["tau"]))["tau"]
    schreibe("gegner_wahl", {"k_wahl": k_wahl, "tau_wahl": tau_wahl, "k": bk, "tau": bt}, fall)
    print(fall, "Auswahl fertig: k", bk, "tau", bt, round(time.perf_counter() - t0, 1), "s", flush=True)


def gegner_wert(fall: str):
    """Bewertung mit frischen Zufalls-Seeds: ein Läufer, das gewählte k und das gewählte tau."""
    g, s = Z.gegner_fall(fall)
    key = _netz_key(fall)
    wahl = lade()["gegner_wahl"][fall]
    bk, bt = wahl["k"], wahl["tau"]
    t0 = time.perf_counter()
    ein = M.zelle(ZWECK_BEWERTUNG, key, g, s, 1, M.laeufe_wert(key))
    kz = M.zelle(ZWECK_BEWERTUNG, key, g, s, bk, M.laeufe_wert(key))
    tz = M.zelle(ZWECK_BEWERTUNG, key, g, s, 1, M.laeufe_wert(key), tau=bt)
    schreibe("gegner", {"exakt": False, "start": s, "k_wahl": wahl["k_wahl"], "tau_wahl": wahl["tau_wahl"], "ein": ein, "bestes_k": kz, "bestes_tau": tz}, fall)
    print(fall, "ein", round(ein["runden"], 1), "±", round(1.96 * ein["se"], 1), "| k", bk, round(bk * kz["runden"], 1), "±", round(1.96 * bk * kz["se"], 1),
          "| tau", bt, round(tz["runden"], 1), "±", round(1.96 * tz["se"], 1), round(time.perf_counter() - t0, 1), "s", flush=True)


ABSCHNITTE = {"hallen": hallen, "kurven_hallen": kurven_hallen, "kurven_saele": kurven_saele, "kurven_klein": kurven_klein, "pi": pi, "tuer": tuer,
              "tuer3x3": tuer3x3, "pole": pole, "weg15": weg15, "atlas_kante": atlas_kante, "atlas_laeufer": atlas_laeufer}


def main(argumente):
    for name in argumente:
        t0 = time.perf_counter()
        if name == "alle":
            main(list(ABSCHNITTE) + [f"gegner_{f}" for f in C.GEGNER_FAELLE])
        elif name.startswith("gegnerwahl_"):
            gegner_wahl(name[len("gegnerwahl_"):])
        elif name.startswith("gegnerwert_"):
            gegner_wert(name[len("gegnerwert_"):])
        elif name.startswith("gegner_"):
            gegner(name[len("gegner_"):])
        else:
            ABSCHNITTE[name]()
        print(f"[{name}] {time.perf_counter() - t0:.1f} s", flush=True)


if __name__ == "__main__":
    main(sys.argv[1:])
