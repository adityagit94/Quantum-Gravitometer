from __future__ import annotations

import numpy as np

from .phase_models import (
    equivalent_gravity_error_m_s2,
    gravity_gradient_phase_rad,
    gravity_phase_rad,
    vibration_phase_rad,
)


def expected_gravity_phase_rad(
    g_m_s2: np.ndarray | float,
    *,
    k_eff_rad_per_m: float,
    interferometer_time_s: float,
    phase_bias_rad: float = 0.0,
) -> np.ndarray:
    return gravity_phase_rad(
        g_m_s2,
        k_eff_rad_per_m=k_eff_rad_per_m,
        interferometer_time_s=interferometer_time_s,
        phase_bias_rad=phase_bias_rad,
    )


def expected_vibration_phase_rad(
    amplitudes_m: np.ndarray | float,
    *,
    frequency_hz: float,
    interferometer_time_s: float,
    k_eff_rad_per_m: float,
    phase0_rad: float = 0.0,
) -> np.ndarray:
    return vibration_phase_rad(
        amplitudes_m,
        frequency_hz=frequency_hz,
        interferometer_time_s=interferometer_time_s,
        k_eff_rad_per_m=k_eff_rad_per_m,
        phase0_rad=phase0_rad,
    )


def expected_gravity_gradient_phase_rad(
    *,
    k_eff_rad_per_m: float,
    gravity_gradient_per_m: float,
    g_m_s2: float,
    interferometer_time_s: float,
    initial_position_m: float = 0.0,
    initial_velocity_m_s: float = 0.0,
    z_ref_m: float = 0.0,
) -> float:
    return gravity_gradient_phase_rad(
        k_eff_rad_per_m=k_eff_rad_per_m,
        gravity_gradient_per_m=gravity_gradient_per_m,
        g_m_s2=g_m_s2,
        interferometer_time_s=interferometer_time_s,
        initial_position_m=initial_position_m,
        initial_velocity_m_s=initial_velocity_m_s,
        z_ref_m=z_ref_m,
    )


def expected_population_fringe(
    phase_rad: np.ndarray | float, *, offset: float, amplitude: float, phase_offset_rad: float
) -> np.ndarray:
    phase = np.asarray(phase_rad, dtype=np.float64)
    return offset + amplitude * np.cos(phase + float(phase_offset_rad))


def expected_equivalent_gravity_error_m_s2(
    phase_rad: np.ndarray | float, *, k_eff_rad_per_m: float, interferometer_time_s: float
) -> np.ndarray:
    return equivalent_gravity_error_m_s2(
        phase_rad,
        k_eff_rad_per_m=k_eff_rad_per_m,
        interferometer_time_s=interferometer_time_s,
    )
