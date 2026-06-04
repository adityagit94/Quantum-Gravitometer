# Research Findings Summary — Topics 1–9

Quick-reference summary of the highest-impact findings from the 9 research files, focused on **what changes in the roadmap**. Detailed citations are in the individual files.

---

## 🟢 Findings that VALIDATE the v1.0 work

### F1. The factor-of-2 claim in Patch C is **independently confirmed**
**Source:** `RESEARCH_AISIM_PHYSICS.md` TL;DR

> *"The factor-of-2 claim of Patch C is consistent with every primary source surveyed, provided the patched code applies `exp(-i δ(t₀) t₀)` on top of an unmodified Cheinet 2008-style rotation."*

**Implication:** The single most important physics claim in our `PHYSICS_REVIEW_PACKET.md` has been independently verified against Cheinet 2008, Kasevich & Chu 1991, Young/Kasevich/Chu 1997, and the Chu Nobel lecture. We can quote this finding in the review packet's §4 ("the factor-of-2 derivation has been corroborated by an independent literature survey") — this strengthens the packet considerably before sending it to a human reviewer.

### F2. Open-source niche is real
**Source:** `RESEARCH_OSS_COMPARISON.md` TL;DR

> *"qgrav occupies a niche that no single existing open-source package fully covers... There is no public release of a gravimetry simulation pipeline from the leading experimental groups (Stanford/Kasevich, Berkeley/Müller, Sandia, NPL, NIST quantum-sensing)."*

**Implication:** The JOSS Statement of Need writes itself. We are filling a documented gap.

---

## 🟡 Findings that CORRECT our Phase 13/16 setup parameters

### F3. Freier 2016 corrections
**Source:** `RESEARCH_FREIER_2016.md`

Our `freier_2016_setup.py` placeholder in the roadmap had three wrong values:

| Parameter | Roadmap guess | **Correct value** | Source |
|-----------|--------------:|------------------:|--------|
| `tau_pi_half_s` | 23e-6 | **17e-6** (= 17 µs π/2; π pulse is 34 µs) | Freier thesis 2017 |
| `single_photon_detuning_hz` | "a few GHz" | **−7e8** (= −700 MHz, red of F'=1) | Hu et al. arXiv:1805.05159 on GAIN |
| `beam_radius_m` | 0.01475 (29.5e-3/2) | **0.015** (1/e² diameter = 30 mm) | Hu et al., 2018 |

Verified correct:
- T = 260 ms ✓
- T_cycle = 1.5 s ✓
- Cloud temp ≈ 2 µK ✓
- Detection: state-selective normalised fluorescence ✓
- Vibration: active feedback on Minus-K passive platform + Güralp CMG-3VL seismometer post-correction
- Chirp rate α = 2π × 25.14 MHz/s

### F4. Hu 2013 corrections (BIG ONE)
**Source:** `RESEARCH_HU_2013.md` TL;DR

> ***"The user's task premise is incorrect: Hu et al., Phys. Rev. A 88, 043610 (2013) is NOT a 10-meter drop-tower gravimeter.** It is a short atomic-fountain gravimeter at HUST, Wuhan, with free-evolution time **T = 300 ms** and an atomic apex of ≈ 0.75 m above the MOT."*

**Implication:** Our roadmap's Hu 2013 setup file would have been completely wrong if we'd used the "10 m drop tower" assumption. The correct identification is HUST short fountain, T = 300 ms, n_atoms ≈ 5×10⁷ post-state-selection, single-photon detuning ≈ 1.5 GHz, cloud temp ≈ 7 µK (longitudinal-selected to ~300 nK).

The "Wuhan 10 m" instrument is a **different group** (M.-S. Zhan / WIPM-CAS) and a different paper (Zhou et al., Gen. Relativ. Gravit. 43, 1931 (2011)).

The Hu 2013 paper has **no systematic-error budget**; the first HUST systematic-error budget is in **Xu et al., Metrologia 59, 055001 (2022)** with HUST-QG short-term sensitivity 24 µGal/√Hz and combined uncertainty 3 µGal.

### F5. Ménoret 2018 corrections
**Source:** `RESEARCH_MENORET_2018.md` TL;DR

The roadmap's Ménoret setup placeholder used `interferometer_time_s = 80e-3`. **Correct value is T = 60 ms.** Cycle is **500 ms (2 Hz)**, not 1.0 s.

Vibration handling is **feed-forward active correction of the Raman laser phase using a hard-mounted Nanometrics Titan classical accelerometer — NOT a passive table**, which our roadmap mis-described.

The 7.5e-7 m/s²/√Hz value we corrected in v1.0.1 is **one of five distinct Allan-deviation numbers** in the paper:
- 500 nm/s²/√Hz — abstract/nominal
- 500 nm/s²/√Hz — Larzac best
- **750 nm/s²/√Hz — Larzac campaign** ← what we corrected to
- 600 nm/s²/√Hz — Talence quiet
- 700 nm/s²/√Hz — Talence typical

We picked the right one for "field/transportable robustness" benchmark per the original user instruction.

---

## 🔵 Findings that UNLOCK new capability

### F6. Bertoldi 2019 gives an analytical finite-τ correction
**Source:** `RESEARCH_FINITE_TAU.md` TL;DR

> *"The canonical leading-order finite-τ correction to the Mach–Zehnder scale factor Φ = k_eff·a·T² is multiplicative: Φ → k_eff·a·T²·[1 − ((2π−4)/π)·(τ/T)], with (2π−4)/π ≈ 0.7268"* (Bertoldi, Minardi & Prevedelli, PRA 99, 033619 (2019), Eq. 21)

> Equivalently: `T_eff = T + (2/Ω_R)·tan(Ω_R·τ_R/2)`, which for an ideal π/2-pulse area reduces to `T_eff = T + 4τ_R/π`.

**Implication for Phase 18:** We don't need to do the full sub-pulse integration (Approach B). We can substitute the **Bertoldi correction** as a closed-form replacement and check whether it eliminates the ~2.5 rad calibration offset. Pulse-center time convention (Approach A, 2 hours) plus the Bertoldi `T_eff` (1 more hour) should bring the residual down to <0.1 rad.

This **changes Phase 18's time estimate from 8–16 hours to ~3 hours** total.

### F7. Cheinet 2008 places time origin at pulse 2 CENTER
**Source:** `RESEARCH_FINITE_TAU.md` §1

> *"Cheinet 2008's sensitivity-function formalism explicitly places the time origin at the middle of the central π pulse, and gives an exact piecewise expression g(t) with sin(Ω_R t) ramps inside each rectangular Raman pulse"*

> Verbatim: *"Finally, we choose the time origin at the middle of the second Raman pulse. We thus have t_i = −(T + 2τ_R) and t_f = T + 2τ_R."*

**Implication:** Confirms our Phase 18 hypothesis that pulse-center timing is the correct convention. The standard MZ literature uses pulse-center-to-pulse-center for T, not pulse-edge-to-pulse-edge.

---

## 🟣 Findings that suggest NEW phase work

### F8. JOSS hard pre-review gates (2025)
**Source:** `RESEARCH_JOSS_SUBMISSION.md` TL;DR

JOSS now requires:
- ≥6 months of iterative public commit history
- OSI license file (we have GPL-3.0 ✓)
- Automated tests in CI (we have 276 tests but no CI yet — **Phase 17 is now blocking JOSS**)
- Documented Statement of Need
- Demonstrated research use (reproducing a published gravimetry result — **this is exactly what Phase 13 produces with Freier 2016**)
- **AI Usage Disclosure** (NEW 2025 requirement — we need to disclose that v1.0 plan was AI-assisted)
- 750–1100 word paper

**Implication:** Phase 17 (CI) and Phase 13 (Freier 2016 regression) are now **JOSS blockers**, not just nice-to-haves. The roadmap ordering is still correct but the criticality is higher than I labelled.

The AI Usage Disclosure deserves its own task. I'll add it.

### F9. Two new benchmark candidates suggested
**Source:** `RESEARCH_RECENT_BENCHMARKS.md` TL;DR

> *"qgrav v1.1.0 should retain all three existing regression targets and **add two new 2020+ targets** — Xu 2022 (HUST-QG, transportable; Metrologia) and Wu 2019 (Berkeley mobile; Sci. Adv.) — to broaden coverage to transportable and mobile/field regimes. Stray 2022 (Birmingham, Nature) is recommended as an optional gradiometer target."*

**Implication:** Phase 16 should be extended to include Xu 2022 + Wu 2019 (and optionally Stray 2022). This expands Phase 16 from "+2 benchmarks" to "+4 benchmarks". Time estimate increases from 5 hr to ~8 hr.

### F10. IGETS migrated FTP → SFTP in May 2025
**Source:** `RESEARCH_REAL_DATA_SOURCES.md` §1

Our existing `qgrav.datasets.gravimetry` loader works on local GGP files but **the IGETS server URL changed**: `igetsftp.gfz-potsdam.de` (SFTP, was FTP). If we add a programmatic IGETS fetcher later, update the URL.

---

## What I'm adding to the task list as a result

1. **Update task #20 (Phase 13: Freier 2016)** to use corrected parameters from F3 (τ=17µs, Δ=−700 MHz, beam radius 15 mm).
2. **Update task #23 (Phase 16: Hu 2013 + Ménoret 2018)** to use corrected parameters from F4, F5 (Hu T=300ms, Ménoret T=60ms cycle 500ms) and to consider adding Xu 2022 + Wu 2019.
3. **Update task #25 (Phase 18: Eliminate calibration)** to incorporate Bertoldi 2019 finite-τ correction (F6) — should shorten the work substantially.
4. **New task: AI Usage Disclosure** for the JOSS submission (F8).
5. **Update task #26 (Phase 19: COMPLETE_GUIDE refresh + JOSS paper)** to reference the JOSS hard pre-review gates from F8.
6. **Update PHYSICS_REVIEW_PACKET.md** with a section citing the AISim physics research (F1) as independent validation — strengthens the case before sending to a human reviewer.

These updates fold the research findings directly into the v1.1 implementation work.

---

## ✅ STATUS — applied to plans on 2026-05-28

The above findings were folded into the planning documents (no source-code changes yet, per user request to "understand → update plans → then move on"):

- **`docs/ROADMAP_V1_TO_V2.md`** — new §1.5 "Research-driven updates (Topics 1–11)" added with corrected Freier/Hu/Ménoret parameter tables, the Bertoldi closed-form finite-τ correction, the two new benchmark targets (Xu 2022, Wu 2019), and the JOSS hard-gate notes. The §3 "who owns what" table was revised (Phase 16: 5→8 hr; Phase 18: 8–16→3 hr; Phase 11 marked done).
- **Task list** — tasks #20, #23, #25, #24, #26 rewritten with the corrected parameters and citations so they are correct at execution time.
- **Still pending (waiting on user):** Topics 12–14 research files; population of `REVIEW_REQUEST_TEMPLATE.md` with Achim Peters' contact; and the actual source-code work (Phases 12–20), which resumes once the user signals to proceed.

Items NOT yet done (deferred until code work resumes):
- Adding the F1 citation into `PHYSICS_REVIEW_PACKET.md` §4 (a doc edit; will do alongside Phase 13 or when packet is sent).
- Creating an explicit "AI Usage Disclosure" task (folded into task #26 description for now).

---

## Addendum — Topics 12 & 14 (final batch, May 2026) + Topic 13 applied

### F13. Dissemination venues (Topic 12, `RESEARCH_VENUES.md`)
Most 2026 conference deadlines have passed. Forward targets: JOSS (software) + CPC/SoftwareX (fuller paper); YAO 2026 (Crete, Jun), SciPy 2027, NCAMP 2027 (India). **JOSS requires ≥6 months of public open-development history** → the practical gating action is to make the GitHub repo public and start its commit history now; JOSS lands ~6 months later. Folded into roadmap §1.5.9.

### F14. Finite-τ closed-form formulas (Topic 14, `RESEARCH_FINITE_TAU_FORMULAS.md`)
Confirms and refines F6:
- Bertoldi 2019 Eq. 21 multiplicative factor `(1 − (2π−4)/π · τ/T)` reconfirmed; equals `1 − 2τ/T + 4τ/(πT)`.
- Adds the **Fang/Mielec 2018 equivalent scale factor** `S_rec = k_eff·(T+τ/2)·(T+(4/π−3/2)τ)`.
- Bertoldi Eq. 32 residual single-shot term **averages to zero over the velocity distribution** — so for our ensemble the velocity-averaged correction is exactly the multiplicative factor (good news for Phase 18 calibration).
- **Caveat:** the `T+(4/Ω)tan(Ωτ/2)` form must NOT be attributed to Peters 2001 or Le Gouët 2008. Folded into roadmap §1.5.5 with corrected citations.
- Cheinet 2008 exact `G(ω)` (Eq. 8) and low-freq `|H(2πf)|² = 16 sin⁴(πfT)` are code-ready if we ever want an exact transfer-function path.

### Topic 13 — DONE and shipped
The reference audit (Topic 13) was applied in **v1.0.2**: 3 unit-category errors fixed + 2 ambiguous re-labelled, registry 12→14 entries, 286 tests pass. See CHANGELOG v1.0.2.

---

## ✅ ALL 14 RESEARCH TOPICS COMPLETE

No research remains. Everything is folded into `docs/ROADMAP_V1_TO_V2.md` §1.5 and the task list. The remaining work is the v1.1 source-code implementation (Phases 12–20), on hold pending the user's go-ahead.

---

## Addendum — Topics 10 & 11 (researched May 2026, second batch)

### F11. Reviewer-contact short list confirmed
**Source:** `RESEARCH_REVIEWER_CONTACTS.md`

Highest-priority contact for the physics-review packet is **Prof. Achim Peters** at HU Berlin (achim.peters@physik.hu-berlin.de) — directly relevant to the Freier 2016 benchmark since GAIN is his group's instrument. Bastian Leykauf (AISim upstream maintainer, also at QOM HU Berlin) is the natural second contact.

**Implication:** No code change. User can now populate the `REVIEW_REQUEST_TEMPLATE.md` cover letter with a real email address and send. This unblocks resolving C14 (no independent physics review) — the gating item for crediblity of the `FULLY_SIMULATED` study scope label.

### F12. Exail AQG is the only fully-documented commercial atom gravimeter
**Source:** `RESEARCH_HARDWARE_VENDORS.md` TL;DR

Only Exail (ex-Muquans / iXBlue) AQG family has a complete public spec sheet: 500 nm/s²/√Hz, ~2 Hz drop rate, sub-µGal long-term stability, BKG-independently-verified accuracy ~100 nm/s². No published API, file format, or schema documentation for any commercial atom gravimeter. AOSense, Vector Atomic GAINS, Infleqtion, Q-CTRL all publish marketing copy only.

For the signal-chain integration layer (v2.0 hardware bench): the right reference architectures are Microchip 5125A (digital cross-correlation ADEV analyzer), Microsemi TimePod 5330A (16-bit RF ADC), and NI PXIe-4464 DSA (24-bit delta-sigma for fluorescence-photodiode chains).

**Implication for v2.0:** The hardware-bench layer should target Exail-style telemetry as the closest-to-public reference. Until they publish an API, the qgrav v2.0 hardware bench will have to define its own schema; this is fine but worth documenting as a design choice. None of this changes v1.1 work.
