import numpy as np

from qgrav.sim_ai import (
    is_aisim_available,
    run_aisim_gravity_sweep,
    run_aisim_mach_zehnder_phase_scan,
    run_aisim_rabi_scan,
    run_aisim_vibration_sensitivity_sweep,
)


def test_aisim_is_available():
    assert is_aisim_available() is True


def test_aisim_rabi_scan_shapes_and_bounds():
    out = run_aisim_rabi_scan(n_atoms=150, n_steps=12, tau_step_s=1e-6, seed=2)
    taus = out["taus_s"]
    occ = out["excited_fraction"]
    assert len(taus) == 13
    assert len(occ) == 13
    assert np.all(np.isfinite(occ))
    assert np.all((occ >= 0.0) & (occ <= 1.0))
    assert out["n_atoms_detected"] > 0


def test_mach_zehnder_phase_scan_outputs_are_finite():
    out = run_aisim_mach_zehnder_phase_scan(n_atoms=150, n_phase_points=15, seed=2)
    assert out["model"] == "mach_zehnder_phase_scan"
    assert len(out["phase_scan_rad"]) == 15
    assert np.all(np.isfinite(out["output_port_2"]))
    assert np.all(np.isfinite(out["output_port_3"]))
    assert 0.0 <= out["fringe_fit_r2"] <= 1.0
    assert out["n_atoms_detected"] > 0


def test_gravity_sweep_outputs_are_finite_and_keff_positive():
    out = run_aisim_gravity_sweep(n_atoms=120, n_gravity_points=11, gravity_span_m_s2=2e-6, seed=3)
    assert out["model"] == "gravity_sweep"
    assert len(out["gravity_values_m_s2"]) == 11
    assert out["k_eff_rad_per_m"] > 0
    assert np.all(np.isfinite(out["normalized_differential_signal"]))


def test_vibration_sweep_zero_amplitude_means_zero_equivalent_gravity_error():
    out = run_aisim_vibration_sensitivity_sweep(
        n_atoms=120,
        n_amplitude_points=9,
        amplitude_min_m=0.0,
        amplitude_max_m=1e-8,
        seed=4,
    )
    assert out["model"] == "vibration_sensitivity_sweep"
    assert len(out["vibration_amplitude_m"]) == 9
    assert abs(float(out["equivalent_gravity_error_m_s2"][0])) < 1e-15
    assert np.all(np.isfinite(out["vibration_phase_rad"]))


def test_gravity_sweep_includes_sensitivity():
    out = run_aisim_gravity_sweep(n_atoms=200, n_gravity_points=7, seed=42)
    assert "shot_noise_sensitivity_m_s2_per_sqrt_hz" in out
    assert out["shot_noise_sensitivity_m_s2_per_sqrt_hz"] > 0
    assert "shot_noise_sensitivity_ugal_per_sqrt_hz" in out


def test_phase_scan_includes_sensitivity():
    out = run_aisim_mach_zehnder_phase_scan(n_atoms=200, n_phase_points=9, seed=42)
    assert "shot_noise_sensitivity_m_s2_per_sqrt_hz" in out
    assert out["shot_noise_sensitivity_m_s2_per_sqrt_hz"] > 0


def test_vibration_sweep_includes_sensitivity():
    out = run_aisim_vibration_sensitivity_sweep(n_atoms=200, n_amplitude_points=7, seed=42)
    assert "shot_noise_sensitivity_m_s2_per_sqrt_hz" in out
    assert out["shot_noise_sensitivity_m_s2_per_sqrt_hz"] > 0


def test_aisim_does_not_mutate_global_random_state():
    """Ensure that AISim functions use local RNG and never touch np.random global state."""
    # Set a known global state and capture reference draws
    np.random.seed(12345)
    expected = np.random.random(5).copy()

    # Reset to same global seed, then run AISim in between
    np.random.seed(12345)
    _ = run_aisim_rabi_scan(n_atoms=100, n_steps=5, tau_step_s=1e-6, seed=99)
    actual = np.random.random(5)

    np.testing.assert_array_equal(
        actual,
        expected,
        err_msg="AISim mutated the global numpy random state",
    )
