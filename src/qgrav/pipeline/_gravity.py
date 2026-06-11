"""Real-gravity pipeline stage."""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

import numpy as np

from qgrav import __version__
from qgrav.bench_ifo import load_real_gravity
from qgrav.config import resolve_project_relative_path
from qgrav.metrics import allan_deviation_overlapping
from qgrav.pipeline._common import (
    RunPaths,
    _compare_allan_backends,
    _jsonable,
    _logspace_taus,
    _stats_cfg,
    _write_run_metadata,
    _write_summary,
)
from qgrav.pipeline._plots import _make_real_gravity_plots
from qgrav.pipeline._simulation import _add_simulation
from qgrav.reporting import build_html_report

logger = logging.getLogger(__name__)


def _run_real_gravity_pipeline(
    cfg: dict[str, Any],
    cfg_text: str,
    paths: RunPaths,
    config_path: Path,
    *,
    project_root: Path | None = None,
) -> Path:
    grav_cfg = cfg.get("bench_real_gravity")
    if not isinstance(grav_cfg, dict):
        raise ValueError("Config missing required section 'bench_real_gravity'")
    data = load_real_gravity(
        source_path=resolve_project_relative_path(
            config_path, grav_cfg["source_path"], project_root=project_root
        )
        or grav_cfg["source_path"],
        station_code=grav_cfg.get("station_code"),
        metadata_path=resolve_project_relative_path(
            config_path, grav_cfg.get("metadata_path"), project_root=project_root
        ),
        segment_strategy=str(grav_cfg.get("segment_strategy", "longest_contiguous")),
        gap_tolerance_fraction=float(grav_cfg.get("gap_tolerance_fraction", 0.1)),
    )

    x_full = np.asarray(data["gravity_residual_full"], dtype=np.float64)
    t_full = np.asarray(data["t_full"], dtype=np.float64)
    x = np.asarray(data["gravity_residual"], dtype=np.float64)
    if x.size < 3:
        raise ValueError("Dataset too small. Need at least 3 samples.")
    t = np.asarray(data["t"], dtype=np.float64)
    fs = float(data["sample_rate_hz"])

    # Preserve raw arrays before any corrections are applied.
    x_full_raw = x_full.copy()
    x_raw = x.copy()
    tide_subtracted = np.array([])  # populated if tide correction runs

    # ----- v0.8: optional tide / pressure corrections -----
    corrections_applied: list[str] = []
    correction_metrics: dict[str, Any] = {}
    raw_igets_level_cfg = str(grav_cfg.get("igets_level", "auto")).lower()
    apply_corrections = bool(grav_cfg.get("apply_corrections", False))

    from qgrav.datasets.corrections import (
        apply_pressure_correction,
        apply_tide_correction,
        detect_igets_level,
    )

    if raw_igets_level_cfg == "auto":
        data_product_level = detect_igets_level(data)
    else:
        try:
            data_product_level = int(raw_igets_level_cfg)
        except ValueError:
            data_product_level = detect_igets_level(data)

    corrections_warnings: list[str] = []
    if apply_corrections and data_product_level < 3:
        lat = data.get("latitude_deg")
        lon = data.get("longitude_deg")
        if lat is not None and lon is not None:
            # Convert numpy datetime64 timestamps to Unix seconds.
            ts_full = data.get("timestamps_full")
            ts_seg = data.get("timestamps")
            if ts_full is not None and ts_seg is not None:
                unix_full = np.asarray(ts_full, dtype="datetime64[ns]").astype("int64") / 1e9
                unix_seg = np.asarray(ts_seg, dtype="datetime64[ns]").astype("int64") / 1e9
                tide_backend = str(grav_cfg.get("tide_backend", "auto"))
                try:
                    tide_full = apply_tide_correction(
                        unix_full,
                        x_full,
                        latitude_deg=float(lat),
                        longitude_deg=float(lon),
                        backend=tide_backend,
                    )
                    tide_seg = apply_tide_correction(
                        unix_seg,
                        x,
                        latitude_deg=float(lat),
                        longitude_deg=float(lon),
                        backend=tide_backend,
                    )
                    x_full = tide_full["corrected"]
                    x = tide_seg["corrected"]
                    tide_subtracted = tide_seg.get("tide_subtracted", np.array([]))
                    corrections_applied.append(f"solid_earth_tide ({tide_seg['backend_used']})")
                    correction_metrics["tide_rms_subtracted_ugal"] = float(
                        tide_seg["rms_subtracted_ugal"]
                    )
                    correction_metrics["tide_backend"] = tide_seg["backend_used"]
                except Exception as exc:
                    logger.warning("Tide correction skipped: %s", exc)
                    corrections_warnings.append(f"Tide correction failed: {exc}")
        else:
            logger.warning("Tide correction requested but no station coordinates available")
            corrections_applied.append("SKIPPED:tide (no station coordinates)")
            corrections_warnings.append(
                "Tide correction skipped: no station coordinates in metadata"
            )
        # Optional pressure correction
        pressure_path = grav_cfg.get("pressure_csv_path")
        if pressure_path:
            try:
                pressure_path_resolved = resolve_project_relative_path(
                    config_path, pressure_path, project_root=project_root
                )
                pressure_data = np.loadtxt(pressure_path_resolved, delimiter=",", skiprows=1)
                # Expect columns: unix_seconds, pressure_hpa
                p_t = pressure_data[:, 0]
                p_v = pressure_data[:, 1]
                ts_seg = data.get("timestamps")
                if ts_seg is not None:
                    unix_seg = np.asarray(ts_seg, dtype="datetime64[ns]").astype("int64") / 1e9
                    # Coverage check: ensure pressure data overlaps gravity series.
                    span = unix_seg[-1] - unix_seg[0]
                    if span > 0:
                        overlap_start = max(unix_seg[0], p_t[0])
                        overlap_end = min(unix_seg[-1], p_t[-1])
                        coverage = max(0.0, (overlap_end - overlap_start) / span)
                    else:
                        coverage = 1.0
                    if coverage < 0.5:
                        logger.warning(
                            "Pressure coverage %.0f%% — skipping correction", coverage * 100
                        )
                        corrections_warnings.append(
                            f"Pressure correction skipped: only {coverage*100:.0f}% temporal overlap"
                        )
                    else:
                        if coverage < 0.95:
                            logger.warning(
                                "Pressure coverage %.0f%% — applying with caution", coverage * 100
                            )
                            corrections_warnings.append(
                                f"Pressure coverage low: {coverage*100:.0f}% temporal overlap"
                            )
                        pressure_interp = np.interp(unix_seg, p_t, p_v)
                        admittance = float(grav_cfg.get("pressure_admittance_nm_s2_per_hpa", -3.0))
                        rms_pressure_before = float(np.std(x))
                        x = apply_pressure_correction(
                            unix_seg,
                            x,
                            pressure_interp,
                            admittance_nm_s2_per_hpa=admittance,
                        )
                        rms_pressure_after = float(np.std(x))
                        corrections_applied.append("atmospheric_pressure")
                        correction_metrics["pressure_admittance_nm_s2_per_hpa"] = admittance
                        correction_metrics["pressure_rms_change_ugal"] = (
                            rms_pressure_before - rms_pressure_after
                        ) * 1e8
                        correction_metrics["pressure_coverage_fraction"] = float(coverage)
            except Exception as exc:
                logger.warning("Pressure correction skipped: %s", exc)

        # ----- v1.5: polar motion + ocean loading (both off by default) -----
        corr_cfg = grav_cfg.get("corrections")
        corr_cfg = corr_cfg if isinstance(corr_cfg, dict) else {}
        ts_seg = data.get("timestamps")
        unix_seg_corr = (
            np.asarray(ts_seg, dtype="datetime64[ns]").astype("int64") / 1e9
            if ts_seg is not None
            else None
        )

        pm_cfg = corr_cfg.get("polar_motion")
        pm_cfg = pm_cfg if isinstance(pm_cfg, dict) else {}
        if bool(pm_cfg.get("enabled", False)):
            try:
                from qgrav.datasets.corrections import apply_polar_motion_correction

                pm_lat = pm_cfg.get("latitude_deg", data.get("latitude_deg"))
                pm_lon = pm_cfg.get("longitude_deg", data.get("longitude_deg"))
                if pm_lat is None or pm_lon is None:
                    raise ValueError("polar_motion needs station coordinates")
                before = x.copy()
                x = apply_polar_motion_correction(
                    x,
                    latitude_deg=float(pm_lat),
                    longitude_deg=float(pm_lon),
                    xp_arcsec=float(pm_cfg.get("xp_arcsec", 0.0)),
                    yp_arcsec=float(pm_cfg.get("yp_arcsec", 0.0)),
                    gravimetric_factor=float(pm_cfg.get("gravimetric_factor", 1.164)),
                )
                corrections_applied.append("polar_motion")
                correction_metrics["polar_motion_delta_g_ugal"] = float(np.mean(before - x) * 1e8)
            except Exception as exc:
                logger.warning("Polar-motion correction skipped: %s", exc)
                corrections_warnings.append(f"Polar-motion correction failed: {exc}")

        ol_cfg = corr_cfg.get("ocean_loading")
        ol_cfg = ol_cfg if isinstance(ol_cfg, dict) else {}
        if bool(ol_cfg.get("enabled", False)):
            try:
                from qgrav.datasets.corrections import apply_ocean_loading_correction

                if unix_seg_corr is None:
                    raise ValueError("ocean_loading needs sample timestamps")
                ol_constituents = ol_cfg.get("constituents") or []
                before = x.copy()
                x = apply_ocean_loading_correction(unix_seg_corr, x, ol_constituents)
                names = ",".join(str(c.get("name")) for c in ol_constituents)
                corrections_applied.append(f"ocean_loading ({names})")
                correction_metrics["ocean_loading_rms_subtracted_ugal"] = float(
                    np.sqrt(np.mean((before - x) ** 2)) * 1e8
                )
            except Exception as exc:
                logger.warning("Ocean-loading correction skipped: %s", exc)
                corrections_warnings.append(f"Ocean-loading correction failed: {exc}")
    # ----- end v0.8 corrections -----
    (
        psd_method,
        nperseg,
        noverlap,
        metrics_backend,
        allan_data_type,
        compare_allan_backends,
        comparison_backend,
    ) = _stats_cfg(cfg)
    nperseg = min(max(8, nperseg), len(x))
    noverlap = min(max(1, noverlap), max(1, nperseg - 1))
    taus = _logspace_taus(duration_s=float(t[-1] - t[0]) if len(t) > 1 else 1.0, sample_rate_hz=fs)

    adev = allan_deviation_overlapping(
        x, fs, taus, backend=metrics_backend, data_type=allan_data_type
    )

    from qgrav.metrics.allan import allan_minimum, identify_noise_type, identify_noise_type_acf

    _adev_arr = np.asarray(adev["adev"])
    _taus_arr = np.asarray(adev["taus_s"])
    # v0.8: primary noise-ID is the lag-1 autocorrelation method (Riley 2004);
    # the older log-log-slope fit is preserved alongside for cross-checking.
    noise_id = identify_noise_type_acf(x, data_type=allan_data_type)
    noise_id["legacy_slope_method"] = identify_noise_type(_taus_arr, _adev_arr)
    adev_min = allan_minimum(_taus_arr, _adev_arr)

    metrics: dict[str, Any] = {
        "qgrav_output_format_version": "1.0",
        "qgrav_version": __version__,
        "bench_type": "real_gravity",
        "have_truth": False,
        "sample_rate_hz": fs,
        "wavelength_m": None,
        "psd_method": psd_method,
        "welch_nperseg": nperseg,
        "welch_noverlap": noverlap,
        "allan_backend_used": str(adev["backend"]),
        "allan_data_type": str(adev["data_type"]),
        "series_units": data.get("units"),
        "data_product_level_at_analysis": int(data_product_level),
        "corrections_applied": corrections_applied,
        "corrections_warnings": corrections_warnings,
        "correction_metrics": correction_metrics,
        "station_code": data.get("station_code"),
        "longitude_deg": data.get("longitude_deg"),
        "latitude_deg": data.get("latitude_deg"),
        "source_path": data.get("source_path"),
        "source_kind": data.get("source_kind"),
        "record_start": data.get("record_start"),
        "record_end": data.get("record_end"),
        "gravity_summary": {
            "mean": float(np.mean(x)),
            "std": float(np.std(x)),
            "min": float(np.min(x)),
            "max": float(np.max(x)),
            "median": float(np.median(x)),
        },
        "gap_report": data.get("gap_report", {}),
        "analysis_segment": data.get("analysis_segment", {}),
        "unit_warnings": data.get("unit_warnings", []),
        "dropped_rows": int(data.get("dropped_rows", 0)),
        "noise_identification": noise_id,
        "allan_minimum": adev_min,
        "notes": [
            "This run uses real gravimetry time-series data rather than interferometer I/Q channels.",
            "PSD and Allan deviation are computed on the selected analysis segment of the gravity residual series.",
            "If gaps exist, the default strategy is to analyze the longest contiguous segment and report the gap statistics separately.",
        ],
    }
    if compare_allan_backends:
        primary_backend = str(adev["backend"])
        if comparison_backend == primary_backend:
            comparison_backend = "custom" if primary_backend != "custom" else "allantools"
        metrics["allan_backend_comparison"] = _compare_allan_backends(
            x,
            fs,
            taus,
            primary_backend=primary_backend,
            reference_backend=comparison_backend,
            data_type=allan_data_type,
        )

    save_dict: dict[str, np.ndarray] = {
        "t_full": t_full,
        "gravity_residual_full": x_full,
        "gravity_residual_full_raw": x_full_raw,
        "t": t,
        "gravity_residual": x,
        "gravity_residual_raw": x_raw,
        "tide_subtracted": tide_subtracted,
        "allan_taus": np.asarray(adev["taus_s"], dtype=np.float64),
        "allan_series": np.asarray(adev["adev"], dtype=np.float64),
    }
    sim_cfg = cfg.get("simulation", {}) if isinstance(cfg.get("simulation", {}), dict) else {}
    _add_simulation(metrics, save_dict, sim_cfg)

    try:
        from qgrav.physics.systematics import systematics_summary

        lat = data.get("latitude_deg")
        metrics["systematics"] = systematics_summary(
            latitude_deg=float(lat) if lat is not None else 45.0,
        )
    except Exception:
        logger.warning("Systematics computation failed", exc_info=True)

    metrics_jsonable = _jsonable(metrics)
    paths.metrics_path.write_text(json.dumps(metrics_jsonable, indent=2), encoding="utf-8")
    np.savez_compressed(paths.data_path, **save_dict)
    plot_paths = _make_real_gravity_plots(
        paths,
        metrics,
        t_full,
        x_full,
        t,
        x,
        fs,
        psd_method,
        nperseg,
        noverlap,
        adev,
        "simulation" in metrics,
    )
    _write_summary(paths.summary_path, metrics_jsonable)
    _write_run_metadata(paths.run_metadata_path, cfg, metrics_jsonable)
    return build_html_report(
        run_dir=paths.run_dir, config_text=cfg_text, metrics=metrics_jsonable, plot_paths=plot_paths
    )
