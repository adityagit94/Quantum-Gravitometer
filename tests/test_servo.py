"""Tests for fringe-locking servo (Phase 7)."""
from __future__ import annotations

import numpy as np
import pytest

from qgrav.physics.readout_models import servo_integrator_step
from qgrav.sim_ai.aisim_adapter import run_aisim_multi_drop_cycle


class TestServoIntegratorBasic:
    """Verify the basic servo step function."""

    def test_servo_zero_error_no_change(self):
        """When P = setpoint, no phase correction."""
        out = servo_integrator_step(
            population=0.5, phase_estimate=1.234,
            setpoint=0.5, gain=1.0,
        )
        np.testing.assert_allclose(out, 1.234)

    def test_servo_positive_error_decreases_phase(self):
        """P > setpoint -> phase decreases."""
        out = servo_integrator_step(
            population=0.7, phase_estimate=1.0,
            setpoint=0.5, gain=2.0,
        )
        # error = 0.7 - 0.5 = 0.2
        # phase_new = 1.0 - 2.0 * 0.2 = 0.6
        np.testing.assert_allclose(out, 0.6)

    def test_servo_negative_error_increases_phase(self):
        out = servo_integrator_step(
            population=0.3, phase_estimate=1.0,
            setpoint=0.5, gain=2.0,
        )
        # error = 0.3 - 0.5 = -0.2
        # phase_new = 1.0 - 2.0 * (-0.2) = 1.4
        np.testing.assert_allclose(out, 1.4)


class TestServoLocksToMidfringe:
    """After several drops, P3 should be locked near midfringe."""

    def test_servo_locks_to_midfringe(self):
        """The mean of the servo-locked P3 trajectory should be near midfringe.

        Note: each drop uses a fresh ensemble (seed+i), so there is irreducible
        per-drop ensemble noise (~0.05 in P3) that the servo cannot suppress
        because it is uncorrelated.  The MEAN of P3 across many drops should
        converge to the setpoint (0.5).
        """
        result = run_aisim_multi_drop_cycle(
            n_atoms=500,
            seed=42,
            n_drops=30,
            cycle_time_s=1.0,
            gravity_propagation=False,
            detection_noise_enabled=False,  # no detection noise so servo locks cleanly
            servo_enabled=True,
            servo_gain=0.5,
        )
        # Skip first few drops (transient), check mean of remaining
        p3 = result["port_3_noisy"]
        steady_mean = float(np.mean(p3[5:]))
        assert abs(steady_mean - 0.5) < 0.05, (
            f"Servo did not lock to midfringe: mean P3 = {steady_mean}"
        )

    def test_servo_g_estimate_converges(self):
        """g_estimates from servo should converge to gravity_true."""
        result = run_aisim_multi_drop_cycle(
            n_atoms=500,
            seed=42,
            n_drops=20,
            cycle_time_s=1.0,
            gravity_propagation=False,
            detection_noise_enabled=False,
            servo_enabled=True,
            servo_gain=0.5,
            gravity_true_m_s2=9.81,
        )
        # Late-time g_estimates should be close to true
        g_est = result["g_estimates_m_s2"]
        late_mean = float(np.mean(g_est[-5:]))
        np.testing.assert_allclose(late_mean, 9.81, atol=1e-6)


class TestServoDisabled:
    """When servo_enabled=False, phase_bias should not change between drops."""

    def test_servo_disabled_no_correction(self):
        r_no_servo = run_aisim_multi_drop_cycle(
            n_atoms=500, seed=42, n_drops=5,
            gravity_propagation=False,
            detection_noise_enabled=False,
            servo_enabled=False,
        )
        # All P3 values should be very similar (only ensemble noise between drops)
        p3 = r_no_servo["port_3_noisy"]
        assert np.std(p3) < 0.05  # tight spread without servo correction
