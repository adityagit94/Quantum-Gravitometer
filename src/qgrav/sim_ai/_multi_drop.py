"""Multi-drop measurement-cycle study (noise budget, servo, Allan) (moved verbatim from ``aisim_adapter.py`` in the v1.4
modularisation; the physics is unchanged). Re-exported by
:mod:`qgrav.sim_ai.aisim_adapter`, which remains the public import path."""

from __future__ import annotations

import logging
from typing import Any

import numpy as np

from qgrav.physics.constants import NOMINAL_GRAVITY, WAVELENGTH_RB87_D2
from qgrav.sim_ai._adapter_core import (
    _calibrate_gravity_phase_and_visibility,
    _classify_study_scope,
    _create_detected_ensemble,
    _gaussian_beam,
    _run_mach_zehnder_sequence,
    _run_mach_zehnder_sequence_with_gravity,
    _wave_vectors,
)

logger = logging.getLogger(__name__)


def _multi_drop_noise_description(
    detection_noise_enabled: bool,
    detection_sigma_p: float | None,
    raman_phase_noise_rad: float,
    correlated_vibration: bool,
    seismic_model: str,
    projection_noise: bool = False,
) -> str:
    """Human-readable summary of the active noise terms in a multi-drop run."""
    terms = []
    if projection_noise:
        terms.append("quantum projection noise (binomial per-atom readout)")
        if detection_noise_enabled and detection_sigma_p is not None and detection_sigma_p > 0:
            terms.append(f"technical detection sigma_P={detection_sigma_p:.1e}")
    elif detection_noise_enabled:
        if detection_sigma_p is not None and detection_sigma_p > 0:
            terms.append(f"technical detection sigma_P={detection_sigma_p:.1e}")
        else:
            terms.append("projection detection (Gaussian sigma=1/sqrt(N_det))")
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

    Octave-spaced integration times; the estimator matches
    :func:`qgrav.metrics.allan.allan_deviation_overlapping` (custom backend)
    evaluated at the same taus.

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
    csum = np.concatenate([[0.0], np.cumsum(x, dtype=np.float64)])
    m = 1
    while m <= n // 2 and len(taus) < max_levels:
        # Overlapping estimator (unit stride): all length-m window means, then
        # σ²_A(m·τ₀) = 1/(2(N-2m+1)) Σ_j (ȳ_{j+m} - ȳ_j)²
        window_means = (csum[m:] - csum[:-m]) / m
        diffs = window_means[m:] - window_means[:-m]
        if len(diffs) < 1:
            break
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
    servo_settle_drops: int = 0,
    raman_substeps: int = 1,
    projection_noise: bool = False,
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
    projection_noise : bool
        If True, the per-drop readout draws the detected excited-state count
        from ``Binomial(n_detected_per_drop, P3)`` (seeded from the run's
        RNG stream), so quantum projection noise *emerges* from single-atom
        statistics instead of being injected as a configured Gaussian.
        Composition order: the binomial draw happens FIRST (it is the
        measurement physics); an explicit technical ``detection_sigma_p``
        then adds on top of ``P_hat``.  The legacy default Gaussian
        ``sigma = 1/sqrt(N)`` draw is skipped when this flag is on (it
        approximates the same physics and would double-count QPN).
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
    servo_settle_drops : int
        Number of initial drops treated as servo acquisition and excluded
        from the summary statistics (``mean_g_m_s2``, ``std_g_m_s2``) and
        the Allan deviation.  The full per-drop series (including the
        settle segment) is still returned in ``g_estimates_m_s2`` /
        ``timestamps_s``.  Default 0 (no exclusion) preserves the
        historical behaviour.

    Returns
    -------
    dict with keys including ``g_estimates_m_s2``, ``timestamps_s``,
    ``mean_g_m_s2``, ``std_g_m_s2``, ``allan_taus_s``, ``allan_dev_m_s2``,
    plus the usual metadata.  When ``servo_settle_drops`` > 0 the summary
    statistics and Allan arrays describe the locked segment only.
    """
    from qgrav.physics.noise_models import add_detection_noise
    from qgrav.physics.readout_models import (
        PIDServoState,
        binomial_projection_readout,
        servo_integrator_step,
        servo_pid_step,
    )

    n = int(n_drops)
    if n < 1:
        raise ValueError("n_drops must be >= 1")
    if cycle_time_s <= 0:
        raise ValueError("cycle_time_s must be > 0")
    if int(raman_substeps) < 1:
        raise ValueError("raman_substeps must be >= 1.")
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
            raman_substeps=int(raman_substeps),
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

        # Need samples at t_i, t_i+T, t_i+2T for every drop.  Sample at >=8
        # points per T and >=4 per cycle (>=50 Hz floor); _z_at interpolates
        # linearly between grid samples so arbitrary T stays exact.
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
            ft = float(t) * vib_sample_rate_hz
            i0 = max(0, min(len(z_disp) - 2, int(np.floor(ft))))
            frac = ft - i0
            return float((1.0 - frac) * z_disp[i0] + frac * z_disp[i0 + 1])

        for i in range(n):
            t_i = i * float(cycle_time_s)
            z0 = _z_at(t_i)
            zT = _z_at(t_i + T)
            z2T = _z_at(t_i + 2.0 * T)
            vib_phase_per_drop[i] = k_eff * (z0 - 2.0 * zT + z2T)

    # Per-shot quantum-projection-noise stream (deterministic from seed,
    # same discipline as the Raman / vibration streams below).
    projection_rng = np.random.default_rng(int(seed) + 88_000)

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
                raman_substeps=int(raman_substeps),
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

        # Readout-noise composition (order matters and is documented in the
        # docstring): quantum projection noise is drawn FIRST — it is the
        # physics of the measurement, k ~ Binomial(N_det, P) — and any
        # configured TECHNICAL detection noise (explicit detection_sigma_p)
        # adds on top of the projected P_hat.  When projection_noise is on,
        # the legacy default Gaussian sigma = 1/sqrt(N) draw is skipped:
        # it is the Gaussian approximation of the same physics and keeping
        # both would double-count QPN.
        if projection_noise:
            p_hat = binomial_projection_readout(
                p3_raw[i], int(n_detected_per_drop), rng=projection_rng
            )
            if detection_noise_enabled and detection_sigma_p is not None and detection_sigma_p > 0:
                noisy = add_detection_noise(
                    np.array([p_hat]),
                    n_detected=int(n_detected_effective),
                    seed=int(seed) + 10_000 + i,
                )
                p_hat = float(noisy[0])
            p3_noisy[i] = p_hat
        elif detection_noise_enabled:
            # Legacy path: technical sigma_P if given, else Gaussian 1/sqrt(N).
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

    # Statistics.  When a servo-acquisition segment is declared, summary
    # statistics and the Allan deviation describe the locked segment only;
    # the full series is still returned for plotting and inspection.
    settle = max(0, min(int(servo_settle_drops), n - 1))
    g_locked = g_estimates[settle:]
    mean_g = float(np.mean(g_locked))
    std_g = float(np.std(g_locked))
    taus, adev = _allan_deviation(g_locked, float(cycle_time_s))

    # Derived series in µGal for the standard run plots.
    g_deviation_ugal = (g_estimates - float(gravity_true_m_s2)) * 1e8
    allan_dev_ugal = adev * 1e8
    white_noise_guide_ugal = (
        allan_dev_ugal[0] * np.sqrt(taus[0] / taus) if len(taus) else allan_dev_ugal
    )

    # Determine study scope based on whether we use fully-simulated MZ
    if gravity_propagation:
        study_scope = "fully_simulated_multi_drop_cycle"
    else:
        study_scope = "hybrid_aisim_plus_closed_form_multi_drop_cycle"
    category, description = _classify_study_scope(study_scope)

    primary_title = "Multi-drop campaign: per-drop gravity estimates"
    if settle:
        primary_title += f" (first {settle} drops = servo acquisition)"
    allan_title = "Allan deviation of g"
    if settle:
        allan_title += " (locked segment)"

    return {
        "backend": "aisim",
        "model": "multi_drop_cycle",
        "study_type": "multi_drop_cycle",
        "n_drops": int(n),
        "cycle_time_s": float(cycle_time_s),
        "gravity_true_m_s2": float(gravity_true_m_s2),
        "gravity_propagation": bool(gravity_propagation),
        "raman_substeps": int(raman_substeps),
        "detection_noise_enabled": bool(detection_noise_enabled),
        "projection_noise": bool(projection_noise),
        "n_detected_per_drop": int(n_detected_per_drop),
        # NOTE: ``n_detected_effective`` is 1/sigma_P^2 -- the equivalent atom
        # number representing the *technical* detection noise, NOT a count of
        # detected atoms.  ``detection_noise_equivalent_atoms`` is the same
        # value under an unambiguous name; the old key is kept for
        # backwards compatibility with existing consumers.
        "n_detected_effective": int(n_detected_effective),
        "detection_noise_equivalent_atoms": int(n_detected_effective),
        "detection_sigma_p": (None if detection_sigma_p is None else float(detection_sigma_p)),
        "raman_phase_noise_rad": float(raman_phase_noise_rad),
        "correlated_vibration": bool(correlated_vibration),
        "visibility_estimate": float(visibility_estimate),
        "servo_enabled": bool(servo_enabled),
        "servo_type": str(servo_type),
        "servo_settle_drops": int(settle),
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
        "g_deviation_ugal": g_deviation_ugal,
        "allan_dev_ugal": allan_dev_ugal,
        "allan_white_noise_guide_ugal": white_noise_guide_ugal,
        "plot_specs": [
            {
                "name": "simulation_primary",
                "title": primary_title,
                "x_key": "timestamps_s",
                "x_label": "time in campaign (s)",
                "y_label": "g - g_true (µGal)",
                "series": [
                    {
                        "key": "g_deviation_ugal",
                        "label": "per-drop estimate",
                        "kind": "line_markers",
                    },
                ],
            },
            {
                "name": "simulation_secondary",
                "title": allan_title,
                "x_key": "allan_taus_s",
                "x_label": "averaging time tau (s)",
                "y_label": "Allan deviation (µGal)",
                "xscale": "log",
                "yscale": "log",
                "series": [
                    {"key": "allan_dev_ugal", "label": "campaign", "kind": "line_markers"},
                    {
                        "key": "allan_white_noise_guide_ugal",
                        "label": "white-noise tau^-1/2 guide",
                        "kind": "dashed",
                    },
                ],
            },
        ],
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
                projection_noise=bool(projection_noise),
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
