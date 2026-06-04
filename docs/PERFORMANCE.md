# Performance (v1.2.3)

Representative timings for the qgrav AISim simulation hot paths. Numbers from
the benchmark harness (`tests/benchmark_aisim.py`, run with
`pip install .[benchmark] && pytest -m benchmark`).

## Reference machine

| | |
|---|---|
| Platform | Windows 11 (10.0.26200) |
| Python | 3.14.4 |
| NumPy | 2.4.4 |
| CPU | typical 2020s laptop |

## Representative timings

| Operation | Parameters | Time |
|-----------|------------|------|
| Single Mach–Zehnder sequence | 1000 atoms, 3-pulse | **~1.3 ms** |
| Gravity sweep (hybrid) | 1000 atoms, 61 points | **~0.09 s** |
| Gravity sweep (emergent) | 1000 atoms, 61 points (+ calibration scan) | **~0.20 s** |
| Multi-drop cycle (emergent) | 100 drops, 1000 atoms/drop | **~0.30 s** |

## Scaling notes

- **The MZ matrix operations are vectorised over atoms** (NumPy einsum on the
  block-diagonal propagator), so per-sequence time grows ~linearly with atom
  count and is dominated by the matrix multiplies, not Python overhead. Doubling
  the atom count roughly doubles the per-sequence time; the published-reference
  regressions run at N=4000 atoms in well under a second.
- **The gravity sweep / multi-drop time is dominated by the number of MZ
  sequences** (= number of gravity points or drops), each ~1–2 ms. The
  emergent-mode calibration scan adds one fixed ~73-sequence fringe scan
  (~0.1 s) per call, independent of the sweep/drop count.
- **No O(n²) hot paths.** The per-drop fresh-ensemble creation in the
  multi-drop cycle is O(n_drops · n_atoms) but is a small fraction of the
  per-drop MZ cost, so it does not dominate. A profiling pass (v1.2.3) found no
  bottleneck worth vectorising further.

## Regression guard

`tests/test_performance_guard.py` runs in the normal suite (no plugin needed)
and asserts a single MZ sequence completes under a generous 200 ms ceiling
(~150× the representative 1.3 ms), so an accidental algorithmic regression in
the hot path is caught by CI without being flaky on machine-speed variation.

## Practical guidance

- For interactive exploration: 200–500 atoms, 11–21 sweep points → sub-second.
- For published-reference accuracy (floor below the injected noise budget):
  N=4000 atoms (see `docs/research/` and the Freier regression docstring).
- The full fast test suite (`pytest -m "not slow"`) runs in ~30 s; the `@slow`
  published-reference regressions add ~20 s.
