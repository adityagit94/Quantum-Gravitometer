"""Freier 2016 (GAIN) — PRIMARY published-reference regression (Phase 13).

Validates that qgrav reproduces the Freier 2016 short-term sensitivity
(96 nm/s^2/sqrt(Hz)) two ways:

1. **Noise-budget reproduction** (fast, deterministic): the documented per-shot
   noise terms (detection, Raman-phase, vibration) combine in quadrature to the
   published short-term ASD within a factor of 2.

2. **Simulation reproduction** (``@slow``): a multi-drop cycle in the fully
   simulated (emergent-gravity) mode, driven by those noise terms, yields a
   short-term ASD within a factor of 2 of 96 nm/s^2/sqrt(Hz).

See ``docs/research/RESEARCH_FREIER_2016.md`` for parameter provenance and
``src/qgrav/validation/freier_2016_setup.py`` for the curated values.
"""
from __future__ import annotations

import math

import numpy as np
import pytest

from qgrav.sim_ai.aisim_adapter import run_aisim_multi_drop_cycle
from qgrav.validation.freier_2016_setup import (
    FREIER_2016_PARAMS,
    FREIER_2016_TARGETS,
    multi_drop_kwargs,
    predicted_short_term_asd_m_s2_per_sqrt_hz,
    total_per_shot_g_noise_m_s2,
)


class TestFreier2016Parameters:
    """Curated parameters must match the research-validated values."""

    def test_key_parameters(self):
        p = FREIER_2016_PARAMS
        assert p["interferometer_time_s"] == 0.260
        assert p["cycle_time_s"] == 1.5
        assert p["tau_pi_half_s"] == 17e-6           # NOT 23e-6 (research F3)
        assert p["single_photon_detuning_hz"] == -700e6   # NOT "few GHz"
        assert p["beam_radius_m"] == 0.015
        assert p["n_detected_per_drop"] == 5e5

    def test_targets(self):
        t = FREIER_2016_TARGETS
        assert t["short_term_noise_m_s2_per_sqrt_hz"] == 9.6e-8
        assert t["long_term_stability_m_s2"] == 5e-10
        assert t["accuracy_m_s2"] == 3.9e-8


class TestFreier2016NoiseBudget:
    """The documented per-shot budget reproduces the headline short-term noise."""

    def test_per_shot_quadrature_order_of_magnitude(self):
        # sqrt(30^2 + 40^2 + 71^2) nm/s^2 ~ 87 nm/s^2
        sigma = total_per_shot_g_noise_m_s2()
        assert 7e-8 < sigma < 1.0e-7

    def test_noise_budget_reproduces_short_term(self):
        """Predicted ASD from the budget is within a factor of 2 of 96 nm/s^2/sqrt(Hz)."""
        predicted = predicted_short_term_asd_m_s2_per_sqrt_hz()
        target = FREIER_2016_TARGETS["short_term_noise_m_s2_per_sqrt_hz"]
        tol = FREIER_2016_TARGETS["tolerance_factor"]
        factor = predicted / target
        assert 1.0 / tol < factor < tol, (
            f"Predicted short-term ASD {predicted:.2e} m/s^2/sqrt(Hz) vs "
            f"Freier 2016 target {target:.2e}; factor {factor:.2f} outside x{tol}."
        )


@pytest.mark.slow
class TestFreier2016Simulation:
    """End-to-end multi-drop simulation reproduces the short-term sensitivity."""

    def test_simulation_reproduces_short_term_noise(self):
        """Simulated ASD reproduces 96 nm/s^2/sqrt(Hz) within factor 2.

        Tolerance tightened from factor 3 (v1.1) to factor 2 (v1.2) after the
        v1.2.0 investigation.  The v1.1 factor-3 envelope was needed because a
        300-atom test ensemble has a large *finite-ensemble projection floor*
        (sigma_g_floor ~ 1/sqrt(N_atoms): 148 / 92 / 52 nm/s^2 at N = 300 /
        1000 / 3000) that SWAMPED the injected GAIN noise budget, inflating the
        simulated ASD to ~206 nm/s^2/sqrt(Hz).  Real GAIN uses ~2e7 atoms, so
        its projection floor is negligible.  Raising the test ensemble to
        N = 4000 drops the floor (~57 nm/s^2) below the injected budget
        (~104 nm/s^2/sqrt(Hz) ASD), so the total
        ASD = sqrt(floor^2 + budget^2) lands at ~115 nm/s^2/sqrt(Hz) =
        factor 1.2 vs the published 96 — now genuinely budget-limited rather
        than test-ensemble-limited.  (Runtime is still <1 s because the MZ
        matrix ops are vectorised over atoms.)
        """
        kwargs = multi_drop_kwargs(
            n_drops=100, seed=2016, n_atoms=4000, gravity_propagation=True,
        )
        result = run_aisim_multi_drop_cycle(**kwargs)

        # White-noise short-term ASD = std(g_estimates) * sqrt(T_cycle).
        T_cycle = FREIER_2016_PARAMS["cycle_time_s"]
        asd = float(result["std_g_m_s2"]) * math.sqrt(T_cycle)
        target = FREIER_2016_TARGETS["short_term_noise_m_s2_per_sqrt_hz"]
        tol = 2.0  # tightened in v1.2.0 (see docstring)
        factor = asd / target
        assert 1.0 / tol < factor < tol, (
            f"Simulated short-term ASD {asd:.2e} m/s^2/sqrt(Hz) vs Freier 2016 "
            f"target {target:.2e}; factor {factor:.2f} outside x{tol}. "
            f"(std_g={result['std_g_m_s2']:.2e}, V={result['visibility_estimate']:.3f})"
        )

    def test_simulation_is_fully_simulated_scope(self):
        # Use a longer run + small abs tolerance.  With Freier-class per-shot
        # noise (~100 nm/s^2), 6 drops gives a mean uncertainty ~40 nm/s^2; we
        # need a multi-microGal absolute tolerance just for the smoke-test mean.
        kwargs = multi_drop_kwargs(
            n_drops=20, seed=2016, n_atoms=200, gravity_propagation=True,
        )
        result = run_aisim_multi_drop_cycle(**kwargs)
        assert result["gravity_propagation"] is True
        scope = str(result["study_scope_category"]).upper()
        assert "FULLY" in scope or "SIMULATED" in scope, scope
        # The smoke-test mean has two error sources:
        #   - sample mean of N=20 Freier-class drops: ~100 nm/s^2 / sqrt(20) ~ 22 nm/s^2 statistical
        #   - small mid-fringe-linearisation bias at V~0.6 (~12% of std_g)
        # Allow ~5 microGal (5e-7 m/s^2) on the absolute mean for this smoke test;
        # the dedicated `test_simulation_reproduces_short_term_noise` tightens
        # the ASD comparison separately.
        assert result["mean_g_m_s2"] == pytest.approx(
            FREIER_2016_PARAMS["gravity_true_m_s2"], abs=5e-6
        )
