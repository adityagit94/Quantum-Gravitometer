"""Sub-pulse integration of finite-duration Raman pulses (raman_substeps).

With ``raman_substeps = N > 1`` each pulse is applied as N composed slices:
the atoms keep falling ballistically during the pulse and every slice's
rotation matrix is evaluated at the slice midpoint (position, velocity,
chirp time).  The finite-tau pulse physics then *emerges* numerically and
must converge to the published closed form

    phi_g / (k_eff * dg)  ->  (T + 2*tau) * (T + 4*tau/pi)

which is simultaneously the Fang/Mielec 2018 scale factor
``S_rec = k_eff*(Tcc + tau/2)*(Tcc + (4/pi - 3/2)*tau)`` written for this
simulation's edge-to-edge free-evolution time T (pulse centres are spaced
``Tcc = T + 3*tau/2``) and the Bertoldi 2019 expansion
``T_B^2*(1 - (2pi-4)/pi * tau/T_B)`` with ``T_B = T + 2*tau`` (they are
algebraically identical: both equal ``(T + 2*tau)*(T + 4*tau/pi)``).

References: docs/research/RESEARCH_FINITE_TAU_FORMULAS.md,
docs/research/RESEARCH_SUBPULSE.md.
"""

from __future__ import annotations

import numpy as np
import pytest

from qgrav.sim_ai._adapter_core import (
    _calibrate_gravity_phase_and_visibility,
    _create_detected_ensemble,
    _gaussian_beam,
    _wave_vectors,
)
from qgrav.sim_ai.aisim_adapter import run_aisim_gravity_sweep

# Exaggerated pulse duration so the finite-tau correction (~3% relative) is
# orders of magnitude above the deterministic fringe-fit resolution.
TAU = 2.0e-3  # pi/2 pulse duration (s)
T_SIM = 0.05  # free evolution between pulse edges (s); eta = tau/T = 0.04
G_CHIRP = 9.81
DG = 2.0e-5  # gravity offset for the scale-factor measurement (m/s^2)
RABI_HZ = 1.0 / (4.0 * TAU)  # on-axis pulse area Omega*tau = pi/2


@pytest.fixture(scope="module")
def mz_setup():
    """A cold, small, deterministic ensemble + chirped Raman beams."""
    _, atoms, _, _, _ = _create_detected_ensemble(
        n_atoms=60,
        seed=11,
        cloud_radius_m=1.0e-3,
        temp_xy_K=1e-12,
        temp_z_K=1e-12,
        detector_time_s=0.3,
        detector_radius_m=0.5,
        multiport=True,
    )
    profile = _gaussian_beam(beam_radius_m=0.5, center_rabi_freq_hz=RABI_HZ)
    wv_plain = _wave_vectors(wavelength_m=780.2e-9)
    k_eff = float(wv_plain.k1 - wv_plain.k2)
    wv = _wave_vectors(wavelength_m=780.2e-9, chirp_rate_rad_per_s2=-k_eff * G_CHIRP)
    return atoms, profile, wv, k_eff


def _wrap(x: float) -> float:
    return (x + np.pi) % (2.0 * np.pi) - np.pi


def _peak_phase(setup, g: float, n_sub: int) -> float:
    atoms, profile, wv, _ = setup
    offset, _vis = _calibrate_gravity_phase_and_visibility(
        atoms,
        tau_pi_half_s=TAU,
        interferometer_time_s=T_SIM,
        intensity_profile=profile,
        wave_vectors=wv,
        g_chirp_m_s2=g,
        n_calibration_phases=49,
        raman_substeps=n_sub,
    )
    return float(offset)


def _gravity_phase(setup, n_sub: int) -> float:
    """Fringe-peak shift between g_chirp and g_chirp + DG (the gravity phase)."""
    return _wrap(_peak_phase(setup, G_CHIRP + DG, n_sub) - _peak_phase(setup, G_CHIRP, n_sub))


@pytest.mark.slow
def test_subpulse_phase_converges_and_matches_closed_form(mz_setup):
    """phi(N) is Cauchy-convergent and its limit is the Bertoldi/Fang form."""
    _, _, _, k_eff = mz_setup
    n_values = [1, 2, 4, 8, 16, 32]
    phis = {n: _gravity_phase(mz_setup, n) for n in n_values}

    # --- Convergence: |phi(2N) - phi(N)| shrinks by < 0.6 per doubling ---
    diffs = [abs(phis[2 * n] - phis[n]) for n in n_values[:-1]]
    for d_prev, d_next in zip(diffs[:-1], diffs[1:], strict=True):
        assert d_next < 0.6 * d_prev, f"not converging: diffs={diffs}"

    # --- Cross-check vs the closed form (T_B = T + 2*tau convention) ---
    predicted = k_eff * DG * (T_SIM + 2.0 * TAU) * (T_SIM + 4.0 * TAU / np.pi)
    measured = abs(phis[32])
    # Empirically 2.2e-3 relative at eta = 0.04 (the residual is O(eta^2));
    # 1e-2 gives a 4x margin while staying far below the 13% naive-T^2 gap.
    assert measured == pytest.approx(predicted, rel=1e-2)

    # --- The check is non-trivial: N=1 sits near the NAIVE scale factor ---
    # --- (within a few %; the exact value carries the single-shot       ---
    # --- Bertoldi Eq. 32 residual, which no longer velocity-averages    ---
    # --- away for this ultra-cold ensemble), while the closed form is   ---
    # --- 13% away for these parameters.                                 ---
    naive = k_eff * DG * T_SIM**2
    assert abs(phis[1]) == pytest.approx(naive, rel=5e-2)
    assert abs(abs(phis[1]) - naive) < abs(abs(phis[1]) - predicted)
    assert abs(naive - predicted) / predicted > 0.10


@pytest.mark.slow
def test_subpulse_calibration_artifact_shrinks_with_n(mz_setup):
    """The g-independent fringe offset at g_chirp (the finite-pulse
    discretisation artefact the empirical calibration removes) must shrink
    roughly like 1/N once sub-pulse integration is on."""
    off_1 = _wrap(_peak_phase(mz_setup, G_CHIRP, 1))
    off_8 = _wrap(_peak_phase(mz_setup, G_CHIRP, 8))
    off_32 = _wrap(_peak_phase(mz_setup, G_CHIRP, 32))
    assert abs(off_32) < 0.1 * abs(off_1)
    assert abs(off_32) < 0.5 * abs(off_8)


def test_substeps_default_is_bit_identical():
    """raman_substeps=1 (and omitting it) must not change anything."""
    kwargs = dict(
        n_atoms=60,
        seed=42,
        n_gravity_points=7,
        gravity_span_m_s2=4e-6,
        lock_to_midfringe=True,
        gravity_propagation=True,
    )
    baseline = run_aisim_gravity_sweep(**kwargs)
    explicit = run_aisim_gravity_sweep(**kwargs, raman_substeps=1)
    np.testing.assert_array_equal(baseline["output_port_3"], explicit["output_port_3"])
    np.testing.assert_array_equal(baseline["output_port_2"], explicit["output_port_2"])
    assert explicit["raman_substeps"] == 1


def test_substeps_invalid_raises():
    with pytest.raises(ValueError, match="raman_substeps"):
        run_aisim_gravity_sweep(
            n_atoms=20,
            n_gravity_points=5,
            gravity_propagation=True,
            raman_substeps=0,
        )


def test_substeps_through_config_dispatcher():
    from qgrav.sim_ai.aisim_adapter import run_simulation_from_config

    result = run_simulation_from_config(
        {
            "enabled": True,
            "backend": "aisim",
            "model": "gravity_sweep",
            "n_atoms": 30,
            "seed": 3,
            "n_gravity_points": 5,
            "gravity_propagation": True,
            "raman_substeps": 2,
        }
    )
    assert result is not None
    assert result["raman_substeps"] == 2


def test_substeps_multi_drop_smoke():
    """multi_drop_cycle accepts raman_substeps and reports it."""
    from qgrav.sim_ai.aisim_adapter import run_aisim_multi_drop_cycle

    out = run_aisim_multi_drop_cycle(
        n_drops=3,
        n_atoms=30,
        seed=5,
        gravity_propagation=True,
        raman_substeps=2,
        detection_noise_enabled=False,
    )
    assert out["raman_substeps"] == 2
    assert np.all(np.isfinite(out["g_estimates_m_s2"]))
