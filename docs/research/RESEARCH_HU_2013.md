# Parameter Extraction Report: Hu et al. 2013 Atom-Interferometry Absolute Gravimeter (HUST, Wuhan) - for qgrav v1.1.0 Validation

## TL;DR
- **The user's task premise is incorrect: Hu et al., Phys. Rev. A 88, 043610 (2013) is NOT a 10-meter drop-tower gravimeter.** It is a short atomic-fountain gravimeter at Huazhong University of Science and Technology (HUST), Wuhan, with free-evolution time **T = 300 ms** and an atomic apex of ≈ 0.75 m above the MOT. The "10-meter Wuhan" apparatus belongs to a different group (M.-S. Zhan, J. Wang, L. Zhou et al. at WIPM-CAS).
- For Hu 2013 (⁸⁷Rb), the confirmed parameters useful for qgrav validation are: T = 300 ms; cycle time ≈ 1 s/shot; N ≈ 5 × 10⁷ atoms post-state-selection (3 × 10⁹ in the MOT); cloud temperature ≈ 7 µK (with longitudinal velocity-selected width ≈ 300 nK); single-photon detuning ≈ 1.5 GHz; normalized fluorescence detection; **4.2 µGal/√Hz** short-term sensitivity (= 4.2 × 10⁻⁸ m s⁻²/√Hz ≈ 4.3 × 10⁻⁹ g/√Hz) reached on a continuous 40-h Allan-deviation run during 14-16 April 2013.
- **Hu 2013 contains no explicit numeric systematic-error budget** (Coriolis, wavefront aberration, gravity gradient, light shift, etc.). It is a sensitivity / noise-budget paper. The first published HUST systematic-error budget appeared nine years later in Xu et al., Metrologia 59, 055001 (2022): "HUST-QG exhibited a short-term sensitivity of 24 μGal Hz⁻¹/² and a combined uncertainty of 3 μGal."

---

## Key Findings

### Identity and isotope
The Hu 2013 paper is by Z.-K. Hu, B.-L. Sun, X.-C. Duan, M.-K. Zhou, L.-L. Chen, S. Zhan, Q.-Z. Zhang, and J. Luo (HUST, Wuhan 430074). The paper states verbatim in its abstract:

> "We present an ultrahigh-sensitivity gravimeter based on an ⁸⁷Rb atom interferometer using stimulated Raman transitions."

DOI: 10.1103/PhysRevA.88.043610; published 8 October 2013. **No arXiv preprint exists** (confirmed via ADS bibcode 2013PhRvA..88d3610H and arXiv search).

### The "10-m" claim does not apply
The 10-m Wuhan apparatus referenced in the user's task description is the WIPM-CAS Wuhan project led by M.-S. Zhan, described in Zhou et al., Gen. Relativ. Gravit. 43, 1931 (2011), DOI 10.1007/s10714-011-1167-9: "Experimental realizations of cold ⁸⁵Rb atom interferometers in Wuhan are reviewed in this paper… The resolutions of gravity measurement are 2.0 × 10⁻⁷g for 1 s and 4.5 × 10⁻⁹g for 1,888 s… A 10-meter atom interferometer designed for precision gravity measurement and the equivalence principle test is under construction." That apparatus uses ⁸⁵Rb (with ⁸⁷Rb for dual-species runs); the Hu 2013 paper does not.

### 1. Interrogation time T (free evolution between Raman pulses)
**T = 300 ms = 0.300 s.** Total interferometer time 2T = 0.600 s.

The HUST-group's own 2015 review (Zhou, Duan, Chen, Luo, Xu, Hu, Chinese Physics B 24, 050401 (2015), citing Hu 2013 as ref. [72]) states verbatim in the caption of Fig. 7: "A typical atom-interferometry fringe at a pulse separation of T = 300 ms, the total measuring time is 40 s for 40 shots." The same review repeats elsewhere: "considering a fringe visibility of about 15% and a pulse separation time of 300 ms."

The user's "0.6-1 s" working hypothesis is not supported by any source.

### 2. Cycle time
**≈ 1.0 s per measurement shot; data binned at 2 shots / 2 s.**

Zhou et al., Chin. Phys. B 24, 050401 (2015) (describing the Hu 2013 setup): "The whole time used for a single measurement is 1 s." And: "Each point represents two shots in every 2 s." MOT loading time is explicitly stated: "the loading time is set at 200 ms."

### 3. Sensitivity, integration time, and number of drops
**Short-term sensitivity 4.2 µGal/√Hz ≡ 4.2 × 10⁻⁸ m s⁻²/√Hz ≈ 4.3 × 10⁻⁹ g/√Hz** (note the hedging "about" in the abstract). The Allan deviation reaches **better than 0.5 µGal at 100 s integration** (≈ 5 × 10⁻⁹ m s⁻²).

Verbatim from the Hu 2013 abstract:

> "a short-term sensitivity of about 4.2 μGal/√Hz (1 μGal = 1 × 10⁻⁸ m/s²) is reached, which improves the sensitivity by a factor of 2 compared with the former best reported value."

Integration window from the HUST-group 2015 review (citing Hu 2013): a continuous 40-hour gravity run between 14 and 16 April 2013 (the Allan-deviation curve covers up to ~100 s for the white-noise plateau; bump near 2000 s). "After an integration time of 100 s, the resolution is better than 0.5 μGal." Drop count ≈ 40 h × 1 s⁻¹ ≈ 1.4 × 10⁵ drops (or ~7 × 10⁴ binned pairs at "2 shots per 2 s").

### 4. Number of atoms per shot
**N_MOT ≈ 3 × 10⁹; N in interferometer ≈ 5 × 10⁷ after state preparation.**

From Zhou et al., Chin. Phys. B 24, 050401 (2015) describing Hu 2013: "In our current experiment, about 3 × 10⁹ atoms with a temperature of 7 μK are trapped within 200 ms. The trapped atoms are then launched with an initial velocity of about 3.83 m/s, corresponding to a flight apex of about 0.75 m relative to the MOT center. After the state preparation, about 5 × 10⁷ atoms with a longitudinal temperature of about 300 nK are prepared in the F = 1, mF = 0 state."

### 5. Cloud temperature and isotope
- **Transverse cloud temperature: ≈ 7 µK** (3D-MOT + molasses).  
- **Longitudinal velocity-selected sample: ≈ 300 nK = 3 × 10⁻⁷ K.**  
- **Isotope: ⁸⁷Rb** (D₂ line, 780.241 nm) - confirmed verbatim from the Hu 2013 abstract.

Quote, same review: "about 3 × 10⁹ atoms with a temperature of 7 μK are trapped within 200 ms… about 5 × 10⁷ atoms with a longitudinal temperature of about 300 nK."

### 6. Detection method
**Normalized (state-resolved) fluorescence detection.**

Zhou et al., Chin. Phys. B 24, 050401 (2015): "Finally, the populations of atoms in F = 2 and 1 states are detected with the normalized detection method." The F = 2 fluorescence is detected first by a resonant probe; a repumping beam pumps F = 1 atoms to F = 2 for the second measurement; the population ratio rejects shot-to-shot atom-number fluctuations. Detailed geometry is not in any open source (it is in the paywalled body of Hu 2013 and in the precursor Zhou et al., Phys. Rev. A 86, 043630 (2012)).

### 7. Single-photon detuning Δ
**|Δ| ≈ 1.5 GHz** from the ⁸⁷Rb D₂ line (red-detuned, large compared with hyperfine splittings of the excited state). Sign and exact reference level are not unambiguously stated in open sources for Hu 2013.

Quote (Zhou et al. CPB 24, 050401, 2015, describing the Hu 2013 setup): "The Raman beam is obtained with an optical phase locking loop, and is then shifted by 1.5 GHz with an AOM to form a large detuning from the excited states. The phase noise of the laser beat note in the region of 200 Hz to 200 kHz is less than −100 dBc/Hz." The cooling-master laser is locked on |5S₁/₂, F = 2⟩ → |5P₃/₂, F' = 3⟩ ("The laser frequency is locked on the transition of |5S₁/₂, F = 2⟩ → |5P₃/₂, F = 3⟩ by the modulation-transfer stabilized (MTS) method"). The Raman frequency-chirp rate during free fall is 25.14 MHz/s (HUST review) - comparable to but not identical to 25.12 MHz/s quoted for a later HUST portable apparatus (Tao et al., Photonics 7, 32 (2020)): "Raman lasers are realized by OPLL with a sweeping frequency range of 11 MHz and chirp rate of 25.12 MHz/s." Treat 25.14 MHz/s as the closest open-source value for Hu 2013.

### 8. Vibration isolation
- **Residual vertical vibration contribution to g: 1.2 µGal/√Hz = 1.2 × 10⁻⁸ m s⁻²/√Hz.** Verbatim from the Hu 2013 abstract: "By a modulation experiment, we further indicate that the residual vibration noise contribution is about 1.2 μGal/√Hz, which implies a possible improvement over the present absolute gravity measurement level by about one order of magnitude."  
- **System:** three-axis commercial seismometer + passive isolator (resonance 0.5 Hz) carrying the Raman retro-reflector; digital LabVIEW feedback at 1 kHz / 16-bit DAQ. Detailed isolator characterization is in the precursor Zhou, Hu, Duan, Sun, Chen, Zhang, Luo, Phys. Rev. A 86, 043630 (2012), DOI 10.1103/PhysRevA.86.043630.  
- **Closed-loop natural frequency f₀ = 0.016 Hz** (step-response period 63 s).  
- **Loop gain:** acceleration error signal reduced by ×100 over 0.1-1 Hz; below 2 Hz the in-loop residual is **< 1 × 10⁻⁹ g/√Hz ≈ 10⁻⁸ m s⁻²/√Hz**, limited by sensor intrinsic noise and DAQ digitization (HUST 2015 review).

There is no "10-m drop tower" seismic isolation specification associated with this paper.

### 9. Systematic-error budget
**Hu 2013 does NOT publish a per-effect numeric systematic-error budget table.** It is a sensitivity / noise-budget paper, not an accuracy paper. The noise contributions reported in the HUST 2015 review (citing Hu 2013) are:

| Noise term | Contribution to g | SI |
|---|---|---|
| Raman-laser phase noise | ≈ 0.8 µGal/√Hz | 8.0 × 10⁻⁹ m s⁻²/√Hz |
| Detection noise (per shot, C ≈ 15%, T = 300 ms) | ≈ 3.3 µGal/√Hz | 3.3 × 10⁻⁸ m s⁻²/√Hz |
| Residual vertical vibration | ≈ 1.2 µGal/√Hz | 1.2 × 10⁻⁸ m s⁻²/√Hz |
| **Quadrature sum (measured)** | **≈ 4.2 µGal/√Hz** | **4.2 × 10⁻⁸ m s⁻²/√Hz** |

The first formal per-effect HUST systematic-error budget (Coriolis, wavefront, light shift, gravity gradient, 2nd-order Zeeman, gravity-gradient correction, self-attraction, etc.) appears in Xu, Cui, Qi, Chen, Deng, Luo, Zhang, Tan, Shao, Zhou, Duan, Hu, "Evaluation of the transportable atom gravimeter HUST-QG," Metrologia 59, 055001 (2022), DOI 10.1088/1681-7575/ac8258. Verbatim: "HUST-QG exhibited a short-term sensitivity of 24 μGal Hz⁻¹/² and a combined uncertainty of 3 μGal. The operation and evaluation of HUST-QG for transportable gravity measurements during the 10th International Comparison of Absolute Gravimeters are discussed. And the degree of equivalence for HUST-QG in this comparison is 1.3 μGal, which supports our evaluation." Those numbers belong to HUST-QG (2022) and **must not be back-projected onto Hu 2013**.

### 10. Follow-up papers from the same HUST group
| Citation | DOI / arXiv | Role |
|---|---|---|
| Zhou, Hu, Duan, Sun, Zhao, Luo, Front. Phys. China 4, 170 (2009) | 10.1007/s11467-009-0036-4 | Earliest project announcement (cave lab MOT) |
| Zhou, Hu, Duan, Sun, Chen, Zhang, Luo, Phys. Rev. A 86, 043630 (2012) | 10.1103/PhysRevA.86.043630 | **Precursor** active-vibration-isolator gravimeter (≈ 8 µGal/√Hz). Cited as "previous work" in Hu 2013 abstract. |
| Hu, Sun, Duan, Zhou, Chen, Zhan, Zhang, Luo, Phys. Rev. A 88, 043610 (2013) | 10.1103/PhysRevA.88.043610 | The paper of interest. |
| Duan, Zhou, Mao, Yao, Deng, Luo, Hu, Phys. Rev. A 90, 023617 (2014) | 10.1103/PhysRevA.90.023617 | Dual-fringe-locked gradiometer; verbatim: "A short-term sensitivity of 670 E/√Hz with a 0.25 Hz sampling rate is achieved in our gravity gradiometer." |
| Zhou, Duan, Chen, Luo, Xu, Hu, Chin. Phys. B 24, 050401 (2015) | 10.1088/1674-1056/24/5/050401 | HUST-group **review**; richest open-source description of Hu 2013 |
| Zhou, Xiong, Chen, Cui, Duan, Hu, Rev. Sci. Instrum. 86, 046108 (2015) | 10.1063/1.4919292 | 3-D active vibration isolator |
| Tao, Zhou, Zhang, Cui, Duan, Shao, Hu, Rev. Sci. Instrum. 86, 096108 (2015) | 10.1063/1.4931715 | DDS chirp-rate calibration |
| Duan, Deng, Zhou, Zhang, Xu, Xiong, Cui, Hu, Shao, Luo, Phys. Rev. Lett. 117, 023001 (2016) | 10.1103/PhysRevLett.117.023001 | Spin-orientation UFF test with ⁸⁷Rb |
| Zhou, Luo, Chen, Duan, Hu, Phys. Rev. A 93, 043610 (2016) | 10.1103/PhysRevA.93.043610 | Wavefront aberration via Raman-beam-diameter modulation |
| Luo, Zhang, Zhang, Duan, Hu, Chen, Zhou, Rev. Sci. Instrum. 90, 043104 (2019) | 10.1063/1.5053132 | Compact 1560-nm-doubled laser system for portable HUST gravimeter |
| Zhang, Ren, Yan, Cheng, Zhou, Gao, Luo, Zhou, Hu, Opt. Express 29, 30007 (2021) | 10.1364/OE.434375 | BEC-source gravimeter; 76(4)% fringe contrast at T = 80 ms; 6 µGal at 3000 s |
| Zhang, Xu, Sun, Shu, Luo, Cheng, Hu, Zhou, AIP Advances 11, 115223 (2021) | 10.1063/5.0068761 | Car-based portable HUST gravimeter (T = 29 ms; 1.9 mGal/√Hz) |
| Xu, Cui, Qi, Chen, Deng, Luo, Zhang, Tan, Shao, Zhou, Duan, Hu, Metrologia 59, 055001 (2022) | 10.1088/1681-7575/ac8258 | **First full HUST systematic-error budget**: 24 µGal/√Hz, combined uncertainty 3 µGal, ICAG-2017 equivalence 1.3 µGal |
| Zhang, Chen, Shu, Xu, Cheng, Luo, Hu, Zhou, Phys. Rev. Applied 20, 014067 (2023) | 10.1103/PhysRevApplied.20.014067 | Bragg atom gravimeter, 2.24 × 10⁻⁹ g/√Hz, Lorentz-violation test |
| Duan, Geng, Luo, Xu, Hu, arXiv:2412.14438 (2024) | arXiv:2412.14438 | Fast Raman-tilt determination |

The Wuhan **10-m apparatus** is a separate WIPM-CAS project of M.-S. Zhan and colleagues, distinct from HUST:
- Zhou, Xiong, Yang, Tang, Peng, Hao, Li, Liu, Wang, Zhan, Gen. Relativ. Gravit. 43, 1931 (2011), DOI 10.1007/s10714-011-1167-9 - first announcement of the 10-m apparatus, with the smaller precursor reaching "2.0 × 10⁻⁷ g for 1 s and 4.5 × 10⁻⁹ g for 1,888 s. The absolute g value was derived with a difference of 1.6 × 10⁻⁷ g compared to the gravity reference value."  
- Zhou, Long, Tang, Chen, Gao, Peng, Duan, Zhong, Xiong, Wang, Zhang, Zhan, Phys. Rev. Lett. 115, 013004 (2015), arXiv:1503.00401 - ⁸⁵Rb-⁸⁷Rb double-diffraction WEP test: "The statistical uncertainty of the experimental data for Eötvös parameter η is 0.8 × 10⁻⁸ at 3200 s. With various systematic errors corrected the final value is η = (2.8 ± 3.0) × 10⁻⁸. The major uncertainty is attributed to the Coriolis effect."  
- Zhou, He, Yan, Chen, Gao, Duan et al., Phys. Rev. A 104, 022822 (2021) - joint mass-and-energy WEP test at 10⁻¹⁰ level.

---

## Details

**Source pedigree.** Hu 2013 full text is paywalled at APS and has no arXiv preprint. Open-source verbatim quotation is limited to the abstract (4.2 µGal/√Hz, 1.2 µGal/√Hz residual vibration, ⁸⁷Rb, the "2D MOT was added" claim). All non-abstract parameter values originate from the HUST group's own 2015 review (Zhou et al., Chin. Phys. B 24, 050401), which describes the same apparatus and cites Hu 2013 as ref. [72]. Wording is the review's, not Hu 2013's, but the authors overlap (M.-K. Zhou, X.-C. Duan, L.-L. Chen, Z.-K. Hu) and the section explicitly labels the figures with the Hu 2013 data.

**Cross-source consistency.** Multiple later citing papers consistently report 4.2 µGal/√Hz and 87Rb for Hu 2013; no source disputes T = 300 ms; the HUST group's later portable gravimeters use shorter T (29-55 ms) and warmer T_cloud (~2-5 µK) - those values must not be transplanted into a Hu 2013 simulation.

**Unit-conversion checks**:
- 4.2 µGal/√Hz × 10⁻⁸ m s⁻² per µGal = **4.2 × 10⁻⁸ m s⁻² Hz⁻¹ᐟ²**; in g: 4.2 × 10⁻⁸ / 9.80 ≈ **4.3 × 10⁻⁹ g/√Hz**.  
- 1.2 µGal/√Hz = **1.2 × 10⁻⁸ m s⁻² Hz⁻¹ᐟ²**.  
- 0.5 µGal at 100 s = **5 × 10⁻⁹ m s⁻²**.  
- Launch velocity 3.83 m s⁻¹ ⇒ apex h = v²/(2g) = (3.83)²/(2 × 9.793 m s⁻²) ≈ **0.749 m**, consistent with quoted 0.75 m.  
- k_eff = 4π / 780.241 nm ≈ **1.611 × 10⁷ rad m⁻¹**.  
- Interferometer scale factor: k_eff·T² = 1.611 × 10⁷ × 0.0900 s² ≈ **1.45 × 10⁶ rad / (m s⁻²) ≈ 1.45 × 10⁻² rad / µGal**.  
- Mean phase: Φ = k_eff·g·T² = 1.611 × 10⁷ × 9.793 × 0.090 ≈ **1.42 × 10⁷ rad** (unwrapped) - chirp linearizes it.

**Coriolis intuition.** Wuhan latitude φ ≈ 30.5°, Ω = 7.292 × 10⁻⁵ rad s⁻¹. For horizontal velocity component v_h ≤ 1 cm s⁻¹ (typical cold-atom selection), Coriolis acceleration 2Ω v_h cos φ ≲ 1.3 × 10⁻⁶ m s⁻² ≈ 0.1 µGal - sub-µGal with rotating-mirror compensation as later implemented at HUST. Hu 2013 itself does not state a Coriolis correction.

**Gravity gradient.** Earth's vertical gradient γ ≈ 3.086 × 10⁻⁶ s⁻². The standard correction γ (z₀ + v₀ T) T² is at the ≈ µGal level with the Hu-2013 trajectory; not numerically tabulated in Hu 2013.

---

## Recommendations for qgrav v1.1.0 validation

**Adopt the following baseline parameter set** when reproducing Hu 2013 in simulation. Each row is tagged with source quality so you can mark which assertions are verbatim from Hu 2013 and which are sourced from the HUST-group's own 2015 review.

| qgrav input | Value (SI) | Source |
|---|---|---|
| Isotope | ⁸⁷Rb (D₂, 780.241 nm) | Hu 2013 abstract (verbatim) |
| T (pulse separation) | 0.300 s | HUST review Chin. Phys. B 24, 050401 (2015), Fig. 7, citing Hu 2013 |
| 2T (total interrogation) | 0.600 s | derived |
| τ_π (π-pulse duration) | not in open sources | needs paywalled body |
| Cycle time T_c | 1.0 s | HUST 2015 review (verbatim) |
| MOT load time | 0.200 s | HUST 2015 review (verbatim) |
| N_atoms (MOT) | 3 × 10⁹ | HUST 2015 review (verbatim) |
| N_atoms (interferometer) | 5 × 10⁷ | HUST 2015 review (verbatim) |
| Cloud T transverse | 7 × 10⁻⁶ K | HUST 2015 review (verbatim) |
| Cloud T longitudinal (post-selection) | 3 × 10⁻⁷ K | HUST 2015 review (verbatim) |
| Launch velocity | 3.83 m s⁻¹ | HUST 2015 review (verbatim) |
| Apex above MOT | 0.75 m | HUST 2015 review (verbatim) |
| Single-photon detuning |Δ| | 1.5 × 10⁹ Hz from F=2→F'=3 cooling line | HUST 2015 review (verbatim); sign not in open sources |
| Chirp rate α | 25.14 MHz s⁻¹ (closest open value: 25.12 MHz/s in Tao et al. Photonics 7, 32, 2020) | flag as unverified for Hu 2013 |
| Raman phase noise | < −100 dBc/Hz, 200 Hz-200 kHz | HUST 2015 review (verbatim) |
| Detection | normalized fluorescence | HUST 2015 review (verbatim) |
| Active isolator f₀ (closed-loop) | 0.016 Hz | Zhou et al. PRA 86, 043630 (2012); HUST 2015 review |
| Residual vibration < 2 Hz | < 1 × 10⁻⁸ m s⁻²/√Hz (≈ 10⁻⁹ g/√Hz) | HUST 2015 review (verbatim) |
| Vibration-contribution to g | 1.2 × 10⁻⁸ m s⁻²/√Hz | Hu 2013 abstract (verbatim) |
| Raman-phase-noise contribution | 8 × 10⁻⁹ m s⁻²/√Hz | HUST 2015 review |
| Detection-noise contribution (per shot) | 3.3 × 10⁻⁸ m s⁻²/√Hz | HUST 2015 review |
| **Target σ(g) at 1 s** | **4.2 × 10⁻⁸ m s⁻²/√Hz** | Hu 2013 abstract (verbatim) |
| σ(g) at 100 s | < 5 × 10⁻⁹ m s⁻² | HUST 2015 review |
| Drops integrated | ~7 × 10⁴ to 1.4 × 10⁵ over 40 h | derived from HUST 2015 review |

**Staged validation plan**

1. **Stage 1 - kinematics & phase scaling.** Verify qgrav reproduces Φ = k_eff·g·T² = 1.45 × 10⁶ rad / (m s⁻²) and the chirp rate α₀ = k_eff·g / (2π) ≈ 25.1 MHz s⁻¹ that nulls the phase. **Pass threshold:** ≤ 10⁻⁶ relative error in Φ vs analytic formula at fixed g.

2. **Stage 2 - noise budget.** Inject (a) Raman phase noise with PSD floor −100 dBc/Hz across 200 Hz-200 kHz, (b) seismometer-residual PSD scaled to ≤ 10⁻⁸ m s⁻²/√Hz below 2 Hz, (c) shot noise from N = 5 × 10⁷ and C ≈ 0.15. **Pass threshold:** σ_g(1 s) ∈ [3.5, 5.0] µGal/√Hz and σ_g(100 s) ≤ 0.7 µGal. If σ_g(1 s) is high by > 25%, recheck the chirp rate, π-pulse duration, and contrast assumption.

3. **Stage 3 - systematics.** Skip for Hu 2013 (no published per-effect table). For an accuracy benchmark, instead reproduce the HUST-QG (Xu et al. Metrologia 2022) per-effect budget (target combined uncertainty 3 µGal) or the LNE-SYRTE / SU-Berlin GAIN budgets.

4. **Stage 4 - long-baseline benchmark (optional).** If qgrav must validate a 10-m geometry, use Zhou et al. PRL 115, 013004 (2015) for the WIPM-CAS 10-m apparatus; do not conflate with Hu 2013.

**Decision thresholds for revisiting assumptions**:
- > 25% miss on σ_g(1 s) → obtain paywalled Hu 2013 body to retrieve τ_π, beam waists, and exact contrast.
- > 50% miss → suspect Raman detuning sign/reference level (the 1.5 GHz number is well attested but red vs blue is unconfirmed for Hu 2013).
- Any qualitative disagreement in fringe shape → check the assumed gravity gradient correction γ ≈ 3.086 × 10⁻⁶ s⁻² and apex height 0.75 m.

---

## Caveats

1. **Premise correction.** Hu 2013 PRA 88, 043610 is **not** a 10-m drop tower. It is a HUST cave-laboratory fountain with T = 300 ms and a 0.75-m apex. The Wuhan 10-m apparatus is a separate WIPM-CAS project (M.-S. Zhan, J. Wang, L. Zhou). Mixing the two will produce inconsistent simulation parameters. Adjust the qgrav v1.1.0 test docket accordingly.
2. **Paywall.** Hu 2013 full text is paywalled and has **no arXiv preprint** (verified via ADS bibcode 2013PhRvA..88d3610H). All verbatim quotes from Hu 2013 are limited to the abstract on the APS landing page. Non-abstract parameters are sourced from the HUST group's own review (Zhou et al., Chin. Phys. B 24, 050401, 2015) - same group, overlapping authors, same apparatus, but the wording is the review's, not Hu 2013's.
3. **No systematic-error budget exists in Hu 2013.** The user's task item #9 cannot be answered from the open literature in the form requested; it likely is not in the paper at all. The first HUST systematic-error budget is Xu et al., Metrologia 59, 055001 (2022) - a different apparatus (HUST-QG), 9 years later.
4. **Raman detuning sign and reference level** (red vs blue; relative to F'=1, 2, or 3) are not unambiguously confirmable for Hu 2013 from open sources. The 1.34-GHz / red-detuned 0.95 GHz from F'=0 used in Tao et al. Photonics 7, 32 (2020) is a different (portable) HUST laser system and **must not be carried into a Hu 2013 simulation** without direct verification.
5. **Unverified for Hu 2013:** π-pulse Rabi duration τ_π, Raman beam waist and intensity, MOT and Raman beam diameters, detection-beam geometry, exact chirp-rate value (25.14 vs 25.12 MHz/s). Treat as TBD pending paywalled access.
6. **Drop count for the Allan deviation** is not stated explicitly in Hu 2013. Inferred from "40 h continuous, 2 shots per 2 s" in the HUST review: ≈ 7 × 10⁴ binned pairs ≈ 1.4 × 10⁵ raw drops.
7. **Hedging:** the headline "4.2 μGal/√Hz" is explicitly preceded by "about" in the abstract - keep this uncertainty band in qgrav unit tests.
8. **Subsequent gradiometer sensitivity 670 E/√Hz** is verbatim from Duan et al. PRA 90, 023617 (2014). The differential-acceleration figure quoted in some review papers (~4 × 10⁻⁹ g/√Hz) is not in the PRA 90 abstract and should be treated as derived/secondhand unless confirmed against the paywalled body.