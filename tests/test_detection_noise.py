"""Tests for detection noise & spontaneous emission models (Phase 5)."""

from __future__ import annotations

import numpy as np

from qgrav.physics.noise_models import (
    add_detection_noise,
    spontaneous_emission_loss_probability,
)


class TestDetectionNoiseScalesWithAtoms:
    """Detection noise std should scale as 1/sqrt(N)."""

    def test_detection_noise_scales_with_atoms(self):
        n_trials = 10000
        populations = np.full(n_trials, 0.5)  # midfringe population

        noisy_100 = add_detection_noise(populations, n_detected=100, seed=42)
        noisy_10000 = add_detection_noise(populations, n_detected=10000, seed=42)

        std_100 = float(np.std(noisy_100))
        std_10000 = float(np.std(noisy_10000))

        # σ(N=100) ≈ 0.1, σ(N=10000) ≈ 0.01
        np.testing.assert_allclose(std_100, 0.1, rtol=0.15)
        np.testing.assert_allclose(std_10000, 0.01, rtol=0.15)
        # Ratio should be approximately sqrt(10000/100) = 10
        ratio = std_100 / std_10000
        np.testing.assert_allclose(ratio, 10.0, rtol=0.2)


class TestDetectionNoiseClipping:
    """Output should be clipped to [0, 1]."""

    def test_detection_noise_clipped(self):
        # Populations at the boundary
        populations = np.array([0.0, 0.5, 1.0] * 100)
        noisy = add_detection_noise(populations, n_detected=10, seed=42)
        assert noisy.min() >= 0.0
        assert noisy.max() <= 1.0

    def test_detection_noise_deterministic_with_seed(self):
        populations = np.array([0.3, 0.5, 0.7])
        r1 = add_detection_noise(populations, n_detected=100, seed=42)
        r2 = add_detection_noise(populations, n_detected=100, seed=42)
        np.testing.assert_array_equal(r1, r2)


class TestSpontaneousEmissionOrderOfMagnitude:
    """For typical Rb-87 D2 parameters, p_se ~ 1e-5 per pulse."""

    def test_spontaneous_emission_order_of_magnitude(self):
        # Typical parameters for Rb-87 Raman π/2 pulse:
        # Rabi freq ≈ 2π·15 kHz, single-photon detuning ~1 GHz
        # pulse duration ~25 µs (π/2 pulse with Ω_eff ≈ 2π·10 kHz)
        omega_eff = 2.0 * np.pi * 15000  # rad/s
        delta_hz = 1.0e9  # 1 GHz detuning
        tau = 25e-6
        lifetime = 26.24e-9  # Rb-87 D2

        p_se = spontaneous_emission_loss_probability(
            rabi_freq_rad_s=omega_eff,
            single_photon_detuning_hz=delta_hz,
            pulse_duration_s=tau,
            excited_state_lifetime_s=lifetime,
        )
        # Expected: (2π·15k / (2π·1e9))² · 25e-6 / 26.24e-9
        # = (1.5e-5)² · 953 ≈ 2.1e-7
        assert 1e-8 < p_se < 1e-5, f"p_se = {p_se:.3e}, expected ~1e-7"

    def test_spontaneous_emission_scales_with_detuning(self):
        """Doubling Δ should reduce p_se by factor of 4 (p_se ~ 1/Δ²)."""
        common = dict(
            rabi_freq_rad_s=1e5,
            pulse_duration_s=25e-6,
            excited_state_lifetime_s=26.24e-9,
        )
        p1 = spontaneous_emission_loss_probability(
            single_photon_detuning_hz=1e9,
            **common,
        )
        p2 = spontaneous_emission_loss_probability(
            single_photon_detuning_hz=2e9,
            **common,
        )
        np.testing.assert_allclose(p1 / p2, 4.0, rtol=1e-10)

    def test_spontaneous_emission_scales_with_duration(self):
        """Doubling τ should double p_se (p_se ~ τ)."""
        common = dict(
            rabi_freq_rad_s=1e5,
            single_photon_detuning_hz=1e9,
            excited_state_lifetime_s=26.24e-9,
        )
        p1 = spontaneous_emission_loss_probability(
            pulse_duration_s=25e-6,
            **common,
        )
        p2 = spontaneous_emission_loss_probability(
            pulse_duration_s=50e-6,
            **common,
        )
        np.testing.assert_allclose(p2 / p1, 2.0, rtol=1e-10)
