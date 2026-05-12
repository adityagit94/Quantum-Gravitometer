import numpy as np

from qgrav.physics import (
    MachZehnderPulseSequence,
    RabiPulseScan,
    equivalent_gravity_error_m_s2,
    gravity_phase_rad,
    gravity_sweep_axis,
    normalized_differential_signal,
    phase_scan_axis,
    vibration_amplitude_axis,
    vibration_phase_rad,
)


def test_rabi_pulse_scan_axis():
    scan = RabiPulseScan(tau_step_s=1e-6, n_steps=4)
    taus = scan.tau_axis()
    assert np.allclose(taus, np.array([0.0, 1e-6, 2e-6, 3e-6, 4e-6]))


def test_mach_zehnder_sequence_helpers():
    seq = MachZehnderPulseSequence(tau_pi_half_s=2.3e-5, interferometer_time_s=0.26)
    assert seq.pulse_durations_s() == (2.3e-5, 4.6e-5, 2.3e-5)
    assert seq.pulse_times_s() == (0.0, 0.26, 0.52)


def test_phase_and_equivalent_gravity_are_consistent():
    g = np.array([9.81, 9.810001])
    k_eff = 1.6e7
    T = 0.26
    phi = gravity_phase_rad(g, k_eff_rad_per_m=k_eff, interferometer_time_s=T, phase_bias_rad=0.0)
    dg = equivalent_gravity_error_m_s2(phi - phi[0], k_eff_rad_per_m=k_eff, interferometer_time_s=T)
    assert np.isclose(dg[0], 0.0)
    assert np.isclose(dg[1], g[1] - g[0])


def test_vibration_phase_is_linear_in_amplitude():
    amps = vibration_amplitude_axis(0.0, 1e-8, 8)
    phase = vibration_phase_rad(
        amps,
        frequency_hz=1.0,
        interferometer_time_s=0.26,
        k_eff_rad_per_m=1.6e7,
        phase0_rad=0.3,
    )
    ratios = phase[1:] / amps[1:]
    assert np.allclose(ratios, ratios[0])


def test_normalized_differential_signal_bounds():
    p2 = np.array([0.2, 0.6])
    p3 = np.array([0.8, 0.4])
    nd = normalized_differential_signal(p2, p3)
    assert np.all(nd <= 1.0)
    assert np.all(nd >= -1.0)


def test_scan_axis_helpers_lengths():
    assert len(phase_scan_axis(0.0, 2.0 * np.pi, 9)) == 9
    assert len(gravity_sweep_axis(9.81, 1e-6, 7)) == 7
    assert len(vibration_amplitude_axis(0.0, 1e-8, 11)) == 11


def test_shot_noise_sensitivity_hand_calculated():
    """Verify against hand calculation.
    k_eff=1.6e7, T=0.26, N=1e6, C=0.5, T_cycle=1:
    delta_g = 1/(0.5 * 1.6e7 * 0.0676 * 1000) = 1/5.408e8 ~ 1.85e-9
    """
    from qgrav.physics.phase_models import shot_noise_sensitivity_m_s2_per_sqrt_hz
    result = shot_noise_sensitivity_m_s2_per_sqrt_hz(1.6e7, 0.26, 1_000_000, 0.5, 1.0)
    assert 1e-9 < result < 3e-9


def test_sensitivity_scales_with_sqrt_N():
    from qgrav.physics.phase_models import shot_noise_sensitivity_m_s2_per_sqrt_hz
    s100 = shot_noise_sensitivity_m_s2_per_sqrt_hz(1.6e7, 0.26, 100, 1.0)
    s10000 = shot_noise_sensitivity_m_s2_per_sqrt_hz(1.6e7, 0.26, 10000, 1.0)
    ratio = s100 / s10000
    assert abs(ratio - 10.0) < 0.1  # sqrt(10000/100) = 10


def test_sensitivity_scales_with_T_squared():
    from qgrav.physics.phase_models import shot_noise_sensitivity_m_s2_per_sqrt_hz
    s1 = shot_noise_sensitivity_m_s2_per_sqrt_hz(1.6e7, 0.1, 1000, 1.0)
    s2 = shot_noise_sensitivity_m_s2_per_sqrt_hz(1.6e7, 0.2, 1000, 1.0)
    ratio = s1 / s2
    assert abs(ratio - 4.0) < 0.1  # (0.2/0.1)^2 = 4


def test_sensitivity_rejects_bad_inputs():
    from qgrav.physics.phase_models import shot_noise_sensitivity_m_s2_per_sqrt_hz
    import pytest
    with pytest.raises(ValueError):
        shot_noise_sensitivity_m_s2_per_sqrt_hz(1.6e7, 0.26, 0, 1.0)
    with pytest.raises(ValueError):
        shot_noise_sensitivity_m_s2_per_sqrt_hz(1.6e7, 0.26, 100, 0.0)
    with pytest.raises(ValueError):
        shot_noise_sensitivity_m_s2_per_sqrt_hz(1.6e7, 0.26, 100, 1.5)
    # k_eff must be positive
    with pytest.raises(ValueError):
        shot_noise_sensitivity_m_s2_per_sqrt_hz(0.0, 0.26, 100, 1.0)
    with pytest.raises(ValueError):
        shot_noise_sensitivity_m_s2_per_sqrt_hz(-1.6e7, 0.26, 100, 1.0)
    # cycle_time must be positive
    with pytest.raises(ValueError):
        shot_noise_sensitivity_m_s2_per_sqrt_hz(1.6e7, 0.26, 100, 1.0, 0.0)
    with pytest.raises(ValueError):
        shot_noise_sensitivity_m_s2_per_sqrt_hz(1.6e7, 0.26, 100, 1.0, -1.0)


def test_gravity_gradient_positive():
    from qgrav.physics.systematics import gravity_gradient_shift_m_s2
    shift = gravity_gradient_shift_m_s2()
    assert shift > 0.0
    # With larger drop height, shift should increase
    shift2 = gravity_gradient_shift_m_s2(drop_height_m=1.0)
    assert shift2 > shift


def test_gravity_gradient_rejects_negative_time():
    from qgrav.physics.systematics import gravity_gradient_shift_m_s2
    import pytest
    with pytest.raises(ValueError, match="non-negative"):
        gravity_gradient_shift_m_s2(interferometer_time_s=-0.1)


def test_coriolis_zero_at_pole():
    from qgrav.physics.systematics import coriolis_shift_m_s2
    shift = coriolis_shift_m_s2(latitude_deg=90.0, horizontal_velocity_m_s=1e-3)
    assert shift < 1e-15  # cos(90°) ≈ 0


def test_coriolis_always_non_negative():
    from qgrav.physics.systematics import coriolis_shift_m_s2
    # Even for out-of-range latitude, result must be >= 0
    for lat in (-100.0, -90.0, 0.0, 45.0, 90.0, 91.0, 180.0):
        shift = coriolis_shift_m_s2(latitude_deg=lat, horizontal_velocity_m_s=1e-3)
        assert shift >= 0.0, f"Negative Coriolis shift at lat={lat}: {shift}"


def test_systematics_summary_keys():
    from qgrav.physics.systematics import systematics_summary
    result = systematics_summary()
    assert "gravity_gradient" in result
    assert "coriolis" in result
    assert "total_systematic_m_s2" in result
    assert "total_systematic_ugal" in result
    assert result["gravity_gradient"]["value_m_s2"] > 0
    assert result["coriolis"]["value_m_s2"] > 0
    assert result["total_systematic_ugal"] == result["total_systematic_m_s2"] * 1e8
