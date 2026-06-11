"""Rabi and Mach-Zehnder phase-scan studies (moved verbatim from ``aisim_adapter.py`` in the v1.4
modularisation; the physics is unchanged). Re-exported by
:mod:`qgrav.sim_ai.aisim_adapter`, which remains the public import path."""

from __future__ import annotations

import logging
from typing import Any

import numpy as np

from qgrav.physics import (
    MachZehnderPulseSequence,
    RabiPulseScan,
    phase_scan_axis,
)
from qgrav.physics.constants import WAVELENGTH_RB87_D2
from qgrav.sim_ai._adapter_core import (
    _build_wavefront,
    _create_detected_ensemble,
    _fit_sinusoid,
    _gaussian_beam,
    _pack_result,
    _run_mach_zehnder_sequence,
    _wave_vectors,
)

logger = logging.getLogger(__name__)


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
    intensity_profile = _gaussian_beam(
        beam_radius_m=beam_radius_m, center_rabi_freq_hz=center_rabi_freq_hz
    )
    wave_vectors = _wave_vectors(
        wavelength_m=wavelength_m, k1_rad_per_m=k1_rad_per_m, k2_rad_per_m=k2_rad_per_m
    )
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
    single_photon_detuning_hz: float = 0.0,
    wavefront_zernike_coeffs: dict | None = None,
    wavefront_radius_m: float = 0.05,
) -> dict[str, Any]:
    if n_phase_points < 5:
        raise ValueError("n_phase_points must be at least 5.")
    _wavefront = _build_wavefront(
        wavefront_zernike_coeffs=wavefront_zernike_coeffs,
        wavefront_radius_m=wavefront_radius_m,
    )
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
    intensity_profile = _gaussian_beam(
        beam_radius_m=beam_radius_m, center_rabi_freq_hz=center_rabi_freq_hz
    )
    wave_vectors = _wave_vectors(
        wavelength_m=wavelength_m, k1_rad_per_m=k1_rad_per_m, k2_rad_per_m=k2_rad_per_m
    )
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
            wavefront=_wavefront,
            single_photon_detuning_hz=float(single_photon_detuning_hz),
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
                    {
                        "key": "normalized_differential_signal",
                        "label": "normalized diff",
                        "kind": "line",
                    },
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
