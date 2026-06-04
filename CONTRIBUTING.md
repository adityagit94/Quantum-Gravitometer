# Contributing to qgrav

Thanks for your interest in qgrav. This is a research codebase, so correctness
and honest scoping matter more than feature count.

## Development setup

```bash
git clone https://github.com/adityagit94/Quantum-Gravitometer
cd Quantum-Gravitometer
python -m pip install -e ".[test,qutip,benchmark]"
```

Use the **same** interpreter for `pip` and `python` — mixing them is the usual
cause of a "command not found" `qgrav` / `qgrav-gui` script.

## Running the tests

```bash
python -m pytest -q -m "not slow"   # fast suite (what CI runs)
python -m pytest -q -m slow         # published-reference regressions (slow)
python -m pytest -q -m benchmark    # performance micro-benchmarks
```

On headless machines set `MPLBACKEND=Agg`. The GUI tests skip automatically when
Tk has no display.

## Code style

`ruff` and `black`, line length 100 (configured in `pyproject.toml`):

```bash
ruff check . && black --check .
```

Use type hints where practical, and `from __future__ import annotations` in
modules that use `X | Y` syntax (the project supports Python 3.10+).

## Guiding principles

1. **Backward-compatible defaults** — new behaviour is opt-in behind a flag; no
   existing result silently changes except a deliberate, documented tolerance change.
2. **Honest tolerances and scope** — when a value lands outside an envelope,
   document the physical reason instead of tuning seeds until green. Every
   simulation result carries a study-scope label (fully simulated / hybrid /
   analytical only).
3. **Research-sourced** — physics parameters and claims trace to a paper or to `docs/`.
4. **One verification per change** — a green suite plus a `CHANGELOG.md` entry.

## Pull requests

1. Branch off `main`.
2. Add or update tests for the behaviour you change.
3. Keep the fast suite green; add a `CHANGELOG.md` entry under **Unreleased**.
4. Do **not** edit the vendored `src/qgrav/vendor/` tree in place — extend it via
   subclasses (see `src/qgrav/vendor/ATTRIBUTION.md`).

## Reporting bugs / requesting features

Use the GitHub issue templates. For security issues see [`SECURITY.md`](SECURITY.md).

## License

By contributing you agree that your contributions are licensed under the
project's `GPL-3.0-or-later`.
