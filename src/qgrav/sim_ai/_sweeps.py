"""Gravity and vibration-sensitivity sweep studies (moved verbatim from ``aisim_adapter.py`` in the v1.4
modularisation; the physics is unchanged). Re-exported by
:mod:`qgrav.sim_ai.aisim_adapter`, which remains the public import path."""

from __future__ import annotations

import logging
from typing import Any

import numpy as np

from qgrav.physics import (
    MachZehnderPulseSequence,
    equivalent_gravity_error_m_s2,
    gravity_sweep_axis,
    vibration_amplitude_axis,
)
from qgrav.physics.constants import NOMINAL_GRAVITY, WAVELENGTH_RB87_D2
from qgrav.sim_ai._adapter_core import (
    _build_wavefront,
    _calibrate_gravity_phase_offset,
    _create_detected_ensemble,
    _gaussian_beam,
    _hybrid_gravity_phase_rad,
    _pack_result,
    _run_mach_zehnder_sequence,
    _run_mach_zehnder_sequence_with_gravity,
    _vibration_phase_sinusoid,
    _wave_vectors,
    bertoldi_finite_tau_scale_factor,
)

logger = logging.getLogger(__name__)


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
    gravity_propagation: bool = False,
    gravity_gradient_per_m: float = 0.0,
    single_photon_detuning_hz: float = 0.0,
    wavefront_zernike_coeffs: dict | None = None,
    wavefront_radius_m: float = 0.05,
    raman_substeps: int = 1,
) -> dict[str, Any]:
    if n_gravity_points < 5:
        raise ValueError("n_gravity_points must be at least 5.")
    if int(raman_substeps) < 1:
        raise ValueError("raman_substeps must be >= 1.")
    _wavefront = _build_wavefront(
        wavefront_zernike_coeffs=wavefront_zernike_coeffs,
        wavefront_radius_m=wavefront_radius_m,
    )
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
    intensity_profile = _gaussian_beam(
        beam_radius_m=beam_radius_m, center_rabi_freq_hz=center_rabi_freq_hz
    )
    # Compute k_eff from default or custom wave vectors
    wv_tmp = _wave_vectors(
        wavelength_m=wavelength_m, k1_rad_per_m=k1_rad_per_m, k2_rad_per_m=k2_rad_per_m
    )
    k_eff = float(wv_tmp.k1 - wv_tmp.k2)

    if gravity_propagation:
        # --- FULLY SIMULATED path ---
        # Chirp the laser at -k_eff * g_center to cancel gravity-induced Doppler
        chirp_rate = -k_eff * float(gravity_center_m_s2)
        wave_vectors = _wave_vectors(
            wavelength_m=wavelength_m,
            k1_rad_per_m=k1_rad_per_m,
            k2_rad_per_m=k2_rad_per_m,
            chirp_rate_rad_per_s2=chirp_rate,
        )
        # In simulated mode, gravity phase emerges from the trajectory.
        # phase_bias is purely the offset applied to bs2 (e.g. pi/2 for mid-fringe).
        if phase_bias_rad is None:
            phase_bias_rad = 0.0
        if lock_to_midfringe:
            phase_bias_rad = float(np.pi / 2.0)
    else:
        # --- HYBRID path (original behaviour) ---
        wave_vectors = wv_tmp
        if phase_bias_rad is None:
            phase_bias_rad = 0.0
        if lock_to_midfringe:
            phase_bias_rad = float(
                np.pi / 2.0
                - k_eff * float(gravity_center_m_s2) * (float(interferometer_time_s) ** 2)
            )

    sequence = MachZehnderPulseSequence(
        tau_pi_half_s=float(tau_pi_half_s),
        interferometer_time_s=float(interferometer_time_s),
    )
    g_values = gravity_sweep_axis(
        float(gravity_center_m_s2), float(gravity_span_m_s2), int(n_gravity_points)
    )

    if not gravity_propagation:
        total_phase = _hybrid_gravity_phase_rad(
            g_m_s2=g_values,
            k_eff_rad_per_m=k_eff,
            T_s=interferometer_time_s,
            phase_bias_rad=phase_bias_rad,
        )
    else:
        # In gravity-propagation mode, total_phase is not computed analytically;
        # the gravity phase emerges from the simulation.  Store phase_bias for reference.
        total_phase = np.full_like(g_values, float(phase_bias_rad))

    # Calibrate the simulated mode's residual pulse-timing phase offset by
    # running an MZ fringe scan at g = g_chirp (= gravity_center).  At this
    # gravity value, the chirp perfectly tracks gravity and the analytical
    # gravity phase vanishes; any non-zero fringe shift is a pulse-timing
    # artefact.  Subtracting this offset from phase_scan aligns the
    # simulated and hybrid fringes.  Cost: one fringe scan (~70 MZ calls)
    # per sweep, independent of n_gravity_points.
    sim_phase_offset = 0.0
    if gravity_propagation:
        sim_phase_offset = _calibrate_gravity_phase_offset(
            detected_atoms,
            tau_pi_half_s=tau_pi_half_s,
            interferometer_time_s=interferometer_time_s,
            intensity_profile=intensity_profile,
            wave_vectors=wave_vectors,
            g_chirp_m_s2=float(gravity_center_m_s2),
            gravity_gradient_per_m=float(gravity_gradient_per_m),
            raman_substeps=int(raman_substeps),
        )

    port2 = np.zeros_like(g_values)
    port3 = np.zeros_like(g_values)
    diff = np.zeros_like(g_values)
    norm_diff = np.zeros_like(g_values)
    for i, g_val in enumerate(g_values):
        if gravity_propagation:
            out = _run_mach_zehnder_sequence_with_gravity(
                detected_atoms,
                tau_pi_half_s=tau_pi_half_s,
                interferometer_time_s=interferometer_time_s,
                intensity_profile=intensity_profile,
                wave_vectors=wave_vectors,
                final_phase_rad=float(phase_bias_rad),
                g_m_s2=float(g_val),
                gravity_gradient_per_m=float(gravity_gradient_per_m),
                phase_offset_rad=sim_phase_offset,
                wavefront=_wavefront,
                single_photon_detuning_hz=float(single_photon_detuning_hz),
                raman_substeps=int(raman_substeps),
            )
        else:
            out = _run_mach_zehnder_sequence(
                detected_atoms,
                tau_pi_half_s=tau_pi_half_s,
                interferometer_time_s=interferometer_time_s,
                intensity_profile=intensity_profile,
                wave_vectors=wave_vectors,
                final_phase_rad=float(total_phase[i]),
                wavefront=_wavefront,
                single_photon_detuning_hz=float(single_photon_detuning_hz),
            )
        port2[i] = out["port_2"]
        port3[i] = out["port_3"]
        diff[i] = out["differential_signal"]
        norm_diff[i] = out["normalized_differential_signal"]
    center_idx = len(g_values) // 2
    if 0 < center_idx < len(g_values) - 1:
        slope = float(
            (norm_diff[center_idx + 1] - norm_diff[center_idx - 1])
            / (g_values[center_idx + 1] - g_values[center_idx - 1])
        )
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

    _study_type = (
        "fully_simulated_gravity_propagation"
        if gravity_propagation
        else "hybrid_aisim_plus_analytic_gravity_phase"
    )
    result = {
        "backend": "aisim",
        "model": "gravity_sweep",
        "study_type": _study_type,
        "gravity_propagation": bool(gravity_propagation),
        "raman_substeps": int(raman_substeps),
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
        # Phase 18: Bertoldi 2019 closed-form finite-tau scale-factor correction.
        # Reported alongside the empirical calibration as an independent
        # analytical cross-check (the calibration removes the residual
        # numerically; this number predicts what the residual *should* be from
        # finite-pulse-duration physics).
        "bertoldi_finite_tau_scale_factor": float(
            bertoldi_finite_tau_scale_factor(
                tau_pi_half_s=float(tau_pi_half_s),
                interferometer_time_s=float(interferometer_time_s),
            )
        ),
        "empirical_phase_offset_rad": float(sim_phase_offset),
        "shot_noise_sensitivity_m_s2_per_sqrt_hz": _sens_gs,
        "shot_noise_sensitivity_ugal_per_sqrt_hz": _sens_gs * 1e8,
        "summary_rows": {
            "Backend": "aisim",
            "Model": "gravity_sweep",
            "Study type": _study_type,
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
                    {
                        "key": "normalized_differential_signal",
                        "label": "normalized diff",
                        "kind": "line",
                    },
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
    if gravity_propagation:
        _physical_model = {
            "atom_source": "AISim random ensemble + spherical detector",
            "pulse_sequence": "AISim SpatialSuperpositionTransitionPropagator three-pulse sequence",
            "propagation": "GravityFreePropagator with ballistic trajectory under local g",
            "phase_accumulation": "Gravity phase emerges from trajectory + chirped-laser detuning mismatch",
            "chirp_rate": f"{-k_eff * float(gravity_center_m_s2):.6e} rad/s^2 (tracking g_center)",
            "noise": "none beyond ensemble/beam inhomogeneity already present in AISim",
            "estimator": "output-port populations and normalized differential signal around mid-fringe",
            "readout": "population in output ports 2 and 3",
        }
        _scope = "fully_simulated_gravity_propagation"
        _limits = [
            "Pulse durations are short enough that gravity during pulses is neglected (tau << T).",
            "Gravity gradient is constant during the interferometer (no tidal terms).",
        ]
    else:
        _physical_model = {
            "atom_source": "AISim random ensemble + spherical detector",
            "pulse_sequence": "AISim SpatialSuperpositionTransitionPropagator three-pulse sequence",
            "phase_accumulation": "Hybrid model: AISim pulse contrast + analytic gravity phase k_eff g T^2",
            "noise": "none beyond ensemble/beam inhomogeneity already present in AISim",
            "estimator": "output-port populations and normalized differential signal around mid-fringe",
            "readout": "population in output ports 2 and 3",
        }
        _scope = "hybrid_aisim_plus_closed_form_gravity_phase"
        _limits = [
            "Gravity coupling is introduced analytically through k_eff g T^2 rather than derived from a full space-time evolution in AISim.",
            "This is suitable for gravimeter-response studies but should not be described as a complete digital twin.",
        ]

    return _pack_result(
        result,
        source_cfg=source_cfg,
        detected_count=detected_count,
        pulse_sequence={"model": "mach_zehnder_gravity_sweep", **sequence.as_dict()},
        physical_model=_physical_model,
        study_scope=_scope,
        limitations=_limits,
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
    gravity_propagation: bool = False,
    gravity_gradient_per_m: float = 0.0,
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
    intensity_profile = _gaussian_beam(
        beam_radius_m=beam_radius_m, center_rabi_freq_hz=center_rabi_freq_hz
    )
    wv_tmp = _wave_vectors(
        wavelength_m=wavelength_m, k1_rad_per_m=k1_rad_per_m, k2_rad_per_m=k2_rad_per_m
    )
    k_eff = float(wv_tmp.k1 - wv_tmp.k2)

    if gravity_propagation:
        chirp_rate = -k_eff * float(gravity_ref_m_s2)
        wave_vectors = _wave_vectors(
            wavelength_m=wavelength_m,
            k1_rad_per_m=k1_rad_per_m,
            k2_rad_per_m=k2_rad_per_m,
            chirp_rate_rad_per_s2=chirp_rate,
        )
        if phase_bias_rad is None:
            phase_bias_rad = 0.0
        if lock_to_midfringe:
            phase_bias_rad = float(np.pi / 2.0)
    else:
        wave_vectors = wv_tmp
        if phase_bias_rad is None:
            phase_bias_rad = 0.0
        if lock_to_midfringe:
            phase_bias_rad = float(
                np.pi / 2.0 - k_eff * float(gravity_ref_m_s2) * (float(interferometer_time_s) ** 2)
            )

    if not gravity_propagation:
        base_phase = _hybrid_gravity_phase_rad(
            g_m_s2=np.array([gravity_ref_m_s2], dtype=np.float64),
            k_eff_rad_per_m=k_eff,
            T_s=interferometer_time_s,
            phase_bias_rad=phase_bias_rad,
        )[0]
    else:
        base_phase = float(phase_bias_rad)

    sequence = MachZehnderPulseSequence(
        tau_pi_half_s=float(tau_pi_half_s),
        interferometer_time_s=float(interferometer_time_s),
    )
    amplitudes = vibration_amplitude_axis(
        float(amplitude_min_m), float(amplitude_max_m), int(n_amplitude_points)
    )
    vib_phase = _vibration_phase_sinusoid(
        amplitudes_m=amplitudes,
        frequency_hz=vibration_frequency_hz,
        interferometer_time_s=interferometer_time_s,
        k_eff_rad_per_m=k_eff,
        phase0_rad=vibration_phase0_rad,
    )
    total_phase = base_phase + vib_phase

    # Calibrate the simulated-mode constant phase offset (see
    # `_calibrate_gravity_phase_offset` for details).
    sim_phase_offset = 0.0
    if gravity_propagation:
        sim_phase_offset = _calibrate_gravity_phase_offset(
            detected_atoms,
            tau_pi_half_s=tau_pi_half_s,
            interferometer_time_s=interferometer_time_s,
            intensity_profile=intensity_profile,
            wave_vectors=wave_vectors,
            g_chirp_m_s2=float(gravity_ref_m_s2),
            gravity_gradient_per_m=float(gravity_gradient_per_m),
        )

    port2 = np.zeros_like(amplitudes)
    port3 = np.zeros_like(amplitudes)
    diff = np.zeros_like(amplitudes)
    norm_diff = np.zeros_like(amplitudes)
    for i, phase in enumerate(total_phase):
        if gravity_propagation:
            out = _run_mach_zehnder_sequence_with_gravity(
                detected_atoms,
                tau_pi_half_s=tau_pi_half_s,
                interferometer_time_s=interferometer_time_s,
                intensity_profile=intensity_profile,
                wave_vectors=wave_vectors,
                final_phase_rad=float(phase),
                g_m_s2=float(gravity_ref_m_s2),
                gravity_gradient_per_m=float(gravity_gradient_per_m),
                phase_offset_rad=sim_phase_offset,
            )
        else:
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
        slope = float(
            (equiv_g_error[-1] - equiv_g_error[0]) / max(amplitudes[-1] - amplitudes[0], 1e-30)
        )
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
                    {
                        "key": "equivalent_gravity_error_m_s2",
                        "label": "equiv gravity error (m/s²)",
                        "kind": "line",
                    },
                    {
                        "key": "normalized_differential_signal",
                        "label": "normalized diff",
                        "kind": "line",
                    },
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
                    {
                        "key": "vibration_phase_rad",
                        "label": "vibration phase (rad)",
                        "kind": "line",
                    },
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
