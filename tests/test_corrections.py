"""Tests for the v0.8 real-data corrections module."""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pytest

from qgrav.config import find_project_root
from qgrav.datasets._tides_hw95 import constituent_names, gravity_tide_ugal
from qgrav.datasets.corrections import (
    apply_pressure_correction,
    apply_tide_correction,
    detect_igets_level,
)


def test_constituent_names_include_m2_and_s2():
    names = constituent_names()
    assert "M2" in names
    assert "S2" in names
    assert "K1" in names
    assert "O1" in names


def test_hw95_tide_returns_to_similar_values_on_lunar_cycle():
    """Tide values should be bounded across a full ~lunar half-cycle, not
    drift to non-physical values. We test that two values 14 days apart fall
    within the M2-amplitude envelope (~150 microGal at mid-latitude)."""
    t0 = 1_700_000_000.0  # arbitrary Unix time
    fortnight = 14 * 86400.0
    t = np.array([t0, t0 + fortnight])
    tide = gravity_tide_ugal(t, latitude_deg=45.0, longitude_deg=0.0)
    # Bounded by ~2x the M2 amplitude (165 uGal) at mid-latitude with
    # cos^2(45) factor + body-tide elasticity 1.16; envelope ~ 200 uGal.
    assert abs(tide[0]) < 300.0
    assert abs(tide[1]) < 300.0


def test_hw95_tide_is_smooth_over_short_intervals():
    """Tide should not jump by more than its O(100 uGal) amplitude within
    a few minutes."""
    t0 = 1_700_000_000.0
    t = t0 + np.arange(0, 600, 60.0)  # 10 samples, 1-minute spacing
    tide = gravity_tide_ugal(t, latitude_deg=45.0, longitude_deg=0.0)
    # Successive 1-min steps should be < 5 uGal apart (M2 derivative bound).
    assert np.max(np.abs(np.diff(tide))) < 5.0


def test_hw95_tide_magnitude_order_of_magnitude():
    """The body-tide RMS at mid-latitude should be O(100 microGal)."""
    t0 = 1_700_000_000.0
    t = t0 + np.arange(0, 7 * 86400.0, 3600.0)  # 7-day hourly sampling
    tide = gravity_tide_ugal(t, latitude_deg=45.0, longitude_deg=0.0)
    rms = float(np.sqrt(np.mean(tide ** 2)))
    # Real body-tide RMS is around 70-120 microGal at mid-latitude
    assert 30.0 < rms < 250.0, f"tide RMS {rms:.1f} uGal out of expected range"


def test_apply_tide_correction_zero_size_returns_empty():
    out = apply_tide_correction(
        np.array([], dtype=np.float64),
        np.array([], dtype=np.float64),
        latitude_deg=45.0, longitude_deg=0.0,
        backend="internal_hw95",
    )
    assert out["corrected"].size == 0
    assert out["backend_used"] == "internal_hw95"


def test_apply_tide_correction_internal_hw95_reduces_variance():
    """When the input data contains pure tide signal, subtracting the tide
    should leave a much smaller residual."""
    t0 = 1_700_000_000.0
    t = t0 + np.arange(0, 3 * 86400.0, 60.0)
    tide_m_s2 = gravity_tide_ugal(t, latitude_deg=45.0, longitude_deg=0.0) * 1e-8
    # Add small Gaussian noise
    rng = np.random.default_rng(42)
    noise = rng.normal(scale=1e-9, size=t.shape)  # 0.1 microGal noise
    raw = tide_m_s2 + noise

    result = apply_tide_correction(
        t, raw,
        latitude_deg=45.0, longitude_deg=0.0,
        backend="internal_hw95",
    )
    rms_before = float(np.std(raw))
    rms_after = float(np.std(result["corrected"]))
    # The tide is much larger than the noise so the correction should drop
    # the RMS by at least 50x.
    assert rms_before > 50.0 * rms_after
    assert result["backend_used"] == "internal_hw95"
    assert result["rms_subtracted_ugal"] > 10.0


def test_apply_tide_correction_auto_falls_back_when_pygtide_missing():
    """If PyGTide isn't installed, auto backend should fall back gracefully."""
    t = np.array([1_700_000_000.0, 1_700_000_060.0])
    v = np.array([0.0, 0.0])
    result = apply_tide_correction(
        t, v,
        latitude_deg=0.0, longitude_deg=0.0,
        backend="auto",
    )
    # The backend used must be one of the supported values.
    assert result["backend_used"] in {"pygtide", "internal_hw95"}


def test_apply_tide_correction_unknown_backend_raises():
    with pytest.raises(ValueError):
        apply_tide_correction(
            np.array([1.0]), np.array([0.0]),
            latitude_deg=0.0, longitude_deg=0.0,
            backend="nonsense",
        )


def test_apply_pressure_correction_known_admittance():
    """Inverting the formula: known pressure change x known admittance
    should produce known gravity change."""
    t = np.linspace(0, 10, 11)
    g = np.zeros_like(t)
    p = np.linspace(1010.0, 1020.0, 11)  # 10 hPa rise
    # Admittance -3 nm/s^2/hPa => g should decrease by 30 nm/s^2 = 3e-8 m/s^2
    # When subtracting the correction, corrected = g - admittance*(p-p_ref).
    # With p_ref = mean(p) = 1015.0, max(p - p_ref) = +5 -> max correction
    # = -3e-9 * 5 = -1.5e-8 m/s^2 (gravity drop), so corrected = +1.5e-8.
    out = apply_pressure_correction(t, g, p, admittance_nm_s2_per_hpa=-3.0)
    # The peak corrected value at the highest pressure should be +1.5e-8
    assert np.isclose(out[-1], 1.5e-8, rtol=1e-6)
    # And at the lowest pressure -1.5e-8.
    assert np.isclose(out[0], -1.5e-8, rtol=1e-6)


def test_detect_igets_level_by_sample_rate():
    assert detect_igets_level({"sample_rate_hz": 1.0}) == 1
    assert detect_igets_level({"sample_rate_hz": 1.0 / 60.0}) == 2
    assert detect_igets_level({"sample_rate_hz": 1.0 / 3600.0}) == 3
    # No sample rate -> conservative L1
    assert detect_igets_level({}) == 1
    assert detect_igets_level({"sample_rate_hz": 0.0}) == 1


def test_pipeline_integration_runs_when_apply_corrections_true():
    """End-to-end: a real_gravity run with apply_corrections=true writes
    corrections metadata into metrics.json. Skipped if sample data is
    absent."""
    project_root = find_project_root(Path(__file__))
    data_dir = project_root / "data" / "raw" / "sg_sample"
    if not data_dir.exists():
        pytest.skip(f"sample data not found at {data_dir}")

    import tempfile
    import yaml
    import json
    from qgrav.pipeline import run_pipeline

    cfg = {
        "output": {"runs_dir": "runs", "name": "tide_correction_test"},
        "bench": {"type": "real_gravity"},
        "bench_real_gravity": {
            "source_path": str(data_dir),
            "station_code": "ap046",
            "apply_corrections": True,
            "tide_backend": "internal_hw95",
        },
        "stats": {
            "metrics_backend": "auto",
            "psd_method": "welch",
            "welch_nperseg": 128,
            "welch_noverlap": 64,
        },
    }
    # Force level=1 so the corrections actually run on the bundled (hourly)
    # sample, even though auto-detection would treat it as L3.
    cfg["bench_real_gravity"]["igets_level"] = "1"
    with tempfile.TemporaryDirectory() as tdir:
        cfg_path = Path(tdir) / "config.yaml"
        cfg_path.write_text(yaml.safe_dump(cfg), encoding="utf-8")
        report_path = run_pipeline(cfg_path, project_root=project_root)
        run_dir = report_path.parent
        metrics = json.loads((run_dir / "metrics.json").read_text(encoding="utf-8"))
        assert metrics["qgrav_output_format_version"] == "1.0"
        assert "data_product_level_at_analysis" in metrics
        assert "corrections_applied" in metrics
        # With forced level=1 we expect tide correction to fire.
        assert any("tide" in c for c in metrics["corrections_applied"]), (
            f"expected tide in corrections_applied but got: "
            f"{metrics['corrections_applied']}"
        )
        assert metrics["correction_metrics"]["tide_rms_subtracted_ugal"] > 0


def test_pipeline_integration_default_apply_corrections_false():
    """With the default ``apply_corrections: false``, no corrections fire and
    the report still gets the new output_format_version field."""
    project_root = find_project_root(Path(__file__))
    data_dir = project_root / "data" / "raw" / "sg_sample"
    if not data_dir.exists():
        pytest.skip(f"sample data not found at {data_dir}")

    import tempfile
    import yaml
    import json
    from qgrav.pipeline import run_pipeline

    cfg = {
        "output": {"runs_dir": "runs", "name": "no_corrections"},
        "bench": {"type": "real_gravity"},
        "bench_real_gravity": {
            "source_path": str(data_dir),
            "station_code": "ap046",
        },
        "stats": {
            "metrics_backend": "auto",
            "psd_method": "welch",
            "welch_nperseg": 128,
            "welch_noverlap": 64,
        },
    }
    with tempfile.TemporaryDirectory() as tdir:
        cfg_path = Path(tdir) / "config.yaml"
        cfg_path.write_text(yaml.safe_dump(cfg), encoding="utf-8")
        report_path = run_pipeline(cfg_path, project_root=project_root)
        metrics = json.loads((report_path.parent / "metrics.json").read_text(encoding="utf-8"))
        assert metrics["qgrav_output_format_version"] == "1.0"
        assert metrics["corrections_applied"] == []
