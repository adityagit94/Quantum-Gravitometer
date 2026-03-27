# Reproduction Guide

## Environment
```bash
python -m venv .venv
# Windows:
.venv\Scripts\activate
# Linux/macOS:
source .venv/bin/activate
pip install -U pip
pip install -e .
```

## Sanity checks
```bash
pytest -q
```

## Reproduce the bundled examples
```bash
qgrav run --config configs/example.yaml
qgrav run --config configs/example_aisim.yaml
qgrav run --config configs/example_real_gravity.yaml
```

## Reproduce a station CSV conversion
```bash
qgrav convert-ggp --source data/raw/sg_sample --station ap046 --out /tmp/ap046.csv
```

## Reproduce the GUI workflow
```bash
qgrav gui --config configs/example_real_gravity.yaml
```

## What to archive with a result
For every final run, archive:
- the YAML config
- `metrics.json`
- `SUMMARY.md`
- `report.html`
- plots
- the exact source path and station code
