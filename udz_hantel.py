"""Überdeckungszeit eines Läufers auf „zwei Säle mit Flurknoten“ ohne Zufall, für große Säle (ohne Streamlit, nur numpy).

Die Plätze eines Saals außer dem Anschlussplatz sind untereinander gleichwertig. Es genügt deshalb, je Saal zu zählen, **wie viele** Innenplätze besucht sind:
Zustand = (Flurmitte besucht?, Anschluss A?, Anschluss B?, besuchte Innenplätze in A, in B) und der Platz-Typ, auf dem der Läufer steht. Die besuchte Menge wächst nur,
also wird von vielen zu wenigen besuchten Plätzen gerechnet; je Zustandsklasse ein Gleichungssystem mit höchstens 5 Unbekannten (zusammengefasste Kette).
Der unabhängige zweite Weg (Ein-/Ausschluss über Symmetrieklassen gemiedener Mengen in Brüchen) steht im Orakel-Test.

Platz-Typen: 'F' Flurmitte, 'a' Anschlussplatz (Saal A), 'i' Innenplatz (Saal A). Saal B ist spiegelgleich.
"""

import numpy as np

TYPEN = ("F", "a", "i")


def typ_von(n: int, platz: int) -> str:
    """Typ eines Platzes in `udz_netze.saele_mit_flurknoten(n)`."""
    m = (n - 1) // 2
    if platz == m:
        return "F"
    if platz in (m - 1, m + 1):
        return "a"
    return "i"


def ueberdeckung(n: int) -> dict:
    """{'F': C_1 ab Flurmitte, 'a': ab Anschlussplatz, 'i': ab einem Saal-Innenplatz}."""
    if n < 5 or n % 2 == 0:
        raise ValueError("n ungerade und mindestens 5")
    r = (n - 1) // 2 - 1                                   # Innenplätze je Saal
    # Orte: 0 = Flur, 1 = Anschluss A, 2 = Anschluss B, 3 = (irgendein besuchter) Innenplatz A, 4 = Innenplatz B
    E = {}
    m = r + 1                                              # Plätze je Saal
    zustaende = [(f, a, b, x, y) for f in (0, 1) for a in (0, 1) for b in (0, 1) for x in range(r + 1) for y in range(r + 1)]
    zustaende.sort(key=lambda z: -sum(z))
    voll = (1, 1, 1, r, r)
    for z in zustaende:
        f, a, b, x, y = z
        orte = [o for o, da in enumerate((f, a, b, x > 0, y > 0)) if da]
        if z == voll:
            for o in orte:
                E[z, o] = 0.0
            continue
        if not orte:
            continue
        ix = {o: i for i, o in enumerate(orte)}
        M = np.eye(len(orte))
        rhs = np.ones(len(orte))

        def gehe(zeile, wahrsch, ziel_z, ziel_o):
            if wahrsch == 0:
                return
            if ziel_z == z:
                M[zeile, ix[ziel_o]] -= wahrsch
            else:
                rhs[zeile] += wahrsch * E[ziel_z, ziel_o]

        for o in orte:
            i = ix[o]
            if o == 0:                                     # Flur: je 1/2 zu Anschluss A und B
                gehe(i, 0.5, (f, 1, b, x, y), 1)
                gehe(i, 0.5, (f, a, 1, x, y), 2)
            elif o in (1, 2):                              # Anschluss: Grad m (Flur + r Innenplätze)
                gehe(i, 1 / m, (1, a, b, x, y), 0)
                innen = x if o == 1 else y
                ziel_o = 3 if o == 1 else 4
                gehe(i, innen / m, z, ziel_o)              # schon besuchter Innenplatz
                if innen < r:
                    gehe(i, (r - innen) / m, (f, a, b, x + 1, y) if o == 1 else (f, a, b, x, y + 1), ziel_o)
            else:                                          # Innenplatz: Grad m−1 (Anschluss + r−1 andere Innenplätze)
                saal_a = o == 3
                anker = 1 if saal_a else 2
                innen = x if saal_a else y
                grad = m - 1
                gehe(i, 1 / grad, (f, 1, b, x, y) if saal_a else (f, a, 1, x, y), anker)
                gehe(i, (innen - 1) / grad, z, o)          # anderer schon besuchter Innenplatz
                if innen < r:
                    gehe(i, (r - innen) / grad, (f, a, b, x + 1, y) if saal_a else (f, a, b, x, y + 1), o)
        try:
            loesung = np.linalg.solve(M, rhs)
        except np.linalg.LinAlgError:                      # nicht erreichbare Klasse ohne Ausgang
            continue
        for o in orte:
            E[z, o] = float(loesung[ix[o]])
    return {"F": E[(1, 0, 0, 0, 0), 0], "a": E[(0, 1, 0, 0, 0), 1], "i": E[(0, 0, 0, 1, 0), 3]}
