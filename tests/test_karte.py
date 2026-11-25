"""Karte: Knotennummern für die Klickauswahl, feste Farben, volle Deckkraft nach einer Auswahl, gesperrte Achsen."""

import udz_karte as K
import udz_netze as N


def test_knoten_haben_nummern_und_behalten_die_deckkraft():
    g = N.handnetz()
    fig = K.karte(g, farben=["#000000"] * 6, marken={2: ("Start", "#ff0000"), 3: ("", "#00ff00")}, neue_kante=(0, 5))
    knoten = [t for t in fig.data if t.customdata is not None]
    assert len(knoten) == 1 and list(knoten[0].customdata) == list(range(6))
    assert knoten[0].selected.marker.opacity == 1 and knoten[0].unselected.marker.opacity == 1
    assert list(knoten[0].marker.color) == ["#000000"] * 6
    texte = [a.text for a in fig.layout.annotations]
    assert "<b>Start</b>" in texte and "<b></b>" not in texte
    assert fig.layout.xaxis.fixedrange and fig.layout.yaxis.fixedrange


def test_werte_farbskala_und_grosse_netze_ohne_beschriftung():
    g = N.saele_mit_flurknoten(65)
    fig = K.karte(g, werte=range(65), farbtitel="x")
    knoten = [t for t in fig.data if t.customdata is not None][0]
    assert knoten.marker.showscale and list(knoten.marker.color) == [float(i) for i in range(65)]
    assert len(fig.layout.annotations) == 0
