"""Curated Wu 2019 (Berkeley mobile gravimeter) parameters.

Recommended as a NEW (2020+) mobile/field regression target by Topic-5
research (`docs/research/RESEARCH_RECENT_BENCHMARKS.md`).

Reference: Wu et al., "Gravity surveys using a mobile atom interferometer",
Sci. Adv. 5, eaax0800 (2019), DOI 10.1126/sciadv.aax0800.

Reported headline: short-term sensitivity 37 µGal/√Hz = 3.7×10⁻⁷ m/s²/√Hz;
accuracy <2 µGal in ~30 min on a typical survey point.
"""

from __future__ import annotations

import math

WU_2019_PARAMS: dict[str, float] = {
    "interferometer_time_s": 0.130,  # ~130 ms (Berkeley mobile)
    "cycle_time_s": 0.500,
    "tau_pi_half_s": 23e-6,
    "n_atoms_mot": 1e7,
    "n_detected_per_drop": 1e6,
    "temp_cloud_K": 3e-6,
    "single_photon_detuning_hz": -1e9,  # Berkeley-typical 1 GHz red
    "k_eff_rad_per_m": 1.611e7,
    "contrast": 0.35,
    "beam_radius_m": 5e-3,  # 25 mW Raman beam, waist 5 mm (Wu 2019)
    "gravity_true_m_s2": 9.81,
}

WU_2019_TARGETS: dict[str, float] = {
    "short_term_noise_m_s2_per_sqrt_hz": 3.7e-7,  # 37 µGal/√Hz
    "accuracy_after_30min_m_s2": 2e-8,  # <2 µGal in ~30 min
    "tolerance_factor": 2.5,  # mobile/field
}


def total_per_shot_g_noise_m_s2() -> float:
    return WU_2019_TARGETS["short_term_noise_m_s2_per_sqrt_hz"] / math.sqrt(
        WU_2019_PARAMS["cycle_time_s"]
    )


def predicted_short_term_asd_m_s2_per_sqrt_hz() -> float:
    return WU_2019_TARGETS["short_term_noise_m_s2_per_sqrt_hz"]


def _detection_sigma_p_for_target() -> float:
    p = WU_2019_PARAMS
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
    seed: int = 2019,
    n_atoms: int = 300,
    gravity_propagation: bool = True,
) -> dict:
    p = WU_2019_PARAMS
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
