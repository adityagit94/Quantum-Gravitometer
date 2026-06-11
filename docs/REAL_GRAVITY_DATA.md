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

## Reducing real data (v1.5): the full correction chain

A standard superconducting-gravimeter residual reduction applies, in order:
**solid-earth tide → atmospheric pressure → polar motion → ocean loading.**
The first two are described above; the last two are new in v1.5 and are
**off by default** — each needs its own `enabled: true` under a
`corrections:` block (and the master `apply_corrections: true`). All inputs
are user-supplied; qgrav never fetches anything from the network.

### Polar motion (pole tide)

The wobble of the rotation axis (Chandler + annual) modulates the
centrifugal contribution to local gravity by up to ~±10 µGal
(IERS Conventions 2010, ch. 7; IAGBN standard):

```
delta_g = -delta * omega^2 * R * sin(2*phi) * (x_p*cos(lambda) - y_p*sin(lambda))
```

with gravimetric factor delta = 1.164. You supply the pole coordinates
`x_p`/`y_p` in arcseconds for your epoch from the **IERS EOP 14 C04**
series (https://hpiers.obspm.fr/iers/eop/eopc04/ or the `finals.all`
file at datacenter.iers.org — columns `x_pole` and `y_pole`). Scalars are
fine for records much shorter than the ~433-day Chandler period.

### Ocean loading

The elastic deformation under ocean tides adds a station-specific signal
of a few µGal. Full Green's-function convolution (HARDISP) is out of
scope; instead you supply per-constituent **amplitude + local phase** and
qgrav synthesizes the series with the same astronomical-argument machinery
as the internal tide model:

```
delta_g(t) = sum_i A_i * cos(chi_i(t) - phi_i)
```

Get the values from the **Onsala free-ocean-loading provider**
(http://holt.oso.chalmers.se/loading/): select the *gravity* observable
and a tide model (e.g. FES2014), submit your station coordinates, and copy
from the returned BLQ block the amplitude row and the phase row
(one column per constituent; gravity amplitudes are positive-down,
commonly quoted in nm/s² — check the header). Supported constituents:
M2, S2, N2, K2, K1, O1, P1, Q1, Mf, Mm, Ssa.

Both corrections follow the same sign convention as the tide/pressure
stages: `corrected = observed - effect`.

```yaml
bench_real_gravity:
  apply_corrections: true
  corrections:
    polar_motion:
      enabled: true
      latitude_deg: 49.144      # defaults to station metadata if omitted
      longitude_deg: 12.878
      xp_arcsec: 0.12           # IERS EOP C04 for the record's epoch
      yp_arcsec: 0.33
    ocean_loading:
      enabled: true
      constituents:             # from an Onsala BLQ gravity block
        - {name: M2, amplitude_nm_s2: 12.3, phase_deg: -47.0}
        - {name: O1, amplitude_nm_s2: 3.1, phase_deg: 12.0}
```

Applied corrections are recorded in `metrics.json` (`corrections_applied`,
`correction_metrics.polar_motion_delta_g_ugal`,
`correction_metrics.ocean_loading_rms_subtracted_ugal`) and surface in the
HTML report like the tide stage.

### Configuration keys for corrections

| Key | Type | Default | Description |
|-----|------|---------|-------------|
| `apply_corrections` | bool | `false` | Master switch for corrections stage |
| `igets_level` | string | `"auto"` | Force IGETS product level: auto, 1, 2, 3 |
| `tide_backend` | string | `"auto"` | Tide model: auto, pygtide, internal_hw95 |
| `pressure_csv_path` | string | - | Path to pressure CSV |
| `pressure_admittance_nm_s2_per_hpa` | float | `-3.0` | Barometric admittance |
| `corrections.polar_motion.enabled` | bool | `false` | Pole-tide correction |
| `corrections.polar_motion.xp_arcsec` / `yp_arcsec` | float/array | `0.0` | IERS pole coordinates |
| `corrections.polar_motion.gravimetric_factor` | float | `1.164` | IERS delta factor |
| `corrections.ocean_loading.enabled` | bool | `false` | Ocean tidal loading |
| `corrections.ocean_loading.constituents` | list | `[]` | `{name, amplitude_nm_s2, phase_deg}` per constituent |

### What gets recorded

When corrections are applied, `metrics.json` includes:

- `data_product_level_at_analysis` - the detected or forced IGETS level (1, 2, or 3)
- `corrections_applied` - list of correction names (e.g., `["tide"]`)
- `correction_metrics.tide_rms_subtracted_ugal` - RMS of the subtracted tide signal
- `correction_metrics.tide_backend_used` - which backend was actually used
