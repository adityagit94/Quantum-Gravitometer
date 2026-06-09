# qgrav Roadmap - v1.0.0 → v2.0.0

**Document version:** 1.0 (initial draft, 2026-05-26)
**Author:** Aditya Prakash + AI working session
**Status:** Living document - edit as priorities change

---

## Table of contents

1. [Where we are](#1-where-we-are)
2. [Three guiding principles](#2-three-guiding-principles)
3. [Quick reference: who owns what](#3-quick-reference-who-owns-what)
4. [Phase 11 - Reference-registry bug fixes (URGENT)](#4-phase-11---reference-registry-bug-fixes-urgent)
5. [Phase 12 - Subclass refactor of vendor patches](#5-phase-12---subclass-refactor-of-vendor-patches)
6. [Phase 13 - Freier 2016 automated regression (PRIMARY)](#6-phase-13---freier-2016-automated-regression-primary)
7. [Phase 14 - Wire advanced AISim features through configs](#7-phase-14---wire-advanced-aisim-features-through-configs)
8. [Phase 15 - Multi-drop realism upgrades](#8-phase-15---multi-drop-realism-upgrades)
9. [Phase 16 - Hu 2013 and Ménoret 2018 benchmarks](#9-phase-16---hu-2013-and-mnoret-2018-benchmarks)
10. [Phase 17 - CI / CD / packaging infrastructure](#10-phase-17---ci---cd---packaging-infrastructure)
11. [Phase 18 - Eliminate the empirical calibration](#11-phase-18---eliminate-the-empirical-calibration)
12. [Phase 19 - Documentation completion](#12-phase-19---documentation-completion)
13. [Phase 20 - Release v1.1.0 (consolidation)](#13-phase-20---release-v110-consolidation)
14. [Beyond v1.1: v2.0 vision](#14-beyond-v11-v20-vision)
15. [What you need to do (and when)](#15-what-you-need-to-do-and-when)
16. [Cumulative test-count target](#16-cumulative-test-count-target)

---

## 1. Where we are

**Released:** qgrav **v1.0.0** (2026-05-26)

- 253 passing tests (192 baseline + 61 new from the v1.0 ten-phase upgrade)
- Full physics simulation upgrade: `GravityFreePropagator`, chirped `Wavevectors`, integrated-phase patch in `TwoLevelTransitionPropagator`, multi-drop measurement cycle with detection noise and servo, AC Stark, wavefront aberrations, Peterson NLNM/NHNM time-domain vibration noise
- Documentation: README, GUIDE, PROJECT_SPEC, ARCHITECTURE, SCIENTIFIC_HARDENING, AISIM_GRAVIMETER_STUDIES, AISIM_INTEGRATION, V1_PHYSICS_UPGRADE, PHYSICS_REVIEW_PACKET (with executable reviewer notebook), CHANGELOG
- Honest assessment of cons/caveats published

**Known issues identified in the honest-assessment session:**

| # | Issue | Severity |
|---|-------|----------|
| C1 | "Fully simulated" mode needs an empirical per-sweep calibration | High |
| C2 | Cross-validation tolerance atol=0.15 is generous | Medium |
| C3 | Wavefront tests barely demonstrate the effect | Medium |
| C4 | Patches are inside vendored AISim files, fragile to upstream updates | High |
| C5 | Multi-drop cycle has fully-independent drops (no realistic correlations) | High |
| C6 | Servo is I-only without anti-windup | Medium |
| C7 | AC Stark not exposed in YAML configs | Low (mechanical) |
| C8 | Time-domain vibration not wired into vibration sweep | Low (mechanical) |
| C9 | Multi-drop g_estimate inversion assumes visibility = 1 | Medium |
| C10 | Truth checks don't compare to published references | High |
| C11 | No CI / packaging / DockerHub | High |
| C13 | `docs/COMPLETE_GUIDE.md` is partially stale | Low |
| C14 | No independent physics review yet | **Highest** |
| C15 | Performance not characterised | Low |

**Plus the user-identified bug from the validation discussion:**

| # | Issue | Severity |
|---|-------|----------|
| C-bug-1 | `hu_2013_short_term_noise = 4.2e-9 m/s²/√Hz` should be `4.2e-8` (off by factor 10) | High |
| C-bug-2 | `menoret_2018_short_term_noise = 5e-7 m/s²/√Hz` should be `7.5e-7` (paper says 750 nm/s²/√Hz in the Larzac trace) | Medium |

This roadmap explains how each of these gets resolved across phases 11-20 leading to v2.0.

**Status update (2026-05-28):** v1.0.1 released (Phase 11 done - both reference bugs fixed, 276 tests pass). Internet research Topics 1-11 completed and stored in `docs/research/`. The findings materially change Phases 13, 16, and 18 - see §1.5 below.

**Status update (2026-05-29):** v1.0.2 released (Topic-13 audit: 3 unit errors + 2 ambiguous re-labelled, registry 12→14, 286 tests). All 14 research topics complete. **Phase 12 done** (vendor subclass refactor, 294 tests). **Execution-order revision (research-driven):** because GAIN's 96 nm/s²/√Hz is technically/vibration-limited, not projection-limited (F3), the benchmark phases need the noise machinery first. New order: **12 ✓ → 15 (noise realism) → 13 (Freier) → 16 (Hu/Ménoret/Xu/Wu) → 14 (YAML wiring) → 18 (calibration) → 17 (CI) → 19 (docs) → 20 (release).**

---

## 1.5. Research-driven updates (from `docs/research/`, Topics 1-11)

The internet research (9 + 2 files in `docs/research/`, summarised in `docs/research/FINDINGS_SUMMARY.md`) corrects several assumptions baked into the original roadmap. **These corrections must be applied when Phases 13, 16, and 18 are implemented.**

### 1.5.1 Physics claim VALIDATED (affects review packet, not code)

The Patch C "factor-of-2" claim is **independently confirmed** against Cheinet 2008, Kasevich & Chu 1991, Young/Kasevich/Chu 1997, and the Chu Nobel lecture (`RESEARCH_AISIM_PHYSICS.md`). The chirp enters via the integral `∫₀^{t₀} ω(t')dt' = ½αt₀²`, not `δ(t₀)·t₀ = αt₀²`. → Add this citation to `PHYSICS_REVIEW_PACKET.md` §4 before sending to a human reviewer.

### 1.5.2 Freier 2016 - corrected parameters (Phase 13)

Source: `RESEARCH_FREIER_2016.md` (Freier 2017 PhD thesis, doi:10.18452/17795, is the gold mine). The roadmap's earlier guesses were wrong on three counts:

| Parameter | Earlier guess | **Corrected** | Note |
|-----------|--------------:|--------------:|------|
| `tau_pi_half_s` | 23e-6 | **17e-6** (π/2; π = 34 µs) | Onsala 2015 campaign = the 2016 dataset |
| `single_photon_detuning_hz` | "few GHz" | **−700e6** (red of F′=1) | GAIN runs unusually close to resonance |
| `beam_radius_m` (1/e²) | 0.01475 | **0.015** (30 mm diameter) | - |
| T | 260e-3 | 260e-3 ✓ | Hauth 2013's 230 ms is a *different* config - do not mix |
| T_cycle | 1.5 | 1.5 ✓ | verbatim |
| cloud temp | 2 µK | 2 µK ✓ | but **selected σ_v = 5.2e-3 m/s** is the interferometer-relevant width |
| N_detected | - | **5e5** | NOT projection-limited; measured σ_P ≈ 6e-3 (≈4-6× above shot noise) |
| chirp rate | - | **25.14e6 Hz/s** (= k_eff·g/2π) | - |

**Critical modelling note:** GAIN is **technically-limited, not projection-limited**. Do not model the 96 nm/s²/√Hz from √N detection noise alone - add an explicit detection-technical-noise floor σ_P ≈ 6e-3 (≤ 30 nm/s² in g). Raman-phase-noise term ≈ 40 nm/s²/shot (Onsala-maser-comparable). The per-τ ADEV values (10/100/1000 s) are **NOT tabulated** in the paper - regress only against the two verbatim numbers (96 nm/s²/√Hz at 1 s, 0.5 nm/s² long-term) and the white-noise τ⁻¹/² slope; mark any intermediate values as *derived*.

A complete qgrav-ready `FREIER_2016` dict is given at the end of `RESEARCH_FREIER_2016.md` - copy it into `freier_2016_setup.py`.

### 1.5.3 Hu 2013 - MAJOR correction (Phase 16)

Source: `RESEARCH_HU_2013.md`. **The roadmap's "Wuhan 10 m drop tower" premise is wrong.** Hu et al. PRA 88, 043610 (2013) is a **HUST short atomic fountain** (T = 300 ms, apex 0.75 m above the MOT). The 10 m apparatus is a *different group* (M.-S. Zhan / WIPM-CAS) and a different paper.

Corrected Hu 2013 parameters:
- T = **300 ms** (not "0.6-1 s"); 2T = 600 ms
- N_MOT = **3e9**; N in interferometer = **5e7** (after state prep)
- Transverse cloud temp = **7 µK**; longitudinal selected = **300 nK**
- Launch velocity **3.83 m/s**; apex **0.75 m**
- Single-photon detuning |Δ| ≈ **1.5 GHz** (sign unconfirmed in open sources)
- **Contrast C ≈ 0.15** (low! - drives the detection-noise term)
- Target: **4.2 µGal/√Hz at 1 s** (= 4.2e-8 m/s²/√Hz), < 0.5 µGal at 100 s
- **No systematic-error budget exists in Hu 2013** (it's a noise-budget paper); τ_π and beam waist are paywalled/unverified

→ Phase 16's `hu_2013_setup.py` must use these. Mark τ_π and beam waist as TBD. Do NOT attempt a systematic-error-budget comparison for Hu 2013.

### 1.5.4 Ménoret 2018 - corrected parameters (Phase 16)

Source: `RESEARCH_MENORET_2018.md`. Corrections to the roadmap placeholder:
- T = **60 ms** (not 80 ms)
- τ_π/2 = **10 µs**, τ_π = **20 µs**
- n_atoms = **1e7**; cycle = **500 ms (2 Hz)** (not 1 s)
- Contrast C = **0.40**; detection SNR = 150; effective SNR = 60; single-shot floor ≈ **294 nm/s²**
- Vibration: **active feed-forward Raman-phase correction with a Nanometrics Titan accelerometer - NO mechanical isolation** (roadmap mis-described this as passive). Rejection factor > 60.
- Beam waist: **NOT stated in the paper** - leave as a free/TBD parameter
- Corrections applied before ADEV: tilt + microwave-quartz drift + pressure (admittance −3 nm/s²/hPa) + locally-trained synthetic tide
- The 750 nm/s²/√Hz (our v1.0.1 value) is the **Larzac campaign** value - one of five in the paper (best Larzac 500, campaign 750, Talence quiet 600, Talence typical 700, abstract 500). Correct for "field robustness".

### 1.5.5 Finite-τ correction is a CLOSED FORM - shortens Phase 18

Sources: `RESEARCH_FINITE_TAU.md` (Topic 9) and `RESEARCH_FINITE_TAU_FORMULAS.md` (Topic 14, code-ready equations).

**Bertoldi, Minardi & Prevedelli, PRA 99, 033619 (2019), Eq. 21** gives a closed-form multiplicative finite-τ scale-factor correction on the gravity phase:

> Φ → k_eff·(g − α/k_eff)·T²·[1 − ((2π−4)/π)·(τ/T)],  with (2π−4)/π ≈ **0.7268**
> (equivalently the bracket = 1 − 2τ/T + 4τ/(πT); agrees with Shao 2015)

**Equivalent form (Fang/Mielec et al., New J. Phys. 20, 023020 (2018), citing Cheinet's 2006 thesis):**

> S_rec = k_eff·(T + τ/2)·(T + (4/π − 3/2)·τ)

Both are leading-order-in-η (η = τ/T) equivalent. **Convention confirmed: T is pulse-CENTER to pulse-CENTER; free evolution between pulse edges is T − 2τ; time origin at the middle of the central π pulse** (Cheinet 2008, Le Gouët 2008, Fang 2018, Bertoldi 2019 all agree).

**⚠ Citation caveat (Topic 14):** the loose "`T_eff = T + (4/Ω)·tan(Ωτ/2)`" effective-time form I used in earlier notes is **NOT** found in Peters/Chung/Chu 2001 or Le Gouët 2008 - do not attribute it to them. Use the Bertoldi or Fang/Mielec closed forms above with their correct citations. For rectangular π/2 pulses the leading-order `T_eff = T + 4τ/π` is fine as a *derived* approximation but should be labelled as such.

**Also useful (Topic 14):** Bertoldi Eq. 32 gives a residual *single-shot* term δφ₂ = −4θ²(T)·sin(2φ₂) that **averages to zero over the velocity distribution** - i.e. for our ensemble simulation the velocity-averaged correction is exactly the multiplicative factor above, with no residual. This is reassuring for the calibration approach.

**Implication:** Phase 18 no longer needs the 8-16 hr sub-pulse-integration (Approach B) as the first move. Instead:
1. Approach A (pulse-center time, ~2 hr) - already planned
2. **Approach A2:** substitute the Bertoldi/Fang-Mielec closed form into the analytical comparison and the calibration so the residual offset is *predicted*, not just calibrated (~1 hr)

This likely brings the calibration residual below 0.1 rad **without** the expensive sub-pulse integration. Phase 18 estimate stays at **~3 hr**. No published simulator does sub-pulse integration, so our Approach B (if ever needed) would be novel - worth a JOSS mention.

### 1.5.6 Two NEW benchmark targets recommended (extends Phase 16)

Source: `RESEARCH_RECENT_BENCHMARKS.md`. Retain all three existing targets and **add two 2020+ targets** to broaden regime coverage:

| New target | Value | T | Regime | Citation |
|-----------|-------|---|--------|----------|
| **Xu 2022** (HUST-QG) | 24 µGal/√Hz = 2.4e-7 m/s²/√Hz; 3 µGal combined uncertainty | ~300 ms | transportable + **first full HUST systematic budget** | Metrologia 59, 055001 (2022) |
| **Wu 2019** (Berkeley mobile) | 37 µGal/√Hz = 3.7e-7 m/s²/√Hz; <2 µGal in ~30 min | ~130 ms | mobile/field | Sci. Adv. 5, eaax0800 (2019) |
| Stray 2022 (Birmingham, optional) | gradiometer | - | gradiometry | Nature 602, 590 (2022) |

→ Phase 16 grows from "+2 benchmarks" to "+4 (Hu, Ménoret, Xu, Wu)". Time estimate 5 hr → **~8 hr**. Xu 2022 is especially valuable because it has the only published HUST systematic-error budget (3 µGal combined uncertainty), enabling an *accuracy* (not just sensitivity) regression.

### 1.5.7 JOSS hard pre-review gates (affects Phases 17, 19, 20)

Source: `RESEARCH_JOSS_SUBMISSION.md`. JOSS now desk-rejects submissions lacking:
- ≥ 6 months public commit history
- CI with automated tests (→ **Phase 17 is now a JOSS blocker**)
- demonstrated research use reproducing a published result (→ **Phase 13 Freier regression satisfies this**)
- **AI Usage Disclosure** (NEW 2025 - must disclose the AI-assisted v1.0 plan/implementation)
- 750-1100 word paper

Closest JOSS precedents: GPUE (BEC solver, 10.21105/joss.01037) and RydIQule (Rydberg sensor, 10.21105/joss.08539). State-of-field tools to cite: PyLCP, AtomECS, ARC, QuTiP. → Add an AI-Usage-Disclosure task; Phase 19 must include it.

### 1.5.8 Hardware + reviewer-contact findings (no v1.1 code impact)

- `RESEARCH_REVIEWER_CONTACTS.md`: top contact is **Prof. Achim Peters** (achim.peters@physik.hu-berlin.de, HU Berlin) - GAIN group, directly relevant to Freier 2016. Bastian Leykauf (AISim upstream) is the natural second. → user populates `REVIEW_REQUEST_TEMPLATE.md` and sends.
- `RESEARCH_HARDWARE_VENDORS.md`: Exail AQG is the only fully-spec'd commercial atom gravimeter; no vendor publishes an API. v2.0 hardware bench will define its own schema. Signal-chain reference: Microchip 5125A / Microsemi TimePod 5330A / NI PXIe-4464.

### 1.5.9 Dissemination venues (Topic 12 - affects Phases 19/20)

Source: `RESEARCH_VENUES.md`. Most 2026 deadlines have **passed** (ICAP 2026 Wuhan, EFTF 2026, IFCS 2026, SciPy 2026, EuroSciPy 2026). Realistic forward targets:

| Venue | When | Type | Note |
|-------|------|------|------|
| **JOSS** | rolling | software paper | first home; but see hard gates below |
| **Computer Physics Communications** (QuTiP's venue) or **SoftwareX** (Pykat's venue) | rolling | substantial methods+software paper | for a fuller paper than JOSS |
| YAO 2026 | Crete, ~Jun 7-12 2026 | student/early-career AMO | most accessible community meeting still open |
| SciPy 2027 | ~Jul 2027 | software visibility | next clean CFP after the passed 2026 one |
| NCAMP (India) | ~2027 | domestic AMO | ISAMP biennial; good home venue |
| GRC Atomic Physics / ICOLS 27 | ~2027 | domain | not yet announced |

**JOSS hard gates (reconfirmed, Topic 12):** auto-flag < 1000 LOC, **desk-reject < 300 LOC** (qgrav is far above this - fine); **≥ 6 months public open-development history** before submission; AI-usage disclosure. Safe-to-cite example software papers: Universal atom-interferometer simulator (Sci. Rep., 10.1038/s41598-020-78859-1), QuTiP (CPC, 10.1016/j.cpc.2012.02.021), atom-gravimeter key comparison (Metrologia, 10.1088/0026-1394/49/6/666). → The 6-month-public-history clock means **start the public GitHub commit history now** (user action); JOSS submission realistically lands ~6 months after the repo goes public with CI.

---

## 2. Three guiding principles

1. **Honesty over polish.** Whenever the simulation deviates from the analytical formula or a published value, document the deviation in the test message, in the truth-check output, and in the HTML report.
2. **The packet is the deliverable.** Every claim we make about the simulation's physical correctness should be traceable to a question answered in `docs/PHYSICS_REVIEW_PACKET.md`. Until a real physics reviewer answers those questions, we cannot upgrade `FULLY_SIMULATED` to "validated."
3. **Freier 2016 is the primary regression target.** Per your input, this is the closest paper to what we're trying to simulate operationally (mobile gravimeter, both short-term noise and long-term stability reported in the same paper). Every release after v1.0 must continue to pass the Freier 2016 regression test.

---

## 3. Quick reference: who owns what

**Times revised after the Topics 1-11 research (see §1.5).**

| Phase | What | Who | Estimated time | Blocker for next phase? |
|-------|------|-----|----------------|--------------------------|
| 11 | Reference-registry bug fixes | Me | ~~1 hr~~ ✅ DONE (v1.0.1) | - |
| 12 | Subclass refactor of vendor patches | Me | 3 hr | No (parallel) |
| 13 | **Freier 2016 automated regression** (corrected params §1.5.2) | Me | 5 hr | No (deliverable) |
| 14 | Wire AC Stark / wavefront / time-domain vib through YAML | Me | 3 hr | No (parallel) |
| 15 | Multi-drop realism (PID + correlated noise + V-fit) | Me | 6 hr | Yes - Phase 16 depends |
| 16 | Hu + Ménoret + **Xu 2022 + Wu 2019** benchmarks (§1.5.3/4/6) | Me | ~~5 hr~~ **8 hr** | No (deliverable) |
| 17 | CI / PyPI / Dockerfile (**JOSS blocker** §1.5.7) | Me + you (secrets) | 4 hr + your time | No (parallel) |
| 18 | Eliminate empirical calibration (**Bertoldi closed form** §1.5.5) | Me | ~~8-16 hr~~ **3 hr** | No (research) |
| 19 | Documentation completion + AI-usage disclosure | Me | 4 hr | No |
| 20 | Release v1.1.0 | Me + you | 2 hr | Yes |
| ext | Independent physics review | **You + reviewer** | weeks | No (parallel) |

**Phases 11, 13, 14, 17 can run in parallel** - they touch different files. **Phase 12 should land before 14** (because 14 will add YAML-config plumbing that we'd rather only do once).

**Total my-side work: ~40-48 hours** spread across multiple sessions.

---

## 4. Phase 11 - Reference-registry bug fixes (URGENT)

### Goal
Fix the two incorrect short-term-noise values you identified, before anyone uses them as benchmark targets.

### Tasks

#### 11.1 Fix Hu 2013 short-term noise

Change `value=4.2e-9` to `value=4.2e-8` in `published_references.py` at line ~125. Update the description and the source citation note so anyone reading the table sees the unit conversion explicitly:

```python
"hu_2013_short_term_noise": PublishedReference(
    key="hu_2013_short_term_noise",
    description="Wuhan 10 m AI gravimeter short-term noise (Hu 2013): 4.2 µGal/√Hz",
    value=4.2e-8,                       # FIXED: was 4.2e-9 in v1.0.0
    unit="m/s^2/sqrt(Hz)",              # 1 µGal/√Hz = 1e-8 m/s²/√Hz
    source="Hu et al., Phys. Rev. A 88, 043610 (2013), §III",
    year=2013,
    tolerance_pct=50.0,
    doi="10.1103/PhysRevA.88.043610",
),
```

#### 11.2 Fix Ménoret 2018 short-term noise

Change `value=5e-7` to `value=7.5e-7`:

```python
"menoret_2018_short_term_noise": PublishedReference(
    key="menoret_2018_short_term_noise",
    description="AQG-A01 Larzac short-term noise (Menoret 2018): 750 nm/s²/√Hz",
    value=7.5e-7,                       # FIXED: was 5e-7 in v1.0.0
    unit="m/s^2/sqrt(Hz)",
    source="Menoret et al., Sci. Rep. 8, 12300 (2018), Allan-deviation figure",
    year=2018,
    tolerance_pct=50.0,
    doi="10.1038/s41598-018-30608-1",
),
```

#### 11.3 Add a deprecation shim that emits a warning

```python
# In the deprecation-shim table at the bottom of published_references.py:
"hu_2013_short_term_noise_v1_0_value": (
    "hu_2013_short_term_noise",
    "qgrav v1.0.0 reported this value as 4.2e-9; the correct value is "
    "4.2e-8 (4.2 µGal/√Hz = 4.2×10⁻⁸ m/s²/√Hz). Anyone using the v1.0 "
    "value should re-evaluate downstream metrics."
),
```

#### 11.4 Add a regression test

`tests/test_published_references_values.py` (new):

```python
def test_hu_2013_short_term_noise():
    """Hu 2013 short-term noise = 4.2 µGal/√Hz = 4.2e-8 m/s²/√Hz."""
    from qgrav.validation.published_references import REFERENCES
    ref = REFERENCES["hu_2013_short_term_noise"]
    assert ref.value == 4.2e-8, (
        f"Hu 2013 short-term noise is the lab best-case sensitivity reference. "
        f"The published value is 4.2 µGal/√Hz = 4.2e-8 m/s²/√Hz (NOT 4.2e-9). "
        f"See Phys. Rev. A 88, 043610 (2013) §III."
    )
    assert ref.unit == "m/s^2/sqrt(Hz)"
    assert ref.year == 2013

def test_menoret_2018_short_term_noise():
    """Ménoret 2018 AQG-A01 Larzac trace = 750 nm/s²/√Hz."""
    from qgrav.validation.published_references import REFERENCES
    ref = REFERENCES["menoret_2018_short_term_noise"]
    assert ref.value == 7.5e-7, (
        f"Ménoret 2018 AQG-A01 Larzac short-term noise is 750 nm/s²/√Hz "
        f"= 7.5e-7 m/s²/√Hz (NOT 5e-7). See Sci. Rep. 8, 12300 (2018) Fig. 4."
    )

def test_freier_2016_short_term_noise():
    """Freier 2016 GAIN short-term noise = 96 nm/s²/√Hz = 9.6e-8 m/s²/√Hz."""
    from qgrav.validation.published_references import REFERENCES
    ref = REFERENCES["freier_2016_short_term_noise"]
    assert ref.value == 9.6e-8

def test_freier_2016_long_term_stability():
    """Freier 2016 GAIN long-term stability = 0.5 nm/s² = 5e-10 m/s²."""
    from qgrav.validation.published_references import REFERENCES
    ref = REFERENCES["freier_2016_long_term_stability"]
    assert ref.value == 5e-10
```

#### 11.5 Audit other reference values

Cross-check all 12 entries against their cited DOIs while we're here. Document any other off-by-factors.

### Owner: me
### Time: 1 hour
### Success criteria
- Two values fixed
- 4 new regression tests added
- CHANGELOG entry: `"v1.0.1: Reference-registry bug fix release. Hu 2013 and Ménoret 2018 short-term noise values corrected."`

### Resolves: C-bug-1, C-bug-2

---

## 5. Phase 12 - Subclass refactor of vendor patches

### Goal
Remove the v1.0 patches from inside the vendored AISim files. Move them into a clean `qgrav/sim_ai/_aisim_overrides.py` module that subclasses or wraps the upstream classes. Restore `vendor/aisim/*.py` to upstream-clean.

### Why this matters
The current state of `vendor/aisim/prop.py` and `vendor/aisim/beam.py` is *modified* upstream code. If we ever re-vendor a newer AISim release, we'll have to re-apply three non-trivial patches manually. The subclass approach makes the vendored code byte-identical to upstream.

### Tasks

#### 12.1 Create `qgrav/sim_ai/_aisim_overrides.py`

Contains:

```python
"""Local overrides for vendored AISim physics.

This module subclasses the upstream AISim classes and patches in:
1. GravityFreePropagator (new propagator for ballistic motion under gravity)
2. ChirpedWavevectors (extends Wavevectors with chirp_rate)
3. IntegratedPhaseTwoLevelTransitionPropagator
   (replaces δ·t₀ phase factor with the time-integrated -k_eff·z + ½·α·t² formula)
4. IntegratedPhaseSpatialSuperpositionTransitionPropagator (same, for multi-momentum-state)

By keeping these in qgrav/sim_ai/ rather than vendor/aisim/, the vendored
upstream files remain byte-identical to a clean AISim install. The trade-off
is one extra import indirection in aisim_adapter.py.

See docs/PHYSICS_REVIEW_PACKET.md for the physics rationale.
"""
import copy
import numpy as np
from qgrav.vendor.aisim.prop import (
    Propagator, FreePropagator, TwoLevelTransitionPropagator,
    SpatialSuperpositionTransitionPropagator as _UpstreamSpatial,
)
from qgrav.vendor.aisim.beam import Wavevectors as _UpstreamWavevectors


class GravityFreePropagator(Propagator):
    """[LOCAL OVERRIDE] Ballistic free propagation under uniform gravity."""
    # ... (same body as the current vendor/aisim/prop.py code)


class ChirpedWavevectors(_UpstreamWavevectors):
    """[LOCAL OVERRIDE] Wavevectors with chirp_rate_rad_per_s2."""
    def __init__(self, k1=8055366, k2=-8055366, chirp_rate_rad_per_s2=0.0):
        super().__init__(k1=k1, k2=k2)
        self.chirp_rate_rad_per_s2 = float(chirp_rate_rad_per_s2)

    def doppler_shift(self, atoms):
        base = super().doppler_shift(atoms)
        if self.chirp_rate_rad_per_s2 != 0.0:
            return base + self.chirp_rate_rad_per_s2 * atoms.time
        return base


class IntegratedPhaseTwoLevelTransitionPropagator(TwoLevelTransitionPropagator):
    """[LOCAL OVERRIDE] Replaces delta*t0 with integrated -k_eff*z + ½α·t²."""
    def __init__(self, time_delta, intensity_profile, wave_vectors=None,
                 wf=None, phase_scan=0, single_photon_detuning_hz=0.0):
        super().__init__(time_delta, intensity_profile=intensity_profile,
                         wave_vectors=wave_vectors, wf=wf, phase_scan=phase_scan)
        self.single_photon_detuning_hz = float(single_photon_detuning_hz)

    def _prop_matrix(self, atoms):
        # Override the imprint phase + add AC Stark correction.
        # (Full code in the current vendor/aisim/prop.py patch, adapted to
        # not modify the base class.)
        ...


class IntegratedPhaseSpatialSuperposition(_UpstreamSpatial):
    """[LOCAL OVERRIDE] SpatialSuperposition that uses the integrated-phase 2-level base."""
    # Replace the _prop_matrix base call to route through
    # IntegratedPhaseTwoLevelTransitionPropagator instead of upstream.
```

#### 12.2 Restore upstream-clean `vendor/aisim/prop.py` and `vendor/aisim/beam.py`

Revert the v1.0 patches in these files. The vendored code becomes byte-identical to a clean `pip install aisim`.

#### 12.3 Update `aisim_adapter.py`

Change every import of `GravityFreePropagator`, `SpatialSuperpositionTransitionPropagator`, `Wavevectors` to use the overrides:

```python
from qgrav.sim_ai._aisim_overrides import (
    GravityFreePropagator,
    ChirpedWavevectors as Wavevectors,
    IntegratedPhaseSpatialSuperposition as SpatialSuperpositionTransitionPropagator,
)
```

#### 12.4 Update `vendor/aisim/__init__.py`

Remove the local `GravityFreePropagator` export. Re-export it through `qgrav.sim_ai` instead.

#### 12.5 Add a smoke test

`tests/test_vendor_aisim_unmodified.py`:

```python
def test_vendor_prop_matches_upstream_signature():
    """Vendored prop.py must NOT contain '[LOCAL PATCH]' markers after Phase 12."""
    from pathlib import Path
    text = (Path(__file__).parent.parent
            / "src/qgrav/vendor/aisim/prop.py").read_text()
    assert "[LOCAL PATCH]" not in text, (
        "Vendor file contains local patches. Move them to "
        "qgrav/sim_ai/_aisim_overrides.py per Phase 12 of ROADMAP."
    )
```

### Owner: me
### Time: 3 hours
### Success criteria
- All 253 v1.0 tests still pass
- The 5 v1.0 vendor patches (`[LOCAL PATCH]` comments) all gone from `vendor/aisim/*`
- New tests confirm vendored code is unmodified
- `aisim_adapter.py` imports from `_aisim_overrides` everywhere

### Resolves: C4

---

## 6. Phase 13 - Freier 2016 automated regression (PRIMARY)

### Goal
A test that says: **"a simulated gravimeter with Freier 2016 parameters reproduces Freier's published short-term noise (96 nm/s²/√Hz) and long-term stability (0.5 nm/s²) within factor 2."** This is the **primary regression target** for the project per your input.

### Why Freier 2016 first
- Mobile Rb-87 gravimeter - closest architecture to what AISim models
- Both short-term and long-term metrics published in the same paper
- Standardized parameters (n_atoms, T, beam radius, etc.) inferable from the paper
- Cited as the operational benchmark in nearly every subsequent gravimeter paper

### Tasks

#### 13.1 Curate Freier 2016 simulation parameters

`src/qgrav/validation/freier_2016_setup.py` (new):

```python
"""Simulation parameters that approximately match the Freier 2016 GAIN setup.

Reference: Freier, C. et al. "Mobile quantum gravity sensor with unprecedented
stability." J. Phys.: Conf. Ser. 723, 012050 (2016).
DOI: 10.1088/1742-6596/723/1/012050

Reported metrics:
  • Short-term noise:    96 nm/s²/√Hz  (Allan deviation at τ=1 s)
  • Long-term stability: 0.5 nm/s²      (Allan deviation at τ ~ 1000 s)
  • Cycle time:           1.5 s
  • Interferometer time T: 260 ms
  • Atomic species: Rb-87
  • Source temperature: ~2 µK
"""
FREIER_2016_PARAMS = {
    "n_atoms":             10_000,
    "n_detected_per_drop": 5_000,   # ~50% detection efficiency typical
    "cloud_radius_m":      3.0e-3,
    "temp_xy_K":           2.0e-6,
    "temp_z_K":            2.0e-6,  # Freier 2016 uses 2D-MOT-cooled atoms
    "tau_pi_half_s":       23e-6,
    "interferometer_time_s": 260e-3,
    "cycle_time_s":        1.5,
    "beam_radius_m":       29.5e-3 / 2.0,
    "center_rabi_freq_hz": 12.5e3,
    "gravity_true_m_s2":   9.81,
    "gravity_propagation": True,
    "detection_noise_enabled": True,
    "servo_enabled":       True,
    "servo_gain":          0.5,
}

FREIER_2016_TARGETS = {
    # Allan-deviation comparison targets.
    # We allow a factor of 2 either way (typical for simulation-vs-experiment).
    "short_term_at_1s_m_s2_per_sqrt_hz":  9.6e-8,    # 96 nm/s²/√Hz
    "tolerance_factor":                    2.0,
    "long_term_at_1000s_m_s2":             5.0e-10,  # 0.5 nm/s²
    "long_term_tolerance_factor":          5.0,      # long-term is harder
}
```

#### 13.2 Add a long-multi-drop simulation

`run_aisim_multi_drop_cycle` needs to handle ~2000 drops (50 minutes of simulated time) to get a meaningful Allan deviation at τ ~ 1000 s. Performance budget: ~5 minutes wall-clock for the full Freier benchmark.

Likely improvements needed first:
- Vectorise the per-drop ensemble creation (currently O(n_drops · n_atoms))
- Cache the calibration result once per run

#### 13.3 Wire correlated noise

Phase 15 will deliver `drop_to_drop_correlation_model`. Until then, Freier 2016 will run with independent drops (white-noise floor only), and the test will only check short-term noise. The long-term test runs after Phase 15.

#### 13.4 Truth check: Freier 2016 short-term

`tests/test_published_validation_freier_2016.py` (new):

```python
import numpy as np
import pytest
from qgrav.sim_ai.aisim_adapter import run_aisim_multi_drop_cycle
from qgrav.validation.freier_2016_setup import FREIER_2016_PARAMS, FREIER_2016_TARGETS

@pytest.mark.slow
def test_freier_2016_short_term_noise():
    """A Freier-2016-like multi-drop simulation should reproduce the
    published 96 nm/s²/√Hz short-term noise within factor 2.

    Reference: Freier et al., J. Phys.: Conf. Ser. 723, 012050 (2016).
    """
    result = run_aisim_multi_drop_cycle(
        n_drops=200,          # ~5 min of simulated time; enough for τ=1 s ADEV
        seed=42,
        **FREIER_2016_PARAMS,
    )
    taus = result["allan_taus_s"]
    adev = result["allan_dev_m_s2"]

    # Find ADEV closest to τ = cycle_time_s (= 1.5 s, the shortest tau we sample)
    target_tau = FREIER_2016_PARAMS["cycle_time_s"]
    idx = int(np.argmin(np.abs(taus - target_tau)))
    measured = adev[idx]
    target  = FREIER_2016_TARGETS["short_term_at_1s_m_s2_per_sqrt_hz"]
    # Convert measured ADEV (m/s²) to noise spectral density (m/s²/√Hz):
    #   noise = ADEV · √(2 · τ)   (for white-noise, Riley 2008)
    measured_psd_sqrt = measured * np.sqrt(2.0 * taus[idx])
    factor = measured_psd_sqrt / target

    tol = FREIER_2016_TARGETS["tolerance_factor"]
    assert 1.0 / tol < factor < tol, (
        f"Simulated short-term noise = {measured_psd_sqrt:.2e} m/s²/√Hz; "
        f"Freier 2016 target = {target:.2e}. Factor = {factor:.2f}, "
        f"tolerance = ±{tol}×."
    )

@pytest.mark.slow
@pytest.mark.skip(reason="Requires correlated-noise model from Phase 15")
def test_freier_2016_long_term_stability():
    """Allan deviation at τ ~ 1000 s should reach 0.5 nm/s² within factor 5."""
    ...
```

#### 13.5 Wire into HTML report

When a `multi_drop_cycle` config matches Freier 2016 parameters within ~5%, the report should automatically render a "Freier 2016 comparison" panel showing measured vs published values.

### Owner: me
### Time: 5 hours
### Success criteria
- `test_freier_2016_short_term_noise` passes with `gravity_propagation=True`
- HTML report shows comparison panel
- New entry in `CHANGELOG`: `"v1.1.0: Freier 2016 primary regression added"`

### Resolves: partial C10 (short-term; long-term waits for Phase 15)

### Dependency
Phase 11 must land first (the corrected reference values).

---

## 7. Phase 14 - Wire advanced AISim features through configs

### Goal
Make AC Stark, wavefront aberrations, and time-domain vibration noise accessible from YAML configs (currently they only work via direct Python calls).

### Tasks

#### 14.1 AC Stark
- Add `single_photon_detuning_hz` to the config schema
- Pass through `run_aisim_gravity_sweep`, `run_aisim_vibration_sensitivity_sweep`, `run_aisim_multi_drop_cycle`
- Update `_run_mach_zehnder_sequence` and `_run_mach_zehnder_sequence_with_gravity` to forward it to the AISim propagator constructors
- Test: a `gravity_sweep` config with `single_photon_detuning_hz: 1e6` produces a fringe shift compared to the same config with `0.0`

#### 14.2 Wavefront aberrations
- Add `wavefront_zernike_coeffs: dict[int, float]` and `wavefront_radius_m: float` to the config schema
- Build the `Wavefront` via `_build_wavefront` and pass to the MZ sequences
- Sanity check: `wavefront_radius_m` must be > 1.5 × (cloud radius + thermal drift), else log a warning at config-validation time

#### 14.3 Time-domain vibration
- Add `vibration_model: "time_domain"` switch to `run_aisim_vibration_sensitivity_sweep`
- When `time_domain`: generate `generate_vibration_timeseries(...)` once, sample displacement at `t=0, T, 2T` per atom, compute `φ_vib = k_eff · [z(0) − 2z(T) + z(2T)]`
- Config keys: `vibration_seismic_model: "nlnm"|"nhnm"`, `vibration_isolation_cutoff_hz: float`, `vibration_seed: int`

#### 14.4 Tests
- 3 new tests verifying each YAML path produces measurably different output from the baseline
- 1 new test verifying that the warning fires for too-small `wavefront_radius_m`

### Owner: me
### Time: 3 hours
### Success criteria
- All three features usable from YAML
- All v1.0 + 4 new tests pass
- Documentation: update `docs/AISIM_GRAVIMETER_STUDIES.md` to mention the new YAML keys

### Resolves: C7, C8

---

## 8. Phase 15 - Multi-drop realism upgrades

### Goal
Make the multi-drop cycle behave more like a real instrument, so the Allan deviation actually exhibits the white → flicker → random-walk structure that lets Phase 13 verify long-term stability.

### Tasks

#### 15.1 PID servo with anti-windup

`physics/readout_models.servo_pid_step`:

```python
class PIDServoState:
    integral: float
    last_error: float

def servo_pid_step(*, population, servo_state: PIDServoState,
                   setpoint=0.5, kp=0.5, ki=0.1, kd=0.0,
                   integrator_clamp=10.0, ...) -> tuple[float, PIDServoState]:
    error = population - setpoint
    new_integral = servo_state.integral + error
    # Anti-windup: clamp integral
    new_integral = max(-integrator_clamp, min(integrator_clamp, new_integral))
    derivative = error - servo_state.last_error
    correction = kp * error + ki * new_integral + kd * derivative
    return -correction, PIDServoState(new_integral, error)
```

Keep the I-only `servo_integrator_step` as a default for backward compat.

#### 15.2 Drop-to-drop correlated noise

Generate a long acceleration trace at `multi_drop_cycle` startup, sample it at the drop cadence:

```python
seismic_trace = generate_vibration_timeseries(
    duration_s = n_drops * cycle_time_s,
    sample_rate_hz = max(2 * frequency_band_max_hz, 10.0),
    seismic_model="nlnm",
    isolation_cutoff_hz=isolation_cutoff_hz,
    seed=seed + 99_000,
)
# At each drop i, sample displacement at t=0, T, 2T relative to drop_i_start
# and apply φ_vib = k_eff·[z(0) - 2z(T) + z(2T)] as an additive phase.
```

New config keys: `correlated_noise: bool`, `seismic_model: "nlnm"|"nhnm"`, `isolation_cutoff_hz`.

#### 15.3 Visibility fitting

During `_calibrate_gravity_phase_offset`, also extract the fringe amplitude from `_fit_sinusoid`:

```python
fit = _fit_sinusoid(phis, p3_values)
sim_phase_offset = -fit["phase_offset_rad"] mod 2π
sim_visibility = 2 * fit["amplitude"]    # peak-to-peak P3 range
```

Use this `sim_visibility` in the multi-drop mid-fringe inversion:

```python
fringe_slope_per_m_s2 = -0.5 * sim_visibility * k_eff * T**2
```

#### 15.4 Tests
- `test_pid_servo_anti_windup`: large step error doesn't blow up the integral
- `test_correlated_noise_produces_random_walk_allan`: with `correlated_noise=True` and NLNM, the Allan deviation at long τ rises (1/f or random-walk regime)
- `test_visibility_estimate_matches_empirical_fringe`: fit visibility within 5% of the manual fringe-scan visibility

### Owner: me
### Time: 6 hours
### Success criteria
- 3 new tests pass
- Phase 13's `test_freier_2016_long_term_stability` no longer needs `@pytest.mark.skip`
- A 200-drop run with correlated noise shows an Allan-deviation shape that's visibly different from pure white noise

### Resolves: C5, C6, C9

### Dependency
None (independent of Phases 11-14).

---

## 9. Phase 16 - Hu 2013 and Ménoret 2018 benchmarks

### Goal
Two more automated regression tests using the lab-best-case (Hu 2013) and the transportable real-world (Ménoret 2018) targets.

### Tasks

#### 16.1 Hu 2013 setup

`src/qgrav/validation/hu_2013_setup.py`:

```python
"""Hu 2013 - Wuhan 10 m drop tower atom-interferometer gravimeter.

Reference: Hu, Z.-K. et al. "Demonstration of an ultrahigh-sensitivity
atom-interferometry absolute gravimeter." Phys. Rev. A 88, 043610 (2013).

Reported metrics:
  • Short-term noise: 4.2 µGal/√Hz = 4.2e-8 m/s²/√Hz
  • T:               300 ms  (longer than Freier 2016)
  • n_atoms:         ~10⁶ atoms (higher than typical mobile)
"""
HU_2013_PARAMS = {
    "n_atoms":             100_000,    # representative cold-atom flux
    "n_detected_per_drop": 50_000,
    "interferometer_time_s": 300e-3,
    "tau_pi_half_s":       12e-6,      # tighter, higher Rabi freq
    "center_rabi_freq_hz": 21e3,
    "cycle_time_s":        2.0,
    # ... other Rb-87 D2 standard params ...
}

HU_2013_TARGETS = {
    "short_term_at_1s_m_s2_per_sqrt_hz": 4.2e-8,
    "tolerance_factor":                  2.0,
}
```

#### 16.2 Ménoret 2018 setup

`src/qgrav/validation/menoret_2018_setup.py`:

```python
"""Ménoret 2018 - Muquans AQG-A01 transportable absolute gravimeter (Larzac).

Reference: Ménoret, V. et al. "Gravity measurements below 10⁻⁹ g with a
transportable absolute quantum gravimeter." Sci. Rep. 8, 12300 (2018).

Reported metrics:
  • Short-term noise:    750 nm/s²/√Hz  (Larzac trace, Fig. 4)
  • Long-term stability: < 10 nm/s²     (1 µGal, abstract)
  • Cycle time:          ~1 s
"""
MENORET_2018_PARAMS = {
    "n_atoms":             10_000,
    "n_detected_per_drop": 5_000,
    "interferometer_time_s": 80e-3,    # shorter T for transportable robustness
    "cycle_time_s":        1.0,
    # ... worse isolation: isolation_cutoff_hz=0.0 (no passive isolation) ...
    "isolation_cutoff_hz": 0.0,
    "correlated_noise":    True,
    # ... etc. ...
}

MENORET_2018_TARGETS = {
    "short_term_at_1s_m_s2_per_sqrt_hz": 7.5e-7,
    "tolerance_factor":                  2.0,
    "long_term_at_1000s_m_s2":           1e-8,
    "long_term_tolerance_factor":        3.0,
}
```

#### 16.3 Tests

Two new test files following the same pattern as `test_published_validation_freier_2016.py`. Mark with `@pytest.mark.slow` so they don't run on every commit but do run nightly.

#### 16.4 Combined dashboard

Add a `qgrav validate-against-published` CLI command that runs all three benchmarks and emits a Markdown summary table:

```
$ qgrav validate-against-published
Running Freier 2016 short-term...         [PASS] 9.4e-8 (target 9.6e-8, factor 0.98)
Running Hu 2013 short-term...             [PASS] 4.0e-8 (target 4.2e-8, factor 0.95)
Running Ménoret 2018 short-term...        [PASS] 6.8e-7 (target 7.5e-7, factor 0.91)
Running Freier 2016 long-term stability... [PASS] 0.6 nm/s² (target 0.5, factor 1.2)
Running Ménoret 2018 long-term...         [PASS] 12 nm/s² (target 10, factor 1.2)

All 5 benchmarks pass.
```

### Owner: me
### Time: 5 hours
### Success criteria
- 5 published-reference regressions pass on `gravity_propagation=True`
- The CLI dashboard works
- The HTML report shows comparison panels for all three references when applicable

### Resolves: rest of C10

### Dependency
Phases 11 (correct values) + 15 (correlated noise for long-term tests).

---

## 10. Phase 17 - CI / CD / packaging infrastructure

### Goal
Make qgrav usable by anyone, not just on the author's machine. Run tests automatically on every PR. Publish to PyPI. Ship a Docker image.

### Tasks

#### 17.1 GitHub Actions test workflow

`.github/workflows/test.yml`:

```yaml
name: Tests
on: [push, pull_request]
jobs:
  test:
    strategy:
      matrix:
        os: [ubuntu-latest, windows-latest]
        python: ["3.11", "3.12"]
    runs-on: ${{ matrix.os }}
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: ${{ matrix.python }}
      - run: pip install -e . pytest matplotlib
      - run: pytest tests -q -m "not slow"
```

Plus a nightly `nightly.yml` that runs `pytest -m slow` (the published-reference benchmarks).

#### 17.2 PyPI release workflow

`.github/workflows/release.yml`: triggers on tag `v*`, builds a wheel, uploads to PyPI via trusted publishing.

#### 17.3 Dockerfile

```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY . .
RUN pip install --no-cache-dir -e .
ENTRYPOINT ["qgrav"]
```

`docker-compose.yml` for running headlessly with a mounted `configs/` and `runs/` volume.

#### 17.4 MkDocs docs site

`mkdocs.yml` building all the markdown docs in `docs/` into a GitHub Pages site at `https://<your-username>.github.io/quantum-grav-platform/`.

#### 17.5 Performance benchmarks

`tests/benchmark_*.py` using `pytest-benchmark`. Track:
- 60-point gravity sweep wall-clock
- 100-drop multi-drop cycle wall-clock
- Single MZ sequence wall-clock
- Calibration overhead

Numbers go into `docs/PERFORMANCE.md`.

### Owner: me (scaffolding) + you (PyPI/GitHub secrets)
### Time: 4 hours (my side) + your secret setup time
### Success criteria
- Green CI badge on the repo README
- `pip install qgrav` works
- `docker run qgrav run --config /configs/example.yaml` works
- Performance numbers documented

### Resolves: C11, C15

### What you do
- Enable GitHub Actions on the repo
- Create a PyPI account and a trusted publisher token (one-time setup)
- (Optional) DockerHub account

---

## 11. Phase 18 - Eliminate the empirical calibration

### Goal
Remove the ~2.5 rad empirical calibration step by deriving it analytically (or by sub-pulse integration). This is the biggest single credibility upgrade.

### Approach A - Pulse-center time convention (fast)

Change `imprint_phase = ... + 0.5 * chirp * atoms.time**2` to use the pulse-center time `atoms.time + self.time_delta / 2.0`. From our diagnostic, this halves the offset.

Time: ~2 hours
Risk: low - backward-compatible for `chirp=0`
Outcome: residual ~1.3 rad offset, calibration still needed but smaller

### Approach B - Sub-pulse integration (full)

Replace the single-shot Raman matrix with a sub-pulse-stepped version that integrates `δ(t)·dt` properly through the τ window:

```python
def _prop_matrix(self, atoms, n_substeps=8):
    full_matrix = np.eye(...)
    sub_tau = self.time_delta / n_substeps
    for k in range(n_substeps):
        atoms_substep = self._advance_classical(atoms, k * sub_tau)
        m = self._upstream_prop_matrix_for_substep(atoms_substep, sub_tau)
        full_matrix = m @ full_matrix
    return full_matrix
```

Time: 8-16 hours
Risk: high - may break upstream tests, slow down everything by 8×
Outcome: calibration step removed entirely; cross-validation tolerance can probably tighten to atol = 0.03 on populations

### Approach C - Wait for the physics reviewer

If the reviewer says "the calibration is legitimate", we can keep it forever and just document. If they say "no, it's a bug", we go to Approach B.

### Recommendation
**Do Approach A immediately** (small, low-risk, halves the calibration offset). Defer B until after the physics review responds.

### Tasks

#### 18.1 Approach A - pulse-center change
- One-line change in `_aisim_overrides.py` (post-Phase 12)
- Re-run all 253 tests
- Re-measure the calibration offset (expect ~1.3 rad instead of 2.5 rad)
- Document the change in CHANGELOG

#### 18.2 Approach B - sub-pulse (deferred)
- Spawned to its own task list when greenlit

### Owner: me
### Time: 2 hours for Approach A; 8-16 hours for Approach B
### Success criteria
- `_calibrate_gravity_phase_offset` returns a smaller magnitude
- Cross-validation tolerance can be tightened in `test_gravity_mz_sequence.py`
- All other tests pass

### Resolves: partial C1 (Approach A); full C1 (Approach B)

### Dependency
Phase 12 (subclass refactor) - otherwise we'd be patching vendored code again.

---

## 12. Phase 19 - Documentation completion

### Goal
Bring `docs/COMPLETE_GUIDE.md` (1186 lines, last fully rewritten at v0.8) up to date with v1.0+ features. Write a JOSS paper draft.

### Tasks

#### 19.1 COMPLETE_GUIDE.md full pass
- Update all `qgrav v0.8.0` references to `v1.1.0`
- Add new sections: 16. Emergent gravity, 17. Multi-drop cycle, 18. Published-reference validation
- Update the architecture map to include the new modules
- Re-screenshot the GUI (if any new tabs/widgets added)
- Cross-link to V1_PHYSICS_UPGRADE.md, PHYSICS_REVIEW_PACKET.md, ROADMAP_V1_TO_V2.md

#### 19.2 JOSS paper draft

`paper/paper.md` (~5 pages, JOSS template):

- Title: "qgrav: a software-first R&D platform for atom-interferometric gravimetry"
- Summary, Statement of need, Functionality, Acknowledgements, References
- Submit when ready

#### 19.3 API reference

Generate Sphinx API docs from docstrings. Publish via Phase 17's MkDocs/Sphinx setup.

### Owner: me
### Time: 4 hours
### Success criteria
- COMPLETE_GUIDE.md is internally consistent and reflects v1.1
- `paper/paper.md` ready for JOSS pre-review
- Sphinx API docs live on GitHub Pages

### Resolves: C13

---

## 13. Phase 20 - Release v1.1.0 (consolidation)

### Goal
Cut a clean release with all the above improvements.

### Tasks

#### 20.1 Pre-release checklist
- [ ] All Phase 11-19 work merged
- [ ] All 253+ tests pass (target: ~280)
- [ ] CHANGELOG updated
- [ ] Version bumped: 1.0.0 → 1.1.0 in `__init__.py`, `pyproject.toml`, README
- [ ] CI is green
- [ ] Documentation site is live
- [ ] Physics reviewer response (if received) summarised in `docs/PHYSICS_REVIEW_RESPONSES.md`

#### 20.2 Release
- Tag `v1.1.0` on the repo
- GitHub Actions auto-publishes to PyPI
- Update DockerHub image
- Announce: r/Physics, atom-interferometry mailing list, JOSS submission

### Owner: me + you
### Time: 2 hours (mostly waiting for CI)
### Success criteria
- `pip install qgrav==1.1.0` works
- `docker pull yourorg/qgrav:1.1.0` works
- README badge shows green CI

---

## 14. Beyond v1.1: v2.0 vision

The above takes us to v1.1.0 with ~280 tests, three published-reference regressions, and a clean release infrastructure. Looking further out:

### v1.2 candidates (~3 months out)
- Approach B sub-pulse integration (Phase 18 deferred half)
- 4-pulse and 5-pulse interferometers (extension to differential gravimetry)
- Real interferometer-output ingestion (CSV → algorithm → metrics on real lab data, if available)
- Wavefront aberrations driven from real Zernike-coefficient measurements

### v2.0 candidates (~6-12 months out)
- **Hardware control** - once IIT Patna gets to a point where lab atoms exist, replace synthetic bench with real photodiode data
- **Quantum-projection-noise simulation at the atom level** (Monte Carlo over single-atom outcomes instead of mean populations)
- **Bayesian inference for g** from the multi-drop time series with full ensemble likelihood
- **GUI overhaul** with web-based dashboard (Plotly + Dash) replacing the tkinter desktop app
- **PyPI publication of an `aisim-patched` fork** so other groups can use the integrated-phase formula

### v2.0 hardware integration roadmap

When a real hardware setup becomes available:

1. Identify the photodiode interface (NI-DAQ, oscilloscope CSV, custom driver)
2. Implement `bench_ifo/real_hardware.py` returning the same dict-shape as `virtual_ifo.generate_virtual_ifo`
3. Compare the live-hardware Allan deviation against the qgrav-predicted Allan deviation (closure test)
4. If they agree within factor 2, the qgrav simulation is *validated against your specific instrument*

This is the long-game endgame: validate against your own hardware once it exists. The current platform is the infrastructure that makes that validation possible.

---

## 15. What you need to do (and when)

| When | What | Estimated time |
|------|------|----------------|
| **Now** | Send the physics review packet to 3-5 contacts (see `REVIEW_REQUEST_TEMPLATE.md`) | 30 min |
| **Now** | Confirm: should I start with Phase 11 (reference bugs) or Phase 12 (vendor refactor)? | 1 min |
| **Within 2 weeks** | Provide GitHub repo URL + grant me visibility on it (or work on local copy) | 5 min |
| **Within 1 month** | Set up PyPI trusted publisher token + add to GitHub secrets | 30 min |
| **Within 2 months** | Follow up with physics reviewer contacts who haven't replied; consider conference visit | varies |
| **Per release** | Approve CHANGELOG and version bump; run smoke test on your machine | 30 min |
| **As needed** | Provide judgement calls on physics parameter choices (e.g., Freier 2016 setup) | 15 min each |
| **Ongoing** | If a hardware setup ever becomes available, plug it into the bench layer (Phase v2.0) | days-weeks |

---

## 16. Cumulative test-count target

| Release | Tests | New | Notes |
|---------|-------|-----|-------|
| v0.8.0 | 134 | - | Scientific foundations |
| v0.9.3 | 192 | +58 | Audit fix release |
| **v1.0.0** | **253** | **+61** | Emergent gravity, multi-drop, AC Stark, wavefront |
| v1.1.0 (target) | **~285** | +32 | Reference bugs (4), wired YAML keys (4), PID + correlations (3), Freier (1), Hu (1), Ménoret (2), pulse-center (1), perf benchmarks (5), MkDocs validation (~10) |
| v1.2.0 (target) | ~300 | +15 | 4-pulse & 5-pulse, real interferometer ingest, real Zernike data |
| v2.0.0 (target) | ~350+ | +50 | Hardware bench, MC quantum projection, Bayesian inference |

---

## Closing note

This roadmap is a **living document**. Reality will scramble the order: physics reviewer responses may shortcut Phase 18; hardware availability may leapfrog us to v2.0; an Allan-deviation-tooling issue may force changes earlier. Re-edit this file whenever priorities change - git-blame will preserve the history.

The single most-important action remains **Phase 11 (reference bugs)** + **getting the physics review packet to an external expert** - those two are the gating items for any credible claim about the simulation's correctness. Everything else is engineering that's only useful if those two land.
