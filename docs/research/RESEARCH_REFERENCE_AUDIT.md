# Verification of 10 Reference Values in the qgrav Atom-Interferometric Gravimetry Package

## TL;DR
- **6 of 10 values are CORRECT** (Freier 2016 ×3, Ménoret 2018, Peters 2001 accuracy), **3 are WRONG because the stored unit/quantity is mis-typed** (Kasevich–Chu 1991, Bidel 2018, and the superconducting-gravimeter noise floor each conflate a different physical quantity with an amplitude spectral density), and **2 are AMBIGUOUS** (the NLNM scalar is frequency-dependent and ~4 dB high; the Peters-2001 fringe visibility of 0.5 could not be confirmed in the primary source).
- The three serious errors are unit-category confusions: a dimensionless Δg/g resolution stored as m/s²/√Hz (Kasevich–Chu); a static measurement *uncertainty* (0.17 mGal) stored as a /√Hz sensitivity, when the paper's actual sensitivity is 0.8 mGal/√Hz = 8e-6 m/s²/√Hz (Bidel); and a frequency-domain *detectability* (1 nGal) stored as an amplitude spectral density that is ~100–300× too low (SG noise floor; realistic ASD ≈ 1–3 nm/s²/√Hz).
- The Freier 2016 trio (9.6e-8 m/s²/√Hz short-term noise, 3.9e-8 m/s² accuracy, 5e-10 m/s² long-term stability) all trace exactly to the paper's abstract (96 nm/s²/√Hz, 39 nm/s², 0.5 nm/s²) and are correct.

## Key Findings

| # | KEY | Stored value | Verdict |
|---|-----|--------------|---------|
| 1 | freier_2016_short_term_noise | 9.6e-8 m/s²/√Hz | **CORRECT** |
| 2 | freier_2016_accuracy | 3.9e-8 m/s² | **CORRECT** |
| 3 | freier_2016_long_term_stability | 5e-10 m/s² | **CORRECT** |
| 4 | menoret_2018_long_term_stability | 1e-8 m/s² | **CORRECT** (paper states it as an upper bound) |
| 5 | peters_2001_accuracy | 3e-8 m/s² | **CORRECT** (fractional accuracy → acceleration) |
| 6 | kasevich_chu_1991_first_demo | 3e-6 m/s²/√Hz | **WRONG** — dimensionless Δg/g mislabeled as ASD |
| 7 | bidel_2018_marine | 1.7e-6 m/s²/√Hz | **WRONG** — 0.17 mGal uncertainty ≠ sensitivity; true ASD = 8e-6 m/s²/√Hz |
| 8 | nlnm_low_freq | 7e-10 m/s²/√Hz | **AMBIGUOUS** — right band/order, but ~4 dB high; true min ≈ 4e-10 m/s²/√Hz |
| 9 | sg_noise_floor | 1e-11 m/s²/√Hz | **WRONG** — 1 nGal detectability mislabeled as ASD; true ASD ≈ 1–3e-9 m/s²/√Hz |
| 10 | mz_visibility | 0.5 (dimensionless) | **AMBIGUOUS/UNVERIFIED** — not confirmed in Peters 2001 |

## Details

### 1. freier_2016_short_term_noise — 9.6e-8 m/s²/√Hz — CORRECT
- **Source:** Freier, Hauth, Schkolnik, Leykauf, Schilling, Wziontek, Scherneck, Müller, Peters (2016), "Mobile quantum gravity sensor with unprecedented stability," *J. Phys.: Conf. Ser.* **723**, 012050. **DOI 10.1088/1742-6596/723/1/012050**; arXiv:1512.05660 (https://arxiv.org/abs/1512.05660).
- **Value as printed:** short-term noise of **96 nm/s²/√Hz**.
- **Location:** Abstract (identical on arXiv abstract page).
- **Verbatim quote:** "They show the best-reported performance of mobile atomic gravimeters to date with an accuracy of 39 nm/s², long-term stability of 0.5 nm/s² and short-term noise of 96 nm/s²/√Hz."
- **SI conversion (arithmetic):** 96 nm/s²/√Hz × 1e-9 (m/s²)/(nm/s²) = **9.6e-8 m/s²/√Hz** (= 9.6 µGal/√Hz, since 1 µGal = 1e-8 m/s² → 9.6e-8/1e-8 = 9.6 µGal/√Hz).
- **Verdict: CORRECT.** No source disagreement.

### 2. freier_2016_accuracy — 3.9e-8 m/s² — CORRECT
- **Source:** Same as #1; Abstract.
- **Value as printed:** accuracy of **39 nm/s²**.
- **Verbatim quote:** (same sentence as above).
- **SI conversion:** 39 nm/s² × 1e-9 = **3.9e-8 m/s²** = 3.9 µGal (39/10 nm/s² per µGal = 3.9 µGal).
- **Verdict: CORRECT.**

### 3. freier_2016_long_term_stability — 5e-10 m/s² — CORRECT
- **Source:** Same as #1; Abstract.
- **Value as printed:** long-term stability of **0.5 nm/s²**.
- **Verbatim quote:** (same sentence as above).
- **SI conversion:** 0.5 nm/s² × 1e-9 = **5e-10 m/s²** = 0.05 µGal.
- **Verdict: CORRECT.**

### 4. menoret_2018_long_term_stability — 1e-8 m/s² — CORRECT (stated as an upper bound)
- **Source:** Ménoret, Vermeulen, Le Moigne, Bonvalot, Bouyer, Landragin, Desruelle (2018), "Gravity measurements below 10⁻⁹ g with a transportable absolute quantum gravimeter," *Sci. Rep.* **8**, 12300. **DOI 10.1038/s41598-018-30608-1**; arXiv:1809.04908; PMC6098009.
- **Values as printed:** long-term stability **below 10 nm·s⁻² (1 µGal)**; measurement sensitivity **500 nm·s⁻²·Hz⁻¹ᐟ²** at a 2 Hz repetition rate.
- **Location:** Abstract and main text ("Here, we report on both operability and sensitivity at the level of 10 nm.s⁻²…").
- **Verbatim quotes:** (Abstract) "measure the absolute gravitational acceleration continuously with a long-term stability below 10 nm.s−2 (1 μGal)." (Body) "The resulting sensor measures gravity at a 2 Hz repetition rate with a sensitivity of 500 nm.s−2.Hz−1/2 and a long term stability below 10 nm.s−2 with a short installation and warm-up time."
- **SI conversion:** 10 nm/s² × 1e-9 = **1e-8 m/s² = 1 µGal**. (Title's "below 10⁻⁹ g" = 9.8e-9 m/s² ≈ 1e-8 m/s², consistent.)
- **Verdict: CORRECT**, with the caveat that the paper reports this as an upper bound ("below 10 nm/s²"), not an exact equality. The separately stated short-term sensitivity (500 nm/s²/√Hz = 5e-7 m/s²/√Hz) is a different quantity and should not be confused with the stability figure.

### 5. peters_2001_accuracy — 3e-8 m/s² — CORRECT
- **Source:** Peters, Chung, Chu (2001), "High-precision gravity measurements using atom interferometry," *Metrologia* **38**, 25–61. **DOI 10.1088/0026-1394/38/1/4**. Companion: Peters, Chung, Chu (1999), *Nature* **400**, 849–852, **DOI 10.1038/23655**.
- **Values as printed (2001 abstract):** resolution Δg/g = **2×10⁻⁸** (single 1.3 s shot), **3×10⁻⁹** (1 min), **1×10⁻¹⁰** (two days); difference vs falling-corner-cube gravimeter = **(7 ± 7)×10⁻⁹ g**. The 1999 Nature paper states an absolute uncertainty of **Δg/g ≈ 3×10⁻⁹**.
- **Verbatim quote (2001 abstract):** "We have built an atom interferometer that can measure g, the local acceleration due to gravity, with a resolution of Δg/g = 2 × 10⁻⁸ after a single 1.3 s measurement cycle, 3 × 10⁻⁹ after 1 min and 1 × 10⁻¹⁰ after two days of integration time. The difference between our value for g and one obtained by a falling corner-cube optical interferometer is (7 ± 7) × 10⁻⁹ g."
- **Verbatim quote (1999 Nature):** "…we achieve an absolute uncertainty of Δg/g ≈ 3 × 10⁻⁹, representing a million-fold increase in absolute accuracy compared with previous atom-interferometer experiments."
- **SI conversion:** Δg/g ≈ 3×10⁻⁹ × g(≈9.8 m/s²) = 2.94e-8 ≈ **3e-8 m/s² (≈ 3 µGal)**.
- **Verdict: CORRECT.** Note the value is a *fractional* accuracy (Δg/g ≈ 3e-9) converted to acceleration; do not conflate it with the "3×10⁻⁹ after 1 min" *resolution*, which is a per-minute statistical resolution at the same numerical value but a different physical meaning.

### 6. kasevich_chu_1991_first_demo — 3e-6 m/s²/√Hz — WRONG (unit/quantity error)
- **Source:** Kasevich & Chu (1991), "Atomic interferometry using stimulated Raman transitions," *Phys. Rev. Lett.* **67**(2), 181–184. **DOI 10.1103/PhysRevLett.67.181**.
- **Value as printed:** resolution of **3×10⁻⁶ after 1000 sec** of integration time.
- **Location:** Abstract / first page.
- **Verbatim quote:** "Using the interferometer as an inertial sensor, the acceleration of a sodium atom due to gravity has been measured with a resolution of 3×10⁻⁶ after 1000 sec of integration time."
- **Critical flag — quantity mismatch:** The "3×10⁻⁶" is a **dimensionless fractional resolution (Δg/g) after 1000 s**, NOT an amplitude spectral density. The stored entry copies the numeral but assigns it units of m/s²/√Hz, which is physically incorrect. As an acceleration, 3×10⁻⁶ × g ≈ 2.9e-5 m/s² RMS after 1000 s; expressed as an ASD that would be ≈ 2.9e-5 × √1000 ≈ 9e-4 m/s²/√Hz — three orders of magnitude away from the stored figure.
- **Verdict: WRONG.** Store as dimensionless Δg/g = 3e-6 (at 1000 s integration), or recompute the ASD (≈ 9e-4 m/s²/√Hz). Note: the 1991 PRL used **sodium** atoms; the often-cited 3×10⁻⁸ g resolution comes from the later Kasevich & Chu (1992, *Appl. Phys. B* **54**, 321) follow-up, a different paper.

### 7. bidel_2018_marine — 1.7e-6 m/s²/√Hz — WRONG (unit/quantity error)
- **Source:** Bidel, Zahzam, Blanchard, Bonnin, Cadoret, Bresson, Rouxel, Lequentrec-Lalancette (2018), "Absolute marine gravimetry with matter-wave interferometry," *Nat. Commun.* **9**, 627. **DOI 10.1038/s41467-018-03040-2**; PMC5809417; HAL hal-01727834.
- **Values as printed:** static **measurement sensitivity = 0.8 mGal·Hz⁻¹ᐟ²**; static **measurement uncertainties** of **0.06 mGal** (T=39 ms, 42 mm drop) and **0.17 mGal** (T=20 ms, 14 mm drop). (1 mGal = 1e-5 m/s².)
- **Location:** "Evaluation of the gravimeter sensitivity and accuracy in static" section.
- **Verbatim quotes:** "The measurement sensitivity of our gravimeter in static is equal to 0.8 mGal Hz−1/2 limited by the sensitivity of the force balanced accelerometer." And: "The measurement uncertainty has been estimated to 0.06 mGal (1 mGal = 10−5 m s−2) with T = 39 ms using the 42 mm falling distance and to 0.17 mGal with T = 20 ms using the 14 mm falling distance."
- **Critical flag:** The stored 1.7e-6 m/s²/√Hz = 0.17 mGal/√Hz appears to mis-take the **0.17 mGal static uncertainty** (a bias/uncertainty, no /√Hz) as a spectral-density sensitivity. The paper's actual short-term **sensitivity** is **0.8 mGal/√Hz**.
- **SI conversion of the correct sensitivity:** 0.8 mGal/√Hz × 1e-5 (m/s²)/mGal = **8e-6 m/s²/√Hz**.
- **Verdict: WRONG.** Replace with 8e-6 m/s²/√Hz (0.8 mGal/√Hz). If a "0.17 mGal" figure is wanted, store it separately as a static measurement uncertainty (= 1.7e-6 m/s², no /√Hz). Note also the overall marine **precision below 10⁻⁵ m s⁻²** quoted in the abstract is yet another distinct figure (a campaign result, not an ASD).

### 8. nlnm_low_freq — 7e-10 m/s²/√Hz — AMBIGUOUS (right band/order, ~4 dB high)
- **Source:** Peterson (1993), "Observations and modeling of seismic background noise," USGS Open-File Report 93-322 (95 pp.). Stable URL https://pubs.usgs.gov/of/1993/0322/. Conversion reference: Bormann (1998), *J. Seismology* **2**, 37–45, **DOI 10.1023/A:1009780205669**.
- **How the model is published:** acceleration **power** spectral density in **dB relative to (1 m/s²)²/Hz**. Per the seizmo implementation of Peterson's NLNM (g2e/seizmo `nlnm.m`): "returns the Peterson 1993 New Low Noise Model (NLNM)… The noise model is in units of decibels relative to (1 m/s^2)^2/Hz." Per Bormann (1998): "the new global low-noise model (NLNM) as given by Peterson (1993). Peterson published values for Pa [dB] only. The respective numbers for ground acceleration (Pa), velocity and displacement have been calculated… Between the listed periods the values are to be linearly interpolated in a PSD-logT diagram." The deepest portion of the NLNM acceleration PSD is approximately **−187.5 dB** near ~45–70 s period and **−185 dB** near ~100–150 s.
- **Conversion arithmetic — stored value:** (7e-10)² = 4.9e-19 (m/s²)²/Hz → 10·log₁₀(4.9e-19) ≈ **−183.1 dB**.
- **Conversion arithmetic — NLNM minimum:** −187.5 dB → 10^(−187.5/10) = 1.78e-19 (m/s²)²/Hz → √ = **4.2e-10 m/s²/√Hz**; −185 dB → 10^(−18.5) = 3.16e-19 → √ = **5.6e-10 m/s²/√Hz**.
- **Verdict: AMBIGUOUS.** The stored 7e-10 m/s²/√Hz (≈ −183 dB) is the correct order of magnitude and sits in the right (long-period, ~30–100 s) band, but is about **4 dB high** versus the true NLNM minimum of ~4e-10 m/s²/√Hz (−187.5 dB). Because the NLNM is strongly frequency-dependent (spanning ~−188 dB to far higher across the band), a single scalar is inherently an approximation; the band must be documented. Recommend storing ~4e-10 m/s²/√Hz for the minimum and noting it applies at ~30–100 s period.

### 9. sg_noise_floor — 1e-11 m/s²/√Hz — WRONG (unit/quantity error)
- **Source:** Hinderer, Crossley, Warburton, "Superconducting gravimetry," *Treatise on Geophysics* Vol. 3 (Geodesy), Ch. 3.04, pp. 65–122 (1st ed., 2007), **DOI 10.1016/B978-044452748-6.00172-3** (2nd ed., 2015, pp. 59–115/66–122, DOI 10.1016/B978-0-444-53802-4.00062-2). Supporting quantitative figures: Van Camp et al. (2017), *Reviews of Geophysics* **55**, **DOI 10.1002/2017RG000566**.
- **Reported figures:**
  - The "1 nGal" precision attributed to Hinderer/Crossley/Warburton is a **frequency-domain detectability**, with a **time-domain** figure of ~1 nm/s²: literature citing the chapter states "The smallest detectable gravity change in the frequency domain has been quantified as 1 nGal (0.01 nm·s⁻²) and 1 nm·s⁻² or better in the time domain." Neither is an amplitude spectral density.
  - The realistic PSD floor, from Van Camp et al. (2017), verbatim: "Current SGs have a power spectral density noise level ranging typically 1–10 (nm/s²)²/Hz (Figure A11), which means that they are able to detect temporal gravity change ranging 0.1–0.3 nm/s² (or 10–30 nGal) within 1 min." Taking the square root gives an **ASD of √1 to √10 ≈ 1.0–3.2 nm/s²/√Hz = 1.0e-9 to 3.2e-9 m/s²/√Hz**.
  - Best-site example (LSBB superconducting gravimeter), verbatim: "The instrument installed at LSBB has a noise performance among the best in a worldwide network of superconducting gravimeters, with an amplitude spectral density of 1.8 nm/s²/Hz⁻¹ᐟ² at 1 mHz" (= 1.8e-9 m/s²/√Hz).
- **Critical flag:** Stored 1e-11 m/s²/√Hz = 1 nGal/√Hz — this is the **1 nGal frequency-domain detectability mislabeled as an amplitude spectral density**. The true SG ASD noise floor is ~1–3e-9 m/s²/√Hz, i.e., **~100–300× higher** than the stored value.
- **Verdict: WRONG.** Store the ASD floor as ~1–3e-9 m/s²/√Hz (band ~0.1–10 mHz; SG noise is strongly frequency-dependent, rising below ~1 mHz). Keep "1 nGal" only if separately labeled as a frequency-domain detectability, not an ASD.

### 10. mz_visibility — 0.5 (dimensionless) — AMBIGUOUS / UNVERIFIED
- **Source claimed:** Peters, Chung, Chu (2001), *Metrologia* **38**, 25–61, **DOI 10.1088/0026-1394/38/1/4**.
- **Finding:** I could **not locate an explicit fringe contrast/visibility number** (e.g., "0.5" or "50%") in the Peters 2001 primary text. The paper contains the relevant figure — Figure 19, "Typical Doppler-sensitive interferometer fringe" — and the companion Nature 1999 paper has the analogous "Figure 2 Typical Doppler-sensitive interferometer fringe for T = 160 ms," but neither accessible excerpt states a numeric contrast, and the full-text contrast figure was paywalled (IOPscience/ResearchGate access-blocked). Per instructions, I am stating this explicitly rather than inventing a value.
- **Physical context (not a substitute for the source):** For a standard two-output Mach–Zehnder Raman interferometer, the *idealized* maximum contrast is C₀ = 0.5. The enricher confirmed a comparable real-instrument value from Bidel et al. 2018 (Methods), verbatim: "P = Pm−C/2 cos(ϕ), where Pm is the offset of the fringe and C is the contrast which is typically equal to 0.3 for our sensor." Other Raman gravimeters report contrasts ~0.16–0.6.
- **Verdict: AMBIGUOUS / UNVERIFIED.** 0.5 is a plausible idealized Mach–Zehnder value but is **not confirmed as the value reported in Peters 2001**. Do not cite Peters 2001 as the source without direct page verification.

## Recommendations
**Stage 1 — Fix the three unit-category errors now (highest priority; these are physically wrong, not just imprecise):**
1. **kasevich_chu_1991_first_demo:** change to dimensionless **Δg/g = 3e-6 at 1000 s integration** (PRL 67, 181). Do not store as m/s²/√Hz. If an ASD is genuinely needed, compute ≈ 9e-4 m/s²/√Hz and document the derivation.
2. **bidel_2018_marine:** change to **8e-6 m/s²/√Hz (0.8 mGal/√Hz)** for the static sensitivity. Store the 0.17 mGal / 0.06 mGal figures separately as static measurement *uncertainties* (1.7e-6 / 6e-7 m/s², no /√Hz).
3. **sg_noise_floor:** change to **~1–3e-9 m/s²/√Hz** (e.g., 1.8e-9 m/s²/√Hz at 1 mHz, LSBB), citing Van Camp et al. 2017 (DOI 10.1002/2017RG000566). Retain "1 nGal = 1e-11 m/s²" only as a separately labeled frequency-domain detectability.

**Stage 2 — Re-label the two frequency-dependent / unverified entries:**
4. **nlnm_low_freq:** treat as a frequency-dependent curve. If a scalar minimum is required, use **~4e-10 m/s²/√Hz (−187.5 dB)** and document the band (~30–100 s period). Cite Peterson 1993 (USGS OFR 93-322) with the Bormann (1998) conversion.
5. **mz_visibility:** either (a) verify the contrast from a full-text copy of Peters 2001 or Peters' 1998 Stanford thesis (ProQuest 9901575) and update the value/source, or (b) relabel 0.5 as a generic *idealized* Mach–Zehnder maximum not attributed to Peters 2001; alternatively adopt a sourced real value such as C = 0.3 (Bidel 2018, verified verbatim).

**Benchmark that would change these recommendations:** If a full-text copy of Peters 2001 (or the 1998 thesis) provides an explicit contrast number near Fig. 19, update entry 10 to that value and re-confirm its source. If qgrav's intended use of these constants is purely for order-of-magnitude noise budgeting (not metrological reporting), entries 6/7/9 still must be re-typed, but entry 8's 4 dB discrepancy may be tolerable with a documented note.

## Caveats
- **Quantity-type discipline is the recurring failure mode here.** Per-shot/per-interval resolutions, fractional ratios (Δg/g), RMS over an integration time, static measurement uncertainties, frequency-domain detectabilities, power spectral densities (PSD), and amplitude spectral densities (ASD = √PSD) are *distinct* physical quantities. Entries 6, 7, and 9 each took a correctly transcribed *number* from the source but attached the wrong quantity type and unit.
- Entries 4 (Ménoret) and 5 (Peters accuracy) are stated by their papers as bounds/fractional figures, not exact equalities.
- The Hinderer/Crossley/Warburton chapter exists in a 2007 1st edition (pp. 65–122) and a 2015 2nd edition; the "1 nGal" detectability sentence is most directly attributed to the 2015 version in citing literature, and the chapter's internal page/figure for that exact sentence was paywalled. The quantitative SG noise PSD figure used above (1–10 (nm/s²)²/Hz) is from Van Camp et al. 2017, which cites Fores et al. 2017 / Rosat & Hinderer 2011 / Van Camp et al. 2005 — not the Hinderer/Crossley/Warburton chapter itself.
- No numbers were fabricated. Entry 10 is explicitly flagged as unverified against the named primary source.