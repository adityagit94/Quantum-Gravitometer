from __future__ import annotations

import logging
from functools import partial
from typing import Any

import numpy as np

from qgrav.physics import (
    AtomSourceConfig,
    MachZehnderPulseSequence,
    RabiPulseScan,
    equivalent_gravity_error_m_s2,
    gravity_phase_rad,
    gravity_sweep_axis,
    phase_scan_axis,
    port_differential_summary,
    source_summary_rows,
    vibration_amplitude_axis,
    vibration_phase_rad,
)
from qgrav.physics.constants import NOMINAL_GRAVITY, WAVELENGTH_RB87_D2
from qgrav.sim_ai._aisim_overrides import (
    ChirpedWavevectors,
    GravityFreePropagator,
    IntegratedPhaseSpatialSuperpositionTransitionPropagator,
)
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
        from qgrav.vendor import aisim as ais

        return ais
    except Exception:
        logger.exception("Vendored AISim import failed; trying external package")
        try:
            import aisim as ais

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


def _wave_vectors(
    *,
    wavelength_m: float,
    k1_rad_per_m: float | None = None,
    k2_rad_per_m: float | None = None,
    chirp_rate_rad_per_s2: float = 0.0,
):
    k1 = float(k1_rad_per_m) if k1_rad_per_m is not None else 2.0 * np.pi / float(wavelength_m)
    k2 = float(k2_rad_per_m) if k2_rad_per_m is not None else -2.0 * np.pi / float(wavelength_m)
    return ChirpedWavevectors(k1=k1, k2=k2, chirp_rate_rad_per_s2=float(chirp_rate_rad_per_s2))


def _gaussian_beam(*, beam_radius_m: float, center_rabi_freq_hz: float):
    ais = _import_aisim()
    return ais.IntensityProfile(
        r_profile=float(beam_radius_m),
        center_rabi_freq=2.0 * np.pi * float(center_rabi_freq_hz),
    )


def _coerce_zernike_coeffs(raw) -> dict[int, float] | None:
    """Coerce a YAML-supplied Zernike-coefficient mapping to ``{int: float}``.

    YAML may parse the polynomial single-index keys as strings (e.g. ``{"4":
    0.1}``); AISim's ``Wavefront`` expects integer keys.  Returns None for an
    empty/None input.
    """
    if not raw:
        return None
    if not isinstance(raw, dict):
        raise ValueError(
            f"wavefront_zernike_coeffs must be a mapping of {{j: coeff}}; got {type(raw)!r}"
        )
    return {int(j): float(c) for j, c in raw.items()}


def _build_wavefront(
    *,
    wavefront_zernike_coeffs: dict[int, float] | None,
    wavefront_radius_m: float,
) -> object | None:
    """Build an AISim Wavefront object from a Zernike coefficient dict.

    Returns None if ``wavefront_zernike_coeffs`` is None or empty (no aberration).
    """
    if not wavefront_zernike_coeffs:
        return None
    ais = _import_aisim()
    return ais.Wavefront(
        r_wf=float(wavefront_radius_m),
        coeff=dict(wavefront_zernike_coeffs),
    )


def _run_mach_zehnder_sequence(
    atoms0,
    *,
    tau_pi_half_s: float,
    interferometer_time_s: float,
    intensity_profile,
    wave_vectors,
    final_phase_rad: float,
    wavefront=None,
    single_photon_detuning_hz: float = 0.0,
) -> dict[str, float]:
    """Run a three-pulse AISim Mach–Zehnder-style sequence.

    This follows the structure demonstrated in AISim's multiport atom-interferometer
    example using SpatialSuperpositionTransitionPropagator objects for the three pulses.
    The final beam splitter includes an effective phase_scan term, which we use to study
    fringes and gravimeter-relevant phase response.

    ``wavefront`` is an optional AISim Wavefront object that imprints a
    position-dependent phase on each pulse.

    ``single_photon_detuning_hz`` enables the AC Stark / light-shift correction.
    """
    ais = _import_aisim()
    bs1 = IntegratedPhaseSpatialSuperpositionTransitionPropagator(
        float(tau_pi_half_s),
        n_pulse=1,
        n_pulses=3,
        intensity_profile=intensity_profile,
        wave_vectors=wave_vectors,
        wf=wavefront,
        single_photon_detuning_hz=float(single_photon_detuning_hz),
    )
    mirror = IntegratedPhaseSpatialSuperpositionTransitionPropagator(
        2.0 * float(tau_pi_half_s),
        n_pulse=2,
        n_pulses=3,
        intensity_profile=intensity_profile,
        wave_vectors=wave_vectors,
        wf=wavefront,
        single_photon_detuning_hz=float(single_photon_detuning_hz),
    )
    bs2 = IntegratedPhaseSpatialSuperpositionTransitionPropagator(
        float(tau_pi_half_s),
        n_pulse=3,
        n_pulses=3,
        intensity_profile=intensity_profile,
        wave_vectors=wave_vectors,
        phase_scan=float(final_phase_rad),
        wf=wavefront,
        single_photon_detuning_hz=float(single_photon_detuning_hz),
    )
    free_prop = ais.FreePropagator(float(interferometer_time_s))

    atoms = bs1.propagate(atoms0)
    atoms = free_prop.propagate(atoms)
    atoms = mirror.propagate(atoms)
    atoms = free_prop.propagate(atoms)
    atoms = bs2.propagate(atoms)

    port2 = float(np.mean(atoms.state_occupation(2)))
    port3 = float(np.mean(atoms.state_occupation(3)))
    summary = port_differential_summary(
        np.array([port2], dtype=np.float64), np.array([port3], dtype=np.float64)
    )
    return {
        "port_2": port2,
        "port_3": port3,
        "closed_total": float(summary["closed_total"][0]),
        "differential_signal": float(summary["differential_signal"][0]),
        "normalized_differential_signal": float(summary["normalized_differential_signal"][0]),
    }


def _run_mach_zehnder_sequence_with_gravity(
    atoms0,
    *,
    tau_pi_half_s: float,
    interferometer_time_s: float,
    intensity_profile,
    wave_vectors,
    final_phase_rad: float,
    g_m_s2: float,
    gravity_gradient_per_m: float = 0.0,
    z_ref_m: float = 0.0,
    phase_offset_rad: float = 0.0,
    wavefront=None,
    single_photon_detuning_hz: float = 0.0,
) -> dict[str, float]:
    """Run a three-pulse MZ sequence with ballistic gravity propagation.

    Same structure as ``_run_mach_zehnder_sequence`` but replaces
    ``FreePropagator`` with ``GravityFreePropagator``.  The gravity
    phase emerges from the trajectory + chirped laser detuning mismatch
    rather than being injected analytically.

    ``final_phase_rad`` carries only the phase bias (e.g. pi/2 for
    mid-fringe), not the gravity phase.

    ``phase_offset_rad`` is a constant residual offset (computed by
    ``_calibrate_gravity_phase_offset``) that aligns the simulated mode
    with the hybrid mode's fringe centre.  It captures pulse-timing
    artefacts (chirp accumulation during the finite pulse durations)
    that are not present in the idealised analytical formula.

    Notes
    -----
    The AISim ``TwoLevelTransitionPropagator._prop_matrix`` has been patched
    locally to use the physically correct integrated laser phase
    ``-k_eff*z(t0) + 0.5*chirp*t0**2`` instead of the instantaneous
    ``delta * t0`` product.  This makes the MZ combination produce the
    standard atom-interferometry result ``k_eff*(g-g_chirp)*T**2`` for the
    gravity phase, matching the analytical formula used in the hybrid mode.
    """
    _import_aisim()  # fail fast if the vendored AISim cannot be imported
    T = float(interferometer_time_s)

    # Adjust phase_scan by the calibration offset so the simulated and
    # hybrid modes share the same fringe centre at g = g_chirp.
    #
    # The calibration finds the phase_scan value that maximises P3 at
    # g = g_chirp (call it `peak_phi`).  For P3 ~ 0.5(1 + cos(total)),
    # this means the natural-mode total phase at peak is 0:
    #     natural(g_chirp) + peak_phi = 0  =>  natural(g_chirp) = -peak_phi.
    # To make the simulated mode behave like the hybrid at midfringe
    # (total = pi/2 when final_phase_rad = pi/2), we ADD peak_phi to
    # the phase_scan:
    #     total = natural(g_chirp) + (final_phase_rad + peak_phi)
    #           = -peak_phi + final_phase_rad + peak_phi
    #           = final_phase_rad   (matches hybrid)
    corrected_phase_scan = float(final_phase_rad) + float(phase_offset_rad)

    bs1 = IntegratedPhaseSpatialSuperpositionTransitionPropagator(
        float(tau_pi_half_s),
        n_pulse=1,
        n_pulses=3,
        intensity_profile=intensity_profile,
        wave_vectors=wave_vectors,
        wf=wavefront,
        single_photon_detuning_hz=float(single_photon_detuning_hz),
    )
    mirror = IntegratedPhaseSpatialSuperpositionTransitionPropagator(
        2.0 * float(tau_pi_half_s),
        n_pulse=2,
        n_pulses=3,
        intensity_profile=intensity_profile,
        wave_vectors=wave_vectors,
        wf=wavefront,
        single_photon_detuning_hz=float(single_photon_detuning_hz),
    )
    bs2 = IntegratedPhaseSpatialSuperpositionTransitionPropagator(
        float(tau_pi_half_s),
        n_pulse=3,
        n_pulses=3,
        intensity_profile=intensity_profile,
        wave_vectors=wave_vectors,
        phase_scan=corrected_phase_scan,
        wf=wavefront,
        single_photon_detuning_hz=float(single_photon_detuning_hz),
    )
    grav_prop = GravityFreePropagator(
        T,
        g_m_s2=float(g_m_s2),
        gravity_gradient_per_m=float(gravity_gradient_per_m),
        z_ref_m=float(z_ref_m),
    )

    atoms = bs1.propagate(atoms0)
    atoms = grav_prop.propagate(atoms)
    atoms = mirror.propagate(atoms)
    atoms = grav_prop.propagate(atoms)
    atoms = bs2.propagate(atoms)

    port2 = float(np.mean(atoms.state_occupation(2)))
    port3 = float(np.mean(atoms.state_occupation(3)))
    summary = port_differential_summary(
        np.array([port2], dtype=np.float64), np.array([port3], dtype=np.float64)
    )
    return {
        "port_2": port2,
        "port_3": port3,
        "closed_total": float(summary["closed_total"][0]),
        "differential_signal": float(summary["differential_signal"][0]),
        "normalized_differential_signal": float(summary["normalized_differential_signal"][0]),
    }


def bertoldi_finite_tau_scale_factor(
    *,
    tau_pi_half_s: float,
    interferometer_time_s: float,
) -> float:
    """Bertoldi 2019 closed-form finite-τ correction to the MZ gravity phase.

    From Bertoldi, Minardi & Prevedelli, *Phys. Rev. A* **99**, 033619 (2019),
    Eq. 21 (verbatim from `docs/research/RESEARCH_FINITE_TAU_FORMULAS.md`),
    the leading-order multiplicative correction to the Mach–Zehnder gravity
    phase ``Φ = k_eff·g·T²`` is

        Φ → Φ · [ 1 − ((2π − 4)/π) · (τ/T) ]

    where ``τ`` is the π/2-pulse duration and ``T`` is the pulse-CENTER to
    pulse-CENTER interrogation time (consistent with Cheinet 2008, Le Gouët
    2008, Fang/Mielec 2018).  The numerical coefficient is
    ``(2π − 4)/π ≈ 0.7268`` (Shao 2015 obtains the same value; Li/Shao/Hu
    2015 reports a different coefficient that Bertoldi et al. explicitly flag
    as a disagreement).

    The Fang/Mielec 2018 equivalent scale factor ``S_rec = k_eff·(T+τ/2)·(T +
    (4/π − 3/2)·τ)`` agrees with this to first order in η = τ/T.

    Bertoldi Eq. 32's residual single-shot term ``-4·θ²(T)·sin(2φ₂)``
    **averages to zero over the velocity distribution** (per the research
    F14 note), so for an ensemble simulation this multiplicative factor is
    the complete correction at leading order.

    Returns the scale-factor multiplier (typically slightly less than 1).
    """
    tau = float(tau_pi_half_s)
    T = float(interferometer_time_s)
    if T <= 0:
        raise ValueError("interferometer_time_s must be > 0")
    eta = tau / T
    coeff = (2.0 * np.pi - 4.0) / np.pi  # ~ 0.72676
    return 1.0 - coeff * eta


def _calibrate_gravity_phase_offset(
    atoms0,
    *,
    tau_pi_half_s: float,
    interferometer_time_s: float,
    intensity_profile,
    wave_vectors,
    g_chirp_m_s2: float,
    gravity_gradient_per_m: float = 0.0,
    z_ref_m: float = 0.0,
    n_calibration_phases: int = 73,
) -> float:
    """Determine the constant phase offset between simulated and hybrid modes.

    At ``g = g_chirp`` (the gravity the laser chirp is tuned to track), the
    gravity contribution to the MZ phase should vanish, leaving only
    pulse-timing residuals (chirp accumulated during finite-duration pulses).
    These residuals manifest as a constant offset that shifts the fringe.

    This function runs a fringe scan at ``g = g_chirp`` and identifies the
    phase_scan value that gives maximum P3 minus pi (since the hybrid mode
    has its peak at phase_scan = 0 when no gravity phase is applied).
    Subtracting this offset from subsequent phase_scan inputs aligns the
    simulated fringe with the hybrid fringe.

    The calibration uses the same ensemble as the main sweep so that
    thermal-velocity averaging is consistent.  The cost is one full
    fringe scan (~70 MZ sequences), independent of the main sweep size.

    Returns the offset in radians.
    """
    offset, _visibility = _calibrate_gravity_phase_and_visibility(
        atoms0,
        tau_pi_half_s=tau_pi_half_s,
        interferometer_time_s=interferometer_time_s,
        intensity_profile=intensity_profile,
        wave_vectors=wave_vectors,
        g_chirp_m_s2=g_chirp_m_s2,
        gravity_gradient_per_m=gravity_gradient_per_m,
        z_ref_m=z_ref_m,
        n_calibration_phases=n_calibration_phases,
    )
    return offset


def _calibrate_gravity_phase_and_visibility(
    atoms0,
    *,
    tau_pi_half_s: float,
    interferometer_time_s: float,
    intensity_profile,
    wave_vectors,
    g_chirp_m_s2: float,
    gravity_gradient_per_m: float = 0.0,
    z_ref_m: float = 0.0,
    n_calibration_phases: int = 73,
) -> tuple[float, float]:
    """Calibration fringe scan returning ``(phase_offset_rad, visibility)``.

    Runs one MZ fringe scan at ``g = g_chirp`` (where the gravity phase
    vanishes) and fits a sinusoid ``P3 = offset + A*cos(phi - peak_phi)``.

    Returns
    -------
    (phase_offset_rad, visibility) where ``phase_offset_rad = peak_phi mod 2pi``
    is the residual pulse-timing offset and ``visibility = 2*A`` is the fringe
    contrast (P3 swings over ``0.5*(1 +/- visibility)`` for offset ~ 0.5),
    clipped to [0, 1].  The visibility is used to invert P3 -> g without
    assuming an ideal contrast of 1.
    """
    phis = np.linspace(0.0, 2.0 * np.pi, int(n_calibration_phases), endpoint=False)
    p3_values = np.empty_like(phis)
    for i, phi in enumerate(phis):
        result = _run_mach_zehnder_sequence_with_gravity(
            atoms0,
            tau_pi_half_s=tau_pi_half_s,
            interferometer_time_s=interferometer_time_s,
            intensity_profile=intensity_profile,
            wave_vectors=wave_vectors,
            final_phase_rad=float(phi),
            g_m_s2=float(g_chirp_m_s2),
            gravity_gradient_per_m=float(gravity_gradient_per_m),
            z_ref_m=float(z_ref_m),
            phase_offset_rad=0.0,  # no offset during calibration
        )
        p3_values[i] = result["port_3"]
    # Sinusoidal fit gives a robust estimate of the peak phase even with
    # ensemble noise.  Model: y = offset + A*cos(x - peak_phi) where the
    # peak of P3 lies at x = peak_phi.  The fit returns
    # `phase_offset_rad = arctan2(-c_sin, c_cos) = -peak_phi`, so we negate.
    fit = _fit_sinusoid(phis, p3_values)
    peak_phi = -float(fit["phase_offset_rad"])
    offset_rad = float(np.mod(peak_phi, 2.0 * np.pi))
    # Contrast V such that P3 = 0.5*(1 +/- V): V = 2*amplitude (offset ~ 0.5).
    visibility = float(np.clip(2.0 * float(fit["amplitude"]), 0.0, 1.0))
    return offset_rad, visibility


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


def _hybrid_gravity_phase_rad(
    *, g_m_s2: np.ndarray, k_eff_rad_per_m: float, T_s: float, phase_bias_rad: float
) -> np.ndarray:
    return gravity_phase_rad(
        g_m_s2,
        k_eff_rad_per_m=k_eff_rad_per_m,
        interferometer_time_s=T_s,
        phase_bias_rad=phase_bias_rad,
    )


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
        summary_rows["All truth checks passed"] = bool(truth["all_passed"])
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
) -> dict[str, Any]:
    if n_gravity_points < 5:
        raise ValueError("n_gravity_points must be at least 5.")
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


def _multi_drop_noise_description(
    detection_noise_enabled: bool,
    detection_sigma_p: float | None,
    raman_phase_noise_rad: float,
    correlated_vibration: bool,
    seismic_model: str,
) -> str:
    """Human-readable summary of the active noise terms in a multi-drop run."""
    terms = []
    if detection_noise_enabled:
        if detection_sigma_p is not None and detection_sigma_p > 0:
            terms.append(f"technical detection sigma_P={detection_sigma_p:.1e}")
        else:
            terms.append("projection detection (sigma=1/sqrt(N_det))")
    if raman_phase_noise_rad > 0:
        terms.append(f"Raman phase noise {raman_phase_noise_rad:.1e} rad/shot")
    if correlated_vibration:
        terms.append(f"correlated seismic vibration ({seismic_model})")
    return "; ".join(terms) if terms else "none"


def _allan_deviation(
    g_values: np.ndarray,
    cycle_time_s: float,
    *,
    max_levels: int = 10,
) -> tuple[np.ndarray, np.ndarray]:
    """Compute the overlapping Allan deviation of a g time-series.

    Parameters
    ----------
    g_values : 1-D array
        Gravity estimates from N drops.
    cycle_time_s : float
        Time between consecutive drops, in seconds (= τ₀).
    max_levels : int
        Maximum number of octave levels to compute.

    Returns
    -------
    (taus, adev) : tuple of 1-D arrays.
        ``taus`` is the integration time at each level (in seconds).
        ``adev`` is the Allan deviation in m/s² at each level.
    """
    x = np.asarray(g_values, dtype=np.float64)
    n = len(x)
    if n < 4:
        return np.array([cycle_time_s]), np.array([float(np.std(x))])
    taus: list[float] = []
    adevs: list[float] = []
    m = 1
    while m <= n // 2 and len(taus) < max_levels:
        # Group into blocks of size m, average each block
        n_blocks = n // m
        blocks = x[: n_blocks * m].reshape(n_blocks, m).mean(axis=1)
        if len(blocks) < 2:
            break
        # Allan variance estimator: σ²_A(τ) = 1/(2(N-1)) Σ (y_{k+1} - y_k)²
        diffs = np.diff(blocks)
        var_a = 0.5 * float(np.mean(diffs**2))
        taus.append(m * cycle_time_s)
        adevs.append(float(np.sqrt(var_a)))
        m *= 2
    return np.asarray(taus, dtype=np.float64), np.asarray(adevs, dtype=np.float64)


def run_aisim_multi_drop_cycle(
    *,
    n_drops: int = 100,
    cycle_time_s: float = 1.0,
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
    k1_rad_per_m: float | None = None,
    k2_rad_per_m: float | None = None,
    tau_pi_half_s: float = 23e-6,
    interferometer_time_s: float = 260e-3,
    gravity_true_m_s2: float = NOMINAL_GRAVITY.value,
    gravity_propagation: bool = True,
    gravity_gradient_per_m: float = 0.0,
    detection_noise_enabled: bool = True,
    n_detected_per_drop: int | None = None,
    detection_sigma_p: float | None = None,
    raman_phase_noise_rad: float = 0.0,
    correlated_vibration: bool = False,
    seismic_model: str = "nlnm",
    vibration_isolation_cutoff_hz: float = 0.0,
    vibration_seed: int | None = None,
    fit_visibility: bool = False,
    servo_enabled: bool = False,
    servo_type: str = "integrator",
    servo_gain: float = 0.5,
    servo_kp: float = 0.5,
    servo_ki: float = 0.1,
    servo_kd: float = 0.0,
) -> dict[str, Any]:
    """Run a multi-drop gravimeter measurement cycle.

    Simulates ``n_drops`` independent drops at a cycle time of ``cycle_time_s``,
    each producing one gravity estimate by reading out the MZ population at
    the operating point.  Optionally adds detection noise and an integrator
    servo that locks the phase bias to mid-fringe.

    Each drop uses a fresh atom ensemble (seed = ``seed + i``) for true
    statistical independence.

    Parameters
    ----------
    n_drops : int
        Number of drops in the cycle (typically 100-1000).
    cycle_time_s : float
        Time between drops, in seconds.  Sets the noise integration cadence.
    gravity_true_m_s2 : float
        The actual gravity value to simulate (the "truth").
    gravity_propagation : bool
        If True, use the fully-simulated mode (gravity emerges from
        trajectory + chirped laser).  If False, use the hybrid mode.
    detection_noise_enabled : bool
        If True, add detection noise to each drop's P3.
    n_detected_per_drop : int, optional
        Number of atoms detected per drop (sets sigma = 1/sqrt(N)).  Defaults
        to ``n_atoms``.
    detection_sigma_p : float, optional
        If set, overrides the 1/sqrt(N) projection-noise model with an explicit
        technical detection-noise standard deviation on P3.  Use this to model
        instruments that are technically-limited rather than projection-limited
        (e.g. GAIN/Freier 2016, where sigma_P ~ 6e-3 >> 1/sqrt(N)).
    raman_phase_noise_rad : float
        Per-shot Gaussian standard deviation (rad) added to the interferometer
        phase, modelling Raman-laser phase noise.
    correlated_vibration : bool
        If True, generate a single seismic acceleration time-series for the
        whole campaign (Peterson ``seismic_model`` with optional isolation
        ``vibration_isolation_cutoff_hz``) and add the per-drop vibration phase
        ``k_eff*[z(0) - 2 z(T) + z(2T)]`` sampled at each drop's pulse times.
        Unlike per-drop white noise this produces realistic low-frequency
        (random-walk/flicker) structure in the Allan deviation.
    fit_visibility : bool
        If True (simulated mode only), estimate the fringe contrast from the
        calibration scan and use it in the P3 -> g inversion instead of
        assuming an ideal contrast of 1.
    servo_enabled : bool
        If True, run a fringe-locking servo on the phase bias between drops.
    servo_type : str
        ``"integrator"`` (default, pure-I, uses ``servo_gain``) or ``"pid"``
        (uses ``servo_kp``/``servo_ki``/``servo_kd`` with anti-windup).

    Returns
    -------
    dict with keys including ``g_estimates_m_s2``, ``timestamps_s``,
    ``mean_g_m_s2``, ``std_g_m_s2``, ``allan_taus_s``, ``allan_dev_m_s2``,
    plus the usual metadata.
    """
    from qgrav.physics.noise_models import add_detection_noise
    from qgrav.physics.readout_models import (
        PIDServoState,
        servo_integrator_step,
        servo_pid_step,
    )

    n = int(n_drops)
    if n < 1:
        raise ValueError("n_drops must be >= 1")
    if cycle_time_s <= 0:
        raise ValueError("cycle_time_s must be > 0")
    if n_detected_per_drop is None:
        n_detected_per_drop = int(n_atoms)
    # Effective detected-atom count for the detection-noise sigma.  If an
    # explicit technical sigma_P is given, convert it to the equivalent N so
    # the existing add_detection_noise(sigma = 1/sqrt(N)) machinery is reused.
    if detection_sigma_p is not None and detection_sigma_p > 0:
        n_detected_effective = int(round(1.0 / float(detection_sigma_p) ** 2))
    else:
        n_detected_effective = int(n_detected_per_drop)

    # Precompute beam, wavevectors, etc. (shared across drops)
    intensity_profile = _gaussian_beam(
        beam_radius_m=beam_radius_m, center_rabi_freq_hz=center_rabi_freq_hz
    )
    wv_tmp = _wave_vectors(
        wavelength_m=wavelength_m, k1_rad_per_m=k1_rad_per_m, k2_rad_per_m=k2_rad_per_m
    )
    k_eff = float(wv_tmp.k1 - wv_tmp.k2)
    T = float(interferometer_time_s)

    if gravity_propagation:
        chirp_rate = -k_eff * float(gravity_true_m_s2)
        wave_vectors = _wave_vectors(
            wavelength_m=wavelength_m,
            k1_rad_per_m=k1_rad_per_m,
            k2_rad_per_m=k2_rad_per_m,
            chirp_rate_rad_per_s2=chirp_rate,
        )
        phase_bias_base = float(np.pi / 2.0)
    else:
        wave_vectors = wv_tmp
        # Hybrid: phase_bias includes the gravity term to lock to mid-fringe at g_true
        phase_bias_base = float(np.pi / 2.0 - k_eff * float(gravity_true_m_s2) * T**2)

    # Calibrate the offset once for the simulated mode (uses an arbitrary
    # ensemble; offset depends only on chirp/T/tau).  Optionally also fit the
    # fringe contrast for a more accurate P3 -> g inversion.
    sim_phase_offset = 0.0
    visibility_estimate = 1.0  # default; refined below if fit_visibility
    if gravity_propagation:
        _, cal_atoms, _, _, _ = _create_detected_ensemble(
            n_atoms=int(n_atoms),
            seed=int(seed),
            cloud_radius_m=cloud_radius_m,
            temp_xy_K=temp_xy_K,
            temp_z_K=temp_z_K,
            detector_time_s=detector_time_s,
            detector_radius_m=detector_radius_m,
            multiport=True,
        )
        sim_phase_offset, fitted_visibility = _calibrate_gravity_phase_and_visibility(
            cal_atoms,
            tau_pi_half_s=tau_pi_half_s,
            interferometer_time_s=interferometer_time_s,
            intensity_profile=intensity_profile,
            wave_vectors=wave_vectors,
            g_chirp_m_s2=float(gravity_true_m_s2),
            gravity_gradient_per_m=float(gravity_gradient_per_m),
        )
        if fit_visibility and fitted_visibility > 1e-3:
            visibility_estimate = fitted_visibility

    # Fringe slope for inverting P3 -> g.  At mid-fringe,
    # P3 ≈ 0.5 - 0.5·V·k_eff·δg·T²  (V = fringe contrast).
    fringe_slope_per_m_s2 = -0.5 * visibility_estimate * k_eff * T**2

    # Pre-generate the correlated seismic vibration phase per drop, if enabled.
    # phi_vib(drop i) = k_eff*[z(t_i) - 2 z(t_i+T) + z(t_i+2T)] where z is the
    # mirror displacement time-series and t_i = i*cycle_time.
    vib_phase_per_drop = np.zeros(n, dtype=np.float64)
    if correlated_vibration:
        from qgrav.physics.noise_models import generate_vibration_timeseries

        # Need samples at t_i, t_i+T, t_i+2T for every drop.  Sample fast enough
        # that T and 2T land near grid points; use 1 ms resolution or finer.
        vib_sample_rate_hz = max(1.0 / cycle_time_s * 4.0, 1.0 / max(T, 1e-3) * 8.0, 50.0)
        vib_duration_s = (n - 1) * cycle_time_s + 2.0 * T + 1.0
        vib_ts = generate_vibration_timeseries(
            duration_s=float(vib_duration_s),
            sample_rate_hz=float(vib_sample_rate_hz),
            seismic_model=str(seismic_model),
            isolation_cutoff_hz=float(vibration_isolation_cutoff_hz),
            seed=(int(vibration_seed) if vibration_seed is not None else int(seed) + 99_000),
        )
        z_disp = vib_ts["displacement_m"]

        def _z_at(t):
            idx = int(round(float(t) * vib_sample_rate_hz))
            idx = max(0, min(len(z_disp) - 1, idx))
            return float(z_disp[idx])

        for i in range(n):
            t_i = i * float(cycle_time_s)
            z0 = _z_at(t_i)
            zT = _z_at(t_i + T)
            z2T = _z_at(t_i + 2.0 * T)
            vib_phase_per_drop[i] = k_eff * (z0 - 2.0 * zT + z2T)

    # Per-shot Raman phase-noise stream (deterministic from seed).
    raman_rng = np.random.default_rng(int(seed) + 77_000)
    raman_phase_per_drop = (
        raman_rng.normal(0.0, float(raman_phase_noise_rad), size=n)
        if raman_phase_noise_rad > 0
        else np.zeros(n, dtype=np.float64)
    )

    # Run the drops
    g_estimates = np.zeros(n, dtype=np.float64)
    timestamps = np.arange(n, dtype=np.float64) * float(cycle_time_s)
    p3_raw = np.zeros(n, dtype=np.float64)
    p3_noisy = np.zeros(n, dtype=np.float64)

    # Servo state
    servo_phase_correction = 0.0
    pid_state = PIDServoState()

    for i in range(n):
        # Fresh ensemble per drop (true independence)
        _, drop_atoms, _, _, _ = _create_detected_ensemble(
            n_atoms=int(n_atoms),
            seed=int(seed) + i + 1,
            cloud_radius_m=cloud_radius_m,
            temp_xy_K=temp_xy_K,
            temp_z_K=temp_z_K,
            detector_time_s=detector_time_s,
            detector_radius_m=detector_radius_m,
            multiport=True,
        )
        # Total phase bias = operating point + servo correction + physical
        # perturbations (correlated vibration + Raman phase noise).
        phase_bias_drop = (
            phase_bias_base
            + servo_phase_correction
            + float(vib_phase_per_drop[i])
            + float(raman_phase_per_drop[i])
        )
        if gravity_propagation:
            out = _run_mach_zehnder_sequence_with_gravity(
                drop_atoms,
                tau_pi_half_s=tau_pi_half_s,
                interferometer_time_s=interferometer_time_s,
                intensity_profile=intensity_profile,
                wave_vectors=wave_vectors,
                final_phase_rad=phase_bias_drop,
                g_m_s2=float(gravity_true_m_s2),
                gravity_gradient_per_m=float(gravity_gradient_per_m),
                phase_offset_rad=sim_phase_offset,
            )
        else:
            out = _run_mach_zehnder_sequence(
                drop_atoms,
                tau_pi_half_s=tau_pi_half_s,
                interferometer_time_s=interferometer_time_s,
                intensity_profile=intensity_profile,
                wave_vectors=wave_vectors,
                final_phase_rad=phase_bias_drop,
            )
        p3_raw[i] = out["port_3"]

        # Apply detection noise (technical sigma_P if given, else 1/sqrt(N)).
        if detection_noise_enabled:
            noisy = add_detection_noise(
                np.array([p3_raw[i]]),
                n_detected=int(n_detected_effective),
                seed=int(seed) + 10_000 + i,
            )
            p3_noisy[i] = float(noisy[0])
        else:
            p3_noisy[i] = p3_raw[i]

        # Extract g estimate by inverting the mid-fringe linearisation:
        # P3 = 0.5 + slope·(g - g_setpoint), so g_est = g_setpoint + (P3 - 0.5)/slope
        if fringe_slope_per_m_s2 != 0:
            g_est = float(gravity_true_m_s2) + (p3_noisy[i] - 0.5) / fringe_slope_per_m_s2
        else:
            g_est = float(gravity_true_m_s2)
        g_estimates[i] = g_est

        # Servo update
        if servo_enabled:
            if str(servo_type).lower() == "pid":
                pid_state = servo_pid_step(
                    pid_state,
                    population=p3_noisy[i],
                    setpoint=0.5,
                    kp=float(servo_kp),
                    ki=float(servo_ki),
                    kd=float(servo_kd),
                )
                servo_phase_correction = pid_state.phase_estimate
            else:
                servo_phase_correction = servo_integrator_step(
                    population=p3_noisy[i],
                    phase_estimate=servo_phase_correction,
                    setpoint=0.5,
                    gain=float(servo_gain),
                )

    # Statistics
    mean_g = float(np.mean(g_estimates))
    std_g = float(np.std(g_estimates))
    taus, adev = _allan_deviation(g_estimates, float(cycle_time_s))

    # Determine study scope based on whether we use fully-simulated MZ
    if gravity_propagation:
        study_scope = "fully_simulated_multi_drop_cycle"
    else:
        study_scope = "hybrid_aisim_plus_closed_form_multi_drop_cycle"
    category, description = _classify_study_scope(study_scope)

    return {
        "backend": "aisim",
        "model": "multi_drop_cycle",
        "study_type": "multi_drop_cycle",
        "n_drops": int(n),
        "cycle_time_s": float(cycle_time_s),
        "gravity_true_m_s2": float(gravity_true_m_s2),
        "gravity_propagation": bool(gravity_propagation),
        "detection_noise_enabled": bool(detection_noise_enabled),
        "n_detected_per_drop": int(n_detected_per_drop),
        "n_detected_effective": int(n_detected_effective),
        "detection_sigma_p": (None if detection_sigma_p is None else float(detection_sigma_p)),
        "raman_phase_noise_rad": float(raman_phase_noise_rad),
        "correlated_vibration": bool(correlated_vibration),
        "visibility_estimate": float(visibility_estimate),
        "servo_enabled": bool(servo_enabled),
        "servo_type": str(servo_type),
        "g_estimates_m_s2": g_estimates,
        "timestamps_s": timestamps,
        "port_3_raw": p3_raw,
        "port_3_noisy": p3_noisy,
        "vibration_phase_rad": vib_phase_per_drop,
        "mean_g_m_s2": mean_g,
        "std_g_m_s2": std_g,
        "mean_minus_true_m_s2": mean_g - float(gravity_true_m_s2),
        "allan_taus_s": taus,
        "allan_dev_m_s2": adev,
        "interferometer_time_s": float(interferometer_time_s),
        "tau_pi_half_s": float(tau_pi_half_s),
        "k_eff_rad_per_m": k_eff,
        "study_scope": study_scope,
        "study_scope_category": category,
        "study_scope_description": description,
        "physical_model": {
            "ensemble": f"fresh ensemble per drop (seed={seed}+i)",
            "atom_optics": "AISim SpatialSuperpositionTransitionPropagator three-pulse MZ",
            "noise": _multi_drop_noise_description(
                detection_noise_enabled,
                detection_sigma_p,
                raman_phase_noise_rad,
                correlated_vibration,
                seismic_model,
            ),
            "feedback": (f"{servo_type} servo on phase bias" if servo_enabled else "open loop"),
        },
        "limitations": [
            (
                "Drop-to-drop correlations modelled only via the optional "
                "correlated seismic vibration; laser-frequency / magnetic / "
                "thermal drifts are not yet modelled."
            ),
            (
                "Servo is integrator or PID with anti-windup; no non-linear "
                "or feed-forward corrections."
            ),
            (
                "P3->g inversion uses a linear mid-fringe model with the "
                "(optionally fitted) contrast; large excursions are not "
                "re-linearised."
            ),
        ],
    }


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
