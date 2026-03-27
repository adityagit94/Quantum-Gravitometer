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
