"""Tests for issues found in the v0.9.2 codebase audit."""
from __future__ import annotations

import json
import math
import sys
from io import StringIO
from pathlib import Path
from unittest import mock

import numpy as np
import pytest

# ─── A: phase_models input validation ────────────────────────────────────


def test_equivalent_gravity_error_rejects_zero_k_eff():
    from qgrav.physics.phase_models import equivalent_gravity_error_m_s2

    with pytest.raises(ValueError, match="k_eff_rad_per_m must be positive"):
        equivalent_gravity_error_m_s2(1.0, k_eff_rad_per_m=0.0, interferometer_time_s=0.1)


def test_equivalent_gravity_error_rejects_negative_T():
    from qgrav.physics.phase_models import equivalent_gravity_error_m_s2

    with pytest.raises(ValueError, match="interferometer_time_s must be positive"):
        equivalent_gravity_error_m_s2(1.0, k_eff_rad_per_m=1e7, interferometer_time_s=-0.1)


def test_equivalent_gravity_error_valid_inputs():
    from qgrav.physics.phase_models import equivalent_gravity_error_m_s2

    result = equivalent_gravity_error_m_s2(
        np.pi, k_eff_rad_per_m=1e7, interferometer_time_s=0.1
    )
    assert np.isfinite(result)
    assert float(result) > 0


# ─── C: interpolate_psd rejects zero frequency ──────────────────────────


def test_interpolate_psd_rejects_zero_frequency():
    from qgrav.physics._seismic_models import interpolate_psd

    with pytest.raises(ValueError, match="positive"):
        interpolate_psd(np.array([0.0, 1.0, 2.0]))


def test_interpolate_psd_rejects_negative_frequency():
    from qgrav.physics._seismic_models import interpolate_psd

    with pytest.raises(ValueError, match="positive"):
        interpolate_psd(np.array([-1.0, 1.0]))


def test_interpolate_psd_valid_frequencies():
    from qgrav.physics._seismic_models import interpolate_psd

    result = interpolate_psd(np.array([0.01, 0.1, 1.0, 10.0]), model="nlnm")
    assert np.all(np.isfinite(result))
    assert np.all(result > 0)


# ─── D: empty tide RMS is NaN ───────────────────────────────────────────


def test_tide_correction_empty_rms_is_nan():
    from qgrav.datasets.corrections import apply_tide_correction

    result = apply_tide_correction(
        np.array([], dtype=np.float64),
        np.array([], dtype=np.float64),
        latitude_deg=45.0,
        longitude_deg=0.0,
        backend="internal_hw95",
    )
    assert math.isnan(result["rms_subtracted_ugal"])


# ─── E: CLI error handling ──────────────────────────────────────────────


def test_cli_run_bad_config_exits_cleanly(tmp_path):
    """CLI should print a clean error (not a raw traceback) for invalid configs."""
    from qgrav.cli import main

    bad_cfg = tmp_path / "bad.yaml"
    bad_cfg.write_text("bench:\n  type: nonexistent_type\n", encoding="utf-8")

    buf = StringIO()
    with mock.patch.object(sys, "argv", ["qgrav", "run", "--config", str(bad_cfg)]), \
         mock.patch("sys.stderr", buf):
        with pytest.raises(SystemExit) as exc_info:
            main()
    assert exc_info.value.code == 1
    stderr_output = buf.getvalue()
    assert "Error" in stderr_output


def test_cli_verbose_shows_traceback(tmp_path):
    """With --verbose, the full traceback should appear in stderr."""
    from qgrav.cli import main

    bad_cfg = tmp_path / "bad.yaml"
    bad_cfg.write_text("bench:\n  type: nonexistent_type\n", encoding="utf-8")

    buf = StringIO()
    with mock.patch.object(sys, "argv", ["qgrav", "--verbose", "run", "--config", str(bad_cfg)]), \
         mock.patch("sys.stderr", buf):
        with pytest.raises(SystemExit):
            main()
    stderr_output = buf.getvalue()
    assert "Traceback" in stderr_output


# ─── J: _jsonable extended numpy types ───────────────────────────────────


def test_jsonable_handles_numpy_datetime64():
    from qgrav.pipeline._common import _jsonable

    dt = np.datetime64("2024-01-15T12:30:00")
    result = _jsonable(dt)
    assert isinstance(result, str)
    assert "2024" in result


def test_jsonable_handles_numpy_timedelta64():
    from qgrav.pipeline._common import _jsonable

    td = np.timedelta64(90500, "ms")  # 90.5 seconds
    result = _jsonable(td)
    assert isinstance(result, float)
    assert abs(result - 90.5) < 1e-6


def test_jsonable_handles_nat_timedelta():
    from qgrav.pipeline._common import _jsonable

    td = np.timedelta64("NaT")
    result = _jsonable(td)
    assert result is None


def test_jsonable_handles_numpy_str():
    from qgrav.pipeline._common import _jsonable

    result = _jsonable(np.str_("hello"))
    assert result == "hello"
    assert isinstance(result, str)


def test_jsonable_full_dict_serializes():
    from qgrav.pipeline._common import _jsonable

    data = {
        "timestamp": np.datetime64("2024-01-01"),
        "duration": np.timedelta64(3600, "s"),
        "value": np.float64(1.23),
        "count": np.int64(42),
        "name": np.str_("test"),
    }
    result = _jsonable(data)
    # Must be JSON-serializable
    json.dumps(result)


# ─── H: PSD guard — short data doesn't crash plots ──────────────────────


def test_plot_psd_short_data_no_crash():
    """_plot_psd should not crash when PSD has only 1 frequency bin."""
    from qgrav.visuals import _plot_psd
    from matplotlib.figure import Figure

    fig = Figure()
    ax = fig.add_subplot(111)
    # 4 samples (minimum for PSD) at fs=1 → rfftfreq gives 3 bins
    x = np.array([1.0, 2.0, 3.0, 4.0])
    # Should not raise
    _plot_psd(ax, x, fs=1.0, label="test", psd_method="periodogram", nperseg=4, noverlap=0)


# ─── M: pipeline entry points reject missing config sections ────────────


def test_gravity_pipeline_rejects_missing_config_section():
    from qgrav.pipeline._gravity import _run_real_gravity_pipeline
    from qgrav.pipeline._common import RunPaths

    cfg = {"bench": {"type": "real_gravity"}}  # missing bench_real_gravity
    paths = RunPaths(
        run_dir=Path("/tmp/fake"), plots_dir=Path("/tmp/fake/plots"),
        data_path=Path("/tmp/fake/data.npz"), config_copy=Path("/tmp/fake/cfg.yaml"),
        metrics_path=Path("/tmp/fake/m.json"), summary_path=Path("/tmp/fake/s.md"),
        run_metadata_path=Path("/tmp/fake/rm.json"),
    )
    with pytest.raises(ValueError, match="bench_real_gravity"):
        _run_real_gravity_pipeline(cfg, "", paths, Path("/tmp/fake.yaml"))
