"""Tests for time-domain vibration noise generator (Phase 4)."""

from __future__ import annotations

import numpy as np
import pytest

from qgrav.physics.noise_models import generate_vibration_timeseries


class TestVibrationPSDMatchesInput:
    """Generated time-series should have PSD close to the input NLNM PSD."""

    def test_vibration_psd_matches_input(self):
        # Long enough series to get good PSD resolution
        result = generate_vibration_timeseries(
            duration_s=400.0,
            sample_rate_hz=20.0,
            seismic_model="nlnm",
            isolation_cutoff_hz=0.0,
            seed=42,
        )
        accel = result["accel_m_s2"]
        freqs = result["psd_freq_hz"]
        psd_input = result["psd_input_m_s2_2_per_hz"]

        # Compute PSD from time series using Welch-like method
        n = len(accel)
        # Use simple periodogram for simplicity
        spectrum = np.fft.rfft(accel)
        psd_measured = (np.abs(spectrum) ** 2) * 2.0 / (n * 20.0)
        psd_measured[0] = 0.0
        if n % 2 == 0:
            psd_measured[-1] /= 2.0

        # Check at frequencies where NLNM is well-defined (0.01 to 1 Hz)
        mask = (freqs > 0.05) & (freqs < 1.0) & (psd_input > 0)
        if not np.any(mask):
            pytest.skip("No frequencies in range")
        # PSD should match input within a factor of 3 (statistical fluctuation)
        ratio = psd_measured[mask] / psd_input[mask]
        median_ratio = float(np.median(ratio))
        assert 0.3 < median_ratio < 3.0, f"PSD ratio out of range: median = {median_ratio}"


class TestVibrationIsolationAttenuates:
    """Isolation filter should attenuate low frequencies."""

    def test_vibration_isolation_attenuates(self):
        result = generate_vibration_timeseries(
            duration_s=400.0,
            sample_rate_hz=20.0,
            seismic_model="nlnm",
            isolation_cutoff_hz=1.0,  # 1 Hz cutoff
            seed=42,
        )
        freqs = result["psd_freq_hz"]
        psd_input = result["psd_input_m_s2_2_per_hz"]
        psd_filtered = result["psd_filtered_m_s2_2_per_hz"]

        # At f=0.1 Hz (f << f_c=1), H^2 = (0.1)^4 / (0.1^2 + 1)^2 ≈ 1e-4
        idx_low = np.argmin(np.abs(freqs - 0.1))
        if psd_input[idx_low] > 0:
            attenuation = psd_filtered[idx_low] / psd_input[idx_low]
            expected_H2 = (0.1**4) / ((0.1**2 + 1.0**2) ** 2)
            np.testing.assert_allclose(attenuation, expected_H2, rtol=0.1)

    def test_vibration_isolation_passthrough_at_high_f(self):
        """At f >> f_c, isolation filter should have ~unity gain."""
        result = generate_vibration_timeseries(
            duration_s=20.0,
            sample_rate_hz=100.0,
            seismic_model="nlnm",
            isolation_cutoff_hz=1.0,
            seed=42,
        )
        freqs = result["psd_freq_hz"]
        psd_input = result["psd_input_m_s2_2_per_hz"]
        psd_filtered = result["psd_filtered_m_s2_2_per_hz"]

        # At f=10 Hz (f >> 1), H^2 = (10)^4 / (100+1)^2 ≈ 1
        idx_high = np.argmin(np.abs(freqs - 10.0))
        if psd_input[idx_high] > 0:
            attenuation = psd_filtered[idx_high] / psd_input[idx_high]
            assert attenuation > 0.95, f"High-f attenuation: {attenuation}"


class TestVibrationDeterministicWithSeed:
    """Same seed should produce identical output."""

    def test_vibration_deterministic_with_seed(self):
        kwargs = dict(
            duration_s=10.0,
            sample_rate_hz=50.0,
            seismic_model="nlnm",
            isolation_cutoff_hz=1.0,
            seed=123,
        )
        r1 = generate_vibration_timeseries(**kwargs)
        r2 = generate_vibration_timeseries(**kwargs)
        np.testing.assert_array_equal(r1["accel_m_s2"], r2["accel_m_s2"])
        np.testing.assert_array_equal(r1["displacement_m"], r2["displacement_m"])

    def test_vibration_different_seeds_differ(self):
        r1 = generate_vibration_timeseries(
            duration_s=10.0,
            sample_rate_hz=50.0,
            seed=1,
        )
        r2 = generate_vibration_timeseries(
            duration_s=10.0,
            sample_rate_hz=50.0,
            seed=2,
        )
        # They should differ in at least 50% of samples
        diff = np.abs(r1["accel_m_s2"] - r2["accel_m_s2"])
        assert np.median(diff) > 0


class TestTimeDomainOutputShape:
    """Output time-series should have the correct length and structure."""

    def test_output_shape(self):
        result = generate_vibration_timeseries(
            duration_s=2.0,
            sample_rate_hz=10.0,
            seed=0,
        )
        # n_samples = duration * fs = 20
        assert len(result["t_s"]) == 20
        assert len(result["accel_m_s2"]) == 20
        assert len(result["velocity_m_s"]) == 20
        assert len(result["displacement_m"]) == 20
        # Time array
        np.testing.assert_allclose(result["t_s"][0], 0.0)
        np.testing.assert_allclose(result["t_s"][1] - result["t_s"][0], 0.1)


class TestDisplacementDoubleIntegralOfAcceleration:
    """Numerical d²(disp)/dt² should approximately equal accel for low-frequency content."""

    def test_displacement_relates_to_accel(self):
        """For a band-limited signal, freq-domain double-integration should be self-consistent."""
        result = generate_vibration_timeseries(
            duration_s=200.0,
            sample_rate_hz=20.0,
            seismic_model="nlnm",
            isolation_cutoff_hz=0.5,
            seed=42,
        )
        accel = result["accel_m_s2"]
        disp = result["displacement_m"]
        # The displacement and acceleration should have correlated structure
        # Take the FFTs and verify A(f) = -ω² X(f) for f > 0.
        fs = 20.0
        n = len(accel)
        freqs = np.fft.rfftfreq(n, d=1.0 / fs)
        A = np.fft.rfft(accel)
        X = np.fft.rfft(disp)
        omega = 2.0 * np.pi * freqs
        # For nonzero freqs:
        nonzero = freqs > 0.5  # well above DC, where it's defined
        if np.any(nonzero):
            ratio = A[nonzero] / (-(omega[nonzero] ** 2) * X[nonzero] + 1e-30)
            # Most of the ratios should be very close to 1
            # (we don't check NaN; expect them where X is tiny)
            valid = np.isfinite(ratio) & (np.abs(X[nonzero]) > 1e-15)
            if np.any(valid):
                median_real = float(np.median(np.real(ratio[valid])))
                assert 0.5 < median_real < 2.0, f"ratio median = {median_real}"
