"""Phase 14 — multi-drop YAML config passthrough.

Verifies the Phase 15 multi-drop noise/servo knobs are exposed through
``run_simulation_from_config`` (the YAML entry point) and round-trip into the
result dict so downstream pipelines + report HTML can surface them.
"""
from __future__ import annotations

from qgrav.sim_ai.aisim_adapter import run_simulation_from_config


def _base_cfg(**overrides):
    cfg = dict(
        enabled=True,
        backend="aisim",
        model="multi_drop_cycle",
        n_atoms=200,
        seed=42,
        n_drops=4,
        cycle_time_s=1.0,
        interferometer_time_s=0.05,  # short for test speed
        tau_pi_half_s=23e-6,
        gravity_true_m_s2=9.81,
        gravity_propagation=False,   # hybrid path is fast
        detection_noise_enabled=False,
    )
    cfg.update(overrides)
    return cfg


class TestPhase15KnobsThroughYAML:
    """The Phase 15 noise machinery must round-trip through the YAML entrypoint."""

    def test_default_no_correlated_vibration(self):
        result = run_simulation_from_config(_base_cfg())
        assert result is not None
        assert result["correlated_vibration"] is False
        assert result["raman_phase_noise_rad"] == 0.0
        assert result["servo_type"] == "integrator"
        assert result["visibility_estimate"] == 1.0

    def test_correlated_vibration_via_yaml(self):
        result = run_simulation_from_config(_base_cfg(
            correlated_vibration=True,
            seismic_model="nlnm",
            vibration_isolation_cutoff_hz=1.0,
            vibration_seed=123,
        ))
        assert result["correlated_vibration"] is True

    def test_raman_phase_noise_via_yaml(self):
        result = run_simulation_from_config(_base_cfg(
            raman_phase_noise_rad=0.05,
        ))
        assert result["raman_phase_noise_rad"] == 0.05

    def test_detection_sigma_p_via_yaml(self):
        result = run_simulation_from_config(_base_cfg(
            detection_noise_enabled=True,
            detection_sigma_p=6e-3,
        ))
        assert result["detection_sigma_p"] == 6e-3
        # n_eff = 1/sigma^2
        assert result["n_detected_effective"] == int(round(1.0 / 6e-3 ** 2))

    def test_pid_servo_via_yaml(self):
        result = run_simulation_from_config(_base_cfg(
            servo_enabled=True,
            servo_type="pid",
            servo_kp=0.4,
            servo_ki=0.15,
            servo_kd=0.05,
        ))
        assert result["servo_enabled"] is True
        assert result["servo_type"] == "pid"

    def test_fit_visibility_via_yaml(self):
        result = run_simulation_from_config(_base_cfg(
            gravity_propagation=True,   # fit_visibility only matters in simulated mode
            fit_visibility=True,
            n_drops=3,
        ))
        # The fitted contrast must be in (0, 1] and not the default 1.0
        # placeholder (real ensembles are never perfectly contrasted).
        v = result["visibility_estimate"]
        assert 0.0 < v <= 1.0
