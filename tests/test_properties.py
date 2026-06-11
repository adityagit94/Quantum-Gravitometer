"""Property-based tests using Hypothesis for qgrav core modules.

These tests verify mathematical invariants and structural properties that
must hold for ALL valid inputs, not just a few manually chosen examples.
"""

from __future__ import annotations

import numpy as np
import pytest
from hypothesis import HealthCheck, given, settings
from hypothesis import strategies as st
from hypothesis.extra.numpy import arrays

from qgrav.datasets._tides_hw95 import gravity_tide_m_s2, gravity_tide_ugal
from qgrav.metrics.allan import allan_deviation_overlapping
from qgrav.metrics.psd import compute_psd
from qgrav.metrics.summary import compute_error_statistics, improvement_percent
from qgrav.physics.phase_models import (
    equivalent_gravity_error_m_s2,
    gravity_phase_rad,
    normalized_differential_signal,
    shot_noise_sensitivity_m_s2_per_sqrt_hz,
)
from qgrav.physics.sensitivity_function import (
    sensitivity_function_time_domain,
    transfer_function_vibration,
)

# ─── Reusable strategies ────────────────────────────────────────────────


def _finite_floats(min_value=-1e6, max_value=1e6):
    return st.floats(
        min_value=min_value, max_value=max_value, allow_nan=False, allow_infinity=False
    )


def _positive_floats(min_value=1e-6, max_value=1e6):
    return st.floats(
        min_value=min_value, max_value=max_value, allow_nan=False, allow_infinity=False
    )


def _signal_arrays(min_size=20, max_size=500):
    return arrays(
        dtype=np.float64,
        shape=st.integers(min_value=min_size, max_value=max_size),
        elements=_finite_floats(-100, 100),
    )


# ═══════════════════════════════════════════════════════════════════════
# PSD properties
# ═══════════════════════════════════════════════════════════════════════


@given(
    x=_signal_arrays(min_size=8, max_size=256),
    fs=_positive_floats(1.0, 1e4),
)
@settings(max_examples=40, suppress_health_check=[HealthCheck.too_slow])
def test_psd_non_negative(x, fs):
    """PSD values must be >= 0 for any real-valued input."""
    result = compute_psd(x, fs, method="periodogram")
    assert np.all(result["psd"] >= 0), "PSD has negative values"


@given(
    x=_signal_arrays(min_size=8, max_size=256),
    fs=_positive_floats(1.0, 1e4),
)
@settings(max_examples=40, suppress_health_check=[HealthCheck.too_slow])
def test_psd_frequency_grid_structure(x, fs):
    """PSD frequency grid starts at 0 and has correct length (n//2+1)."""
    result = compute_psd(x, fs, method="periodogram")
    f = result["f_hz"]
    n = len(x)
    assert f[0] == pytest.approx(0.0)
    assert len(f) == n // 2 + 1
    # For even n the last bin is exactly fs/2; for odd n it falls short.
    assert f[-1] <= fs / 2.0 + 1e-10


@given(
    x=_signal_arrays(min_size=32, max_size=256),
    fs=_positive_floats(1.0, 1e4),
)
@settings(max_examples=30, suppress_health_check=[HealthCheck.too_slow])
def test_psd_welch_non_negative(x, fs):
    """Welch PSD values must be >= 0."""
    nperseg = min(16, len(x))
    noverlap = nperseg // 2
    result = compute_psd(x, fs, method="welch", nperseg=nperseg, noverlap=noverlap)
    assert np.all(result["psd"] >= 0), "Welch PSD has negative values"


@given(x=_signal_arrays(min_size=8, max_size=128))
@settings(max_examples=30, suppress_health_check=[HealthCheck.too_slow])
def test_psd_constant_input_is_near_zero(x):
    """A constant signal (after removing mean) has zero variance → PSD ~ 0."""
    c = np.ones_like(x) * 42.0
    result = compute_psd(c, 100.0, method="periodogram")
    # DC bin can be nonzero if mean isn't perfectly subtracted, but rest should be ~0
    assert np.allclose(result["psd"][1:], 0.0, atol=1e-20)


# ═══════════════════════════════════════════════════════════════════════
# Allan deviation properties
# ═══════════════════════════════════════════════════════════════════════


@given(
    x=_signal_arrays(min_size=50, max_size=200),
    fs=_positive_floats(1.0, 100.0),
)
@settings(max_examples=25, suppress_health_check=[HealthCheck.too_slow])
def test_allan_deviation_non_negative(x, fs):
    """Allan deviation must be >= 0."""
    taus = np.array([5.0 / fs, 10.0 / fs])
    result = allan_deviation_overlapping(x, fs, taus, backend="custom")
    assert np.all(np.asarray(result["adev"]) >= 0)


@given(scale=_positive_floats(0.01, 100.0))
@settings(max_examples=25, suppress_health_check=[HealthCheck.too_slow])
def test_allan_scales_linearly_with_amplitude(scale):
    """Scaling input by k scales ADEV by |k|."""
    rng = np.random.default_rng(42)
    x = rng.normal(size=100)
    taus = np.array([1.0, 5.0])
    result_x = allan_deviation_overlapping(x, 1.0, taus, backend="custom")
    result_kx = allan_deviation_overlapping(x * scale, 1.0, taus, backend="custom")
    if len(result_x["adev"]) > 0 and len(result_kx["adev"]) > 0:
        np.testing.assert_allclose(
            np.asarray(result_kx["adev"]),
            np.asarray(result_x["adev"]) * scale,
            rtol=1e-10,
        )


# ═══════════════════════════════════════════════════════════════════════
# Phase-model properties
# ═══════════════════════════════════════════════════════════════════════


@given(
    g=_finite_floats(-20.0, 20.0),
    k_eff=_positive_floats(1e3, 1e8),
    T=_positive_floats(1e-3, 1.0),
)
@settings(max_examples=50)
def test_phase_gravity_roundtrip(g, k_eff, T):
    """gravity_phase_rad → equivalent_gravity_error must recover the input g."""
    phi = gravity_phase_rad(g, k_eff_rad_per_m=k_eff, interferometer_time_s=T)
    g_recovered = equivalent_gravity_error_m_s2(phi, k_eff_rad_per_m=k_eff, interferometer_time_s=T)
    np.testing.assert_allclose(float(g_recovered), g, rtol=1e-10, atol=1e-15)


@given(
    g=_finite_floats(-20.0, 20.0),
    k_eff=_positive_floats(1e3, 1e8),
    T=_positive_floats(1e-3, 1.0),
    bias=_finite_floats(-10.0, 10.0),
)
@settings(max_examples=40)
def test_phase_bias_shifts_phase(g, k_eff, T, bias):
    """Adding a phase bias offsets the result by exactly that bias.

    We use a tolerance scaled to the magnitude of the main phase term
    to account for floating-point cancellation in subtraction.
    """
    phi_no_bias = gravity_phase_rad(g, k_eff_rad_per_m=k_eff, interferometer_time_s=T)
    phi_with_bias = gravity_phase_rad(
        g, k_eff_rad_per_m=k_eff, interferometer_time_s=T, phase_bias_rad=bias
    )
    # Tolerance must account for catastrophic cancellation when |phi| >> |bias|
    eps_scale = max(abs(float(phi_no_bias)), abs(bias), 1.0) * 1e-12
    np.testing.assert_allclose(phi_with_bias - phi_no_bias, bias, atol=eps_scale)


@given(
    p2=arrays(np.float64, shape=10, elements=_positive_floats(0.01, 100.0)),
    p3=arrays(np.float64, shape=10, elements=_positive_floats(0.01, 100.0)),
)
@settings(max_examples=40)
def test_normalized_signal_bounded(p2, p3):
    """Normalized differential signal must be in [-1, +1] for positive inputs."""
    nds = normalized_differential_signal(p2, p3)
    assert np.all(nds >= -1.0 - 1e-12)
    assert np.all(nds <= 1.0 + 1e-12)


# ═══════════════════════════════════════════════════════════════════════
# Sensitivity function properties
# ═══════════════════════════════════════════════════════════════════════


@given(T=_positive_floats(1e-3, 1.0))
@settings(max_examples=40)
def test_sensitivity_integral_is_zero(T):
    """The integral of the MZ sensitivity function over [0, 2T] must be zero.

    Physical meaning: a constant acceleration produces no net phase shift
    in a balanced interferometer.
    """
    t = np.linspace(-0.01 * T, 2.01 * T, 10_000)
    gs = sensitivity_function_time_domain(t, interferometer_time_s=T)
    integral = np.trapz(gs, t) if not hasattr(np, "trapezoid") else np.trapezoid(gs, t)
    assert abs(integral) < 1e-3 * T, f"Integral {integral} too far from zero"


@given(T=_positive_floats(0.01, 1.0))
@settings(max_examples=40)
def test_sensitivity_antisymmetric_about_T(T):
    """g_s(T-dt) = -g_s(T+dt) for the instantaneous-pulse limit."""
    dt = np.linspace(0.01 * T, 0.99 * T, 200)
    gs_left = sensitivity_function_time_domain(T - dt, interferometer_time_s=T)
    gs_right = sensitivity_function_time_domain(T + dt, interferometer_time_s=T)
    np.testing.assert_allclose(gs_left, -gs_right, atol=1e-12)


@given(T=_positive_floats(0.01, 1.0))
@settings(max_examples=30)
def test_transfer_function_notches_at_harmonics(T):
    """The vibration transfer function has notches at f = n/T."""
    n_harmonics = np.arange(1, 4)
    f_notch = n_harmonics / T
    H_sq = transfer_function_vibration(f_notch, interferometer_time_s=T)
    np.testing.assert_allclose(H_sq, 0.0, atol=1e-20)


@given(T=_positive_floats(0.01, 1.0))
@settings(max_examples=30)
def test_transfer_function_non_negative(T):
    """The transfer function squared is always >= 0."""
    f = np.linspace(0.1, 100.0, 500)
    H_sq = transfer_function_vibration(f, interferometer_time_s=T)
    assert np.all(H_sq >= -1e-30), "Transfer function squared has negative values"


# ═══════════════════════════════════════════════════════════════════════
# Shot noise sensitivity properties
# ═══════════════════════════════════════════════════════════════════════


@given(
    k_eff=_positive_floats(1e4, 1e8),
    T=_positive_floats(0.001, 1.0),
    n_atoms=st.integers(min_value=100, max_value=10_000_000),
    contrast=st.floats(min_value=0.01, max_value=1.0, allow_nan=False, allow_infinity=False),
)
@settings(max_examples=40)
def test_shot_noise_positive(k_eff, T, n_atoms, contrast):
    """Shot noise sensitivity must be positive."""
    s = shot_noise_sensitivity_m_s2_per_sqrt_hz(k_eff, T, n_atoms, contrast)
    assert s > 0


@given(
    k_eff=_positive_floats(1e5, 1e7),
    T=_positive_floats(0.01, 0.5),
    contrast=st.floats(min_value=0.1, max_value=1.0, allow_nan=False, allow_infinity=False),
)
@settings(max_examples=30)
def test_shot_noise_improves_with_more_atoms(k_eff, T, contrast):
    """More atoms → better (lower) shot noise sensitivity (1/sqrt(N))."""
    s_100 = shot_noise_sensitivity_m_s2_per_sqrt_hz(k_eff, T, 100, contrast)
    s_10000 = shot_noise_sensitivity_m_s2_per_sqrt_hz(k_eff, T, 10_000, contrast)
    assert s_10000 < s_100


# ═══════════════════════════════════════════════════════════════════════
# Tide model properties
# ═══════════════════════════════════════════════════════════════════════


@given(lat=st.floats(min_value=-90.0, max_value=90.0, allow_nan=False, allow_infinity=False))
@settings(max_examples=30)
def test_tide_ugal_to_m_s2_conversion(lat):
    """gravity_tide_m_s2 must equal gravity_tide_ugal * 1e-8."""
    t = np.array([1_700_000_000.0])  # fixed timestamp
    ugal = gravity_tide_ugal(t, latitude_deg=lat)
    m_s2 = gravity_tide_m_s2(t, latitude_deg=lat)
    np.testing.assert_allclose(m_s2, ugal * 1e-8, rtol=1e-12)


@given(lat=st.floats(min_value=-90.0, max_value=90.0, allow_nan=False, allow_infinity=False))
@settings(max_examples=30)
def test_tide_finite_output(lat):
    """Tide model must return finite values for any valid latitude."""
    t = np.linspace(1_700_000_000.0, 1_700_100_000.0, 100)
    result = gravity_tide_ugal(t, latitude_deg=lat)
    assert np.all(np.isfinite(result)), "Tide model returned non-finite values"


@given(
    lat=st.floats(min_value=-85.0, max_value=85.0, allow_nan=False, allow_infinity=False),
    lon=st.floats(min_value=-180.0, max_value=180.0, allow_nan=False, allow_infinity=False),
)
@settings(max_examples=20)
def test_tide_amplitude_bounded(lat, lon):
    """Solid earth tide should be bounded (< 500 uGal peak-to-peak)."""
    # One full day of data
    t = np.linspace(1_700_000_000.0, 1_700_086_400.0, 1000)
    result = gravity_tide_ugal(t, latitude_deg=lat, longitude_deg=lon)
    assert np.all(
        np.abs(result) < 500.0
    ), f"Tide amplitude {np.max(np.abs(result)):.1f} uGal exceeds bounds"


# ═══════════════════════════════════════════════════════════════════════
# Error statistics properties
# ═══════════════════════════════════════════════════════════════════════


@given(
    y=arrays(np.float64, shape=50, elements=_finite_floats(-100, 100)),
)
@settings(max_examples=30)
def test_error_stats_perfect_prediction(y):
    """When y_hat == y_true, RMSE and MAE must be zero."""
    stats = compute_error_statistics(y, y)
    assert stats["rmse"] == pytest.approx(0.0, abs=1e-15)
    assert stats["mae"] == pytest.approx(0.0, abs=1e-15)
    assert stats["max_abs_error"] == pytest.approx(0.0, abs=1e-15)


@given(
    y_true=arrays(np.float64, shape=50, elements=_finite_floats(-100, 100)),
    y_hat=arrays(np.float64, shape=50, elements=_finite_floats(-100, 100)),
)
@settings(max_examples=30)
def test_error_stats_rmse_ge_mae(y_true, y_hat):
    """RMSE >= MAE by Jensen's inequality (sqrt of mean of squares >= mean of abs)."""
    stats = compute_error_statistics(y_true, y_hat)
    assert stats["rmse"] >= stats["mae"] - 1e-12


@given(
    baseline=_positive_floats(0.01, 1000.0),
    improved=_positive_floats(0.01, 1000.0),
)
@settings(max_examples=50)
def test_improvement_percent_sign(baseline, improved):
    """Improvement is positive when improved < baseline, negative when worse."""
    pct = improvement_percent(baseline, improved)
    if improved < baseline:
        assert pct > 0
    elif improved > baseline:
        assert pct < 0
    else:
        assert pct == pytest.approx(0.0)
