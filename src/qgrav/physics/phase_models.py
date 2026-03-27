from __future__ import annotations

import numpy as np


def gravity_phase_rad(
    g_m_s2: np.ndarray | float,
    *,
    k_eff_rad_per_m: float,
    interferometer_time_s: float,
    phase_bias_rad: float = 0.0,
) -> np.ndarray:
    g = np.asarray(g_m_s2, dtype=np.float64)
    return float(k_eff_rad_per_m) * g * (float(interferometer_time_s) ** 2) + float(phase_bias_rad)


def vibration_phase_rad(
    amplitudes_m: np.ndarray | float,
    *,
    frequency_hz: float,
    interferometer_time_s: float,
    k_eff_rad_per_m: float,
    phase0_rad: float = 0.0,
) -> np.ndarray:
    """Reference-mirror sinusoidal vibration phase for a three-pulse AI.

    Uses z(t)=A sin(2π f t + φ0) and Δφ = k_eff [z(0) - 2 z(T) + z(2T)].
    """
    amps = np.asarray(amplitudes_m, dtype=np.float64)
    T = float(interferometer_time_s)
    w = 2.0 * np.pi * float(frequency_hz)
    z0 = amps * np.sin(float(phase0_rad))
    z1 = amps * np.sin(w * T + float(phase0_rad))
    z2 = amps * np.sin(2.0 * w * T + float(phase0_rad))
    return float(k_eff_rad_per_m) * (z0 - 2.0 * z1 + z2)


def equivalent_gravity_error_m_s2(
    phase_rad: np.ndarray | float,
    *,
    k_eff_rad_per_m: float,
    interferometer_time_s: float,
) -> np.ndarray:
    denom = max(abs(float(k_eff_rad_per_m) * (float(interferometer_time_s) ** 2)), 1e-30)
    return np.asarray(phase_rad, dtype=np.float64) / denom


def normalized_differential_signal(port2: np.ndarray | float, port3: np.ndarray | float) -> np.ndarray:
    p2 = np.asarray(port2, dtype=np.float64)
    p3 = np.asarray(port3, dtype=np.float64)
    closed_total = np.maximum(p2 + p3, 1e-15)
    return (p3 - p2) / closed_total
