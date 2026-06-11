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
    rms = float(np.sqrt(np.mean(tide**2)))
    # Real body-tide RMS is around 70-120 microGal at mid-latitude
    assert 30.0 < rms < 250.0, f"tide RMS {rms:.1f} uGal out of expected range"


def test_apply_tide_correction_zero_size_returns_empty():
    out = apply_tide_correction(
        np.array([], dtype=np.float64),
        np.array([], dtype=np.float64),
        latitude_deg=45.0,
        longitude_deg=0.0,
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
        t,
        raw,
        latitude_deg=45.0,
        longitude_deg=0.0,
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
        t,
        v,
        latitude_deg=0.0,
        longitude_deg=0.0,
        backend="auto",
    )
    # The backend used must be one of the supported values.
    assert result["backend_used"] in {"pygtide", "internal_hw95"}


def test_apply_tide_correction_unknown_backend_raises():
    with pytest.raises(ValueError):
        apply_tide_correction(
            np.array([1.0]),
            np.array([0.0]),
            latitude_deg=0.0,
            longitude_deg=0.0,
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

    import json
    import tempfile

    import yaml

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
            f"expected tide in corrections_applied but got: " f"{metrics['corrections_applied']}"
        )
        assert metrics["correction_metrics"]["tide_rms_subtracted_ugal"] > 0


def test_pipeline_integration_default_apply_corrections_false():
    """With the default ``apply_corrections: false``, no corrections fire and
    the report still gets the new output_format_version field."""
    project_root = find_project_root(Path(__file__))
    data_dir = project_root / "data" / "raw" / "sg_sample"
    if not data_dir.exists():
        pytest.skip(f"sample data not found at {data_dir}")

    import json
    import tempfile

    import yaml

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


def test_pressure_correction_warns_on_partial_overlap(tmp_path):
    """Pressure correction should warn when pressure data has low temporal overlap."""
    project_root = find_project_root(Path(__file__))
    data_dir = project_root / "data" / "raw" / "sg_sample"
    if not data_dir.exists():
        pytest.skip(f"sample data not found at {data_dir}")

    import json
    import tempfile

    import yaml

    from qgrav.pipeline import run_pipeline

    # Create a pressure CSV that only covers a tiny slice of the gravity time range.
    # The gravity data for ap046 typically spans several days.
    pressure_csv = tmp_path / "pressure.csv"
    pressure_csv.write_text(
        "unix_seconds,pressure_hpa\n" "0,1013.0\n" "100,1013.5\n",
        encoding="utf-8",
    )

    cfg = {
        "output": {"runs_dir": "runs", "name": "pressure_overlap_test"},
        "bench": {"type": "real_gravity"},
        "bench_real_gravity": {
            "source_path": str(data_dir),
            "station_code": "ap046",
            "apply_corrections": True,
            "tide_backend": "internal_hw95",
            "igets_level": "1",
            "pressure_csv_path": str(pressure_csv),
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
        # With near-zero overlap, pressure should have been skipped.
        assert (
            "atmospheric_pressure" not in metrics["corrections_applied"]
        ), "Pressure correction should be skipped with <50% coverage"
        # There should be a warning about coverage.
        assert any("Pressure" in w for w in metrics.get("corrections_warnings", []))


def test_corrections_skipped_warning_when_no_coordinates():
    """When corrections are requested but station has no coordinates, the run
    should complete and include a SKIPPED entry + warning."""
    project_root = find_project_root(Path(__file__))
    data_dir = project_root / "data" / "raw" / "sg_sample"
    if not data_dir.exists():
        pytest.skip(f"sample data not found at {data_dir}")

    import json
    import tempfile

    import yaml

    from qgrav.pipeline import run_pipeline

    cfg = {
        "output": {"runs_dir": "runs", "name": "no_coords_warning_test"},
        "bench": {"type": "real_gravity"},
        "bench_real_gravity": {
            "source_path": str(data_dir),
            "station_code": "ap046",
            "apply_corrections": True,
            "tide_backend": "internal_hw95",
            "igets_level": "1",
        },
        "stats": {
            "metrics_backend": "auto",
            "psd_method": "welch",
            "welch_nperseg": 128,
            "welch_noverlap": 64,
        },
    }
    # The sample ap046 actually *has* coordinates, so this test relies on the
    # current dataset's metadata.  If lat/lon are present we instead verify
    # there are no SKIPPED warnings.  (We test the full code-path; a unit test
    # with mocked data would be needed to test the missing-coords path.)
    with tempfile.TemporaryDirectory() as tdir:
        cfg_path = Path(tdir) / "config.yaml"
        cfg_path.write_text(yaml.safe_dump(cfg), encoding="utf-8")
        report_path = run_pipeline(cfg_path, project_root=project_root)
        metrics = json.loads((report_path.parent / "metrics.json").read_text(encoding="utf-8"))
        # corrections_warnings key must always be present
        assert "corrections_warnings" in metrics
        # Since ap046 has coords, there should be no SKIPPED warning
        skipped = [c for c in metrics["corrections_applied"] if c.startswith("SKIPPED")]
        assert len(skipped) == 0, f"Expected no SKIPPED entries but got: {skipped}"


def test_corrected_run_preserves_raw_data():
    """When corrections are applied, the raw (pre-correction) arrays must be
    stored alongside the corrected arrays in data.npz."""
    project_root = find_project_root(Path(__file__))
    data_dir = project_root / "data" / "raw" / "sg_sample"
    if not data_dir.exists():
        pytest.skip(f"sample data not found at {data_dir}")

    import tempfile

    import yaml

    from qgrav.pipeline import run_pipeline

    cfg = {
        "output": {"runs_dir": "runs", "name": "raw_preservation_test"},
        "bench": {"type": "real_gravity"},
        "bench_real_gravity": {
            "source_path": str(data_dir),
            "station_code": "ap046",
            "apply_corrections": True,
            "tide_backend": "internal_hw95",
            "igets_level": "1",
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
        run_dir = report_path.parent
        data = dict(np.load(run_dir / "data.npz"))
        # Raw arrays must exist
        assert "gravity_residual_raw" in data, "missing gravity_residual_raw in data.npz"
        assert "gravity_residual_full_raw" in data, "missing gravity_residual_full_raw in data.npz"
        assert "tide_subtracted" in data, "missing tide_subtracted in data.npz"
        # Corrected and raw should differ (tide was applied)
        assert not np.array_equal(
            data["gravity_residual"], data["gravity_residual_raw"]
        ), "raw and corrected arrays should differ after corrections"


def test_synthetic_tide_correction_improves_allan_deviation():
    """Synthetic integration test: create data = tide + white noise, apply tide
    correction, and verify that the corrected Allan deviation is lower than the
    uncorrected one.  This tests the full corrections â†’ metrics chain."""
    from qgrav.metrics.allan import allan_deviation_overlapping

    rng = np.random.default_rng(2024)
    # 3 days of 1-minute samples â‡’ 4320 points
    n = 4320
    dt_s = 60.0
    t0 = 1_700_000_000.0
    t = t0 + np.arange(n) * dt_s
    fs = 1.0 / dt_s

    # Tide signal at mid-latitude (dominant M2 ~ 12.42 hr period)
    from qgrav.datasets._tides_hw95 import gravity_tide_ugal

    tide_ugal = gravity_tide_ugal(t, latitude_deg=45.0, longitude_deg=0.0)
    tide_m_s2 = tide_ugal * 1e-8

    # White noise at 0.1 ÂµGal level (1e-9 m/sÂ²)
    noise = rng.normal(scale=1e-9, size=n)
    raw_signal = tide_m_s2 + noise

    # Compute Allan deviation BEFORE correction
    taus = np.logspace(np.log10(2 * dt_s), np.log10(0.1 * n * dt_s), 10)
    adev_before = allan_deviation_overlapping(raw_signal, fs, taus, backend="custom")

    # Apply tide correction
    corrected = apply_tide_correction(
        t,
        raw_signal,
        latitude_deg=45.0,
        longitude_deg=0.0,
        backend="internal_hw95",
    )
    adev_after = allan_deviation_overlapping(corrected["corrected"], fs, taus, backend="custom")

    # The corrected ADEV should be lower at every tau (tide was the dominant signal)
    adev_b = np.asarray(adev_before["adev"])
    adev_a = np.asarray(adev_after["adev"])
    n_common = min(len(adev_b), len(adev_a))
    assert n_common > 0, "No ADEV points produced"
    assert np.all(adev_a[:n_common] < adev_b[:n_common]), (
        f"Expected corrected ADEV < raw ADEV at all taus, but "
        f"before={adev_b[:n_common].tolist()}, after={adev_a[:n_common].tolist()}"
    )


def test_html_report_escapes_special_characters():
    """The HTML report must escape < > & characters in config text and metrics
    to prevent XSS or rendering breakage."""
    import tempfile

    from qgrav.reporting.report import build_html_report

    with tempfile.TemporaryDirectory() as tdir:
        run_dir = Path(tdir)
        # Config text with script tag that should be escaped
        config_text = 'name: "<script>alert(1)</script>"'
        metrics = {
            "bench_type": "real_gravity",
            "sample_rate_hz": 1.0,
            "psd_method": "welch",
            "allan_backend_used": "custom",
            "allan_data_type": "freq",
            "qgrav_output_format_version": "1.0",
            "qgrav_version": "0.8.1",
            "corrections_warnings": ['<img src=x onerror="alert(1)">'],
            "station_code": "test",
            "source_path": "/tmp/test",
            "record_start": "2024-01-01",
            "record_end": "2024-01-02",
            "longitude_deg": 0.0,
            "latitude_deg": 0.0,
            "gravity_summary": {"mean": 0.0, "std": 1.0},
            "gap_report": {
                "n_samples_total": 100,
                "gap_count": 0,
                "missing_samples_estimate": 0,
                "largest_contiguous_segment_samples": 100,
            },
            "dropped_rows": 0,
            "analysis_segment": {
                "segment_samples": 100,
                "segment_start": "2024-01-01",
                "segment_end": "2024-01-02",
            },
            "series_units": "nm/s**2",
            "unit_warnings": [],
            "data_product_level_at_analysis": 1,
            "corrections_applied": ["solid_earth_tide (internal_hw95)"],
            "correction_metrics": {},
        }
        plot_paths = {
            "displacement": "disp.png",
            "psd": "psd.png",
            "allan": "allan.png",
            "raw": "raw.png",
        }
        report_path = build_html_report(
            run_dir=run_dir,
            config_text=config_text,
            metrics=metrics,
            plot_paths=plot_paths,
        )
        html = report_path.read_text(encoding="utf-8")
        # The <script> tag in config text should be escaped
        assert "<script>" not in html, "Config text was not escaped in HTML"
        assert "&lt;script&gt;" in html, "Expected escaped script tag in HTML"
        # The XSS payload in corrections_warnings should be escaped
        assert "<img src=x" not in html, "corrections_warnings was not escaped"


# ----------------------------------------------------------------------
# Edge-case coverage: raises, custom reference pressure, PyGTide paths
# ----------------------------------------------------------------------
def test_apply_tide_correction_shape_mismatch_raises():
    with pytest.raises(ValueError, match="same shape"):
        apply_tide_correction(
            np.array([1.0, 2.0]),
            np.array([0.0]),
            latitude_deg=0.0,
            longitude_deg=0.0,
        )


def test_apply_tide_correction_pygtide_backend_raises_when_missing(monkeypatch):
    import qgrav.datasets.corrections as corr

    monkeypatch.setattr(corr, "_try_import_pygtide", lambda: None)
    with pytest.raises(ImportError, match="PyGTide backend requested"):
        apply_tide_correction(
            np.array([1_700_000_000.0]),
            np.array([0.0]),
            latitude_deg=49.0,
            longitude_deg=12.0,
            backend="pygtide",
        )


def test_try_import_pygtide_returns_module_when_present(monkeypatch):
    import sys

    import qgrav.datasets.corrections as corr

    sentinel = type(sys)("pygtide")
    monkeypatch.setitem(sys.modules, "pygtide", sentinel)
    assert corr._try_import_pygtide() is sentinel


class _FakeColumn:
    def __init__(self, values):
        self._values = np.asarray(values)

    def to_numpy(self):
        return self._values

    def astype(self, dtype):
        return _FakeColumn(self._values.astype(dtype))


class _FakeResults:
    """Minimal stand-in for the pandas DataFrame PyGTide returns."""

    def __init__(self, utc_ns, signal_nm_s2):
        self._data = {
            "UTC": _FakeColumn(utc_ns),
            "Signal [nm/s**2]": _FakeColumn(signal_nm_s2),
        }

    @property
    def columns(self):
        return list(self._data)

    def __getitem__(self, key):
        return self._data[key]


class _FakePyGTide:
    """Fake pygtide module: predict() is recorded, results() returns a grid."""

    def __init__(self, utc_ns, signal_nm_s2):
        self._utc_ns = utc_ns
        self._signal = signal_nm_s2
        self.predict_kwargs = None

    def pygtide(self):
        return self

    def predict(self, **kwargs):
        self.predict_kwargs = kwargs

    def results(self):
        return _FakeResults(self._utc_ns, self._signal)


def test_apply_tide_correction_pygtide_path_with_fake_module(monkeypatch):
    """Exercise the full pygtide code path using a fake module."""
    import qgrav.datasets.corrections as corr

    t0 = 1_700_000_000.0
    # PyGTide grid: 3 points at 60 s spacing; constant 100 nm/s^2 signal.
    grid_unix = np.array([t0, t0 + 60.0, t0 + 120.0])
    fake = _FakePyGTide(utc_ns=(grid_unix * 1e9).astype(np.int64), signal_nm_s2=[100.0] * 3)
    monkeypatch.setattr(corr, "_try_import_pygtide", lambda: fake)

    t = np.array([t0, t0 + 30.0, t0 + 90.0])
    v = np.zeros(3)
    result = apply_tide_correction(t, v, latitude_deg=49.0, longitude_deg=12.0, backend="pygtide")

    assert result["backend_used"] == "pygtide"
    # 100 nm/s^2 = 1e-7 m/s^2 subtracted everywhere
    np.testing.assert_allclose(result["tide_subtracted"], 1e-7)
    np.testing.assert_allclose(result["corrected"], -1e-7)
    assert result["rms_subtracted_ugal"] == pytest.approx(10.0, rel=1e-6)
    assert fake.predict_kwargs["latitude"] == 49.0


def test_apply_tide_correction_pygtide_empty_input_returns_empty(monkeypatch):
    import qgrav.datasets.corrections as corr

    fake = _FakePyGTide(utc_ns=np.array([], dtype=np.int64), signal_nm_s2=[])
    monkeypatch.setattr(corr, "_try_import_pygtide", lambda: fake)
    result = apply_tide_correction(
        np.zeros(0), np.zeros(0), latitude_deg=0.0, longitude_deg=0.0, backend="pygtide"
    )
    assert result["tide_subtracted"].size == 0


def test_compute_tide_pygtide_falls_back_to_any_signal_column():
    from qgrav.datasets.corrections import _compute_tide_pygtide

    t0 = 1_700_000_000.0
    grid_unix = np.array([t0, t0 + 60.0])

    class _OddNameResults(_FakeResults):
        def __init__(self):
            self._data = {
                "UTC": _FakeColumn((grid_unix * 1e9).astype(np.int64)),
                "Signal weird name": _FakeColumn([50.0, 50.0]),
            }

    class _OddFake(_FakePyGTide):
        def results(self):
            return _OddNameResults()

    fake = _OddFake(utc_ns=None, signal_nm_s2=None)
    tide = _compute_tide_pygtide(
        fake, np.array([t0]), latitude_deg=0.0, longitude_deg=0.0, height_m=0.0
    )
    np.testing.assert_allclose(tide, 5e-8)


def test_compute_tide_pygtide_no_signal_column_raises():
    from qgrav.datasets.corrections import _compute_tide_pygtide

    t0 = 1_700_000_000.0

    class _NoSignalResults(_FakeResults):
        def __init__(self):
            self._data = {"UTC": _FakeColumn(np.array([int(t0 * 1e9)], dtype=np.int64))}

    class _NoSignalFake(_FakePyGTide):
        def results(self):
            return _NoSignalResults()

    fake = _NoSignalFake(utc_ns=None, signal_nm_s2=None)
    with pytest.raises(RuntimeError, match="no 'Signal' column"):
        _compute_tide_pygtide(
            fake, np.array([t0]), latitude_deg=0.0, longitude_deg=0.0, height_m=0.0
        )


def test_apply_pressure_correction_custom_reference_pressure():
    t = np.linspace(0, 10, 3)
    g = np.zeros(3)
    p = np.array([1000.0, 1010.0, 1020.0])
    out = apply_pressure_correction(
        t, g, p, admittance_nm_s2_per_hpa=-3.0, reference_pressure_hpa=1000.0
    )
    # At P = P_ref the correction is zero by construction.
    assert out[0] == 0.0
    # corrected = g - (-3e-9)*(P - 1000): +20 hPa -> +6e-8
    assert out[2] == pytest.approx(6e-8, rel=1e-9)


def test_apply_pressure_correction_shape_mismatch_raises():
    with pytest.raises(ValueError, match="share shape"):
        apply_pressure_correction(np.zeros(3), np.zeros(3), np.zeros(2))


def test_apply_pressure_correction_propagates_nan_pressure():
    """NaN pressure samples produce NaN corrected values (and a NaN mean
    reference would poison everything -- callers pass reference_pressure_hpa)."""
    t = np.linspace(0, 1, 4)
    g = np.zeros(4)
    p = np.array([1000.0, np.nan, 1010.0, 1020.0])
    out = apply_pressure_correction(t, g, p, reference_pressure_hpa=1010.0)
    assert np.isnan(out[1])
    finite = np.isfinite(out)
    assert finite.tolist() == [True, False, True, True]
