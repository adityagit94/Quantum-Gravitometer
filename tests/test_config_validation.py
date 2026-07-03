"""Structural validation of every shipped YAML config.

Guards the README quick-start commands (``qgrav run --config configs/...``)
and the GUI run path, both of which call :func:`validate_config` /
:func:`validate_config_structure` before running the pipeline.  A config that
ships in ``configs/`` but fails validation is a release bug (regression:
``example_aisim_multi_drop.yaml`` failed because ``multi_drop_cycle`` was
missing from the validator's allowed models and the file lacked the
``bench_virtual_ifo`` section the pipeline requires for virtual-bench runs).
"""

from __future__ import annotations

import copy
from pathlib import Path

import pytest

from qgrav.config import find_project_root, load_config, validate_config, validate_config_structure

_PROJECT_ROOT = find_project_root(Path(__file__))
_CONFIG_FILES = sorted((_PROJECT_ROOT / "configs").glob("*.yaml"))


def test_shipped_configs_discovered():
    """The glob must actually see the shipped configs (guards a silent no-op)."""
    names = {p.name for p in _CONFIG_FILES}
    assert "example.yaml" in names
    assert "example_aisim_multi_drop.yaml" in names


@pytest.mark.parametrize("config_path", _CONFIG_FILES, ids=lambda p: p.name)
def test_every_shipped_config_validates(config_path: Path):
    cfg, _ = load_config(config_path)
    validate_config(cfg)  # raises ValueError on any structural issue


# ----------------------------------------------------------------------
# multi_drop_cycle validator branch
# ----------------------------------------------------------------------
_MULTI_DROP_CFG = {
    "output": {"runs_dir": "runs", "name": "multi_drop_unit_test"},
    "bench": {"type": "virtual"},
    "bench_virtual_ifo": {
        "wavelength_m": 1.55e-6,
        "sample_rate_hz": 2000,
        "duration_s": 5.0,
        "displacement_sines": [{"amplitude_m": 4.0e-9, "freq_hz": 3.0, "phase_rad": 0.0}],
        "measurement_noise_std": 0.03,
    },
    "simulation": {
        "enabled": True,
        "backend": "aisim",
        "model": "multi_drop_cycle",
        "n_atoms": 100,
        "tau_pi_half_s": 23e-6,
        "interferometer_time_s": 0.26,
        "n_drops": 8,
        "cycle_time_s": 1.0,
    },
}


def test_multi_drop_cycle_is_an_allowed_model():
    assert validate_config_structure(copy.deepcopy(_MULTI_DROP_CFG)) == []


def test_multi_drop_cycle_missing_knobs_are_flagged():
    cfg = copy.deepcopy(_MULTI_DROP_CFG)
    del cfg["simulation"]["n_drops"]
    del cfg["simulation"]["cycle_time_s"]
    issues = "\n".join(validate_config_structure(cfg))
    assert "simulation.n_drops" in issues
    assert "simulation.cycle_time_s" in issues


def test_gui_reproduction_configs_pass_validation():
    """The Validation tab's one-click reproduction configs must validate,
    since the GUI run path (`_prepare_run_config`) rejects configs that fail
    `validate_config_structure`."""
    pytest.importorskip("tkinter")
    import importlib

    from qgrav.gui._tab_validation import ValidationTabMixin

    class _BlankVar:
        def get(self) -> str:
            return ""

    class _FakeApp:
        repro_atoms_var = _BlankVar()
        repro_drops_var = _BlankVar()

    for suffix in ["freier_2016", "hu_2013", "menoret_2018", "xu_2022", "wu_2019"]:
        mod = importlib.import_module(f"qgrav.validation.{suffix}_setup")
        row = {"suffix": suffix, "module": mod}
        cfg = ValidationTabMixin._build_reproduction_config(_FakeApp(), row)
        validate_config(cfg)
