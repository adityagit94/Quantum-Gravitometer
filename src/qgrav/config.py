from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml


def load_config(config_path: Path) -> tuple[dict[str, Any], str]:
    text = config_path.read_text(encoding="utf-8")
    cfg = yaml.safe_load(text)
    if not isinstance(cfg, dict):
        raise ValueError("Configuration root must be a mapping/dictionary.")
    return cfg, text


def find_project_root(start: Path) -> Path:
    current = start.resolve()
    if current.is_file():
        current = current.parent
    for candidate in [current, *current.parents]:
        if (candidate / "pyproject.toml").exists():
            return candidate
    return current


def resolve_runs_dir(cfg: dict[str, Any], config_path: Path) -> Path:
    out_cfg = cfg.get("output", {})
    if not isinstance(out_cfg, dict):
        raise ValueError("output section must be a mapping/dictionary.")
    runs_dir = Path(str(out_cfg.get("runs_dir", "runs")))
    if runs_dir.is_absolute():
        return runs_dir
    project_root = find_project_root(config_path)
    return (project_root / runs_dir).resolve()


def validate_config_structure(cfg: dict[str, Any]) -> list[str]:
    issues: list[str] = []
    if not isinstance(cfg, dict):
        return ["Configuration root must be a mapping/dictionary."]

    bench = cfg.get("bench", {})
    if not isinstance(bench, dict):
        issues.append("`bench` must be a mapping/dictionary.")
        bench = {}
    bench_type = str(bench.get("type", "virtual")).strip().lower()
    if bench_type not in {"virtual", "real", "real_gravity"}:
        issues.append("`bench.type` must be one of: `virtual`, `real`, `real_gravity`.")

    if bench_type == "virtual":
        virtual_cfg = cfg.get("bench_virtual_ifo")
        if not isinstance(virtual_cfg, dict):
            issues.append("Virtual mode requires a `bench_virtual_ifo` section.")
        else:
            for key in [
                "wavelength_m",
                "sample_rate_hz",
                "duration_s",
                "displacement_sines",
                "measurement_noise_std",
            ]:
                if key not in virtual_cfg:
                    issues.append(f"Missing `bench_virtual_ifo.{key}`.")
    elif bench_type == "real":
        real_cfg = cfg.get("bench_real_ifo")
        if not isinstance(real_cfg, dict):
            issues.append("Real interferometer mode requires a `bench_real_ifo` section.")
        else:
            if "csv_path" not in real_cfg:
                issues.append("Missing `bench_real_ifo.csv_path`.")
    elif bench_type == "real_gravity":
        grav_cfg = cfg.get("bench_real_gravity")
        if not isinstance(grav_cfg, dict):
            issues.append("Real gravimetry mode requires a `bench_real_gravity` section.")
        else:
            if "source_path" not in grav_cfg:
                issues.append("Missing `bench_real_gravity.source_path`.")
            level = str(grav_cfg.get("igets_level", "auto")).strip().lower()
            if level not in {"auto", "1", "2", "3"}:
                issues.append("`bench_real_gravity.igets_level` must be one of: auto, 1, 2, 3.")
            tide_backend = str(grav_cfg.get("tide_backend", "auto")).strip().lower()
            if tide_backend not in {"auto", "pygtide", "internal_hw95"}:
                issues.append(
                    "`bench_real_gravity.tide_backend` must be one of: "
                    "auto, pygtide, internal_hw95."
                )

    stats = cfg.get("stats", {})
    if stats is not None and not isinstance(stats, dict):
        issues.append("`stats` must be a mapping/dictionary when present.")
    elif isinstance(stats, dict):
        backend = (
            str(stats.get("metrics_backend", stats.get("allan_backend", "auto"))).strip().lower()
        )
        if backend not in {"auto", "custom", "allantools"}:
            issues.append("`stats.metrics_backend` must be one of: auto, custom, allantools.")
        data_type = str(stats.get("allan_data_type", "freq")).strip().lower()
        if data_type not in {"freq", "phase"}:
            issues.append("`stats.allan_data_type` must be either `freq` or `phase`.")
        psd_method = str(stats.get("psd_method", "welch")).strip().lower()
        if psd_method not in {"welch", "periodogram"}:
            issues.append("`stats.psd_method` must be `welch` or `periodogram`.")

    alg = cfg.get("algorithms", {})
    if alg is not None and not isinstance(alg, dict):
        issues.append("`algorithms` must be a mapping/dictionary when present.")

    simulation = cfg.get("simulation", {})
    if simulation is not None and not isinstance(simulation, dict):
        issues.append("`simulation` must be a mapping/dictionary when present.")
    elif isinstance(simulation, dict) and simulation.get("enabled", False):
        backend = str(simulation.get("backend", "aisim")).strip().lower()
        if backend != "aisim":
            issues.append("`simulation.backend` currently supports only `aisim`.")
        model = str(simulation.get("model", "rabi_scan")).strip().lower()
        allowed_models = {
            "rabi_scan",
            "mach_zehnder_phase_scan",
            "gravity_sweep",
            "vibration_sensitivity_sweep",
        }
        if model not in allowed_models:
            issues.append(
                "`simulation.model` must be one of: rabi_scan, mach_zehnder_phase_scan, gravity_sweep, vibration_sensitivity_sweep."
            )
        if "n_atoms" not in simulation:
            issues.append("Missing `simulation.n_atoms` for enabled AISim simulation.")
        if model == "rabi_scan":
            for key in ["tau_step_s", "n_steps"]:
                if key not in simulation:
                    issues.append(f"Missing `simulation.{key}` for enabled AISim simulation.")
        elif model == "mach_zehnder_phase_scan":
            for key in ["tau_pi_half_s", "interferometer_time_s", "n_phase_points"]:
                if key not in simulation:
                    issues.append(f"Missing `simulation.{key}` for enabled AISim simulation.")
        elif model == "gravity_sweep":
            for key in [
                "tau_pi_half_s",
                "interferometer_time_s",
                "gravity_center_m_s2",
                "gravity_span_m_s2",
                "n_gravity_points",
            ]:
                if key not in simulation:
                    issues.append(f"Missing `simulation.{key}` for enabled AISim simulation.")
        elif model == "vibration_sensitivity_sweep":
            for key in [
                "tau_pi_half_s",
                "interferometer_time_s",
                "gravity_ref_m_s2",
                "vibration_frequency_hz",
                "amplitude_max_m",
                "n_amplitude_points",
            ]:
                if key not in simulation:
                    issues.append(f"Missing `simulation.{key}` for enabled AISim simulation.")
    return issues


def resolve_project_relative_path(
    config_path: Path,
    raw_path: str | None,
    *,
    project_root: Path | None = None,
) -> str | None:
    """Resolve a relative path from a config file to an absolute path.

    Resolution order:
    1. If *raw_path* is absolute, return it unchanged.
    2. Try relative to *config_path*'s parent directory.
    3. Try relative to *project_root* (or ``find_project_root(config_path)``).
    4. Fall back to the config-relative candidate (even if it doesn't exist).

    The *project_root* parameter allows callers (e.g. the GUI) to supply the
    real project root when *config_path* is a temporary file outside the repo.
    """
    if raw_path is None:
        return None
    p = Path(str(raw_path))
    if p.is_absolute():
        return str(p)
    base = config_path.parent.resolve()
    candidate = (base / p).resolve()
    if candidate.exists():
        return str(candidate)
    root = project_root or find_project_root(config_path)
    project_candidate = (root / p).resolve()
    return str(project_candidate if project_candidate.exists() else candidate)


def validate_config(cfg: dict[str, Any]) -> None:
    """Defensive config validation compatible with the current schema.

    This project uses `bench.type` / `simulation.enabled` rather than a single required
    top-level `mode`. If `mode` is present, validate it. Always run structural validation.
    """
    if not isinstance(cfg, dict):
        raise TypeError("Config must be dict")

    if "mode" in cfg:
        allowed_modes = {"sim", "real", "aisim"}
        mode = cfg.get("mode")
        if mode not in allowed_modes:
            raise ValueError(f"Invalid mode '{mode}'. Must be one of {allowed_modes}")

    issues = validate_config_structure(cfg)
    if issues:
        raise ValueError("Configuration validation failed:\n- " + "\n- ".join(issues))
