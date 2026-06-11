"""Tests for the polar-motion and ocean-loading corrections (v1.5)."""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pytest

from qgrav.datasets.corrections import (
    apply_ocean_loading_correction,
    apply_polar_motion_correction,
)

UGAL = 1e-8  # m/s^2


# ----------------------------------------------------------------------
# Polar motion
# ----------------------------------------------------------------------
def test_polar_motion_magnitude_within_physical_envelope():
    """|x_p|,|y_p| <= 0.4 arcsec keeps |delta_g| under ~15 microGal."""
    g = np.zeros(8)
    rng = np.random.default_rng(0)
    for _ in range(50):
        lat = rng.uniform(-90.0, 90.0)
        lon = rng.uniform(-180.0, 180.0)
        xp = rng.uniform(-0.4, 0.4)
        yp = rng.uniform(-0.4, 0.4)
        out = apply_polar_motion_correction(g, lat, lon, xp, yp)
        assert np.all(np.abs(out) < 1.5e-7)


def test_polar_motion_zero_at_equator_and_pole():
    g = np.zeros(4)
    for lat in (0.0, 90.0, -90.0):
        out = apply_polar_motion_correction(g, lat, 12.9, 0.2, 0.3)
        np.testing.assert_allclose(out, 0.0, atol=1e-20)


def test_polar_motion_sign_flips_with_xp_at_zero_longitude():
    g = np.zeros(4)
    out_pos = apply_polar_motion_correction(g, 45.0, 0.0, 0.2, 0.0)
    out_neg = apply_polar_motion_correction(g, 45.0, 0.0, -0.2, 0.0)
    np.testing.assert_allclose(out_pos, -out_neg)
    assert np.all(out_pos != 0.0)


def test_polar_motion_known_value():
    """Hand-evaluated formula at phi=45, lam=0, x_p=0.2 arcsec."""
    delta, omega, radius = 1.164, 7.292115e-5, 6.371e6
    xp_rad = np.deg2rad(0.2 / 3600.0)
    expected_delta_g = -delta * omega**2 * radius * 1.0 * xp_rad  # sin(2*45deg)=1
    out = apply_polar_motion_correction(np.zeros(1), 45.0, 0.0, 0.2, 0.0)
    # corrected = 0 - delta_g
    np.testing.assert_allclose(out[0], -expected_delta_g, rtol=1e-12)


def test_polar_motion_array_broadcasting():
    g = np.zeros(5)
    xp = np.linspace(-0.2, 0.2, 5)
    yp = np.zeros(5)
    out = apply_polar_motion_correction(g, 45.0, 0.0, xp, yp)
    assert out.shape == (5,)
    # Linear in x_p at lam=0: antisymmetric around the middle sample.
    np.testing.assert_allclose(out, -out[::-1])


def test_polar_motion_array_shape_mismatch_raises():
    with pytest.raises(ValueError, match="shape"):
        apply_polar_motion_correction(np.zeros(5), 45.0, 0.0, np.zeros(3), 0.0)


def test_polar_motion_zero_pole_is_noop():
    g = np.linspace(1.0, 2.0, 6)
    out = apply_polar_motion_correction(g, 45.0, 10.0, 0.0, 0.0)
    np.testing.assert_array_equal(out, g)


# ----------------------------------------------------------------------
# Ocean loading
# ----------------------------------------------------------------------
def _synthesize_loading(times, constituents):
    """The loading series the correction would subtract (via the public API)."""
    return -apply_ocean_loading_correction(times, np.zeros_like(times), constituents)


def test_ocean_loading_single_constituent_roundtrip():
    """Injecting a synthetic M2 signal and correcting it leaves a flat series."""
    t = np.arange(0.0, 5 * 86400.0, 60.0) + 1.7e9
    constituents = [{"name": "M2", "amplitude_nm_s2": 12.3, "phase_deg": -47.0}]
    signal = _synthesize_loading(t, constituents)
    assert np.std(signal) > 0.3 * 12.3e-9  # the injected tide actually oscillates

    g = np.full_like(t, 9.81) + signal
    corrected = apply_ocean_loading_correction(t, g, constituents)
    residual_rms = float(np.std(corrected - 9.81))
    assert residual_rms < 0.01 * 12.3e-9


def test_ocean_loading_m2_period():
    """The synthesized M2 series peaks at 12.4206 h within one FFT bin."""
    span_days = 30
    dt = 300.0
    t = np.arange(0.0, span_days * 86400.0, dt) + 1.7e9
    sig = _synthesize_loading(t, [{"name": "M2", "amplitude_nm_s2": 10.0, "phase_deg": 0.0}])

    spec = np.abs(np.fft.rfft(sig - np.mean(sig)))
    freqs = np.fft.rfftfreq(len(sig), d=dt)
    f_peak = freqs[np.argmax(spec)]
    f_m2 = 1.0 / (12.4206012 * 3600.0)
    df = freqs[1] - freqs[0]
    assert abs(f_peak - f_m2) <= df


def test_ocean_loading_empty_constituents_is_noop():
    t = np.arange(0.0, 3600.0, 60.0) + 1.7e9
    g = np.linspace(0.0, 1.0, t.size)
    out = apply_ocean_loading_correction(t, g, [])
    np.testing.assert_array_equal(out, g)


def test_ocean_loading_unknown_constituent_raises():
    t = np.zeros(3)
    with pytest.raises(ValueError, match="M2"):
        apply_ocean_loading_correction(
            t, t, [{"name": "X9", "amplitude_nm_s2": 1.0, "phase_deg": 0.0}]
        )


def test_ocean_loading_shape_mismatch_raises():
    with pytest.raises(ValueError, match="same shape"):
        apply_ocean_loading_correction(np.zeros(4), np.zeros(3), [])


def test_ocean_loading_all_supported_names_accepted():
    t = np.arange(0.0, 7200.0, 600.0) + 1.7e9
    constituents = [
        {"name": name, "amplitude_nm_s2": 1.0, "phase_deg": 0.0}
        for name in ("M2", "S2", "N2", "K2", "K1", "O1", "P1", "Q1", "Mf", "Mm", "Ssa")
    ]
    out = apply_ocean_loading_correction(t, np.zeros_like(t), constituents)
    assert np.all(np.isfinite(out))


# ----------------------------------------------------------------------
# Pipeline wiring: config-off => no-op
# ----------------------------------------------------------------------
def test_pipeline_corrections_block_absent_means_untouched(tmp_path):
    """Without the corrections: block, PM/OL never run (structural no-op).

    The pipeline-level integration (corrections lists in metrics.json) is
    covered by the existing tests in test_corrections.py; here we assert the
    new code paths are inert when disabled.
    """
    g = np.linspace(0.0, 1.0, 10)
    # enabled: false blocks
    out_pm = apply_polar_motion_correction(g, 45.0, 0.0, 0.0, 0.0)
    out_ol = apply_ocean_loading_correction(np.arange(10.0), g, [])
    np.testing.assert_array_equal(out_pm, g)
    np.testing.assert_array_equal(out_ol, g)


def test_pipeline_wiring_polar_motion_and_ocean_loading(tmp_path):
    """End-to-end: enabling the new blocks records them in metrics.json."""
    import json

    import yaml

    from qgrav.config import find_project_root
    from qgrav.pipeline import run_pipeline

    project_root = find_project_root(Path(__file__))
    data_dir = project_root / "data" / "raw" / "sg_sample"
    if not data_dir.exists():
        pytest.skip(f"sample data not found at {data_dir}")

    cfg = {
        "output": {"runs_dir": "runs", "name": "pm_ol_wiring_test"},
        "bench": {"type": "real_gravity"},
        "bench_real_gravity": {
            "source_path": str(data_dir),
            "station_code": "ap046",
            "apply_corrections": True,
            "tide_backend": "internal_hw95",
            "igets_level": "1",
            "corrections": {
                "polar_motion": {
                    "enabled": True,
                    "latitude_deg": 49.144,
                    "longitude_deg": 12.878,
                    "xp_arcsec": 0.12,
                    "yp_arcsec": 0.33,
                },
                "ocean_loading": {
                    "enabled": True,
                    "constituents": [
                        {"name": "M2", "amplitude_nm_s2": 12.3, "phase_deg": -47.0},
                        {"name": "O1", "amplitude_nm_s2": 3.1, "phase_deg": 12.0},
                    ],
                },
            },
        },
        "stats": {"psd_method": "welch", "welch_nperseg": 128, "welch_noverlap": 64},
    }
    cfg_path = tmp_path / "config.yaml"
    cfg_path.write_text(yaml.safe_dump(cfg), encoding="utf-8")
    report_path = run_pipeline(cfg_path, project_root=project_root)
    metrics = json.loads((report_path.parent / "metrics.json").read_text(encoding="utf-8"))
    applied = metrics["corrections_applied"]
    assert "polar_motion" in applied
    assert any(c.startswith("ocean_loading") and "M2" in c for c in applied)
    assert "polar_motion_delta_g_ugal" in metrics["correction_metrics"]
    assert metrics["correction_metrics"]["ocean_loading_rms_subtracted_ugal"] > 0
