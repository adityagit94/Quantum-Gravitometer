# qgrav

**Software-first R&D platform for atom-interferometric gravimetry.**

qgrav simulates light-pulse atom-interferometer gravimeters from first
principles — the gravity phase emerges from a ballistic atom trajectory under a
chirped Raman laser, with finite-duration pulses integrated sub-pulse so the
finite-τ physics converges to the Bertoldi 2019 closed form. It models realistic
(and emergent Monte-Carlo) noise and systematics, runs multi-drop measurement
cycles, ingests real precision-gravity data through a complete tide → pressure →
polar-motion → ocean-loading residual chain, and validates itself against five
published instruments.

## Install

```bash
pip install qgrav
```

Run your first pipeline with `qgrav run --config configs/example.yaml`, or launch
the desktop GUI with `qgrav gui`. The [Complete guide](COMPLETE_GUIDE.md) covers
everything else.

## Start here

- **New to the project?** Read the [Complete guide](COMPLETE_GUIDE.md).
- **Want the physics?** See the [v1.0 physics upgrade](V1_PHYSICS_UPGRADE.md)
  and the [physics review packet](PHYSICS_REVIEW_PACKET.md).
- **Designing / extending?** See the [architecture](ARCHITECTURE.md) and the
  [roadmap](ROADMAP_V1_TO_V2.md).
- **Reproducibility & honesty:** every result carries a study-scope label; see
  [scientific hardening](SCIENTIFIC_HARDENING.md) and the
  [AI usage disclosure](AI_USAGE_DISCLOSURE.md).

## Validation at a glance

- **Primary regression:** Freier 2016 (GAIN), 96 nm/s²/√Hz.
- **Secondary:** Hu 2013, Ménoret 2018, Xu 2022, Wu 2019.
- **Independent cross-check:** QuTiP reproduces the Raman dynamics to ~1.6×10⁻⁶.
- **Emergent floors:** the finite-τ phase converges to the Bertoldi 2019 closed
  form (≤2×10⁻³ relative), and the multi-drop quantum-projection-noise floor
  matches σ_g = 1/(√N_det·k_eff·T²) to ~0.2 %.
- **Real data:** IGETS superconducting-gravimeter ingest for the analysis chain.

See the repository `README.md` and `CHANGELOG.md` for installation and the full
version history.
