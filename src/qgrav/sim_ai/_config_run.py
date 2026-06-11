"""YAML-config dispatcher mapping `model:` to the study functions (moved verbatim from ``aisim_adapter.py`` in the v1.4
modularisation; the physics is unchanged). Re-exported by
:mod:`qgrav.sim_ai.aisim_adapter`, which remains the public import path."""

from __future__ import annotations

import logging
from typing import Any

import numpy as np

from qgrav.physics.constants import NOMINAL_GRAVITY, WAVELENGTH_RB87_D2
from qgrav.sim_ai._adapter_core import (
    _coerce_zernike_coeffs,
)
from qgrav.sim_ai._multi_drop import run_aisim_multi_drop_cycle
from qgrav.sim_ai._scans import run_aisim_mach_zehnder_phase_scan, run_aisim_rabi_scan
from qgrav.sim_ai._sweeps import (
    run_aisim_gravity_sweep,
    run_aisim_vibration_sensitivity_sweep,
)

logger = logging.getLogger(__name__)


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
        k1_rad_per_m=(
            None if sim_cfg.get("k1_rad_per_m") is None else float(sim_cfg.get("k1_rad_per_m"))
        ),
        k2_rad_per_m=(
            None if sim_cfg.get("k2_rad_per_m") is None else float(sim_cfg.get("k2_rad_per_m"))
        ),
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
            single_photon_detuning_hz=float(sim_cfg.get("single_photon_detuning_hz", 0.0)),
            wavefront_zernike_coeffs=_coerce_zernike_coeffs(
                sim_cfg.get("wavefront_zernike_coeffs")
            ),
            wavefront_radius_m=float(sim_cfg.get("wavefront_radius_m", 0.05)),
        )
    if model == "gravity_sweep":
        return run_aisim_gravity_sweep(
            **common,
            tau_pi_half_s=float(sim_cfg.get("tau_pi_half_s", 23e-6)),
            interferometer_time_s=float(sim_cfg.get("interferometer_time_s", 260e-3)),
            gravity_center_m_s2=float(sim_cfg.get("gravity_center_m_s2", NOMINAL_GRAVITY.value)),
            gravity_span_m_s2=float(sim_cfg.get("gravity_span_m_s2", 6.0e-6)),
            n_gravity_points=int(sim_cfg.get("n_gravity_points", 61)),
            phase_bias_rad=(
                None
                if sim_cfg.get("phase_bias_rad") is None
                else float(sim_cfg.get("phase_bias_rad"))
            ),
            lock_to_midfringe=bool(sim_cfg.get("lock_to_midfringe", True)),
            gravity_propagation=bool(sim_cfg.get("gravity_propagation", False)),
            gravity_gradient_per_m=float(sim_cfg.get("gravity_gradient_per_m", 0.0)),
            single_photon_detuning_hz=float(sim_cfg.get("single_photon_detuning_hz", 0.0)),
            wavefront_zernike_coeffs=_coerce_zernike_coeffs(
                sim_cfg.get("wavefront_zernike_coeffs")
            ),
            wavefront_radius_m=float(sim_cfg.get("wavefront_radius_m", 0.05)),
            raman_substeps=int(sim_cfg.get("raman_substeps", 1)),
        )
    if model == "multi_drop_cycle":
        return run_aisim_multi_drop_cycle(
            **common,
            tau_pi_half_s=float(sim_cfg.get("tau_pi_half_s", 23e-6)),
            interferometer_time_s=float(sim_cfg.get("interferometer_time_s", 260e-3)),
            gravity_true_m_s2=float(sim_cfg.get("gravity_true_m_s2", NOMINAL_GRAVITY.value)),
            gravity_propagation=bool(sim_cfg.get("gravity_propagation", True)),
            gravity_gradient_per_m=float(sim_cfg.get("gravity_gradient_per_m", 0.0)),
            n_drops=int(sim_cfg.get("n_drops", 100)),
            cycle_time_s=float(sim_cfg.get("cycle_time_s", 1.0)),
            detection_noise_enabled=bool(sim_cfg.get("detection_noise_enabled", True)),
            n_detected_per_drop=(
                None
                if sim_cfg.get("n_detected_per_drop") is None
                else int(sim_cfg.get("n_detected_per_drop"))
            ),
            # Phase 15 noise machinery (all default to off).
            detection_sigma_p=(
                None
                if sim_cfg.get("detection_sigma_p") is None
                else float(sim_cfg.get("detection_sigma_p"))
            ),
            raman_phase_noise_rad=float(sim_cfg.get("raman_phase_noise_rad", 0.0)),
            correlated_vibration=bool(sim_cfg.get("correlated_vibration", False)),
            seismic_model=str(sim_cfg.get("seismic_model", "nlnm")),
            vibration_isolation_cutoff_hz=float(sim_cfg.get("vibration_isolation_cutoff_hz", 0.0)),
            vibration_seed=(
                None
                if sim_cfg.get("vibration_seed") is None
                else int(sim_cfg.get("vibration_seed"))
            ),
            fit_visibility=bool(sim_cfg.get("fit_visibility", False)),
            servo_enabled=bool(sim_cfg.get("servo_enabled", False)),
            servo_type=str(sim_cfg.get("servo_type", "integrator")),
            servo_gain=float(sim_cfg.get("servo_gain", 0.5)),
            servo_kp=float(sim_cfg.get("servo_kp", 0.5)),
            servo_ki=float(sim_cfg.get("servo_ki", 0.1)),
            servo_kd=float(sim_cfg.get("servo_kd", 0.0)),
            raman_substeps=int(sim_cfg.get("raman_substeps", 1)),
            projection_noise=bool(sim_cfg.get("projection_noise", False)),
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
            phase_bias_rad=(
                None
                if sim_cfg.get("phase_bias_rad") is None
                else float(sim_cfg.get("phase_bias_rad"))
            ),
            lock_to_midfringe=bool(sim_cfg.get("lock_to_midfringe", True)),
            gravity_propagation=bool(sim_cfg.get("gravity_propagation", False)),
            gravity_gradient_per_m=float(sim_cfg.get("gravity_gradient_per_m", 0.0)),
        )
    raise ValueError(f"Unsupported AISim model: {model}")
