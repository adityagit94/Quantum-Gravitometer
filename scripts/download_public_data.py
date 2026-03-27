"""Download a public dataset for validation.

This script is intentionally generic because dataset URLs and filenames change.
It accepts a direct URL and saves it into data/raw/.

Usage:
  python scripts/download_public_data.py --url <DIRECT_URL> --out data/raw/file.ext
"""

from __future__ import annotations

import argparse
from pathlib import Path
from urllib.request import urlretrieve

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--url", required=True, help="Direct download URL")
    ap.add_argument("--out", required=True, help="Output path (e.g., data/raw/dataset.csv)")
    args = ap.parse_args()

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    print(f"Downloading to: {out}")
    urlretrieve(args.url, out)
    print("Done.")

if __name__ == "__main__":
    main()
