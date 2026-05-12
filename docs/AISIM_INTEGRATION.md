# AISim integration

The repository now includes a vendored `aisim` package and a wrapper module:
- `src/aisim/`
- `src/qgrav/sim_ai/aisim_adapter.py`

Current model:
- backend: `aisim`
- model: `rabi_scan`

It creates a random cold-atom ensemble, applies a spherical detector and free propagation, then drives a two-level Raman-like transition step-by-step and records the mean excited-state population as pulse duration increases.

It does **not yet** simulate the full gravimeter sequence with gravity sensitivity extraction.

## License

The vendored AISim code is derived from the upstream `aisim` package
(GPL-3.0). See `docs/THIRD_PARTY_LICENSES/AISim-LICENSE.txt` for details
and license status.
