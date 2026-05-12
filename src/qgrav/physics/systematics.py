"""Systematic effects for atom interferometer gravimeters.

All functions provide order-of-magnitude estimates. These effects are NOT
included in the AISim simulation.
"""
from __future__ import annotations

import numpy as np
from typing import Any


def gravity_gradient_shift_m_s2(
    gradient_per_m: float = 3.086e-6,
    drop_height_m: float = 0.0,
    interferometer_time_s: float = 0.260,
) -> float:
    """Order-of-magnitude vertical gravity gradient effect.

    Order-of-magnitude estimate. Not included in AISim simulation.

    delta_g ~ gamma * (h + 0.5 * g * T^2) where gamma is the vertical
    gradient (free-air ~ 3.086e-6 /s^2/m), h is initial cloud height,
    and 0.5*g*T^2 is the free-fall distance during interrogation.

    Raises :class:`ValueError` if ``interferometer_time_s`` is negative.
    """
    if interferometer_time_s < 0:
        raise ValueError("interferometer_time_s must be non-negative")
    g_approx = 9.81
    effective_drop = abs(drop_height_m) + 0.5 * g_approx * interferometer_time_s**2
    return abs(gradient_per_m) * effective_drop


def coriolis_shift_m_s2(
    latitude_deg: float = 45.0,
    horizontal_velocity_m_s: float = 1e-3,
) -> float:
    """Coriolis systematic shift from Earth rotation.

    Order-of-magnitude estimate. Not included in AISim simulation.

    delta_g = 2 * Omega_earth * v_horizontal * |cos(latitude)|

    Latitude is clamped to [-90, 90]. The absolute value of cos(latitude)
    is used so the result is always a non-negative magnitude.
    """
    omega_earth = 7.2921e-5  # rad/s
    lat_clamped = float(np.clip(latitude_deg, -90.0, 90.0))
    lat_rad = np.radians(lat_clamped)
    return 2.0 * omega_earth * abs(horizontal_velocity_m_s) * abs(float(np.cos(lat_rad)))


def systematics_summary(
    interferometer_time_s: float = 0.260,
    gradient_per_m: float = 3.086e-6,
    drop_height_m: float = 0.0,
    latitude_deg: float = 45.0,
    horizontal_velocity_m_s: float = 1e-3,
) -> dict[str, Any]:
    """Compute a summary of systematic effects.

    Order-of-magnitude estimates. Not included in AISim simulation.

    Returns a dict with each effect's value in m/s^2 and uGal, plus notes.
    """
    grad = gravity_gradient_shift_m_s2(gradient_per_m, drop_height_m, interferometer_time_s)
    cori = coriolis_shift_m_s2(latitude_deg, horizontal_velocity_m_s)

    return {
        "gravity_gradient": {
            "value_m_s2": grad,
            "value_ugal": grad * 1e8,
            "note": f"Free-air gradient {gradient_per_m:.2e} /s^2/m, T={interferometer_time_s} s",
        },
        "coriolis": {
            "value_m_s2": cori,
            "value_ugal": cori * 1e8,
            "note": f"Lat={latitude_deg} deg, v_h={horizontal_velocity_m_s:.1e} m/s",
        },
        "total_systematic_m_s2": grad + cori,
        "total_systematic_ugal": (grad + cori) * 1e8,
    }
