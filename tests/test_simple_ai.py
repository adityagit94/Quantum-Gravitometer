"""Direct unit tests for the minimal baseline model in ``qgrav.sim_ai.simple_ai``."""

from __future__ import annotations

import numpy as np

from qgrav.sim_ai.simple_ai import phase_mach_zehnder, simulate_phase_timeseries


def test_phase_mach_zehnder_matches_k_a_T_squared():
    k_eff = 1.6e7
    a = 9.81
    T = 0.26
    assert phase_mach_zehnder(k_eff, a, T) == k_eff * a * T**2


def test_phase_mach_zehnder_zero_acceleration_gives_zero_phase():
    assert phase_mach_zehnder(1.6e7, 0.0, 0.26) == 0.0


def test_phase_mach_zehnder_scales_quadratically_with_T():
    phi_1 = phase_mach_zehnder(1.6e7, 9.81, 0.1)
    phi_2 = phase_mach_zehnder(1.6e7, 9.81, 0.2)
    np.testing.assert_allclose(phi_2, 4.0 * phi_1)


def test_simulate_phase_timeseries_shapes_and_time_axis():
    out = simulate_phase_timeseries(
        k_eff=1.6e7,
        T=0.26,
        a_mean=9.81,
        sample_rate_hz=10.0,
        duration_s=2.0,
        seed=1,
    )
    assert set(out) == {"t", "a", "phi"}
    assert out["t"].shape == out["a"].shape == out["phi"].shape == (20,)
    np.testing.assert_allclose(np.diff(out["t"]), 0.1)
    assert out["t"][0] == 0.0


def test_simulate_phase_timeseries_noiseless_is_constant():
    out = simulate_phase_timeseries(
        k_eff=1.6e7,
        T=0.26,
        a_mean=9.81,
        sample_rate_hz=5.0,
        duration_s=1.0,
    )
    np.testing.assert_allclose(out["a"], 9.81)
    np.testing.assert_allclose(out["phi"], 1.6e7 * 9.81 * 0.26**2)


def test_simulate_phase_timeseries_seed_reproducible():
    kwargs = dict(
        k_eff=1.6e7,
        T=0.26,
        a_mean=9.81,
        sample_rate_hz=100.0,
        duration_s=1.0,
        a_noise_std=1e-6,
        seed=42,
    )
    out1 = simulate_phase_timeseries(**kwargs)
    out2 = simulate_phase_timeseries(**kwargs)
    np.testing.assert_array_equal(out1["a"], out2["a"])
    np.testing.assert_array_equal(out1["phi"], out2["phi"])


def test_simulate_phase_timeseries_noise_statistics():
    out = simulate_phase_timeseries(
        k_eff=1.0,
        T=1.0,
        a_mean=0.0,
        sample_rate_hz=1000.0,
        duration_s=50.0,
        a_noise_std=1.0,
        seed=7,
    )
    # 50k samples: the sample std should sit close to the requested std.
    assert abs(float(np.std(out["a"])) - 1.0) < 0.02
    # phi = k*T^2*a with k=T=1 -> identical to a
    np.testing.assert_array_equal(out["phi"], out["a"])
