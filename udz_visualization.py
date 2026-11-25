"""Plotly-Figuren der Demo. Alle Achsen sind gesperrt; Beschriftungen innerhalb der Diagramme sind Annotationen oder Legenden."""

import math

import numpy as np
import plotly.graph_objects as go

import udz_constants as C
import udz_karte as K
import udz_netze as N


def _gesperrt(fig: go.Figure, hoehe: int, legende: bool = True) -> go.Figure:
    fig.update_xaxes(fixedrange=True)
    fig.update_yaxes(fixedrange=True)
    fig.update_layout(height=hoehe, margin=dict(l=10, r=10, t=20, b=10), dragmode=False, plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
                      showlegend=legende, legend=dict(orientation="h", y=-0.28, x=0))
    return fig


def karte_lauf(g: N.Netz, erste: np.ndarray, orte: list, t: int, start: int) -> go.Figure:
    """Ein Lauf nach t Runden: besuchte Plätze gefärbt, Läufer als rote Ringe."""
    besucht = (erste >= 0) & (erste <= t)
    farben = [C.FARBE_BESUCHT if b else C.FARBE_OFFEN for b in besucht]
    belegt = {}
    for o in orte:
        belegt[int(o)] = belegt.get(int(o), 0) + 1
    marken = {o: ("", C.FARBE_LAEUFER) for o in sorted(belegt)}
    hover = [f"{g.knoten[i]}: {'besucht seit Runde ' + str(int(erste[i])) if besucht[i] else 'noch nicht besucht'}"
             + (f" · {belegt[i]} Läufer hier" if i in belegt else "") + (" · Start" if i == start else "") for i in range(g.n)]
    return K.karte(g, farben=farben, marken=marken, hover=hover, hoehe=380)


def verlauf_besucht(erste: np.ndarray, runden: int, t: int, n: int) -> go.Figure:
    """Zahl der besuchten Plätze über die Runden eines Laufs."""
    zeiten = np.sort(erste[erste >= 0])
    x = [0] + [int(v) for v in zeiten[zeiten > 0]] + [runden]
    y = [int((erste == 0).sum())]
    for v in zeiten[zeiten > 0]:
        y.append(int((zeiten <= v).sum()))
    y.append(int((erste >= 0).sum()))
    fig = go.Figure(go.Scatter(x=x, y=y, mode="lines", line=dict(shape="hv", color=C.FARBE_BESUCHT, width=2), name="besuchte Plätze", hovertemplate="Runde %{x}: %{y} Plätze<extra></extra>"))
    fig.add_vline(x=t, line=dict(color=C.FARBE_LAEUFER, width=2, dash="dot"))
    fig.update_xaxes(title="Runde")
    fig.update_yaxes(title="besuchte Plätze", range=[0, n * 1.04])
    return _gesperrt(fig, 200, legende=False)


def karte_zeit_je_start(g: N.Netz, werte: np.ndarray, start: int, schlecht: int, art: str) -> go.Figure:
    """Überdeckungszeit (ein Läufer) je Startplatz als Farbe."""
    hover = [f"Start {g.knoten[i]}: {werte[i]:,.0f} Schritte ({art})".replace(",", " ") for i in range(g.n)]
    marken = {start: ("Start", C.FARBE_LAEUFER)}
    if schlecht != start:
        marken[schlecht] = ("längster", "#6a3d9a")
    return K.karte(g, werte=werte, farbtitel="Schritte je Start", marken=marken, hover=hover, hoehe=380)


def balken_klammer(unten: float, t: float, oben: float, menge: float = None) -> go.Figure:
    """Untere Schranke, gemessene bzw. berechnete Zeit und obere Schranke auf logarithmischer Achse."""
    namen = ["Matthews unten", "Mengenschranke", "Zeit (schlechtester Start)", "Matthews oben"]
    werte = [unten, menge, t, oben]
    farben = [C.FARBE_GRAU, C.FARBE_C, C.FARBE_A, C.FARBE_GRAU]
    paare = [(n, w, f) for n, w, f in zip(namen, werte, farben) if w is not None]
    fig = go.Figure(go.Bar(y=[p[0] for p in paare], x=[p[1] for p in paare], orientation="h", marker_color=[p[2] for p in paare],
                           hovertemplate="%{y}: %{x:.1f}<extra></extra>"))
    fig.update_xaxes(type="log", title="Schritte (logarithmisch)", range=[math.log10(min(p[1] for p in paare) / 1.6), math.log10(max(p[1] for p in paare) * 1.6)])
    fig.update_yaxes(autorange="reversed")
    return _gesperrt(fig, 220, legende=False)


def karte_kante(g: N.Netz, aenderung: np.ndarray, kante: tuple, start: int) -> go.Figure:
    """Änderung der Zeit je Startplatz durch eine neue Verbindung (rot länger, blau kürzer)."""
    grenze = float(max(np.abs(aenderung).max(), 1e-9))
    hover = [f"Start {g.knoten[i]}: {aenderung[i]:+.2f} Schritte" for i in range(g.n)]
    return K.karte(g, werte=aenderung, farbtitel="Änderung (Schritte)", farbskala="RdBu_r", cmin=-grenze, cmax=grenze, marken={start: ("Start", C.FARBE_LAEUFER)},
                   neue_kante=kante, hover=hover, hoehe=380)


def kurve_runden(zeilen_je_start: list) -> go.Figure:
    """Runden und Gesamtschritte über k, je Start eine Farbe. zeilen_je_start: [(Name, Zeilen aus kurve)]."""
    farben = [C.FARBE_A, C.FARBE_B]
    fig = go.Figure()
    for (name, zeilen), farbe in zip(zeilen_je_start, farben):
        ks = [z["k"] for z in zeilen]
        fig.add_trace(go.Scatter(x=ks, y=[z["gesamt"] for z in zeilen], mode="lines+markers", line=dict(color=farbe, width=2), name=f"{name}: Gesamtschritte",
                                 error_y=dict(type="data", array=[1.96 * z["gesamt_se"] for z in zeilen], visible=True, thickness=1)))
        fig.add_trace(go.Scatter(x=ks, y=[z["runden"] for z in zeilen], mode="lines+markers", line=dict(color=farbe, width=2, dash="dot"), name=f"{name}: Runden"))
    fig.update_xaxes(type="log", tickvals=list(C.K_WERTE), title="Läuferzahl k")
    fig.update_yaxes(type="log", title="Schritte bzw. Runden")
    return _gesperrt(fig, 340)


def kurve_speedup(zeilen_je_start: list, k: int) -> go.Figure:
    """S_k / k über k; über 1 heißt: k Läufer brauchen zusammen weniger Schritte als einer."""
    farben = [C.FARBE_A, C.FARBE_B]
    fig = go.Figure()
    for (name, zeilen), farbe in zip(zeilen_je_start, farben):
        fig.add_trace(go.Scatter(x=[z["k"] for z in zeilen], y=[z["s_je_k"] for z in zeilen], mode="lines+markers", line=dict(color=farbe, width=2), name=name,
                                 error_y=dict(type="data", array=[1.96 * z["s_je_k_se"] for z in zeilen], visible=True, thickness=1)))
    fig.add_hline(y=1, line=dict(color="rgba(90,90,90,0.8)", width=1, dash="dash"))
    if k > 1:
        fig.add_vline(x=k, line=dict(color=C.FARBE_C, width=1.5, dash="dot"))
    fig.update_xaxes(type="log", tickvals=list(C.K_WERTE), title="Läuferzahl k")
    fig.update_yaxes(title="S_k / k", rangemode="tozero")
    return _gesperrt(fig, 300)


def raster(punkte: list, x_feld: str, titel_x: str, bestes, vergleich: float, vergleich_name: str) -> go.Figure:
    """Gesamtschritte über die Rasterwerte (Auswahlläufe); Vergleichslinie, bester Rasterwert markiert."""
    gueltig = [p for p in punkte if p.get("gesamt") is not None]
    fig = go.Figure(go.Scatter(x=[p[x_feld] for p in gueltig], y=[p["gesamt"] for p in gueltig], mode="lines+markers", line=dict(color=C.FARBE_A, width=2),
                               name="Auswahlläufe", hovertemplate=f"{titel_x} %{{x}}: %{{y:.1f}} Gesamtschritte<extra></extra>"))
    best = [p for p in gueltig if p[x_feld] == bestes]
    if best:
        fig.add_trace(go.Scatter(x=[bestes], y=[best[0]["gesamt"]], mode="markers", marker=dict(size=13, color=C.FARBE_LAEUFER, symbol="star"), name="gewählt"))
    xs = [p[x_feld] for p in gueltig]
    # Vergleichslinie als Spur statt add_hline (add_hline streckt logarithmische Achsen ins Unendliche)
    fig.add_trace(go.Scatter(x=[min(xs), max(xs)], y=[vergleich, vergleich], mode="lines", line=dict(color="rgba(90,90,90,0.8)", width=1, dash="dash"),
                             hoverinfo="skip", name=vergleich_name))
    fig.add_annotation(xref="paper", x=1, y=math.log10(vergleich), yref="y", text=vergleich_name, showarrow=False, xanchor="right", yanchor="bottom", font=dict(size=11),
                       bgcolor="rgba(255,255,255,0.85)")
    fig.update_xaxes(type="log" if x_feld == "tau" else "linear", title=titel_x, dtick=1 if x_feld == "tau" else None)
    fig.update_yaxes(type="log", title="Gesamtschritte")
    return _gesperrt(fig, 300, legende=False)
