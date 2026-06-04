"""Curated Ménoret 2018 (Muquans AQG-A01 Larzac) parameters and noise budget.

Ménoret 2018 is the **transportable real-world robustness** regression target
for qgrav.  See `docs/research/RESEARCH_MENORET_2018.md` for verbatim quotes.

**Critical research corrections**:
  - T = 60 ms (NOT 80 ms); π/2 = 10 µs, π = 20 µs
  - cycle = 500 ms (~2 Hz, NOT 1 s)
  - vibration handled by **feed-forward active Raman-phase correction** with a
    Nanometrics Titan accelerometer — NO mechanical isolation
  - 5 distinct sensitivity values in the paper; the 750 nm/s²/√Hz (Larzac
    campaign value) was the v1.0.2 corrected registry value
"""
from __future__ import annotations

import math

MENORET_2018_PARAMS: dict[str, float] = {
    "interferometer_time_s": 0.060,   # verbatim "T = 60 ms"
    "cycle_time_s": 0.500,             # ~2 Hz repetition rate
    "tau_pi_half_s": 10e-6,            # verbatim "10 us pi/2, 20 us pi"
    "tau_pi_s": 20e-6,
    "n_atoms": 1e7,                    # ~10^7 atoms per MOT load
    "n_detected_per_drop": 1e7,
    "temp_cloud_K": 2e-6,              # "below 2 µK"
    "mot_load_time_s": 0.250,
    "single_photon_detuning_hz": -1.5e9,   # Muquans-style, not stated explicitly
    "chirp_rate_hz_per_s": 25.16e6,    # α ≈ 25 MHz/s (verbatim)
    "k_eff_rad_per_m": 1.611e7,
    "contrast": 0.40,                   # verbatim "C = 40%"
    "detection_snr": 150.0,             # verbatim
    "effective_snr": 60.0,              # = C * SNR = 0.4 * 150
    "verticality_uncertainty_rad": 10e-6,
    "gravity_true_m_s2": 9.81,
}

MENORET_2018_NOISE_BUDGET: dict[str, float] = {
    # The paper's IDEAL single-shot floor (δg/g = 1/(k_eff·g·T²·SNR_eff))
    # = 2.94e-7 m/s² per shot, equivalent to the BEST-Larzac 500 nm/s²/√Hz
    # at T_cycle = 0.5 s.  Not directly used in the budget below.
    "ideal_single_shot_g_noise_m_s2": 2.94e-7,
    # Residual vibration AFTER feed-forward Raman-phase correction
    # ("36 mrad rms residual"); verbatim in the paper's Methods.
    "vibration_residual_phase_rad": 36e-3,
    # The AS-OPERATED Larzac campaign value (target) — the value v1.0.2
    # corrected to in the registry.  Backed out: σ_per_shot = target/sqrt(Tc).
    "campaign_g_noise_target_m_s2_per_sqrt_hz": 7.5e-7,
}

MENORET_2018_TARGETS: dict[str, float] = {
    "short_term_noise_m_s2_per_sqrt_hz": 7.5e-7,   # 750 nm/s²/√Hz (Larzac campaign)
    "long_term_stability_m_s2": 1e-8,              # < 10 nm/s² = 1 µGal
    "tolerance_factor": 2.5,                        # field-deployed → wider envelope
}


def total_per_shot_g_noise_m_s2() -> float:
    """Per-shot σ_g backed out from the AS-OPERATED Larzac campaign ASD."""
    target = MENORET_2018_NOISE_BUDGET["campaign_g_noise_target_m_s2_per_sqrt_hz"]
    return target / math.sqrt(MENORET_2018_PARAMS["cycle_time_s"])


def predicted_short_term_asd_m_s2_per_sqrt_hz() -> float:
    """The target itself (this is the as-operated campaign value)."""
    return MENORET_2018_NOISE_BUDGET["campaign_g_noise_target_m_s2_per_sqrt_hz"]


def phase_noise_per_shot_rad() -> float:
    """Per-shot residual vibration phase (verbatim 36 mrad rms)."""
    return MENORET_2018_NOISE_BUDGET["vibration_residual_phase_rad"]


def _detection_sigma_p_for_target() -> float:
    """σ_P = σ_per_shot * V/2 * k_eff * T² (mid-fringe linearisation)."""
    p = MENORET_2018_PARAMS
    return (
        total_per_shot_g_noise_m_s2()
        * 0.5 * p["contrast"] * p["k_eff_rad_per_m"] * p["interferometer_time_s"] ** 2
    )


def multi_drop_kwargs(
    *,
    n_drops: int = 60,
    seed: int = 2018,
    n_atoms: int = 300,
    gravity_propagation: bool = True,
) -> dict:
    """Build kwargs for run_aisim_multi_drop_cycle in a Ménoret-2018 configuration."""
    p = MENORET_2018_PARAMS
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
        raman_phase_noise_rad=phase_noise_per_shot_rad(),
        fit_visibility=bool(gravity_propagation),
    )
