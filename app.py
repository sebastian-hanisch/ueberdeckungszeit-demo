"""Bis jeder Ort besucht ist - Überdeckungszeit einer Irrfahrt auf Netzen - interaktive Konzept-Demo
Sebastian Hanisch - Operations Research und Machine Learning

Wie lange braucht eine Irrfahrt auf einem Netz, bis sie jeden Platz besucht hat? Matthews-Klammer, eine neue Verbindung, mehrere Läufer und zwei Gegner
(fester Rücksprung, Läufer mit Karte). Aufbau und Regeln stehen im DEMO-PLAYBOOK.md (§2).

Lauffähig mit: streamlit run app.py
"""

import numpy as np
import streamlit as st

import udz_constants as C
import udz_daten as D
import udz_evaluation as E
import udz_netze as N
import udz_szenario as S
import udz_trefferzeit as T
from udz_karte import karte
from udz_layout import dunkles_design, kopf_css
from udz_presets import (
    bounds,
    groesse_gewechselt,
    init_session_state_defaults,
    load_permalink_settings,
    netz_gewechselt,
    passe_start_an,
    randomize_seed,
    sidebar_presets,
    sync_query_params,
)
from udz_visualization import (
    balken_klammer,
    karte_kante,
    karte_lauf,
    karte_zeit_je_start,
    kurve_runden,
    kurve_speedup,
    raster,
    verlauf_besucht,
)

st.set_page_config(page_title="Überdeckungszeit – Sebastian Hanisch", layout="wide")


@st.cache_data(show_spinner=False)
def _lauf(netz, groesse, start, k, seed):
    return E.lauf(netz, groesse, start, k, seed)


@st.cache_data(show_spinner=False)
def _erwartung(netz, groesse, start, k, seed):
    return E.erwartung(netz, groesse, start, k, seed)


@st.cache_data(show_spinner=False)
def _je_start(netz, groesse):
    return E.je_start(netz, groesse)


@st.cache_data(show_spinner=False)
def _matthews(netz, groesse):
    return E.matthews(netz, groesse)


@st.cache_data(show_spinner=False)
def _tabelle():
    return E.tabelle_vergleich()


@st.cache_data(show_spinner=False)
def _kante(netz, groesse, kante):
    return E.kante_exakt(netz, groesse, kante)


@st.cache_data(show_spinner=False)
def _alle_kanten(netz, groesse):
    return E.alle_neuen_kanten(netz, groesse)


@st.cache_data(show_spinner=False)
def _kurve(netz, groesse, start):
    return E.kurve(netz, groesse, start)


@st.cache_data(show_spinner=False)
def _gegner(fall):
    return E.gegner(fall)


@st.cache_data(show_spinner=False)
def _karte_zufall(fall):
    return E.karte_gegen_zufall(fall)


@st.cache_data(show_spinner=False)
def _fuenf():
    return E.fuenf_netze()


def _karte_geklickt():
    """Klick auf einen Platz der Hauptkarte setzt den Start."""
    auswahl = st.session_state.get("hauptkarte")
    punkte = auswahl["selection"]["points"] if auswahl else []
    if punkte and punkte[0].get("customdata") is not None:
        wert = punkte[0]["customdata"]
        wert = wert[0] if isinstance(wert, (list, tuple)) else wert
        st.session_state["start"] = int(wert)


# Fester Kopf: nur der Titel bleibt beim Scrollen oben (Stylesheet in udz_layout.py).
st.html(kopf_css(dunkles_design()))
st.html('<style>[data-testid="stMarkdownContainer"] table { display: block; overflow-x: auto; max-width: 100%; }</style>')   # breite Tabellen scrollen auf dem Telefon
with st.container(key="kopf"):
    st.title("🗺️ Bis jeder Ort besucht ist – Überdeckungszeit einer Irrfahrt auf Netzen")
st.markdown(
    """
Eine **Irrfahrt** (random walk) geht in jedem Schritt von ihrem Platz zu einem zufällig gewählten Nachbarn, jeder gleich wahrscheinlich. Die **Überdeckungszeit** (cover time)
ist die erwartete Zahl der Schritte, bis sie **jeden Platz mindestens einmal** besucht hat; der Startplatz zählt als besucht. Wie lange das dauert, hängt an **Netz und
Startplatz**. Die Demo zeigt, wann die bekannte Matthews-Klammer hilft, dass eine **neue Verbindung** die Zeit verlängern kann, wann **mehrere Läufer** vom selben Start
zusammen Schritte sparen, und was zwei Gegner leisten: ein Läufer mit **festem Rücksprung** und Läufer mit **Karte**.

Weiter unten: **❓ Kernfragen**, vier **🔬 Experimente**, **🚧 Wo die Annahmen enden** und die Expander **⚠️ Annahmen, Grenzen und bekannte Probleme** und
**📐 Mathematische Formulierung**.
"""
)

with st.expander("So funktioniert die Überdeckungszeit", expanded=True):
    st.markdown(
        """
1. **Ein Schritt.** Die Irrfahrt geht von ihrem Platz zu einem seiner Nachbarn, jeder mit derselben Wahrscheinlichkeit.
2. **Besucht.** Jeder erreichte Platz wird gefärbt; der Startplatz ist von Anfang an gefärbt. Fertig ist die Irrfahrt, wenn alle gefärbt sind.
3. **Mehrere Läufer** starten auf demselben Platz und gehen gleichzeitig: In einer **Runde** macht jeder einen Schritt. Gezählt werden **Runden** und **Gesamtschritte**
   (Zahl der Läufer mal Runden). S_k = Zeit eines Läufers durch Zeit von k Läufern in Runden; **S_k / k > 1** heißt: Die k Läufer brauchen zusammen weniger Schritte als einer.
4. **Rechnen oder messen.** Auf kleinen Netzen wird die erwartete Zeit ohne Zufall gerechnet, auf großen aus vielen simulierten Läufen gemessen und mit einem
   95-%-Intervall des Mittels angegeben.
        """
    )

st.caption("🔗 Die Adresszeile oben spiegelt Ihre aktuelle Konfiguration wider – einfach kopieren, um ein Szenario zu teilen.")

load_permalink_settings()
init_session_state_defaults()
passe_start_an()

netz_jetzt = st.session_state["netz"]
g_jetzt = S.netz_fuer(netz_jetzt, int(st.session_state["a"]), int(st.session_state["nsaele"]))

with st.sidebar:
    sidebar_presets()  # Schnellstart oben, das aktive Preset ist hervorgehoben
    st.header("🧩 Netz")
    st.selectbox("Netz", C.NETZE, key="netz", format_func=C.NETZ_TEXT.get, on_change=netz_gewechselt,
                 help="Kleine Handnetze, wachsende Gitterhallen und Vergleichsnetze mit Engpass oder langen Gängen.")
    st.slider("Hallenseite a (Gitterhallen)", *bounds("a"), key="a", disabled=netz_jetzt != C.NETZ_HALLEN, on_change=groesse_gewechselt, args=(C.NETZ_HALLEN,),
              help="Jede Halle ist ein Gitter a×a mit einer Tür in der Zeile a // 2, zusammen 2a² Plätze (8 bis 128). Nur bei den Gitterhallen.")
    st.selectbox("Plätze der Säle mit Flurknoten", C.SAELE_GROESSEN, key="nsaele", disabled=netz_jetzt != C.NETZ_SAELE, on_change=groesse_gewechselt, args=(C.NETZ_SAELE,),
                 help="Zwei vollständige Säle mit je (n − 1) / 2 Plätzen und ein Flurknoten dazwischen. Nur bei diesem Netz.")
    st.header("🚶 Irrfahrt")
    st.selectbox("Start", range(g_jetzt.n), key="start", format_func=lambda i: g_jetzt.knoten[i], help="Auch per Klick auf die Hauptkarte wählbar.")
    st.select_slider("Läufer k", options=C.K_WERTE, key="k", help="So viele Läufer starten auf demselben Platz und gehen gleichzeitig.")
    st.number_input("Zufalls-Seed", *bounds("seed"), key="seed", step=1, help="Steuert den gezeigten Lauf (und die Probeläufe für freie Startplätze auf großen Netzen).")
    st.button("🎲 Neuen Zufalls-Seed ziehen", width="stretch", on_click=randomize_seed)

sync_query_params({key: st.session_state[key] for key in ("netz", "a", "nsaele", "start", "k", "seed")})

netz = st.session_state["netz"]
groesse = S.groesse_von(netz, st.session_state["a"], st.session_state["nsaele"])
start, k, seed = int(st.session_state["start"]), int(st.session_state["k"]), int(st.session_state["seed"])
g = S.baue(netz, groesse)
netzname = g.name
starts = S.vergleichsstarts(netz, groesse)
startname = next((t for _, s, t in starts if s == start), f"Platz {g.knoten[start]}")

# --- Ergebnis: ein Lauf ------------------------------------------------------------------------------------------------------------------------

st.markdown("## 🎯 Eine Irrfahrt, Runde für Runde")
st.caption(f"{netzname}: {g.n} Plätze, {len(g.kanten)} Verbindungen. Start {g.knoten[start]}, {k} Läufer, Zufalls-Seed {seed}.")
with st.spinner("Lasse die Läufer laufen …"):
    spur, erste, fertig = _lauf(netz, groesse, start, k, seed)
    erw = _erwartung(netz, groesse, start, k, seed)
ende = len(spur) - 1
runde_key = f"runde_{netz}_{groesse}_{start}_{k}_{seed}"
t = st.slider("Runde", 0, ende, ende // 2, key=runde_key, help="Zeigt den Stand nach so vielen Runden.")
besucht = int(((erste >= 0) & (erste <= t)).sum())
m1, m2, m3, m4 = st.columns(4)
m1.metric("Runden", E.ganz(t))
m2.metric("Gesamtschritte", E.ganz(k * t), help="Zahl der Läufer mal Runden.")
m3.metric("Besuchte Plätze", f"{besucht} von {g.n}")
quelle = {"exakt": "erwartet (ohne Zufall)", "gemessen": "erwartet (gemessen)", "probelaeufe": "geschätzt"}[erw["quelle"]]
m4.metric(f"Runden bis alle besucht, {quelle}", E.zeit(erw["runden"]),
          help="Mittlere Rundenzahl über viele Läufe bzw. der ohne Zufall gerechnete Erwartungswert. Der gezeigte Lauf streut stark darum.")
if erw["quelle"] == "probelaeufe":
    st.caption(f"Für diesen Start ist nichts vorgerechnet: {C.LIVE_LAEUFE} Probeläufe mit Ihrem Zufalls-Seed geben {E.mit_intervall(erw['runden'], erw['se'])} Runden (95-%-Intervall).")
elif erw["se"]:
    st.caption(f"Gemessen: {E.mit_intervall(erw['runden'], erw['se'])} Runden (95-%-Intervall des Mittels).")
st.plotly_chart(karte_lauf(g, erste, spur[t].tolist(), t, start), width="stretch", key="hauptkarte", on_select=_karte_geklickt, selection_mode="points")
st.caption("Grün: schon besucht. Grau: noch nicht. Rote Ringe: die Läufer nach der gewählten Runde. Ein Klick auf einen Platz macht ihn zum Start.")
st.plotly_chart(verlauf_besucht(erste, ende, t, g.n), width="stretch", key="verlauf")
if fertig:
    st.success(f"Dieser Lauf hat alle {g.n} Plätze nach **{E.runden_wort(ende)}** ({E.ganz(k * ende)} Gesamtschritten) besucht.")
else:
    st.warning(f"Nach {E.ganz(ende)} Runden bricht die Anzeige ab; nicht alle Plätze sind besucht.")

# --- Kernfragen --------------------------------------------------------------------------------------------------------------------------------

with st.spinner("Rechne die Kennzahlen …"):
    mat = _matthews(netz, groesse)
    tab = _tabelle()
    saele_f = {z["k"]: z for z in _kurve(C.NETZ_SAELE, 65, 32)}
    saele_i = {z["k"]: z for z in _kurve(C.NETZ_SAELE, 65, 0)}
    fuenf = _fuenf()
atlas = D.laden()["atlas_kante"]
atlas_l = D.laden()["atlas_laeufer"]

st.markdown("---")
st.markdown("## ❓ Kernfragen")
stich = next(z for z in tab if z["netz"] == C.NETZ_STICH)
st.markdown("**1. Wann nützt die Matthews-Klammer?**")
st.markdown(f"Beim vollständigen Saal sind beide Schranken genau. Beim Saal mit Stichgang 9 + 5 liegt die obere beim {E.de(stich['oben_faktor'], 1)}-Fachen und die untere beim "
            f"1/{E.de(stich['unten_faktor'], 0)}-Fachen. Auf diesem Netz ({netzname}): obere {E.de(mat['oben_faktor'], 2)}-fach, untere 1/{E.de(mat['unten_faktor'], 1)} (Experiment 1).")
st.markdown("**2. Kann eine neue Verbindung die Zeit verlängern?**")
st.markdown(f"Ja. Im 4-Kreis hebt die Diagonale die Zeit des schlechtesten Starts von 6 auf 6,8 Schritte. In {E.ganz(atlas['laenger'])} von {E.ganz(atlas['ergaenzungen'])} Fällen "
            f"(zusammenhängende Netze mit 3 bis 7 Plätzen, je Netz bis auf Isomorphie einmal, jede fehlende Verbindung einzeln) wird sie länger (Experiment 2).")
st.markdown("**3. Sparen viele Läufer Schritte, und von wo?**")
st.markdown(f"Auf zwei Sälen mit Flurknoten (65 Plätze) ist S_8/8 aus der Flurmitte {E.de(saele_f[8]['s_je_k'], 2)}, von einem Saal-Innenplatz {E.de(saele_i[8]['s_je_k'], 2)}: "
            "Es hängt am Startplatz (Experiment 3).")
st.markdown("**4. Was leisten fester Rücksprung und Karte?**")
st.markdown(f"{E.satz_fuenf_netze(fuenf)} Auf kleinen Netzen gilt das nicht immer: In {len(atlas_l['ruecksprung_mehr'])} von {E.ganz(atlas_l['paare_mit_gewinn'])} "
            "Paaren aus Netz und Start, bei denen mehrere Läufer Schritte sparen, braucht der Rücksprung mehr als die beste Läuferzahl. Abgesprochene Läufer mit Karte brauchten in "
            "den gemessenen Fällen weniger Runden als Irrfahrer (Experiment 4). τ und k sind je Netz und Start gewählt.")
st.caption("Die Antworten rechnen mit den Einstellungen der Seitenleiste, wo „dieses Netz“ genannt ist; die Voraussetzungen stehen in den Experimenten.")

st.markdown("---")

# --- Experiment 1 --------------------------------------------------------------------------------------------------------------------------------

st.subheader("🔬 Experiment 1: Bis alle besucht sind")
js = _je_start(netz, groesse)
wort = "ohne Zufall gerechnet" if js["art"] == "exakt" else "gemessen"
st.caption(f"Ein Läufer. Zeit je Startplatz, {wort}. Die **Matthews-Klammer** schätzt die Zeit des schlechtesten Starts allein aus der größten und kleinsten Trefferzeit "
           "(Schritte bis zu einem bestimmten Platz) zwischen zwei Plätzen.")
x1, x2, x3, x4 = st.columns(4)
x1.metric(f"Ab Start {g.knoten[start]}", E.zeit(js["werte"][start]), help="Erwartete Schritte eines Läufers, bis alle Plätze besucht sind.")
x2.metric("Schlechtester Start", E.zeit(mat["t_cov"]), help=f"Platz {g.knoten[mat['t_start']]}. Die Überdeckungszeit des Netzes ist die des schlechtesten Starts.")
x3.metric("Matthews unten", E.zeit(mat["unten"]), help="H_min · (1 + 1/2 + … + 1/(n−1))")
x4.metric("Matthews oben", E.zeit(mat["oben"]), help="H_max · (1 + 1/2 + … + 1/(n−1))")
art, text = E.verdict_matthews(netzname, mat["oben_faktor"], mat["unten_faktor"], mat["t_art"])
getattr(st, art)(text)
if mat["t_art"] == "gemessen":
    d = D.laden()["hallen"][str(groesse)]
    st.caption(f"Schlechtester Start: alle {g.n} Startplätze mit je {E.ganz(d['sicht_laeufe'])} Läufen gesichtet, die längsten {C.SICHTEN_BESTE} sowie Türplatz und ferne Ecke "
               f"mit frischen Zufalls-Seeds nachgemessen ({E.ganz(D.laden()['hallen'][str(groesse)]['bestaetigt'][str(mat['t_start'])]['laeufe'])} Läufe). Größter nachgemessener Wert: "
               f"{E.mit_intervall(mat['t_cov'], mat['t_se'])} am Platz {g.knoten[mat['t_start']]}. Einzelne Starts liegen so dicht beieinander, dass die Rangfolge unter ihnen nicht gesichert ist.")
if "menge_wert" in mat:
    menge = ", ".join(g.knoten[i] for i in mat["menge"])
    st.markdown(f"**Mengenschranke** (schärfere untere Schranke über alle Platzmengen, hier durch Aufzählen): {E.zeit(mat['menge_wert'])}; die Zeit liegt beim "
                f"{E.de(mat['menge_faktor'], 2)}-Fachen. Größte Schranke z. B. mit der Menge {{{menge}}}.")
st.plotly_chart(balken_klammer(mat["unten"], mat["t_cov"], mat["oben"], mat.get("menge_wert")), width="stretch", key="klammer")
st.plotly_chart(karte_zeit_je_start(g, np.asarray(js["werte"]), start, mat["t_start"], wort), width="stretch", key="karte_je_start")
if js["art"] == "gemessen":
    st.caption(f"Farbe je Startplatz aus der Sichtung ({E.ganz(D.laden()['hallen'][str(groesse)]['sicht_laeufe'])} Läufe je Platz); die nachgemessenen Plätze mit ihrem genaueren Wert.")
st.markdown("**Vergleichsnetze mit je 14 Plätzen** (ohne Zufall; wählbar auch in der Seitenleiste):")
st.dataframe([{"Netz": C.NETZ_TEXT[z["netz"]], "Zeit (schlechtester Start)": E.zeit(z["t_cov"]), "oben / Zeit": E.de(z["oben_faktor"], 2),
               "Zeit / unten": E.de(z["unten_faktor"], 2), "Zeit / Mengenschranke": E.de(z["menge_faktor"], 2)} for z in tab], hide_index=True, width="stretch")
hallen_zeilen = []
for a_h in range(3, C.A_MAX + 1):
    mh = _matthews(C.NETZ_HALLEN, a_h)
    hallen_zeilen.append({"Hallen a×a": f"{a_h}×{a_h}", "Zeit (schlechtester Start)": E.zeit(mh["t_cov"]), "oben / Zeit": E.de(mh["oben_faktor"], 2),
                          "Zeit / unten": E.de(mh["unten_faktor"], 2), "Rechenweg": "ohne Zufall" if mh["t_art"] == "exakt" else "gemessen"})
st.markdown("**Zum Vergleich die Gitterhallen:** Hier liegt die Klammer weder genau noch extrem weit daneben. Dass sie je nach Netzform genau oder weit daneben liegen kann, "
            "zeigen die Vergleichsnetze oben (Saal gegen Stichgang), nicht die Hallen.")
st.dataframe(hallen_zeilen, hide_index=True, width="stretch")

st.markdown("---")

# --- Experiment 2 --------------------------------------------------------------------------------------------------------------------------------

st.subheader("🔬 Experiment 2: Eine Verbindung mehr")
st.caption("Ein Läufer. Verglichen wird die Überdeckungszeit des **schlechtesten Starts** und des gewählten Starts vor und nach einer neuen Verbindung.")
fehlend = N.fehlende_kanten(g)
if netz == C.NETZ_HALLEN and groesse >= 3:
    zeilen_r = [r for r in range(groesse) if r != groesse // 2]
    r_wahl = st.selectbox("Eine Tür mehr: in welche Zeile?", zeilen_r + ["alle"], key=f"tuer_{groesse}",
                          format_func=lambda r: "in jede übrige Zeile (alle Türen)" if r == "alle" else f"Zeile {r}",
                          help=f"Die vorhandene Tür in Zeile {groesse // 2} bleibt.")
    if r_wahl != "alle":
        neu = (N.hallenknoten(groesse, 0, r_wahl, groesse - 1), N.hallenknoten(groesse, 1, r_wahl, 0))
        st.plotly_chart(karte(g, neue_kante=neu), width="stretch", key="karte_tuer")
        st.caption("Orange gestrichelt: die neue Tür.")
    for name_kurz in ("tuer", "ecke"):
        z = E.tuer_zeile(groesse, r_wahl, name_kurz)
        art, text = E.verdict_tuer(groesse, r_wahl, name_kurz, z)
        getattr(st, art)(text)
    st.markdown("**Alle Zeilen** (Zeit bis alle besucht sind, ab Türplatz und ab ferner Ecke):")
    tabelle_tuer = []
    for r in zeilen_r + ["alle"]:
        zt, ze = E.tuer_zeile(groesse, r, "tuer"), E.tuer_zeile(groesse, r, "ecke")
        tabelle_tuer.append({"neue Türen": "alle Zeilen" if r == "alle" else f"Zeile {r}", "ab Türplatz": E.mit_intervall(zt["nachher"], zt["nachher_se"]),
                             "ab ferner Ecke": E.mit_intervall(ze["nachher"], ze["nachher_se"])})
    zt, ze = E.tuer_zeile(groesse, zeilen_r[0], "tuer"), E.tuer_zeile(groesse, zeilen_r[0], "ecke")
    st.dataframe([{"neue Türen": "keine (eine Tür)", "ab Türplatz": E.mit_intervall(zt["vorher"], zt["vorher_se"]),
                   "ab ferner Ecke": E.mit_intervall(ze["vorher"], ze["vorher_se"])}] + tabelle_tuer, hide_index=True, width="stretch")
    if groesse == 3:
        alle = _alle_kanten(netz, 3)
        z = E.zaehle_laenger(alle, 3)
        st.markdown("**Jede der möglichen neuen Verbindungen** auf zwei 3×3-Hallen (ohne Zufall, vorgerechnet):")
        art, text = E.verdict_alle_kanten("zwei 3×3-Hallen", z)
        getattr(st, art)(text)
    else:
        st.caption("Ob neue Verbindungen innerhalb einer Halle die Zeit verlängern, ist für Hallen ab 4×4 nicht gemessen (die Zählung braucht die Rechnung ohne Zufall).")
elif not fehlend:
    st.info("In diesem Netz sind schon alle Plätze miteinander verbunden; es gibt keine neue Verbindung.")
elif g.n > C.EXAKT_START_MAX:
    st.info("Die Zeit mit einer neuen Verbindung wird hier ohne Zufall gerechnet, und das geht bis 18 Plätze. Zum Ausprobieren: Handnetz, 4-Kreis, Hallen 2×2 oder 3×3.")
else:
    standard = {C.NETZ_HAND: (0, 5), C.NETZ_KREIS4: (0, 2)}.get(netz, (1, 2) if (netz == C.NETZ_HALLEN and (1, 2) in fehlend) else fehlend[0])
    kante = st.selectbox("Neue Verbindung", fehlend, index=fehlend.index(standard), key=f"kante_{netz}_{groesse}",
                         format_func=lambda e: f"{g.knoten[e[0]]} – {g.knoten[e[1]]}")
    erg = _kante(netz, groesse, kante)
    vor, nach = erg["vorher"], erg["nachher"]
    k1, k2 = st.columns(2)
    k1.metric("Schlechtester Start", E.zeit(nach.max()), delta=f"{E.zeit(nach.max() - vor.max())} (vorher {E.zeit(vor.max())})", delta_color="inverse")
    k2.metric(f"Ab Start {g.knoten[start]}", E.zeit(nach[start]), delta=f"{E.zeit(nach[start] - vor[start])} (vorher {E.zeit(vor[start])})", delta_color="inverse")
    beschreibung = f"Die neue Verbindung {g.knoten[kante[0]]} – {g.knoten[kante[1]]}"
    art, text = E.verdict_neue_kante(beschreibung, float(vor.max()), float(nach.max()))
    getattr(st, art)(text)
    st.plotly_chart(karte_kante(g, nach - vor, kante, start), width="stretch", key="karte_kante")
    st.caption("Farbe je Startplatz: Änderung der Zeit ab diesem Start (rot länger, blau kürzer). Orange gestrichelt: die neue Verbindung.")
    if E.hat_alle_kanten(netz, groesse):
        with st.spinner("Rechne alle möglichen neuen Verbindungen …"):
            alle = _alle_kanten(netz, groesse)
        z = E.zaehle_laenger(alle, groesse if netz == C.NETZ_HALLEN else None)
        name = "zwei 2×2-Hallen" if netz == C.NETZ_HALLEN else f"dem Netz „{netzname}“"
        art, text = E.verdict_alle_kanten(name, z)
        getattr(st, art)(text)
        with st.expander("Alle möglichen neuen Verbindungen"):
            st.dataframe([{"neue Verbindung": f"{g.knoten[z['kante'][0]]} – {g.knoten[z['kante'][1]]}", "schlechtester Start danach": E.zeit(z["nachher"]),
                           "länger?": "ja" if E.laenger(z["nachher"], z["vorher"]) else "nein"} for z in alle], hide_index=True, width="stretch")
vk = N.vierkreis()
h_vor, h_nach = T.treffer_matrix(vk), T.treffer_matrix(N.mit_kante(vk, 0, 2))
c4_vor, c4_nach = _je_start(C.NETZ_KREIS4, None)["werte"].max(), _kante(C.NETZ_KREIS4, None, (0, 2))["nachher"].max()
st.markdown(f"**Dieselbe Kante, zwei Zeiten:** Im 4-Kreis mit der Diagonale 0–2 steigt die Pendelzeit (hin und zurück) zwischen den Plätzen 1 und 3 von "
            f"{E.zeit(T.pendelzeit(h_vor, 1, 3))} auf {E.zeit(T.pendelzeit(h_nach, 1, 3))} Schritte, die Überdeckungszeit des schlechtesten Starts von {E.zeit(c4_vor)} auf "
            f"{E.zeit(c4_nach)}. Die Pendelzeit erklärt die Demo „Pendelzeit“ der Reihe.")
st.caption("Nach Barlow, Ding, Nachmias und Peres (The evolution of the cover time, Proposition 1.4) kann eine Verbindung die Überdeckungszeit höchstens um den Faktor 4 erhöhen.")
with st.expander("Zählung über alle kleinen Netze (vorgerechnet)"):
    st.markdown(
        f"Alle {E.ganz(atlas['graphen'])} zusammenhängenden, nicht isomorphen Netze mit 3 bis 7 Plätzen (Graphen-Atlas aus networkx), Zeit des schlechtesten Starts, "
        f"jede fehlende Verbindung einzeln. {E.ganz(atlas['mit_verlaengernder_kante'])} der {E.ganz(atlas['nicht_vollstaendig'])} nicht vollständigen Netze haben mindestens "
        f"eine verlängernde Verbindung; der größte Faktor ist {E.de(atlas['groesster_faktor'], 2)}; das kleinste Beispiel ist der 4-Kreis ({E.zeit(atlas['kleinste']['vorher'])} → "
        f"{E.zeit(atlas['kleinste']['nachher'])}). Der Anteil hängt an der Zähleinheit:\n\n"
        "| gezählt wird | länger | von | Anteil |\n|---|---|---|---|\n"
        f"| je Netz bis auf Isomorphie, jede fehlende Verbindung | {E.ganz(atlas['laenger'])} | {E.ganz(atlas['ergaenzungen'])} | {E.prozent(atlas['laenger'] / atlas['ergaenzungen'], 1)} |\n"
        f"| je Netz, gleichwertige Verbindungen nur einmal | {E.ganz(atlas['bahnen_laenger'])} | {E.ganz(atlas['bahnen'])} | {E.prozent(atlas['bahnen_laenger'] / atlas['bahnen'], 1)} |\n"
        f"| je Netz mit nummerierten Plätzen, jede fehlende Verbindung | {E.ganz(atlas['beschriftet_laenger'])} | {E.ganz(atlas['beschriftet'])} | "
        f"{E.prozent(atlas['beschriftet_laenger'] / atlas['beschriftet'], 1)} |\n"
    )

st.markdown("---")

# --- Experiment 3 --------------------------------------------------------------------------------------------------------------------------------

st.subheader("🔬 Experiment 3: Viele Läufer vom selben Start")
st.caption("k Läufer starten auf demselben Platz und gehen gleichzeitig. Zwei benannte Starts nebeneinander; S_k = Zeit eines Läufers / Rundenzahl von k Läufern. "
           "S_k / k > 1 heißt: Die k Läufer brauchen zusammen weniger Schritte als einer.")
paare = starts[:2]
kurven = [(name, _kurve(netz, groesse, s)) for _, s, name in paare]
k_v = k if k > 1 else 2
if k == 1:
    st.caption("In der Seitenleiste ist k = 1 gewählt; die Antworten unten gelten für k = 2.")
spalten = st.columns(len(paare))
for spalte, (name, zeilen) in zip(spalten, kurven):
    art, text = E.verdict_viele(netzname, name, next(z for z in zeilen if z["k"] == k_v))
    getattr(spalte, art)(text)
st.plotly_chart(kurve_runden(kurven), width="stretch", key="kurve_runden")
st.caption("Durchgezogen: Gesamtschritte (k mal Runden). Gepunktet: Runden. Fehlerbalken: 95-%-Intervall des Mittels. Beide Achsen logarithmisch.")
st.plotly_chart(kurve_speedup(kurven, k), width="stretch", key="kurve_speedup")
st.caption("S_k / k über der Läuferzahl; die gestrichelte Linie ist 1. Orange: die gewählte Läuferzahl.")
alle_starts = [(name, _kurve(netz, groesse, s)) for _, s, name in starts]
st.dataframe(
    [{"Start": name, "k": z["k"], "Runden (Mittel)": E.mit_intervall(z["runden"], z["se"]), "Runden (Median)": E.zeit(z["median"]),
      "Gesamtschritte (Mittel)": E.zeit(z["gesamt"]), "Gesamtschritte (Median)": E.zeit(z["gesamt_median"]), "S_k": E.de(z["s"], 2), "S_k / k": E.de(z["s_je_k"], 2)}
     for name, zeilen in alle_starts for z in zeilen],
    hide_index=True, width="stretch", height=320,
)
herkunft = ("Ohne Zufall gerechnet; der Median ist die kleinste Rundenzahl, bis zu der mindestens die Hälfte der Läufe fertig ist." if kurven[0][1][0]["art"] == "exakt"
            else f"Gemessen mit eigenen Zufalls-Seeds ({E.ganz(D.laden()['kurven'][S.netz_schluessel(netz, groesse)][str(paare[0][1])]['2']['laeufe'])} Läufe je Wert).")
st.caption(herkunft + (" Die Zeit eines Läufers (C₁) ist, wo das geht, ohne Zufall gerechnet und steht dann auch in S_k." if kurven[0][1][0]["c1_art"] == "exakt" else ""))
if netz == C.NETZ_SAELE:
    st.markdown("Auf diesem Netz ist die Verteilung ab der Flurmitte bei wenigen Läufern schief: Einige Läufe dauern sehr viel länger. Darum stehen Mittel **und** Median in der Tabelle.")
if netz == C.NETZ_HALLEN and groesse == 8:
    ecke = {z["k"]: z for z in kurven[1][1]}
    st.warning("Negativbefund auf diesem Netz: Ab der fernen Ecke sparte keine der getesteten Läuferzahlen (k = 2 bis 16 und 32) Gesamtschritte. "
               f"Bei k = 32 ist S_32/32 = {E.de(ecke[32]['s_je_k'], 2)}: 32 Läufer brauchen zusammen rund das {E.de(1 / ecke[32]['s_je_k'], 1)}-Fache "
               "der Schritte eines einzelnen.")
with st.expander("Starts nach der stationären Verteilung (zwei Hallen 8×8)"):
    st.markdown("Starten die k Läufer unabhängig auf zufälligen Plätzen, jeder Platz mit Anteil proportional zu seiner Nachbarzahl (stationäre Verteilung π), ergibt sich:")
    st.dataframe([{"k": z["k"], "Runden": E.zeit(z["runden"]), "Gesamtschritte": E.zeit(z["gesamt"]), "S_k / k": E.de(z["s_je_k"], 2)} for z in E.pi_start()], hide_index=True, width="stretch")
    st.markdown(f"**Vorsicht beim Vergleich:** k verteilte Läufer haben schon beim Start bis zu k verschiedene Plätze besucht, und das Hinkommen erledigt das Aufstellen. "
                f"Aufstellen nach π braucht Kenntnis des Netzes. Zum Vergleich: ein Läufer ab einem π-gezogenen Platz braucht {E.zeit(E.pi_start()[0]['c1'])} Schritte.")
with st.expander("Gegenpole: wo viele Läufer wenig bringen"):
    st.dataframe([{"Netz": z["netz"], "k": z["k"], "Gesamtschritte": E.zeit(z["gesamt"]), "ein Läufer": E.zeit(z["c1"]), "S_k / k": E.de(z["s_je_k"], 2)} for z in E.gegenpole()],
                 hide_index=True, width="stretch")
    st.markdown(f"Gemessen mit je {E.ganz(C.R_POLE)} Läufen; die Zeit eines Läufers auf Kreis und Weg ist die bekannte Formel, auf dem Gitter gemessen.")
w15 = D.laden()["weg15"]
with st.expander("Alle kleinen Netze und die Sätze aus der Literatur"):
    st.markdown(
        f"""
**Alle {E.ganz(atlas_l['graphen'])} zusammenhängenden Netze mit 3 bis 7 Plätzen** (je einmal bis auf Isomorphie, ohne Zufall): Bei keinem sparen k = 2 oder k = 3 Läufer an
**allen** Startplätzen Gesamtschritte. Für k = 2 sparen sie an einem Teil der Starts bei {E.ganz(atlas_l['an_teil']['2'])} Netzen, an keinem Start bei {E.ganz(atlas_l['an_keinem']['2'])}.
Auf den {E.ganz(atlas_l['graphen_bis6'])} Netzen mit 3 bis 6 Plätzen gilt dasselbe für k = 4. Auf dem vollständigen Saal mit 8 Plätzen und auf dem Kreis mit 10 Plätzen spart k = 2 an keinem Start.

**Mit dem schlechtesten Start je Läuferzahl** (so definieren Alon u. a. ihre Beschleunigung, eine andere Größe als S_k oben): Auf dem Weg mit 15 Plätzen ist sie für zwei
Läufer {E.de(w15['s2'], 3)}, also über 2.

**Nur genannt** (N. Alon, C. Avin, M. Koucký, G. Kozma, Z. Lotker, M. Tuttle, *Many Random Walks Are Faster Than One*): Auf der Hantel aus zwei vollständigen Netzen mit
einem Weg der Länge 2 braucht ein Läufer Θ(n²) Schritte, k = 20·ln n Läufer **ab der Mitte** brauchen O(n) Runden. Gezeigt ist das für diesen Start; ob die Beschleunigung von
anderen Starts höchstens k ist, lassen die Autoren offen. Auf dem Kreis ist die Beschleunigung nur Θ(log k) (für k < e^(n/4)). Diese Sätze gelten für wachsende n; die Zahlen
der Demo sind Einzelfälle fester Größe.
        """
    )

st.markdown("---")

# --- Experiment 4 --------------------------------------------------------------------------------------------------------------------------------

st.subheader("🔬 Experiment 4: Gegner mit mehr Wissen – fester Rücksprung und Karte")
st.markdown("**Fester Rücksprung:** Ein einziger Läufer, der nach je τ Schritten wieder auf den Startplatz gesetzt wird; **der Sprung zählt nicht als Schritt**. k Läufer über t Runden "
            "besuchen dieselbe Verteilung von Platzmengen wie ein Läufer in k Abschnitten zu je t Schritten ab dem Start. **Karte:** abgesprochene Läufer mit einem Plan, der aus der ganzen Karte berechnet wird. "
            "Die Demo „Lokaler Schnitt“ benutzt einen zufälligen Neustart; er ist ein anderes Verfahren.")
vorschlag = S.fall_fuer_einstellung(netz, groesse, start)
fall = st.selectbox("Fall", C.GEGNER_FAELLE, index=C.GEGNER_FAELLE.index(vorschlag) if vorschlag else 0, key=f"fall_{netz}_{groesse}_{start}",
                    format_func=C.GEGNER_TEXT.get, help="Vorgerechnete Fälle. Passt die Einstellung der Seitenleiste zu einem Fall, ist er vorausgewählt.")
if vorschlag is None:
    st.caption("Für Netz und Start der Seitenleiste ist kein Gegner-Vergleich vorgerechnet; gezeigt wird der oben gewählte Fall.")
with st.spinner("Rechne den Karten-Plan …"):
    geg = _gegner(fall)
tabelle_g = [{"Gegner": z["name"], "Gesamtschritte": E.mit_intervall(z["gesamt"], z["gesamt_se"]),
              "Median": "–" if z["gesamt_median"] is None else E.zeit(z["gesamt_median"]), "Runden": E.mit_intervall(z["runden"], z["runden_se"]),
              "Was weiß er?": z["wissen"]} for z in geg["zeilen"]]
for kk, name in ((1, "ein Läufer mit Karte"), (geg["k"], f"k = {geg['k']} abgesprochene Läufer mit Karte")):
    plan = geg["plan"][kk]
    tabelle_g.append({"Gegner": name, "Gesamtschritte": f"höchstens {E.ganz(kk * plan['runden'])}", "Median": "–",
                      "Runden": f"{plan['runden']} (kein Plan unter {plan['unten']})", "Was weiß er?": E.WISSEN_PLAN})
st.dataframe(tabelle_g, hide_index=True, width="stretch")
art, text = E.verdict_gegner(C.GEGNER_TEXT[fall], geg)
getattr(st, art)(text)
if geg["exakt"]:
    st.caption("Ohne Zufall gerechnet. τ und k aus dem ganzen Raster, k ab 2, τ bis 80.")
else:
    st.caption(f"τ und k auf eigenen Zufalls-Seeds aus den Rastern unten gewählt ({E.ganz(C.laeufe_wahl(fall))} Läufe je Rasterwert), dann mit frischen Zufalls-Seeds bewertet "
               f"({E.ganz(D.laden()['gegner'][fall]['bestes_tau']['laeufe'])} Läufe). Beide sind für genau dieses Netz und diesen Start gewählt. Diese Bewertungen haben eigene "
               "Zufalls-Seeds: Läuferzahlen, die auch in Experiment 3 vorkommen, weichen dort im Rahmen der Intervalle ab. Der Karten-Plan ist eine obere Schranke für den "
               "kürzesten Plan (nächster Nachbar, 2-opt, in k Stücke geteilt, nachgelaufen); die Faktoren sind deshalb Untergrenzen.")
if geg["tau_am_rand"]:
    st.caption("Das gewählte τ liegt am Rand des Rasters: Ein besseres τ außerhalb ist nicht ausgeschlossen. Bei großem τ ist der Rücksprung selten, der Läufer verhält sich fast wie ohne Rücksprung.")
if geg["k_am_rand"]:
    st.caption("Die gewählte Läuferzahl liegt am Rand des k-Rasters.")
ein_wert = geg["zeilen"][0]["gesamt"]
r1, r2 = st.columns(2)
punkte_tau = [dict(p) if geg["exakt"] else {"tau": p["tau"], "gesamt": p["runden"] if p["fertig"] else None} for p in geg["tau_wahl"]]
punkte_k = [dict(p) if geg["exakt"] else {"k": p["k"], "gesamt": p["k"] * p["runden"] if p["fertig"] else None} for p in geg["k_wahl"]]
r1.plotly_chart(raster(punkte_tau, "tau", "τ (Schritte)", geg["tau"], ein_wert, "ein Läufer"), width="stretch", key="raster_tau")
r2.plotly_chart(raster(punkte_k, "k", "Läuferzahl k", geg["k"], ein_wert, "ein Läufer"), width="stretch", key="raster_k")
zufall = _karte_zufall(fall)
if zufall:
    st.markdown("**Karte gegen Zufall in Runden:**")
    st.dataframe([{"k": z["k"], "Plan mit Karte": z["plan"], "kein Plan unter": z["untere"], "Irrfahrer (Mittel)": E.zeit(z["zufall"]), "Faktor": E.de(z["faktor"], 1)} for z in zufall],
                 hide_index=True, width="stretch")
st.markdown("**Die fünf größeren Netze, auf denen mehrere Läufer Gesamtschritte sparen:** " + E.satz_fuenf_netze(fuenf))
st.caption("Bei fast flachem Raster entscheidet das Zufallsrauschen der Auswahl mit, welches τ und k gewählt wird; Unterschiede um 1 % sind deshalb nicht als Vorteil eines Gegners zu lesen.")
st.dataframe([{"Fall": C.GEGNER_TEXT[z["fall"]], "ein Läufer": E.zeit(z["ein"]), "bestes k": f"{z['k']}: {E.zeit(z['k_gesamt'])}",
               "Rücksprung": f"τ = {z['tau']}: {E.zeit(z['tau_gesamt'])}",
               "Rücksprung gegen bestes k": {"weniger": "weniger Schritte", "gleichauf": "gleichauf", "mehr": "mehr Schritte"}[z["tau_gegen_k"]]} for z in fuenf],
             hide_index=True, width="stretch")
with st.expander(f"Die Gegenfälle: {len(atlas_l['ruecksprung_mehr'])} kleine Netze, auf denen der Rücksprung mehr braucht"):
    st.markdown(f"Alle Paare aus Netz (3 bis 7 Plätze) und Start, bei denen ein k von 2 bis {C.ATLAS_K_MAX} Gesamtschritte spart: {E.ganz(atlas_l['paare_mit_gewinn'])} Paare "
                f"(gleichwertige Starts einzeln gezählt). Der beste Rücksprung mit τ bis {C.ATLAS_TAU_MAX} braucht in {E.ganz(atlas_l['ruecksprung_hoechstens'])} höchstens so viele "
                f"Schritte wie das beste k, in {len(atlas_l['ruecksprung_mehr'])} mehr, höchstens um {E.prozent(atlas_l['groesster_ueberschuss'], 1)}.")
    st.dataframe([{"Plätze": f["knoten"], "Verbindungen": " ".join(f"{u}-{v}" for u, v in f["kanten"]), "Start": f["start"],
                   "bestes k": f"{f['k']}: {E.de(f['k_gesamt'], 3)}", "bester Rücksprung": f"τ = {f['tau']}: {E.de(f['tau_gesamt'], 3)}"}
                  for f in atlas_l["ruecksprung_mehr"]], hide_index=True, width="stretch")

st.markdown("---")

# --- Grenzen -------------------------------------------------------------------------------------------------------------------------------------

st.subheader("🚧 Wo die Annahmen enden")
st.markdown("Diese Demo gehört zur Reihe „Irrfahrten auf Netzen“. Die rechte Spalte nennt die Demo der Reihe, in der es um die genannte Frage geht; jede ist eine eigene Demo.")
st.markdown(
    """
| Grenze dieser Demo | Wie es weitergeht | Thema |
|---|---|---|
| **Gefragt sind alle Plätze, nicht ein Ziel.** | Die Demo „Trefferzeit“ misst, wie lange die Irrfahrt bis zu einem bestimmten Ziel braucht. Diese Demo fragt auf demselben Handnetz und auf benannten Kontrastnetzen, wie lange es dauert, bis sie jeden Knoten mindestens einmal besucht hat, und was mehrere Läufer vom selben Start daran ändern. | Trefferzeit |
| **Die Pendelzeit ist eine andere Größe.** | Dieselbe neue Kante im 4-Kreis hebt die Pendelzeit zwischen zwei Plätzen von 8 auf 10 und die Überdeckungszeit von 6 auf 6,8. | Pendelzeit |
| **Nur ein fester Rücksprung.** | Die Demo „Lokaler Schnitt“ benutzt einen zufälligen Neustart; er ist ein anderes Verfahren. | Lokaler Schnitt |
| **Die Übergänge sind vorgegeben.** | Wer den Weg selbst wählt, um einen Angriff zu entdecken, hat eine andere Aufgabe: Das zeigt die Demo „Streife“ in einem Forschungsmodell, mit geplanter Rundtour gegen Zufall. Hier wird nur die Besuchszeit gezählt, ohne Angreifer. | Streife |
"""
)
st.markdown(
    """
* **Aldous-Broder:** Die [Demo zu zufälligen Spannbäumen](https://sebastianhanisch-random-spanning-tree-demo.streamlit.app/) lässt eine Irrfahrt von der Wurzel laufen, bis alle Plätze gesehen sind, und baut daraus einen Spannbaum. Hier geht es nur um die Zeit.
* **Träge Irrfahrt:** Bleibt die Irrfahrt in jedem Schritt mit Wahrscheinlichkeit ½ stehen, wird die Überdeckungszeit genau doppelt so lang.
* **Gerichtete oder gewichtete Netze** rechnet die Demo nicht.
* **Zufall gegen Plan:** Wer die Karte kennt und sich absprechen kann, ist in den gemessenen Fällen mit weniger Runden fertig. Die Irrfahrt braucht beides nicht.
"""
)

st.markdown("---")

with st.expander("⚠️ Annahmen, Grenzen und bekannte Probleme"):
    st.markdown(
        """
**Annahmen.**
- Einfaches, ungerichtetes, zusammenhängendes Netz; in jedem Schritt jeder Nachbar gleich wahrscheinlich; die Irrfahrt bleibt nie stehen. Alle Zeiten sind **erwartete** Schritte bzw. Runden; der Startplatz zählt als besucht.
- Mehrere Läufer starten auf demselben Platz, gehen gleichzeitig und unabhängig.
- Fester Rücksprung: Der Läufer kann jederzeit zum Start springen, und der Sprung kostet nichts. τ und die Läuferzahl sind je Netz und Start gewählt, also mit Kenntnis des Netzes.
- Der Karten-Gegner kennt das ganze Netz und die Läufer sprechen sich ab.

**Grenzen.**
- Die Zahlen gelten für die genannten Netze und Starts. Ob mehrere Läufer oder der Rücksprung Schritte sparen, hängt an beidem.
- Die Vergleiche mit dem Rücksprung gelten für die getesteten Werte von τ und k, nicht für alle denkbaren.
- Der Karten-Plan ist nicht als kürzester Plan bewiesen: Auf kleinen Zufallsnetzen ist er in einem Teil der Fälle länger als der kürzeste Plan aus einer vollständigen Suche.
- Neue Verbindungen: Die Beobachtung zu Verbindungen innerhalb und zwischen den Hallen ist nur für 2×2 und 3×3 gerechnet.
- Der schlechteste Start der Gitterhallen ab 4×4 ist gemessen; nahe Werte lassen sich nicht sicher ordnen.

**Bekannte Probleme und Unsicherheiten.**
- Die Wahl des Starts per Klick auf die Karte ist nicht mit einem echten Mausklick bestätigt (geprüft wurde die Verarbeitung eines im Browser ausgelösten Auswahl-Ereignisses). Das Auswahlfeld in der Seitenleiste tut dasselbe.
- Auf den größten Netzen dauern einzelne Rechnungen beim ersten Aufruf einige Sekunden.
        """
    )

# --- Formeln -------------------------------------------------------------------------------------------------------------------------------------

with st.expander("📐 Mathematische Formulierung"):
    st.markdown(
        r"""
**Lesehilfe.** Gegeben ist ein zusammenhängendes, einfaches, ungerichtetes Netz mit $n$ Plätzen und $m$ Verbindungen und ein Startplatz $s$. Gesucht ist die erwartete Zahl der
Schritte, bis die einfache Irrfahrt ab $s$ jeden Platz besucht hat.

| Symbol | Bedeutung |
|---|---|
| $\tau_{\mathrm{cov}}$ | erster Zeitpunkt, zu dem alle Plätze besucht sind |
| $C(s) = E_s[\tau_{\mathrm{cov}}]$ | Überdeckungszeit ab Start $s$ |
| $t_{\mathrm{cov}} = \max_s C(s)$ | Überdeckungszeit des Netzes (schlechtester Start) |
| $H(u,v)$ | Trefferzeit von $u$ nach $v$ |
| $h_k = 1 + 1/2 + \dots + 1/k$ | harmonische Zahl |
| $T_k$, $S_k = C(s)/E[T_k]$ | Runden von $k$ Läufern ab $s$; Beschleunigung gegenüber einem |
| $q_A(t)$ | Wahrscheinlichkeit, ab $s$ in $t$ Schritten keinen Platz aus $A$ zu besuchen |

**Rechnen auf kleinen Netzen.** Der Zustand ist (besuchte Menge $M$, Platz $x$). Weil $M$ nur wächst, wird von großen zu kleinen Mengen gelöst; je Menge ist es ein lineares
Gleichungssystem, mit $f(V,x) = 0$:

$$
f(M,x) = 1 + \frac{1}{d_x} \sum_{w \sim x} f(M_w, w)
$$

mit $M_w = M \cup \{w\}$.

**Mehrere unabhängige Läufer** ab demselben Start (Ein- und Ausschluss über gemiedene Mengen):

$$
P(T_k > t) = \sum_{A \ne \emptyset} (-1)^{|A|+1} q_A(t)^k
$$

**Fester Rücksprung** alle $\tau$ Schritte (Sprung zählt nicht; mit $\tau$ kleiner als der Entfernung zum fernsten Platz wird nie alles besucht):

$$
E = \sum_{A \ne \emptyset} (-1)^{|A|+1} \frac{\sum_{r<\tau} q_A(r)}{1 - q_A(\tau)}
$$

**Matthews-Klammer** (mit $H_{\max}$, $H_{\min}$ über alle Paare verschiedener Plätze):

$$
H_{\min}\, h_{n-1} \le t_{\mathrm{cov}} \le H_{\max}\, h_{n-1}
$$

**Mengenschranke** (untere Schranke, über jede Menge $B$ mit mindestens zwei Plätzen):

$$
t_{\mathrm{cov}} \ge \min_{u \ne v \in B} H(u,v) \cdot h_{|B|-1}
$$

**Literatur.** D. Levin, Y. Peres, E. Wilmer, *Markov Chains and Mixing Times*, 2. Auflage: Matthews-Methode (Satz 11.2 und Proposition 11.4). R. Aleliunas, R. Karp, R. Lipton, L. Lovász,
C. Rackoff (1979), Satz 4: Überdeckungszeit von jedem Start höchstens $2m(n-1)$. L. Lovász, *Random Walks on Graphs: A Survey* (1993): Kreis $n(n-1)/2$, vollständiges Netz $(n-1)\,h_{n-1}$.
M. Barlow, J. Ding, A. Nachmias, Y. Peres, *The evolution of the cover time*, Proposition 1.4. N. Alon u. a., *Many Random Walks Are Faster Than One*. Die Arbeit von Matthews (1988) ist
nicht im Original eingesehen.
        """
    )

st.markdown("---")
st.caption(
    "Diese Demo ist Teil des Portfolios von [Sebastian Hanisch](https://sebastianhanisch.net) – "
    "Operations Research und Machine Learning ([Über mich](https://sebastianhanisch.net/ueber-mich.html)). "
    "Mehr zur Reihe: [Irrfahrten auf Netzen: Trefferzeit bis Schnitt](https://sebastianhanisch.net/konzepte-irrfahrten.html)."
)
