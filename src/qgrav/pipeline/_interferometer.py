"""Interferometer (virtual / real IFO) pipeline stage."""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

import numpy as np

from qgrav import __version__
from qgrav.algorithms import estimate_displacement_baseline, estimate_displacement_improved
from qgrav.bench_ifo import generate_virtual_ifo, load_real_ifo_csv
from qgrav.config import resolve_project_relative_path
from qgrav.metrics import (
    allan_deviation_overlapping,
    compute_error_statistics,
    compute_psd,
    improvement_percent,
)
from qgrav.pipeline._common import (
    RunPaths,
    _compare_allan_backends,
    _jsonable,
    _logspace_taus,
    _stats_cfg,
    _write_run_metadata,
    _write_summary,
)
from qgrav.pipeline._plots import _make_ifo_plots
from qgrav.pipeline._simulation import _add_simulation
from qgrav.reporting import build_html_report
from qgrav.validation import curve_correlation

logger = logging.getLogger(__name__)


def _run_interferometer_pipeline(
    cfg: dict[str, Any],
    cfg_text: str,
    paths: RunPaths,
    config_path: Path,
    *,
    project_root: Path | None = None,
) -> Path:
    bench_cfg = cfg.get("bench", {}) if isinstance(cfg.get("bench", {}), dict) else {}
    bench_type = str(bench_cfg.get("type", "virtual")).lower().strip()
    if bench_type == "real":
        real_cfg = cfg.get("bench_real_ifo")
        if not isinstance(real_cfg, dict):
            raise ValueError("Config missing required section 'bench_real_ifo'")
        data = load_real_ifo_csv(
            csv_path=resolve_project_relative_path(
                config_path, real_cfg["csv_path"], project_root=project_root
            )
            or real_cfg["csv_path"],
            sample_rate_hz=real_cfg.get("sample_rate_hz"),
            delimiter=str(real_cfg.get("delimiter", ",")),
            has_header=bool(real_cfg.get("has_header", True)),
        )
        if real_cfg.get("sample_rate_hz") is not None:
            fs = float(real_cfg.get("sample_rate_hz"))
        elif "sample_rate_hz" in data:
            fs = float(np.asarray(data["sample_rate_hz"], dtype=np.float64).reshape(-1)[0])
        else:
            dt = np.diff(np.asarray(data["t"], dtype=np.float64))
            if len(dt) == 0:
                raise ValueError(
                    "Need at least two samples to infer sample rate for real interferometer data."
                )
            fs = float(1.0 / np.median(dt))
        lam = float(
            real_cfg.get(
                "wavelength_m", cfg.get("bench_virtual_ifo", {}).get("wavelength_m", 1.55e-6)
            )
        )
    else:
        virtual_cfg = cfg.get("bench_virtual_ifo")
        if not isinstance(virtual_cfg, dict):
            raise ValueError("Config missing required section 'bench_virtual_ifo'")
        data = generate_virtual_ifo(
            wavelength_m=float(virtual_cfg["wavelength_m"]),
            sample_rate_hz=float(virtual_cfg["sample_rate_hz"]),
            duration_s=float(virtual_cfg["duration_s"]),
            displacement_sines=list(virtual_cfg["displacement_sines"]),
            measurement_noise_std=float(virtual_cfg["measurement_noise_std"]),
            amplitude=float(virtual_cfg.get("amplitude", 1.0)),
            dc_offset=float(virtual_cfg.get("dc_offset", 0.0)),
            offset_drift_std_per_s=float(virtual_cfg.get("offset_drift_std_per_s", 0.0)),
            amplitude_drift_std_per_s=float(virtual_cfg.get("amplitude_drift_std_per_s", 0.0)),
            seed=int(virtual_cfg.get("seed", 0)),
        )
        fs = float(virtual_cfg["sample_rate_hz"])
        lam = float(virtual_cfg["wavelength_m"])

    t = np.asarray(data["t"], dtype=np.float64)
    I = np.asarray(data["I_meas"], dtype=np.float64)
    Q = np.asarray(data["Q_meas"], dtype=np.float64)
    x_true = np.asarray(data.get("x_true", np.full_like(t, np.nan)), dtype=np.float64)
    if len(t) < 3:
        raise ValueError("Not enough samples for interferometer analysis.")

    alg_cfg = cfg.get("algorithms", {}) if isinstance(cfg.get("algorithms", {}), dict) else {}
    imp_cfg = alg_cfg.get("improved", {}) if isinstance(alg_cfg.get("improved", {}), dict) else {}
    (
        psd_method,
        nperseg,
        noverlap,
        metrics_backend,
        allan_data_type,
        compare_allan_backends,
        comparison_backend,
    ) = _stats_cfg(cfg)
    nperseg = min(max(8, nperseg), len(t))
    noverlap = min(max(1, noverlap), max(1, nperseg - 1))

    est_base = estimate_displacement_baseline(I, Q, wavelength_m=lam)
    est_imp = estimate_displacement_improved(
        I,
        Q,
        wavelength_m=lam,
        offset_tracking_alpha=float(imp_cfg.get("offset_tracking_alpha", 0.01)),
        phase_smooth_window=int(imp_cfg.get("phase_smooth_window", 21)),
    )

    x_b = np.asarray(est_base["x_hat"], dtype=np.float64)
    x_i = np.asarray(est_imp["x_hat"], dtype=np.float64)
    lengths = [len(t), len(I), len(Q), len(x_true), len(x_b), len(x_i)]
    n = min(lengths)
    if len(set(lengths)) > 1:
        logger.warning("Array length mismatch %s; truncating to %d samples", lengths, n)
    t, I, Q, x_true, x_b, x_i = t[:n], I[:n], Q[:n], x_true[:n], x_b[:n], x_i[:n]
    have_truth = bool(np.all(np.isfinite(x_true)))
    taus = _logspace_taus(duration_s=float(t[-1] - t[0]) if len(t) > 1 else 1.0, sample_rate_hz=fs)

    psd_true = (
        compute_psd(x_true, fs, method=psd_method, nperseg=nperseg, noverlap=noverlap)
        if have_truth
        else None
    )
    psd_b = compute_psd(x_b, fs, method=psd_method, nperseg=nperseg, noverlap=noverlap)
    psd_i = compute_psd(x_i, fs, method=psd_method, nperseg=nperseg, noverlap=noverlap)
    adev_b = allan_deviation_overlapping(
        x_b, fs, taus, backend=metrics_backend, data_type=allan_data_type
    )
    adev_i = allan_deviation_overlapping(
        x_i, fs, taus, backend=metrics_backend, data_type=allan_data_type
    )

    from qgrav.metrics.allan import allan_minimum, identify_noise_type

    _ni_b = identify_noise_type(np.asarray(adev_b["taus_s"]), np.asarray(adev_b["adev"]))
    _ni_i = identify_noise_type(np.asarray(adev_i["taus_s"]), np.asarray(adev_i["adev"]))
    _am_b = allan_minimum(np.asarray(adev_b["taus_s"]), np.asarray(adev_b["adev"]))
    _am_i = allan_minimum(np.asarray(adev_i["taus_s"]), np.asarray(adev_i["adev"]))

    metrics: dict[str, Any] = {
        "qgrav_output_format_version": "1.0",
        "qgrav_version": __version__,
        "bench_type": bench_type,
        "have_truth": have_truth,
        "sample_rate_hz": fs,
        "wavelength_m": lam,
        "psd_method": psd_method,
        "welch_nperseg": nperseg,
        "welch_noverlap": noverlap,
        "allan_backend_used": str(adev_i["backend"]),
        "allan_data_type": str(adev_i["data_type"]),
        "noise_identification_baseline": _ni_b,
        "noise_identification_improved": _ni_i,
        "allan_minimum_baseline": _am_b,
        "allan_minimum_improved": _am_i,
        "notes": [
            "Improvement percent > 0 means the improved estimator reduced the chosen error/statistic.",
            "When truth is unavailable, the report focuses on stability/spectral summaries rather than RMSE-based accuracy.",
            "In this project, AllanTools `data_type=freq` means the sampled quantity is the directly measured time series (for example displacement), not literal oscillator frequency.",
            "AISim simulation studies are saved alongside the signal-processing results. The exact interpretation depends on the selected simulation model and is documented in the report.",
        ],
    }

    if have_truth:
        adev_true = allan_deviation_overlapping(
            x_true, fs, taus, backend=metrics_backend, data_type=allan_data_type
        )
        comp_base = curve_correlation(
            psd_b["f_hz"],
            np.log10(psd_b["psd"] + 1e-30),
            psd_true["f_hz"],
            np.log10(psd_true["psd"] + 1e-30),
        )
        comp_imp = curve_correlation(
            psd_i["f_hz"],
            np.log10(psd_i["psd"] + 1e-30),
            psd_true["f_hz"],
            np.log10(psd_true["psd"] + 1e-30),
        )
        base_stats = compute_error_statistics(x_true, x_b)
        imp_stats = compute_error_statistics(x_true, x_i)
        metrics.update(
            {
                "baseline": base_stats,
                "improved": imp_stats,
                "rmse_improvement_percent": improvement_percent(
                    base_stats["rmse"], imp_stats["rmse"]
                ),
                "mae_improvement_percent": improvement_percent(base_stats["mae"], imp_stats["mae"]),
                "psd_vs_truth_baseline": comp_base,
                "psd_vs_truth_improved": comp_imp,
            }
        )
    else:
        adev_true = None
        metrics.update(
            {
                "baseline": {"note": "No truth available: error statistics skipped."},
                "improved": {"note": "No truth available: error statistics skipped."},
            }
        )

    if len(np.asarray(adev_b["adev"])) and len(np.asarray(adev_i["adev"])):
        common_tau = min(len(np.asarray(adev_b["adev"])), len(np.asarray(adev_i["adev"])))
        metrics["allan_improvement_percent_mean"] = improvement_percent(
            float(np.nanmean(np.asarray(adev_b["adev"])[:common_tau])),
            float(np.nanmean(np.asarray(adev_i["adev"])[:common_tau])),
        )

    if compare_allan_backends:
        primary_backend = str(adev_i["backend"])
        if comparison_backend == primary_backend:
            comparison_backend = "custom" if primary_backend != "custom" else "allantools"
        metrics["allan_backend_comparison"] = _compare_allan_backends(
            x_i,
            fs,
            taus,
            primary_backend=primary_backend,
            reference_backend=comparison_backend,
            data_type=allan_data_type,
        )

    save_dict: dict[str, np.ndarray] = {
        "t": t,
        "I_meas": I,
        "Q_meas": Q,
        "x_hat_baseline": x_b,
        "x_hat_improved": x_i,
        "allan_taus": np.asarray(adev_i["taus_s"], dtype=np.float64),
        "allan_baseline": np.asarray(adev_b["adev"], dtype=np.float64),
        "allan_improved": np.asarray(adev_i["adev"], dtype=np.float64),
    }
    if have_truth:
        save_dict["x_true"] = x_true
        save_dict["allan_truth"] = np.asarray(adev_true["adev"], dtype=np.float64)
    sim_cfg = cfg.get("simulation", {}) if isinstance(cfg.get("simulation", {}), dict) else {}
    _add_simulation(metrics, save_dict, sim_cfg)

    try:
        from qgrav.physics.systematics import systematics_summary

        ifo_cfg = (
            cfg.get("interferometer", {}) if isinstance(cfg.get("interferometer", {}), dict) else {}
        )
        metrics["systematics"] = systematics_summary(
            interferometer_time_s=float(ifo_cfg.get("interferometer_time_s", 0.260)),
        )
    except Exception:
        logger.warning("Systematics computation failed", exc_info=True)

    metrics_jsonable = _jsonable(metrics)
    paths.metrics_path.write_text(json.dumps(metrics_jsonable, indent=2), encoding="utf-8")
    np.savez_compressed(paths.data_path, **save_dict)
    plot_paths = _make_ifo_plots(
        paths,
        metrics,
        t,
        I,
        Q,
        x_true if have_truth else None,
        x_b,
        x_i,
        fs,
        psd_method,
        nperseg,
        noverlap,
        adev_true,
        adev_b,
        adev_i,
        "simulation" in metrics,
    )
    _write_summary(paths.summary_path, metrics_jsonable)
    _write_run_metadata(paths.run_metadata_path, cfg, metrics_jsonable)
    return build_html_report(
        run_dir=paths.run_dir, config_text=cfg_text, metrics=metrics_jsonable, plot_paths=plot_paths
    )
