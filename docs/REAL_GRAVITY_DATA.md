# Real Gravimetry Data Lane

## Purpose

This module supports **public gravimetry residual time series** as a validation source when lab hardware is unavailable.

## Supported inputs

- `.ggp` files
- `.zip` archives containing `.ggp` files
- directories containing `.ggp` files
- converted CSV files with at least:
  - `timestamp`
  - `gravity_residual`

Optional metadata columns for CSV:
- `station_code`
- `longitude`
- `latitude`

## Parsing assumptions for `.ggp`

The parser looks for rows of the form:

```text
YYYYMMDD HHMMSS VALUE
```

Header rows and malformed rows are skipped.

## Metadata file

If `SG station.txt` is present next to the data or inside the ZIP archive, the loader extracts:
- station code
- longitude
- latitude

## Gap handling

The loader computes:
- median sampling interval
- duplicate count
- reverse-time count
- gap count
- estimated missing samples
- size of the largest contiguous segment

By default, the analysis uses the **longest contiguous segment**.

## Why this matters

Allan deviation and PSD are most meaningful for regularly sampled data. The gap report makes the analysis transparent instead of silently hiding missing data.

## Typical outputs

- full-series trend plot
- histogram
- PSD
- Allan deviation
- metadata + gap summary

## IGETS data product levels (v0.8)

IGETS (International Geodynamics and Earth Tide Service) distributes superconducting gravimeter data at three processing levels:

| Level | Sample rate | Processing |
|-------|-------------|------------|
| **Level 1** | ~1 Hz | Raw gravimeter output. Tides and atmospheric pressure are still in the signal. |
| **Level 2** | ~1 minute | Decimated averages. Partially corrected at some stations. |
| **Level 3** | ~1 hour | Fully corrected for solid-earth tides and atmospheric pressure. |

The pipeline auto-detects the level from the sample rate via `detect_igets_level()`. You can also force it with `igets_level: "1"` (or `"2"`, `"3"`) in the config.

**Why this matters:** Allan deviation computed on Level 1 data is dominated by the ~100 uGal body-tide signal, not instrument noise. Comparing such results to published SG noise floors (which assume Level 3 processing) is misleading. Enable corrections to remove this effect.

## Tide and pressure corrections (v0.8)

Enable with `apply_corrections: true` in the `bench_real_gravity` section of your config.

### Tide correction

Subtracts the predicted solid-earth body tide from the gravity residual series.

- **PyGTide backend** (preferred): Full Wenzel HW95 catalogue with ~12,000 constituents. Sub-microGal accuracy. Requires `pip install pygtide` (Fortran extension; may need a compiler on Windows).
- **Internal HW95 backend** (fallback): Simplified 20-constituent model (M2, S2, N2, K2, K1, O1, P1, Q1, Mf, Mm, plus 10 smaller). Pure Python, no extra dependencies. Truncation error ~50 nGal RMS vs full catalogue.
- **Auto backend** (default): Tries PyGTide first; if not installed, falls back to internal HW95 with a logged warning.

Set the backend with `tide_backend: auto` | `pygtide` | `internal_hw95`.

### Pressure correction

Subtracts the atmospheric pressure loading effect using a linear admittance model (Crossley 1995):

```
corrected = gravity - admittance * (pressure - reference_pressure)
```

Requires a co-located pressure CSV file with `unix_seconds` and `pressure_hpa` columns. Reference pressure defaults to the mean of the series.

Set the path with `pressure_csv_path` and the admittance with `pressure_admittance_nm_s2_per_hpa` (default: -3.0 nm/s^2/hPa).

### Configuration keys for corrections

| Key | Type | Default | Description |
|-----|------|---------|-------------|
| `apply_corrections` | bool | `false` | Master switch for corrections stage |
| `igets_level` | string | `"auto"` | Force IGETS product level: auto, 1, 2, 3 |
| `tide_backend` | string | `"auto"` | Tide model: auto, pygtide, internal_hw95 |
| `pressure_csv_path` | string | - | Path to pressure CSV |
| `pressure_admittance_nm_s2_per_hpa` | float | `-3.0` | Barometric admittance |

### What gets recorded

When corrections are applied, `metrics.json` includes:

- `data_product_level_at_analysis` - the detected or forced IGETS level (1, 2, or 3)
- `corrections_applied` - list of correction names (e.g., `["tide"]`)
- `correction_metrics.tide_rms_subtracted_ugal` - RMS of the subtracted tide signal
- `correction_metrics.tide_backend_used` - which backend was actually used
