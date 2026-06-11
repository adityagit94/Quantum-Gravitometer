"""Tests for gravity-enabled MZ sequence — Phase 3 of v1.0 upgrade.

The key cross-validation: simulated mode (GravityFreePropagator + chirped laser)
must produce the same fringe pattern as the hybrid mode (analytical gravity phase),
since both implement the same underlying physics.
"""

from __future__ import annotations

import numpy as np
import pytest

from qgrav.sim_ai.aisim_adapter import (
    STUDY_SCOPE_FULLY_SIMULATED,
    STUDY_SCOPE_HYBRID,
    run_aisim_gravity_sweep,
    run_simulation_from_config,
)

# Use small atom counts + few points for speed in CI.
_COMMON = dict(
    n_atoms=200,
    seed=42,
    n_gravity_points=11,
    gravity_span_m_s2=4.0e-6,
    lock_to_midfringe=True,
)


class TestGravitySweepSimulatedMatchesAnalytical:
    """THE key test: simulated and hybrid modes must produce matching fringes.

    With the AISim ``_prop_matrix`` patched to use the integrated laser phase
    and a per-sweep empirical calibration at ``g = g_chirp``, the two modes
    track the same MZ fringe (same rate, same amplitude, aligned centre).
    A small residual mismatch (~0.15 in P3) remains due to finite-pulse-duration
    effects: in the simulated mode the chirped laser produces a τ-dependent
    residual detuning at each pulse (~k_eff*g*τ for the mirror, ~3*k_eff*g*τ
    for bs2), which slightly modifies the Rabi rotation angles compared to the
    idealised infinitely-short-pulse analytical formula.  This is a real
    physical effect captured by the simulation, not a numerical artefact.
    """

    @pytest.fixture(scope="class")
    def both_results(self):
        hybrid = run_aisim_gravity_sweep(**_COMMON, gravity_propagation=False)
        simulated = run_aisim_gravity_sweep(**_COMMON, gravity_propagation=True)
        return hybrid, simulated

    def test_port3_populations_agree(self, both_results):
        hybrid, simulated = both_results
        p3_h = hybrid["output_port_3"]
        p3_s = simulated["output_port_3"]
        # Populations agree within finite-tau physics differences (atol=0.15)
        np.testing.assert_allclose(
            p3_s, p3_h, atol=0.15, err_msg="Simulated and hybrid port-3 populations disagree"
        )

    def test_port2_populations_agree(self, both_results):
        hybrid, simulated = both_results
        p2_h = hybrid["output_port_2"]
        p2_s = simulated["output_port_2"]
        np.testing.assert_allclose(
            p2_s, p2_h, atol=0.15, err_msg="Simulated and hybrid port-2 populations disagree"
        )

    def test_normalized_diff_agrees(self, both_results):
        hybrid, simulated = both_results
        nd_h = hybrid["normalized_differential_signal"]
        nd_s = simulated["normalized_differential_signal"]
        np.testing.assert_allclose(
            nd_s, nd_h, atol=0.30, err_msg="Normalized differential signals disagree"
        )


class TestGravitySweepFringeVisibility:
    """Fringe visibility must be preserved in simulated mode."""

    def test_fringe_visibility_preserved(self):
        hybrid = run_aisim_gravity_sweep(**_COMMON, gravity_propagation=False)
        simulated = run_aisim_gravity_sweep(**_COMMON, gravity_propagation=True)
        # Compute visibility as (max-min)/(max+min) on port 3
        p3_h = hybrid["output_port_3"]
        p3_s = simulated["output_port_3"]
        vis_h = (np.max(p3_h) - np.min(p3_h)) / max(np.max(p3_h) + np.min(p3_h), 1e-15)
        vis_s = (np.max(p3_s) - np.min(p3_s)) / max(np.max(p3_s) + np.min(p3_s), 1e-15)
        assert (
            abs(vis_s - vis_h) < 0.1
        ), f"Visibility mismatch: simulated={vis_s:.3f} vs hybrid={vis_h:.3f}"


class TestGravitySweepStudyScope:
    """Study scope must be FULLY_SIMULATED when gravity_propagation=True."""

    def test_study_scope_fully_simulated(self):
        result = run_aisim_gravity_sweep(**_COMMON, gravity_propagation=True)
        assert result["study_scope_category"] == STUDY_SCOPE_FULLY_SIMULATED
        assert result["gravity_propagation"] is True

    def test_study_scope_hybrid_default(self):
        result = run_aisim_gravity_sweep(**_COMMON, gravity_propagation=False)
        assert result["study_scope_category"] == STUDY_SCOPE_HYBRID
        assert result["gravity_propagation"] is False


class TestGravitySweepDefaultIsHybrid:
    """Default behaviour (no gravity_propagation arg) must be hybrid."""

    def test_default_is_hybrid(self):
        result = run_aisim_gravity_sweep(
            n_atoms=100,
            seed=1,
            n_gravity_points=5,
            gravity_span_m_s2=2.0e-6,
        )
        assert result["study_scope_category"] == STUDY_SCOPE_HYBRID
        assert result["gravity_propagation"] is False


class TestGravityPropagationConfigPassthrough:
    """run_simulation_from_config must pass gravity_propagation through."""

    def test_config_passthrough_true(self):
        cfg = {
            "enabled": True,
            "backend": "aisim",
            "model": "gravity_sweep",
            "n_atoms": 100,
            "seed": 1,
            "n_gravity_points": 5,
            "gravity_span_m_s2": 2.0e-6,
            "gravity_propagation": True,
        }
        result = run_simulation_from_config(cfg)
        assert result is not None
        assert result["gravity_propagation"] is True
        assert result["study_scope_category"] == STUDY_SCOPE_FULLY_SIMULATED

    def test_config_passthrough_false_default(self):
        cfg = {
            "enabled": True,
            "backend": "aisim",
            "model": "gravity_sweep",
            "n_atoms": 100,
            "seed": 1,
            "n_gravity_points": 5,
            "gravity_span_m_s2": 2.0e-6,
        }
        result = run_simulation_from_config(cfg)
        assert result is not None
        assert result["gravity_propagation"] is False
        assert result["study_scope_category"] == STUDY_SCOPE_HYBRID
