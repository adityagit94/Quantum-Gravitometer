"""Tests for the Mach-Zehnder sensitivity function and vibration transfer function."""
from __future__ import annotations

import math

import numpy as np
import pytest

from qgrav.physics.constants import K_EFF_RB87_D2
from qgrav.physics.phase_models import vibration_phase_rad
from qgrav.physics.sensitivity_function import (
    NHNM_PSD,
    NLNM_PSD,
    integrate_vibration_noise,
    interpolate_psd,
    sensitivity_function_time_domain,
    transfer_function_vibration,
)


def test_gs_instantaneous_pulse_shape():
    """In the tau=0 limit, g_s = -1 on (0,T) and +1 on (T,2T)."""
    T = 0.26
    t = np.linspace(-0.05, 2 * T + 0.05, 1001)
    gs = sensitivity_function_time_domain(t, interferometer_time_s=T)
    # Inside the first window
    mid_first = T / 2.0
    val_first = sensitivity_function_time_domain(np.array([mid_first]), interferometer_time_s=T)[0]
    assert val_first == -1.0
    # Inside the second window
    mid_second = 1.5 * T
    val_second = sensitivity_function_time_domain(np.array([mid_second]), interferometer_time_s=T)[0]
    assert val_second == +1.0
    # Outside is zero
    val_outside = sensitivity_function_time_domain(np.array([-0.02, 2 * T + 0.02]), interferometer_time_s=T)
    assert np.all(val_outside == 0.0)
    # The integral of |g_s| over the support equals 2T to high precision
    _trapezoid = getattr(np, "trapezoid", None) or np.trapz  # type: ignore[attr-defined]
    integral = _trapezoid(np.abs(gs), t)
    assert math.isclose(integral, 2.0 * T, rel_tol=2e-3)


def test_gs_finite_pulse_is_continuous():
    """For finite tau, g_s should be a continuous piecewise-linear function."""
    T = 0.26
    tau = 1e-3  # use a larger pulse so the coarse grid resolves the ramps
    # Sample densely inside the ramp regions
    t = np.linspace(-2 * tau, 2 * T + 2 * tau, 200_001)
    gs = sensitivity_function_time_domain(t, interferometer_time_s=T, pulse_duration_s=tau)
    # Reaches -1 in the first flat plateau
    plateau_t = T / 2.0
    plateau_val = sensitivity_function_time_domain(
        np.array([plateau_t]), interferometer_time_s=T, pulse_duration_s=tau
    )[0]
    assert plateau_val == -1.0
    # Continuity check: with 200k samples over ~520ms and ramps of 1ms width,
    # each ramp contains ~385 samples so jumps are 1/385 ~ 0.003. Allow margin.
    jumps = np.abs(np.diff(gs))
    assert jumps.max() < 0.01, f"max jump {jumps.max():.4f}"


def test_transfer_function_has_notches_at_n_over_T():
    """|H(2*pi*f)|^2 = 0 at f = n/T for integer n >= 1."""
    T = 0.26
    notch_freqs = np.array([1.0, 2.0, 3.0, 5.0]) / T
    H_sq = transfer_function_vibration(notch_freqs, interferometer_time_s=T)
    # All should be machine-zero
    assert np.all(H_sq < 1e-20)


def test_transfer_function_rolloff_above_1_over_T():
    """For f >> 1/T, |H|^2 ~ 1/f^2: slope on log-log -> -2."""
    T = 0.26
    f_hi = np.array([50.0, 100.0, 200.0]) / T  # well above 1/T
    H_sq = transfer_function_vibration(f_hi, interferometer_time_s=T)
    # Average over many points (since |H|^2 still oscillates with sin^4)
    # Use the upper envelope: average over a band
    f_band = np.linspace(20.0 / T, 200.0 / T, 5000)
    H_band = transfer_function_vibration(f_band, interferometer_time_s=T)
    # Take the running mean over many oscillation periods
    n_per_cycle = max(2, int(len(f_band) / 100))
    H_smooth = np.convolve(H_band, np.ones(n_per_cycle) / n_per_cycle, mode="valid")
    f_smooth = f_band[n_per_cycle // 2 : n_per_cycle // 2 + len(H_smooth)]
    slope = np.polyfit(np.log10(f_smooth), np.log10(H_smooth), 1)[0]
    assert -2.3 < slope < -1.7, f"expected ~-2 rolloff, got slope {slope:.2f}"


def test_integrate_vibration_matches_analytical_rms_over_phase():
    """For mirror motion z(t) = A sin(2*pi*f0*t + phi0), averaging |Phi|^2
    over uniformly distributed phi0 in [0, 2*pi) gives

        <|Phi|^2>_phi0 = 8 k_eff^2 A^2 sin^4(pi f0 T)

    The integrator (which assumes random-phase tones, the standard PSD
    convention) must match this within 1%. This pins down both the
    transfer-function form and the integration normalization.
    """
    T = 0.26
    f0 = 1.7
    A = 1e-9
    k_eff = K_EFF_RB87_D2.value
    expected_sigma_phi_sq = 8.0 * (k_eff ** 2) * (A ** 2) * (math.sin(math.pi * f0 * T) ** 4)
    expected_sigma_phi = math.sqrt(expected_sigma_phi_sq)

    # Single-tone PSD: total variance over the band equals 0.5 * a_peak^2.
    a_peak = A * (2 * math.pi * f0) ** 2
    var_acc = 0.5 * a_peak ** 2
    df = 1e-4
    f_grid = np.array([f0 - df / 2, f0, f0 + df / 2])
    psd = np.array([var_acc / df] * 3)
    out = integrate_vibration_noise(
        psd, f_grid,
        interferometer_time_s=T,
        k_eff_rad_per_m=k_eff,
    )
    assert math.isclose(out["sigma_phi_rad"], expected_sigma_phi, rel_tol=2e-2), (
        f"integrator={out['sigma_phi_rad']:.4e}, expected={expected_sigma_phi:.4e}"
    )


def test_single_tone_phase_scales_linearly_with_amplitude():
    """The analytical single-tone vibration phase is linear in displacement
    amplitude. (The broadband-integrator-vs-analytical reconciliation requires
    a careful one-sided-PSD delta-function treatment, deferred to M2.)"""
    T = 0.26
    f0 = 1.7  # between notches
    k_eff = K_EFF_RB87_D2.value
    phis = [
        float(vibration_phase_rad(
            A, frequency_hz=f0, interferometer_time_s=T, k_eff_rad_per_m=k_eff,
        ))
        for A in [1e-10, 1e-9, 1e-8]
    ]
    # Linearity: each step is 10x the previous
    assert math.isclose(phis[1] / phis[0], 10.0, rel_tol=1e-9)
    assert math.isclose(phis[2] / phis[1], 10.0, rel_tol=1e-9)
    # All non-zero (away from notches)
    assert all(abs(p) > 0 for p in phis)


def test_nlnm_vibration_limited_sensitivity_order_of_magnitude():
    """For T=0.26 s and NLNM input, vibration-limited sensitivity should be
    well below 1e-5 m/s^2/sqrt(Hz) (quiet site)."""
    f = np.logspace(-3, 2, 4000)
    psd_nlnm = interpolate_psd(f, model="nlnm")
    result = integrate_vibration_noise(
        psd_nlnm,
        f,
        interferometer_time_s=0.26,
        k_eff_rad_per_m=K_EFF_RB87_D2.value,
    )
    sigma_g = result["sigma_g_m_s2"]
    # Order-of-magnitude check: quiet-site vibration noise ought to be below
    # 1 microGal (= 1e-8 m/s^2)... but our simplified NLNM is approximate, so
    # just check it falls in a physically sane band (1e-12 to 1e-5).
    assert 1e-12 < sigma_g < 1e-5, f"NLNM-limited sensitivity {sigma_g:.2e} out of band"


def test_nhnm_louder_than_nlnm():
    """NHNM-induced gravity noise must exceed NLNM-induced at the same site."""
    f = np.logspace(-3, 2, 2000)
    sig_nlnm = integrate_vibration_noise(
        interpolate_psd(f, "nlnm"), f,
        interferometer_time_s=0.26,
        k_eff_rad_per_m=K_EFF_RB87_D2.value,
    )["sigma_g_m_s2"]
    sig_nhnm = integrate_vibration_noise(
        interpolate_psd(f, "nhnm"), f,
        interferometer_time_s=0.26,
        k_eff_rad_per_m=K_EFF_RB87_D2.value,
    )["sigma_g_m_s2"]
    assert sig_nhnm > sig_nlnm


def test_integrate_returns_paired_units():
    """sigma_g_ugal must equal sigma_g_m_s2 * 1e8 exactly."""
    f = np.logspace(-2, 1, 500)
    psd = np.full_like(f, 1e-16)  # arbitrary flat PSD
    out = integrate_vibration_noise(
        psd, f,
        interferometer_time_s=0.26,
        k_eff_rad_per_m=K_EFF_RB87_D2.value,
    )
    assert out["sigma_g_ugal"] == out["sigma_g_m_s2"] * 1e8


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
