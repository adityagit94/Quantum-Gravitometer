"""Phase 18 — Bertoldi 2019 closed-form finite-τ correction.

Verifies the analytical scale-factor predictor (Bertoldi et al., PRA 99,
033619, Eq. 21) is correctly computed and surfaced alongside the empirical
calibration so the latter becomes the *empirical confirmation* of an
analytical prediction rather than an unjustified numerical workaround.

References: docs/research/RESEARCH_FINITE_TAU_FORMULAS.md (Topic 14).
"""

from __future__ import annotations

import math

import numpy as np
import pytest

from qgrav.sim_ai import bertoldi_finite_tau_scale_factor
from qgrav.sim_ai.aisim_adapter import run_aisim_gravity_sweep


class TestBertoldiClosedForm:
    """Unit tests for the closed-form scale factor."""

    def test_returns_unity_when_tau_zero(self):
        # Bertoldi correction vanishes for delta pulses.
        s = bertoldi_finite_tau_scale_factor(
            tau_pi_half_s=0.0,
            interferometer_time_s=0.26,
        )
        assert s == 1.0

    def test_known_coefficient(self):
        # (2pi - 4)/pi ~ 0.72676 is the canonical Bertoldi/Shao coefficient.
        # For tau/T = 0.1, factor = 1 - 0.7268*0.1 = 0.92732.
        s = bertoldi_finite_tau_scale_factor(
            tau_pi_half_s=0.026,
            interferometer_time_s=0.26,
        )
        assert math.isclose(s, 1.0 - 0.72676 * 0.1, rel_tol=1e-4)

    def test_freier_2016_parameters(self):
        # Freier 2016 tau=17us, T=260ms -> eta=6.54e-5 -> correction ~5e-5
        # below unity (tiny, as expected for a quality lab gravimeter).
        s = bertoldi_finite_tau_scale_factor(
            tau_pi_half_s=17e-6,
            interferometer_time_s=0.260,
        )
        assert 1.0 - 1e-4 < s < 1.0

    def test_menoret_2018_parameters(self):
        # Menoret tau=10us, T=60ms -> eta=1.67e-4 -> correction ~1.2e-4
        s = bertoldi_finite_tau_scale_factor(
            tau_pi_half_s=10e-6,
            interferometer_time_s=0.060,
        )
        assert 1.0 - 2e-4 < s < 1.0

    def test_rejects_invalid_T(self):
        with pytest.raises(ValueError):
            bertoldi_finite_tau_scale_factor(
                tau_pi_half_s=10e-6,
                interferometer_time_s=0.0,
            )


class TestBertoldiInGravitySweep:
    """The gravity sweep result must surface the analytical correction
    next to the empirical calibration."""

    def test_gravity_sweep_reports_bertoldi(self):
        result = run_aisim_gravity_sweep(
            n_atoms=100,
            seed=42,
            n_gravity_points=11,
            gravity_span_m_s2=4e-6,
            lock_to_midfringe=True,
            gravity_propagation=True,
        )
        # Both diagnostics must be present and finite.
        assert "bertoldi_finite_tau_scale_factor" in result
        assert "empirical_phase_offset_rad" in result
        bert = result["bertoldi_finite_tau_scale_factor"]
        emp = result["empirical_phase_offset_rad"]
        assert 0.9 < bert <= 1.0
        assert np.isfinite(emp)

    def test_hybrid_mode_also_reports_diagnostics(self):
        # Even in hybrid mode the analytical scale factor is meaningful
        # (it's the prediction for what the simulated mode would carry).
        result = run_aisim_gravity_sweep(
            n_atoms=100,
            seed=42,
            n_gravity_points=11,
            gravity_span_m_s2=4e-6,
            lock_to_midfringe=True,
            gravity_propagation=False,
        )
        assert "bertoldi_finite_tau_scale_factor" in result
        # Hybrid empirical_phase_offset is 0.0 (no calibration runs).
        assert result["empirical_phase_offset_rad"] == 0.0
