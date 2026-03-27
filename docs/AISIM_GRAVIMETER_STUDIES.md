# AISim gravimeter studies

This document explains the three thesis/report-quality AISim studies added in this stage, what they mean scientifically, and what they do **not** claim.

## 1. Why these studies exist

The project now has three complementary lanes:

1. **Signal-processing lane**
   - virtual interferometer I/Q data
   - baseline vs improved estimators
   - PSD / Allan deviation / reports

2. **Real-data gravimetry lane**
   - superconducting gravimeter residual data
   - gap checks, PSD, Allan deviation, long-term drift/stability summaries

3. **AISim gravimeter-study lane**
   - atom-optics simulation studies that are closer to light-pulse gravimeter physics

This AISim stage moves the project from a generic atom-light demo toward a gravimeter-relevant software study.

---

## 2. The three studies in this stage

### 2.1 Mach–Zehnder phase scan

Config example:
- `configs/example_aisim_phase_scan.yaml`

Model name:
- `mach_zehnder_phase_scan`

What is simulated directly in AISim:
- a **three-pulse** sequence using `SpatialSuperpositionTransitionPropagator`
- first beam splitter pulse
- free evolution for time `T`
- mirror pulse
- free evolution for time `T`
- final beam splitter pulse with a configurable `phase_scan`

What is reported:
- output-port populations (`port 2`, `port 3`)
- differential signal
- fitted fringe visibility
- fitted phase offset
- a fit quality score (R²)

Why it matters:
- this is the closest study in the repo to a real light-pulse atom interferometer fringe measurement
- it shows whether the selected pulse/ensemble settings produce a usable interferometer signal

What it does **not** claim:
- it is still a compact study, not a full field gravimeter digital twin
- it does not include every systematic effect of a deployed absolute gravimeter

---

### 2.2 Gravity sweep

Config example:
- `configs/example_aisim_gravity_sweep.yaml`

Model name:
- `gravity_sweep`

What it does:
- keeps the AISim three-pulse sequence for pulse-transfer/contrast behavior
- maps gravity `g` to interferometer phase using the standard Mach–Zehnder scaling

In other words, this is a **hybrid study**:
- pulse sequence + imperfect populations: **AISim**
- gravity-induced phase law: **analytical gravimeter model**

Why this hybrid is used:
- it is honest and practical
- it gives a gravimeter-relevant sweep now, without pretending AISim alone already includes every deployed-gravimeter effect end-to-end in this repo

What is reported:
- gravity values
- total phase used for each gravity point
- output-port populations
- differential / normalized differential signal
- mid-fringe slope near the operating point

What it means:
- this shows how sensitive the simulated interferometer output is to small gravity changes

---

### 2.3 Vibration sensitivity sweep

Config example:
- `configs/example_aisim_vibration_sweep.yaml`

Model name:
- `vibration_sensitivity_sweep`

What it does:
- uses the same hybrid gravimeter idea
- adds a sinusoidal reference-mirror motion model
- converts that mirror motion into interferometer phase using the three-pulse discrete phase response

The phase model used is the standard pulse-time approximation:
- pulse times at `0`, `T`, `2T`
- vibration phase from the mirror positions at those pulse times

What is reported:
- vibration amplitude sweep
- induced vibration phase
- equivalent gravity error
- output-port populations and differential signal

Why it matters:
- vibration is one of the most important practical limitations in real atom gravimeters
- this gives you a software-only way to study vibration sensitivity before any hardware exists

What it does **not** claim:
- it is not a full seismic/isolation model
- it is a clean first-order sensitivity study

---

## 3. How to interpret the study types

### `full_aisim_three_pulse_sequence`
This means the three-pulse interferometer sequence itself is simulated directly with AISim.

### `hybrid_aisim_plus_analytic_gravity_phase`
This means:
- AISim handles the pulse-transfer / atom-optics part
- the gravity phase is imposed analytically using the standard Mach–Zehnder gravimeter scaling

### `hybrid_aisim_plus_analytic_vibration_phase`
This means:
- AISim handles the pulse-transfer / atom-optics part
- the vibration phase is imposed analytically from the mirror-motion phase response of a three-pulse interferometer

These labels are intentionally explicit so the report stays scientifically honest.

---

## 4. Recommended thesis/report wording

A safe and accurate way to describe this stage is:

> The project integrates AISim into a software-first gravimeter R&D platform and implements three gravimeter-relevant studies: a full three-pulse Mach–Zehnder phase scan in AISim, a hybrid gravity sweep combining AISim pulse-transfer effects with the standard light-pulse gravimeter phase law, and a hybrid vibration sensitivity sweep using the discrete three-pulse vibration phase response.

A shorter version is:

> The simulation layer now goes beyond Rabi oscillations and includes gravimeter-relevant phase, gravity, and vibration studies.

---

## 5. What should come next after this stage

The best next upgrades are:

1. add **run comparison** across the three AISim studies
2. add **frequency sweeps** for vibration sensitivity, not just amplitude sweeps
3. add **wavefront / beam-size / temperature sensitivity** sweeps using AISim inputs
4. compare synthetic stability summaries against the real gravimetry data lane

That is the path from a strong thesis-quality project toward a more publishable methodology study.
