"""Simulation: Zufallsfolge, Ziehregel, Rücksprung, Deckel und Fehlerfälle."""

import numpy as np
import pytest

import udz_irrfahrt_sim as S
import udz_netze as N
from udz_rng import SplitMix64


@pytest.mark.parametrize("seed", [0, 1, 12345, (1 << 64) - 1])
def test_blockzufall_ist_die_folge_von_splitmix64(seed):
    block = S.BlockZufall(seed)
    erste, zweite = block.u64(7), block.u64(5)
    rng = SplitMix64(seed)
    assert [int(x) for x in np.concatenate([erste, zweite])] == [rng.next_u64() for _ in range(12)]


def test_waehle_bleibt_unter_dem_grad_und_trifft_jeden_nachbarn():
    w = S.BlockZufall(3).u64(30000)
    grad = np.full(30000, 7, dtype=np.uint64)
    z = S.waehle(w, grad)
    assert z.max() < 7 and set(np.unique(z).tolist()) == set(range(7))
    anteile = np.bincount(z.astype(np.int64), minlength=7) / len(z)
    assert np.abs(anteile - 1 / 7).max() < 0.01
    assert [int(x) for x in z[:5]] == [((int(v) >> 32) * 7) >> 32 for v in w[:5]]


def test_weg_a_m_b_ein_laeufer_hat_ungerade_zeiten_ab_der_mitte():
    r = S.simuliere_ueberdeckung(N.weg_amb(), 1, 1, 500, 8)
    assert set((r % 2).tolist()) == {1} and r.min() == 3


def test_deckel_markiert_nicht_fertige_laeufe():
    r = S.simuliere_ueberdeckung(N.weg(20), 0, 1, 5, 1, max_runden=10)
    assert (r == -1).all()
    with pytest.raises(ValueError):
        S.kennzahlen(r, 1)


def test_ruecksprung_zu_kurz_oder_mit_startfeld_wird_abgewiesen():
    g = N.flurnetz()
    with pytest.raises(ValueError):
        S.simuliere_ueberdeckung(g, 6, 1, 10, 1, tau=1)                  # Ecken liegen 2 Schritte entfernt
    with pytest.raises(ValueError):
        S.simuliere_ueberdeckung(g, np.zeros((10, 1), dtype=int), 1, 10, 1, tau=5)


def test_startfeld_zaehlt_die_startplaetze_als_besucht():
    g = N.weg(3)
    starts = np.array([[0, 1, 2], [0, 0, 2]])
    r = S.simuliere_ueberdeckung(g, starts, 3, 2, 4)
    assert r[0] == 0 and r[1] >= 1
    with pytest.raises(ValueError):
        S.simuliere_ueberdeckung(g, 5, 1, 3, 1)
    with pytest.raises(ValueError):
        S.simuliere_ueberdeckung(N.netz("x", 4, [(0, 1)]), 0, 1, 3, 1)


def test_stationaere_ziehung_folgt_dem_grad():
    g = N.stern(5)
    z = S.zieh_stationaer(g, 40000, 11)
    anteil = np.bincount(z, minlength=5) / len(z)
    assert anteil[0] == pytest.approx(0.5, abs=0.01) and np.abs(anteil[1:] - 0.125).max() < 0.01


def test_kennzahlen():
    k = S.kennzahlen(np.array([2, 4, 9]), 2)
    assert k["runden"] == 5 and k["median"] == 4 and k["se"] == pytest.approx(np.std([2, 4, 9], ddof=1) / np.sqrt(3))


def test_verlauf_haelt_beim_deckel_an():
    spur, erste, fertig = S.verlauf(N.weg(30), 0, 1, 1, max_runden=5)
    assert not fertig and len(spur) == 6 and (erste == -1).sum() > 0
