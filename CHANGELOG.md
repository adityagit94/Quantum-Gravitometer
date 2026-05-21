# Changelog

## v0.8.0 (2026-05-17)

Milestone 1 of the Physics PRD: scientific foundations. Adds a physical constants registry, Mach-Zehnder sensitivity function with vibration integrator, solid-earth tide and atmospheric pressure corrections for real gravimetry data, ACF-based noise identification, study-scope labelling on every simulation, and expands the published-reference registry from 4 to 12 entries. **55 new tests** (79 → 134 passing).

---

### Physical Constants Module (W1)

New `src/qgrav/physics/constants.py` — single source of truth for all physical constants used across the codebase.

- Frozen `PhysicalConstant` dataclass with `value`, `unit`, `source`, `uncertainty`, `note` fields
- CODATA fundamentals: speed of light, Planck constant, Boltzmann constant
- Rb-87 / Cs-133 atom data: masses, hyperfine frequencies, D2 wavelengths, recoil velocities/energies
- Effective wavevectors: `K_EFF_RB87_D2 = 1.6105747e7 rad/m` (counter-propagating Raman)
- Geophysical: Earth rotation rate (IERS 2010), free-air gradient, standard/nominal gravity
- All previously hardcoded literals in `systematics.py`, `aisim_adapter.py`, and `gui/app.py` replaced with constants module references
- Regression test (`test_physics_constants.py`) scans source files for stray numerical literals

### Sensitivity Function Module (W2)

New `src/qgrav/physics/sensitivity_function.py` — three-pulse Mach-Zehnder sensitivity function and vibration transfer function (Cheinet 2008).

- `sensitivity_function_time_domain(t, *, interferometer_time_s, pulse_duration_s=0)` — instantaneous and finite-pulse g_s(t)
- `transfer_function_vibration(f_hz, ...)` — laser-phase transfer function |G(2πf)|² = 16 sin⁴(πfT) / (2πf)²
- `acceleration_to_phase_transfer_function_sq(f_hz, *, ..., k_eff_rad_per_m)` — acceleration-to-phase |H_a|² = 16 k_eff² sin⁴(πfT) / (2πf)⁴
- `integrate_vibration_noise(psd_acceleration, f_hz, ...)` → `{sigma_phi_rad, sigma_g_m_s2, sigma_g_ugal}` via trapezoidal integration

New `src/qgrav/physics/_seismic_models.py` — Peterson 1993 NLNM/NHNM seismic noise floor models as (f_hz, psd) pairs with log-log interpolation.

### Corrections Module (W6)

New `src/qgrav/datasets/corrections.py` — tide and atmospheric pressure corrections for IGETS gravimetry data.

- `detect_igets_level(data)` — heuristic from sample rate (1 Hz → L1, 1/60 Hz → L2, 1/3600 Hz → L3)
- `apply_tide_correction(timestamps, values, *, latitude_deg, longitude_deg, backend="auto")` — PyGTide preferred, internal HW95 fallback
- `apply_pressure_correction(timestamps, gravity, pressure, *, admittance_nm_s2_per_hpa=-3.0)` — Crossley 1995 linear admittance
- Returns corrected series plus `{backend_used, rms_subtracted_ugal}` metadata

New `src/qgrav/datasets/_tides_hw95.py` — simplified 20-constituent Wenzel HW95 tidal catalogue.

- Constituents: M2, S2, N2, K2, K1, O1, P1, Q1, Mf, Mm, plus 10 smaller
- Doodson-argument computation from UTC timestamps (GMST, lunar/solar longitudes)
- Body-tide elasticity factor δ = 1.16 (Wahr-Dehant)
- Geographic amplitude factors: cos²(lat) for semi-diurnal, sin(2·lat)/2 for diurnal
- Truncation error ~50 nGal RMS vs full HW95 catalogue

### ACF Noise Identification (W9)

- New `identify_noise_type_acf()` in `metrics/allan.py` wrapping `allantools.ci.autocorr_noise_id`
- Lag-1 autocorrelation method (Riley 2004) — more robust than slope-fitting for mixed noise
- Returns `{method, noise_type, alpha_int, alpha, d, rho, description}`
- ACF is now the primary noise-ID method in the pipeline; legacy slope method preserved under `noise_identification.legacy_slope_method`

### Study Scope Labels (W10)

- Every `run_aisim_*` function now returns `study_scope_category` and `study_scope_description`
- Categories: `FULLY_SIMULATED`, `HYBRID_AISIM_PLUS_ANALYTICAL`, `ANALYTICAL_ONLY`
- HTML report renders a colour-coded study-scope panel (green/amber) above each simulation block
- `_classify_study_scope()` helper in `aisim_adapter.py`

### Published References Expansion (W1)

Registry expanded from 4 to 12 entries in `validation/published_references.py`:

| Key | Value | Unit | Status |
|-----|-------|------|--------|
| `freier_2016_short_term_noise` | 9.6e-8 | m/s²/√Hz | **corrected** (was 5e-8) |
| `freier_2016_accuracy` | 3.9e-8 | m/s² | new |
| `freier_2016_long_term_stability` | 5e-10 | m/s² | new |
| `menoret_2018_short_term_noise` | 5e-7 | m/s²/√Hz | new |
| `menoret_2018_long_term_stability` | 1e-8 | m/s² | **corrected** (was mislabeled 2.5e-8) |
| `hu_2013_short_term_noise` | 4.2e-9 | m/s²/√Hz | new |
| `peters_2001_accuracy` | 3e-8 | m/s² | new |
| `kasevich_chu_1991_first_demo` | 3e-6 | m/s²/√Hz | new |
| `bidel_2018_marine` | 1.7e-6 | m/s²/√Hz | new |
| `nlnm_low_freq` | 7e-10 | m/s²/√Hz | new (Peterson 1993) |
| `sg_noise_floor` | 1e-11 | m/s²/√Hz | retained |
| `mz_visibility` | 0.5 | dimensionless | retained |

- Deprecated keys `freier_2016_sensitivity` and `menoret_2018_accuracy` remain importable via `_LEGACY_KEYS` with `DeprecationWarning`
- New `get_reference(key)` function resolves aliases automatically

### Pipeline Enhancements

- `qgrav_output_format_version: "1.0"` added to every `metrics.json`
- Corrections stage in `_run_real_gravity_pipeline()`: runs between data load and Allan/PSD computation when `apply_corrections: true`
- New metrics keys: `data_product_level_at_analysis`, `corrections_applied`, `correction_metrics`
- `qgrav_version` field in all outputs

### Configuration Additions

New keys under `bench_real_gravity`:

| Key | Type | Default | Description |
|-----|------|---------|-------------|
| `apply_corrections` | bool | `false` | Enable tide + pressure correction stage |
| `igets_level` | string | `"auto"` | Force IGETS level: auto, 1, 2, 3 |
| `tide_backend` | string | `"auto"` | Tide model: auto, pygtide, internal_hw95 |
| `pressure_csv_path` | string | — | Path to pressure CSV |
| `pressure_admittance_nm_s2_per_hpa` | float | `-3.0` | Barometric admittance |

### HTML Report

- Study-scope panel (colour-coded green/amber) above each AISim simulation block
- Corrections section listing what was applied and RMS subtracted
- IGETS level banner (red/orange) when Level < 3 warning about un-removed tides
- Footer showing `qgrav_output_format_version` and `qgrav_version`

### Version Bump

Version `0.7.0` → `0.8.0` in `__init__.py` and `pyproject.toml`.

### Test Summary

| Category | Tests |
|----------|-------|
| **Total** | **134 passing** (was 79) |
| New: `test_physics_constants.py` | 14 tests |
| New: `test_sensitivity_function.py` | 9 tests |
| New: `test_corrections.py` | 12 tests |
| New: `test_noise_id_v2.py` | 5 tests |
| New: `test_unit_conversions.py` | 5 tests |
| New: `test_scope_labels.py` | 7 tests |
| Expanded existing files | +3 tests |

### Files Changed

- **16 source files** modified or created
- **6 new test files** (55 new tests)
- New modules: `physics/constants.py`, `physics/sensitivity_function.py`, `physics/_seismic_models.py`, `datasets/corrections.py`, `datasets/_tides_hw95.py`

---

## v0.7.0 (2026-05-12)

Upgrade from v0.5.0 covering 22 commits across 3 tracks: stabilization, scientific validation, and GUI refactoring. Followed by a comprehensive code audit that identified and fixed 8 bugs and resolved 10 code-quality issues.

---

### Track A: Stabilization

| Task | Commit | Description |
|------|--------|-------------|
| A1 | `fbe3996` | **Fix dashboard rendering bug** — nested `for ax in axes.flat` loop in `visuals.py` shadowed the axis variable and caused premature `return`. Replaced with explicit subplot assignments. |
| A2 | `de40cea` | **Reformat semicolon-joined lines** — split 10+ semicolon-joined matplotlib calls in `pipeline.py` plot functions onto separate lines. |
| A3 | `6ca0cfe` | **Track dropped rows** — `real_ifo.py` CSV loader now counts rows dropped due to NaN/malformed data and stores `dropped_rows` in output dict. |
| A4 | `1eaa825` | **Fix float tau matching** — replaced fragile `np.intersect1d` on float64 arrays with `_match_taus()` using `np.searchsorted` and relative tolerance (`rtol=1e-9`). |
| A5 | `719e55c` | **Clean up temp configs** — GUI now tracks temporary config files in `_temp_config_paths` list and deletes them on window close via `WM_DELETE_WINDOW` protocol. |
| A6 | `8f40a87` | **AISim license placeholder** — added `docs/THIRD_PARTY_LICENSES/AISim-LICENSE.txt` and referenced it in `AISIM_INTEGRATION.md`. |
| A7 | `c5d54b3` | **Document R-squared asymmetry** — expanded `curve_correlation` docstring explaining R-squared is asymmetric, can be negative, and how it differs from Pearson correlation. |
| A8 | `fc0a5e2` | **Clarify scipy dependency** — added comment in `pyproject.toml` noting scipy is only required by vendored allantools and vendor/aisim, not qgrav core. |

### Track B: Scientific Validation

| Task | Commit | Description |
|------|--------|-------------|
| B1 | `8a2296a` | **Shot-noise sensitivity function** — `shot_noise_sensitivity_m_s2_per_sqrt_hz()` implementing `1/(C * k_eff * T^2 * sqrt(N/T_cycle))` with full input validation. Also added `sensitivity_ugal_per_sqrt_hz()` wrapper. |
| B2 | `72fd328` | **Sensitivity in AISim outputs** — all three Mach-Zehnder simulation functions (`phase_scan`, `gravity_sweep`, `vibration_sweep`) now compute and report shot-noise sensitivity using fringe visibility as contrast. |
| B3 | `758b375` | **Noise type identification** — `identify_noise_type()` classifies Allan deviation curves via log-log slope fitting into 5 noise types (white PM, flicker PM, white FM, flicker FM, random walk FM). |
| B4 | `5f66832` | **Noise ID in pipeline** — both pipeline paths (interferometer and real gravity) now compute noise identification and Allan minimum, storing results in `metrics.json` and `SUMMARY.md`. |
| B5 | `758b375` | **Allan minimum finder** — `allan_minimum()` locates the optimal averaging time (tau at minimum ADEV) with index. |
| B6 | `b403aa2` | **Systematic effects module** — new `physics/systematics.py` with `gravity_gradient_shift_m_s2()`, `coriolis_shift_m_s2()`, and `systematics_summary()`. All clearly documented as order-of-magnitude estimates not included in AISim. |
| B7 | `38b1dc8` | **Published references module** — frozen `PublishedReference` dataclass with DOI links, `REFERENCES` registry (Freier 2016, Menoret 2018, SG noise floor, MZ visibility), and `compare_to_reference()` helper. |

### Track C: GUI Refactor & Infrastructure

| Task | Commit | Description |
|------|--------|-------------|
| C1 | `f74455f` | **GUI module split** — moved `gui.py` to `gui/` package. Extracted `MetricCards` to `gui/widgets/metric_cards.py` and `ScrollableFrame` to `gui/widgets/scrollable_frame.py`. `gui/__init__.py` re-exports `QGravApp` and `main`. |
| C2 | `0d70853` | **Allan plot noise annotation** — all 4 Allan deviation plot locations in `visuals.py` now show noise type and slope annotation via `_annotate_noise_type()`, wrapped in try/except to never break plots. |
| C3 | `9633b22` | **Systematics in HTML report** — Jinja2 template gains a systematic effects table showing gravity gradient, Coriolis, and total in both m/s^2 and uGal. Pipeline computes systematics for both bench types. |
| C4 | `60ece53` | **Batch processing scripts** — `scripts/batch_scan_stations.py` scans all stations and writes quality metrics to CSV. `scripts/multi_station_comparison.py` produces overlaid Allan/PSD plots with bar chart. |
| C5 | `330cd18` | **IGETS unit format expansion** — `gravimetry.py` now recognizes `nm/s**2`, `nm s-2`, `nanometers/second**2`, `nm/s2` as valid unit variants. |

### Version Bump

| Commit | Description |
|--------|-------------|
| `c8e694c` | Bumped version `0.5.0` -> `0.7.0` in `__init__.py` and `pyproject.toml`. Updated `README.md` with new features. Updated `SCIENTIFIC_HARDENING.md` with Track B additions. |

---

### Code Audit & Bug Fixes

After implementation, a comprehensive line-by-line audit was performed. Two fix commits addressed all findings:

#### Bugs Fixed (`11542e5`)

| # | Bug | Fix |
|---|-----|-----|
| 1 | `shot_noise_sensitivity` accepted `k_eff <= 0` (returned negative/inf) | Added `ValueError` for non-positive `k_eff_rad_per_m` |
| 2 | `shot_noise_sensitivity` accepted `cycle_time_s <= 0` (NaN/RuntimeWarning) | Added `ValueError` for non-positive `cycle_time_s` |
| 3 | `systematics_summary` had dead `k_eff_rad_per_m` parameter (accepted but unused) | Removed from function signature and all callers |
| 4 | `coriolis_shift_m_s2` returned negative values for latitude > 90 degrees | Clamped latitude to [-90, 90] with `np.clip`, added `abs()` on output |
| 5 | `_match_taus` was O(n^2) — 3.5 seconds for 5000 elements | Rewrote with `np.searchsorted` — 0.015s (230x speedup) |
| 6 | `_match_taus` allowed duplicate target matches (two sources mapping to same target) | Added `used[]` boolean array preventing duplicate assignments |
| 7 | `_write_summary` format string `:.3f` crashed if slope key was missing | Safe float cast: `float(ni.get("slope", float("nan")))` |
| 8 | `_annotate_noise_type` swallowed all exceptions with bare `except: pass` | Changed to `logger.debug("...", exc_info=True)` |

#### Code Quality Fixes (`66da09b`)

| # | Issue | Fix |
|---|-------|-----|
| 1 | `gravity_gradient_shift_m_s2` accepted negative `interferometer_time_s` | Added `ValueError` with test |
| 2 | `PublishedReference.contains()` degenerated when `value=0` (tolerance band collapsed to zero) | Added `abs_tol` fallback parameter (default `1e-15`) |
| 3 | Published references lacked DOI links | Added `doi` field to dataclass, populated all 4 references with real DOIs |
| 4 | `select_autoescape()` didn't activate for `from_string` templates | Changed to `autoescape=True` in report.py |
| 5 | Bare `except Exception: pass` in batch scripts (4 locations) | Replaced with `logger.warning(...)` with `exc_info=True` |
| 6 | No tests for batch processing scripts | Added 6 functional tests using synthetic `.ggp` data |

---

### Test Summary

- **79 tests total** (73 passing, 3 pre-existing failures from missing sample data, 3 skipped)
- **New test files:** `test_batch_scripts.py`, `test_published_references.py`
- **Expanded:** `test_metrics.py` (+7 tests), `test_physics_models.py` (+8 tests), `test_data_edge_cases.py` (+2 tests), `test_aisim_adapter.py` (+3 tests)

### Files Changed

- **33 files** modified or created
- **+1503 lines** added, **-131 lines** removed
- **7 new source files**, **2 new test files**, **2 new scripts**
