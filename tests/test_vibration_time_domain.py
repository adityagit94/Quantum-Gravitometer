"""Time-domain vibration mode: mirror motion from a synthesized Peterson
series fed through the pulse sequence, validating the Cheinet transfer
function end-to-end (PROJECT_SPEC's `vibration_model="time_domain"`).

The key physics check: the realized per-shot phase noise (std of
k_eff*[z(0)-2z(T)+z(2T)] sampled from the synthesized displacement record)
must reproduce the frequency-domain budget int S_a |H_a|^2 df computed on
the same effective PSD.  Empirically the ratio is 0.92-1.13 across seeds
(statistical error of a std estimate over O(100) correlated shots).
"""

from __future__ import annotations

import numpy as np

from qgrav.config import validate_config_structure
from qgrav.sim_ai import run_aisim_vibration_sensitivity_sweep

FAST_KWARGS = dict(
    n_atoms=120,
    seed=3,
    interferometer_time_s=0.13,
    tau_pi_half_s=17e-6,
    vibration_model="time_domain",
    seismic_model="nhnm",
    cycle_time_s=1.0,
)


def test_realized_noise_matches_cheinet_budget():
    result = run_aisim_vibration_sensitivity_sweep(**FAST_KWARGS, n_shots=300, vibration_seed=7)
    ratio = result["phase_noise_ratio"]
    assert 0.85 < ratio < 1.20, f"realized/budget ratio {ratio}"
    assert result["truth_checks"]["all_passed"]
    assert result["realized_phase_noise_rad"] > 0.0
    assert result["analytic_phase_noise_rad"] > 0.0


def test_result_contract_and_scope():
    result = run_aisim_vibration_sensitivity_sweep(**FAST_KWARGS, n_shots=60, vibration_seed=7)
    assert result["model"] == "vibration_sensitivity_sweep"
    assert result["vibration_model"] == "time_domain"
    assert result["study_type"] == "hybrid_aisim_plus_time_domain_seismic_vibration_phase"
    assert "vibration_amplitude_m" not in result
    assert len(result["shot_index"]) == 60
    assert len(result["vibration_phase_rad"]) == 60
    assert len(result["output_port_3"]) == 60
    # Sinusoidal-only slope is meaningless here.
    assert np.isnan(result["equivalent_gravity_error_per_m"])
    # Plot specs must reference keys that exist in the result.
    for spec in result["plot_specs"]:
        assert spec["x_key"] in result
        for series in spec["series"]:
            assert series["key"] in result


def test_time_domain_is_deterministic_per_seed():
    r1 = run_aisim_vibration_sensitivity_sweep(**FAST_KWARGS, n_shots=60, vibration_seed=11)
    r2 = run_aisim_vibration_sensitivity_sweep(**FAST_KWARGS, n_shots=60, vibration_seed=11)
    np.testing.assert_array_equal(r1["vibration_phase_rad"], r2["vibration_phase_rad"])
    r3 = run_aisim_vibration_sensitivity_sweep(**FAST_KWARGS, n_shots=60, vibration_seed=12)
    assert not np.array_equal(r1["vibration_phase_rad"], r3["vibration_phase_rad"])


def test_isolation_cutoff_reduces_noise_consistently():
    """A 1 Hz isolation high-pass must lower BOTH the realized and the
    budgeted noise, and the two must still agree (the analytic budget uses
    the same isolation-filtered PSD as the generator)."""
    raw = run_aisim_vibration_sensitivity_sweep(**FAST_KWARGS, n_shots=200, vibration_seed=7)
    iso = run_aisim_vibration_sensitivity_sweep(
        **FAST_KWARGS, n_shots=200, vibration_seed=7, vibration_isolation_cutoff_hz=1.0
    )
    assert iso["analytic_phase_noise_rad"] < raw["analytic_phase_noise_rad"]
    assert iso["realized_phase_noise_rad"] < raw["realized_phase_noise_rad"]
    assert iso["truth_checks"]["all_passed"]


def test_rejects_bad_inputs():
    import pytest

    with pytest.raises(ValueError, match="vibration_model"):
        run_aisim_vibration_sensitivity_sweep(**{**FAST_KWARGS, "vibration_model": "bogus"})
    with pytest.raises(ValueError, match="n_shots"):
        run_aisim_vibration_sensitivity_sweep(**FAST_KWARGS, n_shots=5)


def test_config_dispatch_runs_time_domain():
    from qgrav.sim_ai import run_simulation_from_config

    result = run_simulation_from_config(
        {
            "enabled": True,
            "backend": "aisim",
            "model": "vibration_sensitivity_sweep",
            "vibration_model": "time_domain",
            "n_atoms": 120,
            "seed": 3,
            "tau_pi_half_s": 17e-6,
            "interferometer_time_s": 0.13,
            "gravity_ref_m_s2": 9.81,
            "seismic_model": "nhnm",
            "n_shots": 60,
            "cycle_time_s": 1.0,
            "vibration_seed": 7,
        }
    )
    assert result is not None
    assert result["vibration_model"] == "time_domain"
    assert result["truth_checks"]["all_passed"]


class TestConfigValidation:
    def _base_cfg(self, sim: dict) -> dict:
        return {
            "output": {"runs_dir": "runs", "name": "x"},
            "bench": {"type": "virtual"},
            "bench_virtual_ifo": {
                "wavelength_m": 1.55e-6,
                "sample_rate_hz": 100,
                "duration_s": 1.0,
            },
            "simulation": {
                "enabled": True,
                "backend": "aisim",
                "model": "vibration_sensitivity_sweep",
                "n_atoms": 100,
                "tau_pi_half_s": 17e-6,
                "interferometer_time_s": 0.13,
                "gravity_ref_m_s2": 9.81,
                **sim,
            },
        }

    def test_time_domain_needs_no_amplitude_axis(self):
        issues = validate_config_structure(self._base_cfg({"vibration_model": "time_domain"}))
        assert not [i for i in issues if "amplitude" in i or "vibration_frequency" in i]

    def test_sinusoidal_still_requires_amplitude_axis(self):
        issues = validate_config_structure(self._base_cfg({}))
        assert any("amplitude_max_m" in i for i in issues)
        assert any("n_amplitude_points" in i for i in issues)

    def test_bogus_vibration_model_is_rejected(self):
        issues = validate_config_structure(self._base_cfg({"vibration_model": "bogus"}))
        assert any("vibration_model" in i for i in issues)
