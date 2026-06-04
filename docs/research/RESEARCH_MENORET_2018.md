# Simulation Parameters from Ménoret et al. (2018) for qgrav Validation

**Primary source (verbatim throughout):** V. Ménoret, P. Vermeulen, N. Le Moigne, S. Bonvalot, P. Bouyer, A. Landragin, B. Desruelle, "Gravity measurements below 10⁻⁹ g with a transportable absolute quantum gravimeter," *Scientific Reports* **8**, 12300 (2018). DOI: 10.1038/s41598-018-30608-1. URL: https://www.nature.com/articles/s41598-018-30608-1

## TL;DR (whole report)

- **The Ménoret 2018 paper provides full simulator parameters for the AQG-A01 except the Raman beam waist, which is never numerically stated.** Key values: T = 60 ms; ~10⁷ ⁸⁷Rb atoms; cycle ≈ 500 ms (2 Hz); λ = 780 nm; k_eff ≈ 1.61 × 10⁷ m⁻¹; contrast C = 0.40; detection SNR = 150 (effective SNR = 60). Pyramid single-beam geometry; mu-metal shielded vacuum chamber; measurement height 55 cm; verticality known to ~10 µrad.
- **Vibration handling is feed-forward active correction of the Raman laser phase using a hard-mounted Nanometrics Titan classical accelerometer — NOT a passive table, NOT an active isolation platform, and NOT post-correction.** No mechanical isolation device is used; the gravimeter sits directly on the ground / pillar. The Larzac sensitivity number cited in the prompt — **750 nm s⁻² Hz⁻¹/²** — is the as-operated short-term sensitivity during the 2017 month-long campaign at the Larzac plateau (NOT LSBB Rustrel), and is one of *five* distinct sensitivity numbers reported (best-Larzac 500; campaign-Larzac 750; Talence quiet 600; Talence typical 700; abstract/nominal 500). The long-term stability is below 10 nm s⁻² (= 1 µGal ≈ 1 × 10⁻⁹ g), reached at τ ≈ 24 h.
- **Tide, atmospheric pressure (admittance −3 nm s⁻² hPa⁻¹), tilt, and microwave-quartz-drift corrections were applied before the Allan deviation; polar motion and ocean loading are in the software pipeline but not explicitly stated to have been applied to the analyzed data.** Three peer-reviewed follow-up evaluations (Cooke 2021, Antoni-Micollier 2022, Glässel 2025) and one fleet-wide proceedings paper (Antoni-Micollier 2024) extend the benchmarks: the modern AQG fleet (16 units, AQG-A01–A04 and AQG-B01–B12) reproducibly achieves < 800 nm s⁻² Hz⁻¹/² short-term in noisy conditions and < 500 nm s⁻² Hz⁻¹/² at quiet sites, with long-term stability < 10 nm s⁻² independent of site — i.e. the 2018 numbers are still the target.

---

## Key Findings

1. The Ménoret 2018 paper IS the authoritative simulator-parameter source for the AQG-A01; the published Exail/iXblue/Muquans datasheets do **not** expose T, n_atoms, cycle time, or beam waist values that a simulator needs.
2. The 750 nm s⁻² Hz⁻¹/² Larzac value is real but **not** the instrument's best — it is the as-operated 2017-campaign value, degraded from the 500 nm s⁻² Hz⁻¹/² instrument-best by a transient atom-number reduction. The paper states this issue was later resolved.
3. The 1-day standard deviation differs by less than 25% across the two extreme-noise sites (Talence: 8.5 nm s⁻², Larzac: 9.4 nm s⁻²) — long-term stability is **site-independent** at ≈ 1 µGal, exactly the central claim.
4. Allan deviation curve numerical values at τ = 10 s, 100 s, 1000 s are **not tabulated**; only the white-noise asymptote (750 nm s⁻² Hz⁻¹/² → τ = 1 s) and three averaging-time anchors (σ(10 min) = 25.2 nm s⁻²; σ(1 h) = 10.7 / 8.5 nm s⁻²; σ(1 day) = 9.4 nm s⁻²) are stated as text.
5. The vibration scheme is feed-forward active phase correction with a Nanometrics Titan accelerometer, real-time, no mechanical isolation. The Etna AQG-B successor replaced the Titan with a Nanometrics Trillium Compact 120 s broadband seismometer — a hardware deviation that should NOT be copied for a Larzac replica.
6. Corrections actually applied to the analysis dataset: **tilt + microwave-quartz drift + atmospheric pressure (admittance = −3 nm s⁻² hPa⁻¹) + locally-trained synthetic Earth tide**. Polar motion and ocean loading exist in the software but are not explicitly applied to the analyzed series.
7. The Raman beam waist is **never given numerically by Ménoret 2018**. For a comparator only (different instrument): Wu et al., *Sci. Adv.* 5, eaax0800 (2019), DOI 10.1126/sciadv.aax0800, states verbatim: *"the 25-mW Raman beam has a waist of 5 mm."* Do not assume the AQG-A01 value matches.

---

## Details — Section by Section

## 1. AQG-A01 Instrument Specifications

**TL;DR:** T = 60 ms, ~10⁷ ⁸⁷Rb atoms per cycle, ~500 ms cycle time, λ ≈ 780 nm, k_eff ≈ 1.61 × 10⁷ m⁻¹, contrast C = 0.40, detection SNR = 150. **The paper does NOT state a Raman beam waist.** The current Exail datasheet does not publish T, n_atoms, cycle time, or beam waist.

### 1A. Paper-reported values (Ménoret et al. 2018)

- **Interrogation time T:** *"the the [sic] atoms are in near-perfect free fall for an interrogation time of T = 60 ms."* → T = 6.0 × 10⁻² s.
- **Raman pulse durations:** *"three counterpropagating Raman pulses of duration 10, 20 and 10 μs in a π/2 − π − π/2 configuration."* → τ_π/2 = 1.0 × 10⁻⁵ s; τ_π = 2.0 × 10⁻⁵ s.
- **Atom number per cycle:** *"Approximately 10⁷ atoms are loaded in a magneto-optical trap (MOT) inside the pyramid and cooled down to 2 μK."* → n_atoms ≈ 1 × 10⁷ ⁸⁷Rb atoms.
- **Atomic temperature:** *"below 2 μK"* in optical molasses; measured by Raman spectroscopy.
- **MOT loading time:** *"we load 10⁷ ⁸⁷Rb atoms in a magneto-optical trap (MOT) in 250 ms."*
- **Pre-interferometer free-fall:** *"After approximately 30 ms (4.4 mm) of free-fall, the atoms exit the pyramidal reflector and we apply the π/2 − π − π/2 sequence."*
- **Cycle / repetition rate:** ≈ 2 Hz → cycle ≈ 0.5 s (see Section 3).
- **Wavelength and species:** *"the lasers are tuned close to the D2 line of ⁸⁷Rb, with a wavelength λ ≈ 780 nm."*
- **Effective wavevector k_eff:** *"k_eff = 4π/λ ≈ 16 × 10⁶ m⁻¹ is the effective wavevector of the two-photon transition."*  
  Arithmetic: k_eff = 4π / (780 × 10⁻⁹ m) = 12.566 / 7.80 × 10⁻⁷ = **1.611 × 10⁷ m⁻¹** ≈ 16.1 × 10⁶ m⁻¹ ✓
- **Frequency chirp α:** *"α ≈ 25 MHz.s⁻¹ is a frequency chirp applied to the Raman lasers to compensate the Doppler effect."* → α ≈ 2.5 × 10⁷ Hz s⁻¹.  
  Check: α = k_eff·g/(2π) = (1.611 × 10⁷ × 9.81) / (2π) = 1.581 × 10⁸ / 6.283 = **2.516 × 10⁷ Hz s⁻¹** ✓
- **Contrast C:** *"τ = 10 μs, T = 60 ms, C = 40%"* → C = 0.40.
- **Detection SNR:** *"a detection signal-to-noise ratio of 150."*
- **Effective SNR and single-shot floor:** *"A contrast C of 40% and a detection signal-to-noise ratio of 150 correspond to an effective signal-to-noise ratio (SNR) of 0.4 × 150 = 60. … With the previous parameters, δg/g ≈ 3 × 10⁻⁸. This constitutes the single-shot sensitivity floor of the instrument."*  
  Arithmetic: δg/g = 1/(k_eff · g · T² · SNR) = 1/(1.61×10⁷ · 9.81 · (0.060)² · 60) = 1/(3.41 × 10⁷) ≈ **2.93 × 10⁻⁸** ✓ → δg_single-shot ≈ 2.94 × 10⁻⁷ m s⁻² ≈ **294 nm s⁻² per shot**.
- **Detection geometry:** *"At the bottom of the chamber (150 mm below the position of the trap), we measure the proportion of atoms in each output port."*
- **Verticality control:** verticality error ~100 µrad in install; tiltmeter offset known to better than 10 µrad.
- **Measurement height:** 55 cm above ground (48.8 cm above tripod by design; tripod height measured to 1 mm).
- **Magnetic shielding:** two layers of mu-metal.
- **k-reversal:** *"We also periodically reverse the orientation of the effective Raman wavevector to reject the systematic effects that do not depend on the sign of k_eff."*
- **Laser linewidth:** 12 kHz Lorentzian (per laser).
- **Laser long-term frequency stability:** *"the standard deviation over four days is 27 kHz"*; worst-case per-laser < 30 kHz rms.
- **Pyramid wavefront quality:** *"better than λ/80 (peak-to-valley, 780 nm) in the center region."*
- **Fiber output power per Raman:** *"At the fiber output, the power in each wavelength is approximately 150 mW and polarization extinction ratio is higher than 20 dB."*
- **⚠ Raman beam waist (1/e² radius):** **NOT STATED NUMERICALLY anywhere in the paper text.** For comparator only (different instrument): Wu et al., *Sci. Adv.* 5, eaax0800 (2019), DOI 10.1126/sciadv.aax0800, states verbatim *"the 25-mW Raman beam has a waist of 5 mm."* This number is **not** authoritative for the AQG-A01.

### 1B. Vendor datasheet values (Exail, accessed 2026-05-27)

Source: Exail "Quantum gravimeters" product page (https://www.exail.com/product/quantum-gravimeters) and family page (https://www.exail.com/product-family/quantum-and-metrology-instruments-photonics).

- *"performs measurement at a level of 10⁻⁸ m/s² (1 μGal) in terms of sensitivity, stability and repeatability."*
- *"continuous data acquisition from a few seconds to several years."*
- *"The AQG comes in 2 versions: the AQG-A for indoor use and the AQG-B for field measurements."*
- *"efficiently rejects ground vibration noise with an active compensation technique that does not require any mechanical isolation device or superspring."*
- **⚠ The current public Exail datasheet does NOT publish numerical values for T, n_atoms per cycle, cycle time, or Raman beam waist.** These remain accessible only via the peer-reviewed literature.

### 1C. AQG-B variant parameters (Antoni-Micollier et al. 2022)

DOI: 10.1029/2022GL097814. *"The measurement sequence of the AQG-B includes four main steps, that are repeated at a frequency of 1.85 Hz (Ménoret et al., 2018; Carbone et al., 2020). 1: 10⁶ atoms are magneto-optically trapped during 270 ms and cooled down to 2 µK in optical molasses."*

→ AQG-B: **1.85 Hz** (cycle 540 ms); **10⁶ atoms** (10× fewer than AQG-A01); MOT 270 ms (vs. 250 ms). Use these only for AQG-B validation, not for the original Ménoret-2018 Larzac replica.

---

## 2. Vibration-Isolation Method at the Larzac Measurement

**TL;DR:** Real-time **active feed-forward correction of the Raman laser phase** using a hard-mounted **Nanometrics Titan** classical accelerometer. **No passive seismic isolation table, no active isolation platform, no superspring.** The accelerometer signal is bandpass-filtered (0.05 Hz – 1 kHz), digitized, weighted by the triangular sensitivity function of the atom interferometer, and a phase correction is applied to the Raman lasers less than 1 ms before the final π/2 pulse — i.e., within the same measurement cycle.

**Exact passages:**

- *"A high-performance accelerometer is attached to the top of the vacuum chamber, as close as possible to the pyramidal reflector. Its signal is used to apply a real-time correction to the laser phase, in order to reject seismic noise."* (Figure 1 caption.)
- *"A high-performance classical accelerometer is attached to the top of the vacuum chamber in order to implement an active compensation of vibrations and to make the instrument robust against seismic noise without the need of an isolation device."* (Sensor head.)
- *"This allows the instrument to be installed directly on the ground without any vibration damping."* (Discussion.)
- *"The signal from the classical accelerometer (Nanometrics Titan) is filtered by a bandpass filter with cut-off frequencies f_hp = 0.05 Hz and f_lp = 1 kHz. … Since the atom interferometer behaves as a second-order filter with a low-pass cut-off frequency of 1/2T = 8.3 Hz, f_lp is chosen significantly higher."* (Methods.)
- *"Less than 1 ms before the last Raman pulse, the calculated correction is applied to the phase lock loop of the Raman lasers to compensate the vibration phase shift."*
- *"The integrated seismic noise typically corresponds to phase shifts of 2.3 rad rms (20 rad peak-to-peak), meaning the interference fringes are completely blurred. Using this real-time compensation, we recover the fringes and keep the residual acceleration noise to a level of approximately 36 mrad rms (250 mrad pk-pk), corresponding to a rejection factor higher than 60."*
- **Larzac pillar installation:** *"The AQG-A01 was installed on a dedicated concrete pillar directly built on the bedrock."* (No separate isolator.)

**Note on successor instruments:** Antoni-Micollier et al. (2022) report that for the Etna AQG-B deployment the standard Titan accelerometer was *"replaced by a broadband seismometer (Nanometrics Trillium Compact 120 s)"*. This is **not** what was used at Larzac in 2017; keep the Nanometrics Titan + standard hybridization scheme for the Ménoret-2018 Larzac replica.

---

## 3. Cycle Time / Repetition Rate

**TL;DR: Sub-1-second, ≈ 2 Hz, cycle ≈ 500 ms.**

**Exact passages:**

- *"The resulting sensor measures gravity at a 2 Hz repetition rate with a sensitivity of 500 nm.s⁻² .Hz⁻¹/²."* (Introduction.)
- *"since the instrument's repetition rate is on the order of 2 Hz."* (Measurement principle.)
- *"gravity data are acquired by the AQG at a rate of approximately 2 Hz."* (Sensitivity and stability.)
- *"Each point corresponds to 1 measurement cycle (approx. 500 ms)."* (Figure 6 caption.)
- *"f_hp has been chosen much lower than the cycle frequency of the AQG (2 Hz)."* (Methods.)

**Arithmetic:** 2 Hz → T_cyc = 1/2 = 0.500 s. Internal accounting: MOT 250 ms + state-selection + 30 ms pre-interferometer free-fall + 2T = 120 ms + detection ≈ 0.4–0.5 s ✓.

**Successor:** AQG-B at Etna runs at **1.85 Hz** (cycle ≈ 540 ms) per Antoni-Micollier 2022.

---

## 4. The Larzac Sensitivity Value — and ALL Other Sensitivity Numbers in the Paper

**TL;DR:** The 750 nm s⁻² Hz⁻¹/² value is the **as-operated** 2017-campaign Larzac short-term sensitivity, NOT the instrumental noise floor. Five distinct numbers are stated.

### 4A. All distinct sensitivity numbers

| Context | Sensitivity (white-noise extrapolation to τ = 1 s) | Verbatim passage |
|---|---|---|
| **Larzac — instrument best** | **500 nm s⁻² Hz⁻¹/²** | *"The best sensitivity achieved by our instrument in Larzac is 500 nm.s⁻² .Hz⁻¹/² and is mainly limited by imperfections in the compensation of vibrations."* |
| **Larzac — 2017 month-long campaign** | **750 nm s⁻² Hz⁻¹/²** | *"During the measurement campaign of 2017, the gravimeter was operated at a slightly lower sensitivity of 750 nm.s⁻² .Hz⁻¹/² due to a decrease of the number of atoms loaded in the interferometer."* |
| **Talence — quiet 5-day window (Christmas 2016)** | **~600 nm s⁻² Hz⁻¹/²** | *"The sensitivity of the instrument during the five days was approximately 600 nm.s⁻² .Hz⁻¹/², mainly limited by the residual vibration noise."* |
| **Talence — typical operation** | **~700 nm s⁻² Hz⁻¹/²** | *"When the noise is higher, the sensitivity is typically 700 nm.s⁻² .Hz⁻¹/²."* |
| **AQG nominal (abstract/intro)** | **500 nm s⁻² Hz⁻¹/²** | *"The resulting sensor measures gravity at a 2 Hz repetition rate with a sensitivity of 500 nm.s⁻² .Hz⁻¹/² and a long term stability below 10 nm.s⁻²."* |
| **FG5#228 comparison (Larzac, 36 s effective drop interval)** | **~450 nm s⁻² Hz⁻¹/²** | *"the FG5 has a slightly better short-term sensitivity of approximately 450 nm.s⁻² .Hz⁻¹/²"* |

### 4B. Definition of "sensitivity" used in the paper (Methods)

*"The sensitivity 𝒮 of the instrument, expressed in nm.s⁻² .Hz⁻¹/², is the extrapolation of the white noise behaviour to τ = 1 s. This can be conveniently interpreted as the statistical uncertainty obtained after averaging data over 1 s."*

### 4C. Unit conversions for the Larzac 750 nm s⁻² Hz⁻¹/² value

- 750 nm s⁻² Hz⁻¹/² = 750 × 10⁻⁹ m s⁻² Hz⁻¹/² = **7.50 × 10⁻⁷ m s⁻² Hz⁻¹/²**.
- 1 µGal = 10⁻⁸ m s⁻² = 10 nm s⁻². 750 nm s⁻² = 750/10 = **75 µGal** → **75 µGal Hz⁻¹/²**.
- In g: 7.50 × 10⁻⁷ / 9.80665 = **7.65 × 10⁻⁸ g Hz⁻¹/²**.

For the instrument-best 500 nm s⁻² Hz⁻¹/²: 5.0 × 10⁻⁷ m s⁻² Hz⁻¹/² = 50 µGal Hz⁻¹/² = 5.10 × 10⁻⁸ g Hz⁻¹/².

### 4D. Caveat

The paper distinguishes the instrumental best (500) from the as-operated campaign value (750). Use 750 nm s⁻² Hz⁻¹/² for a faithful 2017 Larzac replica; use 500 for the instrument-limit benchmark. The transient atom-number reduction *"has since been resolved."*

---

## 5. Deployment Sites and Spread of Sensitivity/Stability Numbers

**TL;DR:** Two characterized sites: (i) **Muquans laboratory in Talence** (Bordeaux suburb, noisy second-floor inner-city building on sediments) and (ii) **Larzac plateau observatory** (low-noise concrete pillar on bedrock, southern France). A comparative dataset from FG5#228 at the same Larzac pillar. **NOT LSBB Rustrel** — the 2018 paper does not mention LSBB.

### 5A. Site descriptions

- **Talence:** *"This site features a high level of microseismic noise due to its proximity to the ocean and its location on the second floor of an inner-city building constructed on sediments."*
- **Larzac:** *"This site is dedicated to hydrology studies and local gravity has been measured there by absolute and relative gravimeters on a regular basis since 2006. The Larzac observatory has a very low level of high-frequency vibration noise (i.e. above 1 Hz) compared to Talence."* *"The AQG-A01 was installed on a dedicated concrete pillar directly built on the bedrock."*
- **Within-Larzac repeatability:** three pillars (NE, NW, SE), each measured twice; per-pillar between-visit differences −23.6 / +5.1 / +1.8 nm s⁻².

### 5B. Spread of numbers across the two sites (all from the paper text)

| Metric | Talence (noisy) | Larzac (quiet) |
|---|---|---|
| Short-term sensitivity (τ=1 s) | 600 (quiet 5 d) / 700 (typical) nm s⁻² Hz⁻¹/² | 500 (best) / **750 (campaign)** nm s⁻² Hz⁻¹/² |
| σ at 10 min averaging | 25.2 nm s⁻² | not separately quoted |
| σ at 1 h averaging | 10.7 nm s⁻² | not separately quoted |
| Allan deviation at 1 h, best 24 h | 8.5 nm s⁻² | not separately quoted |
| σ at 1 day averaging | not quoted | **9.4 nm s⁻²** |
| Campaign length | 5 days continuous (Dec 2016) | **1 month continuous (Summer 2017)** with no measurable drift |
| FG5#228 cross-check | n/a | two measurements (25 Jul / 4 Sep 2017) differ by 20 nm s⁻² within statistical uncertainty |

**Interpretation:** The σ(1 day) values are 8.5 vs 9.4 nm s⁻² — within ~10% across the two extreme-noise sites. Long-term stability is therefore **site-independent** at the ≈ 1 µGal floor; only short-term sensitivity is site-dependent (500–750 nm s⁻² Hz⁻¹/²).

### 5C. Successor-instrument extension of the site map

- **AQG#B01 at Larzac (Cooke et al. 2021, DOI 10.5194/gi-10-65-2021):** σ(τ = 1 h) = **10 nm s⁻²** at Larzac (low-noise); **20 nm s⁻² at 1 h** in Montpellier; **26 nm s⁻² at 1 h** in a garage. Repeatability *"better than 50 nm s⁻²"*; small-scale repeatability 3 nm s⁻², σ = 25 nm s⁻². Drift = −0.02 ± 0.04 nm s⁻² d⁻¹ over ≈ 2 months. *"a 100 nm s⁻² gravity change is detected with the AQG#B01 after a rainfall event at the Larzac geodetic observatory (southern France). The data agreed with the gravity changes measured with a superconducting relative gravimeter (GWR, iGrav#002) and the expected gravity change simulated as an infinite Bouguer slab approximation."*
- **AQG-A02 and AQG-B10 at BKG sites (Glässel et al. 2025, DOI 10.1007/s00190-025-01995-x):** *"Our measurements confirm a sensitivity of 500 nm s⁻² Hz⁻¹/² at a quiet site, as specified, equivalent to a precision of 10 nm/s² after 1-h integration time, and a combined uncertainty on the order of 100 nm/s²."* AQG-B10 at Wettzell: 430 nm s⁻² Hz⁻¹/². AQG-A02 at Bad Homburg: 300 nm s⁻² Hz⁻¹/² *"during the night of 30/10/2020 to 01/11/2020, the 1st November being a bank holiday in Germany."*
- **AQG-B at Mt Etna PDN (Antoni-Micollier et al. 2022):** σ(τ = 1 s) ≈ **1,200 nm s⁻² (low tremor)** and **≈ 1,600 nm s⁻² (high tremor)** — 2–3× degraded vs. quiet lab, after switching to the Trillium Compact 120 s seismometer.
- **Fleet-wide reproducibility (Antoni-Micollier et al. 2024, arXiv:2405.10844, published in IEEE Instrumentation & Measurement Magazine):** *"For all units the short-term sensitivity is below 800 nm/s²/τ¹/²"* at the noisy Talence factory site (16 units). *"At a dedicated geodetic site, it is typically better than 500 nm/s²/τ¹/². The long-term sensitivity is better than 10 nm/s² = 1 µGal."*

---

## 6. Allan Deviation Curve (Fig. 5)

**TL;DR:** The paper does **NOT tabulate numerical Allan deviation values at τ = 1, 10, 100, 1000 s.** It shows a curve in **Figure 5** with TWO numerical anchors in text: (i) the white-noise extrapolation to τ = 1 s (**750 nm s⁻² Hz⁻¹/²** for AQG-A01 at Larzac), and (ii) the long-term floor reached around τ ≈ 24 h (**8.5 nm s⁻²** Talence best, **9.4 nm s⁻²** Larzac month-long σ_1day). The "below 10⁻⁹ g" title is supported by these long-term anchors.

### 6A. Qualitative behavior (per text)

- *"the Allan deviation decreases in proportion with the square root of the averaging time τ. In the log-log plot of Fig. 5 this behaviour is characterized by a linear decrease with a slope of −1/2."* (Methods.)
- *"all three data sets exhibit a clear white-noise signature between 100 and 2000 s. The corresponding sensitivities are indicated by the dashed lines: approximately 450 nm.s⁻² .Hz⁻¹/² for the FG5 and 750 nm.s⁻² .Hz⁻¹/² for the AQG measurement in Larzac."*
- *"At timescales longer than 10⁴ s, the data are no longer described by white noise. However, in the three datasets presented here, no significant low-frequency drift is visible."*

### 6B. Numerical anchors in text (use only these)

- **τ → 1 s (white-noise extrapolation):** 750 nm s⁻² Hz⁻¹/² (AQG-A01 Larzac), 450 nm s⁻² Hz⁻¹/² (FG5#228).
- **τ = 10 min, Talence:** σ = 25.2 nm s⁻² — *"The standard deviation over the series is 25.2 nm.s⁻² … when data is averaged over 10 min."*
- **τ = 1 h, Talence 5-day series:** σ = 10.7 nm s⁻² — *"With gravity data averaged over 1 hour, the standard deviation of these measurements is 10.7 nm.s⁻²."*
- **τ = 1 h, Talence best 24 h:** σ = 8.5 nm s⁻² — Figure 4 caption: *"Error bars correspond to the value of the Allan deviation at 1 h of the series (8.5 nm.s⁻²)."*
- **τ = 1 day, Larzac month-long:** σ = 9.4 nm s⁻² — *"When data are averaged over 1 day … the standard deviation of the series is 9.4 nm.s⁻²."*

**⚠ Specific Allan deviation values at τ = 1, 10, 100, 1000 s are NOT in the paper text or any table — they appear only as plotted curves in Fig. 5.** Do not quote them as if authoritative. Model-derived τ⁻¹/² estimates from the 750 nm s⁻² Hz⁻¹/² anchor are:
- σ(τ=1 s) ≈ 750 nm s⁻²
- σ(τ=10 s) ≈ 237 nm s⁻²
- σ(τ=100 s) ≈ 75 nm s⁻²
- σ(τ=1000 s) ≈ 23.7 nm s⁻²
- σ(τ=3600 s) ≈ 12.5 nm s⁻²

These predictions are consistent with the σ(1 h) = 10.7 / 8.5 nm s⁻² text values and the σ(1 day) = 9.4 nm s⁻² text value — but they are simulator-projection numbers, not authoritative paper values.

### 6C. PSD anchor

*"The red (resp. green) dashed line in the Allan plot indicates a sensitivity of 750 (resp. 450) nm.s⁻² .Hz⁻¹/². This corresponds to a white noise level of 1.1 (resp. 0.41) × 10⁶ (nm.s⁻²)² .Hz⁻¹ in the PSD plot."* — Verification: S = 2·𝒮² = 2 × 750² = **1.125 × 10⁶ (nm s⁻²)² Hz⁻¹** ✓.

### 6D. The "below 10⁻⁹ g" floor

1 × 10⁻⁹ g = 1 × 10⁻⁹ × 9.80665 m s⁻² = **9.81 × 10⁻⁹ m s⁻² = 9.81 nm s⁻² ≈ 0.981 µGal**.

Supporting text: *"measure the absolute gravitational acceleration continuously with a long-term stability below 10 nm.s⁻² (1 μGal)"* (Abstract); *"the standard deviation over the series reaches 9.4 nm.s⁻²"* (Larzac 1-day); *"this deviation reduces to 8.5 nm.s⁻²"* (Talence best 24 h). **Integration time at which the floor is reached: τ ≈ 24 h (1 day).**

---

## 7. Data Pre-processing (Corrections Applied Before the Allan Deviation)

**TL;DR:** Four corrections are explicitly applied to the analysis data before Allan-deviation/PSD computation:
1. **Tilt** (continuous monitoring, two tiltmeters)
2. **Microwave-quartz oscillator drift** (periodic Ramsey self-calibration, ~30 s pause)
3. **Atmospheric pressure** (admittance −3 nm s⁻² hPa⁻¹, barometer accuracy 1 hPa)
4. **Synthetic Earth tide** with locally-trained parameters: 9-month CG5 recording at Talence, 3-year superconducting gravimeter recording at Larzac.

**Ocean loading and polar motion** are implemented in the control software (via a TSoft routine) but the paper does NOT explicitly state they were applied to the Talence-5-day or Larzac-month-long Allan deviation datasets.

**Exact passages:**

- *"These data are then averaged to improve statistical uncertainty, and corrected for tilt variations, drifts of the microwave oscillator, and atmospheric pressure using the admittance. Gravity data are also corrected by a synthetic tide, with parameters determined by analyzing a 9-month recording by a CG5 relative gravimeter in Talence, and a 3-year recording performed by a superconducting gravimeter in Larzac."* (Sensitivity and stability section.)
- **Pressure admittance value:** *"Since pressure admittance is of the order of −3 nm.s⁻² .hPa⁻¹, this is sufficient to ensure that the residual effect due to the barometer is lower than 10 nm.s⁻²."* (Mitigation of external effects.)
- **Software pipeline (full):** *"the software calculates tilts, atmospheric pressure, vertical gravity gradients, polar motion and quartz oscillator frequency drifts. Earth tide and ocean loading corrections are also implemented, by calling a TSoft routine."* (Instrument control.)
- **Tide model precision check:** *"the tide models we use on both sites are precise enough at these frequencies, and because there were no measurable hydrological or geophysical events during our measurements."*
- **Microwave self-calibration:** *"the gravity measurement is paused for approximately 30 s and the instrument switches from a Raman to a Ramsey π/2 − π/2 sequence … allows us to measure the frequency of the oscillator with an uncertainty lower than 1 part in 10¹⁰. We correct the value of α and g accordingly, making the residual contribution lower than 1 nm.s⁻²."*

**Inferred order:** raw single-shot g → tilt → microwave/clock → pressure (−3 nm s⁻² hPa⁻¹ × ΔP) → synthetic Earth tide → averaging into 10-min/1-h/1-day bins → Allan deviation. The k-reversal averaging happens at the raw-cycle level.

---

## 8. Successor Instruments and Updated Benchmarks

**TL;DR:** Three peer-reviewed evaluations (Cooke 2021, Antoni-Micollier 2022, Glässel 2025) and one IEEE magazine article (Antoni-Micollier et al. 2024) extend the benchmarks. The 1 µGal sensitivity/stability class has held for 8 years across 16 fabricated units; the Ménoret-2018 numbers remain valid simulation targets.

### 8A. Cooke, Champollion, Le Moigne (2021)
Geosci. Instrum. Method. Data Syst. 10, 65–79. DOI: 10.5194/gi-10-65-2021. URL: https://gi.copernicus.org/articles/10/65/2021/

*"The AQG#B01 is the field version follow-up of the AQG#A01 portable absolute quantum gravimeter developed by the French quantum sensor company Muquans."* (Manufacturer at time of publication was Muquans, not Exail.)

- Sampling rate: 2 Hz; *"It is based on the same measurement specifications and overall architecture but underwent a complete system redesign in order to meet outdoor operation requirements."*
- Power: *"Power consumption has been reduced to 250 W."*
- σ(τ = 1 h, Larzac): *"At an integration interval of 1 h, the sensitivity of the AQG#B01 reached 10 nm s⁻², the iGrav#002 shows a higher sensitivity at short timescale, but both the iGrav#002 and the AQG#B01 reach the same level of sensitivity at 24 h."*
- σ at urban (Montpellier): *"approximately 20 nm s⁻² after 1 h; after 24 h it was below 10 nm s⁻²."*
- σ in garage: *"26 nm s⁻² are reached after 1 h of averaging, sensitivity is better than 10 nm s⁻² after 24 h."*
- Drift: −0.02 ± 0.04 nm s⁻² d⁻¹ over ≈ 2 months.
- Repeatability: *"better than 50 nm s⁻²"* (abstract); small-scale 3 nm s⁻², σ = 25 nm s⁻².
- Geophysical demonstration: *"a 100 nm s⁻² gravity change is detected with the AQG#B01 after a rainfall event at the Larzac geodetic observatory (southern France). The data agreed with the gravity changes measured with a superconducting relative gravimeter (GWR, iGrav#002) and the expected gravity change simulated as an infinite Bouguer slab approximation."*
- **Important comparability note:** Cooke et al. report sensitivity only as Allan deviation at fixed integration times (1 h, 24 h), NOT in nm s⁻² Hz⁻¹/² units; **there is no direct apples-to-apples replacement of the Ménoret 2018 "750 nm s⁻² Hz⁻¹/²" Larzac figure** in this paper.

### 8B. Antoni-Micollier, L. et al. (2022)
Geophys. Res. Lett. 49(13), e2022GL097814. DOI: 10.1029/2022GL097814. URL: https://agupubs.onlinelibrary.wiley.com/doi/full/10.1029/2022GL097814.

Updated numbers (AQG-B03 at Pizzi Deneri observatory, ~2.5 km from Mt Etna active craters):

- Cycle rate / atoms: *"repeated at a frequency of 1.85 Hz … 10⁶ atoms are magneto-optically trapped during 270 ms and cooled down to 2 µK."*
- Allan deviation at τ = 1 s: *"approximately 1,200 and 1,600 nm/s² at 1 s, for the subintervals of low and high tremor, respectively, corresponding to only a 2 to 3-fold degradation with respect to a quiet laboratory environment."*
- Vibration-channel change: *"The vibration rejection system was therefore optimized by replacing the accelerometer with a broadband seismometer (Nanometrics Trillium Compact 120 s)."*
- Detected gravity-change amplitudes: *"a few tens and a few hundreds of nm/s²"*.
- **Long-term floor at PDN appears only in Figure 2c / Supporting Information S4; no single text value is recoverable verbatim from this source.**

### 8C. Glässel, J. et al. (2025)
J. Geod. 99, 73. DOI: 10.1007/s00190-025-01995-x. URL: https://link.springer.com/article/10.1007/s00190-025-01995-x

BKG operational evaluation at Wettzell and Bad Homburg:

- *"Our measurements confirm a sensitivity of 500 nm s⁻² Hz⁻¹/² at a quiet site, as specified, equivalent to a precision of 10 nm/s² after 1-h integration time, and a combined uncertainty on the order of 100 nm/s², based on a comparison to the local gravity reference function."*
- Measurement heights: AQG-A02 ≈ 56 cm; AQG-B10 ≈ 65 cm (vs. 55 cm in Ménoret 2018).
- Verdict: *"both AQGs do not reach the accuracy of FG5-type gravimeters, but provide advantages for continuous measurements and operation."*

### 8D. Antoni-Micollier, L. et al. (2024)
"Absolute quantum gravimeters and gradiometers for field measurements." Published in **IEEE Instrumentation & Measurement Magazine** (IEEE Xplore document 10654720); also arXiv:2405.10844. Authors: L. Antoni-Micollier, M. Arnal, R. Gautier, C. Janvier, V. Ménoret, J. Richard, P. Vermeulen, P. Rosenbusch, C. Majek, B. Desruelle.

Fleet-wide reproducibility across 16 units (AQG-A01–A04, AQG-B01–B12):

- *"For all units the short-term sensitivity is below 800 nm/s²/τ¹/²"* at the noisy Talence factory site.
- *"At a dedicated geodetic site, it is typically better than 500 nm/s²/τ¹/². The long-term sensitivity is better than 10 nm/s² = 1 µGal."*
- AQG B10 at Wettzell: 430 nm s⁻² Hz⁻¹/²; AQG A02 at Bad Homburg: 300 nm s⁻² Hz⁻¹/² *"during the night of 30/10/2020 to 01/11/2020, the 1st November being a bank holiday in Germany."*
- DQG (Differential Quantum Gravimeter) sister product: cycle 1.08 s for 2T = 240 ms; gravity sensitivity 650 nm s⁻² Hz⁻¹/², gradient sensitivity 56 E Hz⁻¹/². *"the DQG reaches a long-term stability of 0.15 E = 1.5 × 10⁻¹⁰ s⁻²"* (1 E = 10⁻⁹ s⁻² is the spec target, not the achieved figure).

### 8E. Reconciliation table — primary paper vs. successors

| Parameter | Ménoret 2018 AQG-A01 | Cooke 2021 AQG#B01 | Antoni-Micollier 2022 AQG-B03 (Etna) | Glässel 2025 AQG-A02/B10 |
|---|---|---|---|---|
| T | 60 ms | same architecture | not re-stated | not re-stated |
| Atoms / cycle | ~10⁷ | (same) | **10⁶** | not re-stated |
| Cycle / rate | ~500 ms / 2 Hz | 2 Hz | 540 ms / **1.85 Hz** | not re-stated |
| Short-term sensitivity (best) | 500 nm s⁻² Hz⁻¹/² (Larzac nominal) | only Allan-time units | σ(τ=1s) ≈ 1200–1600 nm s⁻² with tremor | 430 (Wettzell) / 300 (Bad Homburg quiet) nm s⁻² Hz⁻¹/² |
| Long-term stability | < 10 nm s⁻² in 24 h | 10 nm s⁻² in 1 h (Larzac) | "few tens to few hundreds nm s⁻²" detected | "10 nm/s² after 1 h" |
| Vibration channel | Nanometrics Titan + real-time phase correction | same | **CHANGED: Nanometrics Trillium Compact 120 s** | same as Ménoret 2018 |

**Conclusion on successors:** The 2018 Larzac short-term sensitivity (750 nm s⁻² Hz⁻¹/²) has not been republished with the AQG-A01 at the same site. Across the production fleet, the short-term sensitivity benchmark remains < 800 nm s⁻² Hz⁻¹/² in noisy environments and < 500 nm s⁻² Hz⁻¹/² at quiet geodetic sites — essentially identical to Ménoret 2018's range, confirming the original numbers as still-valid simulation targets.

---

## 9. Additional Context

### 9A. g-value at Larzac and total uncertainty

The 2018 paper does **NOT publish an absolute g-value at the Larzac pillar.** It only reports the cross-check: *"This was confirmed by two measurements carried out with FG5#228 absolute gravimeter on July 25th 2017 and September 4th 2017. The second FG5 value is lower by 20 nm.s⁻² (within statistical uncertainty), which shows that there has been no significant long-term gravity change over this period."* Inter-pillar values in Table 1 are expressed relative to an arbitrary g₀. The accuracy budget was explicitly still in progress: *"Our target is to characterize all the systematic effects so that the absolute value of g is known with an uncertainty better than 50 nm.s⁻² and can be measured with a repeatability and stability of 10 nm.s⁻²."*

### 9B. Pyramid reflector wavefront

*"its quality is better than λ/80 (peak-to-valley, 780 nm) in the center region used for the atom interferometer."*

### 9C. Vertical gravity gradient

*"gravity gradients are of the order of 3000 nm.s⁻² .m⁻¹."*

---

## Recommendations

**Stage 1 — minimum-viable validation against Ménoret 2018 Larzac:**
Configure qgrav with T = 60 ms, τ_π/2 = 10 µs, τ_π = 20 µs, λ = 780 nm, k_eff = 1.61 × 10⁷ m⁻¹, ⁸⁷Rb D2, 2 Hz cycle, ~10⁷ atoms, MOT 250 ms, 30 ms pre-interferometer free-fall, contrast C = 0.40, detection SNR = 150, effective SNR = 60, periodic k-reversal. Inject a Nanometrics-Titan-like accelerometer noise profile and apply real-time feed-forward Raman-phase correction using the triangular sensitivity function with high-pass at 0.05 Hz and low-pass at 1 kHz. Apply corrections: tilt, pressure (admittance −3 nm s⁻² hPa⁻¹), microwave clock drift, locally-trained Larzac synthetic Earth tide. **Target match:** δg_single-shot ≈ 3 × 10⁻⁸ g; white-noise extrapolation to 1 s = 750 nm s⁻² Hz⁻¹/²; σ(1 day) = 9.4 nm s⁻²; no measurable drift over 30 days. The simulator passes if these three numbers reproduce within ±10–20%.

**Stage 2 — instrument-best benchmark:**
Re-run with full atom number (no transient reduction) and target the 500 nm s⁻² Hz⁻¹/² white-noise floor and 8.5 nm s⁻² σ(24 h). This validates the SNR–floor coupling through paper equation (4).

**Stage 3 — cross-site / cross-noise benchmark:**
Re-run with Talence-like vibration spectra (microseismic, tramway, sediment-supported floor) targeting 600 nm s⁻² Hz⁻¹/² (quiet 5 d) and 700 nm s⁻² Hz⁻¹/² (typical). Confirm vibration rejection factor > 60 (2.3 rad rms → 36 mrad rms post-correction).

**Stage 4 — successor-instrument extension:**
For the AQG-B family, switch to 1.85 Hz / 10⁶ atoms / 270 ms MOT. For Etna-like noise also switch to the broadband Trillium Compact 120 s seismometer model and target σ(τ=1 s) ≈ 1200–1600 nm s⁻². For BKG-like quiet sites, target 300–500 nm s⁻² Hz⁻¹/². For AQG#B01 hydrology demonstrations, target σ(1 h) = 10 nm s⁻² at Larzac and the ability to detect a 100 nm s⁻² step.

**Thresholds that would change these recommendations:**
- If the simulator white-noise floor is more than ±30% off the 750 nm s⁻² Hz⁻¹/² Larzac target with all Stage-1 parameters set, audit the vibration channel and the detection-noise model (eq. 4–5 of the paper) before tuning anything else.
- If σ(1 day) is < 7 nm s⁻² or > 13 nm s⁻², audit the pressure-admittance and Earth-tide-residual treatment.
- If σ(10 min) at Talence is outside 19–32 nm s⁻² (±25% around 25.2), verify (k+, k−) Raman-reversal pair averaging.
- If the rejection factor between raw and corrected vibration phase noise falls below 30, audit the sensitivity-function timing alignment (delay-optimization is mentioned in the paper Methods).

---

## Caveats

1. **The Raman beam waist is not numerically reported by Ménoret et al. (2018) and not exposed in the public Exail datasheet.** If the simulator requires a beam-waist input, treat it as a free parameter constrained by the single-shot SNR, or cite a different instrument explicitly (e.g. Wu et al. 2019, *Sci. Adv.* 5, eaax0800, DOI 10.1126/sciadv.aax0800: *"the 25-mW Raman beam has a waist of 5 mm"* — but this is a different instrument, not the AQG-A01).
2. **The 750 nm s⁻² Hz⁻¹/² Larzac sensitivity is the as-operated 2017-campaign value, degraded from the 500 nm s⁻² Hz⁻¹/² instrument-best by a transient atom-number reduction; the paper states this issue was later resolved.** Choose deliberately and document the choice.
3. **The site is the Larzac plateau hydro-geodetic observatory (Saint-Maurice-Navacelles area, southern France), NOT LSBB / Rustrel.** The 2018 paper does not mention LSBB.
4. **Allan deviation values at intermediate τ (10 s, 100 s, 1000 s) are NOT stated in the paper text or any table** — only in Fig. 5. Do not quote them as authoritative; only the τ → 1 s asymptote (750 nm s⁻² Hz⁻¹/²) and the long-time anchors (σ(1 h) = 10.7 and 8.5 nm s⁻²; σ(1 day) = 9.4 nm s⁻²) are reliable.
5. **Ocean loading and polar motion are implemented in the AQG control software (TSoft routine) but are not explicitly listed as having been applied to the Talence-5-day or Larzac-month-long datasets whose Allan deviations are shown in Figs. 4 and 5.** Only tilt + microwave clock + pressure + synthetic Earth tide are explicitly stated for the analysis data.
6. **Antoni-Micollier et al. (2022) Wiley full-text and ESS Open Archive preprint returned HTTP 403 to direct fetch**; the verbatim passages quoted in Section 8B and successor tables were extracted via indexed search snippets cross-checked across two independent sources. Wording is internally consistent, but a small risk of paraphrase remains. The DOI 10.1029/2022GL097814 and the supporting preprint URL are stable.
7. **Vendor specifications are dated 2024–2025** (current Exail product page as of May 2026). They do not include T, n_atoms, cycle time, or Raman beam waist.
8. **Manufacturer name evolution:** Muquans → iXblue (acquired) → Exail (rebranded). Older papers and Cooke 2021 refer to Muquans; Antoni-Micollier 2022 to iXblue; Glässel 2025 and the 2024 magazine article to Exail.
9. **For the gradient instrument (DQG) cited in Section 8D, the 1 E figure is a specification target; the achieved long-term gradient stability is 0.15 E = 1.5 × 10⁻¹⁰ s⁻²** per the body of Antoni-Micollier et al. 2024 (arXiv:2405.10844).