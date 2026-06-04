"""Phase 15 — multi-drop realism: PID servo, correlated vibration, V-fit.

These extend the basic multi-drop cycle (test_multi_drop_cycle.py) with the
noise/feedback machinery needed to reproduce published gravimeter Allan
deviations (Phases 13/16).
"""
from __future__ import annotations

import numpy as np
import pytest

from qgrav.physics.readout_models import PIDServoState, servo_pid_step
from qgrav.sim_ai.aisim_adapter import run_aisim_multi_drop_cycle


class TestPIDServo:
    """Unit tests for the PID servo step with anti-windup."""

    def test_zero_error_holds(self):
        st = servo_pid_step(PIDServoState(), population=0.5, setpoint=0.5,
                            kp=0.5, ki=0.1, kd=0.0)
        assert st.phase_estimate == 0.0
        assert st.integral == 0.0

    def test_proportional_sign(self):
        # P3 > setpoint -> phase correction is negative (drives P3 down)
        st = servo_pid_step(PIDServoState(), population=0.7, setpoint=0.5,
                            kp=1.0, ki=0.0, kd=0.0)
        assert st.phase_estimate < 0

    def test_anti_windup_clamps_integral(self):
        st = PIDServoState()
        # Drive a large constant error for many steps; integral must clamp.
        for _ in range(1000):
            st = servo_pid_step(st, population=1.0, setpoint=0.5,
                                kp=0.0, ki=1.0, kd=0.0, integral_clamp=10.0)
        assert abs(st.integral) <= 10.0 + 1e-9
        # And the phase estimate stays bounded by ki*clamp.
        assert abs(st.phase_estimate) <= 10.0 + 1e-9

    def test_derivative_responds_to_change(self):
        st = PIDServoState(last_error=0.0)
        st2 = servo_pid_step(st, population=0.6, setpoint=0.5,
                             kp=0.0, ki=0.0, kd=1.0)
        # derivative term = error - last_error = 0.1 - 0 = 0.1 -> phase = -0.1
        np.testing.assert_allclose(st2.phase_estimate, -0.1, atol=1e-12)


class TestPIDServoInMultiDrop:
    """PID servo wired into the multi-drop cycle locks to mid-fringe."""

    def test_pid_servo_reduces_offset_vs_open_loop(self):
        """The PID servo must pull the steady-state P3 closer to the 0.5
        setpoint than the open-loop (no-servo) case.

        We compare the mean |P3 - 0.5| over the steady-state portion: with a
        finite-contrast ensemble the open-loop operating point sits off 0.5
        (fringe-offset skew), and a working servo reduces that excursion.
        An absolute threshold is avoided because the achievable lock depends
        on the irreducible per-drop ensemble scatter.
        """
        common = dict(
            n_atoms=500, seed=42, n_drops=30, cycle_time_s=1.0,
            gravity_propagation=False, detection_noise_enabled=False,
        )
        open_loop = run_aisim_multi_drop_cycle(**common, servo_enabled=False)
        pid = run_aisim_multi_drop_cycle(
            **common, servo_enabled=True, servo_type="pid",
            servo_kp=0.5, servo_ki=0.2, servo_kd=0.0,
        )
        assert pid["servo_type"] == "pid"
        off_open = abs(float(np.mean(open_loop["port_3_noisy"][5:])) - 0.5)
        off_pid = abs(float(np.mean(pid["port_3_noisy"][5:])) - 0.5)
        assert off_pid < off_open, (
            f"PID did not improve lock: open-loop |dP3|={off_open:.3f}, "
            f"PID |dP3|={off_pid:.3f}"
        )

    def test_pid_servo_locks_near_midfringe(self):
        """With enough drops the PID steady-state mean P3 is near 0.5."""
        result = run_aisim_multi_drop_cycle(
            n_atoms=500, seed=42, n_drops=40, cycle_time_s=1.0,
            gravity_propagation=False, detection_noise_enabled=False,
            servo_enabled=True, servo_type="pid",
            servo_kp=0.5, servo_ki=0.2, servo_kd=0.0,
        )
        steady_mean = float(np.mean(result["port_3_noisy"][10:]))
        # Generous bound: ensemble skew + finite gain leave a small residual.
        assert abs(steady_mean - 0.5) < 0.08, (
            f"PID steady-state mean P3 = {steady_mean}"
        )


class TestCorrelatedVibration:
    """Correlated seismic vibration produces non-white Allan structure."""

    def test_correlated_vibration_runs_and_reports(self):
        result = run_aisim_multi_drop_cycle(
            n_atoms=300, seed=7, n_drops=32, cycle_time_s=1.0,
            gravity_propagation=False, detection_noise_enabled=False,
            correlated_vibration=True, seismic_model="nlnm",
            vibration_isolation_cutoff_hz=0.0,
        )
        assert result["correlated_vibration"] is True
        vib = result["vibration_phase_rad"]
        assert len(vib) == 32
        # Vibration injects a non-zero per-drop phase.
        assert np.any(np.abs(vib) > 0)

    def test_correlated_vibration_is_deterministic(self):
        kw = dict(
            n_atoms=200, seed=11, n_drops=16, cycle_time_s=1.0,
            gravity_propagation=False, detection_noise_enabled=False,
            correlated_vibration=True, vibration_seed=123,
        )
        r1 = run_aisim_multi_drop_cycle(**kw)
        r2 = run_aisim_multi_drop_cycle(**kw)
        np.testing.assert_array_equal(
            r1["vibration_phase_rad"], r2["vibration_phase_rad"]
        )

    def test_correlated_vibration_more_low_freq_than_white(self):
        """Correlated seismic noise should have more long-tau Allan power
        (relative to its short-tau value) than purely white per-drop noise.

        We compare the ratio adev(longest tau)/adev(shortest tau): for white
        noise this falls steeply (~1/sqrt), for correlated low-frequency noise
        it falls more slowly (or rises).
        """
        common = dict(
            n_atoms=300, seed=3, n_drops=64, cycle_time_s=1.0,
            gravity_propagation=False,
        )
        white = run_aisim_multi_drop_cycle(
            **common, detection_noise_enabled=True, n_detected_per_drop=1000,
            correlated_vibration=False,
        )
        corr = run_aisim_multi_drop_cycle(
            **common, detection_noise_enabled=False,
            correlated_vibration=True, seismic_model="nlnm",
        )

        def tail_ratio(res):
            adev = np.asarray(res["allan_dev_m_s2"])
            adev = adev[adev > 0]
            if len(adev) < 2:
                return np.nan
            return float(adev[-1] / adev[0])

        r_white = tail_ratio(white)
        r_corr = tail_ratio(corr)
        # Correlated noise retains relatively more long-tau power.
        assert r_corr > r_white, (
            f"correlated tail ratio {r_corr:.3f} not > white {r_white:.3f}"
        )


class TestVisibilityFit:
    """Fitted visibility is used in the P3->g inversion (simulated mode)."""

    def test_visibility_fit_reported(self):
        result = run_aisim_multi_drop_cycle(
            n_atoms=300, seed=42, n_drops=4, cycle_time_s=1.0,
            gravity_propagation=True, detection_noise_enabled=False,
            fit_visibility=True,
        )
        v = result["visibility_estimate"]
        assert 0.0 < v <= 1.0
        # A real fitted contrast should differ from the hard-coded 1.0 default
        # (ensembles are never perfectly contrasted).
        assert v < 1.0

    def test_visibility_default_is_unity(self):
        result = run_aisim_multi_drop_cycle(
            n_atoms=300, seed=42, n_drops=4, cycle_time_s=1.0,
            gravity_propagation=True, detection_noise_enabled=False,
            fit_visibility=False,
        )
        assert result["visibility_estimate"] == 1.0


class TestTechnicalDetectionNoise:
    """Explicit technical sigma_P overrides the 1/sqrt(N) projection model."""

    def test_technical_sigma_sets_effective_n(self):
        sigma = 6e-3
        result = run_aisim_multi_drop_cycle(
            n_atoms=300, seed=42, n_drops=8, cycle_time_s=1.0,
            gravity_propagation=False, detection_noise_enabled=True,
            detection_sigma_p=sigma,
        )
        # n_eff = 1/sigma^2
        expected_n = int(round(1.0 / sigma**2))
        assert result["n_detected_effective"] == expected_n
        assert result["detection_sigma_p"] == sigma
