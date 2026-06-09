# qgrav roadmap

A high-level view of where qgrav is and where it is headed. For the detailed,
version-by-version history see [CHANGELOG.md](../CHANGELOG.md).

## Current status

qgrav is a working, validated simulation and analysis platform:

- **Emergent-gravity simulation.** The Mach-Zehnder gravity phase is computed
  from a ballistic atom trajectory under a chirped Raman laser, not injected
  analytically, and every result carries an explicit study-scope label
  (fully simulated / hybrid / analytical only).
- **Realistic measurement cycle.** A multi-drop simulator with a per-shot noise
  budget (seismic vibration, detection noise, Raman-phase noise, AC Stark,
  wavefront aberrations) and a fringe-lock servo produces ASD and Allan-deviation
  curves like a real instrument.
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

- **Sub-pulse integration.** Step the finite-duration Raman pulses in
  sub-intervals to remove the residual pulse-timing calibration entirely, rather
  than predicting it from a closed form.
- **Four- and five-pulse sequences** for gradiometry and differential gravimetry.
- **Measured-wavefront input.** Drive the Zernike wavefront model from real
  wavefront-sensor coefficients.
- **Real interferometer output.** Ingest raw fringe / CSV output from an
  interferometer through the existing analysis pipeline, where such data is
  available.

## Longer-term vision

- **Atom-level projection noise.** A Monte-Carlo model over single-atom outcomes
  rather than mean populations.
- **Bayesian estimation of g** from the multi-drop time series with a full
  ensemble likelihood.
- **Hardware bench.** When a real apparatus is available, ingest live photodiode
  data through the same interface as the virtual bench and run a closure test:
  compare the measured Allan deviation against the qgrav prediction. This is the
  long-term goal, validating the simulation against a specific instrument.

## Contributing

Contributions are welcome. See [CONTRIBUTING.md](../CONTRIBUTING.md) for the
development setup, test commands, and the project's guiding principles.
