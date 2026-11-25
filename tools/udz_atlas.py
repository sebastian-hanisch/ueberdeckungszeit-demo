"""Zählungen über alle kleinen Netze (Graphen-Atlas): neue Verbindung, mehrere Läufer, fester Rücksprung. Nur für das Vorrechnen und die Tests (braucht networkx,
nicht Teil der App; die App zeigt die gespeicherten Ergebnisse)."""

import math

import numpy as np

import udz_exakt as X
import udz_netze as N


def atlas_netze(nmin: int = 3, nmax: int = 7):
    """Alle zusammenhängenden, nicht isomorphen Netze mit nmin bis nmax Plätzen (networkx graph_atlas_g) als (Netz, networkx-Graph)."""
    import networkx as nx

    for H in nx.graph_atlas_g():
        n = H.number_of_nodes()
        if nmin <= n <= nmax and nx.is_connected(H):
            H = nx.convert_node_labels_to_integers(H, ordering="sorted")
            yield N.netz(f"Atlas {n}", n, H.edges()), H


def automorphismen(H) -> list:
    from networkx.algorithms.isomorphism import GraphMatcher

    return [tuple(m[i] for i in range(H.number_of_nodes())) for m in GraphMatcher(H, H).isomorphisms_iter()]


def zaehle_neue_kante() -> dict:
    """Wie oft verlängert eine neue Verbindung die Überdeckungszeit des schlechtesten Starts? Drei Zähleinheiten."""
    z = {"graphen": 0, "nicht_vollstaendig": 0, "mit_verlaengernder_kante": 0, "ergaenzungen": 0, "laenger": 0, "bahnen": 0, "bahnen_laenger": 0,
         "beschriftet": 0, "beschriftet_laenger": 0, "groesster_faktor": 0.0, "kleinste": None}
    for g, H in atlas_netze():
        z["graphen"] += 1
        fehlt = N.fehlende_kanten(g)
        if not fehlt:
            continue
        z["nicht_vollstaendig"] += 1
        auto = automorphismen(H)
        gewicht = math.factorial(g.n) // len(auto)                        # Zahl der Beschriftungen dieses Netzes
        vorher = float(X.zustandsraum(g).max())
        laenger = {}
        for u, v in fehlt:
            nachher = float(X.zustandsraum(N.mit_kante(g, u, v)).max())
            laenger[(u, v)] = nachher > vorher * (1 + 1e-9)
            z["ergaenzungen"] += 1
            z["beschriftet"] += gewicht
            if laenger[(u, v)]:
                z["laenger"] += 1
                z["beschriftet_laenger"] += gewicht
                z["groesster_faktor"] = max(z["groesster_faktor"], nachher / vorher)
                if z["kleinste"] is None:
                    z["kleinste"] = {"knoten": g.n, "kanten": [list(e) for e in g.kanten], "neu": [u, v], "vorher": vorher, "nachher": nachher}
        z["mit_verlaengernder_kante"] += any(laenger.values())
        gesehen = set()
        for e in fehlt:
            if e in gesehen:
                continue
            bahn = {tuple(sorted((p[e[0]], p[e[1]]))) for p in auto}
            gesehen |= bahn
            z["bahnen"] += 1
            if len({laenger[f] for f in bahn}) != 1:
                raise AssertionError("gleichwertige Kanten mit verschiedenem Ergebnis")
            z["bahnen_laenger"] += laenger[e]
    return z


def _spart(c1: float, ck: float, k: int) -> bool:
    """Brauchen k Läufer zusammen (k mal Runden) weniger Schritte als einer?"""
    return k * ck < c1 - 1e-8


def zaehle_laeufer_und_ruecksprung(k_max: int = 12, tau_max: int = 80) -> dict:
    """Mehrere Läufer auf allen Netzen mit 3 bis 7 Plätzen und fester Rücksprung gegen die beste Läuferzahl."""
    z = {"graphen": 0, "an_allen": {"2": 0, "3": 0, "4": 0}, "an_teil": {"2": 0, "3": 0, "4": 0}, "an_keinem": {"2": 0, "3": 0, "4": 0},
         "graphen_bis6": 0, "paare": 0, "paare_mit_gewinn": 0, "ruecksprung_hoechstens": 0, "ruecksprung_mehr": [], "groesster_ueberschuss": 0.0}
    for g, _ in atlas_netze():
        z["graphen"] += 1
        z["graphen_bis6"] += g.n <= 6
        C = X.reihe(g, range(1, k_max + 1))
        for k in (2, 3, 4):
            if k == 4 and g.n > 6:
                continue
            spart = [_spart(C[1][s], C[k][s], k) for s in range(g.n)]
            name = "an_allen" if all(spart) else ("an_teil" if any(spart) else "an_keinem")
            z[name][str(k)] += 1
        for s in range(g.n):
            z["paare"] += 1
            if not any(_spart(C[1][s], C[k][s], k) for k in range(2, k_max + 1)):
                continue
            z["paare_mit_gewinn"] += 1
            gesamt = [k * C[k][s] for k in range(2, k_max + 1)]
            bk = 2 + int(np.argmin(gesamt))
            r = X.ruecksprung(g, s, tau_max)
            gueltig = [(v, t + 1) for t, v in enumerate(r) if v is not None]
            wert, tau = min(gueltig)
            if wert <= min(gesamt) + 1e-8:
                z["ruecksprung_hoechstens"] += 1
            else:
                z["ruecksprung_mehr"].append({"knoten": g.n, "kanten": [list(e) for e in g.kanten], "start": s, "k": bk, "k_gesamt": float(min(gesamt)),
                                              "tau": tau, "tau_gesamt": float(wert)})
                z["groesster_ueberschuss"] = max(z["groesster_ueberschuss"], wert / min(gesamt) - 1)
    return z


def zwei_laeufer_nie(g: N.Netz) -> bool:
    """Sparen zwei Läufer an keinem Start Gesamtschritte?"""
    C = X.reihe(g, [1, 2])
    return not any(_spart(C[1][s], C[2][s], 2) for s in range(g.n))
