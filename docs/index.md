# qgrav

**Software-first R&D platform for atom-interferometric gravimetry.**

qgrav simulates light-pulse atom-interferometer gravimeters from first
principles (gravity phase emerges from a ballistic trajectory under a chirped
Raman laser), models realistic noise and systematics, runs multi-drop
measurement cycles, ingests real precision-gravity data, and validates itself
against five published instruments.

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
- **Real data:** IGETS superconducting-gravimeter ingest for the analysis chain.

See the repository `README.md` and `CHANGELOG.md` for installation and the full
version history.
