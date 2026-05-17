"""Regression test: every paired m/s^2 + uGal output must use the exact
conversion factor 1 microGal = 1e-8 m/s^2."""
from __future__ import annotations

import numpy as np
import pytest

from qgrav.physics.constants import K_EFF_RB87_D2
from qgrav.physics.phase_models import (
    sensitivity_ugal_per_sqrt_hz,
    shot_noise_sensitivity_m_s2_per_sqrt_hz,
)
from qgrav.physics.sensitivity_function import integrate_vibration_noise
from qgrav.physics.systematics import systematics_summary


def test_shot_noise_sensitivity_paired_units():
    k_eff = K_EFF_RB87_D2.value
    si = shot_noise_sensitivity_m_s2_per_sqrt_hz(
        k_eff_rad_per_m=k_eff, interferometer_time_s=0.26, n_atoms=600
    )
    ugal = sensitivity_ugal_per_sqrt_hz(
        k_eff_rad_per_m=k_eff, interferometer_time_s=0.26, n_atoms=600
    )
    assert ugal == si * 1e8


def test_systematics_summary_paired_units():
    summary = systematics_summary(
        interferometer_time_s=0.26,
        latitude_deg=45.0,
        horizontal_velocity_m_s=1e-3,
    )
    grad = summary["gravity_gradient"]
    cori = summary["coriolis"]
    assert grad["value_ugal"] == grad["value_m_s2"] * 1e8
    assert cori["value_ugal"] == cori["value_m_s2"] * 1e8
    assert summary["total_systematic_ugal"] == summary["total_systematic_m_s2"] * 1e8


def test_integrate_vibration_noise_paired_units():
    f = np.logspace(-2, 1, 200)
    psd = np.full_like(f, 1e-14)
    out = integrate_vibration_noise(
        psd, f,
        interferometer_time_s=0.26,
        k_eff_rad_per_m=K_EFF_RB87_D2.value,
    )
    assert out["sigma_g_ugal"] == out["sigma_g_m_s2"] * 1e8


@pytest.mark.parametrize(
    "si_func,ugal_func,kwargs",
    [
        (
            shot_noise_sensitivity_m_s2_per_sqrt_hz,
            sensitivity_ugal_per_sqrt_hz,
            dict(k_eff_rad_per_m=1.6e7, interferometer_time_s=0.26, n_atoms=500),
        ),
        (
            shot_noise_sensitivity_m_s2_per_sqrt_hz,
            sensitivity_ugal_per_sqrt_hz,
            dict(k_eff_rad_per_m=1.6e7, interferometer_time_s=0.5, n_atoms=1000, contrast=0.8),
        ),
    ],
)
def test_paired_si_to_ugal_ratio_exact(si_func, ugal_func, kwargs):
    si = si_func(**kwargs)
    ugal = ugal_func(**kwargs)
    # Exact arithmetic equality (no float drift) because the ugal helper
    # multiplies by 1e8 directly on the SI result.
    assert ugal == si * 1e8
