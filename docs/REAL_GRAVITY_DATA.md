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
