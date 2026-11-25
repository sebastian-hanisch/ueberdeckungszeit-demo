"""Karte eines Netzes als Plotly-Figur (ohne Streamlit). Grundlage ist der gemeinsame Baustein `trz_karte` der Demo „Trefferzeit“, erweitert um feste Farben je
Platz (`farben`).

Jeder Knotenpunkt hat seine Nummer in `customdata` (für die Auswahl per Klick). Beschriftungen sind Annotationen, und ausgewählte wie nicht ausgewählte Punkte behalten die
volle Deckkraft (sonst dunkelt Plotly nach einem Klick den Rest ab). Achsen sind gesperrt."""

import plotly.graph_objects as go

import udz_netze as N

FARBE_KANTE = "rgba(130,130,130,0.55)"
FARBE_KNOTEN = "#9aa5b1"
FARBE_NEU = "#e69f00"


def _linien(g: N.Netz, kanten):
    xs, ys = [], []
    for a, b in kanten:
        xs += [g.pos[a][0], g.pos[b][0], None]
        ys += [g.pos[a][1], g.pos[b][1], None]
    return xs, ys


def knotengroesse(n: int) -> int:
    if n <= 10:
        return 30
    if n <= 40:
        return 18
    if n <= 100:
        return 12
    return 9


def karte(g: N.Netz, werte=None, farbtitel: str = "", farbskala="Viridis", cmin=None, cmax=None, marken=None, neue_kante=None, hover=None,
          hoehe: int = 360, beschriftung: bool = None, farben=None) -> go.Figure:
    """Karte des Netzes.

    werte: je Knoten eine Zahl für die Farbe; farben: je Knoten eine feste Farbe; sonst grau. marken: {Knoten: (Kurzzeichen, Farbe)} für Start usw.
    neue_kante: (a, b), gestrichelt. hover: je Knoten ein Hovertext. beschriftung: Knotennamen anzeigen (Standard: nur bis 10 Knoten)."""
    fig = go.Figure()
    viele = len(g.kanten) > 600
    kantenbreite = 0.35 if viele else (0.6 if len(g.kanten) > 150 else 1.4)
    kantenfarbe = "rgba(150,150,150,0.25)" if viele else FARBE_KANTE
    xs, ys = _linien(g, g.kanten)
    fig.add_trace(go.Scatter(x=[None if x is None else round(x, 3) for x in xs], y=[None if y is None else round(y, 3) for y in ys], mode="lines",
                             line=dict(color=kantenfarbe, width=kantenbreite), hoverinfo="skip", showlegend=False))
    if neue_kante is not None:
        xs, ys = _linien(g, [neue_kante])
        fig.add_trace(go.Scatter(x=xs, y=ys, mode="lines", line=dict(color=FARBE_NEU, width=3, dash="dash"), hoverinfo="skip", showlegend=False))
    groesse = knotengroesse(g.n)
    texte = list(hover) if hover is not None else [g.knoten[i] for i in range(g.n)]
    marker = dict(size=groesse, line=dict(width=1, color="rgba(60,60,60,0.7)"))
    if farben is not None:
        marker["color"] = list(farben)
    elif werte is None:
        marker["color"] = FARBE_KNOTEN
    else:
        marker.update(color=[float(w) for w in werte], colorscale=farbskala, showscale=True,
                      colorbar=dict(title=dict(text=farbtitel, side="top"), orientation="h", y=-0.12, thickness=10, len=0.8, nticks=5))
        if cmin is not None:
            marker.update(cmin=cmin, cmax=cmax)
    fig.add_trace(go.Scatter(x=[p[0] for p in g.pos], y=[p[1] for p in g.pos], mode="markers", marker=marker, customdata=list(range(g.n)), text=texte,
                             hovertemplate="%{text}<extra></extra>", showlegend=False, selected=dict(marker=dict(opacity=1)),
                             unselected=dict(marker=dict(opacity=1))))
    marken = marken or {}
    if beschriftung is None:
        beschriftung = g.n <= 10
    if beschriftung:
        for i in range(g.n):
            fig.add_annotation(x=g.pos[i][0], y=g.pos[i][1], text=g.knoten[i], showarrow=False, font=dict(size=13, color="#111111"),
                               bgcolor="rgba(255,255,255,0.75)")
    for nummer, (knoten, (zeichen, farbe)) in enumerate(marken.items()):
        fig.add_trace(go.Scatter(x=[g.pos[knoten][0]], y=[g.pos[knoten][1]], mode="markers",
                                 marker=dict(size=groesse + 9, color="rgba(0,0,0,0)", line=dict(width=3.5, color=farbe)), hoverinfo="skip", showlegend=False))
        if zeichen:
            # Fähnchen abwechselnd nach links und rechts, damit sich die Marken benachbarter Plätze nicht verdecken
            ax = 0 if len(marken) == 1 else (-24 if nummer % 2 == 0 else 24)
            fig.add_annotation(x=g.pos[knoten][0], y=g.pos[knoten][1], text=f"<b>{zeichen}</b>", showarrow=True, arrowhead=0, ax=ax, ay=-28,
                               font=dict(size=13, color="#ffffff"), bgcolor=farbe, arrowcolor=farbe)
    xs_alle = [p[0] for p in g.pos]
    ys_alle = [p[1] for p in g.pos]
    rand = 0.35 if g.n <= 10 else 0.06 * max(max(xs_alle) - min(xs_alle), max(ys_alle) - min(ys_alle), 1.0)
    # zwei unsichtbare Eckpunkte erzwingen den Rand; gleicher Maßstab über scaleanchor nur mit automatischem Bereich
    fig.add_trace(go.Scatter(x=[min(xs_alle) - rand, max(xs_alle) + rand], y=[min(ys_alle) - rand, max(ys_alle) + rand], mode="markers",
                             marker=dict(size=1, opacity=0), hoverinfo="skip", showlegend=False))
    fig.update_xaxes(visible=False, fixedrange=True)
    fig.update_yaxes(visible=False, fixedrange=True, scaleanchor="x", scaleratio=1)
    fig.update_layout(height=hoehe, margin=dict(l=5, r=5, t=30, b=5), dragmode=False, plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)")
    return fig
