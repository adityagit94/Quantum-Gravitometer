"""Emergent Monte-Carlo quantum projection noise (projection_noise flag).

With ``projection_noise: true`` each drop's readout draws the detected
excited-state count from ``Binomial(N_det, P)`` (seeded RNG stream), so the
quantum-projection-noise floor *emerges* from single-atom statistics instead
of being injected as a configured Gaussian sigma.

Analytic QPN prediction at mid-fringe (P = 1/2, V = 1 inversion):

    sigma_P   = sqrt(P(1-P)/N_det) = 1/(2*sqrt(N_det))
    sigma_phi = sigma_P / |dP/dphi| = 1/sqrt(N_det)
    sigma_g   = sigma_phi / (k_eff * T^2)
    ASD       = sigma_g * sqrt(T_c)
"""

from __future__ import annotations

import numpy as np
import pytest

from qgrav.physics.readout_models import binomial_projection_readout
from qgrav.sim_ai.aisim_adapter import run_aisim_multi_drop_cycle

K_EFF = 16106601.659  # 2 * 2pi / 780.2nm (the adapter default)
T_INTERF = 0.26


def _midfringe_gravity() -> float:
    """A g_true that puts the hybrid-mode operating point at P3 = 1/2.

    In hybrid mode the engine sets phase_bias = pi/2 - k*g*T^2 while the
    (gravity-free) propagation contributes no compensating k*g*T^2, so P3
    traces a fringe in (k*g*T^2 mod 2pi).  Empirically (fringe probe over
    one period, deterministic) the fringe is P3 = 0.5*(1 + V*cos(2pi*f - 0.23))
    with f the fractional part — mid-fringe sits at f ~ 0.287.  The QPN
    floor test asserts the operating point landed near P = 1/2 before
    using the textbook formula.
    """
    m = round(9.81 * K_EFF * T_INTERF**2 / (2.0 * np.pi))
    return (float(m) + 0.287) * 2.0 * np.pi / (K_EFF * T_INTERF**2)


def _qpn_run(n_drops: int, n_det: int, seed: int = 7) -> dict:
    """All technical noises off, servo off, hybrid mode (fast, analytic fringe).

    The ensemble is made effectively noiseless (ultra-cold, tiny cloud, wide
    flat beam, wide detector, exact pi/2 pulse area) so the per-drop
    fresh-ensemble resampling does not contribute P3 scatter — the only
    randomness left is the binomial readout under test.
    """
    return run_aisim_multi_drop_cycle(
        n_drops=n_drops,
        n_atoms=120,
        detector_radius_m=0.05,
        cloud_radius_m=1e-4,
        temp_xy_K=1e-12,
        temp_z_K=1e-12,
        beam_radius_m=0.5,
        # Exact pi/2 pulse area under the flat beam, so the operating point
        # sits at P = 1/2 where the analytic QPN formula applies.
        center_rabi_freq_hz=1.0 / (4.0 * 23e-6),
        seed=seed,
        gravity_propagation=False,
        gravity_true_m_s2=_midfringe_gravity(),
        cycle_time_s=1.0,
        interferometer_time_s=T_INTERF,
        detection_noise_enabled=False,
        projection_noise=True,
        n_detected_per_drop=n_det,
        servo_enabled=False,
        raman_phase_noise_rad=0.0,
        correlated_vibration=False,
    )


def _sigma_g_pred(n_det: int) -> float:
    return 1.0 / (np.sqrt(float(n_det)) * K_EFF * T_INTERF**2)


@pytest.mark.slow
def test_qpn_floor_emerges_from_binomial_statistics():
    """The white noise level of the g series matches the analytic QPN floor."""
    n_det = 10_000
    out = _qpn_run(n_drops=2000, n_det=n_det)
    predicted = _sigma_g_pred(n_det)

    # Precondition: the run really sits at mid-fringe (see _midfringe_gravity).
    p_mean = float(np.mean(out["port_3_raw"]))
    assert 0.4 < p_mean < 0.6, f"operating point off mid-fringe: P={p_mean:.3f}"

    # Per-drop scatter (the white floor itself).
    measured_std = float(out["std_g_m_s2"])
    assert measured_std == pytest.approx(predicted, rel=0.20)

    # The first Allan point of a white series equals the per-drop sigma.
    adev = np.asarray(out["allan_dev_m_s2"], dtype=np.float64)
    assert adev[0] == pytest.approx(predicted, rel=0.20)

    # And it must average down like white noise (next octaves ~1/sqrt(m)).
    assert adev[2] < 0.75 * adev[0]


@pytest.mark.slow
def test_qpn_floor_scales_as_inverse_sqrt_n_detected():
    """Quadrupling N_det halves the emergent floor (within 15%)."""
    out_a = _qpn_run(n_drops=1200, n_det=4_000, seed=21)
    out_b = _qpn_run(n_drops=1200, n_det=16_000, seed=22)
    ratio = float(out_a["std_g_m_s2"]) / float(out_b["std_g_m_s2"])
    assert ratio == pytest.approx(2.0, rel=0.15)


def test_projection_noise_default_off_is_bit_identical():
    """Flag absent and flag=False produce identical series (same seed)."""
    kwargs = dict(
        n_drops=40,
        n_atoms=120,
        detector_radius_m=0.05,
        seed=99,
        gravity_propagation=False,
        detection_noise_enabled=True,
        n_detected_per_drop=500,
        servo_enabled=False,
    )
    base = run_aisim_multi_drop_cycle(**kwargs)
    explicit = run_aisim_multi_drop_cycle(**kwargs, projection_noise=False)
    np.testing.assert_array_equal(base["g_estimates_m_s2"], explicit["g_estimates_m_s2"])
    assert explicit["projection_noise"] is False


def test_projection_noise_mean_population_unbiased():
    """mean(P_hat) over drops ~ P (z-test, 4-sigma band)."""
    n_det = 2_000
    out = _qpn_run(n_drops=400, n_det=n_det, seed=13)
    p_raw = np.asarray(out["port_3_raw"], dtype=np.float64)
    p_noisy = np.asarray(out["port_3_noisy"], dtype=np.float64)
    p_true = float(np.mean(p_raw))
    sigma_mean = np.sqrt(p_true * (1.0 - p_true) / n_det / len(p_noisy))
    z = abs(float(np.mean(p_noisy)) - p_true) / sigma_mean
    assert z < 4.0, f"binomial readout biased: z={z:.2f}"


def test_projection_plus_technical_noise_composes():
    """An explicit technical sigma_p on top of QPN increases the variance."""
    common = dict(
        n_drops=300,
        n_atoms=120,
        detector_radius_m=0.05,
        cloud_radius_m=1e-4,
        temp_xy_K=1e-12,
        temp_z_K=1e-12,
        beam_radius_m=0.5,
        seed=31,
        gravity_propagation=False,
        projection_noise=True,
        n_detected_per_drop=50_000,  # tiny QPN so the technical term dominates
        servo_enabled=False,
    )
    pure = run_aisim_multi_drop_cycle(**common, detection_noise_enabled=False)
    composed = run_aisim_multi_drop_cycle(
        **common, detection_noise_enabled=True, detection_sigma_p=5e-3
    )
    assert float(composed["std_g_m_s2"]) > 2.0 * float(pure["std_g_m_s2"])


def test_projection_noise_through_config_dispatcher():
    from qgrav.sim_ai.aisim_adapter import run_simulation_from_config

    out = run_simulation_from_config(
        {
            "enabled": True,
            "backend": "aisim",
            "model": "multi_drop_cycle",
            "n_atoms": 120,
            "detector_radius_m": 0.05,
            "seed": 4,
            "n_drops": 5,
            "gravity_propagation": False,
            "projection_noise": True,
            "n_detected_per_drop": 1000,
            "detection_noise_enabled": False,
        }
    )
    assert out is not None
    assert out["projection_noise"] is True
    assert "quantum projection noise" in out["physical_model"]["noise"]


def test_binomial_readout_unit_behaviour():
    rng = np.random.default_rng(0)
    # Degenerate probabilities are exact.
    assert binomial_projection_readout(0.0, 100, rng=rng) == 0.0
    assert binomial_projection_readout(1.0, 100, rng=rng) == 1.0
    # Out-of-range inputs are clipped, not fatal.
    assert binomial_projection_readout(1.2, 100, rng=rng) == 1.0
    with pytest.raises(ValueError):
        binomial_projection_readout(0.5, 0, rng=rng)
    # Reproducible under a fixed seed.
    a = binomial_projection_readout(0.5, 1000, rng=np.random.default_rng(5))
    b = binomial_projection_readout(0.5, 1000, rng=np.random.default_rng(5))
    assert a == b
