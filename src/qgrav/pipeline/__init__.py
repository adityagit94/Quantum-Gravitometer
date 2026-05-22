"""Pipeline package — split from the original monolithic pipeline.py."""
from __future__ import annotations

import logging
from pathlib import Path

import matplotlib.pyplot as plt

from qgrav.config import load_config, resolve_runs_dir, validate_config
from qgrav.pipeline._common import _make_run_dir
from qgrav.pipeline._gravity import _run_real_gravity_pipeline
from qgrav.pipeline._interferometer import _run_interferometer_pipeline

logger = logging.getLogger(__name__)


def run_pipeline(config_path: Path, *, project_root: Path | None = None) -> Path:
    """Run the full qgrav pipeline from a YAML config file.

    Parameters
    ----------
    config_path:
        Path to the YAML configuration file (may be a temp file).
    project_root:
        Optional override for the project root directory. When the GUI
        materializes the config to a temp file, relative paths in the config
        cannot be resolved from the temp directory.  Passing the real project
        root ensures ``data/raw/...`` and similar paths resolve correctly.
    """
    try:
        cfg, cfg_text = load_config(config_path)
        validate_config(cfg)
        out_base = resolve_runs_dir(cfg, config_path)
        name = str(cfg.get("output", {}).get("name", "example"))
        paths = _make_run_dir(out_base, name)
        paths.config_copy.write_text(cfg_text, encoding="utf-8")

        bench_cfg = cfg.get("bench", {}) if isinstance(cfg.get("bench", {}), dict) else {}
        bench_type = str(bench_cfg.get("type", "virtual")).lower().strip()
        if bench_type == "real_gravity":
            return _run_real_gravity_pipeline(cfg, cfg_text, paths, config_path, project_root=project_root)
        return _run_interferometer_pipeline(cfg, cfg_text, paths, config_path, project_root=project_root)
    finally:
        plt.close("all")
