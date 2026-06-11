from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

logger = logging.getLogger(__name__)


def _cmd_run(args: argparse.Namespace) -> None:
    import matplotlib

    matplotlib.use("Agg")
    from qgrav.config import load_config, validate_config
    from qgrav.pipeline import run_pipeline

    config_path = Path(args.config)
    if args.dry_run:
        cfg, _ = load_config(config_path)
        validate_config(cfg)
        bench_type = str(cfg.get("bench", {}).get("type", "virtual")).lower()
        print("--- dry-run ---")
        print(f"  Config:     {config_path.resolve()}")
        print(f"  Bench type: {bench_type}")
        print(f"  Output dir: {cfg.get('output', {}).get('runs_dir', 'runs/')}")
        if bench_type == "real_gravity":
            grav_cfg = cfg.get("bench_real_gravity", {})
            print(f"  Source:     {grav_cfg.get('source_path', '(not set)')}")
            print(f"  Station:    {grav_cfg.get('station_code', '(auto)')}")
            print(f"  Corrections: {grav_cfg.get('apply_corrections', False)}")
        stats = cfg.get("stats", {})
        print(f"  PSD method: {stats.get('psd_method', 'welch')}")
        print(f"  Allan back: {stats.get('metrics_backend', 'auto')}")
        print("Config validated OK. Ready to run.")
        return

    report = run_pipeline(config_path)
    print(f"Report written: {report}")
    print(f"Open in browser: {report.resolve()}")


def _cmd_gui(args: argparse.Namespace) -> None:
    from qgrav.gui import main as gui_main

    gui_main(default_config=Path(args.config).resolve() if args.config else None)


def _cmd_convert_ggp(args: argparse.Namespace) -> None:
    from qgrav.datasets import convert_ggp_to_csv

    out = convert_ggp_to_csv(
        source_path=args.source,
        output_path=args.out,
        station_code=args.station,
        metadata_path=args.metadata,
    )
    print(f"CSV written: {out}")


def _safe_dispatch(handler, args: argparse.Namespace) -> None:
    """Run a CLI handler with proper error reporting."""
    try:
        handler(args)
    except SystemExit:
        raise
    except KeyboardInterrupt:
        raise SystemExit(130) from None
    except Exception as exc:
        exc_name = type(exc).__name__
        print(f"Error ({exc_name}): {exc}", file=sys.stderr)
        if getattr(args, "verbose", False):
            import traceback

            traceback.print_exc(file=sys.stderr)
        raise SystemExit(1) from None


def _cmd_validate_data(args: argparse.Namespace) -> None:
    """Validate a gravimetry dataset and print a human-readable summary."""
    source = Path(args.source)
    if not source.exists():
        print(f"Error: source path does not exist: {source}", file=sys.stderr)
        raise SystemExit(1)

    from qgrav.datasets.gravimetry import load_real_gravity_dataset

    try:
        data = load_real_gravity_dataset(
            source_path=source,
            station_code=args.station,
            metadata_path=Path(args.metadata) if args.metadata else None,
        )
    except Exception as exc:
        print(f"Error loading dataset: {exc}", file=sys.stderr)
        raise SystemExit(1) from None

    # Try IGETS level detection
    from qgrav.datasets.corrections import detect_igets_level

    level = detect_igets_level(data)

    print("=== qgrav validate-data ===")
    print(f"  Source:        {source.resolve()}")
    print(f"  Station code:  {data.get('station_code', '(unknown)')}")
    print(f"  Sample rate:   {data.get('sample_rate_hz', '?')} Hz")
    print(f"  IGETS level:   {level}")
    print(f"  Dropped rows:  {data.get('dropped_rows', 0)}")

    gap = data.get("gap_report", {})
    if gap:
        print(f"  Total samples: {gap.get('n_samples_total', '?')}")
        print(f"  Gap count:     {gap.get('gap_count', '?')}")
        print(f"  Missing est.:  {gap.get('missing_samples_estimate', '?')}")
        seg = gap.get("largest_contiguous_segment_samples", "?")
        print(f"  Longest seg.:  {seg} samples")

    seg_info = data.get("analysis_segment", {})
    if seg_info:
        print(f"  Segment start: {seg_info.get('segment_start', '?')}")
        print(f"  Segment end:   {seg_info.get('segment_end', '?')}")
        print(f"  Segment pts:   {seg_info.get('segment_samples', '?')}")

    x = data.get("gravity_residual")
    if x is not None and len(x) > 0:
        import numpy as np

        x = np.asarray(x)
        print(f"  Mean:          {float(np.mean(x)):.6e}")
        print(f"  Std:           {float(np.std(x)):.6e}")
        print(f"  Min:           {float(np.min(x)):.6e}")
        print(f"  Max:           {float(np.max(x)):.6e}")

    units = data.get("series_units", "unknown")
    print(f"  Units:         {units}")
    for w in data.get("unit_warnings", []):
        print(f"  WARNING:       {w}")

    lat = data.get("latitude_deg")
    lon = data.get("longitude_deg")
    if lat is not None:
        print(f"  Latitude:      {lat}")
    if lon is not None:
        print(f"  Longitude:     {lon}")

    print("Validation complete.")


def _cmd_info(_args: argparse.Namespace) -> None:
    """Print version and environment information."""
    import platform

    from qgrav import __version__

    print("=== qgrav info ===")
    print(f"  qgrav version: {__version__}")
    print(f"  Python:        {platform.python_version()} ({sys.executable})")
    print(f"  Platform:      {platform.platform()}")

    # Core dependencies
    deps = ["numpy", "scipy", "matplotlib", "yaml", "jinja2"]
    for name in deps:
        try:
            mod = __import__(name)
            ver = getattr(mod, "__version__", getattr(mod, "version", "?"))
            print(f"  {name:14s}: {ver}")
        except ImportError:
            print(f"  {name:14s}: NOT INSTALLED")

    # Optional dependencies
    optionals = {
        "hypothesis": "hypothesis",
        "pygtide": "pygtide",
        "allantools (ext)": "allantools",
    }
    print()
    print("  Optional packages:")
    for label, modname in optionals.items():
        try:
            mod = __import__(modname)
            ver = getattr(mod, "__version__", getattr(mod, "version", "?"))
            print(f"    {label:18s}: {ver}")
        except ImportError:
            print(f"    {label:18s}: not installed")

    # Vendored packages
    print()
    print("  Vendored packages:")
    try:
        from qgrav.vendor.allantools import allantools as at

        print(f"    allantools:        {getattr(at, '__version__', '?')}")
    except Exception:
        print("    allantools:        unavailable")
    try:
        import qgrav.vendor.aisim  # noqa: F401 - availability probe

        print("    aisim:             available")
    except Exception:
        print("    aisim:             unavailable")


def main() -> None:
    logging.basicConfig(
        level=logging.INFO, format="%(asctime)s | %(levelname)s | %(name)s | %(message)s"
    )
    parser = argparse.ArgumentParser(prog="qgrav", description="Quantum gravimeter R&D platform")
    parser.add_argument(
        "--verbose", "-v", action="store_true", help="Show full tracebacks on error"
    )
    sub = parser.add_subparsers(dest="cmd", required=True)

    # --- run ---
    run_p = sub.add_parser("run", help="Run pipeline from YAML config")
    run_p.add_argument("--config", required=True, help="Path to YAML configuration file")
    run_p.add_argument(
        "--dry-run", action="store_true", help="Validate config and print summary without running"
    )

    # --- gui ---
    gui_p = sub.add_parser("gui", help="Launch the desktop GUI")
    gui_p.add_argument("--config", required=False, help="Optional config to pre-load in the GUI")

    # --- convert-ggp ---
    conv_p = sub.add_parser("convert-ggp", help="Convert .ggp gravimetry data to CSV")
    conv_p.add_argument(
        "--source", required=True, help="Path to .ggp file, directory, or .zip archive"
    )
    conv_p.add_argument("--out", required=True, help="Output CSV path")
    conv_p.add_argument(
        "--station", required=False, help="Station code when source is a directory or zip"
    )
    conv_p.add_argument("--metadata", required=False, help="Optional SG station metadata path")

    # --- validate-data ---
    val_p = sub.add_parser("validate-data", help="Validate a gravimetry dataset and print summary")
    val_p.add_argument("--source", required=True, help="Path to .ggp, .csv, or directory")
    val_p.add_argument(
        "--station", required=False, help="Station code (when source is a directory/zip)"
    )
    val_p.add_argument("--metadata", required=False, help="Optional SG station metadata path")

    # --- info ---
    sub.add_parser("info", help="Print version and environment information")

    args = parser.parse_args()
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    handlers = {
        "run": _cmd_run,
        "gui": _cmd_gui,
        "convert-ggp": _cmd_convert_ggp,
        "validate-data": _cmd_validate_data,
        "info": _cmd_info,
    }
    handler = handlers.get(args.cmd)
    if handler:
        _safe_dispatch(handler, args)
    else:
        parser.print_help()
        raise SystemExit(2)


if __name__ == "__main__":
    main()
