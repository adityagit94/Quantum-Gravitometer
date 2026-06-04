---
title: 'qgrav: a software-first R&D platform for atom-interferometric gravimetry'
tags:
  - Python
  - atom interferometry
  - gravimetry
  - quantum sensing
  - metrology
authors:
  - name: Aditya Prakash
    affiliation: 1
affiliations:
  - name: Indian Institute of Technology Patna, India
    index: 1
date: 30 May 2026
bibliography: paper.bib
---

# Summary

`qgrav` is a software-first research-and-development platform for
atom-interferometric gravimetry. It connects a semiclassical atom-optics
simulator (a patched, vendored copy of AISim [@aisim]) to a configuration-driven
pipeline that runs simulations, ingests real precision-gravity time series,
computes standard sensitivity metrics (power spectral density, overlapping Allan
deviation, shot-noise sensitivity), and emits a reproducible, versioned run
folder with plots and an HTML report. Its distinguishing feature is that the
gravimetric phase **emerges** from a self-consistent numerical simulation — a
ballistic atom trajectory under a chirped Raman laser — rather than being
injected analytically as $k_\mathrm{eff}\,g\,T^2$. Every simulation result
carries an explicit *study-scope label* (`FULLY_SIMULATED` / `HYBRID` /
`ANALYTICAL_ONLY`) so users can tell at a glance what is computed from first
principles versus imposed by formula.

The platform validates itself against five published atom-gravimeter results —
Freier 2016 (GAIN) [@freier2016] as the primary regression target, plus Hu 2013
[@hu2013], Ménoret 2018 [@menoret2018], Xu 2022, and Wu 2019 — and
independently cross-validates its core quantum dynamics against QuTiP [@qutip].

# Statement of need

Light-pulse atom interferometers are now the most accurate absolute gravimeters,
but the simulation codes used to design and interpret them are almost universally
private to individual research groups. The leading experimental groups
(Stanford, Berkeley, SYRTE, Humboldt) publish papers but not companion
simulation pipelines, and the closest open package, AISim [@aisim], stops at the
atom-optics layer (Rabi dynamics, beam profiles, ensemble inhomogeneity) without
a gravimeter-level workflow, noise budget, or validation against published
instruments.

`qgrav` fills this gap. It provides (i) an emergent-gravity simulation in which
the interferometer phase arises from the propagation rather than a closed form,
(ii) a realistic noise model (Peterson NLNM/NHNM seismic vibration, technical
detection noise, Raman-phase noise, spontaneous emission, AC Stark, wavefront
aberrations), (iii) a multi-drop measurement-cycle simulator with a
fringe-locking servo and Allan-deviation output, and (iv) automated regressions
that reproduce published instrument sensitivities. The honest study-scope
labelling and an explicit physics-review packet make the platform's epistemic
status auditable — a deliberate response to the reproducibility expectations of
quantum-sensing R&D.

# Functionality

- **Emergent-gravity simulation.** A `GravityFreePropagator` advances atoms
  ballistically between Raman pulses; a chirped `Wavevectors` cancels the common
  gravity Doppler; the patched two-level propagator uses the time-integrated
  laser phase $-k_\mathrm{eff} z(t_0) + \tfrac12 \alpha t_0^2$ so the
  Mach–Zehnder combination yields $k_\mathrm{eff}(g-g_\mathrm{chirp})T^2$ from
  first principles. The finite-pulse-duration correction is reported in closed
  form (Bertoldi 2019 [@bertoldi2019]).
- **Noise & systematics.** NLNM/NHNM time-domain vibration with isolation
  filtering; detection (projection and technical) noise; Raman-phase noise;
  spontaneous-emission loss; position-dependent AC Stark; Zernike wavefront
  aberrations (whose Mach–Zehnder effect is the known curvature systematic,
  second-order in the inter-pulse drift).
- **Measurement cycle.** Multi-drop simulator with fresh ensembles per drop,
  correlated seismic noise, PID or integrator fringe-locking servo, and
  overlapping Allan deviation.
- **Validation.** Five published-reference regressions; an optional QuTiP
  backend that reproduces the Raman dynamics to $1.6\times10^{-6}$ via
  independent numerical integration; real superconducting-gravimeter data
  ingest (IGETS) for the analysis chain.
- **Pipeline.** Single-YAML configuration, versioned run folders, HTML reports,
  CI (Linux + Windows × Python 3.9–3.12), and a Docker image.

# AI-assistance disclosure

Substantial portions of `qgrav` were developed with AI assistance; all
physics-sensitive code, benchmark values, and citations were human-reviewed and
verified against primary sources. See `docs/AI_USAGE_DISCLOSURE.md` for a full
account, including the specific bugs the review process caught.

# Acknowledgements

`qgrav` vendors and extends AISim [@aisim] and AllanTools, and optionally uses
QuTiP [@qutip]. We thank the authors of those packages.

# References
