# qgrav roadmap

A high-level view of where qgrav is and where it is headed. For the detailed,
version-by-version history see [CHANGELOG.md](../CHANGELOG.md).

## Current status

qgrav is a working, validated simulation and analysis platform:

- **Emergent-gravity simulation.** The Mach-Zehnder gravity phase is computed
  from a ballistic atom trajectory under a chirped Raman laser, not injected
  analytically, and every result carries an explicit study-scope label
  (fully simulated / hybrid / analytical only).
- **Sub-pulse finite-τ Raman integration** (v1.5, opt-in via
  `raman_substeps`). Finite-duration pulses are stepped in sub-intervals with
  ballistic free-fall between slices; the result converges to the
  Bertoldi 2019 closed form within 2×10⁻³ relative, so finite-pulse physics
  is computed rather than predicted.
- **Realistic measurement cycle.** A multi-drop simulator with a per-shot noise
  budget (seismic vibration, detection noise, Raman-phase noise, AC Stark,
  wavefront aberrations) and a fringe-lock servo (PID with anti-windup)
  produces ASD and Allan-deviation curves like a real instrument. Seismic
  vibration is drop-to-drop correlated: one continuous Peterson NLNM/NHNM
  series spans the campaign and every drop samples its three pulse times
  from it.
- **Emergent quantum projection noise** (v1.5). In multi-drop mode the
  shot-noise floor emerges from `Binomial(N_det, P)` single-atom statistics
  and matches the analytic `σ_g = 1/(√N_det·k_eff·T²)` to 0.2 %.
- **Emergent gravity-gradient physics.** `GravityFreePropagator` integrates
  a linear gradient to first order in γ, and the emergent Mach-Zehnder
  gradient phase reproduces the textbook
  `k_eff·γ·T²·[(z₀−z_ref) + v₀T − (7/12)gT²]` closed form
  (Peters/Chung/Chu 2001) to ~0.1 % — regression-locked in
  `tests/test_gravity_gradient_emergent.py`.
- **Time-domain mirror motion** (`vibration_model: "time_domain"`). The
  vibration sweep can drive the pulse sequence with a synthesized Peterson
  NLNM/NHNM displacement record instead of a sinusoidal amplitude axis; the
  realized per-shot phase noise reproduces the frequency-domain Cheinet
  budget `∫S_a·|H_a|²df` end-to-end (ratio 0.92–1.13 across seeds,
  truth-checked on every run).
- **Validation.** Automated regressions reproduce the short-term sensitivity of
  five published transportable gravimeters (Freier 2016 as the primary target,
  plus Hu 2013, Ménoret 2018, Xu 2022, and Wu 2019), and an independent QuTiP
  integration cross-checks the single-pulse Raman dynamics.
- **Real data.** Superconducting-gravimeter (IGETS) time series can be ingested
  through the analysis pipeline.
- **Tooling.** A six-tab desktop GUI, a single-YAML configuration schema,
  auto-generated HTML reports, continuous integration on Linux and Windows, and
  a documentation site.

## Near-term directions

- **Sub-pulse integration by default.** `raman_substeps` (v1.5) already
  computes finite-τ pulse physics numerically; the remaining step is making it
  the default and retiring the empirical pulse-timing calibration entirely.
- **Four- and five-pulse sequences** for gradiometry and differential gravimetry.
- **Measured-wavefront input.** Drive the Zernike wavefront model from real
  wavefront-sensor coefficients.
- **Real interferometer output.** Ingest raw fringe / CSV output from an
  interferometer through the existing analysis pipeline, where such data is
  available.

## Longer-term vision

- **Bayesian estimation of g** from the multi-drop time series with a full
  ensemble likelihood.
- **Hardware bench.** When a real apparatus is available, ingest live photodiode
  data through the same interface as the virtual bench and run a closure test:
  compare the measured Allan deviation against the qgrav prediction. This is the
  long-term goal, validating the simulation against a specific instrument.

## Contributing

Contributions are welcome. See [CONTRIBUTING.md](../CONTRIBUTING.md) for the
development setup, test commands, and the project's guiding principles.
