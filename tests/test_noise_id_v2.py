"""Tests for the lag-1 autocorrelation noise-type identification."""
from __future__ import annotations

import numpy as np
import pytest

from qgrav.metrics.allan import identify_noise_type_acf


def _white_freq_series(n: int, seed: int) -> np.ndarray:
    rng = np.random.default_rng(seed)
    return rng.normal(0.0, 1.0, size=n)


def _random_walk_freq_series(n: int, seed: int) -> np.ndarray:
    rng = np.random.default_rng(seed)
    return np.cumsum(rng.normal(0.0, 1.0, size=n))


def test_acf_identifies_white_frequency_noise_majority():
    """alpha_int = 0 means white frequency noise. Should hold in >=85% of
    trials over a 5000-sample series."""
    hits = 0
    n_trials = 60
    for seed in range(n_trials):
        x = _white_freq_series(5000, seed=seed)
        out = identify_noise_type_acf(x, data_type="freq")
        if out["alpha_int"] == 0:
            hits += 1
    assert hits >= int(0.85 * n_trials), f"only {hits}/{n_trials} white-FM hits"


def test_acf_identifies_random_walk_negative_alpha():
    """For random-walk-frequency noise, alpha_int = -2 most of the time."""
    hits = 0
    n_trials = 30
    for seed in range(n_trials):
        x = _random_walk_freq_series(5000, seed=seed)
        out = identify_noise_type_acf(x, data_type="freq")
        if out["alpha_int"] is not None and out["alpha_int"] <= -1:
            hits += 1
    assert hits >= int(0.8 * n_trials), f"only {hits}/{n_trials} negative-alpha hits"


def test_acf_returns_insufficient_data_for_short_series():
    out = identify_noise_type_acf(np.zeros(5), data_type="freq")
    assert out["noise_type"] == "insufficient_data"


def test_acf_includes_method_and_description():
    x = _white_freq_series(1000, seed=0)
    out = identify_noise_type_acf(x, data_type="freq")
    assert out["method"] == "lag1_autocorrelation"
    assert "ACF-based" in out["description"]
    assert "alpha" in out["description"]


def test_pipeline_stores_acf_with_legacy_slope():
    """Sanity check: the pipeline structure stores ACF method and legacy slope
    side by side. (Run a tiny virtual-bench pipeline to verify the output
    schema.)"""
    import tempfile
    import json
    import yaml
    from pathlib import Path
    from qgrav.pipeline import run_pipeline

    cfg = {
        "output": {"runs_dir": "runs", "name": "noise_id_v2_test"},
        "bench": {"type": "real_gravity"},
        "bench_real_gravity": {},
    }
    # This path is set up by other tests if data is bundled. We use it via
    # the find_project_root helper.
    from qgrav.config import find_project_root
    data_dir = find_project_root(Path(__file__)) / "data" / "raw" / "sg_sample"
    if not data_dir.exists():
        pytest.skip("sample data not present")
    cfg["bench_real_gravity"]["source_path"] = str(data_dir)
    cfg["bench_real_gravity"]["station_code"] = "ap046"
    cfg["stats"] = {
        "metrics_backend": "auto",
        "psd_method": "welch",
        "welch_nperseg": 128,
        "welch_noverlap": 64,
    }
    with tempfile.TemporaryDirectory() as tdir:
        cfg_path = Path(tdir) / "c.yaml"
        cfg_path.write_text(yaml.safe_dump(cfg), encoding="utf-8")
        report = run_pipeline(cfg_path, project_root=find_project_root(Path(__file__)))
        metrics = json.loads((report.parent / "metrics.json").read_text())
        ni = metrics["noise_identification"]
        assert ni["method"] == "lag1_autocorrelation"
        assert "legacy_slope_method" in ni
        assert ni["legacy_slope_method"]["method"] == "log_log_slope_fit"
