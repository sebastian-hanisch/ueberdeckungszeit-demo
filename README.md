# Bis jeder Ort besucht ist – Überdeckungszeit einer Irrfahrt auf Netzen – Streamlit-Demo

Demo der Reihe „Irrfahrten auf Netzen: von der Trefferzeit bis zum lokalen Schnitt“ (Bereich Graphentheorie). Die Demo „Trefferzeit“ misst, wie lange die Irrfahrt bis zu einem
bestimmten Ziel braucht. Diese Demo fragt auf demselben Handnetz und auf benannten Kontrastnetzen, wie lange es dauert, bis sie jeden Knoten mindestens einmal besucht hat,
und was mehrere Läufer vom selben Start daran ändern.

## Warum dieses Problem

Eine **Irrfahrt** (random walk) geht in jedem Schritt gleich wahrscheinlich zu einem Nachbarn; die **Überdeckungszeit** (cover time) ist die erwartete Zahl der Schritte, bis
jeder Platz mindestens einmal besucht ist (der Start zählt als besucht). Wie lange das dauert, hängt an Netz und Start: Auf zwei Sälen mit Flurknoten (65 Plätze) brauchen
8 Läufer aus der Flurmitte zusammen weniger als ein Fünftel der Schritte eines einzelnen, aus einem Saal-Innenplatz zusammen mehr.

## Modell

Einfaches, ungerichtetes, zusammenhängendes Netz; in jedem Schritt jeder Nachbar gleich wahrscheinlich, die Irrfahrt bleibt nie stehen (nicht träge). Alle Zeiten sind erwartete
Schritte; „t_cov“ meint den schlechtesten Start. **k Läufer** starten auf demselben Platz und gehen gleichzeitig; gezählt werden **Runden** und **Gesamtschritte** (k mal Runden).
S_k = Zeit eines Läufers / Rundenzahl von k Läufern; S_k / k > 1 heißt: Die k Läufer brauchen zusammen weniger Schritte als einer. (Alon u. a. bilden ihre Beschleunigung mit dem
schlechtesten Start je Läuferzahl; das ist eine andere Größe.) **Fester Rücksprung alle τ Schritte:** Ein Läufer wird nach je τ Schritten auf den Start gesetzt; der Sprung
zählt nicht als Schritt. Die Demo „Lokaler Schnitt“ benutzt einen zufälligen Neustart; er ist ein anderes Verfahren.

Netze:

- **Handnetze:** „zwei Hallen“ (Dreiecke {0,1,2} und {3,4,5}, Tür 2–3), 4-Kreis, Weg a–m–b, „zwei Hallen mit Flurknoten“ (7 Plätze, keine Tür 2–3).
- **Zwei Gitterhallen a×a** (a = 2 bis 8), eine Tür in Zeile a // 2. Eine neue Tür ist eine **Ergänzung**: Die vorhandene bleibt.
- **Zwei Säle mit Flurknoten** (Hantel nach Alon u. a.): zwei vollständige Säle mit je (n − 1) / 2 Plätzen, über einen Weg der Länge 2 verbunden, n = 17, 33, 65, 129.
- **Vergleichsnetze mit 14 Plätzen:** vollständiger Saal, Stern, Kreis, Weg, Saal mit Stichgang 9 + 5.
- Nur in den Gegner- und Gegenpol-Rechnungen: Barbell 48/32/48, Weg 128, Kreis 128, Gitter 11×11.

## Methodik

- **Ohne Zufall, ein Läufer:** bis 18 Plätze der Zustandsraum (besuchte Menge, Platz), von großen zu kleinen Mengen gelöst; auf den Sälen mit Flurknoten die zusammengefasste Kette über die Zahl der besuchten Innenplätze (bis 129 Plätze).
- **Ohne Zufall, k Läufer (bis 8 Plätze) und fester Rücksprung (kleine Netze):** Ein- und Ausschluss über gemiedene Platzmengen.
- **Matthews-Klammer und Mengenschranke** aus den Trefferzeiten (Mengenschranke durch Aufzählen aller Mengen, bis 18 Plätze).
- **Messungen:** vektorisierte Simulation mit SplitMix64 (`udz_irrfahrt_sim.py`, nur Ganzzahlen), feste Zufalls-Seeds je Zelle. Je Wert 40 000 Läufe, auf zwei Hallen 8×8 und auf dem Weg mit 128 Plätzen 100 000, bei den Gegenpolen 20 000. Intervalle sind 95-%-Intervalle des Mittels. Die Zeit eines Läufers kommt, wo es geht, ohne Zufall aus der Rechnung (auf den Sälen mit Flurknoten an jeder Stelle der Seite).
- **Schlechtester Start der Gitterhallen (a = 4 bis 8):** jeder Startplatz mit 4 000 Läufen gesichtet; die fünf längsten sowie Türplatz und ferne Ecke mit frischen Zufalls-Seeds nachgemessen.
- **Gegner fester Rücksprung und Läuferzahl:** τ und k je Netz und Start auf eigenen Zufalls-Seeds aus Rastern gewählt (20 000 Läufe je Rasterwert, auf dem Weg mit 128 Plätzen 10 000), dann auf anderen bewertet. Kleine Netze ohne Zufall (k von 2 an, τ bis 80). Zwei Werte gelten als unterscheidbar, wenn sich die Intervalle nicht überschneiden.
- **Gegner mit Karte:** Reihenfolge nach nächstem Nachbarn, 2-opt, in höchstens k Stücke geschnitten; jeder Plan wird nachgelaufen. Er ist eine obere Schranke für den kürzesten Plan; untere Schranke max(Entfernung zum fernsten Platz, ⌈(n − 1) / k⌉).
- **Vorgerechnet** (`tools/vorrechnen.py` → `daten/vorgerechnet.json`): alle Messungen und die Zählungen über kleine Netze.

## Befunde (gemessen, keine Behauptungen)

Alle Zahlen rechnet `tests/test_claims.py` nach (ohne Zufall neu gerechnet oder aus den gespeicherten Messungen gelesen; eine Stichprobe der Messzellen wird neu gerechnet).

### Bis alle besucht sind (ein Läufer)

| Frage | Befund |
|---|---|
| Handnetz „zwei Hallen“ | ab einer Hallenecke 812/39 ≈ 20,82, ab einem Türknoten 1741/78 ≈ 22,32 Schritte; Matthews-Klammer 4,57 bis 37,29; Mengenschranke 16,33 |
| Säle mit Flurknoten, ohne Zufall | ab Flurmitte 187,2 / 664,0 / 2 423,2 / 9 084,3 Schritte (n = 17, 33, 65, 129), ab einem Saal-Innenplatz 184,9 / 661,9 / 2 421,1 / 9 082,2 |
| Matthews-Klammer, Netze mit 14 Plätzen (schlechtester Start) | vollständiger Saal 41,34: oben und unten genau; Stern 81,68: oben 1,01-fach, Zeit 25,69-mal die untere; Kreis 91,00: 1,71 und 2,20; Weg 211,00: 2,55 und 66,35; Saal mit Stichgang 9 + 5, 395,22: 3,16 und 124,28. Mengenschranke: Zeit 1,00-, 1,01-, 1,50-, 1,25- und 11,22-mal die Schranke |
| Matthews-Klammer, zwei Hallen a = 3 bis 8 | obere Schranke 2,08-, 2,33-, 2,40-, 2,53-, 2,57- und 2,67-mal die Zeit; Zeit 6,9-, 8,1-, 6,3-, 6,9-, 6,4- und 6,8-mal die untere. Die Klammer sitzt auf den Hallen also weder genau noch extrem; „je nach Netzform genau oder weit daneben“ zeigen die Vergleichsnetze |
| Schlechtester Start, zwei Hallen 8×8 | 2 451 ± 7 Schritte am Platz R(6,2) (größter nachgemessener Wert; Türplatz 2 444 ± 7, ferne Ecke 2 409 ± 7). a = 3 ohne Zufall: 141,58 |
| Weg | der schlechteste Start ist nicht das Ende, sondern ein innerer Platz: bei 4, 6, 8, 10 Plätzen 11, 31, 61, 101 gegen 9, 25, 49, 81 |

### Eine Verbindung mehr (ein Läufer, schlechtester Start)

| Frage | Befund |
|---|---|
| Alle zusammenhängenden Netze mit 3 bis 7 Plätzen (994; je Netz bis auf Isomorphie, jede fehlende Verbindung einzeln) | 2 790 von 9 182 neuen Verbindungen verlängern die Zeit (30,4 %); 848 der 989 nicht vollständigen Netze haben mindestens eine solche; größter Faktor 1,18; kleinstes Beispiel 4-Kreis 6 → 6,8 |
| dieselbe Frage, andere Zähleinheiten | gleichwertige Verbindungen eines Netzes nur einmal: 1 926 von 5 832 (33,0 %); Netze mit nummerierten Plätzen: 6 153 454 von 19 116 131 (32,2 %) |
| 4-Kreis mit der Diagonale 0–2 | Überdeckungszeit 6 → 6,8; die Pendelzeit zwischen den Plätzen 1 und 3 steigt von 8 auf 10 |
| Handnetz „zwei Hallen“ | alle 8 neuen Verbindungen verkürzen (22,32 → 16,24 bis 19,13) |
| Zwei Hallen 2×2 | 4 von 19 verlängern, genau die vier innerhalb einer Halle (36,66 → bis 40,06); jede der 15 zwischen den Hallen verkürzt |
| Zwei Hallen 3×3 (alle 128, ohne Zufall) | 44 der 48 neuen Verbindungen innerhalb einer Halle verlängern, jede der 80 zwischen den Hallen verkürzt. Für größere Hallen nicht gerechnet |
| Eine oder mehr zusätzliche Türen (die vorhandene bleibt) | a = 3, schlechtester Start: 141,58 → 125,61 (zweite Tür in Zeile 0) → 115,36 (alle Zeilen). a = 4 bis 8, je ab Türplatz und ferner Ecke, jede übrige Zeile und alle Zeilen zusammen: in allen 60 Fällen kürzer (Intervalle getrennt). a = 8, ferne Ecke: 2 409 → 2 104 (Zeile 0) bzw. 1 842 (alle Zeilen) |

### Viele Läufer vom selben Start

| Frage | Befund |
|---|---|
| Handnetz, ohne Zufall | ab Türplatz: ein Läufer 22,32, zwei 10,51 Runden (21,02 gesamt), drei 7,09 (21,27); ab Ecke: 20,82, zwei 22,68 und drei 25,76 Gesamtschritte |
| Weg a–m–b ab m | zwei Läufer 7/3 Runden, also 4,67 Gesamtschritte statt 5 |
| Flurknoten-Netz ab Flurmitte | ein Läufer 34,86, zwei Läufer 29,79, vier 25,91 Gesamtschritte; ab Ecke zwei Läufer 34,93 |
| Säle mit Flurknoten, S_8/8 | n = 65: 5,57 ab Flurmitte, 0,79 ab Saal-Innenplatz, 0,85 ab Anschlussplatz; n = 129: 8,63, 0,85, 0,89. Von den drei Startarten spart k = 8 bei diesen Größen nur ab der Mitte. k = 32 ab der Mitte: 6,65 und 11,51 |
| k = 2 ab der Flurmitte (n = 65) | stark schief: Mittel rund 1 470, Median rund 510 Gesamtschritte |
| Zwei Hallen 8×8, S_k/k | Türplatz: 1,02 / 1,06 / 1,06 / 0,86 (k = 2, 4, 8, 32); ferne Ecke: 0,99 / 0,88 / 0,69 / 0,35, bei k = 32 also rund das 2,8-Fache der Schritte eines Läufers. Über a = 3 bis 8, beide Starts und alle getesteten k höchstens knapp 1,07: Der Gewinn ist auf diesen Hallen klein |
| Starts unabhängig nach der stationären Verteilung π, Hallen 8×8 | S_k/k = 1,03 / 1,22 / 1,55 (k = 2, 8, 32), ein Läufer 2 429 Schritte. Vorsicht: Verteilte Läufer haben beim Start schon bis zu k Plätze besucht, und das Aufstellen braucht Kenntnis des Netzes |
| Gegenpole (k = 8 und 32) | Kreis 128: 0,70 und 0,33; Weg 128 ab Ende: 0,47 und 0,20; Gitter 11×11 ab Mitte: 0,98 und 0,88 |
| Alle 994 Netze mit 3 bis 7 Plätzen, ohne Zufall | weder k = 2 noch k = 3 spart bei einem einzigen an allen Starts Gesamtschritte; k = 2 spart bei 704 an einem Teil der Starts, bei 290 an keinem. Mit 3 bis 6 Plätzen (141 Netze) gilt das auch für k = 4. Vollständiger Saal mit 8 Plätzen und Kreis mit 10: k = 2 an keinem Start |
| Weg mit 15 Plätzen, schlechtester Start je Läuferzahl | die Beschleunigung für zwei Läufer ist 2,117 |

### Gegner: fester Rücksprung und Karte

Gesamtschritte mit halber Breite des 95-%-Intervalls; τ und k auf eigenen Zufalls-Seeds gewählt, auf anderen bewertet (Läufe wie unter „Methodik“).

| Netz, Start | ein Läufer | beste getestete Läuferzahl (k) | fester Rücksprung (τ) |
|---|---|---|---|
| Zwei Säle mit Flurknoten 65, Flurmitte | 2 423 (ohne Zufall) | k = 24: 360,3 ± 1,0 | τ = 16: 343,8 ± 0,9 |
| Zwei Säle mit Flurknoten 129, Flurmitte | 9 084 (ohne Zufall) | k = 40: 788,3 ± 1,9 | τ = 20: 763,9 ± 1,8 |
| Barbell 48/32/48, Mitte des Wegs | 76 324 ± 732 | k = 10: 2 864 ± 51 | τ = 512: 2 029 ± 12 |
| Weg 128, Platz 63 | 20 161 (Formel i(L − i) + L²) | k = 4: 17 378 ± 79 | τ = 3 072: 16 889 ± 70 |
| Zwei Hallen 8×8, Türplatz | 2 444 ± 7 | k = 7: 2 303 ± 6 | τ = 448: 2 302 ± 7 |
| Zwei Hallen 8×8, ferne Ecke (kein Gewinn) | 2 409 ± 7 | k = 2: 2 440 ± 7 | τ = 16 384 (zweitgrößter Rasterwert, das Raster reicht bis 32 768): 2 413 ± 7 |
| Säle 65, Saal-Innenplatz (kein Gewinn) | 2 421 (ohne Zufall) | k = 2: 2 429 ± 21 | τ = 4 096: 2 424 ± 22 |
| Flurknoten-Netz, Mitte (ohne Zufall) | 34,86 | k = 5: 25,55 | τ = 4: 21 |
| Handnetz, Türplatz (ohne Zufall) | 22,32 | k = 2: 21,02 | τ = 7: 20,97 |
| Handnetz, Hallenecke (ohne Zufall, kein Gewinn) | 20,82 | k = 2: 22,68 | τ = 80 (Rasterrand): 20,83 |

- **Auf den fünf größeren Netzen mit Gewinn** brauchte der feste Rücksprung auf vier weniger Gesamtschritte als die beste getestete Läuferzahl (Säle 65 und 129, Barbell, Weg), auf den zwei Hallen ab dem Türplatz nicht unterscheidbar viele (dort brauchen beide rund 6 % weniger Gesamtschritte als ein einzelner Läufer). Er ist je Netz und Start abgestimmt.
- **Die Auswahl entscheidet bei flachem Raster mit.** In einer ersten Auswahlrunde mit 4 000 Läufen je Rasterwert (andere Zufalls-Seeds, nicht im Datensatz) war der Rücksprung an der Hallentür um 0,6 % teurer als die gewählte Läuferzahl (τ = 320, k = 5), die Intervalle knapp getrennt. Die Tabelle zeigt die zweite Runde mit mehr Auswahlläufen und neuen Zufalls-Seeds. Ein Unterschied um 1 % an dieser Stelle ist nicht als Vorteil eines Gegners zu lesen.
- **Kein allgemeiner Satz:** Unter allen 1 077 Paaren aus Netz (3 bis 7 Plätze) und Start, bei denen ein k von 2 bis 12 Gesamtschritte spart (gleichwertige Starts einzeln gezählt, ohne Zufall), braucht der beste Rücksprung mit τ bis 80 in 1 058 höchstens so viele Schritte wie das beste k und in 19 mehr, höchstens 2,1 % mehr.
- **Karte:** Auf zwei Hallen 8×8 ab dem Türplatz schafft der Plan mit 1, 2, 8 und 32 Läufern alles in 130, 64, 18 und 12 Runden (kein Plan unter 127, 64, 16, 12), Irrfahrer im Mittel in 2 444, 1 194, 289 und 89 Runden (rund 19-, 19-, 16- und 7-mal so viele). Ab der fernen Ecke 15,6- bis 17,8-mal bis k = 8, 9,3-mal bei k = 32. Säle 65 ab Flurmitte: k = 2, 8, 32 ergibt 32, 9, 3 Runden gegen 736, 54 und 11,4 (rund 23-, 6- und 4-mal). Handnetz ab Türplatz: zwei Läufer mit Karte 3 Runden gegen 10,51, ab Ecke 4 gegen 11,34 (dort ist der Plan der kürzeste, durch Aufzählung geprüft).
- **Wissen:** Irrfahrer kennen nur die Nachbarn (k je Netz und Start gewählt); der Rücksprung muss zum Start springen können, und τ ist je Netz und Start gewählt; der Plan braucht die ganze Karte und Absprache.

## Ehrliche Grenzen

- Die Zahlen gelten für die genannten Netze, Starts, Läuferzahlen und Rasterwerte. Ob mehrere Läufer oder der Rücksprung Gesamtschritte sparen, hängt an Netz und Start.
- Fester Rücksprung: τ ist je Netz und Start gewählt (Netzwissen), und der Sprung zum Start kostet nichts. Ebenso ist die Läuferzahl je Netz und Start gewählt.
- Die Beobachtung zu neuen Verbindungen innerhalb und zwischen den Hallen ist nur für 2×2 und 3×3 gerechnet.
- Der schlechteste Start der Gitterhallen ab 4×4 ist gemessen; nahe Werte lassen sich nicht sicher ordnen.
- Der Karten-Plan ist eine obere Schranke, nicht als kürzester Plan bewiesen; die genannten Faktoren „Irrfahrer gegen Plan“ sind deshalb Untergrenzen für den Faktor gegen den kürzesten Plan.
- Die Sätze zu vielen Läufern (Alon u. a.) und zur Kante (Barlow u. a.) sind Aussagen anderer Arbeiten, nicht nachgerechnet. Die Arbeit von Matthews (1988) ist nicht im Original eingesehen.
- Ein Literaturtest mit Zahlen aus einer Quelle fehlt (offen): Geschlossene Formeln (vollständiges Netz, Kreis, Weg vom Ende) werden an der eigenen Rechnung geprüft, nicht an einer abgedruckten Tabelle.
- Die Wahl des Starts per Klick auf die Karte ist nicht mit einem echten Mausklick bestätigt.

## Verifikation

- **Handrechnungen** (`tests/test_handbeispiele.py`): Handnetz, Weg a–m–b (7/3 für zwei Läufer, von Hand), 4-Kreis, Flurknoten-Netz, 2×2-Hallen, Karten-Pläne auf dem Handnetz.
- **Orakel** (`tests/test_oracle_ueberdeckungszeit.py`, `tests/orakel_hilfen.py`): Zustandsraum und Reihe gegen Ein-/Ausschluss in Brüchen (je gemiedene Menge ein System); fester Rücksprung gegen die Kette mit Phase; Säle gegen Aufzählung und gegen Ein-/Ausschluss über Symmetrieklassen in Brüchen; Mengenschranke gegen Aufzählung; Simulation gegen Rechnung (Band) und bitgleich gegen eine Schleifenfassung; Karten-Plan gegen die kürzesten Pläne aus der Breitensuche und gegen alle Zerlegungen.
- **Eigenschaften** (`tests/test_eigenschaften_ueberdeckungszeit.py`): Matthews- und Aleliunas-Schranke, mehr Läufer brauchen nie mehr Runden, Umnummerieren, träge Irrfahrt verdoppelt, kein Plan unter der unteren Schranke. Nicht geprüft werden „neue Verbindung verkürzt“, „S_k ≤ k“ und „Rücksprung höchstens so teuer wie k Läufer“: alle drei sind falsch.
- **Oberfläche:** AppTest (jedes Preset mit Verdikt, jedes Netz, jeder Gegner-Fall, Permalink), Layout, Footer, Laufzeit-Importe, Randfälle.
- Zusammen 469 Tests, seriell einige Minuten.

## Dateistruktur

| Datei | Zweck |
|---|---|
| `app.py` | Streamlit-App: ein Lauf Runde für Runde, Kernfragen, vier Experimente, Grenzen, Formeln |
| `udz_netze.py` | Netze der Demo (aus dem gemeinsamen Baustein der Demo „Trefferzeit“, erweitert) |
| `udz_exakt.py` | Zustandsraum, Reihe für k Läufer, Median, fester Rücksprung |
| `udz_hantel.py` | zusammengefasste Kette für die Säle mit Flurknoten |
| `udz_trefferzeit.py` | Trefferzeiten (für Matthews und die Pendelzeit) |
| `udz_matthews.py` | Matthews-Klammer und Mengenschranke |
| `udz_irrfahrt_sim.py`, `udz_rng.py` | Simulation mit SplitMix64 |
| `udz_messung.py` | eine Messzelle mit festem Zufalls-Seed |
| `udz_plan.py` | Gegner mit Karte: Plan, Nachlauf-Prüfung, untere Schranke, exakte Suche auf Kleinstnetzen |
| `udz_evaluation.py` | Kennzahlen und Verdikte |
| `udz_szenario.py`, `udz_constants.py`, `udz_presets.py`, `udz_layout.py` | Netzwahl, Grenzen und Raster, Presets und Permalink, fester Kopf |
| `udz_karte.py`, `udz_visualization.py`, `udz_daten.py` | Karte, Diagramme, gespeicherte Zahlen |
| `tools/vorrechnen.py`, `tools/udz_atlas.py`, `daten/vorgerechnet.json` | Vorrechnen; Zählungen über alle kleinen Netze |
| `tests/` | Handrechnungen, Orakel, Eigenschaften, Randfälle, Verdikte, Claims, AppTest, Layout, Footer, Laufzeit-Importe |

## Bewusst nicht umgesetzt

- **Spannbäume:** Die [Demo zu zufälligen Spannbäumen](https://sebastianhanisch-random-spanning-tree-demo.streamlit.app/) lässt eine Irrfahrt von der Wurzel laufen, bis alle Plätze gesehen sind (Aldous-Broder). Hier geht es nur um die Zeit.
- Keine gerichteten oder gewichteten Netze, keine träge Kette (sie verdoppelt die Zeit), keine Mischzeit.
- Sätze zu vielen Läufern (Alon u. a.) und zur Wirkung einer Kante (Barlow u. a.) werden nur genannt.
- Kein Barbell-Wert für die Beschleunigung: Er streut stark.

## Lokal ausführen

```bash
python3 -m venv venv
source venv/bin/activate          # Windows: venv\Scripts\activate

pip install -r requirements.txt
streamlit run app.py
```

Neu vorrechnen (dauert mehrere Minuten, mit `OMP_NUM_THREADS=1`; braucht `requirements-dev.txt`): `python tools/vorrechnen.py alle`.

## Tests ausführen

```bash
pip install -r requirements-dev.txt
pytest tests/ -v
```

Gebaut mit Streamlit, Plotly und NumPy.

---

Diese Demo ist Teil des Portfolios von [Sebastian Hanisch](https://sebastianhanisch.net) – Operations Research und Machine Learning ([Über mich](https://sebastianhanisch.net/ueber-mich.html)). Mehr zur Reihe: [Irrfahrten auf Netzen: Trefferzeit bis Schnitt](https://sebastianhanisch.net/konzepte-irrfahrten.html).
