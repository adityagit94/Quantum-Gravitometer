"""Tests for chirped laser detuning in Wavevectors — Phase 2 of v1.0 upgrade."""
from __future__ import annotations

import numpy as np
import pytest

from qgrav.vendor.aisim import AtomicEnsemble
from qgrav.vendor.aisim import Wavevectors as UpstreamWavevectors
# v1.1 (Phase 12): the chirp extension lives in qgrav.sim_ai as a subclass;
# the vendored Wavevectors is upstream-clean (no chirp parameter).
from qgrav.sim_ai import ChirpedWavevectors as Wavevectors


def _single_atom(vz=0.0, time=0.0):
    """Create a 1-atom ensemble with given vz and time."""
    psv = np.array([[0.0, 0.0, 0.0, 0.0, 0.0, vz]], dtype=np.float64)
    atoms = AtomicEnsemble(psv, state_kets=[1, 0], time=time)
    return atoms


class TestChirpZeroMatchesOriginal:
    """chirp_rate_rad_per_s2=0 must give identical results to unmodified code."""

    def test_chirp_zero_matches_original(self):
        # Compare the ChirpedWavevectors subclass (chirp=0) against the
        # upstream-clean vendored Wavevectors — they must be identical.
        wv_orig = UpstreamWavevectors()
        wv_chirp = Wavevectors(chirp_rate_rad_per_s2=0.0)
        atoms = _single_atom(vz=0.05, time=0.26)
        d1 = wv_orig.doppler_shift(atoms)
        d2 = wv_chirp.doppler_shift(atoms)
        np.testing.assert_array_equal(d1, d2)

    def test_chirp_zero_multiple_velocities(self):
        """Multi-atom ensemble: chirp=0 matches upstream for all atoms."""
        psv = np.zeros((5, 6), dtype=np.float64)
        psv[:, 5] = np.linspace(-0.1, 0.1, 5)  # range of vz
        atoms = AtomicEnsemble(psv, state_kets=[1, 0], time=0.15)
        wv_orig = UpstreamWavevectors()
        wv_chirp = Wavevectors(chirp_rate_rad_per_s2=0.0)
        d1 = wv_orig.doppler_shift(atoms)
        d2 = wv_chirp.doppler_shift(atoms)
        np.testing.assert_array_equal(d1, d2)


class TestChirpCancelsGravityDoppler:
    """With chirp = −k_eff·g, detuning = −v_thermal·k_eff regardless of time."""

    def test_chirp_cancels_gravity_doppler(self):
        k1 = 8055366  # Rb-87 D2, rad/m
        k2 = -8055366
        k_eff = k1 - k2  # 16110732 rad/m
        g = 9.81  # m/s²
        chirp_rate = -k_eff * g  # cancels gravity Doppler
        v_thermal = 0.005  # 5 mm/s thermal velocity

        wv = Wavevectors(k1=k1, k2=k2, chirp_rate_rad_per_s2=chirp_rate)

        # For a falling atom: v_z(t) = v_thermal - g*t
        # Doppler without chirp: -(v_thermal - g*t) * k_eff = -v_thermal*k_eff + g*t*k_eff
        # Chirp adds: chirp * t = -k_eff*g*t
        # Total: -v_thermal*k_eff + g*t*k_eff - k_eff*g*t = -v_thermal*k_eff
        expected = -v_thermal * k_eff

        for t in [0.0, 0.1, 0.26, 0.5]:
            vz_t = v_thermal - g * t
            atoms = _single_atom(vz=vz_t, time=t)
            shift = wv.doppler_shift(atoms)
            np.testing.assert_allclose(shift[0], expected, rtol=1e-10,
                                       err_msg=f"Failed at t={t}")


class TestChirpUnitsConsistency:
    """k_eff·g ≈ 1.58e8 rad/s² — verify dimensional correctness."""

    def test_chirp_units_consistency(self):
        k1 = 8055366  # rad/m
        k2 = -8055366
        k_eff = k1 - k2  # 16110732 rad/m
        g = 9.81  # m/s²
        chirp = k_eff * g  # rad/m * m/s² = rad/s²

        # Expected: ~1.58e8 rad/s²
        assert 1.5e8 < chirp < 1.7e8, f"k_eff*g = {chirp:.3e}, expected ~1.58e8"

    def test_chirp_shifts_linearly_with_time(self):
        """Chirp term contributes linearly in time to Doppler shift."""
        chirp_rate = 1e6  # 1 Mrad/s²
        wv = Wavevectors(chirp_rate_rad_per_s2=chirp_rate)

        # Zero-velocity atom — only chirp matters
        atoms_t0 = _single_atom(vz=0.0, time=0.0)
        atoms_t1 = _single_atom(vz=0.0, time=1.0)
        atoms_t2 = _single_atom(vz=0.0, time=2.0)

        d0 = wv.doppler_shift(atoms_t0)[0]
        d1 = wv.doppler_shift(atoms_t1)[0]
        d2 = wv.doppler_shift(atoms_t2)[0]

        # d(t) = chirp_rate * t (for vz=0)
        np.testing.assert_allclose(d0, 0.0, atol=1e-10)
        np.testing.assert_allclose(d1, chirp_rate * 1.0, rtol=1e-10)
        np.testing.assert_allclose(d2, chirp_rate * 2.0, rtol=1e-10)
