import numpy as np
from qgrav.bench_ifo import generate_virtual_ifo
from qgrav.algorithms import estimate_displacement_baseline, estimate_displacement_improved

def test_improved_beats_baseline_on_drifty_data():
    cfg = dict(
        wavelength_m=1.55e-6,
        sample_rate_hz=1000,
        duration_s=3.0,
        displacement_sines=[{"amplitude_m": 3e-9, "freq_hz": 7.0, "phase_rad": 0.2}],
        measurement_noise_std=0.05,
        amplitude=1.0,
        dc_offset=0.2,
        offset_drift_std_per_s=0.05,
        amplitude_drift_std_per_s=0.01,
        seed=0,
    )
    data = generate_virtual_ifo(**cfg)
    I, Q = data["I_meas"], data["Q_meas"]
    x_true = data["x_true"]
    lam = cfg["wavelength_m"]

    x_b = estimate_displacement_baseline(I, Q, wavelength_m=lam)["x_hat"]
    x_i = estimate_displacement_improved(
        I, Q, wavelength_m=lam, offset_tracking_alpha=0.01, phase_smooth_window=21
    )["x_hat"]

    rmse_b = float(np.sqrt(np.mean((x_b - x_true) ** 2)))
    rmse_i = float(np.sqrt(np.mean((x_i - x_true) ** 2)))

    assert rmse_i <= 0.9 * rmse_b
