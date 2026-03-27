from __future__ import annotations

import argparse
import logging
from pathlib import Path

def main() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s"
    )
    parser = argparse.ArgumentParser(prog="qgrav", description="Quantum gravimeter R&D platform")
    sub = parser.add_subparsers(dest="cmd", required=True)

    run_p = sub.add_parser("run", help="Run pipeline from YAML config")
    run_p.add_argument("--config", required=True, help="Path to YAML configuration file")

    gui_p = sub.add_parser("gui", help="Launch the desktop GUI")
    gui_p.add_argument("--config", required=False, help="Optional config to pre-load in the GUI")

    conv_p = sub.add_parser("convert-ggp", help="Convert .ggp gravimetry data to CSV")
    conv_p.add_argument("--source", required=True, help="Path to .ggp file, directory, or .zip archive")
    conv_p.add_argument("--out", required=True, help="Output CSV path")
    conv_p.add_argument("--station", required=False, help="Station code when source is a directory or zip")
    conv_p.add_argument("--metadata", required=False, help="Optional SG station metadata path")

    args = parser.parse_args()

    if args.cmd == "run":
        import matplotlib
        matplotlib.use("Agg")
        from qgrav.pipeline import run_pipeline

        report = run_pipeline(Path(args.config))
        print(f"Report written: {report}")
        print(f"Open in browser: {report.resolve()}")
        return

    if args.cmd == "gui":
        from qgrav.gui import main as gui_main

        gui_main(default_config=Path(args.config).resolve() if args.config else None)
        return

    if args.cmd == "convert-ggp":
        from qgrav.datasets import convert_ggp_to_csv

        out = convert_ggp_to_csv(
            source_path=args.source,
            output_path=args.out,
            station_code=args.station,
            metadata_path=args.metadata,
        )
        print(f"CSV written: {out}")
        return

    raise SystemExit(2)


if __name__ == "__main__":
    main()
