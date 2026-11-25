"""Matthews-Klammer und Mengenschranke für die Überdeckungszeit (ohne Streamlit, nur numpy).

Mit t_cov = Überdeckungszeit des schlechtesten Starts, H_max bzw. H_min = größte bzw. kleinste Trefferzeit zwischen zwei verschiedenen Plätzen und
h_k = 1 + 1/2 + … + 1/k gilt (Levin, Peres, Wilmer, Markov Chains and Mixing Times, Kapitel 11):

    H_min · h_(n−1) ≤ t_cov ≤ H_max · h_(n−1)

und schärfer für jede Platzmenge A mit mindestens 2 Elementen: t_cov ≥ (kleinste Trefferzeit zwischen zwei Plätzen aus A) · h_(|A|−1). Die **Mengenschranke**
ist das Maximum dieser rechten Seite über alle A (hier durch Aufzählung aller 2^n Mengen, nur auf kleinen Netzen).
"""

import numpy as np

MAX_MENGEN = 18


def harmonisch(k: int) -> float:
    return float(sum(1.0 / i for i in range(1, k + 1)))


def klammer(H: np.ndarray) -> dict:
    """H_max, H_min, untere und obere Matthews-Schranke aus der Trefferzeiten-Matrix."""
    n = len(H)
    ausserhalb = ~np.eye(n, dtype=bool)
    hmax, hmin = float(H[ausserhalb].max()), float(H[ausserhalb].min())
    h = harmonisch(n - 1)
    return {"hmax": hmax, "hmin": hmin, "unten": hmin * h, "oben": hmax * h}


def mengenschranke(H: np.ndarray):
    """(Wert, Menge als Liste): größtes min H(u, v) (u ≠ v aus A) · h_(|A|−1) über alle Mengen A mit mindestens 2 Plätzen."""
    n = len(H)
    if n > MAX_MENGEN:
        raise ValueError(f"Mengenschranke nur bis {MAX_MENGEN} Plätze")
    paar = np.minimum(H, H.T)                                      # beide Richtungen zählen
    alle = np.arange(1 << n, dtype=np.int64)
    kleinste = np.full(1 << n, np.inf)
    for w in range(n):                                              # Mengen mit höchstem Platz w aus der Menge ohne w aufbauen
        ohne = alle[: 1 << w]
        zusatz = np.full(1 << w, np.inf)
        for u in range(w):
            hat = ((ohne >> u) & 1).astype(bool)
            zusatz[hat] = np.minimum(zusatz[hat], paar[u, w])
        kleinste[(1 << w) + ohne] = np.minimum(kleinste[ohne], zusatz)
    anzahl = ((alle[:, None] >> np.arange(n)) & 1).sum(axis=1)
    h = np.array([harmonisch(max(c - 1, 0)) for c in range(n + 1)])
    wert = np.where(anzahl >= 2, kleinste, 0.0) * h[anzahl]
    wert[anzahl < 2] = -1.0
    best = int(np.argmax(wert >= wert.max() - 1e-9))                # erste (kleinste) Menge unter den Gleichstanden
    return float(wert.max()), [i for i in range(n) if best >> i & 1]
