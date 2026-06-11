"""Curated Freier 2016 (GAIN) parameters and noise budget for qgrav validation.

Freier 2016 is the **primary** regression target for qgrav (mobile Rb-87
gravimeter with both short-term noise and long-term stability reported in the
same paper).

Primary sources (see ``docs/research/RESEARCH_FREIER_2016.md`` for the full
per-parameter provenance with verbatim quotes):

- Freier, C. et al., "Mobile quantum gravity sensor with unprecedented
  stability", J. Phys.: Conf. Ser. 723, 012050 (2016).
  DOI: 10.1088/1742-6596/723/1/012050 (arXiv:1512.05660).
- Freier, C., PhD thesis, Humboldt-Universitaet zu Berlin (2017).
  DOI: 10.18452/17795.  *The parameter gold-mine* — most values below come
  from the thesis (same instrument, same Onsala 2015 campaign as the 2016
  paper's dataset).
- Hu, Q.-Q. et al., arXiv:1805.05159 (GAIN operational parameters).

Reported headline metrics (Freier 2016 abstract, verbatim):
"accuracy of 39 nm/s^2, long-term stability of 0.5 nm/s^2 and short-term
noise of 96 nm/s^2/sqrt(Hz)."

.. important::
   GAIN is **technically-limited, not projection-limited** — the 96 nm/s^2/
   sqrt(Hz) is dominated by vibration + Raman-phase + technical-detection
   noise, NOT by sqrt(N) atomic projection noise.  Do not model the noise
   from the detected atom number alone; use ``FREIER_2016_NOISE_BUDGET``.
"""

from __future__ import annotations

import math

# --- Instrument parameters (SI, qgrav-ready) ---------------------------------
# Every value is sourced in docs/research/RESEARCH_FREIER_2016.md.
FREIER_2016_PARAMS: dict[str, float] = {
    "interferometer_time_s": 0.260,  # thesis ch.2.3 ("T = 0.26 s")
    "cycle_time_s": 1.5,  # Freier 2016 §2 (verbatim)
    "tau_pi_half_s": 17e-6,  # thesis ch.4.3 (Onsala; pi = 34 us)
    "n_atoms_mot": 1e9,  # thesis ch.3.1.2
    "n_atoms_selected": 2e7,  # thesis ch.4.2
    "n_detected_per_drop": 5e5,  # thesis ch.4.4
    "temp_cloud_K": 2e-6,  # thesis Fig.4.1; Hu et al.
    "sigma_v_selected_m_s": 5.2e-3,  # thesis ch.4.2 (post velocity selection)
    "beam_radius_m": 0.015,  # 30 mm 1/e^2 diameter; thesis ch.3.1.4
    "single_photon_detuning_hz": -700e6,  # red of F'=1; thesis ch.3.3.1
    "chirp_rate_hz_per_s": 25.14e6,  # = k_eff*g/(2*pi); thesis ch.4.3
    "k_eff_rad_per_m": 1.610e7,  # 2*(2*pi/780.241 nm), counter-prop
    "raman_intensity_ratio_q": 1.72,  # light-shift null; Hu et al.
    "gravity_true_m_s2": 9.81,
}

# --- Documented per-shot g-noise budget (Freier 2017 thesis ch.4.4 / ch.5.4) -
# These are the contributions that sum (in quadrature) to the 96 nm/s^2/sqrt(Hz)
# short-term noise.  GAIN is technically-limited; sqrt(N) projection noise
# (~ 1.4e-3 in sigma_P, well below the technical floor) is NOT the limit.
FREIER_2016_NOISE_BUDGET: dict[str, float] = {
    # Technical detection-noise standard deviation on the state population P.
    # Thesis: measured sigma_P = 0.005-0.009 (vs 1/sqrt(5e5) ~ 1.4e-3 shot).
    "detection_sigma_p": 6e-3,
    # Per-shot equivalent g-noise from detection technical noise (thesis: <= 30 nm/s^2).
    "detection_g_noise_m_s2": 30e-9,
    # Raman-laser phase noise (thesis: 10-40 nm/s^2/shot; use Onsala-maser ~40).
    "raman_phase_g_noise_m_s2": 40e-9,
    # Residual vibration after active isolation + post-correction
    # (thesis Fig.3.11: 140 -> 71 nm/s^2 rms per shot).
    "vibration_g_noise_m_s2": 71e-9,
}

# --- Target benchmarks (Freier 2016 abstract, verbatim) ----------------------
FREIER_2016_TARGETS: dict[str, float] = {
    "short_term_noise_m_s2_per_sqrt_hz": 9.6e-8,  # 96 nm/s^2/sqrt(Hz)
    "long_term_stability_m_s2": 5e-10,  # 0.5 nm/s^2 (~1 day)
    "accuracy_m_s2": 3.9e-8,  # 39 nm/s^2
    "tolerance_factor": 2.0,  # accept within x2 either way
    "long_term_tolerance_factor": 5.0,  # long-term is harder
}


def total_per_shot_g_noise_m_s2() -> float:
    """Quadrature sum of the documented per-shot g-noise contributions (m/s^2)."""
    b = FREIER_2016_NOISE_BUDGET
    return math.sqrt(
        b["detection_g_noise_m_s2"] ** 2
        + b["raman_phase_g_noise_m_s2"] ** 2
        + b["vibration_g_noise_m_s2"] ** 2
    )


def predicted_short_term_asd_m_s2_per_sqrt_hz() -> float:
    """Predicted short-term sensitivity (ASD) from the documented noise budget.

    For white per-shot noise sampled at the cycle time T_c, the short-term
    amplitude spectral density is ``sigma_per_shot * sqrt(T_c)``.
    """
    return total_per_shot_g_noise_m_s2() * math.sqrt(FREIER_2016_PARAMS["cycle_time_s"])


def phase_noise_per_shot_rad() -> float:
    """Combined Raman + vibration per-shot noise expressed as an MZ phase (rad).

    Converts the two phase-type g-noise terms to an interferometer phase via
    ``phi = k_eff * g * T^2``.  (Detection noise is handled separately as a
    P-noise via ``detection_sigma_p``.)
    """
    b = FREIER_2016_NOISE_BUDGET
    k_eff = FREIER_2016_PARAMS["k_eff_rad_per_m"]
    T = FREIER_2016_PARAMS["interferometer_time_s"]
    g_noise = math.sqrt(b["raman_phase_g_noise_m_s2"] ** 2 + b["vibration_g_noise_m_s2"] ** 2)
    return k_eff * T**2 * g_noise


def multi_drop_kwargs(
    *,
    n_drops: int = 60,
    seed: int = 2016,
    n_atoms: int = 300,
    gravity_propagation: bool = True,
) -> dict:
    """Build kwargs for :func:`run_aisim_multi_drop_cycle` driving a Freier-like
    run with the documented noise budget injected.

    The detection technical noise is injected via ``detection_sigma_p`` and the
    combined Raman+vibration phase noise via ``raman_phase_noise_rad``.  The
    fringe contrast is fitted (``fit_visibility=True``) so the P3->g inversion
    is consistent with the real ensemble contrast.

    ``n_atoms`` and ``n_drops`` are kept modest for test runtime; the noise
    knobs (not the atom number) set the sensitivity, consistent with GAIN being
    technically-limited.
    """
    p = FREIER_2016_PARAMS
    return dict(
        n_drops=int(n_drops),
        seed=int(seed),
        n_atoms=int(n_atoms),
        cycle_time_s=p["cycle_time_s"],
        interferometer_time_s=p["interferometer_time_s"],
        tau_pi_half_s=p["tau_pi_half_s"],
        beam_radius_m=p["beam_radius_m"],
        gravity_true_m_s2=p["gravity_true_m_s2"],
        gravity_propagation=bool(gravity_propagation),
        detection_noise_enabled=True,
        detection_sigma_p=FREIER_2016_NOISE_BUDGET["detection_sigma_p"],
        raman_phase_noise_rad=phase_noise_per_shot_rad(),
        fit_visibility=bool(gravity_propagation),
    )
