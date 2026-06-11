"""AISim simulation helpers for the pipeline."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

import numpy as np
from matplotlib.figure import Figure

from qgrav.pipeline._common import RunPaths, _jsonable
from qgrav.sim_ai import run_simulation_from_config

logger = logging.getLogger(__name__)


def _add_simulation(
    metrics: dict[str, Any], save_dict: dict[str, np.ndarray], sim_cfg: dict[str, Any]
) -> None:
    simulation_result = run_simulation_from_config(sim_cfg)
    if simulation_result is None:
        return
    metrics["simulation"] = {
        k: _jsonable(v) for k, v in simulation_result.items() if not isinstance(v, np.ndarray)
    }
    for key, value in simulation_result.items():
        if isinstance(value, np.ndarray):
            save_dict[f"sim_{key}"] = np.asarray(value, dtype=np.float64)


def _plot_series_from_spec(spec: dict[str, Any], data: Any, out_path: Path) -> Path:
    x = np.asarray(data[f"sim_{spec['x_key']}"], dtype=np.float64)
    x_scale = float(spec.get("x_scale", 1.0))
    fig = Figure(figsize=(9.0, 5.0))
    ax = fig.add_subplot(111)
    for series in spec.get("series", []):
        y = np.asarray(data[f"sim_{series['key']}"], dtype=np.float64)
        label = str(series.get("label", series["key"]))
        kind = str(series.get("kind", "line"))
        if kind == "line_markers":
            ax.plot(x * x_scale, y, marker="o", markersize=2.5, linewidth=1.2, label=label)
        elif kind == "dashed":
            ax.plot(x * x_scale, y, linestyle="--", linewidth=1.3, label=label)
        else:
            ax.plot(x * x_scale, y, linewidth=1.3, label=label)
    ax.set_xlabel(str(spec.get("x_label", spec["x_key"])))
    ax.set_ylabel(str(spec.get("y_label", "value")))
    ax.set_title(str(spec.get("title", "Simulation plot")))
    if len(spec.get("series", [])) > 1:
        ax.legend()
    fig.tight_layout()
    fig.savefig(out_path, dpi=160)
    return out_path


def _make_simulation_plots(paths: RunPaths, metrics: dict[str, Any]) -> list[dict[str, str]]:
    sim = metrics.get("simulation")
    if not isinstance(sim, dict):
        return []
    plot_specs = sim.get("plot_specs", [])
    if not isinstance(plot_specs, list):
        return []
    data = np.load(paths.data_path, allow_pickle=False)
    rendered: list[dict[str, str]] = []
    for idx, spec in enumerate(plot_specs):
        if not isinstance(spec, dict):
            continue
        name = str(spec.get("name", f"simulation_{idx}"))
        out_path = paths.plots_dir / f"{name}.png"
        try:
            _plot_series_from_spec(spec, data, out_path)
            rendered.append(
                {
                    "name": name,
                    "title": str(spec.get("title", name.replace("_", " ").title())),
                    "path": str(out_path.relative_to(paths.run_dir)),
                }
            )
        except Exception:
            logger.exception("Plot generation failed")
    return rendered
