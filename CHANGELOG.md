# Changelog

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
