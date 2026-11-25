"""Trefferzeiten H(u, v) der einfachen, nicht trägen Irrfahrt auf einem zusammenhängenden, einfachen, ungerichteten Netz (ohne Streamlit, nur numpy).

Gekürzt kopiert aus dem gemeinsamen Baustein `trz_trefferzeit` der Demo „Trefferzeit“ (ohne den dünn besetzten Weg und die Tetali-Formel). Braucht `udz_netze`.

H(u, v) = erwartete Zahl der Schritte von u bis zum ersten Besuch von v; H(v, v) = 0. Zwei Rechenwege: `treffer_matrix` (Fundamentalmatrix) und `treffer_je_ziel`
(je Ziel ein Gleichungssystem h = 1 + P h mit h(v) = 0).
"""

import numpy as np

import udz_netze as N


def _pruefe(g: N.Netz) -> None:
    if g.n < 2 or not N.ist_zusammenhaengend(g):
        raise ValueError("Trefferzeiten nur für zusammenhängende Netze mit mindestens 2 Knoten")


def stationaer(g: N.Netz) -> np.ndarray:
    """Stationäre Verteilung der Irrfahrt: π(v) = Grad(v) / (2·Kantenzahl)."""
    d = N.grade(g).astype(float)
    return d / d.sum()


def uebergang(g: N.Netz) -> np.ndarray:
    _pruefe(g)
    A = N.adjazenz(g)
    return A / A.sum(axis=1, keepdims=True)


def treffer_matrix(g: N.Netz) -> np.ndarray:
    """Alle Trefferzeiten auf einmal aus der Fundamentalmatrix Z = (I − P + 1πᵀ)⁻¹: H(u, v) = (Z_vv − Z_uv) / π_v."""
    P = uebergang(g)
    pi = stationaer(g)
    Z = np.linalg.inv(np.eye(g.n) - P + np.outer(np.ones(g.n), pi))
    H = (np.diag(Z)[None, :] - Z) / pi[None, :]
    np.fill_diagonal(H, 0.0)
    return H


def treffer_je_ziel(g: N.Netz) -> np.ndarray:
    """Alle Trefferzeiten, je Ziel ein Gleichungssystem (zweiter Rechenweg)."""
    P = uebergang(g)
    H = np.zeros((g.n, g.n))
    for v in range(g.n):
        rest = [u for u in range(g.n) if u != v]
        H[rest, v] = np.linalg.solve(np.eye(g.n - 1) - P[np.ix_(rest, rest)], np.ones(g.n - 1))
    return H


def pendelzeit(H: np.ndarray, u: int, v: int) -> float:
    """Pendelzeit: von u nach v und zurück."""
    return float(H[u, v] + H[v, u])


def residuum(g: N.Netz, H: np.ndarray) -> float:
    """Größte relative Verletzung der Gleichung H(u, v) = 1 + Mittel der H(w, v) über die Nachbarn w von u (u ≠ v) und H(v, v) = 0."""
    rest = H - 1.0 - uebergang(g) @ H
    np.fill_diagonal(rest, 0.0)
    return float(max(np.abs(rest).max(), np.abs(np.diag(H)).max()) / max(1.0, float(np.abs(H).max())))
