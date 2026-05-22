"""Tests for qgrav CLI commands (info, validate-data, run --dry-run)."""
from __future__ import annotations

import json
import sys
from pathlib import Path
from unittest import mock

import pytest

from qgrav.config import find_project_root


def _run_cli(*argv: str) -> str:
    """Run the CLI with the given args and capture stdout."""
    import io
    from qgrav.cli import main

    buf = io.StringIO()
    with mock.patch.object(sys, "argv", ["qgrav", *argv]), \
         mock.patch("sys.stdout", buf):
        main()
    return buf.getvalue()


def test_info_prints_version():
    out = _run_cli("info")
    assert "qgrav version:" in out
    assert "Python:" in out
    assert "numpy" in out


def test_info_shows_vendored_packages():
    out = _run_cli("info")
    assert "Vendored packages:" in out
    assert "allantools:" in out


def test_validate_data_on_sample_dataset():
    project_root = find_project_root(Path(__file__))
    data_dir = project_root / "data" / "raw" / "sg_sample"
    if not data_dir.exists():
        pytest.skip(f"sample data not found at {data_dir}")
    out = _run_cli("validate-data", "--source", str(data_dir))
    assert "Station code:" in out
    assert "Sample rate:" in out
    assert "Validation complete." in out


def test_validate_data_nonexistent_source():
    with pytest.raises(SystemExit):
        _run_cli("validate-data", "--source", "/nonexistent/path/to/data")


def test_dry_run_validates_config():
    project_root = find_project_root(Path(__file__))
    cfg_path = project_root / "configs" / "example_real_gravity.yaml"
    if not cfg_path.exists():
        pytest.skip(f"config not found at {cfg_path}")
    out = _run_cli("run", "--config", str(cfg_path), "--dry-run")
    assert "dry-run" in out
    assert "Bench type:" in out
    assert "Config validated OK" in out


def test_dry_run_invalid_config(tmp_path):
    cfg_path = tmp_path / "bad.yaml"
    cfg_path.write_text("not: a: valid: qgrav: config\n", encoding="utf-8")
    # Should raise because validation will fail (no required keys)
    with pytest.raises(Exception):
        _run_cli("run", "--config", str(cfg_path), "--dry-run")
