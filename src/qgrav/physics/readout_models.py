from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import numpy as np


def clip_probabilities(x: np.ndarray | float) -> np.ndarray:
    return np.clip(np.asarray(x, dtype=np.float64), 0.0, 1.0)


def port_differential_summary(port2: np.ndarray, port3: np.ndarray) -> dict[str, Any]:
    p2 = clip_probabilities(port2)
    p3 = clip_probabilities(port3)
    total = np.maximum(p2 + p3, 1e-15)
    diff = p3 - p2
    norm_diff = diff / total
    return {
        'output_port_2': p2,
        'output_port_3': p3,
        'differential_signal': diff,
        'normalized_differential_signal': norm_diff,
        'closed_total': total,
    }


def servo_integrator_step(
    *,
    population: float,
    phase_estimate: float,
    setpoint: float = 0.5,
    gain: float = 1.0,
) -> float:
    """Single integrator-servo step that drives ``population`` to ``setpoint``.

    For a fringe-locked gravimeter, the operating point is mid-fringe
    (P3 = 0.5).  An error in the phase bias produces an excursion away from
    mid-fringe, ``error = P3 - setpoint``.  The servo accumulates a phase
    correction at rate proportional to the error:

        phase_estimate_new = phase_estimate - gain * (P3 - setpoint)

    Subtracting because P3 increases with phase near the rising slope of the
    fringe — to bring P3 down, we reduce phase_estimate.

    Parameters
    ----------
    population : float
        Measured P3 at the current drop.
    phase_estimate : float
        Accumulated phase correction (state).
    setpoint : float
        Target P3 value (default 0.5 for mid-fringe).
    gain : float
        Integrator gain (units of rad per P3 unit).  ``1.0`` corresponds
        roughly to one fringe per unit error.

    Returns
    -------
    Updated ``phase_estimate``.
    """
    error = float(population) - float(setpoint)
    return float(phase_estimate) - float(gain) * error


@dataclass
class PIDServoState:
    """Mutable state for :func:`servo_pid_step`."""

    phase_estimate: float = 0.0
    integral: float = 0.0
    last_error: float = 0.0


def servo_pid_step(
    state: PIDServoState,
    *,
    population: float,
    setpoint: float = 0.5,
    kp: float = 0.5,
    ki: float = 0.1,
    kd: float = 0.0,
    integral_clamp: float = 10.0,
) -> PIDServoState:
    """One PID-servo step with anti-windup, driving ``population`` to ``setpoint``.

    Extends :func:`servo_integrator_step` (which is pure-integral) with
    proportional and derivative terms and an integrator clamp (anti-windup).
    The sign convention matches the integrator servo: the phase correction is
    *subtracted* because P3 rises with phase on the working slope of the
    fringe.

        error          = P3 - setpoint
        integral       = clamp(integral + error, +/- integral_clamp)
        derivative     = error - last_error
        phase_estimate = -(kp*error + ki*integral + kd*derivative)

    Parameters
    ----------
    state : PIDServoState
        Carried servo state (integral and last error).  A fresh
        ``PIDServoState()`` starts the loop.
    population : float
        Measured P3 at the current drop.
    setpoint : float
        Target P3 (default 0.5, mid-fringe).
    kp, ki, kd : float
        Proportional, integral and derivative gains (rad per P3 unit).
    integral_clamp : float
        Anti-windup bound on the accumulated integral term.

    Returns
    -------
    A new :class:`PIDServoState` with updated ``phase_estimate``, ``integral``
    and ``last_error``.
    """
    error = float(population) - float(setpoint)
    integral = float(state.integral) + error
    # Anti-windup: clamp the integrator
    integral = max(-float(integral_clamp), min(float(integral_clamp), integral))
    derivative = error - float(state.last_error)
    phase_estimate = -(float(kp) * error + float(ki) * integral + float(kd) * derivative)
    return PIDServoState(
        phase_estimate=float(phase_estimate),
        integral=float(integral),
        last_error=float(error),
    )
