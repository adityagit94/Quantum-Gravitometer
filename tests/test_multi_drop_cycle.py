"""Tests for multi-drop measurement cycle (Phase 6)."""
from __future__ import annotations

import numpy as np
import pytest

from qgrav.sim_ai.aisim_adapter import (
    STUDY_SCOPE_FULLY_SIMULATED,
    STUDY_SCOPE_HYBRID,
    run_aisim_multi_drop_cycle,
    run_simulation_from_config,
)


# Small parameter set to keep tests fast
_COMMON_FAST = dict(
    n_atoms=100,
    seed=42,
    n_drops=10,
    cycle_time_s=1.0,
    gravity_propagation=False,  # use hybrid for speed (no calibration)
    detection_noise_enabled=True,
    n_detected_per_drop=1000,
)


class TestMultiDropProducesNMeasurements:
    """n_drops must equal len(g_estimates_m_s2)."""

    def test_multi_drop_produces_n_measurements(self):
        result = run_aisim_multi_drop_cycle(**_COMMON_FAST)
        assert len(result["g_estimates_m_s2"]) == 10
        assert len(result["timestamps_s"]) == 10
        assert len(result["port_3_raw"]) == 10
        assert len(result["port_3_noisy"]) == 10

    def test_multi_drop_timestamps_spaced_correctly(self):
        result = run_aisim_multi_drop_cycle(**_COMMON_FAST)
        ts = result["timestamps_s"]
        # Should be 0, 1, 2, ... 9 (cycle_time_s = 1.0)
        np.testing.assert_array_equal(ts, np.arange(10, dtype=np.float64))


class TestMultiDropMeanNearTrueGravity:
    """Mean(g_estimates) should be near g_true for enough drops."""

    def test_multi_drop_mean_near_true_gravity(self):
        # Use larger n_drops + many detected atoms for tight std
        result = run_aisim_multi_drop_cycle(
            n_atoms=100, seed=42, n_drops=50, cycle_time_s=1.0,
            gravity_propagation=False,
            detection_noise_enabled=True,
            n_detected_per_drop=10000,
            gravity_true_m_s2=9.81,
        )
        mean_g = result["mean_g_m_s2"]
        # Mean should be within a few sigma of g_true
        # For ideal detection: σ_g per drop ≈ 1/(k_eff·T²·V·√N)
        # For 10000 atoms, V≈1, k_eff·T²≈1e6: σ ≈ 1e-8 per drop
        # Mean of 50 drops: σ_mean ≈ 1.4e-9
        np.testing.assert_allclose(mean_g, 9.81, atol=5e-8)


class TestMultiDropAllanDeviationComputed:
    """Allan deviation arrays must be returned and have valid values."""

    def test_multi_drop_allan_deviation_computed(self):
        result = run_aisim_multi_drop_cycle(**_COMMON_FAST)
        taus = result["allan_taus_s"]
        adev = result["allan_dev_m_s2"]
        assert len(taus) == len(adev)
        assert len(taus) >= 1
        assert np.all(taus > 0)
        assert np.all(adev >= 0)
        # First tau should be cycle_time_s
        np.testing.assert_allclose(taus[0], 1.0)

    def test_multi_drop_allan_deviation_decreases_with_tau_for_white_noise(self):
        """For white noise (independent drops), adev should decrease as 1/sqrt(tau)."""
        # Use enough atoms so every seed produces detected atoms
        result = run_aisim_multi_drop_cycle(
            n_atoms=500, seed=42, n_drops=64, cycle_time_s=1.0,
            gravity_propagation=False,
            detection_noise_enabled=True,
            n_detected_per_drop=1000,
        )
        taus = result["allan_taus_s"]
        adev = result["allan_dev_m_s2"]
        if len(taus) >= 3:
            # adev should generally decrease as tau increases (within statistical fluctuation)
            assert adev[-1] < adev[0]


class TestMultiDropIndependentNoise:
    """Different drops should give independent noise (verified by different seeds)."""

    def test_multi_drop_independent_noise(self):
        # Run two cycles with different seeds; they should give different g_estimates
        r1 = run_aisim_multi_drop_cycle(
            n_atoms=100, seed=1, n_drops=5,
            cycle_time_s=1.0, gravity_propagation=False,
            detection_noise_enabled=True,
        )
        r2 = run_aisim_multi_drop_cycle(
            n_atoms=100, seed=2, n_drops=5,
            cycle_time_s=1.0, gravity_propagation=False,
            detection_noise_enabled=True,
        )
        assert not np.array_equal(r1["g_estimates_m_s2"], r2["g_estimates_m_s2"])

    def test_multi_drop_deterministic_with_seed(self):
        r1 = run_aisim_multi_drop_cycle(**_COMMON_FAST)
        r2 = run_aisim_multi_drop_cycle(**_COMMON_FAST)
        np.testing.assert_array_equal(r1["g_estimates_m_s2"], r2["g_estimates_m_s2"])


class TestMultiDropStudyScope:
    """Study scope should reflect gravity_propagation setting."""

    def test_study_scope_fully_simulated(self):
        result = run_aisim_multi_drop_cycle(
            n_atoms=100, seed=1, n_drops=3,
            cycle_time_s=1.0, gravity_propagation=True,
        )
        assert result["study_scope_category"] == STUDY_SCOPE_FULLY_SIMULATED
        assert result["gravity_propagation"] is True

    def test_study_scope_hybrid(self):
        result = run_aisim_multi_drop_cycle(**_COMMON_FAST)
        assert result["study_scope_category"] == STUDY_SCOPE_HYBRID
        assert result["gravity_propagation"] is False


class TestMultiDropConfigPassthrough:
    """run_simulation_from_config should dispatch to multi-drop cycle."""

    def test_multi_drop_via_config(self):
        cfg = {
            "enabled": True,
            "backend": "aisim",
            "model": "multi_drop_cycle",
            "n_atoms": 100,
            "seed": 42,
            "n_drops": 5,
            "cycle_time_s": 1.0,
            "gravity_propagation": False,
        }
        result = run_simulation_from_config(cfg)
        assert result is not None
        assert result["model"] == "multi_drop_cycle"
        assert result["n_drops"] == 5
