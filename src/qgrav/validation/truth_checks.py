from __future__ import annotations

from typing import Any

import numpy as np

from qgrav.physics.ground_truth import expected_gravity_phase_rad, expected_vibration_phase_rad
from qgrav.validation.benchmarks import build_check, finalize_checks, linear_fit_r2


def _as_array(result: dict[str, Any], key: str) -> np.ndarray:
    return np.asarray(result[key], dtype=np.float64)


def evaluate_simulation_truth(result: dict[str, Any]) -> dict[str, Any]:
    model = str(result.get('model', '')).strip().lower()
    if model == 'rabi_scan':
        return _check_rabi_scan(result)
    if model == 'mach_zehnder_phase_scan':
        return _check_phase_scan(result)
    if model == 'gravity_sweep':
        return _check_gravity_sweep(result)
    if model == 'vibration_sensitivity_sweep':
        return _check_vibration_sweep(result)
    return finalize_checks([
        build_check('known_model', False, observed=model, note='No truth-check handler is registered for this model.')
    ])


def _check_rabi_scan(result: dict[str, Any]) -> dict[str, Any]:
    taus = _as_array(result, 'taus_s')
    occ = _as_array(result, 'excited_fraction')
    checks = [
        build_check('finite_excited_fraction', bool(np.all(np.isfinite(occ)))),
        build_check(
            'occupation_bounded',
            bool(np.all((occ >= -1e-12) & (occ <= 1.0 + 1e-12))),
            observed=[float(np.min(occ)), float(np.max(occ))],
            expected='values within [0, 1]',
        ),
        build_check('monotonic_tau_axis', bool(np.all(np.diff(taus) > 0))),
        build_check(
            'nontrivial_response_span',
            bool(float(np.ptp(occ)) > 1e-4),
            observed=float(np.ptp(occ)),
            expected='> 1e-4',
        ),
    ]
    return finalize_checks(checks)


def _check_phase_scan(result: dict[str, Any]) -> dict[str, Any]:
    phase = _as_array(result, 'phase_scan_rad')
    port3 = _as_array(result, 'output_port_3')
    port2 = _as_array(result, 'output_port_2')
    fit = _as_array(result, 'fit_port_3')
    residual_rms = float(np.sqrt(np.mean((port3 - fit) ** 2)))
    checks = [
        build_check('phase_axis_monotonic', bool(np.all(np.diff(phase) > 0))),
        build_check(
            'port2_bounded',
            bool(np.all((port2 >= -1e-9) & (port2 <= 1.0 + 1e-9))),
            observed=[float(np.min(port2)), float(np.max(port2))],
        ),
        build_check(
            'port3_bounded',
            bool(np.all((port3 >= -1e-9) & (port3 <= 1.0 + 1e-9))),
            observed=[float(np.min(port3)), float(np.max(port3))],
        ),
        build_check(
            'fringe_fit_r2_reasonable',
            bool(float(result.get('fringe_fit_r2', float('nan'))) >= 0.90),
            observed=float(result.get('fringe_fit_r2', float('nan'))),
            expected='>= 0.90',
        ),
        build_check(
            'fit_residual_small',
            bool(residual_rms <= 0.15),
            observed=residual_rms,
            expected='<= 0.15 population units',
        ),
    ]
    return finalize_checks(checks)


def _check_gravity_sweep(result: dict[str, Any]) -> dict[str, Any]:
    g = _as_array(result, 'gravity_values_m_s2')
    total_phase = _as_array(result, 'total_phase_rad')
    expected = expected_gravity_phase_rad(
        g,
        k_eff_rad_per_m=float(result['k_eff_rad_per_m']),
        interferometer_time_s=float(result['interferometer_time_s']),
        phase_bias_rad=float(result['phase_bias_rad']),
    )
    max_abs = float(np.max(np.abs(total_phase - expected)))
    r2 = linear_fit_r2(g, total_phase)
    checks = [
        build_check('gravity_axis_monotonic', bool(np.all(np.diff(g) > 0))),
        build_check('analytic_phase_match', bool(max_abs <= 1e-10), observed=max_abs, expected='<= 1e-10 rad'),
        build_check('phase_linearity', bool(r2 >= 0.999999), observed=r2, expected='>= 0.999999'),
        build_check('finite_normalized_signal', bool(np.all(np.isfinite(_as_array(result, 'normalized_differential_signal'))))),
    ]
    return finalize_checks(checks)


def _check_vibration_sweep(result: dict[str, Any]) -> dict[str, Any]:
    amps = _as_array(result, 'vibration_amplitude_m')
    vib_phase = _as_array(result, 'vibration_phase_rad')
    expected = expected_vibration_phase_rad(
        amps,
        frequency_hz=float(result['vibration_frequency_hz']),
        interferometer_time_s=float(result['interferometer_time_s']),
        k_eff_rad_per_m=float(result['k_eff_rad_per_m']),
        phase0_rad=float(result['vibration_phase0_rad']),
    )
    max_abs = float(np.max(np.abs(vib_phase - expected)))
    r2 = linear_fit_r2(amps, vib_phase)
    if abs(float(amps[0])) <= 1e-18:
        zero_amp_check = build_check(
            'zero_amplitude_zero_phase',
            bool(abs(float(vib_phase[0])) <= 1e-15),
            observed=float(vib_phase[0]),
            expected='0 rad at zero amplitude',
        )
    else:
        zero_amp_check = build_check(
            'zero_amplitude_zero_phase',
            True,
            note='First amplitude is not zero; zero-phase check skipped.',
        )
    checks = [
        build_check('amplitude_axis_monotonic', bool(np.all(np.diff(amps) >= 0))),
        zero_amp_check,
        build_check('analytic_vibration_phase_match', bool(max_abs <= 1e-10), observed=max_abs, expected='<= 1e-10 rad'),
        build_check('vibration_phase_linear_in_amplitude', bool(r2 >= 0.999999), observed=r2, expected='>= 0.999999'),
    ]
    return finalize_checks(checks)
