# Patches and Architecture Notes

This document records the robustness patches applied after review feedback.

## Patched now

### 1) Vendored AISim namespace collision
The bundled AISim copy was moved from a top-level package path into:

- `qgrav.vendor.aisim`

The AISim adapter now imports the vendored copy first and falls back to an externally installed `aisim` package only if the vendored copy is absent.

Why this matters:
- avoids accidental import shadowing
- makes the bundled dependency explicit
- reduces the chance that `import aisim` resolves to the wrong package

### 2) Run folder collision
Run directories now use microsecond timestamps and a retry loop, which avoids collisions when multiple runs start inside the same second.

### 3) Real data reverse timestamp detection
Reverse timestamps are now detected **before sorting**, so data-quality issues are not hidden by preprocessing.

### 4) Robust CSV / `.ggp` handling
The real-data loaders now handle more edge cases:
- malformed rows are dropped instead of crashing immediately
- NaN / non-finite values are removed
- single-row CSV inputs are normalized into 1D arrays
- sample-rate inference uses **median spacing**, which is more robust to jitter than the first difference

### 5) Unit sanity warnings
Real gravimetry ingestion now stores `unit_warnings` when values look suspicious or units are unrecognized.

### 6) Run metadata
Each run now saves:
- `run_metadata.json`

This includes the timestamp, config snapshot, version, and top-level metrics keys.

### 7) Simulation plot preservation
Simulation plots are no longer truncated to the first two entries. Reports and the visualizer now support all declared simulation plot specs.

### 8) GUI startup behavior
The GUI now prefers `TkAgg` for desktop interactivity and fails with a clear runtime error in headless environments instead of crashing obscurely.

## Confirmed, no patch needed

### CLI entrypoint
The project already exposes:

```toml
[project.scripts]
qgrav = "qgrav.cli:main"
qgrav-gui = "qgrav.gui:main"
```

So `qgrav run ...` and `qgrav gui ...` are valid when the package is installed.

## Still recommended next (not fully refactored in this patch)

### Pipeline stage separation
The pipeline is still becoming more complex as the number of lanes grows.
A deeper refactor should introduce a dedicated stage layout, for example:

- `qgrav/pipeline_stages/interferometer.py`
- `qgrav/pipeline_stages/real_gravity.py`
- `qgrav/pipeline_stages/simulation.py`
- shared helpers in a support module

This is an architectural improvement rather than an urgent correctness bug, so it should be done in a dedicated refactor milestone with regression tests.

---

## 2026-06-11 - Lint/type enforcement decisions (CI hardening)

Context: adding an enforced ruff/black/mypy gate to CI revealed the
pre-commit hooks had only ever touched changed files, so most of the tree
had never been formatted. Decisions taken:

- **One-time mechanical reformat** of all non-vendor `src` + `tests` with
  black 24.10 (the pre-commit pin). Full suite identical before/after
  (379 passed, 2 skipped).
- **CI pins ruff==0.6.9 / black==24.10.0** to match
  `.pre-commit-config.yaml`, so local hooks and CI can never disagree;
  mypy pinned for stable stubs.
- **E741 globally ignored**: `I` (intensity), `l` are standard physics
  notation here; renaming numerics code is churn, not clarity.
- **`__init__.py` files ignore F401**: they re-export the public API that
  tests and the GUI import from package roots.
- **`gui/app.py`, `pipeline/_common.py`, `visuals.py` ignore E402**: they
  must set `MPLCONFIGDIR` / the matplotlib backend before importing
  `matplotlib.pyplot`.
- **`_tides_hw95.py` gets a B007 per-file-ignore** instead of an edit: the
  tide catalogue is regression-locked, so lint config bends rather than
  the file changing.
- **Scoped mypy overrides** (with `TODO(typing)`) for
  `qgrav.sim_ai.aisim_adapter` (`arg-type`: the YAML dispatcher builds
  `**kwargs` dicts mypy widens to `float | None`) and `qgrav.pipeline.*`
  (`arg-type`, `index`): fixing properly needs TypedDicts per study model.
  Everything else is mypy-clean (62 files).
- The ruff F401 autofix initially **removed the `qgrav info` aisim
  availability probe** (`import qgrav.vendor.aisim` inside `try`); restored
  with an explicit `# noqa: F401` and a comment. Watch for this pattern
  when running autofixes.
