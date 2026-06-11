"""Curated Hu 2013 (HUST short fountain) parameters and noise budget.

Hu 2013 is the **lab-best-case sensitivity** regression target for qgrav.

**Critical research correction** (see `docs/research/RESEARCH_HU_2013.md`):
this paper is NOT the Wuhan 10-m drop tower (that is the WIPM-CAS / M.-S.
Zhan project, a different paper).  Hu et al. PRA 88, 043610 (2013) is a
HUST short atomic fountain with T=300 ms and a 0.75 m apex above the MOT.

Reported headline: short-term sensitivity 4.2 µGal/√Hz = 4.2×10⁻⁸ m/s²/√Hz
(verbatim, abstract).  No per-effect systematic-error budget is published in
the paper itself; the first HUST budget appears in Xu et al. 2022.

The HUST 2015 review (Zhou et al., Chin. Phys. B 24, 050401) breaks the
4.2 µGal/√Hz into three contributions:
  - detection noise (C ~ 0.15, T=300 ms):  3.3 µGal/√Hz = 3.3e-8 m/s²/√Hz
  - residual vibration:                    1.2 µGal/√Hz = 1.2e-8 m/s²/√Hz
  - Raman-phase noise:                     0.8 µGal/√Hz = 8e-9 m/s²/√Hz
Quadrature sum: sqrt(3.3² + 1.2² + 0.8²) ≈ 3.6 µGal/√Hz (close to 4.2).
"""

from __future__ import annotations

import math

HU_2013_PARAMS: dict[str, float] = {
    "interferometer_time_s": 0.300,  # HUST 2015 review, Fig.7 (verbatim)
    "cycle_time_s": 1.0,  # HUST 2015 review (verbatim)
    "tau_pi_half_s": 23e-6,  # not in open sources — generic Rb-87
    "n_atoms_mot": 3e9,  # HUST 2015 review
    "n_atoms_interferometer": 5e7,  # after state preparation
    "n_detected_per_drop": 5e7,
    "temp_cloud_K": 7e-6,  # transverse, post-MOT
    "temp_cloud_long_K": 300e-9,  # longitudinal (velocity-selected)
    "launch_velocity_m_s": 3.83,
    "apex_above_mot_m": 0.75,
    "single_photon_detuning_hz": -1.5e9,  # |Δ| ≈ 1.5 GHz; sign not in open sources
    "chirp_rate_hz_per_s": 25.14e6,  # closest open value
    "k_eff_rad_per_m": 1.611e7,  # 4π/780.241 nm
    "contrast": 0.15,  # low; drives detection noise budget
    "gravity_true_m_s2": 9.81,
}

HU_2013_NOISE_BUDGET: dict[str, float] = {
    # HUST 2015 review per-effect breakdown (citing Hu 2013).
    "detection_g_noise_m_s2": 3.3e-8,  # dominant; low-contrast detection
    "vibration_g_noise_m_s2": 1.2e-8,  # active isolation, 1.2 µGal/√Hz
    "raman_phase_g_noise_m_s2": 8e-9,  # 0.8 µGal/√Hz
}

HU_2013_TARGETS: dict[str, float] = {
    "short_term_noise_m_s2_per_sqrt_hz": 4.2e-8,  # 4.2 µGal/√Hz (verbatim)
    "long_term_at_100s_m_s2": 5e-9,  # better than 0.5 µGal at 100 s
    "tolerance_factor": 2.5,  # accept within x2.5
}


def total_per_shot_g_noise_m_s2() -> float:
    """Quadrature sum of the per-shot g-noise contributions (m/s²)."""
    b = HU_2013_NOISE_BUDGET
    return math.sqrt(
        b["detection_g_noise_m_s2"] ** 2
        + b["vibration_g_noise_m_s2"] ** 2
        + b["raman_phase_g_noise_m_s2"] ** 2
    )


def predicted_short_term_asd_m_s2_per_sqrt_hz() -> float:
    """Predicted short-term ASD = σ_per_shot * sqrt(T_cycle)."""
    return total_per_shot_g_noise_m_s2() * math.sqrt(HU_2013_PARAMS["cycle_time_s"])


def phase_noise_per_shot_rad() -> float:
    """Combined Raman + vibration per-shot noise as an MZ phase (rad)."""
    b = HU_2013_NOISE_BUDGET
    g_noise = math.sqrt(b["raman_phase_g_noise_m_s2"] ** 2 + b["vibration_g_noise_m_s2"] ** 2)
    return (
        HU_2013_PARAMS["k_eff_rad_per_m"] * HU_2013_PARAMS["interferometer_time_s"] ** 2 * g_noise
    )


def _detection_sigma_p_from_g_noise() -> float:
    """Convert the 3.3 µGal/√Hz detection-noise term into an equivalent σ_P.

    Per-shot σ_P = σ_g * (V/2) * k_eff * T² (linearised mid-fringe).
    """
    p = HU_2013_PARAMS
    return (
        HU_2013_NOISE_BUDGET["detection_g_noise_m_s2"]
        * 0.5
        * p["contrast"]
        * p["k_eff_rad_per_m"]
        * p["interferometer_time_s"] ** 2
    )


def multi_drop_kwargs(
    *,
    n_drops: int = 60,
    seed: int = 2013,
    n_atoms: int = 300,
    gravity_propagation: bool = True,
) -> dict:
    """Build kwargs for run_aisim_multi_drop_cycle in a Hu-2013-like configuration."""
    p = HU_2013_PARAMS
    return dict(
        n_drops=int(n_drops),
        seed=int(seed),
        n_atoms=int(n_atoms),
        cycle_time_s=p["cycle_time_s"],
        interferometer_time_s=p["interferometer_time_s"],
        tau_pi_half_s=p["tau_pi_half_s"],
        gravity_true_m_s2=p["gravity_true_m_s2"],
        gravity_propagation=bool(gravity_propagation),
        detection_noise_enabled=True,
        detection_sigma_p=_detection_sigma_p_from_g_noise(),
        raman_phase_noise_rad=phase_noise_per_shot_rad(),
        fit_visibility=bool(gravity_propagation),
    )
