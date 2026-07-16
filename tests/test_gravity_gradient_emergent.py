"""Cross-validate the EMERGENT gravity-gradient phase against the closed form.

In fully-simulated mode the gradient phase is never injected analytically: it
emerges from GravityFreePropagator's O(gamma) trajectory + the integrated
laser phase.  These tests measure that emergent phase with the fringe-scan
calibration helper (run at g = g_chirp, where the uniform-gravity phase and
the pulse-timing artefact are common to both runs and cancel in the
difference) and compare it against

    dphi = k_eff * gamma * T^2 * [ (z0 - z_ref) + v0*T - (7/12)*g*T^2 ]

(Peters, Chung & Chu, Metrologia 38, 25 (2001)), plus an order-of-magnitude
consistency check against the report-level systematics estimate.
"""

from __future__ import annotations

import numpy as np

from qgrav.physics.ground_truth import expected_gravity_gradient_phase_rad
from qgrav.physics.phase_models import gravity_gradient_phase_rad
from qgrav.sim_ai._adapter_core import (
    _calibrate_gravity_phase_offset,
    _create_detected_ensemble,
    _gaussian_beam,
    _wave_vectors,
)

WAVELENGTH_M = 780e-9
K_EFF = 2.0 * (2.0 * np.pi / WAVELENGTH_M)
G0 = 9.81
T_S = 0.13
TAU_S = 17e-6
# Chosen for a ~0.4 rad emergent shift: measurable on the fringe, while
# gamma*T^2 ~ 2e-7 keeps the O(gamma^2) truncation utterly negligible.
GAMMA_TEST = 1.2e-5


class TestGradientClosedForm:
    def test_zero_gradient_gives_zero_phase(self):
        assert (
            gravity_gradient_phase_rad(
                k_eff_rad_per_m=K_EFF,
                gravity_gradient_per_m=0.0,
                g_m_s2=G0,
                interferometer_time_s=T_S,
            )
            == 0.0
        )

    def test_dropped_atom_term_is_seven_twelfths(self):
        phi = gravity_gradient_phase_rad(
            k_eff_rad_per_m=K_EFF,
            gravity_gradient_per_m=GAMMA_TEST,
            g_m_s2=G0,
            interferometer_time_s=T_S,
        )
        expected = -K_EFF * GAMMA_TEST * (7.0 / 12.0) * G0 * T_S**4
        np.testing.assert_allclose(phi, expected, rtol=1e-12)

    def test_position_and_velocity_terms(self):
        z0, v0 = 0.002, 0.01
        phi = gravity_gradient_phase_rad(
            k_eff_rad_per_m=K_EFF,
            gravity_gradient_per_m=GAMMA_TEST,
            g_m_s2=G0,
            interferometer_time_s=T_S,
            initial_position_m=z0,
            initial_velocity_m_s=v0,
        )
        expected = K_EFF * GAMMA_TEST * T_S**2 * (z0 + v0 * T_S - (7.0 / 12.0) * G0 * T_S**2)
        np.testing.assert_allclose(phi, expected, rtol=1e-12)


def _measure_emergent_phase_offset(gamma: float):
    """Fringe-scan phase offset at g = g_chirp for a given gradient."""
    _ais, atoms, _det, _count, _cfg = _create_detected_ensemble(
        n_atoms=400,
        seed=42,
        cloud_radius_m=0.003,
        temp_xy_K=3e-6,
        temp_z_K=1.5e-7,
        detector_time_s=0.01,
        detector_radius_m=1.0,
        multiport=True,
    )
    beam = _gaussian_beam(beam_radius_m=1.0, center_rabi_freq_hz=1.0 / (4.0 * TAU_S))
    wv = _wave_vectors(wavelength_m=WAVELENGTH_M, chirp_rate_rad_per_s2=-K_EFF * G0)
    offset = _calibrate_gravity_phase_offset(
        atoms,
        tau_pi_half_s=TAU_S,
        interferometer_time_s=T_S,
        intensity_profile=beam,
        wave_vectors=wv,
        g_chirp_m_s2=G0,
        gravity_gradient_per_m=gamma,
        z_ref_m=0.0,
    )
    z0_mean = float(np.mean(atoms.position[:, 2]))
    v0_mean = float(np.mean(atoms.velocity[:, 2]))
    return offset, z0_mean, v0_mean


def test_emergent_gradient_phase_matches_closed_form():
    offset_no_gradient, _, _ = _measure_emergent_phase_offset(0.0)
    offset_with_gradient, z0_mean, v0_mean = _measure_emergent_phase_offset(GAMMA_TEST)
    emergent_shift = offset_with_gradient - offset_no_gradient

    expected_shift = expected_gravity_gradient_phase_rad(
        k_eff_rad_per_m=K_EFF,
        gravity_gradient_per_m=GAMMA_TEST,
        g_m_s2=G0,
        interferometer_time_s=T_S,
        initial_position_m=z0_mean,
        initial_velocity_m_s=v0_mean,
    )
    # The calibration offset moves opposite to the natural fringe phase
    # (it is the phase_scan value that re-centres the fringe), hence the
    # sign relation is pinned by this test.  Observed agreement is ~0.12%
    # (73-point fringe-fit discretisation + finite-tau in-pulse effects);
    # 0.5% gives 4x margin.
    np.testing.assert_allclose(emergent_shift, -expected_shift, rtol=0.005)


def test_emergent_gradient_consistent_with_systematics_estimate():
    """The report-level order-of-magnitude estimate gamma*(h + g*T^2/2) must
    agree with the emergent shift within a factor of 2 (the exact trajectory
    coefficient is 7/12 vs the estimate's 1/2)."""
    from qgrav.physics.systematics import gravity_gradient_shift_m_s2

    offset_no_gradient, _, _ = _measure_emergent_phase_offset(0.0)
    offset_with_gradient, _, _ = _measure_emergent_phase_offset(GAMMA_TEST)
    emergent_g_shift = abs(offset_with_gradient - offset_no_gradient) / (K_EFF * T_S**2)

    estimate = gravity_gradient_shift_m_s2(
        gradient_per_m=GAMMA_TEST, drop_height_m=0.0, interferometer_time_s=T_S
    )
    ratio = emergent_g_shift / estimate
    assert 0.5 < ratio < 2.0, f"emergent/estimate ratio {ratio}"
