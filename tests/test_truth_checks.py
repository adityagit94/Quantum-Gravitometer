from qgrav.sim_ai import (
    run_aisim_gravity_sweep,
    run_aisim_mach_zehnder_phase_scan,
    run_aisim_rabi_scan,
    run_aisim_vibration_sensitivity_sweep,
)


def test_rabi_truth_checks_pass():
    result = run_aisim_rabi_scan(n_atoms=120, n_steps=10, tau_step_s=1e-6, seed=10)
    assert result['truth_checks']['all_passed'] is True


def test_phase_scan_truth_checks_pass():
    result = run_aisim_mach_zehnder_phase_scan(n_atoms=120, n_phase_points=13, seed=11)
    assert result['truth_checks']['all_passed'] is True


def test_gravity_sweep_truth_checks_pass():
    result = run_aisim_gravity_sweep(n_atoms=120, n_gravity_points=11, gravity_span_m_s2=2e-6, seed=12)
    assert result['truth_checks']['all_passed'] is True


def test_vibration_sweep_truth_checks_pass():
    result = run_aisim_vibration_sensitivity_sweep(
        n_atoms=120,
        n_amplitude_points=9,
        amplitude_min_m=0.0,
        amplitude_max_m=1e-8,
        seed=13,
    )
    assert result['truth_checks']['all_passed'] is True
