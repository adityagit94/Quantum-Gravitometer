"""Shared low-level helpers for the AISim adapter (moved verbatim from
``aisim_adapter.py`` in the v1.4 modularisation; the physics is unchanged).

Everything here is re-exported by :mod:`qgrav.sim_ai.aisim_adapter`, which
remains the public import path.
"""

from __future__ import annotations

import logging
from functools import partial
from typing import Any

import numpy as np

from qgrav.physics import (
    AtomSourceConfig,
    gravity_phase_rad,
    port_differential_summary,
    source_summary_rows,
    vibration_phase_rad,
)
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
    raman_substeps: int = 1,
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

    # Sub-pulse integration (raman_substeps > 1) needs the gravity parameters
    # inside each pulse so the atoms keep falling during the slices.
    _substep_kwargs = dict(
        raman_substeps=int(raman_substeps),
        substep_g_m_s2=float(g_m_s2),
        substep_gravity_gradient_per_m=float(gravity_gradient_per_m),
        substep_z_ref_m=float(z_ref_m),
    )

    bs1 = IntegratedPhaseSpatialSuperpositionTransitionPropagator(
        float(tau_pi_half_s),
        n_pulse=1,
        n_pulses=3,
        intensity_profile=intensity_profile,
        wave_vectors=wave_vectors,
        wf=wavefront,
        single_photon_detuning_hz=float(single_photon_detuning_hz),
        **_substep_kwargs,
    )
    mirror = IntegratedPhaseSpatialSuperpositionTransitionPropagator(
        2.0 * float(tau_pi_half_s),
        n_pulse=2,
        n_pulses=3,
        intensity_profile=intensity_profile,
        wave_vectors=wave_vectors,
        wf=wavefront,
        single_photon_detuning_hz=float(single_photon_detuning_hz),
        **_substep_kwargs,
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
        **_substep_kwargs,
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
    raman_substeps: int = 1,
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
        raman_substeps=raman_substeps,
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
    raman_substeps: int = 1,
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
            raman_substeps=int(raman_substeps),
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
