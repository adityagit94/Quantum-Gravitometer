from __future__ import annotations

import argparse
from pathlib import Path

from qgrav.datasets import convert_ggp_to_csv


def main() -> None:
    ap = argparse.ArgumentParser(description='Convert a .ggp station file or archive entry to CSV.')
    ap.add_argument('--source', required=True, help='Path to .ggp file, directory, or .zip archive')
    ap.add_argument('--out', required=True, help='Output CSV path')
    ap.add_argument('--station', help='Station code when source is a directory or zip')
    ap.add_argument('--metadata', help='Optional SG station.txt path')
    args = ap.parse_args()

    out = convert_ggp_to_csv(
        source_path=args.source,
        output_path=args.out,
        station_code=args.station,
        metadata_path=args.metadata,
    )
    print(f'Wrote CSV: {out}')


if __name__ == '__main__':
    main()
