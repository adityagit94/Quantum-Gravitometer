"""v1.2.0 — pulse-center timing flag + finite-ensemble floor characterisation.

Two investigations from v1.2.0, captured as regression tests:

1. The `pulse_center_timing` flag on the integrated-phase propagator toggles
   whether the chirp term is evaluated at the pulse start (default) or centre.
   Empirically pulse-centre does NOT reduce the constant calibration residual
   (it enlarges it), so the default is pulse-start; the flag is retained for
   reproducibility.  Either way the residual is gravity-independent and removed
   by the calibration, so the *measured g* is unaffected.

2. The simulated short-term ASD has a finite-ensemble projection floor that
   scales as 1/sqrt(N_atoms).  This is why the v1.1 published-reference tests
   needed wide tolerances at N=300, and why v1.2 raised them to N=4000 (floor
   below the injected budget).
"""
from __future__ import annotations

import math

import numpy as np
import pytest

from qgrav.sim_ai._aisim_overrides import (
    ChirpedWavevectors,
    IntegratedPhaseSpatialSuperpositionTransitionPropagator,
)
from qgrav.sim_ai import aisim_adapter as A
from qgrav.physics.constants import WAVELENGTH_RB87_D2


def _ensemble(n_atoms=300, seed=1):
    _, atoms, _, _, _ = A._create_detected_ensemble(
        n_atoms=n_atoms, seed=seed, cloud_radius_m=3e-3,
        temp_xy_K=2.5e-6, temp_z_K=100e-9,
        detector_time_s=778e-3, detector_radius_m=5e-3, multiport=True,
    )
    return atoms


class TestPulseCenterFlag:
    """The flag exists, defaults to pulse-start, and toggles the imprint."""

    def test_default_is_pulse_start(self):
        prop = IntegratedPhaseSpatialSuperpositionTransitionPropagator(
            23e-6, intensity_profile=A._gaussian_beam(beam_radius_m=0.015,
                                                      center_rabi_freq_hz=12.5e3),
            n_pulses=3, n_pulse=1,
        )
        assert prop.pulse_center_timing is False

    def test_flag_can_be_enabled(self):
        prop = IntegratedPhaseSpatialSuperpositionTransitionPropagator(
            23e-6, intensity_profile=A._gaussian_beam(beam_radius_m=0.015,
                                                      center_rabi_freq_hz=12.5e3),
            n_pulses=3, n_pulse=1, pulse_center_timing=True,
        )
        assert prop.pulse_center_timing is True

    def test_pulse_center_changes_residual_but_both_calibrate(self):
        """Pulse-centre and pulse-start give different residual offsets, but
        both are gravity-independent and absorbed by the calibration.

        We measure the calibration offset for each; they must differ (the flag
        has an effect) yet both be finite (a valid fringe is found either way).
        The calibration runs through `_run_mach_zehnder_sequence_with_gravity`,
        which constructs propagators with the default flag, so we verify the
        flag's effect directly at the propagator level instead.
        """
        tau, T, gc = 23e-6, 0.26, 9.81
        k1 = 2 * np.pi / float(WAVELENGTH_RB87_D2)
        k_eff = 2 * k1
        beam = A._gaussian_beam(beam_radius_m=29.5e-3 / 2, center_rabi_freq_hz=12.5e3)
        wv = ChirpedWavevectors(k1=k1, k2=-k1, chirp_rate_rad_per_s2=-k_eff * gc)
        atoms = _ensemble(n_atoms=200, seed=1)

        def bs2_matrix(pulse_center):
            prop = IntegratedPhaseSpatialSuperpositionTransitionPropagator(
                tau, intensity_profile=beam, n_pulses=3, n_pulse=3,
                wave_vectors=wv, phase_scan=0.0, pulse_center_timing=pulse_center,
            )
            # Advance atoms to the bs2 time so atoms.time reflects a late pulse.
            a = A.GravityFreePropagator(2 * T, g_m_s2=gc).propagate(atoms)
            return prop._prop_matrix(a)

        u_start = bs2_matrix(False)
        u_center = bs2_matrix(True)
        assert np.all(np.isfinite(u_start)) and np.all(np.isfinite(u_center))
        # The two time conventions must give a genuinely different propagator
        # (the chirp term differs by 0.5*chirp*((t0+tau/2)^2 - t0^2)), while the
        # magnitudes (populations) are unchanged because it is a pure phase.
        assert np.abs(u_start - u_center).max() > 1e-6, "flag had no effect"
        np.testing.assert_allclose(np.abs(u_start), np.abs(u_center), atol=1e-9)


class TestFiniteEnsembleFloor:
    """The simulated ASD floor scales as 1/sqrt(N_atoms) — the reason v1.2
    raised the benchmark ensemble size."""

    @pytest.mark.slow
    def test_ensemble_floor_scales_inverse_sqrt_n(self):
        from qgrav.sim_ai.aisim_adapter import run_aisim_multi_drop_cycle

        def floor(n_atoms):
            r = run_aisim_multi_drop_cycle(
                n_drops=60, seed=2016, n_atoms=n_atoms,
                interferometer_time_s=0.26, cycle_time_s=1.5,
                gravity_propagation=True, detection_noise_enabled=False,
                raman_phase_noise_rad=0.0, fit_visibility=True,
            )
            return float(r["std_g_m_s2"])

        f300 = floor(300)
        f1200 = floor(1200)
        # Expect f300 / f1200 ~ sqrt(1200/300) = 2.0; allow a generous band.
        ratio = f300 / f1200
        assert 1.4 < ratio < 2.8, (
            f"ensemble floor ratio {ratio:.2f} not ~sqrt(4)=2 "
            f"(f300={f300:.2e}, f1200={f1200:.2e})"
        )
