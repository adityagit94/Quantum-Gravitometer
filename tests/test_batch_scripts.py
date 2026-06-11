"""Functional tests for batch processing scripts.

Uses synthetic .ggp data in a temporary directory to exercise
``batch_scan_stations.scan_station`` and the CLI entry points.
"""

from __future__ import annotations

import csv
import subprocess
import sys
from pathlib import Path

import numpy as np
import pytest

# ---------------------------------------------------------------------------
# Helpers to create synthetic IGETS/GGP files
# ---------------------------------------------------------------------------

_GGP_HEADER = """\
Station: {code}
Latitude: 48.000
Longitude: 11.000
"""


def _make_ggp_file(
    path: Path, code: str, n_samples: int = 200, *, include_nan: bool = False
) -> None:
    """Write a synthetic .ggp file with ``n_samples`` rows."""
    rng = np.random.default_rng(42)
    lines = [_GGP_HEADER.format(code=code)]
    base_ts = np.datetime64("2024-01-01T00:00:00", "s")
    for i in range(n_samples):
        ts = base_ts + np.timedelta64(i * 60, "s")  # 1-minute sampling
        dt = ts.astype("datetime64[s]").astype(object)
        date_str = dt.strftime("%Y%m%d")
        time_str = dt.strftime("%H%M%S")
        if include_nan and i == 5:
            lines.append(f"{date_str} {time_str} NaN\n")
        else:
            val = rng.normal(0.0, 1.0)
            lines.append(f"{date_str} {time_str} {val:.6f}\n")
    path.write_text("".join(lines), encoding="utf-8")


@pytest.fixture()
def synthetic_source(tmp_path: Path) -> Path:
    """Create a temp directory with two synthetic .ggp station files."""
    _make_ggp_file(tmp_path / "ST01.ggp", "ST01", n_samples=200)
    _make_ggp_file(tmp_path / "ST02.ggp", "ST02", n_samples=150, include_nan=True)
    return tmp_path


# ---------------------------------------------------------------------------
# Tests for batch_scan_stations
# ---------------------------------------------------------------------------


def test_scan_station_returns_metrics(synthetic_source: Path):
    """scan_station should return a dict with statistical keys."""
    sys.path.insert(0, str(Path(__file__).resolve().parents[0] / ".." / "scripts"))
    from batch_scan_stations import scan_station

    row = scan_station(synthetic_source, "ST01")
    assert row["station_code"] == "ST01"
    assert "error" not in row
    assert row["n_samples"] >= 100
    assert isinstance(row["mean"], float)
    assert isinstance(row["std"], float)


def test_scan_station_handles_missing_station(synthetic_source: Path):
    """scan_station should return an error dict for a missing station."""
    sys.path.insert(0, str(Path(__file__).resolve().parents[0] / ".." / "scripts"))
    from batch_scan_stations import scan_station

    row = scan_station(synthetic_source, "NONEXISTENT")
    assert "error" in row


def test_batch_scan_cli_produces_csv(synthetic_source: Path, tmp_path: Path):
    """Running batch_scan_stations.py via CLI should produce a valid CSV."""
    script = Path(__file__).resolve().parents[0] / ".." / "scripts" / "batch_scan_stations.py"
    output_csv = tmp_path / "output.csv"
    result = subprocess.run(
        [
            sys.executable,
            str(script),
            "--source",
            str(synthetic_source),
            "--output",
            str(output_csv),
        ],
        capture_output=True,
        text=True,
        timeout=60,
    )
    assert result.returncode == 0, f"stderr: {result.stderr}"
    assert output_csv.exists()
    with open(output_csv, encoding="utf-8") as f:
        reader = csv.DictReader(f)
        rows = list(reader)
    assert len(rows) == 2
    codes = {r["station_code"] for r in rows}
    assert "ST01" in codes
    assert "ST02" in codes


def test_batch_scan_cli_missing_source(tmp_path: Path):
    """CLI should exit with error for non-existent source."""
    script = Path(__file__).resolve().parents[0] / ".." / "scripts" / "batch_scan_stations.py"
    result = subprocess.run(
        [sys.executable, str(script), "--source", str(tmp_path / "no_such_dir")],
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert result.returncode != 0


# ---------------------------------------------------------------------------
# Tests for multi_station_comparison
# ---------------------------------------------------------------------------


def test_multi_station_comparison_cli_produces_png(synthetic_source: Path, tmp_path: Path):
    """Running multi_station_comparison.py via CLI should produce a PNG."""
    script = Path(__file__).resolve().parents[0] / ".." / "scripts" / "multi_station_comparison.py"
    output_png = tmp_path / "comparison.png"
    result = subprocess.run(
        [
            sys.executable,
            str(script),
            "--source",
            str(synthetic_source),
            "--output",
            str(output_png),
        ],
        capture_output=True,
        text=True,
        timeout=60,
    )
    assert result.returncode == 0, f"stderr: {result.stderr}"
    assert output_png.exists()
    assert output_png.stat().st_size > 1000  # non-trivial PNG


def test_multi_station_comparison_cli_missing_source(tmp_path: Path):
    """CLI should exit with error for non-existent source."""
    script = Path(__file__).resolve().parents[0] / ".." / "scripts" / "multi_station_comparison.py"
    result = subprocess.run(
        [sys.executable, str(script), "--source", str(tmp_path / "no_such_dir")],
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert result.returncode != 0
