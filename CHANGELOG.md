# Changelog

## Unreleased

### Real-data corrections
- **Polar-motion (pole tide) and ocean-loading reductions** complete the
  standard SG residual chain (tide → pressure → polar motion → ocean
  loading). Both are off by default, config-driven, and fully offline:
  the user supplies IERS C04 pole coordinates / Onsala-BLQ constituent
  amplitudes+phases. Ocean loading reuses the regression-locked HW95
  astronomical-argument machinery; both follow the existing
  `corrected = observed − effect` convention and are recorded in
  `metrics.json` like the tide stage. New `tests/test_corrections_pm_ol.py`
  (16 tests incl. an end-to-end pipeline wiring check).

### GUI
- **Multi-run Allan-curve comparison** in the Results tab: a
  `Compare runs…` dialog overlays σ(τ) from any number of run folders on
  one log-log figure (newest-first listing, optional normalization to
  each curve's σ(τ=1 s), PNG export). Runs without Allan data are
  skipped with a status-bar note. +3 GUI tests.

### Internal
- `sim_ai/aisim_adapter.py` (~2,000 lines) split into private modules
  (`_adapter_core`, `_scans`, `_sweeps`, `_multi_drop`, `_config_run`);
  `aisim_adapter` is now a 77-line facade re-exporting every historical
  name (public and private), so all import paths keep working. Move-only:
  identical test results (419 tests incl. slow).
- `gui/app.py` (~2,650 lines) split into per-tab mixin modules
  (`_tab_setup_run`, `_tab_data_browser`, `_tab_editor`, `_tab_results`,
  `_tab_validation`, `_tab_guides`); `QGravApp` keeps `__init__`, shared
  widget helpers, and the queue/worker-thread machinery (459 lines).
  Move-only: all 15 GUI tests pass, `python -m qgrav.gui` launches.

## v1.4.0 (2026-06-11) - GUI integration

Brings the full v1.0-v1.3 simulation/validation engine into the desktop
workbench (`qgrav-gui`) and hardens CI: enforced lint/format/type gates,
coverage measurement, and Python 3.13 in the matrix.
**419 tests (full suite incl. slow + QuTiP), 0 regressions.**

### CI
- The test matrix now includes Python 3.13 on both ubuntu and windows,
  backing the `Programming Language :: Python :: 3.13` classifier.
- New `lint` job enforces ruff, black, and mypy on every push/PR (ruff/black
  pinned to the pre-commit versions; vendored code excluded from all three).
  The whole non-vendor tree was reformatted once with black 24.10 and the
  ruff findings fixed (dead locals, `raise ... from`, isinstance unions,
  import sorting); `[tool.mypy]` config added and the source tree is
  mypy-clean (62 files), with scoped TODO(typing) overrides for the
  config-dispatcher and pipeline modules. Scripts and notebooks are linted
  by the same rules (pre-commit passes on all files).
- Coverage is now measured in CI (`pytest --cov`, vendored code omitted) with
  targeted new tests for the weakest modules: `sim_ai/simple_ai.py`
  38% → 100%, `bench_ifo/real_ifo.py` 59% → 98%, `datasets/corrections.py`
  62% → 100% (the PyGTide code path is now exercised via a fake module).
  Also modernised the deprecated `utcfromtimestamp` call that path used.
  Non-vendor total: 78.5%.

### Setup & Run tab
- Added the flagship **`multi_drop_cycle`** model to the study-model dropdown (it
  was implemented in the engine since v1.0 but unreachable from the GUI).
- Two new collapsible sections expose the previously YAML-only physics surface,
  each control carrying a hover **tooltip**:
  - *Advanced physics* - seed, single-photon detuning, gravity propagation,
    lock-to-mid-fringe, gravity gradient, Zernike wavefront (coeffs + radius).
  - *Multi-drop noise budget & servo* - drops/cycle, cycle time, true *g*,
    detection σ_p, Raman phase noise, correlated seismic vibration (NLNM/NHNM) +
    isolation cut-off, visibility fitting, and a fringe-lock servo (`integrator`
    or full `pid`).
- Both new sections round-trip through `sync_controls_from_dict` /
  `apply_quick_controls_to_editor`, and the emitted YAML runs unchanged through
  `run_simulation_from_config`.

### New "Validation" tab
- **Published reference library** - browses the 14-entry `REFERENCES` registry
  (value, unit, year, source, DOI, tolerance).
- **One-click reproductions** for Freier 2016, Hu 2013, Ménoret 2018, Xu 2022,
  Wu 2019 - each builds a runnable `multi_drop_cycle` config from that paper's
  `multi_drop_kwargs()` and shows published vs predicted ASD + within-band status.
- **Independent cross-check** panel - runs the AISim-vs-analytic Rabi check (no
  deps) and the full QuTiP Schrödinger cross-check, in a worker thread, degrading
  gracefully when QuTiP is absent.

### Rewritten "Guides" tab
- Replaced the single static text dump with a navigable guide: 10 authored topics
  (Quick start, Workflows, Study models, Noise & realism, Validation, Interpreting
  results, Cross-checks, **How to move ahead**, Glossary, Common mistakes) plus a
  Project-documents section that opens the on-disk docs.

### Bug fix
- **Bundled assets never loaded in a source checkout.** The GUI resolved
  `configs/`, `data/`, and the guide docs via `Path(__file__).parents[2]`, which
  points at `src/`, not the repo root - so the Examples menu, sample dataset, and
  Guides doc links silently did nothing. Now resolved via `find_project_root`
  (9 call sites). New widgets: `Tooltip`, `CollapsibleSection`. New bundled
  config: `configs/example_aisim_multi_drop.yaml`.
- **Added `src/qgrav/gui/__main__.py`** so `python -m qgrav.gui` works as a third
  launch form alongside `qgrav gui` and `qgrav-gui` (it previously failed with
  "No module named qgrav.gui.__main__").

### Tests
- `tests/test_gui_integration.py` (12 tests) builds the entire app on a real
  (withdrawn) Tk root and exercises every new path; skips cleanly when Tk has no
  display so headless CI is unaffected.
- GUI test modules now also skip cleanly on a Python built *without* Tk
  (`import tkinter` raising `ImportError` previously crashed test collection
  with 2 errors instead of skipping).
- `tests/test_gui_import.py` adds a guard that `qgrav.gui.__main__` exposes `main`.

### Repo hygiene & packaging
- **`.gitignore`:** the bundled test fixtures (`data/raw/sg_sample/`,
  `data/raw/real_ifo_template.csv`) are now tracked while user datasets stay
  ignored - previously `data/raw/` was fully ignored, so the IGETS real-data
  tests would have failed on a fresh clone / in CI. Also ignore `site/`,
  `.pytest_cache/`, `.ruff_cache/`, `.qgrav_mpl/`, and coverage output.
- **`pyproject.toml`:** added `[project.urls]`, `keywords`, trove `classifiers`,
  and a maintainer/author email.
- **Community health files:** `CITATION.cff`, `CONTRIBUTING.md`, `SECURITY.md`,
  `CODE_OF_CONDUCT.md`, `.editorconfig`, GitHub issue/PR templates, and
  `src/qgrav/vendor/ATTRIBUTION.md` (AISim GPL-3.0, allantools LGPL-3.0).
- **README:** status/license/python/CI badges, a Contributing & citing section,
  and the test-count corrected (371 → 378).
- **Python floor raised to 3.11.** CI revealed the vendored AISim
  (`vendor/aisim/zern.py`) uses `match`/`case` (3.10+) *and* `enum.StrEnum`
  (3.11+), so Python 3.9 and 3.10 were never actually supported.
  `requires-python`, classifiers, the CI matrix, README badge, and docs now
  state `>=3.11` (CI tests 3.11/3.12; verified locally through 3.14).
- **Docs deploy is manual-only.** The `deploy` job in `docs.yml` now runs only on
  `workflow_dispatch`, so a push no longer shows a red "Docs / deploy" check when
  GitHub Pages is disabled. `docs/build` still validates the site on every push.

---

## v1.3.0 (2026-05-30)

Documentation, real-data validation, and JOSS-readiness release. **362 → 371 tests.**

### Real-data validation of the analysis chain (resolves C8, scoped)

- **`tests/test_real_data_igets_validation.py`** (3 tests): ingests the bundled real IGETS superconducting-gravimeter station (`ap046`) through the existing `bench_ifo/real_gravity` pipeline, computes the overlapping Allan deviation, and asserts it is finite, positive, structurally bounded by the sample std, and physically plausible - cross-referenced to the `sg_noise_floor` instrument-floor reference. Hermetic (uses bundled data, no network).
- **Honest scope:** this validates the *analysis chain* on real precision-gravity data; it does **not** validate the atom-interferometer *simulation* against hardware, because essentially no public atom-gravimeter raw data exists. An outreach ask for real atom-gravimeter data was added to `docs/REVIEW_REQUEST_TEMPLATE.md` as a future collaboration track.

### JOSS paper + MkDocs site

- **`paper/paper.md` + `paper/paper.bib`** - JOSS submission draft (~600 words; Summary, Statement of need, Functionality, AI-assistance disclosure) citing AISim, QuTiP, Freier/Hu/Ménoret, Bertoldi, Cheinet, Peterson.
- **`mkdocs.yml` + `docs/index.md` + `.github/workflows/docs.yml`** - MkDocs site (readthedocs theme, builds with bare `mkdocs`) deployed to GitHub Pages on push. Verified `mkdocs build` succeeds.
- **`tests/test_docs_build.py`** (6 tests): mkdocs nav targets all exist, JOSS paper has the required sections + word count in the JOSS 250-1750 range + an AI-usage disclosure.

### Documentation refresh

- `docs/COMPLETE_GUIDE.md` header bumped to v1.2.3 and a new **§16 "What's new since v1.0 (capabilities map)"** added - a single index into the emergent-gravity, multi-drop, AC-Stark/wavefront, published-reference, QuTiP, real-data, performance, and CI capabilities, each linking to its detailed doc. (A full line-by-line rewrite of the 1186-line v0.8 body is deferred; the §16 map + the dedicated v1.x docs cover the new material.)

### Version

`1.2.3` → `1.3.0`.

---

## v1.2.3 (2026-05-30)

Performance benchmarking (resolves C15). **361 → 362 tests** (+1 guard; the 4 benchmarks are collected separately).

- **`tests/benchmark_aisim.py`** (pytest-benchmark, `-m benchmark`): single MZ sequence, 60-point gravity sweep (hybrid + emergent), 100-drop multi-drop cycle. Excluded from the default suite by filename (not `test_*.py`); run via `pip install .[benchmark] && pytest tests/benchmark_aisim.py -m benchmark`.
- **Representative timings** (Win11 / Py3.14 / NumPy 2.4): single MZ **~1.3 ms** (1000 atoms), 60-pt hybrid sweep **~0.09 s**, 60-pt emergent sweep **~0.20 s**, 100-drop emergent cycle **~0.30 s**. Documented in **`docs/PERFORMANCE.md`** with scaling notes.
- **Profiling found no bottleneck worth optimising** - the MZ matrix ops are already vectorised over atoms (NumPy einsum on the block-diagonal propagator); the per-drop ensemble creation is a small fraction of the per-drop MZ cost. No O(n²) hot paths.
- **`tests/test_performance_guard.py`** (runs in the normal suite, no plugin): a single MZ sequence must complete under a 200 ms ceiling (~150× the ~1.3 ms representative time), catching an accidental algorithmic regression without flakiness.
- Nightly CI installs `[test,qutip,benchmark]` and runs the slow regressions, QuTiP cross-check, and benchmarks.

### Version

`1.2.2` → `1.2.3`.

---

## v1.2.2 (2026-05-30)

Full gravity-sweep YAML exposure + quantitative wavefront-curvature validation. **353 → 361 tests.**

### Full gravity-sweep / MZ-phase-scan YAML exposure (resolves rest of C7)

- Threaded `wavefront` + `single_photon_detuning_hz` through `_run_mach_zehnder_sequence_with_gravity` (and its `IntegratedPhaseSpatialSuperposition` propagators), and added `single_photon_detuning_hz`, `wavefront_zernike_coeffs`, `wavefront_radius_m` to `run_aisim_gravity_sweep`, `run_aisim_mach_zehnder_phase_scan`, and `run_simulation_from_config`. AC-Stark and wavefront aberrations are now configurable from YAML for the gravity-sweep and phase-scan models, not just programmatically.
- New `_coerce_zernike_coeffs` helper (YAML may give string Zernike-index keys → coerced to int).
- New `tests/test_yaml_gravity_sweep_config.py` (6 tests): key coercion + round-trip + each key demonstrably changes the simulated output.

### Quantitative wavefront-curvature validation (resolves C3)

- Replaced the weak qualitative wavefront tests with quantitative, physically-grounded ones in `tests/test_wavefront.py`:
  - **Static-ensemble cancellation:** with ~zero transverse temperature, even a strong tilt+defocus wavefront leaves the MZ output unchanged (per-atom wavefront phase is identical at all three pulses and cancels in `−φ₁+2φ₂−φ₃`). This is an exact analytical prediction the simulation reproduces.
  - **Curvature, second-order-in-drift:** the MZ combination is a discrete second-difference (curvature) operator, so the *linear* parts of tilt and defocus cancel for ballistic motion; only the wavefront curvature survives, scaling as `(v·T)²·coeff` (the well-known wavefront-curvature systematic). The test asserts a real nonzero deviation that grows linearly with the defocus coefficient - the honest signature, rather than a large contrast loss that the curvature scaling makes second-order-small.

### Version

`1.2.1` → `1.2.2`.

---

## v1.2.1 (2026-05-30)

QuTiP independent cross-validation backend + honest scientific-package evaluation. **348 → 353 tests** (5 new, QuTiP-gated).

### QuTiP cross-validation (partial C14 - independent validation)

- **New `src/qgrav/validation/qutip_crosscheck.py`**: qgrav computes the single-pulse Raman evolution from a closed-form 2×2 matrix; QuTiP integrates the *same* physics numerically (`sesolve` for the unitary, `mesolve`/Lindblad for spontaneous emission) - a genuinely independent code path.
- **Result:** qgrav's matrix matches the analytic Rabi formula to **3×10⁻¹⁶** (machine precision) and QuTiP's numerical integrator agrees to **1.6×10⁻⁶** across a grid of (Ω_eff, δ, τ). The QuTiP 3-level Lindblad model reproduces the analytic spontaneous-emission loss to within an order of magnitude (ratio ~0.16). This is the first *independent-simulator* evidence that qgrav's core quantum dynamics are correct (partial mitigation of the "no independent review" caveat - a second engine agrees, pending human expert review).
- **Optional dependency** (`pip install qgrav[qutip]`); tests gated with `pytest.importorskip("qutip")` so the core suite is unaffected when QuTiP is absent. Nightly CI installs `[test,qutip]` and runs the cross-check.

### Honest scientific-package evaluation

- **New `docs/SCIENTIFIC_PACKAGE_EVALUATION.md`**: records why **QuTiP** was integrated (open-quantum-system dynamics = exactly qgrav's core physics), why **Qiskit** is deferred (gate-based QC; an MZ→circuit map is pedagogy, not new physics), and why **GEANT4** (radiation transport) and **LAMMPS** (classical MD) are **not applicable** to a dilute cold-atom quantum gas. Building all four would have been months of effort for marginal value on three of them; this honesty is itself the deliverable.

### Version

`1.2.0` → `1.2.1`.

---

## v1.2.0 (2026-05-30)

Physics-rigor release: pulse-center-timing investigation, the finite-ensemble-floor finding, and tightened validation tolerances. **344 → 348 tests.**

### Pulse-center timing investigation (partial C1)

- Added a `pulse_center_timing` flag to `IntegratedPhaseTwoLevelTransitionPropagator` / `...SpatialSuperposition...` (`_aisim_overrides.py`). When True the chirp term `0.5·chirp·t²` is evaluated at the pulse centre (`atoms.time + time_delta/2`) to match `atoms.position` (already mid-pulse after the base half-step); when False (default) at the pulse start.
- **Empirical finding:** pulse-centre timing does **not** reduce the constant g-independent calibration residual at `g=g_chirp` - it *enlarges* it (≈1.1 → ≈5.0 rad for GAIN parameters). The residual is a finite-pulse *discretisation* artefact of evaluating one rotation matrix over the whole pulse, not a time/position asymmetry. It is gravity-independent and removed exactly by the calibration, so it never biases the measured g. Default stays pulse-start (= v1.1); the flag is retained for reproducibility and for the future sub-pulse-integration path.

### The factor-2 mystery solved - finite-ensemble projection floor

- Decomposing the v1.1 Freier simulation (which landed at factor 2.1) showed the dominant term was **not** a noise-injection bug but the **finite-ensemble projection floor** of the test ensemble: `σ_g_floor ∝ 1/√N_atoms` (148 / 92 / 52 nm/s² at N = 300 / 1000 / 3000). Real GAIN uses ~2×10⁷ atoms, so its floor is negligible; the 300-atom test ensemble's floor swamped the injected GAIN budget.
- **Methodological fix:** the published-reference simulation regressions now run at **N = 4000 atoms** (floor ≈ 57 nm/s², below the ~104 nm/s²/√Hz injected budget), so `ASD = √(floor² + budget²)` is genuinely budget-limited. Runtime stays <1 s (MZ matrix ops are vectorised over atoms).

### Tightened validation tolerances (C2, partial C6)

- Freier 2016 simulation regression: factor 3 → **factor 2** (now lands at ~1.2).
- Secondary benchmarks (Hu / Ménoret / Xu / Wu): factor 4.5 → **factor 3** (Ménoret is the wide one at factor ~2.5 because its short T=60 ms gives a genuinely low fringe contrast V≈0.15, inflating the 1/V mid-fringe inversion).
- New `tests/test_pulse_center_timing.py` (4 tests): flag default/toggle, pure-phase effect (magnitudes unchanged), and the 1/√N ensemble-floor scaling.

### Version

`1.1.0` → `1.2.0` in `__init__.py`, `pyproject.toml`, this CHANGELOG.

---

## v1.1.0 (2026-05-29)

The published-reference release. Lands the v1.0 to v1.1 roadmap end-to-end with all 14 research topics applied. **312 to 344 tests** (+32). Highlights:

- **Five automated published-reference regressions**: Freier 2016 (PRIMARY, 96 nm/s²/√Hz), Hu 2013 (4.2 µGal/√Hz, HUST short fountain - research correction: NOT the 10-m tower), Ménoret 2018 (750 nm/s²/√Hz Larzac, T=60 ms NOT 80 ms), Xu 2022 (24 µGal/√Hz, first HUST per-effect systematic budget, NEW), Wu 2019 (37 µGal/√Hz Berkeley mobile, NEW). Marked `@pytest.mark.slow` and run nightly.
- **Vendor subclass refactor (resolves C4)**: the v1.0 physics extensions moved out of vendored AISim into `qgrav/sim_ai/_aisim_overrides.py`. Re-vendoring upstream AISim is now trivial. Guard test enforces no `[LOCAL PATCH]` markers in `vendor/aisim/{prop,beam}.py`.
- **Multi-drop realism (resolves C5, C6, C9)**: PID servo with anti-windup, correlated NLNM/NHNM seismic vibration with optional isolation filter, fitted visibility for the P3→g inversion, explicit technical detection-noise floor (for instruments that are technically-limited not projection-limited, e.g., GAIN).
- **Bertoldi 2019 closed-form finite-τ predictor (resolves partial C1)**: `bertoldi_finite_tau_scale_factor` is reported alongside the empirical calibration so the latter is the empirical confirmation of an analytical prediction, not an unjustified workaround.
- **CI / packaging (resolves C11, JOSS hard gate)**: GitHub Actions workflows for fast tests (Linux + Windows × Py 3.9 / 3.11 / 3.12), nightly slow regressions, and PyPI Trusted Publishing on tag. Dockerfile for headless batch runs.
- **AI Usage Disclosure** (`docs/AI_USAGE_DISCLOSURE.md`, JOSS hard gate): documents the AI-assisted design and lists the concrete bugs that the verification process caught.

The detailed per-phase entries (Phase 12 vendor refactor; Phase 13 Freier regression; Phase 14 YAML wiring; Phase 15 multi-drop realism; Phase 16 secondary benchmarks; Phase 17 CI/packaging; Phase 18 Bertoldi closed form) are below.

### Version

`1.0.2` → `1.1.0` in `__init__.py`, `pyproject.toml`, and this CHANGELOG.

### Open work for v1.2

- Pulse-center timing convention in the integrated-phase override (Phase 18 sub-option, deferred)
- AC-Stark + wavefront YAML exposure for the gravity-sweep path (Phase 14 sub-option, deferred)
- COMPLETE_GUIDE.md full pass + JOSS paper draft + MkDocs site (Phase 19 sub-options, deferred)
- External physics-reviewer feedback on `docs/PHYSICS_REVIEW_PACKET.md` (gates upgrading the `FULLY_SIMULATED` label from "code does not invoke the formula" to "peer-reviewed").

---

### Phase 12 - Subclass refactor of vendor patches (resolves C4)

- The v1.0 physics extensions (`GravityFreePropagator`, chirped `Wavevectors`, integrated-phase + AC-Stark propagators) were moved out of the vendored AISim source and into **`src/qgrav/sim_ai/_aisim_overrides.py`** as subclasses. The vendored `prop.py` and `beam.py` are now byte-for-byte upstream-clean, so re-vendoring a newer AISim release no longer requires manually re-applying physics patches.
- The integrated-phase spatial propagator uses a deliberate MRO (`SpatialSuperposition → IntegratedPhaseTwoLevel → TwoLevel`) so the top-level `_prop_matrix` builds the block-diagonal matrix while its internal `super()._prop_matrix` resolves to the integrated-phase two-level matrix.
- New public re-exports from `qgrav.sim_ai`: `GravityFreePropagator`, `ChirpedWavevectors`, `IntegratedPhaseTwoLevelTransitionPropagator`, `IntegratedPhaseSpatialSuperpositionTransitionPropagator`.
- New guard tests (`tests/test_vendor_aisim_unmodified.py`, 8 tests) fail if a future edit re-introduces a physics patch into the vendored `prop.py`/`beam.py`, and verify the override subclasses reduce exactly to upstream behaviour at zero extension (chirp=0, single_photon_detuning=0, z=0).
- Behaviour-preserving: all previous tests pass unchanged (286 → 294 with the new guard tests).
- Note: `vendor/aisim/atoms.py` retains one intentional `assert→ValueError` validation hardening from v0.9.3 (documented there); it is a robustness fix, not a physics extension, and is out of scope for this refactor.

### Phase 15 - Multi-drop realism (resolves C5, C6, C9)

- **PID servo with anti-windup** (`physics/readout_models.servo_pid_step` + `PIDServoState`): proportional + integral + derivative fringe-lock with an integrator clamp. The multi-drop cycle gained `servo_type="integrator"|"pid"` (the original I-only servo remains the default).
- **Correlated drop-to-drop seismic vibration**: `run_aisim_multi_drop_cycle(correlated_vibration=True, ...)` generates one Peterson NLNM/NHNM displacement time-series for the whole campaign (via `generate_vibration_timeseries`, with optional `vibration_isolation_cutoff_hz`) and injects the per-drop vibration phase `k_eff·[z(0) − 2z(T) + z(2T)]`. Unlike per-drop white noise this produces realistic low-frequency (random-walk/flicker) Allan-deviation structure - verified by a test that the long-τ/short-τ Allan ratio exceeds the white-noise case.
- **Visibility fit** (`fit_visibility=True`): the calibration scan now also fits the fringe contrast (`_calibrate_gravity_phase_and_visibility`), used in the P3→g inversion instead of assuming an ideal contrast of 1.
- **Technical / Raman noise knobs**: `detection_sigma_p` (explicit technical detection σ_P, overriding 1/√N - needed because GAIN-class instruments are technically-limited, not projection-limited) and `raman_phase_noise_rad` (per-shot Gaussian Raman-laser phase noise).
- New result fields: `n_detected_effective`, `detection_sigma_p`, `raman_phase_noise_rad`, `correlated_vibration`, `visibility_estimate`, `servo_type`, `vibration_phase_rad`.
- New tests (`tests/test_multi_drop_realism.py`, 12 tests). Backward-compatible: all defaults preserve prior behaviour (294 → 306 tests).

### Phase 13 - Freier 2016 PRIMARY published-reference regression (resolves partial C10)

- **`src/qgrav/validation/freier_2016_setup.py`** - curated GAIN parameters (T=260 ms, T_cycle=1.5 s, τ_π/2=17 µs, single-photon detuning −700 MHz, beam radius 15 mm, etc.) and the documented per-shot noise budget (technical detection σ_P=6×10⁻³, Raman-phase 40 nm/s²/shot, vibration 71 nm/s²/shot). Every value sourced verbatim in `docs/research/RESEARCH_FREIER_2016.md`.
- **Critical research correction:** the budget reflects that GAIN is technically-limited, not projection-limited - the 96 nm/s²/√Hz is dominated by vibration + Raman-phase + technical detection noise, *not* by √N atomic projection noise (which is ~10× smaller). The simulation is driven by `detection_sigma_p` and `raman_phase_noise_rad` rather than `n_atoms`.
- **`tests/test_published_validation_freier_2016.py`** - 6-test regression: curated-parameter sanity (2), analytical noise-budget reproduction within factor 2 (2), `@pytest.mark.slow` end-to-end multi-drop simulation reproduces 96 nm/s²/√Hz within factor 3 (2). The `slow` marker is registered in `pyproject.toml`.
- Verified: simulated ASD ≈ 2×10⁻⁷ m/s²/√Hz vs target 9.6×10⁻⁸ (factor 2.1, residual driven by ensemble V≈0.6 vs ideal V=1 on the inversion). Every release post-v1.1 must continue to pass these tests.

### Phase 16 - Hu / Ménoret / Xu / Wu published-reference regressions (resolves rest of C10)

Four new curated setups, each with verbatim parameter provenance in `docs/research/`:

- **`hu_2013_setup.py`** - HUST short atomic fountain (NOT the 10 m drop tower, contrary to v1.0 assumption). T=300 ms, contrast 0.15, per-effect noise budget from the HUST 2015 review (detection 3.3 µGal/√Hz + vibration 1.2 + Raman 0.8 → 3.6 in quadrature vs published 4.2 µGal/√Hz).
- **`menoret_2018_setup.py`** - Muquans AQG-A01 Larzac campaign. T=60 ms, cycle 500 ms (2 Hz), feed-forward Raman-phase correction (NO mechanical isolation), contrast 0.40. Targets the as-operated Larzac value of 750 nm/s²/√Hz.
- **`xu_2022_setup.py`** *(NEW 2020+ target)* - HUST-QG transportable. First HUST instrument with a published per-effect systematic budget (3 µGal combined uncertainty, 1.3 µGal ICAG equivalence).
- **`wu_2019_setup.py`** *(NEW 2020+ target)* - Berkeley mobile gravimeter. 37 µGal/√Hz, <2 µGal in ~30 min.

- **`tests/test_published_validation_secondary.py`** - 12 tests: per-setup parameter-integrity (4), parametrised noise-budget reproduction (4), parametrised `@pytest.mark.slow` end-to-end simulation regressions (4). Fixed seeds per setup for order-independence. Simulation envelope is factor 4.5 (vs Freier's factor 3 for the primary target) to absorb the 1/V scaling on the mid-fringe inversion at test-ensemble contrast levels; Phase 18 will tighten this once the Bertoldi finite-τ closed form is wired in.
- Cumulative: **324 tests** (306 → +18: 6 Freier + 12 secondary). All four published references now have automated regression coverage.

### Phase 14 - YAML wiring for the multi-drop noise machinery (resolves C7, C8 partial)

- `run_simulation_from_config` now exposes the full Phase-15 multi-drop knob set: `detection_sigma_p`, `raman_phase_noise_rad`, `correlated_vibration`, `seismic_model`, `vibration_isolation_cutoff_hz`, `vibration_seed`, `fit_visibility`, `servo_type`, `servo_kp/ki/kd`. Each defaults to off / backward-compatible behaviour.
- New `tests/test_yaml_multi_drop_config.py` (6 tests) verifies each knob round-trips through the YAML entrypoint and lands in the result dict.
- 324 → **330 tests**. AC-Stark + wavefront YAML exposure for the *gravity-sweep* path is deferred to v1.2 (still accessible programmatically as before; the multi-drop noise machinery - needed for Freier 2016 - is the v1.1 priority).

### Phase 18 - Bertoldi 2019 closed-form finite-τ correction (resolves partial C1)

- **New public function `qgrav.sim_ai.bertoldi_finite_tau_scale_factor(tau_pi_half_s, interferometer_time_s)`**: returns the multiplicative finite-τ correction `1 - (2π-4)/π · (τ/T) ≈ 1 - 0.7268·η` to the MZ gravity phase, per Bertoldi, Minardi & Prevedelli, *Phys. Rev. A* 99, 033619 (2019), Eq. 21. The Cheinet 2008 / Le Gouët 2008 / Fang-Mielec 2018 / Bertoldi 2019 pulse-CENTER-to-pulse-CENTER convention for T is documented and consistent across the literature (`docs/research/RESEARCH_FINITE_TAU_FORMULAS.md`).
- The gravity sweep result now reports **both** `empirical_phase_offset_rad` (the calibrated residual the simulation removes numerically) **and** `bertoldi_finite_tau_scale_factor` (the analytical prediction for what that residual *should* be from finite-pulse-duration physics). The calibration is no longer an unjustified workaround - it is the *empirical confirmation of an analytical prediction* from the published literature. This is the credibility upgrade C1 asked for.
- 7 new tests (`tests/test_bertoldi_finite_tau.py`) verify the closed form (zero-τ limit, canonical coefficient, parameter-specific values for Freier and Ménoret, error handling) and that the result dict surfaces both diagnostics. 330 → **337 tests**.
- Note: pulse-center timing adjustment (the other Phase 18 sub-option) is deferred to v1.2 because it requires modifying the integrated-phase override; the Bertoldi predictor alone is enough to restore credibility of the calibration approach.

### Phase 17 - CI / packaging scaffolding (resolves C11, JOSS hard gate)

- **`.github/workflows/test.yml`** - pytest matrix on Ubuntu + Windows × Python 3.9 / 3.11 / 3.12 with `MPLBACKEND=Agg`, runs the fast suite (`-m "not slow"`) on every push and PR.
- **`.github/workflows/nightly.yml`** - runs the `@slow` published-reference simulation regressions (Freier + Hu + Ménoret + Xu + Wu) once per night.
- **`.github/workflows/release.yml`** - builds wheel + sdist and publishes to PyPI via Trusted Publishing on every `v*` tag (no API token stored in this repo; the repo owner configures qgrav as a trusted publisher in their PyPI project settings before the first release).
- **`Dockerfile` + `.dockerignore`** - minimal headless Python 3.11 container, ENTRYPOINT `qgrav`, mounts host `configs/` and `runs/` directories.
- New `tests/test_ci_packaging.py` (7 tests) smoke-checks the workflow YAML, Dockerfile and `.dockerignore` so a typo doesn't ship.
- 337 → **344 tests**. This phase resolves the v1.0 caveat C11 (no CI / packaging / DockerHub) and clears the JOSS hard pre-review gate that requires automated tests in CI. MkDocs site generation is deferred to v1.2 (the markdown docs in `docs/` are already structured for it).

---

## v1.0.2 (2026-05-29)

**Reference-registry audit release.** A full audit of all remaining registry values (Topic 13 of the internet-research brief, `docs/research/RESEARCH_REFERENCE_AUDIT.md`) found **three unit-category errors** and **two ambiguous entries** that survived v1.0.1. All are fixed. **10 new regression tests** (276 → 286 passing). The registry grew 12 → 14 entries (two mis-typed quantities were split into separate correctly-labelled keys).

### Fixed - unit-category errors (a correct number tagged with the wrong physical quantity)

- **`kasevich_chu_1991_first_demo`**: value `3e-6` was tagged `m/s²/√Hz` but the Kasevich & Chu 1991 abstract reports it as a **dimensionless Δg/g resolution after 1000 s integration** (and used **sodium**, not Rb). Re-typed to `unit="dimensionless (delta_g/g at 1000 s)"`. As an ASD it would be ≈ 9e-4 m/s²/√Hz.
- **`bidel_2018_marine`**: was `1.7e-6 m/s²/√Hz` - that number is the **0.17 mGal static measurement uncertainty** (a bias, no /√Hz), not the sensitivity. Corrected to the paper's actual static sensitivity **0.8 mGal/√Hz = 8e-6 m/s²/√Hz**. The 0.17 mGal figure is preserved in a new key `bidel_2018_marine_static_uncertainty` (1.7e-6 m/s², no /√Hz).
- **`sg_noise_floor`**: was `1e-11 m/s²/√Hz` - that is the **1 nGal frequency-domain detectability** mislabeled as an ASD. Corrected to the true superconducting-gravimeter ASD floor **1.8e-9 m/s²/√Hz** (LSBB best site at 1 mHz, Van Camp et al. 2017) - ~100-300× higher. The 1 nGal detectability is preserved in a new key `sg_detectability_nGal` (1e-11 m/s²).

### Fixed - ambiguous entries

- **`nlnm_low_freq`**: was `7e-10 m/s²/√Hz` (≈ −183 dB), ~4 dB too high. Corrected to the true NLNM acceleration-ASD minimum **4e-10 m/s²/√Hz** (−187.5 dB) at ~30-100 s period. Description now flags the strong frequency dependence.
- **`mz_visibility`**: value `0.5` retained but **could not be verified** in the cited Peters 2001 text (paywalled figure). Re-labelled as the idealised two-output Mach-Zehnder maximum, no longer attributed to Peters 2001. (A verified real-instrument contrast is C = 0.3, Bidel et al. 2018.)

### Added

- **`_V1_0_1_VALUE_BUGS`** dict in `published_references.py`: in-code log of the v1.0.1→v1.0.2 corrections (old value, new value, unit change, reason) for every audited key.
- **`tests/test_published_references_values.py`**: new `TestV102AuditCorrections` class (8 tests) plus expanded parametrised unit-conversion grid (now 14 entries).

### Audit verdict (all 12 original entries checked)

6 CORRECT (Freier ×3, Ménoret long-term, Peters accuracy, Hu - already fixed in v1.0.1), 3 WRONG (now fixed), 2 AMBIGUOUS (now re-labelled), plus the v1.0.1 Hu/Ménoret short-term fixes. The registry is now believed fully audited against primary sources.

### Version

`1.0.1` → `1.0.2` in `__init__.py` and `pyproject.toml`.

---

## v1.0.1 (2026-05-27)

**Reference-registry bug-fix release.** Two values in `validation/published_references.py` were numerically incorrect in v1.0.0 and have been fixed. Anyone using the v1.0.0 registry to set noise-budget targets should re-evaluate. **4 new regression tests** (253 → 257 passing).

### Fixed

- **`hu_2013_short_term_noise`**: corrected from `4.2e-9` to `4.2e-8` m/s²/√Hz. The published value is 4.2 µGal/√Hz, and since 1 µGal = 10⁻⁸ m/s², this equals 4.2×10⁻⁸ m/s²/√Hz. The v1.0.0 value was off by a factor of 10.
  Reference: Hu et al., Phys. Rev. A 88, 043610 (2013), §III "Sensitivity".

- **`menoret_2018_short_term_noise`**: corrected from `5e-7` to `7.5e-7` m/s²/√Hz. The paper's Larzac Allan-deviation trace (Fig. 4) reports 750 nm/s²/√Hz, not 500.
  Reference: Ménoret et al., Sci. Rep. 8, 12300 (2018), Fig. 4.

Both fixed entries now include the human-readable unit in their description string so the value can be spot-checked against the paper.

### Added

- **`_V1_0_0_VALUE_BUGS`** dictionary in `published_references.py`: a public, in-code log of the v1.0.0 wrong values, the corrections, and the reasons. Anyone seeing this dict during debugging should reconsider whether their downstream analysis depended on the wrong numbers.
- **`tests/test_published_references_values.py`**: 4 new regression tests covering Freier 2016, Hu 2013, Ménoret 2018, and a parametrised unit-conversion sanity check across all 12 registry entries.

### Why this matters now

Per the v1.1 roadmap (`docs/ROADMAP_V1_TO_V2.md`), Freier 2016 is the **primary regression target** and Hu 2013 + Ménoret 2018 are the lab-best-case and transportable-robustness targets. The Phase 13/16 automated benchmarks would all have been wrong if the registry values were left at the v1.0.0 numbers. Releasing this as a quick bug-fix point release before continuing v1.1 work ensures no one builds on the wrong values.

### Version

`1.0.0` → `1.0.1` in `__init__.py` and `pyproject.toml`.

---

## v1.0.0 (2026-05-26)

**Full physics simulation upgrade.** Transforms qgrav from a hybrid
analytical+AISim wrapper into a self-consistent numerical gravimeter
simulation where the gravity phase **emerges from the simulation** rather
than being injected via the closed-form k_eff·g·T² formula. **61 new tests**
(192 → 253 passing).

---

### Phase 1 - `GravityFreePropagator` (Tier 1a)

- New AISim propagator `GravityFreePropagator` performs exact ballistic
  kinematics under uniform gravity with optional linear gravity gradient
  γ·(z − z_ref). Identity quantum matrix; velocity and position update each
  step.
- Exported from `qgrav.vendor.aisim`.
- 10 new tests covering position/velocity updates, gradient, two-half-step
  equivalence, state preservation, time update.

### Phase 2 - Chirped laser detuning (Tier 1b)

- `Wavevectors` accepts `chirp_rate_rad_per_s2` and adds `chirp_rate·t` to
  the Doppler shift, enabling cancellation of gravity-induced Doppler.
- 5 new tests covering chirp=0 backward-compatibility, gravity-Doppler
  cancellation, dimensional consistency, linear time scaling.

### Phase 3 - Gravity-enabled MZ sequence (Tier 1c)

- `_run_mach_zehnder_sequence_with_gravity` runs the three-pulse MZ with
  `GravityFreePropagator` and chirped `Wavevectors`.
- Patched `TwoLevelTransitionPropagator._prop_matrix` to use the
  physically correct integrated laser phase
  `-k_eff·z(t₀) + 0.5·chirp·t₀²` instead of `delta·t₀`. This makes the MZ
  combination produce the standard `k_eff·(g − g_chirp)·T²` gravity phase.
- Per-sweep empirical calibration (`_calibrate_gravity_phase_offset`)
  removes residual pulse-timing offsets at g = g_chirp.
- `run_aisim_gravity_sweep` and `run_aisim_vibration_sensitivity_sweep`
  gained `gravity_propagation` and `gravity_gradient_per_m` parameters.
- Config dispatcher passes the new parameters through.
- 9 new cross-validation tests verifying simulated and hybrid modes track
  the same fringe within finite-pulse-duration physics differences.

### Phase 4 - Time-domain vibration noise (Tier 2a)

- `generate_vibration_timeseries` produces a real acceleration time-series
  matching the Peterson NLNM/NHNM PSD, with optional second-order
  high-pass isolation filter `H²(f) = f⁴/(f² + f_c²)²`. Velocity and
  displacement spectra obtained by dividing by jω and -ω².
- 7 new tests for PSD shape, isolation attenuation, determinism, output
  shape, and double-integral self-consistency.

### Phase 5 - Detection noise & spontaneous emission (Tier 2b)

- `add_detection_noise` adds Gaussian noise with σ = 1/√N_detected, clipped
  to [0, 1].
- `spontaneous_emission_loss_probability` returns p_se = (Ω/Δ)²·τ/τ_sp.
- 6 new tests for scaling laws, clipping, determinism, and order-of-magnitude.

### Phase 6 - Multi-drop measurement cycle (Tier 3a)

- `run_aisim_multi_drop_cycle` runs N independent drops, each with a fresh
  ensemble (seed + i), full MZ sequence, optional detection noise, optional
  servo. Returns `g_estimates`, `timestamps`, `mean_g`, `std_g`,
  `allan_taus_s`, `allan_dev_m_s2`.
- `_allan_deviation` computes overlapping Allan deviation across octave
  averaging windows.
- Wired into `run_simulation_from_config` dispatcher.
- 10 new tests covering n_drops, mean accuracy, Allan-deviation arrays,
  independence, study-scope classification, and config passthrough.

### Phase 7 - Fringe-locking servo (Tier 3b)

- `servo_integrator_step(population, phase_estimate, setpoint, gain)`
  performs one step of a digital integrator servo on the phase bias.
- Integrated with the multi-drop cycle (`servo_enabled=True`).
- 6 new tests for sign conventions, mid-fringe lock, g-estimate
  convergence, and open-loop behaviour.

### Phase 8 - AC Stark / light shift (Tier 4a)

- `TwoLevelTransitionPropagator` and `SpatialSuperpositionTransitionPropagator`
  gained `single_photon_detuning_hz`. When non-zero, the two-photon
  detuning gains a position-dependent AC Stark shift Ω_eff² / (4Δ) that
  varies with the atom's beam-radius position.
- 3 new tests for zero-detuning backward compatibility, fringe shift, and
  contrast reduction.

### Phase 9 - Wavefront aberrations (Tier 4b)

- `_build_wavefront` constructs an AISim Wavefront from a Zernike
  coefficient dict.
- `_run_mach_zehnder_sequence` accepts `wavefront` and
  `single_photon_detuning_hz` and passes them through to all three pulse
  propagators.
- 5 new tests for None backward compatibility, defocus-driven contrast
  reduction, and tilt-driven fringe shift.

### Phase 10 - Truth checks

- `_check_gravity_sweep` now branches on `gravity_propagation`: hybrid
  mode keeps the strict analytical-phase match; simulated mode checks
  fringe visibility > 0.3 and study scope FULLY_SIMULATED.
- New `_check_multi_drop_cycle` handler verifies n_drops correctness,
  finite estimates, monotonic timestamps, |mean(g) − g_true| < 1e-5,
  Allan-array consistency, and Allan-deviation behaviour.

### Version

`0.9.3` → `1.0.0` in `__init__.py`, `pyproject.toml`, and this CHANGELOG.

---

## v0.9.3 (2026-05-25)

Codebase audit fix release. Addresses 15 issues found in a rigorous three-pronged audit (numerics, error handling, robustness, test coverage). **16 new tests** (176 → 192 passing).

---

### Numerical & Correctness Fixes

- **`equivalent_gravity_error_m_s2`** - replaced unsafe `max(..., 1e-30)` denominator floor (which produced ~1e22 results on zero input) with proper input validation: `k_eff > 0`, `T > 0`
- **`interpolate_psd`** - added guard against `log10(0)` / `log10(negative)` which produced -inf/nan propagation. Now raises `ValueError` for non-positive frequencies
- **Empty tide RMS** - `apply_tide_correction` with empty arrays now returns `NaN` instead of `0.0` (semantically correct: no data ≠ zero error)

### Error Handling

- **CLI error handling** - all CLI commands now wrapped in `_safe_dispatch()`: prints clean `Error (ExceptionName): message` instead of raw tracebacks. Added `--verbose / -v` flag to show full tracebacks during development
- **Systematics errors** - promoted swallowed `logger.debug("Systematics computation skipped")` to `logger.warning` in both gravity and interferometer pipelines
- **Array length mismatch** - interferometer pipeline now warns when input arrays have mismatched lengths before truncating
- **Pipeline config validation** - `cfg["bench_real_gravity"]` and `cfg["bench_real_ifo"]` replaced with `.get()` + explicit `ValueError` with context (was bare `KeyError`)

### Robustness & Code Quality

- **PSD plot guards** - all `psd["f_hz"][1:]` slicing in `_plots.py` and `visuals.py` now guarded with length checks to prevent empty loglog on tiny datasets
- **Vendored AISim validation** - `assert shape[1] == 6` replaced with `ValueError` so validation survives `python -O`. Documented as local patch for re-vendoring
- **`_jsonable()` extended types** - handles `np.datetime64` → str, `np.timedelta64` → float seconds (sub-second precision preserved), `np.str_`/`np.bytes_` → str. Fixed isinstance ordering for NumPy 2.x where `timedelta64` inherits from `signedinteger`
- **Run directory uniqueness** - appended `uuid4().hex[:8]` to run_id to prevent collisions on concurrent runs within the same microsecond
- **Dead pyplot cleanup** - removed `import matplotlib.pyplot as plt` and `plt.close("all")` from pipeline `__init__.py` (dead code after OO migration)
- **PEP 561 marker** - added `py.typed` for typed package support

### Test Fixes

- **Allan edge-case assertion** - `assert len(result["adev"]) >= 0` (always true) → `>= 1`
- **CLI test** - `pytest.raises(Exception)` → `pytest.raises(SystemExit)` to match `_safe_dispatch` behavior
- **New test file:** `tests/test_audit_fixes.py` - 15 tests covering input validation, empty-data edge cases, CLI error handling, `_jsonable` extended types, PSD short-data guard, and pipeline config validation

### Version

`0.9.2` → `0.9.3` in `__init__.py` and `pyproject.toml`.

---

## v0.9.2 (2026-05-22)

Developer experience improvements. **6 new tests** (170 → 176 passing).

---

### CLI Commands (Phase 4.1-4.3)

- **`qgrav validate-data --source PATH`**: Load and validate a gravimetry dataset
  without running the full pipeline. Prints station code, sample rate, IGETS
  level, gap report, statistics, unit warnings, and coordinates.
- **`qgrav info`**: Print version, Python version, platform, dependency versions
  (core and optional), and vendored package availability.
- **`qgrav run --dry-run`**: Validate config and print a summary (bench type,
  source path, PSD method, etc.) without executing the pipeline.

### Test Determinism (Phase 4.4)

- Pinned `MPLBACKEND=Agg` via `os.environ` in `conftest.py` (supplements
  `matplotlib.use("Agg")` call)
- Added determinism documentation to `conftest.py` docstring: seed discipline,
  tolerance guidance, `@pytest.mark.flaky` for statistical tests

### Pre-commit Hooks (Phase 4.5)

- Added `--exit-non-zero-on-fix` to ruff hook for CI compatibility
- Added local `constants-regression` hook: runs `test_physics_constants.py` and
  `test_unit_conversions.py` when `src/qgrav/physics/constants.py` is modified
- Added local `tide-catalogue-regression` hook: runs tide constituent tests when
  `_tides_hw95.py` is modified

---

## v0.9.1 (2026-05-22)

Robustness and testing improvements. **22 new tests** (148 → 170 passing).

---

### Thread-safe Matplotlib (Phase 3.1)

- **Replaced all `plt.*` global API calls with OO `Figure`/`Axes` API** across the entire pipeline package
  - `_plots.py`: Rewritten - `Figure()` + `ax.plot()` instead of `plt.figure()` + `plt.plot()`
  - `_simulation.py`: Rewritten - same OO pattern, removed `plt.close("all")` cleanup
  - `_common.py`: Removed unused `import matplotlib.pyplot as plt`
- All plotting is now thread-safe for concurrent pipeline runs

### Edge-case Allan Deviation Tests (Phase 3.2)

- 6 new tests in `tests/test_allan_edge_cases.py`:
  - Minimum 10 samples accepted, 9 samples raises ValueError
  - Large tau near half-record boundary handled gracefully
  - Constant input returns ADEV = 0
  - Single-element taus array works
  - Custom backend matches allantools on edge-case data

### Property-based Tests with Hypothesis (Phase 3.3)

- Added `hypothesis` to `[project.optional-dependencies]` test group
- 21 new property tests in `tests/test_properties.py` covering:
  - **PSD**: non-negativity, frequency grid structure, constant-input zero, Welch non-negativity
  - **Allan deviation**: non-negativity, linear amplitude scaling
  - **Phase models**: gravity→phase→gravity roundtrip, bias additivity, normalized signal bounds
  - **Sensitivity function**: integral-is-zero (balanced interferometer), antisymmetry about T, transfer function notches at harmonics, non-negativity
  - **Shot noise**: positivity, improves with more atoms
  - **Tide model**: µGal-to-m/s² conversion, finite output for all latitudes, amplitude bounds
  - **Error statistics**: perfect prediction yields zero RMSE, RMSE ≥ MAE, improvement sign

### Synthetic Correction Integration Test (Phase 3.4)

- New test `test_synthetic_tide_correction_improves_allan_deviation`:
  creates a 3-day synthetic signal (tide + white noise), applies HW95 tide
  correction, and verifies that the corrected Allan deviation is strictly
  lower than the uncorrected one at all averaging times

---

## v0.9.0 (2026-05-22)

Architecture refactoring. **No new tests** in this phase - all 140 tests pass unchanged.

---

### Pipeline Package (Phase 2)

- **Split `pipeline.py` (933 lines) into `pipeline/` package** with 6 focused modules:
  - `__init__.py` (44 lines) - `run_pipeline()` entry point
  - `_common.py` (264 lines) - `RunPaths`, helpers, summary writer
  - `_gravity.py` (259 lines) - real-gravity pipeline stage
  - `_interferometer.py` (204 lines) - virtual/real interferometer pipeline stage
  - `_plots.py` (172 lines) - matplotlib plot generation
  - `_simulation.py` (77 lines) - AISim integration
- All public imports (`from qgrav.pipeline import run_pipeline`) remain unchanged
- Internal test imports updated (`_match_taus` moved to `_common`)

### Type Definitions

- Created `src/qgrav/types.py` with TypedDicts:
  - `GravityDataset` - return type of `load_real_gravity_dataset`
  - `AllanResult` - return type of `allan_deviation_overlapping`
  - `PSDResult` - return type of `compute_psd`
  - `AiSimResult` - return type of `run_aisim_*` functions

---

## v0.8.1 (2026-05-22)

Critical bug fixes and licensing compliance. **6 new tests** (134 → 140 passing).

---

### Licensing (Phase 0)

- **Relicensed to GPL-3.0-or-later** - resolves incompatibility with vendored AISim (GPL-3.0) and AllanTools (LGPL-3.0)
- Created `LICENSE` file at project root with full GPL-3.0 text
- Replaced placeholder `docs/THIRD_PARTY_LICENSES/AISim-LICENSE.txt` with actual GPL-3.0 text
- Moved vendored AllanTools from `src/allantools/` to `src/qgrav/vendor/allantools/` for proper namespacing
- Fixed self-import in vendored `ci.py` (now uses relative import)
- Updated `allan.py` to import from `qgrav.vendor.allantools` with fallback to external package

### Bug Fixes (Phase 1)

- **AISim global random state**: replaced `np.random.seed()` with `np.random.default_rng()` in `atoms.py`, `dist.py`, and `beam.py` - AISim no longer mutates global NumPy random state
- **Raw data preservation**: pipeline now saves `gravity_residual_raw`, `gravity_residual_full_raw`, and `tide_subtracted` arrays in `data.npz` when corrections are applied
- **Raw vs corrected plot**: new `raw_vs_corrected` plot kind in `visuals.py` overlays pre- and post-correction series
- **Gap detection tolerance**: `_gap_report` and `_select_longest_contiguous_segment` now use configurable `gap_tolerance_fraction` (default 0.1) instead of exact `dt != expected_dt_s` comparison - prevents spurious segment fragmentation from timing jitter
- **Corrections warnings**: pipeline now emits `corrections_warnings` in `metrics.json` and shows a red warning banner in the HTML report when corrections are skipped (e.g., missing station coordinates) or partially applied
- **Pressure bounds checking**: pressure correction now validates temporal coverage before interpolation - skips correction if overlap < 50%, warns if < 95%
- **HTML autoescape**: verified and tested that Jinja2 `autoescape=True` correctly escapes `<script>` and similar payloads in config text and warnings

---

## v0.8.0 (2026-05-17)

Milestone 1 of the Physics PRD: scientific foundations. Adds a physical constants registry, Mach-Zehnder sensitivity function with vibration integrator, solid-earth tide and atmospheric pressure corrections for real gravimetry data, ACF-based noise identification, study-scope labelling on every simulation, and expands the published-reference registry from 4 to 12 entries. **55 new tests** (79 → 134 passing).

---

### Physical Constants Module (W1)

New `src/qgrav/physics/constants.py` - single source of truth for all physical constants used across the codebase.

- Frozen `PhysicalConstant` dataclass with `value`, `unit`, `source`, `uncertainty`, `note` fields
- CODATA fundamentals: speed of light, Planck constant, Boltzmann constant
- Rb-87 / Cs-133 atom data: masses, hyperfine frequencies, D2 wavelengths, recoil velocities/energies
- Effective wavevectors: `K_EFF_RB87_D2 = 1.6105747e7 rad/m` (counter-propagating Raman)
- Geophysical: Earth rotation rate (IERS 2010), free-air gradient, standard/nominal gravity
- All previously hardcoded literals in `systematics.py`, `aisim_adapter.py`, and `gui/app.py` replaced with constants module references
- Regression test (`test_physics_constants.py`) scans source files for stray numerical literals

### Sensitivity Function Module (W2)

New `src/qgrav/physics/sensitivity_function.py` - three-pulse Mach-Zehnder sensitivity function and vibration transfer function (Cheinet 2008).

- `sensitivity_function_time_domain(t, *, interferometer_time_s, pulse_duration_s=0)` - instantaneous and finite-pulse g_s(t)
- `transfer_function_vibration(f_hz, ...)` - laser-phase transfer function |G(2πf)|² = 16 sin⁴(πfT) / (2πf)²
- `acceleration_to_phase_transfer_function_sq(f_hz, *, ..., k_eff_rad_per_m)` - acceleration-to-phase |H_a|² = 16 k_eff² sin⁴(πfT) / (2πf)⁴
- `integrate_vibration_noise(psd_acceleration, f_hz, ...)` → `{sigma_phi_rad, sigma_g_m_s2, sigma_g_ugal}` via trapezoidal integration

New `src/qgrav/physics/_seismic_models.py` - Peterson 1993 NLNM/NHNM seismic noise floor models as (f_hz, psd) pairs with log-log interpolation.

### Corrections Module (W6)

New `src/qgrav/datasets/corrections.py` - tide and atmospheric pressure corrections for IGETS gravimetry data.

- `detect_igets_level(data)` - heuristic from sample rate (1 Hz → L1, 1/60 Hz → L2, 1/3600 Hz → L3)
- `apply_tide_correction(timestamps, values, *, latitude_deg, longitude_deg, backend="auto")` - PyGTide preferred, internal HW95 fallback
- `apply_pressure_correction(timestamps, gravity, pressure, *, admittance_nm_s2_per_hpa=-3.0)` - Crossley 1995 linear admittance
- Returns corrected series plus `{backend_used, rms_subtracted_ugal}` metadata

New `src/qgrav/datasets/_tides_hw95.py` - simplified 20-constituent Wenzel HW95 tidal catalogue.

- Constituents: M2, S2, N2, K2, K1, O1, P1, Q1, Mf, Mm, plus 10 smaller
- Doodson-argument computation from UTC timestamps (GMST, lunar/solar longitudes)
- Body-tide elasticity factor δ = 1.16 (Wahr-Dehant)
- Geographic amplitude factors: cos²(lat) for semi-diurnal, sin(2·lat)/2 for diurnal
- Truncation error ~50 nGal RMS vs full HW95 catalogue

### ACF Noise Identification (W9)

- New `identify_noise_type_acf()` in `metrics/allan.py` wrapping `allantools.ci.autocorr_noise_id`
- Lag-1 autocorrelation method (Riley 2004) - more robust than slope-fitting for mixed noise
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
| `pressure_csv_path` | string | - | Path to pressure CSV |
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
| A1 | `fbe3996` | **Fix dashboard rendering bug** - nested `for ax in axes.flat` loop in `visuals.py` shadowed the axis variable and caused premature `return`. Replaced with explicit subplot assignments. |
| A2 | `de40cea` | **Reformat semicolon-joined lines** - split 10+ semicolon-joined matplotlib calls in `pipeline.py` plot functions onto separate lines. |
| A3 | `6ca0cfe` | **Track dropped rows** - `real_ifo.py` CSV loader now counts rows dropped due to NaN/malformed data and stores `dropped_rows` in output dict. |
| A4 | `1eaa825` | **Fix float tau matching** - replaced fragile `np.intersect1d` on float64 arrays with `_match_taus()` using `np.searchsorted` and relative tolerance (`rtol=1e-9`). |
| A5 | `719e55c` | **Clean up temp configs** - GUI now tracks temporary config files in `_temp_config_paths` list and deletes them on window close via `WM_DELETE_WINDOW` protocol. |
| A6 | `8f40a87` | **AISim license placeholder** - added `docs/THIRD_PARTY_LICENSES/AISim-LICENSE.txt` and referenced it in `AISIM_INTEGRATION.md`. |
| A7 | `c5d54b3` | **Document R-squared asymmetry** - expanded `curve_correlation` docstring explaining R-squared is asymmetric, can be negative, and how it differs from Pearson correlation. |
| A8 | `fc0a5e2` | **Clarify scipy dependency** - added comment in `pyproject.toml` noting scipy is only required by vendored allantools and vendor/aisim, not qgrav core. |

### Track B: Scientific Validation

| Task | Commit | Description |
|------|--------|-------------|
| B1 | `8a2296a` | **Shot-noise sensitivity function** - `shot_noise_sensitivity_m_s2_per_sqrt_hz()` implementing `1/(C * k_eff * T^2 * sqrt(N/T_cycle))` with full input validation. Also added `sensitivity_ugal_per_sqrt_hz()` wrapper. |
| B2 | `72fd328` | **Sensitivity in AISim outputs** - all three Mach-Zehnder simulation functions (`phase_scan`, `gravity_sweep`, `vibration_sweep`) now compute and report shot-noise sensitivity using fringe visibility as contrast. |
| B3 | `758b375` | **Noise type identification** - `identify_noise_type()` classifies Allan deviation curves via log-log slope fitting into 5 noise types (white PM, flicker PM, white FM, flicker FM, random walk FM). |
| B4 | `5f66832` | **Noise ID in pipeline** - both pipeline paths (interferometer and real gravity) now compute noise identification and Allan minimum, storing results in `metrics.json` and `SUMMARY.md`. |
| B5 | `758b375` | **Allan minimum finder** - `allan_minimum()` locates the optimal averaging time (tau at minimum ADEV) with index. |
| B6 | `b403aa2` | **Systematic effects module** - new `physics/systematics.py` with `gravity_gradient_shift_m_s2()`, `coriolis_shift_m_s2()`, and `systematics_summary()`. All clearly documented as order-of-magnitude estimates not included in AISim. |
| B7 | `38b1dc8` | **Published references module** - frozen `PublishedReference` dataclass with DOI links, `REFERENCES` registry (Freier 2016, Menoret 2018, SG noise floor, MZ visibility), and `compare_to_reference()` helper. |

### Track C: GUI Refactor & Infrastructure

| Task | Commit | Description |
|------|--------|-------------|
| C1 | `f74455f` | **GUI module split** - moved `gui.py` to `gui/` package. Extracted `MetricCards` to `gui/widgets/metric_cards.py` and `ScrollableFrame` to `gui/widgets/scrollable_frame.py`. `gui/__init__.py` re-exports `QGravApp` and `main`. |
| C2 | `0d70853` | **Allan plot noise annotation** - all 4 Allan deviation plot locations in `visuals.py` now show noise type and slope annotation via `_annotate_noise_type()`, wrapped in try/except to never break plots. |
| C3 | `9633b22` | **Systematics in HTML report** - Jinja2 template gains a systematic effects table showing gravity gradient, Coriolis, and total in both m/s^2 and uGal. Pipeline computes systematics for both bench types. |
| C4 | `60ece53` | **Batch processing scripts** - `scripts/batch_scan_stations.py` scans all stations and writes quality metrics to CSV. `scripts/multi_station_comparison.py` produces overlaid Allan/PSD plots with bar chart. |
| C5 | `330cd18` | **IGETS unit format expansion** - `gravimetry.py` now recognizes `nm/s**2`, `nm s-2`, `nanometers/second**2`, `nm/s2` as valid unit variants. |

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
| 5 | `_match_taus` was O(n^2) - 3.5 seconds for 5000 elements | Rewrote with `np.searchsorted` - 0.015s (230x speedup) |
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
