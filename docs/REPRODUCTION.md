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
# Expected: 134 tests passing (v0.8.0)
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

## Reproduce a corrections-enabled run (v0.8)

Add `apply_corrections: true` to the `bench_real_gravity` section of your config:

```yaml
bench_real_gravity:
  source_path: data/raw/sg_sample
  station_code: ap046
  apply_corrections: true
  tide_backend: auto
```

Then run:
```bash
qgrav run --config your_config_with_corrections.yaml
```

Check `metrics.json` for `data_product_level_at_analysis`, `corrections_applied`, and `correction_metrics` keys.

## Sensitivity function smoke test (v0.8)
```bash
python -c "
from qgrav.physics.sensitivity_function import integrate_vibration_noise, interpolate_psd
import numpy as np
f = np.logspace(-3, 2, 500)
psd = interpolate_psd(f, model='nlnm')
result = integrate_vibration_noise(psd, f, interferometer_time_s=0.26, k_eff_rad_per_m=1.61e7)
print(f'NLNM-limited gravity noise: {result[\"sigma_g_ugal\"]:.4f} uGal')
print(f'Phase noise: {result[\"sigma_phi_rad\"]:.4f} rad')
"
```

## What to archive with a result
For every final run, archive:
- the YAML config
- `metrics.json` (now includes `qgrav_output_format_version: "1.0"`)
- `SUMMARY.md`
- `report.html`
- plots
- the exact source path and station code
