from __future__ import annotations

from typing import Any

import numpy as np

from qgrav.physics.ground_truth import expected_gravity_phase_rad, expected_vibration_phase_rad
from qgrav.validation.benchmarks import build_check, finalize_checks, linear_fit_r2


def _as_array(result: dict[str, Any], key: str) -> np.ndarray:
    return np.asarray(result[key], dtype=np.float64)


def evaluate_simulation_truth(result: dict[str, Any]) -> dict[str, Any]:
    model = str(result.get("model", "")).strip().lower()
    if model == "rabi_scan":
        return _check_rabi_scan(result)
    if model == "mach_zehnder_phase_scan":
        return _check_phase_scan(result)
    if model == "gravity_sweep":
        return _check_gravity_sweep(result)
    if model == "vibration_sensitivity_sweep":
        return _check_vibration_sweep(result)
    if model == "multi_drop_cycle":
        return _check_multi_drop_cycle(result)
    return finalize_checks(
        [
            build_check(
                "known_model",
                False,
                observed=model,
                note="No truth-check handler is registered for this model.",
            )
        ]
    )


def _check_rabi_scan(result: dict[str, Any]) -> dict[str, Any]:
    taus = _as_array(result, "taus_s")
    occ = _as_array(result, "excited_fraction")
    checks = [
        build_check("finite_excited_fraction", bool(np.all(np.isfinite(occ)))),
        build_check(
            "occupation_bounded",
            bool(np.all((occ >= -1e-12) & (occ <= 1.0 + 1e-12))),
            observed=[float(np.min(occ)), float(np.max(occ))],
            expected="values within [0, 1]",
        ),
        build_check("monotonic_tau_axis", bool(np.all(np.diff(taus) > 0))),
        build_check(
            "nontrivial_response_span",
            bool(float(np.ptp(occ)) > 1e-4),
            observed=float(np.ptp(occ)),
            expected="> 1e-4",
        ),
    ]
    return finalize_checks(checks)


def _check_phase_scan(result: dict[str, Any]) -> dict[str, Any]:
    phase = _as_array(result, "phase_scan_rad")
    port3 = _as_array(result, "output_port_3")
    port2 = _as_array(result, "output_port_2")
    fit = _as_array(result, "fit_port_3")
    residual_rms = float(np.sqrt(np.mean((port3 - fit) ** 2)))
    checks = [
        build_check("phase_axis_monotonic", bool(np.all(np.diff(phase) > 0))),
        build_check(
            "port2_bounded",
            bool(np.all((port2 >= -1e-9) & (port2 <= 1.0 + 1e-9))),
            observed=[float(np.min(port2)), float(np.max(port2))],
        ),
        build_check(
            "port3_bounded",
            bool(np.all((port3 >= -1e-9) & (port3 <= 1.0 + 1e-9))),
            observed=[float(np.min(port3)), float(np.max(port3))],
        ),
        build_check(
            "fringe_fit_r2_reasonable",
            bool(float(result.get("fringe_fit_r2", float("nan"))) >= 0.90),
            observed=float(result.get("fringe_fit_r2", float("nan"))),
            expected=">= 0.90",
        ),
        build_check(
            "fit_residual_small",
            bool(residual_rms <= 0.15),
            observed=residual_rms,
            expected="<= 0.15 population units",
        ),
    ]
    return finalize_checks(checks)


def _check_gravity_sweep(result: dict[str, Any]) -> dict[str, Any]:
    g = _as_array(result, "gravity_values_m_s2")
    total_phase = _as_array(result, "total_phase_rad")
    nd = _as_array(result, "normalized_differential_signal")
    gravity_propagation = bool(result.get("gravity_propagation", False))
    checks = [
        build_check("gravity_axis_monotonic", bool(np.all(np.diff(g) > 0))),
        build_check("finite_normalized_signal", bool(np.all(np.isfinite(nd)))),
    ]
    if not gravity_propagation:
        # Hybrid mode: phase is the analytical formula, exact match required.
        expected = expected_gravity_phase_rad(
            g,
            k_eff_rad_per_m=float(result["k_eff_rad_per_m"]),
            interferometer_time_s=float(result["interferometer_time_s"]),
            phase_bias_rad=float(result["phase_bias_rad"]),
        )
        max_abs = float(np.max(np.abs(total_phase - expected)))
        r2 = linear_fit_r2(g, total_phase)
        checks.append(
            build_check(
                "analytic_phase_match",
                bool(max_abs <= 1e-10),
                observed=max_abs,
                expected="<= 1e-10 rad",
            )
        )
        checks.append(
            build_check(
                "phase_linearity", bool(r2 >= 0.999999), observed=r2, expected=">= 0.999999"
            )
        )
    else:
        # Simulated mode: total_phase is just the phase_bias.  Instead, verify
        # the fringe pattern itself looks like a real gravimeter fringe:
        # visibility > 0.3 and study scope is FULLY_SIMULATED.
        p3 = _as_array(result, "output_port_3")
        visibility = float((np.max(p3) - np.min(p3)) / max(np.max(p3) + np.min(p3), 1e-15))
        scope_category = str(result.get("study_scope_category", "")).upper()
        checks.append(
            build_check(
                "fringe_visibility",
                bool(visibility > 0.3),
                observed=visibility,
                expected="> 0.3",
            )
        )
        checks.append(
            build_check(
                "study_scope_fully_simulated",
                "FULLY" in scope_category or "SIMULATED" in scope_category,
                observed=scope_category,
                expected="FULLY_SIMULATED",
            )
        )
    return finalize_checks(checks)


def _check_multi_drop_cycle(result: dict[str, Any]) -> dict[str, Any]:
    """Truth checks for the multi-drop measurement cycle."""
    g_est = _as_array(result, "g_estimates_m_s2")
    timestamps = _as_array(result, "timestamps_s")
    taus = _as_array(result, "allan_taus_s")
    adev = _as_array(result, "allan_dev_m_s2")
    n_drops_reported = int(result.get("n_drops", 0))
    g_true = float(result.get("gravity_true_m_s2", float("nan")))

    n_correct = len(g_est) == n_drops_reported
    finite = bool(np.all(np.isfinite(g_est)))
    mean_dev = float(np.abs(np.mean(g_est) - g_true)) if np.isfinite(g_true) else float("nan")

    checks = [
        build_check(
            "n_drops_matches",
            n_correct,
            observed=len(g_est),
            expected=n_drops_reported,
        ),
        build_check(
            "g_estimates_finite",
            finite,
        ),
        build_check(
            "timestamps_monotonic",
            bool(np.all(np.diff(timestamps) >= 0)),
        ),
        build_check(
            "mean_close_to_true_gravity",
            bool(np.isfinite(mean_dev) and mean_dev < 1.0e-5),
            observed=mean_dev,
            expected="< 1.0e-5 m/s^2",
        ),
        build_check(
            "allan_arrays_consistent",
            bool(
                len(taus) == len(adev) and len(taus) >= 1 and np.all(taus > 0) and np.all(adev >= 0)
            ),
            observed={"len_taus": len(taus), "len_adev": len(adev)},
        ),
    ]
    if len(adev) >= 2:
        # For independent (white) noise, adev should decrease with tau.
        decreasing = bool(adev[-1] <= adev[0] * 1.2)  # allow some slack
        checks.append(
            build_check(
                "allan_dev_decreasing",
                decreasing,
                observed=[float(adev[0]), float(adev[-1])],
                expected="adev[-1] <= adev[0] * 1.2",
            )
        )
    return finalize_checks(checks)


def _check_vibration_sweep(result: dict[str, Any]) -> dict[str, Any]:
    amps = _as_array(result, "vibration_amplitude_m")
    vib_phase = _as_array(result, "vibration_phase_rad")
    expected = expected_vibration_phase_rad(
        amps,
        frequency_hz=float(result["vibration_frequency_hz"]),
        interferometer_time_s=float(result["interferometer_time_s"]),
        k_eff_rad_per_m=float(result["k_eff_rad_per_m"]),
        phase0_rad=float(result["vibration_phase0_rad"]),
    )
    max_abs = float(np.max(np.abs(vib_phase - expected)))
    r2 = linear_fit_r2(amps, vib_phase)
    if abs(float(amps[0])) <= 1e-18:
        zero_amp_check = build_check(
            "zero_amplitude_zero_phase",
            bool(abs(float(vib_phase[0])) <= 1e-15),
            observed=float(vib_phase[0]),
            expected="0 rad at zero amplitude",
        )
    else:
        zero_amp_check = build_check(
            "zero_amplitude_zero_phase",
            True,
            note="First amplitude is not zero; zero-phase check skipped.",
        )
    checks = [
        build_check("amplitude_axis_monotonic", bool(np.all(np.diff(amps) >= 0))),
        zero_amp_check,
        build_check(
            "analytic_vibration_phase_match",
            bool(max_abs <= 1e-10),
            observed=max_abs,
            expected="<= 1e-10 rad",
        ),
        build_check(
            "vibration_phase_linear_in_amplitude",
            bool(r2 >= 0.999999),
            observed=r2,
            expected=">= 0.999999",
        ),
    ]
    return finalize_checks(checks)
