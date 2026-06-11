"""Curated Xu 2022 (HUST-QG transportable) parameters.

Recommended as a NEW (2020+) regression target by Topic-5 research
(`docs/research/RESEARCH_RECENT_BENCHMARKS.md`).  HUST-QG is the first HUST
transportable atom gravimeter with a **full per-effect systematic-error
budget** — enabling an *accuracy* (not just sensitivity) comparison.

Reference: Xu et al., Metrologia 59, 055001 (2022), DOI 10.1088/1681-7575/ac8258.

Reported headline (verbatim): "HUST-QG exhibited a short-term sensitivity of
24 µGal Hz⁻¹ᐟ² and a combined uncertainty of 3 µGal.  The degree of
equivalence for HUST-QG in this comparison is 1.3 µGal."  (ICAG-2017.)
"""

from __future__ import annotations

import math

XU_2022_PARAMS: dict[str, float] = {
    "interferometer_time_s": 0.300,  # similar to Hu 2013 lineage
    "cycle_time_s": 1.0,
    "tau_pi_half_s": 23e-6,
    "n_atoms_mot": 3e9,
    "n_detected_per_drop": 1e7,
    "temp_cloud_K": 7e-6,
    "single_photon_detuning_hz": -1.5e9,
    "k_eff_rad_per_m": 1.611e7,
    "contrast": 0.30,  # higher than Hu 2013 lab
    "gravity_true_m_s2": 9.81,
}

XU_2022_TARGETS: dict[str, float] = {
    "short_term_noise_m_s2_per_sqrt_hz": 2.4e-7,  # 24 µGal/√Hz
    "combined_uncertainty_m_s2": 3e-8,  # 3 µGal combined uncertainty
    "icag_equivalence_m_s2": 1.3e-8,  # 1.3 µGal degree of equivalence
    "tolerance_factor": 2.5,  # transportable wider envelope
}


def total_per_shot_g_noise_m_s2() -> float:
    """Per-shot σ_g from the 24 µGal/√Hz Allan plateau divided by sqrt(T_cycle)."""
    return XU_2022_TARGETS["short_term_noise_m_s2_per_sqrt_hz"] / math.sqrt(
        XU_2022_PARAMS["cycle_time_s"]
    )


def predicted_short_term_asd_m_s2_per_sqrt_hz() -> float:
    """The target itself (this is the published value, not a derivation)."""
    return XU_2022_TARGETS["short_term_noise_m_s2_per_sqrt_hz"]


def _detection_sigma_p_for_target() -> float:
    """Choose σ_P so the multi-drop simulation reproduces ~24 µGal/√Hz."""
    p = XU_2022_PARAMS
    sigma_g_per_shot = total_per_shot_g_noise_m_s2()
    return (
        sigma_g_per_shot
        * 0.5
        * p["contrast"]
        * p["k_eff_rad_per_m"]
        * p["interferometer_time_s"] ** 2
    )


def multi_drop_kwargs(
    *,
    n_drops: int = 60,
    seed: int = 2022,
    n_atoms: int = 300,
    gravity_propagation: bool = True,
) -> dict:
    """Build kwargs for run_aisim_multi_drop_cycle in a HUST-QG configuration."""
    p = XU_2022_PARAMS
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
        detection_sigma_p=_detection_sigma_p_for_target(),
        fit_visibility=bool(gravity_propagation),
    )
