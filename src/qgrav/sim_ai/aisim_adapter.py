from __future__ import annotations

from functools import partial
import logging
from typing import Any

import numpy as np

from qgrav.physics import (
    AtomSourceConfig,
    MachZehnderPulseSequence,
    RabiPulseScan,
    equivalent_gravity_error_m_s2,
    gravity_phase_rad,
    gravity_sweep_axis,
    normalized_differential_signal,
    phase_scan_axis,
    port_differential_summary,
    source_summary_rows,
    vibration_amplitude_axis,
    vibration_phase_rad,
)
from qgrav.physics.constants import NOMINAL_GRAVITY, WAVELENGTH_RB87_D2
from qgrav.validation.truth_checks import evaluate_simulation_truth

logger = logging.getLogger(__name__)


def is_aisim_available() -> bool:
    try:
        _import_aisim()
        return True
    except Exception:
        logger.exception("AISim availability check failed")
        return False


def _import_aisim():
    try:
        from qgrav.vendor import aisim as ais  # type: ignore
        return ais
    except Exception:
        logger.exception("Vendored AISim import failed; trying external package")
        try:
            import aisim as ais  # type: ignore
            return ais
        except Exception as exc:
            raise RuntimeError(
                "AISim is unavailable. Ensure the vendored package is present under qgrav.vendor.aisim or install a compatible external `aisim` package."
            ) from exc


def _create_detected_ensemble(
    *,
    n_atoms: int,
    seed: int,
    cloud_radius_m: float,
    temp_xy_K: float,
    temp_z_K: float,
    detector_time_s: float,
    detector_radius_m: float,
    multiport: bool,
):
    ais = _import_aisim()
    state_kets = [0, 0, 0, 0, 0, 1] if multiport else [1, 0]
    atoms = ais.create_random_ensemble(
        int(n_atoms),
        x_dist=partial(ais.dist.position_dist_gaussian, std=float(cloud_radius_m)),
        y_dist=partial(ais.dist.position_dist_gaussian, std=float(cloud_radius_m)),
        z_dist=partial(ais.dist.position_dist_gaussian, std=float(cloud_radius_m)),
        vx_dist=partial(ais.dist.velocity_dist_from_temp, temperature=float(temp_xy_K)),
        vy_dist=partial(ais.dist.velocity_dist_from_temp, temperature=float(temp_xy_K)),
        vz_dist=partial(ais.dist.velocity_dist_from_temp, temperature=float(temp_z_K)),
        state_kets=state_kets,
        seed=int(seed),
    )
    detector = ais.SphericalDetector(t_det=float(detector_time_s), r_det=float(detector_radius_m))
    detected_atoms = detector.detected_atoms(atoms)
    detected_count = int(len(detected_atoms))
    if detected_count == 0:
        raise RuntimeError(
            "AISim detector selected zero atoms. Increase detector radius or change cloud settings."
        )
    source_cfg = AtomSourceConfig(
        n_atoms_total=int(n_atoms),
        seed=int(seed),
        cloud_radius_m=float(cloud_radius_m),
        temp_xy_K=float(temp_xy_K),
        temp_z_K=float(temp_z_K),
        detector_time_s=float(detector_time_s),
        detector_radius_m=float(detector_radius_m),
        multiport=bool(multiport),
    )
    return ais, detected_atoms, detector, detected_count, source_cfg


def _wave_vectors(*, wavelength_m: float, k1_rad_per_m: float | None = None, k2_rad_per_m: float | None = None):
    ais = _import_aisim()
    k1 = float(k1_rad_per_m) if k1_rad_per_m is not None else 2.0 * np.pi / float(wavelength_m)
    k2 = float(k2_rad_per_m) if k2_rad_per_m is not None else -2.0 * np.pi / float(wavelength_m)
    return ais.Wavevectors(k1=k1, k2=k2)


def _gaussian_beam(*, beam_radius_m: float, center_rabi_freq_hz: float):
    ais = _import_aisim()
    return ais.IntensityProfile(
        r_profile=float(beam_radius_m),
        center_rabi_freq=2.0 * np.pi * float(center_rabi_freq_hz),
    )


def _run_mach_zehnder_sequence(
    atoms0,
    *,
    tau_pi_half_s: float,
    interferometer_time_s: float,
    intensity_profile,
    wave_vectors,
    final_phase_rad: float,
) -> dict[str, float]:
    """Run a three-pulse AISim Mach–Zehnder-style sequence.

    This follows the structure demonstrated in AISim's multiport atom-interferometer
    example using SpatialSuperpositionTransitionPropagator objects for the three pulses.
    The final beam splitter includes an effective phase_scan term, which we use to study
    fringes and gravimeter-relevant phase response.
    """
    ais = _import_aisim()
    bs1 = ais.SpatialSuperpositionTransitionPropagator(
        float(tau_pi_half_s),
        n_pulse=1,
        n_pulses=3,
        intensity_profile=intensity_profile,
        wave_vectors=wave_vectors,
    )
    mirror = ais.SpatialSuperpositionTransitionPropagator(
        2.0 * float(tau_pi_half_s),
        n_pulse=2,
        n_pulses=3,
        intensity_profile=intensity_profile,
        wave_vectors=wave_vectors,
    )
    bs2 = ais.SpatialSuperpositionTransitionPropagator(
        float(tau_pi_half_s),
        n_pulse=3,
        n_pulses=3,
        intensity_profile=intensity_profile,
        wave_vectors=wave_vectors,
        phase_scan=float(final_phase_rad),
    )
    free_prop = ais.FreePropagator(float(interferometer_time_s))

    atoms = bs1.propagate(atoms0)
    atoms = free_prop.propagate(atoms)
    atoms = mirror.propagate(atoms)
    atoms = free_prop.propagate(atoms)
    atoms = bs2.propagate(atoms)

    port2 = float(np.mean(atoms.state_occupation(2)))
    port3 = float(np.mean(atoms.state_occupation(3)))
    summary = port_differential_summary(np.array([port2], dtype=np.float64), np.array([port3], dtype=np.float64))
    return {
        "port_2": port2,
        "port_3": port3,
        "closed_total": float(summary["closed_total"][0]),
        "differential_signal": float(summary["differential_signal"][0]),
        "normalized_differential_signal": float(summary["normalized_differential_signal"][0]),
    }


def _fit_sinusoid(x_rad: np.ndarray, y: np.ndarray) -> dict[str, float]:
    x = np.asarray(x_rad, dtype=np.float64)
    y = np.asarray(y, dtype=np.float64)
    A = np.column_stack([np.ones_like(x), np.cos(x), np.sin(x)])
    coeffs, _, _, _ = np.linalg.lstsq(A, y, rcond=None)
    offset, c_cos, c_sin = coeffs
    amplitude = float(np.sqrt(c_cos**2 + c_sin**2))
    phase_offset = float(np.arctan2(-c_sin, c_cos))
    fitted = A @ coeffs
    ss_res = float(np.sum((y - fitted) ** 2))
    ss_tot = float(np.sum((y - np.mean(y)) ** 2))
    r2 = 1.0 - ss_res / ss_tot if ss_tot > 0 else float("nan")
    visibility = float(amplitude / max(abs(float(offset)), 1e-15))
    return {
        "offset": float(offset),
        "amplitude": amplitude,
        "phase_offset_rad": phase_offset,
        "visibility": visibility,
        "r2": r2,
    }


def _hybrid_gravity_phase_rad(*, g_m_s2: np.ndarray, k_eff_rad_per_m: float, T_s: float, phase_bias_rad: float) -> np.ndarray:
    return gravity_phase_rad(g_m_s2, k_eff_rad_per_m=k_eff_rad_per_m, interferometer_time_s=T_s, phase_bias_rad=phase_bias_rad)


def _vibration_phase_sinusoid(
    *,
    amplitudes_m: np.ndarray,
    frequency_hz: float,
    interferometer_time_s: float,
    k_eff_rad_per_m: float,
    phase0_rad: float,
) -> np.ndarray:
    return vibration_phase_rad(
        amplitudes_m,
        frequency_hz=frequency_hz,
        interferometer_time_s=interferometer_time_s,
        k_eff_rad_per_m=k_eff_rad_per_m,
        phase0_rad=phase0_rad,
    )


# Canonical study-scope enum (per PRD v1.0 Workstream 10).
STUDY_SCOPE_FULLY_SIMULATED = "FULLY_SIMULATED"
STUDY_SCOPE_HYBRID = "HYBRID_AISIM_PLUS_ANALYTICAL"
STUDY_SCOPE_ANALYTICAL_ONLY = "ANALYTICAL_ONLY"
_ALLOWED_STUDY_SCOPE_CATEGORIES = {
    STUDY_SCOPE_FULLY_SIMULATED,
    STUDY_SCOPE_HYBRID,
    STUDY_SCOPE_ANALYTICAL_ONLY,
}


def _classify_study_scope(study_scope: str) -> tuple[str, str]:
    """Map the free-text study_scope string to (category, description)."""
    s = study_scope.lower()
    if "hybrid" in s or "plus_closed_form" in s or "plus_reference_mirror" in s:
        category = STUDY_SCOPE_HYBRID
        description = (
            "Hybrid: AISim provides the microscopic atom-optics simulation "
            "(contrast and ensemble inhomogeneity); the inertial-phase term "
            "is imposed via a closed-form analytical formula. Truth checks "
            "verify the code matches the formula, not that the formula "
            "matches hardware."
        )
    elif "analytical_only" in s or "closed_form_only" in s:
        category = STUDY_SCOPE_ANALYTICAL_ONLY
        description = (
            "Analytical only: the quantity is the direct evaluation of a "
            "published formula with no microscopic simulation involved."
        )
    else:
        category = STUDY_SCOPE_FULLY_SIMULATED
        description = (
            "Fully simulated: quantities are computed from the AISim "
            "microscopic atom-optics propagator with no closed-form "
            "inertial-phase formula imposed."
        )
    return category, description


def _pack_result(
    result: dict[str, Any],
    *,
    source_cfg: AtomSourceConfig,
    detected_count: int,
    pulse_sequence: dict[str, Any],
    physical_model: dict[str, Any],
    study_scope: str,
    limitations: list[str],
) -> dict[str, Any]:
    result["source_model"] = source_cfg.as_dict()
    result["pulse_sequence"] = pulse_sequence
    result["physical_model"] = physical_model
    result["study_scope"] = study_scope
    category, description = _classify_study_scope(study_scope)
    result["study_scope_category"] = category
    result["study_scope_description"] = description
    result["limitations"] = limitations
    truth = evaluate_simulation_truth(result)
    result["truth_checks"] = truth
    summary_rows = result.setdefault("summary_rows", {})
    if isinstance(summary_rows, dict):
        summary_rows.update(source_summary_rows(source_cfg, detected_count))
        summary_rows["Truth checks passed"] = f"{truth['passed_count']}/{truth['total_count']}"
        summary_rows["All truth checks passed"] = bool(truth['all_passed'])
        summary_rows["Study scope"] = study_scope
        summary_rows["Study scope category"] = category
    return result


def run_aisim_rabi_scan(
    *,
    n_atoms: int = 1000,
    seed: int = 1,
    cloud_radius_m: float = 3.0e-3,
    temp_xy_K: float = 3.0e-6,
    temp_z_K: float = 150e-9,
    detector_time_s: float = 800e-3,
    detector_radius_m: float = 5e-3,
    pre_pulse_delay_s: float = 100e-3,
    beam_radius_m: float = 15e-3,
    center_rabi_freq_hz: float = 15e3,
    wavelength_m: float = WAVELENGTH_RB87_D2.value,
    tau_step_s: float = 1e-6,
    n_steps: int = 60,
    k1_rad_per_m: float | None = None,
    k2_rad_per_m: float | None = None,
) -> dict[str, Any]:
    if n_atoms <= 0:
        raise ValueError("n_atoms must be positive.")
    if n_steps <= 0:
        raise ValueError("n_steps must be positive.")
    if tau_step_s <= 0:
        raise ValueError("tau_step_s must be positive.")

    ais, detected_atoms, _, detected_count, source_cfg = _create_detected_ensemble(
        n_atoms=n_atoms,
        seed=seed,
        cloud_radius_m=cloud_radius_m,
        temp_xy_K=temp_xy_K,
        temp_z_K=temp_z_K,
        detector_time_s=detector_time_s,
        detector_radius_m=detector_radius_m,
        multiport=False,
    )

    atoms_ready = ais.FreePropagator(float(pre_pulse_delay_s)).propagate(detected_atoms)
    intensity_profile = _gaussian_beam(beam_radius_m=beam_radius_m, center_rabi_freq_hz=center_rabi_freq_hz)
    wave_vectors = _wave_vectors(wavelength_m=wavelength_m, k1_rad_per_m=k1_rad_per_m, k2_rad_per_m=k2_rad_per_m)
    propagator = ais.TwoLevelTransitionPropagator(
        float(tau_step_s), intensity_profile=intensity_profile, wave_vectors=wave_vectors
    )

    pulse_scan = RabiPulseScan(tau_step_s=float(tau_step_s), n_steps=int(n_steps))
    taus_s = pulse_scan.tau_axis()
    excited_fraction = np.zeros_like(taus_s)
    current_atoms = atoms_ready
    for idx in range(1, len(taus_s)):
        current_atoms = propagator.propagate(current_atoms)
        excited_fraction[idx] = float(np.mean(current_atoms.state_occupation(state=1)))

    peak_idx = int(np.argmax(excited_fraction))
    area = float(np.trapezoid(excited_fraction, taus_s))
    result = {
        "backend": "aisim",
        "model": "rabi_scan",
        "n_atoms_total": int(n_atoms),
        "n_atoms_detected": detected_count,
        "detected_fraction": float(detected_count / float(n_atoms)),
        "taus_s": taus_s,
        "excited_fraction": excited_fraction,
        "peak_excited_fraction": float(excited_fraction[peak_idx]),
        "peak_tau_s": float(taus_s[peak_idx]),
        "mean_excited_fraction": float(np.mean(excited_fraction)),
        "integrated_excited_fraction_s": area,
        "summary_rows": {
            "Backend": "aisim",
            "Model": "rabi_scan",
            "Total atoms": int(n_atoms),
            "Detected atoms": detected_count,
            "Detected fraction": float(detected_count / float(n_atoms)),
            "Peak excited fraction": float(excited_fraction[peak_idx]),
            "Peak pulse duration (s)": float(taus_s[peak_idx]),
            "Mean excited fraction": float(np.mean(excited_fraction)),
        },
        "plot_specs": [
            {
                "name": "simulation_primary",
                "title": "AISim Rabi scan",
                "x_key": "taus_s",
                "x_scale": 1e6,
                "x_label": "pulse duration (µs)",
                "y_label": "mean excited fraction",
                "series": [
                    {"key": "excited_fraction", "label": "excited fraction", "kind": "line_markers"}
                ],
            }
        ],
        "config": {
            "seed": int(seed),
            "cloud_radius_m": float(cloud_radius_m),
            "temp_xy_K": float(temp_xy_K),
            "temp_z_K": float(temp_z_K),
            "detector_time_s": float(detector_time_s),
            "detector_radius_m": float(detector_radius_m),
            "pre_pulse_delay_s": float(pre_pulse_delay_s),
            "beam_radius_m": float(beam_radius_m),
            "center_rabi_freq_hz": float(center_rabi_freq_hz),
            "wavelength_m": float(wavelength_m),
            "tau_step_s": float(tau_step_s),
            "n_steps": int(n_steps),
        },
    }
    return _pack_result(
        result,
        source_cfg=source_cfg,
        detected_count=detected_count,
        pulse_sequence={"model": "rabi_scan", **pulse_scan.as_dict()},
        physical_model={
            "atom_source": "AISim random ensemble + spherical detector",
            "pulse_sequence": "AISim TwoLevelTransitionPropagator repeatedly applied",
            "phase_accumulation": "pulse-area driven population transfer (no gravimeter phase model)",
            "noise": "none beyond ensemble inhomogeneity from AISim source and beam profile",
            "estimator": "mean excited-state occupation",
            "readout": "state-occupation average over detected atoms",
        },
        study_scope="full_aisim_two_level_population_scan",
        limitations=[
            "This study probes two-level pulse response, not a full gravimeter interferometer.",
            "No explicit inertial phase, vibration, or systematic-shift model is included.",
        ],
    )


def run_aisim_mach_zehnder_phase_scan(
    *,
    n_atoms: int = 1000,
    seed: int = 1,
    cloud_radius_m: float = 3.0e-3,
    temp_xy_K: float = 2.5e-6,
    temp_z_K: float = 100e-9,
    detector_time_s: float = 778e-3,
    detector_radius_m: float = 5e-3,
    beam_radius_m: float = 29.5e-3 / 2.0,
    center_rabi_freq_hz: float = 12.5e3,
    wavelength_m: float = WAVELENGTH_RB87_D2.value,
    tau_pi_half_s: float = 23e-6,
    interferometer_time_s: float = 260e-3,
    phase_min_rad: float = 0.0,
    phase_max_rad: float = 2.0 * np.pi,
    n_phase_points: int = 81,
    k1_rad_per_m: float | None = None,
    k2_rad_per_m: float | None = None,
) -> dict[str, Any]:
    if n_phase_points < 5:
        raise ValueError("n_phase_points must be at least 5.")
    ais, detected_atoms, _, detected_count, source_cfg = _create_detected_ensemble(
        n_atoms=n_atoms,
        seed=seed,
        cloud_radius_m=cloud_radius_m,
        temp_xy_K=temp_xy_K,
        temp_z_K=temp_z_K,
        detector_time_s=detector_time_s,
        detector_radius_m=detector_radius_m,
        multiport=True,
    )
    intensity_profile = _gaussian_beam(beam_radius_m=beam_radius_m, center_rabi_freq_hz=center_rabi_freq_hz)
    wave_vectors = _wave_vectors(wavelength_m=wavelength_m, k1_rad_per_m=k1_rad_per_m, k2_rad_per_m=k2_rad_per_m)
    k_eff = float(wave_vectors.k1 - wave_vectors.k2)

    sequence = MachZehnderPulseSequence(
        tau_pi_half_s=float(tau_pi_half_s),
        interferometer_time_s=float(interferometer_time_s),
    )
    phases = phase_scan_axis(float(phase_min_rad), float(phase_max_rad), int(n_phase_points))
    port2 = np.zeros_like(phases)
    port3 = np.zeros_like(phases)
    diff = np.zeros_like(phases)
    norm_diff = np.zeros_like(phases)
    for i, phase in enumerate(phases):
        out = _run_mach_zehnder_sequence(
            detected_atoms,
            tau_pi_half_s=tau_pi_half_s,
            interferometer_time_s=interferometer_time_s,
            intensity_profile=intensity_profile,
            wave_vectors=wave_vectors,
            final_phase_rad=float(phase),
        )
        port2[i] = out["port_2"]
        port3[i] = out["port_3"]
        diff[i] = out["differential_signal"]
        norm_diff[i] = out["normalized_differential_signal"]

    fit = _fit_sinusoid(phases, port3)
    fit_curve = fit["offset"] + fit["amplitude"] * np.cos(phases + fit["phase_offset_rad"])
    peak_idx = int(np.argmax(port3))

    from qgrav.physics.phase_models import shot_noise_sensitivity_m_s2_per_sqrt_hz
    _visibility = float(fit.get("visibility", 1.0))
    _contrast = max(min(_visibility, 1.0), 0.01)
    _sens = shot_noise_sensitivity_m_s2_per_sqrt_hz(
        k_eff_rad_per_m=k_eff,
        interferometer_time_s=float(interferometer_time_s),
        n_atoms=max(detected_count, 1),
        contrast=_contrast,
        cycle_time_s=1.0,
    )

    result = {
        "backend": "aisim",
        "model": "mach_zehnder_phase_scan",
        "study_type": "full_aisim_three_pulse_sequence",
        "n_atoms_total": int(n_atoms),
        "n_atoms_detected": detected_count,
        "detected_fraction": float(detected_count / float(n_atoms)),
        "k_eff_rad_per_m": k_eff,
        "interferometer_time_s": float(interferometer_time_s),
        "tau_pi_half_s": float(tau_pi_half_s),
        "phase_scan_rad": phases,
        "output_port_2": port2,
        "output_port_3": port3,
        "differential_signal": diff,
        "normalized_differential_signal": norm_diff,
        "fit_port_3": fit_curve,
        "peak_port_3": float(port3[peak_idx]),
        "peak_phase_rad": float(phases[peak_idx]),
        "fringe_visibility_port_3": float(fit["visibility"]),
        "fringe_fit_r2": float(fit["r2"]),
        "fit_phase_offset_rad": float(fit["phase_offset_rad"]),
        "shot_noise_sensitivity_m_s2_per_sqrt_hz": _sens,
        "shot_noise_sensitivity_ugal_per_sqrt_hz": _sens * 1e8,
        "summary_rows": {
            "Backend": "aisim",
            "Model": "mach_zehnder_phase_scan",
            "Study type": "full_aisim_three_pulse_sequence",
            "Total atoms": int(n_atoms),
            "Detected atoms": detected_count,
            "Detected fraction": float(detected_count / float(n_atoms)),
            "k_eff (rad/m)": k_eff,
            "Interferometer time T (s)": float(interferometer_time_s),
            "π/2 pulse duration (s)": float(tau_pi_half_s),
            "Fringe visibility (port 3)": float(fit["visibility"]),
            "Fringe fit R²": float(fit["r2"]),
            "Peak phase (rad)": float(phases[peak_idx]),
            "Sensitivity (m/s²/√Hz)": _sens,
            "Sensitivity (µGal/√Hz)": _sens * 1e8,
        },
        "plot_specs": [
            {
                "name": "simulation_primary",
                "title": "AISim Mach–Zehnder phase scan",
                "x_key": "phase_scan_rad",
                "x_label": "final phase scan (rad)",
                "y_label": "population",
                "series": [
                    {"key": "output_port_2", "label": "port 2", "kind": "line"},
                    {"key": "output_port_3", "label": "port 3", "kind": "line"},
                    {"key": "fit_port_3", "label": "fit (port 3)", "kind": "dashed"},
                ],
            },
            {
                "name": "simulation_secondary",
                "title": "AISim Mach–Zehnder differential output",
                "x_key": "phase_scan_rad",
                "x_label": "final phase scan (rad)",
                "y_label": "signal",
                "series": [
                    {"key": "differential_signal", "label": "port3 - port2", "kind": "line"},
                    {"key": "normalized_differential_signal", "label": "normalized diff", "kind": "line"},
                ],
            },
        ],
        "config": {
            "phase_min_rad": float(phase_min_rad),
            "phase_max_rad": float(phase_max_rad),
            "n_phase_points": int(n_phase_points),
        },
    }
    return _pack_result(
        result,
        source_cfg=source_cfg,
        detected_count=detected_count,
        pulse_sequence={"model": "mach_zehnder_phase_scan", **sequence.as_dict()},
        physical_model={
            "atom_source": "AISim random ensemble + spherical detector",
            "pulse_sequence": "AISim SpatialSuperpositionTransitionPropagator three-pulse sequence",
            "phase_accumulation": "AISim final beam-splitter phase scan only; scanned parameter is directly applied as final phase",
            "noise": "none beyond ensemble/beam inhomogeneity already present in AISim",
            "estimator": "output-port populations and differential population signal",
            "readout": "population in output ports 2 and 3",
        },
        study_scope="full_aisim_three_pulse_phase_fringe_study",
        limitations=[
            "The scanned phase is an imposed final interferometer phase, not a fully derived gravity phase.",
            "Systematics such as gravity gradients, AC Stark shifts, and Coriolis terms are not yet included.",
        ],
    )


def run_aisim_gravity_sweep(
    *,
    n_atoms: int = 1000,
    seed: int = 1,
    cloud_radius_m: float = 3.0e-3,
    temp_xy_K: float = 2.5e-6,
    temp_z_K: float = 100e-9,
    detector_time_s: float = 778e-3,
    detector_radius_m: float = 5e-3,
    beam_radius_m: float = 29.5e-3 / 2.0,
    center_rabi_freq_hz: float = 12.5e3,
    wavelength_m: float = WAVELENGTH_RB87_D2.value,
    tau_pi_half_s: float = 23e-6,
    interferometer_time_s: float = 260e-3,
    gravity_center_m_s2: float = NOMINAL_GRAVITY.value,
    gravity_span_m_s2: float = 6.0e-6,
    n_gravity_points: int = 61,
    phase_bias_rad: float | None = None,
    lock_to_midfringe: bool = True,
    k1_rad_per_m: float | None = None,
    k2_rad_per_m: float | None = None,
) -> dict[str, Any]:
    if n_gravity_points < 5:
        raise ValueError("n_gravity_points must be at least 5.")
    _, detected_atoms, _, detected_count, source_cfg = _create_detected_ensemble(
        n_atoms=n_atoms,
        seed=seed,
        cloud_radius_m=cloud_radius_m,
        temp_xy_K=temp_xy_K,
        temp_z_K=temp_z_K,
        detector_time_s=detector_time_s,
        detector_radius_m=detector_radius_m,
        multiport=True,
    )
    intensity_profile = _gaussian_beam(beam_radius_m=beam_radius_m, center_rabi_freq_hz=center_rabi_freq_hz)
    wave_vectors = _wave_vectors(wavelength_m=wavelength_m, k1_rad_per_m=k1_rad_per_m, k2_rad_per_m=k2_rad_per_m)
    k_eff = float(wave_vectors.k1 - wave_vectors.k2)
    if phase_bias_rad is None:
        phase_bias_rad = 0.0
    if lock_to_midfringe:
        phase_bias_rad = float(np.pi / 2.0 - k_eff * float(gravity_center_m_s2) * (float(interferometer_time_s) ** 2))

    sequence = MachZehnderPulseSequence(
        tau_pi_half_s=float(tau_pi_half_s),
        interferometer_time_s=float(interferometer_time_s),
    )
    g_values = gravity_sweep_axis(float(gravity_center_m_s2), float(gravity_span_m_s2), int(n_gravity_points))
    total_phase = _hybrid_gravity_phase_rad(
        g_m_s2=g_values,
        k_eff_rad_per_m=k_eff,
        T_s=interferometer_time_s,
        phase_bias_rad=phase_bias_rad,
    )
    port2 = np.zeros_like(g_values)
    port3 = np.zeros_like(g_values)
    diff = np.zeros_like(g_values)
    norm_diff = np.zeros_like(g_values)
    for i, phase in enumerate(total_phase):
        out = _run_mach_zehnder_sequence(
            detected_atoms,
            tau_pi_half_s=tau_pi_half_s,
            interferometer_time_s=interferometer_time_s,
            intensity_profile=intensity_profile,
            wave_vectors=wave_vectors,
            final_phase_rad=float(phase),
        )
        port2[i] = out["port_2"]
        port3[i] = out["port_3"]
        diff[i] = out["differential_signal"]
        norm_diff[i] = out["normalized_differential_signal"]
    center_idx = len(g_values) // 2
    if 0 < center_idx < len(g_values) - 1:
        slope = float((norm_diff[center_idx + 1] - norm_diff[center_idx - 1]) / (g_values[center_idx + 1] - g_values[center_idx - 1]))
    else:
        slope = float("nan")

    from qgrav.physics.phase_models import shot_noise_sensitivity_m_s2_per_sqrt_hz
    _sens_gs = shot_noise_sensitivity_m_s2_per_sqrt_hz(
        k_eff_rad_per_m=k_eff,
        interferometer_time_s=float(interferometer_time_s),
        n_atoms=max(detected_count, 1),
        contrast=1.0,
        cycle_time_s=1.0,
    )

    result = {
        "backend": "aisim",
        "model": "gravity_sweep",
        "study_type": "hybrid_aisim_plus_analytic_gravity_phase",
        "n_atoms_total": int(n_atoms),
        "n_atoms_detected": detected_count,
        "detected_fraction": float(detected_count / float(n_atoms)),
        "k_eff_rad_per_m": k_eff,
        "interferometer_time_s": float(interferometer_time_s),
        "tau_pi_half_s": float(tau_pi_half_s),
        "gravity_values_m_s2": g_values,
        "total_phase_rad": total_phase,
        "output_port_2": port2,
        "output_port_3": port3,
        "differential_signal": diff,
        "normalized_differential_signal": norm_diff,
        "gravity_center_m_s2": float(gravity_center_m_s2),
        "gravity_span_m_s2": float(gravity_span_m_s2),
        "phase_bias_rad": float(phase_bias_rad),
        "operating_slope_per_m_s2": slope,
        "shot_noise_sensitivity_m_s2_per_sqrt_hz": _sens_gs,
        "shot_noise_sensitivity_ugal_per_sqrt_hz": _sens_gs * 1e8,
        "summary_rows": {
            "Backend": "aisim",
            "Model": "gravity_sweep",
            "Study type": "hybrid_aisim_plus_analytic_gravity_phase",
            "Total atoms": int(n_atoms),
            "Detected atoms": detected_count,
            "Detected fraction": float(detected_count / float(n_atoms)),
            "k_eff (rad/m)": k_eff,
            "Interferometer time T (s)": float(interferometer_time_s),
            "Gravity center (m/s²)": float(gravity_center_m_s2),
            "Gravity span (m/s²)": float(gravity_span_m_s2),
            "Phase bias (rad)": float(phase_bias_rad),
            "Mid-fringe slope (norm signal per m/s²)": slope,
            "Sensitivity (m/s²/√Hz)": _sens_gs,
            "Sensitivity (µGal/√Hz)": _sens_gs * 1e8,
        },
        "plot_specs": [
            {
                "name": "simulation_primary",
                "title": "Gravity sweep response",
                "x_key": "gravity_values_m_s2",
                "x_label": "gravity (m/s²)",
                "y_label": "signal",
                "series": [
                    {"key": "output_port_2", "label": "port 2", "kind": "line"},
                    {"key": "output_port_3", "label": "port 3", "kind": "line"},
                    {"key": "normalized_differential_signal", "label": "normalized diff", "kind": "line"},
                ],
            },
            {
                "name": "simulation_secondary",
                "title": "Gravity sweep phase mapping",
                "x_key": "gravity_values_m_s2",
                "x_label": "gravity (m/s²)",
                "y_label": "phase / differential signal",
                "series": [
                    {"key": "total_phase_rad", "label": "total phase (rad)", "kind": "line"},
                    {"key": "differential_signal", "label": "diff signal", "kind": "line"},
                ],
            },
        ],
        "config": {
            "n_gravity_points": int(n_gravity_points),
            "lock_to_midfringe": bool(lock_to_midfringe),
        },
    }
    return _pack_result(
        result,
        source_cfg=source_cfg,
        detected_count=detected_count,
        pulse_sequence={"model": "mach_zehnder_gravity_sweep", **sequence.as_dict()},
        physical_model={
            "atom_source": "AISim random ensemble + spherical detector",
            "pulse_sequence": "AISim SpatialSuperpositionTransitionPropagator three-pulse sequence",
            "phase_accumulation": "Hybrid model: AISim pulse contrast + analytic gravity phase k_eff g T^2",
            "noise": "none beyond ensemble/beam inhomogeneity already present in AISim",
            "estimator": "output-port populations and normalized differential signal around mid-fringe",
            "readout": "population in output ports 2 and 3",
        },
        study_scope="hybrid_aisim_plus_closed_form_gravity_phase",
        limitations=[
            "Gravity coupling is introduced analytically through k_eff g T^2 rather than derived from a full space-time evolution in AISim.",
            "This is suitable for gravimeter-response studies but should not be described as a complete digital twin.",
        ],
    )


def run_aisim_vibration_sensitivity_sweep(
    *,
    n_atoms: int = 1000,
    seed: int = 1,
    cloud_radius_m: float = 3.0e-3,
    temp_xy_K: float = 2.5e-6,
    temp_z_K: float = 100e-9,
    detector_time_s: float = 778e-3,
    detector_radius_m: float = 5e-3,
    beam_radius_m: float = 29.5e-3 / 2.0,
    center_rabi_freq_hz: float = 12.5e3,
    wavelength_m: float = WAVELENGTH_RB87_D2.value,
    tau_pi_half_s: float = 23e-6,
    interferometer_time_s: float = 260e-3,
    gravity_ref_m_s2: float = NOMINAL_GRAVITY.value,
    vibration_frequency_hz: float = 1.0,
    vibration_phase0_rad: float = 0.0,
    amplitude_min_m: float = 0.0,
    amplitude_max_m: float = 5.0e-8,
    n_amplitude_points: int = 41,
    phase_bias_rad: float | None = None,
    lock_to_midfringe: bool = True,
    k1_rad_per_m: float | None = None,
    k2_rad_per_m: float | None = None,
) -> dict[str, Any]:
    if n_amplitude_points < 5:
        raise ValueError("n_amplitude_points must be at least 5.")
    _, detected_atoms, _, detected_count, source_cfg = _create_detected_ensemble(
        n_atoms=n_atoms,
        seed=seed,
        cloud_radius_m=cloud_radius_m,
        temp_xy_K=temp_xy_K,
        temp_z_K=temp_z_K,
        detector_time_s=detector_time_s,
        detector_radius_m=detector_radius_m,
        multiport=True,
    )
    intensity_profile = _gaussian_beam(beam_radius_m=beam_radius_m, center_rabi_freq_hz=center_rabi_freq_hz)
    wave_vectors = _wave_vectors(wavelength_m=wavelength_m, k1_rad_per_m=k1_rad_per_m, k2_rad_per_m=k2_rad_per_m)
    k_eff = float(wave_vectors.k1 - wave_vectors.k2)
    if phase_bias_rad is None:
        phase_bias_rad = 0.0
    if lock_to_midfringe:
        phase_bias_rad = float(np.pi / 2.0 - k_eff * float(gravity_ref_m_s2) * (float(interferometer_time_s) ** 2))
    base_phase = _hybrid_gravity_phase_rad(
        g_m_s2=np.array([gravity_ref_m_s2], dtype=np.float64),
        k_eff_rad_per_m=k_eff,
        T_s=interferometer_time_s,
        phase_bias_rad=phase_bias_rad,
    )[0]

    sequence = MachZehnderPulseSequence(
        tau_pi_half_s=float(tau_pi_half_s),
        interferometer_time_s=float(interferometer_time_s),
    )
    amplitudes = vibration_amplitude_axis(float(amplitude_min_m), float(amplitude_max_m), int(n_amplitude_points))
    vib_phase = _vibration_phase_sinusoid(
        amplitudes_m=amplitudes,
        frequency_hz=vibration_frequency_hz,
        interferometer_time_s=interferometer_time_s,
        k_eff_rad_per_m=k_eff,
        phase0_rad=vibration_phase0_rad,
    )
    total_phase = base_phase + vib_phase
    port2 = np.zeros_like(amplitudes)
    port3 = np.zeros_like(amplitudes)
    diff = np.zeros_like(amplitudes)
    norm_diff = np.zeros_like(amplitudes)
    for i, phase in enumerate(total_phase):
        out = _run_mach_zehnder_sequence(
            detected_atoms,
            tau_pi_half_s=tau_pi_half_s,
            interferometer_time_s=interferometer_time_s,
            intensity_profile=intensity_profile,
            wave_vectors=wave_vectors,
            final_phase_rad=float(phase),
        )
        port2[i] = out["port_2"]
        port3[i] = out["port_3"]
        diff[i] = out["differential_signal"]
        norm_diff[i] = out["normalized_differential_signal"]
    equiv_g_error = equivalent_gravity_error_m_s2(
        vib_phase,
        k_eff_rad_per_m=k_eff,
        interferometer_time_s=float(interferometer_time_s),
    )
    if len(amplitudes) >= 2:
        slope = float((equiv_g_error[-1] - equiv_g_error[0]) / max(amplitudes[-1] - amplitudes[0], 1e-30))
    else:
        slope = float("nan")

    from qgrav.physics.phase_models import shot_noise_sensitivity_m_s2_per_sqrt_hz
    _sens_vs = shot_noise_sensitivity_m_s2_per_sqrt_hz(
        k_eff_rad_per_m=k_eff,
        interferometer_time_s=float(interferometer_time_s),
        n_atoms=max(detected_count, 1),
        contrast=1.0,
        cycle_time_s=1.0,
    )

    result = {
        "backend": "aisim",
        "model": "vibration_sensitivity_sweep",
        "study_type": "hybrid_aisim_plus_analytic_vibration_phase",
        "n_atoms_total": int(n_atoms),
        "n_atoms_detected": detected_count,
        "detected_fraction": float(detected_count / float(n_atoms)),
        "k_eff_rad_per_m": k_eff,
        "interferometer_time_s": float(interferometer_time_s),
        "tau_pi_half_s": float(tau_pi_half_s),
        "gravity_ref_m_s2": float(gravity_ref_m_s2),
        "vibration_frequency_hz": float(vibration_frequency_hz),
        "vibration_phase0_rad": float(vibration_phase0_rad),
        "vibration_amplitude_m": amplitudes,
        "vibration_phase_rad": vib_phase,
        "equivalent_gravity_error_m_s2": equiv_g_error,
        "output_port_2": port2,
        "output_port_3": port3,
        "differential_signal": diff,
        "normalized_differential_signal": norm_diff,
        "phase_bias_rad": float(phase_bias_rad),
        "equivalent_gravity_error_per_m": slope,
        "shot_noise_sensitivity_m_s2_per_sqrt_hz": _sens_vs,
        "shot_noise_sensitivity_ugal_per_sqrt_hz": _sens_vs * 1e8,
        "summary_rows": {
            "Backend": "aisim",
            "Model": "vibration_sensitivity_sweep",
            "Study type": "hybrid_aisim_plus_analytic_vibration_phase",
            "Total atoms": int(n_atoms),
            "Detected atoms": detected_count,
            "Detected fraction": float(detected_count / float(n_atoms)),
            "k_eff (rad/m)": k_eff,
            "Interferometer time T (s)": float(interferometer_time_s),
            "Vibration frequency (Hz)": float(vibration_frequency_hz),
            "Max amplitude (m)": float(amplitudes[-1]),
            "Max equivalent gravity error (m/s²)": float(np.max(np.abs(equiv_g_error))),
            "Equivalent gravity error per meter amplitude": slope,
            "Sensitivity (m/s²/√Hz)": _sens_vs,
            "Sensitivity (µGal/√Hz)": _sens_vs * 1e8,
        },
        "plot_specs": [
            {
                "name": "simulation_primary",
                "title": "Vibration sensitivity sweep",
                "x_key": "vibration_amplitude_m",
                "x_scale": 1e9,
                "x_label": "vibration amplitude (nm)",
                "y_label": "equivalent gravity error / signal",
                "series": [
                    {"key": "equivalent_gravity_error_m_s2", "label": "equiv gravity error (m/s²)", "kind": "line"},
                    {"key": "normalized_differential_signal", "label": "normalized diff", "kind": "line"},
                ],
            },
            {
                "name": "simulation_secondary",
                "title": "Vibration-induced phase and output ports",
                "x_key": "vibration_amplitude_m",
                "x_scale": 1e9,
                "x_label": "vibration amplitude (nm)",
                "y_label": "phase / population",
                "series": [
                    {"key": "vibration_phase_rad", "label": "vibration phase (rad)", "kind": "line"},
                    {"key": "output_port_2", "label": "port 2", "kind": "line"},
                    {"key": "output_port_3", "label": "port 3", "kind": "line"},
                ],
            },
        ],
        "config": {
            "n_amplitude_points": int(n_amplitude_points),
            "lock_to_midfringe": bool(lock_to_midfringe),
        },
    }
    return _pack_result(
        result,
        source_cfg=source_cfg,
        detected_count=detected_count,
        pulse_sequence={"model": "mach_zehnder_vibration_sweep", **sequence.as_dict()},
        physical_model={
            "atom_source": "AISim random ensemble + spherical detector",
            "pulse_sequence": "AISim SpatialSuperpositionTransitionPropagator three-pulse sequence",
            "phase_accumulation": "Hybrid model: AISim pulse contrast + analytic reference-mirror vibration phase",
            "noise": "none beyond ensemble/beam inhomogeneity already present in AISim",
            "estimator": "output-port populations and normalized differential signal",
            "readout": "population in output ports 2 and 3",
        },
        study_scope="hybrid_aisim_plus_reference_mirror_vibration_phase",
        limitations=[
            "Vibration coupling uses the standard three-pulse sensitivity-function approximation, not a separate external sensor model.",
            "No active vibration compensation or tilt-coupling estimator is included yet.",
        ],
    )


def run_simulation_from_config(sim_cfg: dict[str, Any]) -> dict[str, Any] | None:
    if not isinstance(sim_cfg, dict) or not bool(sim_cfg.get("enabled", False)):
        return None
    backend = str(sim_cfg.get("backend", "aisim")).strip().lower()
    if backend != "aisim":
        raise ValueError(f"Unsupported simulation backend: {backend}")
    model = str(sim_cfg.get("model", "rabi_scan")).strip().lower()

    common = dict(
        n_atoms=int(sim_cfg.get("n_atoms", 1000)),
        seed=int(sim_cfg.get("seed", 1)),
        cloud_radius_m=float(sim_cfg.get("cloud_radius_m", 3.0e-3)),
        temp_xy_K=float(sim_cfg.get("temp_xy_K", 2.5e-6)),
        temp_z_K=float(sim_cfg.get("temp_z_K", 100e-9)),
        detector_time_s=float(sim_cfg.get("detector_time_s", 778e-3)),
        detector_radius_m=float(sim_cfg.get("detector_radius_m", 5e-3)),
        beam_radius_m=float(sim_cfg.get("beam_radius_m", 29.5e-3 / 2.0)),
        center_rabi_freq_hz=float(sim_cfg.get("center_rabi_freq_hz", 12.5e3)),
        wavelength_m=float(sim_cfg.get("wavelength_m", WAVELENGTH_RB87_D2.value)),
        k1_rad_per_m=None if sim_cfg.get("k1_rad_per_m") is None else float(sim_cfg.get("k1_rad_per_m")),
        k2_rad_per_m=None if sim_cfg.get("k2_rad_per_m") is None else float(sim_cfg.get("k2_rad_per_m")),
    )

    if model == "rabi_scan":
        return run_aisim_rabi_scan(
            **common,
            pre_pulse_delay_s=float(sim_cfg.get("pre_pulse_delay_s", 100e-3)),
            tau_step_s=float(sim_cfg.get("tau_step_s", 1e-6)),
            n_steps=int(sim_cfg.get("n_steps", 60)),
        )
    if model == "mach_zehnder_phase_scan":
        return run_aisim_mach_zehnder_phase_scan(
            **common,
            tau_pi_half_s=float(sim_cfg.get("tau_pi_half_s", 23e-6)),
            interferometer_time_s=float(sim_cfg.get("interferometer_time_s", 260e-3)),
            phase_min_rad=float(sim_cfg.get("phase_min_rad", 0.0)),
            phase_max_rad=float(sim_cfg.get("phase_max_rad", 2.0 * np.pi)),
            n_phase_points=int(sim_cfg.get("n_phase_points", 81)),
        )
    if model == "gravity_sweep":
        return run_aisim_gravity_sweep(
            **common,
            tau_pi_half_s=float(sim_cfg.get("tau_pi_half_s", 23e-6)),
            interferometer_time_s=float(sim_cfg.get("interferometer_time_s", 260e-3)),
            gravity_center_m_s2=float(sim_cfg.get("gravity_center_m_s2", NOMINAL_GRAVITY.value)),
            gravity_span_m_s2=float(sim_cfg.get("gravity_span_m_s2", 6.0e-6)),
            n_gravity_points=int(sim_cfg.get("n_gravity_points", 61)),
            phase_bias_rad=None if sim_cfg.get("phase_bias_rad") is None else float(sim_cfg.get("phase_bias_rad")),
            lock_to_midfringe=bool(sim_cfg.get("lock_to_midfringe", True)),
        )
    if model == "vibration_sensitivity_sweep":
        return run_aisim_vibration_sensitivity_sweep(
            **common,
            tau_pi_half_s=float(sim_cfg.get("tau_pi_half_s", 23e-6)),
            interferometer_time_s=float(sim_cfg.get("interferometer_time_s", 260e-3)),
            gravity_ref_m_s2=float(sim_cfg.get("gravity_ref_m_s2", NOMINAL_GRAVITY.value)),
            vibration_frequency_hz=float(sim_cfg.get("vibration_frequency_hz", 1.0)),
            vibration_phase0_rad=float(sim_cfg.get("vibration_phase0_rad", 0.0)),
            amplitude_min_m=float(sim_cfg.get("amplitude_min_m", 0.0)),
            amplitude_max_m=float(sim_cfg.get("amplitude_max_m", 5.0e-8)),
            n_amplitude_points=int(sim_cfg.get("n_amplitude_points", 41)),
            phase_bias_rad=None if sim_cfg.get("phase_bias_rad") is None else float(sim_cfg.get("phase_bias_rad")),
            lock_to_midfringe=bool(sim_cfg.get("lock_to_midfringe", True)),
        )
    raise ValueError(f"Unsupported AISim model: {model}")
