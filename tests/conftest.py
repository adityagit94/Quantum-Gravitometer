"""Shared pytest configuration and fixtures for the qgrav test suite.

Determinism notes
-----------------
- ``matplotlib.use("Agg")`` is set at import time so no GUI backend is ever
  loaded during testing, even if DISPLAY or MPLBACKEND are set.
- All tests that use random numbers should create their own
  ``np.random.default_rng(seed)`` rather than relying on the global state.
  The AISim global-state tests explicitly verify this.
- Statistical tests that compare two stochastic quantities should use
  generous tolerances and fixed seeds. If a test is inherently flaky, mark
  it with ``@pytest.mark.flaky`` so CI can retry it.
"""
from __future__ import annotations

import os

# Pin matplotlib backend before anything imports pyplot.
os.environ.setdefault("MPLBACKEND", "Agg")
import matplotlib
matplotlib.use("Agg")  # Non-interactive backend for CI / headless runs

import pytest
from pathlib import Path

from qgrav.config import find_project_root


@pytest.fixture
def project_root() -> Path:
    """Return the qgrav project root directory."""
    return find_project_root(Path(__file__))


@pytest.fixture
def sample_data_path(project_root: Path) -> Path:
    """Return path to the bundled sg_sample data directory."""
    return project_root / "data" / "raw" / "sg_sample"
