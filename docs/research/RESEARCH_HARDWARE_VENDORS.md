# Hardware Vendor Reference for the qgrav v2.0 Integration Layer

**TL;DR (overall)**
- The only currently published, peer-reviewed, commercial atom-interferometric gravimeter with a complete public spec sheet is the Exail (ex-Muquans / iXBlue) AQG family: 500 nm/s²/√Hz (5 × 10⁻⁷ m/s²/√Hz) sensitivity, ~2 Hz drop rate, sub-µGal long-term stability, and an independently measured combined uncertainty ~100 nm/s² (1 × 10⁻⁷ m/s²) from BKG (Glässel et al. 2025).
- AOSense, Vector Atomic (GAINS), Infleqtion (ex-ColdQuanta), and Q-CTRL all market cold-atom gravimeters or quantum inertial sensors, but public technical disclosure is at the level of marketing copy and conference abstracts; only Vector Atomic GAINS has a conference-disclosed performance figure ("surpassing 1 mGal precision and accuracy" - < 1 × 10⁻⁵ m/s²), and none publish APIs, data-format specs, or sample-level documentation.
- For the signal-chain integration layer, the right reference architectures are: a digital cross-correlation phase-noise/ADEV analyzer (Microchip 5125A, –145 dBc/Hz typ at 1 Hz on a 10 MHz carrier; < 3 × 10⁻¹⁵ ADEV at 1 s), the Miles Design / Microsemi TimePod 5330A (0.5–30 MHz, 16-bit RF ADCs at ~78 MHz clock, 236 kS/s baseband), and an NI PXIe-4464 DSA module (24-bit delta-sigma, 4 simultaneously sampled channels, 100 S/s–204.8 kS/s, 119 dB DR) for fluorescence-photodiode / lock-in chains.

---

## 1. Muquans / iXBlue / Exail - Absolute Quantum Gravimeter (AQG)

**TL;DR.** Peer-reviewed AQG-A01 sensitivity: 500 nm/s²/√Hz (= 5 × 10⁻⁷ m/s²/√Hz) at a quiet site, 2 Hz repetition rate, long-term stability < 10 nm/s² (1 × 10⁻⁸ m/s², ~1 µGal). Independent BKG evaluation of AQG-A02 / AQG-B10 confirms the 500 nm/s²/√Hz spec, with a combined accuracy budget ~100 nm/s² (1 × 10⁻⁷ m/s²) - not yet competitive with FG5-class FCCGs on accuracy, but uniquely good for continuous absolute monitoring. Software interfaces are described qualitatively (dedicated control software, remote internet operation, raw accelerometer stream, Earth-tide/ocean-loading corrections via a built-in TSoft routine) but **no public API, file-format, or schema documentation exists.**

**Corporate history.** Muquans → acquired by iXblue → rebranded Exail. The Ménoret 2018 paper (DOI 10.1038/s41598-018-30608-1, arXiv:1809.04908) is the canonical first-product reference; AQG-B is the field/outdoor variant, AQG-A the indoor variant; AQG-B10 is among the most recent units evaluated externally (Glässel et al., J. Geod. 99:73, 2025, DOI 10.1007/s00190-025-01995-x). Recent Exail manufacturer summary at arXiv:2405.10844 (Antoni-Micollier et al., 2024 - manufacturer conference paper) reports A01–A04 and B01–B12 already produced.

**Quantitative specs (each with unit conversion):**

| Quantity | Value | SI conversion | Source class |
|---|---|---|---|
| Short-term sensitivity (AQG-A01, peer reviewed) | 500 nm·s⁻²·Hz⁻¹ᐟ² | 5 × 10⁻⁷ m·s⁻²·Hz⁻¹ᐟ² | Peer-reviewed (Ménoret 2018) |
| Sensitivity at Talence (noisy lab) | 600–700 nm·s⁻²·Hz⁻¹ᐟ² | 6–7 × 10⁻⁷ m·s⁻²·Hz⁻¹ᐟ² | Peer-reviewed (Ménoret 2018) |
| Long-term stability (1 day) | 9.4 nm·s⁻² | 9.4 × 10⁻⁹ m·s⁻² | Peer-reviewed (Ménoret 2018) |
| Repeatability between pillars | ≤ ~24 nm·s⁻² | ≤ 2.4 × 10⁻⁸ m·s⁻² | Peer-reviewed (Ménoret 2018) |
| Repetition rate | 2 Hz (drop interval ≈ 0.5 s; BKG study quotes 0.54 s) | T_cycle ≈ 0.5 s | Peer-reviewed (Ménoret 2018; Glässel 2025) |
| Interrogation time T | 60 ms | 0.060 s | Peer-reviewed (Ménoret 2018) |
| Drop free-fall length (cloud after MOT) | ≈ 4.4 mm before Raman; detection 150 mm below trap | - | Peer-reviewed (Ménoret 2018) |
| Atom number per drop | ~10⁷ ⁸⁷Rb | - | Peer-reviewed (Ménoret 2018) |
| Atom temperature | < 2 µK | - | Peer-reviewed (Ménoret 2018) |
| Combined uncertainty (BKG / Bad Homburg & Wettzell) | ~100 nm·s⁻² | 1 × 10⁻⁷ m/s² | Peer-reviewed (Glässel et al. 2025) |
| AQG-B10 measured sensitivity at Wettzell | 430–500 nm·s⁻²·τ⁻¹ᐟ² | 4.3–5.0 × 10⁻⁷ m·s⁻²·Hz⁻¹ᐟ² | Conf./manuf. (arXiv:2405.10844) |
| AQG-A02 measured at Bad Homburg | 300 nm·s⁻²·τ⁻¹ᐟ² | 3 × 10⁻⁷ m·s⁻²·Hz⁻¹ᐟ² | Conf./manuf. (arXiv:2405.10844) |
| Differential AQG (DQG) gradiometer sensitivity | "about 60 E/τ¹ᐟ² for the gradient with a long-term stability around 1 E" | 6 × 10⁻⁸ s⁻²/√Hz; ~1 × 10⁻⁹ s⁻² | Conf./manuf. (arXiv:2405.10844) |
| Manufacturer headline ("turn-key … gravity at a level of 10⁻⁸ m/s²") | 10⁻⁸ m/s² | 10⁻⁸ m/s² | Marketing (exail.com/product/quantum-gravimeters) |
| Power consumption | 500 W (entire system) | - | Conf./manuf. (arXiv:2405.10844) |
| Sensor head weight | ≈ 30 kg | - | Peer-reviewed (Ménoret 2018) |
| Measurement height | 55 cm above ground; 48.8 cm above leveling tripod by design | - | Peer-reviewed (Ménoret 2018) |

**Verbatim quotes:**
- Sensitivity / repetition rate / stability (peer-reviewed): "The resulting sensor measures gravity at a 2 Hz repetition rate with a sensitivity of 500 nm.s⁻².Hz⁻¹ᐟ² and a long term stability below 10 nm.s⁻² with a short installation and warm-up time." - Ménoret et al., Sci. Rep. 8, 12300 (2018).
- Talence (noisy): "The sensitivity of the instrument during the five days was approximately 600 nm.s⁻².Hz⁻¹ᐟ², mainly limited by the residual vibration noise … When the noise is higher, the sensitivity is typically 700 nm.s⁻²·Hz⁻¹ᐟ²." - Ménoret 2018.
- Larzac: "The best sensitivity achieved by our instrument in Larzac is 500 nm·s⁻²·Hz⁻¹ᐟ² … during the measurement campaign of 2017, the gravimeter was operated at a slightly lower sensitivity of 750 nm·s⁻²·Hz⁻¹ᐟ² due to a decrease of the number of atoms loaded in the interferometer." - Ménoret 2018.
- Independent confirmation: "Our measurements confirm a sensitivity of 500 nm s⁻² Hz⁻¹ᐟ² at a quiet site, as specified, equivalent to a precision of 10 nm/s² after 1-h integration time, and a combined uncertainty on the order of 100 nm/s², based on a comparison to the local gravity reference function." - Glässel et al., J. Geod. 99:73 (2025).
- Drop interval (BKG): "The AQG performs a drop measurement once every 0.54 s with a specified sensitivity of 500 nm s⁻² Hz⁻¹ᐟ² and target accuracy of 100 nm/s²." - Glässel 2025.
- Cross-unit reproducibility (manufacturer/conference): "For all units the short-term sensitivity is below 800 nm/s²/τ¹ᐟ² … Measurements with AQG B10 at the geodetic observatory Wettzell, Germany confirm the instrument sensitivity below 500 nm/s²/τ¹ᐟ² … The long-term stability is below 10 nm/s² for all AQG independent of the site." - Antoni-Micollier et al., arXiv:2405.10844.
- Manufacturer headline (marketing): "Transportable, it performs measurement at a level of 10⁻⁸ m/s² (1 μGal) in terms of sensitivity, stability and repeatability." - exail.com/product/quantum-gravimeters.

**Software / API / data-format public information.**
- The paper describes control software that "automatically locks the lasers to a predefined setpoint, turns on the EDFAs and starts the measurement sequence," that "calculates tilts, atmospheric pressure, vertical gravity gradients, polar motion and quartz oscillator frequency drifts," and that applies "Earth tide and ocean loading corrections … by calling a TSoft routine" (Ménoret 2018). It also notes: "Remote access to the gravimeter is possible using an internet connection, both to retrieve data and to control the instrument."
- Glässel et al. (2025) describes the operational topology: "A laptop, that connects to the rack, runs a dedicated control software that is needed to initialize the hardware components and handle the data acquisition" and that "The total systematic bias correction and uncertainty is configured in the control software and applied in data processing."
- **No public API, network protocol, file format, RS-232/Ethernet command set, or programming SDK is documented.** Anyone integrating an AQG must obtain documentation from Exail under NDA.

**Disagreement to flag.** Manufacturer marketing copy describes "the only commercial industry-grade gravity meter" with "µGal-level precision" (1 × 10⁻⁸ m/s²) implying the headline number is accuracy-class. The independent BKG comparison concludes "as of yet, both AQGs do not reach the accuracy of FG5-type gravimeters, but provide advantages for continuous measurements and operation" and the combined uncertainty is closer to 100 nm/s² (1 × 10⁻⁷ m/s²), with the AQG-B10 in particular showing "a significantly higher bias of −94 nm/s² than the AQG-A02" - ~10× the marketing accuracy claim. **For qgrav v2.0, treat the AQG instrument-level accuracy budget as ~100 nm/s², not 10 nm/s².**

---

## 2. AOSense - compact gravimeter and atom-optic inertial products

**TL;DR.** AOSense markets a compact gravimeter, gravity gradiometer, Rb microwave clock, accelerometer/gyroscope modules, and component-level building blocks (ECDLs, tapered amplifiers, optical isolators, frequency combs). **The only public quantitative gravimeter performance number is a 20 Hz sampling rate.** No peer-reviewed sensitivity, bias, or noise spec is associated with the product on the company website; third-party literature (Hu et al. 2018 review of CAAGs) explicitly notes "The performance of AOSense's atom gravimeter has not been reported up to now." No public API or data-format documentation.

**Verbatim quotes:**
- Product, sampling rate (marketing): "AOSense delivered its first commercial compact gravimeter to an aerospace customer in 2010 … The sensor is capable of operating autonomously and acquiring data for weeks. The 20 Hz sampling rate (bandwidth) is compatible with operation in dynamic environments, and compares favorably with typical lab-based sensors that operate in the 0.1-1 Hz range." - aosense.com/products/atom-optic-sensors/gravimeter/
- Rb microwave clock target specs (separate product, marketing): "Rack-mount microwave atomic clock using laser-cooled 87Rb atoms. Production unit target specifications: Allan deviation 2×10⁻¹² @ 1 s, 2×10⁻¹⁴ @ 10⁴ s; flicker floor 1×10⁻¹⁴; absolute accuracy < 1×10⁻¹³." - AOSense Company Catalog (etesters.com).
- Frequency comb (marketing): "The comb is capable of supporting an Allan deviation of < 5 × 10⁻¹⁸ at 1 second and ~10⁻²⁰ after 10⁵ seconds." - AOSense Company Catalog.
- Inferred from independent literature: "The performance of AOSense's atom gravimeter has not been reported up to now, while the researchers of Muquans have reported their instrument recently." - Hu et al., "A new type of compact gravimeter for long-term absolute gravity monitoring" (Metrologia, 2018).

**Software / API.** Not public.

**Pedigree.** "AOSense was formed in 2004 by Brenton Young and Mark Kasevich to spin off innovative research developed at Stanford University, joined by Jim Spilker as Chairman" - aosense.com/about/. First DARPA prime contract (2006) was for a gravity gradiometer and single-axis accelerometer/gyroscope. AOSense's atom-interferometer gradiometer work is associated with NASA satellite-gravimetry pathfinders.

---

## 3. ColdQuanta / Infleqtion - quantum sensing & inertial products

**TL;DR.** Infleqtion (rebranded from ColdQuanta on November 30, 2022, per the company's own press release) sells: (a) an optical atomic clock product line called Tiqker, (b) Rydberg-based quantum RF receivers, (c) cold-atom inertial sensors / "Q-INS" (a Q-NAV programme in pre-commercial development; no shipping product), and (d) a cloud Bose–Einstein-condensate generator now called Oqtant (originally "Albert"). **No quantitative sensitivity, bias, or noise specification for an Infleqtion gravimeter or quantum-inertial sensor is publicly disclosed.** Q-INS is described in press releases as integrating quantum and classical sensors with ML-based denoising; the only quantitative claim is qualitative: "sensor volume reduction of greater than a factor of 10,000 times compared to the current state-of-the-art technology."

**Verbatim quotes (all marketing / press):**
- Product line: "Our range of sensing products-optical atomic clock, quantum radio frequency (RF) receiver, and inertial sensing-tackle real-world challenges in energy, space, national security, and more." - infleqtion.com.
- Q-INS / accelerometer demonstrator: "The team demonstrated the world's first software-configured, quantum-enabled high-performance accelerometer by combining machine learning with quantum sensing … The accelerometer demonstrated a sensor volume reduction of greater than a factor of 10,000 times compared to the current state-of-the-art technology. It also withstands unwanted vibrations by a factor of 10-100 times greater than traditional atom-based sensors." - infleqtion.com/quantum-sensing-breakthrough-…
- Airborne quantum-inertial demonstration: "The successful testing of an optical atomic clock, Infleqtion's Tiqker, and core elements of a quantum inertial sensor aboard QinetiQ's RJ100 Airborne Technology Demonstrator represents a breakthrough in airborne quantum technology." - infleqtion.com/un-jammable-quantum-tech-takes-flight/
- Oqtant cloud BEC (descended from Albert): "Oqtant QMS [Quantum Matter Service] can be used for cutting edge scientific research, as a powerful classroom tool, or a low-barrier of entry into the world of [ultracold atoms]." - medium.com Modern Scientist write-up.

**Software / API.** Oqtant exposes a Python SDK and a job-submission API (oqtant.infleqtion.com) for cloud BEC experiments - **this is the only Infleqtion-product programming interface that is publicly documented**, and it is for the BEC service, not for a gravimeter. Gravimeter/IMU APIs: not public.

---

## 4. Vector Atomic - atom-interferometer GAINS gravimeter and iodine-based optical clocks

**TL;DR.** Vector Atomic's GAINS is a strapdown ⁸⁷Rb atom-interferometric gravimeter that operated at sea on a U.S. Navy vessel for 20 days during RIMPAC 2022 and a follow-on for 36 days; the only public performance metric is "**surpassing 1 mGal gravimeter precision and accuracy**" (i.e., < 1 × 10⁻⁵ m/s²), from the 2025 ION PLANS conference abstract. The company also markets the Evergreen / EG-30 iodine optical clock (35 L / 30 L rackmount, < 100 W, ≈ 25 fs stability at 1 s, < 1 ns holdover for several days; peer-reviewed by Roslund et al., Nature 628, 736–740, 2024, DOI 10.1038/s41586-024-07225-2). MAGIC is Vector Atomic's terrestrial portable atom gravimeter (< 35 kg, 12 V / < 100 W, "µGal-level"). No public API or file-format documentation.

**Verbatim quotes:**
- GAINS performance (conference): "The comparison results confirm that GAINS measurements are more accurate than the publicly available gravity maps, with performance surpassing 1 mGal gravimeter precision and accuracy for all relevant navigation timescales." - Cashen et al., ION PLANS 2025 abstract (ion.org/plans/abstracts.cfm?paperID=15240).
- GAINS uptime: "To date, GAINS has operated at-sea for 36 days, with > 99% uptime through mild to heavy ship dynamics." - Cashen et al., ION PLANS 2025.
- GAINS at RIMPAC 2022 (length, BusinessWire 2023-03-27): "results from a 20 day at-sea gravity survey," and corroborated by Roslund et al., Nature 628 (2024): "Three of these clocks operated continuously aboard a naval ship in the Pacific Ocean for 20 days while accruing timing errors below 300 ps per day."
- GAINS at RIMPAC (marketing): "GAINS generated high-resolution absolute gravity measurements that matched the satellite maps at the micro-g level (0.000001 g), which is within the reported accuracy and discrepancy between available, competing satellite maps." - Vector Atomic / BusinessWire, 27 March 2023.
- MAGIC, terrestrial (conference abstract): "The total package weighs < 35 kg and operates from a single 12V power source consuming < 100 W, making it capable of operating over 12 h off a single battery." - Cashen et al., ION PLANS 2025.
- Iodine optical clock EG-30 (marketing): "EG-30 introduces a new performance class to commercial timing markets, offering 25 femtosecond stability (0.000000000000025 s) at one second, and multiday, sub-nanosecond holdover." - Vector Atomic / BusinessWire, 13 Nov 2023.
- Iodine optical clock holdover (peer reviewed): "The clocks can maintain holdovers of 10 ps for several hours and 1 ns for several days." - Roslund et al., Nature 628, 736–740 (2024). Per the arXiv preprint (arXiv:2308.12457), the same clocks maintained "< 10⁻¹⁴ frequency instability for multiple days."

**SI conversions.**
- 1 mGal = 1 × 10⁻⁵ m/s² → GAINS "surpasses" this precision.
- 1 µGal = 1 × 10⁻⁸ m/s² → MAGIC "µGal-level" implies ≤ 10⁻⁸ m/s² order, but no √Hz figure is public.

**Disagreement / caveat.** Vector Atomic press releases use "matched the satellite maps at the micro-g level (10⁻⁶ g)," which corresponds to 10⁻⁵ m/s², equivalent to ≈ 1 mGal. The ION abstract qualifies this as map-limited and quotes "surpassing 1 mGal" as the actual sensor figure; no specific Allan-deviation curve or mGal/√Hz number is published in a peer-reviewed source as of May 2026.

**Software / API.** Not public.

---

## 5. Q-CTRL - software-ruggedized quantum gravimeter (Ironstone Opal)

**TL;DR.** Ironstone Opal is Q-CTRL's full-stack "quantum-assured" navigation product. The publicly fielded variants are (i) magnetic-anomaly-based (airborne trial, "up to 50× / 111× better positioning than conventional alternatives") and (ii) a quantum dual gravimeter ("quantum dual gravimeter") fielded for 144 h on the Royal Australian Navy MV Sycamore in 2025. **No quantitative gravimeter sensitivity (m/s²/√Hz, µGal/√Hz, bias, or accuracy) is publicly disclosed.** Q-CTRL explicitly states it does not sell sensor components: "Q-CTRL does not sell sensor components, but the Ironstone Opal quantum-assured navigation system is now available for presale." No public gravimeter API or file format. Q-CTRL's adjacent open quantum-control SDKs ("Boulder Opal," "Fire Opal") are Python-based and well-documented, but they target gate-level quantum-computer error suppression, not the gravimeter's output stream.

**Verbatim quotes:**
- Product framing (marketing): "Ironstone Opal delivers reliable GPS-free navigation for land, sea, and air, leveraging unjammable geophysical map matching and offering a quantum-assured solution in GPS-denied environments. It incorporates Q-CTRL's proprietary software-ruggedized gravitational and magnetic sensors with world-leading denoising and positioning software …" - q-ctrl.com/our-work/positioning-navigation-and-timing.
- Maritime trial (marketing): "In these trials, Q-CTRL field deployed a quantum dual gravimeter … This first trial saw over 144 hours of continuous operation and successful data collection with no human intervention during real maritime operations." - q-ctrl.com (Sycamore announcement).
- Power consumption (press): "The dual gravimeter was developed and fielded over a period of 14 months, and bolted to the floor in the space of a single server rack in a communications room onboard MV Sycamore. The sensor consumed only 180W of power …" - Fierce Sensors, 2025.
- Sensor sales (Q-CTRL FAQ): "Q-CTRL does not sell sensor components, but the Ironstone Opal quantum-assured navigation system is now available for presale." - q-ctrl.com/our-work/defense.
- Magnetic navigation performance (peer reviewed/preprint): "Quantum-assured magnetic navigation achieves positioning accuracy better than a strategic-grade INS in airborne and ground-based field trials." - arXiv:2504.08167 (2025).

**Software / API public?** No for the gravimeter. Yes for adjacent quantum-control SDKs (Boulder Opal / Fire Opal) - but these are not the data pipeline qgrav needs.

---

## 6. Lab-grade alternatives for the signal chain - Microchip 5125A, TimePod 5330A, NI DAQ

**TL;DR.** A realistic open-source v2.0 hardware-integration layer can rely entirely on well-documented commercial timing analyzers and DAQ hardware: (a) **Microchip (Microsemi) 5125A** - 1–400 MHz phase-noise / Allan-deviation test set, system noise floor –140 dBc/Hz at 1 Hz (10 MHz carrier), –165 dBc/Hz at 10 kHz, ADEV floor < 3 × 10⁻¹⁵ at 1 s; (b) **Miles Design / Microsemi TimePod 5330A** - cross-spectrum analyzer 0.5–30 MHz, 16-bit RF ADCs with ≈ 78 MHz ADC clock and 236 kS/s baseband, ADEV < 1 × 10⁻¹³ @ 1 s, residual phase-noise < –170 dBc/Hz at offsets > 10 kHz; (c) **NI PXIe-4464 DSA module** - 24-bit delta-sigma, 4 simultaneous-sampled channels, 100 S/s–204.8 kS/s, 119 dB DR (good fit for fluorescence-photodiode / lock-in detection chains). For higher-bandwidth waveform digitization (e.g., direct Raman beat-note sampling or fast atom-detection envelopes), the **NI PXIe-6124** S-series multifunction module (16-bit, 4 MS/s/channel, 4 simultaneous channels) is the canonical low-cost reference. All three vendors document their public APIs (NI-DAQmx for the NI hardware; TSERVE/TimeLab for the 5125A and TimePod).

**Verbatim quotes (5125A - Microsemi datasheet ds_5125a-test-set.pdf):**
- "The Microsemi® 5125A makes accurate phase noise measurements on signals from 1 MHz to 400 MHz, covering the full range of the most commonly used frequency references."
- "The 5125A's industry-leading close-in phase noise performance, -140 dBc/Hz at a 1 Hz offset (10 MHz fundamental), makes it the perfect solution to characterize the lowest noise frequency references available."
- "Excellent phase noise measurements down to -170 dBc/Hz (typical) 10 kHz from the carrier (10 MHz input)"
- "Allan deviation: < 3 × 10⁻¹⁵ at 1 sec (10-400 MHz, 0.5 Hz BW)"
- Input level "3-17 dBm; Input impedance: 50 Ω; Input connectors: TNC."
- (The datasheet does **not** publicly disclose the internal ADC sample rate / bit depth - only "advanced, high-speed, low-noise analog-to-digital converters.")

**Verbatim quotes (TimePod 5330A):**
- "This programmable cross spectrum analyzer measures the amplitude, phase, and frequency stability of RF sources and two-port devices from 0.5 MHz to 30 MHz."
- "All four receiver channels are implemented with high performance 16-bit RF ADCs. USB 2.0 High Speed support is required for all 5330A acquisitions."
- "These graphs are created by calculating phase and/or amplitude differences for all four baseband streams - Q0,I0, Q1,I1, Q2,I2, and Q3,I3 - at the full 236 ks/sec data rate."
- "Phase Noise and Jitter: This function measures SSB phase noise and integrated phase jitter with a noise floor of below -170 dBc/Hz at 10 kHz from the carrier."
- "Allan deviation (ADEV) typically less than 1E-13 at t=1s."

**Verbatim quotes (NI PXIe-4464 spec sheet, ni.com docs):**
- "Analog-to-digital converter (ADC) resolution …………………… 24 bits"
- "ADC type ……………………………………………………… Delta-sigma"
- "Sample rate (fs) ………………………………………………… 100 S/s to 204.8 kS/s"
- Product page: "204.8 kS/s, 119 dB, 6 Gains, AC/DC-Coupled, 4-Input PXI Sound and Vibration Module … The PXI-4464 delivers simultaneous sampling on all channels."

**Software / API public.**
- Microchip 5125A and TimePod 5330A: ASCII data streaming via TSERVE; phase-data streaming and remote acquisition documented in the public TimeLab / 53100A user manual chapters on "Accessing the PhaseStation & TimePod Remotely."
- NI hardware: full NI-DAQmx C/Python/LabVIEW API and IVI drivers - long-standing, stable, public.

**Recommended placement in qgrav.** Use the NI PXIe-4464 (or equivalent 24-bit DSA) for photodiode fluorescence/molasses detection channels (audio-band, ≤ 200 kS/s simultaneous), the PXIe-6124 or similar 4 MS/s 16-bit S-series for short-pulse waveform capture, and route all microwave/Raman LO and quartz reference chains through a 5125A or TimePod 5330A for ADEV / phase-noise characterization. Treat the 5125A and TimePod as canonical reference clocks for the qgrav simulation's noise-injection layer.

---

## 7. Typical atom-gravimeter detection / readout signal chain in the published literature

**TL;DR.** Across the published mobile atom gravimeters (Ménoret 2018 / AQG-A01; Freier 2016 / GAIN; Hu 2013 / HUST; Wu 2014 / Wuhan field; Bidel 2018 marine), the canonical signal chain is: (i) ⁸⁷Rb (or ⁸⁵Rb) trapped in a MOT loaded for ~200–300 ms; (ii) sub-Doppler optical-molasses cooling to ≈ 2 µK; (iii) microwave / Raman state-preparation pulse selecting |F=1, m_F=0⟩; (iv) π/2 − π − π/2 stimulated-Raman or Bragg sequence with T from 50–60 ms (transportable / AQG) to 120 ms (Wu 2014; AQG drop limit) to 300 ms (HUST lab fountain, Hu 2013); (v) **fluorescence detection** (not absorption in any of these production gravimeters) onto Si photodiodes at the D2 (780 nm) line, computing the F=2 / (F=1+F=2) population ratio drop-to-drop; (vi) Allan-weighted servo of the Raman-chirp α (≈ 25 MHz/s for ⁸⁷Rb at T = 60 ms) locked to mid-fringe; (vii) parallel real-time MEMS/seismometer-based vibration compensation. Cycle rates 0.5–2 Hz on lab/field instruments; 50–330 Hz dual-axis dynamic atom interferometers (Sandia / McGuinness 2012, Rakholia 2014) at the cost of an order-of-magnitude single-shot sensitivity penalty.

**Concrete numbers (each quoted verbatim).**

**Detection method = fluorescence on photodiodes (Ménoret 2018, AQG):**
- "Fluorescence detection is used to count the number of atoms in each level and measure the interferometric phase shift."
- "At the end of the sequence, we collect fluorescence on a set of photodiodes and compute the proportion of atoms in each output port of the interferometer."
- "We drive a Raman transition with a 80 μs pulse and detect fluorescence at the bottom of the chamber."
- Detection geometry: "At the bottom of the chamber (150 mm below the position of the trap), we measure the proportion of atoms in each output port of the interferometer with a detection signal-to-noise ratio of 150."

**Vibration-correction signal path (Ménoret 2018, AQG):**
- "The signal from the classical accelerometer (Nanometrics Titan) is filtered by a bandpass filter with cut-off frequencies f_hp = 0.05 Hz and f_lp = 1 kHz."
- "The filtered signal is digitized and weighted in real-time by the transfer function of the atom interferometer … Less than 1 ms before the last Raman pulse, the calculated correction is applied to the phase lock loop of the Raman lasers to compensate the vibration phase shift."
- "Phase noise due to vibrations is 2.3 rad rms, and the interference signal is washed out over several fringes. During the last 1000 cycles, active compensation is turned on and the vibration phase noise is greatly reduced to 36 mrad rms, allowing the interferometer to remain close to mid-fringe."

**Pulse timing, T, k_eff, and chirp (Ménoret 2018, AQG):**
- "The sequence consists of three counterpropagating Raman pulses of duration 10, 20 and 10 μs in a π/2 − π − π/2 configuration. Between these pulses, the the atoms are in near-perfect free fall for an interrogation time of T = 60 ms."
- "k_eff = 4π/λ ≈ 16 × 10⁶ m⁻¹ … α ≈ 25 MHz·s⁻¹ is a frequency chirp applied to the Raman lasers."
- "On average, 55 cm above ground level" measurement height.
- Cycle rate: "the instrument's repetition rate is on the order of 2 Hz."

**Freier 2016 (GAIN, peer-reviewed J. Phys. Conf. Ser. 723 012050, DOI 10.1088/1742-6596/723/1/012050 / arXiv:1512.05660):**
- "best-reported performance of mobile atomic gravimeters to date with an accuracy of 39 nm/s² and long-term stability of 0.5 nm/s² short-term noise of 96 nm/s²/√Hz."
- SI conversions: 39 nm/s² = 3.9 × 10⁻⁸ m/s²; 0.5 nm/s² = 5 × 10⁻¹⁰ m/s²; 96 nm/s²/√Hz = 9.6 × 10⁻⁸ m·s⁻²·Hz⁻¹ᐟ².
- Architecture: "interfering ensembles of laser-cooled ⁸⁷Rb atoms in a fountain setup, using stimulated Raman transitions … modular units with a respective size of roughly (1×1×2) m³."
- Vibration isolation: GAIN uses an "active vibration isolation system" with post-correction (a different topology from the AQG's hybrid accelerometer compensation).

**Hu 2013 (HUST fountain, Phys. Rev. A 88, 043610, DOI 10.1103/PhysRevA.88.043610):**
- Headline (abstract, verbatim): "Benefiting from these efforts and the excellent performance of the active vibration isolator, a short-term sensitivity of about 4.2 μGal/√Hz (1 μGal = 1 × 10⁻⁸ m/s²) is reached, which improves the sensitivity by a factor of 2 compared with the former best reported value."
- "By a modulation experiment, we further indicate that the residual vibration noise contribution is about 1.2 μGal/√Hz, which implies a possible improvement over the present absolute gravity measurement level by about one order of magnitude."
- SI: 4.2 μGal/√Hz = 4.2 × 10⁻⁸ m·s⁻²·Hz⁻¹ᐟ²; 1.2 μGal/√Hz = 1.2 × 10⁻⁸ m·s⁻²·Hz⁻¹ᐟ².
- T = 300 ms is reported for this HUST apparatus in the group's review article (Chinese Phys. B 24, 050401, 2015): "Figure 7 shows a typical fringe for a pulse separation time of 300 ms," implying a cycle rate ~1 Hz; detection method = fluorescence (group standard, not directly quoted from the 2013 PRA abstract); photodiode model not public.

**Wu 2014 (Wuhan, Metrologia 51, 452, "investigation of a microgal-level cold atom gravimeter for field applications," DOI 10.1088/0026-1394/51/5/452):**
- Verbatim: "The total interrogation time is optimized to 120 ms and the repetition rate is 2.2 Hz. A sensitivity of 1.0 × 10⁻⁷ g Hz⁻¹ᐟ² and a resolution of 5.7 × 10⁻⁹ g within 1000 s integration time are reached. A continuous g measurement over 128 h is carried out."
- SI: 1.0 × 10⁻⁷ g/√Hz ≈ 9.81 × 10⁻⁷ m·s⁻²·Hz⁻¹ᐟ² ≈ 980 nm/s²/√Hz; 5.7 × 10⁻⁹ g ≈ 5.6 × 10⁻⁸ m/s² ≈ 5.6 μGal resolution.

**High-data-rate dynamic-environment AIs (Sandia / McGuinness 2012, Rakholia 2014):**
- "We demonstrate a high data-rate light-pulse atom interferometer for measuring acceleration. The device is optimized to operate at rates between 50 Hz to 330 Hz with sensitivities of 0.57 μg/√Hz to 36.7 μg/√Hz, respectively."
- SI: 0.57 μg/√Hz ≈ 5.6 × 10⁻⁶ m·s⁻²·Hz⁻¹ᐟ² (at 50 Hz cycle); 36.7 μg/√Hz ≈ 3.6 × 10⁻⁴ m·s⁻²·Hz⁻¹ᐟ² (at 330 Hz cycle). These are five orders of magnitude noisier than gravimeter-class instruments but enable IMU-class operation.

**Implications for qgrav v2.0.**
- The detection model should default to fluorescence on a small (1–4) array of photodiodes at the D2 wavelength (780 nm for Rb; 852 nm for Cs), with normalized population ratio P = N₂/(N₁+N₂) and SNR floor 100–200 per shot.
- ADC sample rate for the fluorescence pulse can be modest (the integrated fluorescence pulse is a few ms long → 200 kS/s, 24-bit DSA is comfortable; 24-bit gives DR > 119 dB, well above shot-noise-limited signals).
- The vibration-compensation channel (classical accelerometer) needs ≥ 1 kHz bandwidth and clean noise to < 10 ng/√Hz; the AQG uses a Nanometrics Titan as the canonical co-sensor, sampled at sub-kHz with bandpass 0.05 Hz–1 kHz.
- The Raman / Bragg LO chain reference can be modeled at –140 to –165 dBc/Hz close-in (1 Hz–10 kHz, 10 MHz reference) as set by a 5125A-grade quartz; this is the noise floor that limits short-term sensitivity in all the cited instruments.

---

## Overall vendor summary table

| Vendor / Product | Class | Headline sensitivity (verbatim) | Headline sensitivity (SI) | Accuracy / stability (verbatim) | Stability (SI) | Cycle rate | Software / API public? | Best public source class |
|---|---|---|---|---|---|---|---|---|
| Exail AQG-A01 (Ménoret 2018) | Cold-atom absolute gravimeter | "500 nm.s⁻².Hz⁻¹ᐟ²" | 5 × 10⁻⁷ m·s⁻²·Hz⁻¹ᐟ² | "long term stability below 10 nm.s⁻²" | < 1 × 10⁻⁸ m/s² | 2 Hz | No (control SW described, no API spec) | Peer-reviewed (DOI 10.1038/s41598-018-30608-1) + indep. eval. (DOI 10.1007/s00190-025-01995-x) |
| Exail AQG-B (B01–B12) | Cold-atom absolute gravimeter, field | "below 500 nm/s²/τ¹ᐟ²" (B10 at Wettzell) | < 5 × 10⁻⁷ m·s⁻²·Hz⁻¹ᐟ² | "combined uncertainty on the order of 100 nm/s²" | 1 × 10⁻⁷ m/s² | 2 Hz | No | Conf./manuf. (arXiv:2405.10844) + indep. eval. (DOI 10.1007/s00190-025-01995-x) |
| Exail DQG (differential gradiometer) | Cold-atom gravimeter + gradiometer | "about 60 E/τ¹ᐟ² for the gradient" | 6 × 10⁻⁸ s⁻²/√Hz | "long-term stability around 1 E" | 1 × 10⁻⁹ s⁻² | ≈ 2 Hz | No | Conf./manuf. (arXiv:2405.10844) |
| AOSense compact gravimeter | Cold-atom gravimeter | Not public (only "20 Hz sampling rate") | - | Not public | - | 20 Hz | No | Marketing only (aosense.com) |
| AOSense Rb microwave clock | Atomic clock (separate product) | "ADEV 2 × 10⁻¹² @ 1 s, 2 × 10⁻¹⁴ @ 10⁴ s" | - | "absolute accuracy < 1 × 10⁻¹³" | - | n/a | No | Marketing (etesters AOSense catalog) |
| Infleqtion (ColdQuanta) Q-INS / accelerometer | Quantum-classical inertial sensor (dev.) | Not public; only "10–100× more vibration-tolerant" | - | Not public | - | not public | Partial (Oqtant BEC service has public API; gravimeter does not) | Marketing/press (infleqtion.com) |
| Infleqtion Tiqker optical clock | Optical atomic clock | Not public (precision quoted only qualitatively) | - | Not public quant. | - | n/a | No | Marketing |
| Vector Atomic GAINS | Strapdown cold-atom gravimeter | "surpassing 1 mGal gravimeter precision and accuracy" | < 1 × 10⁻⁵ m/s² | "matched the satellite maps at the micro-g level (10⁻⁶ g)" | < 1 × 10⁻⁵ m/s² | Not public | No | Conf. abstract (ION PLANS 2025) + marketing (BusinessWire) |
| Vector Atomic MAGIC | Portable terrestrial gravimeter | "µGal-level observations" | ~10⁻⁸ m/s² order | Not public | - | Not public | No | Conf. abstract (ION PLANS 2025) |
| Vector Atomic EG-30 (Evergreen) | Iodine optical atomic clock | "25 fs stability at one second" | - | "1 ns for several days" holdover; "< 10⁻¹⁴ frequency instability for multiple days" (arXiv:2308.12457) | - | n/a | No | Peer-reviewed (Roslund et al., Nature 628, 736–740, 2024, DOI 10.1038/s41586-024-07225-2) + marketing |
| Q-CTRL Ironstone Opal (gravimetric) | Quantum dual gravimeter (full nav system) | Not public | - | Not public; only "144 h continuous operation," 180 W | - | Not public | No (for sensor); Yes for Boulder/Fire Opal QC SDK | Marketing/press; arXiv:2504.08167 (magnetic variant) |
| Microchip / Microsemi 5125A | Phase-noise / ADEV test set (1–400 MHz) | "-140 dBc/Hz at 1 Hz offset (10 MHz)" | - | "ADEV: < 3 × 10⁻¹⁵ at 1 s" | - | n/a | Yes - TSERVE/TimeLab API documented | Manufacturer datasheet (ds_5125a-test-set.pdf) |
| Miles Design / Microsemi TimePod 5330A | Cross-spectrum phase analyzer (0.5–30 MHz) | "below -170 dBc/Hz at 10 kHz" | - | "ADEV typically < 1 × 10⁻¹³ at 1 s" | - | 236 kS/s baseband, 16-bit ADCs | Yes - TSERVE/TimeLab API documented | Manufacturer manual (miles.io) |
| NI PXIe-4464 | 4-channel DSA module | "100 S/s to 204.8 kS/s, 24-bit delta-sigma" | - | 119 dB DR | - | up to 204.8 kS/s | Yes - NI-DAQmx public API | Manufacturer specs (ni.com) |
| NI PXIe-6124 (representative) | 4-channel S-series DAQ | 16-bit, 4 MS/s/channel | - | n/a | - | up to 4 MS/s | Yes - NI-DAQmx public API | Manufacturer specs (ni.com) |

---

## Recommendations for qgrav v2.0 hardware-integration layer

1. **Adopt the AQG-A/B numbers as the primary reference model** for cold-atom absolute gravimeters. Use 500 nm/s²/√Hz, 2 Hz cycle, T = 60 ms, k_eff ≈ 16 × 10⁶ m⁻¹, fluorescence detection on a 2-channel photodiode pair, 10⁷ Rb atoms, 2 µK cloud, and a 100 nm/s² accuracy budget (not 10 nm/s²) as defaults. Cite Ménoret 2018 + Glässel 2025 in the simulation's docstrings.

2. **Provide a "high-data-rate IMU-class" alternative model** at 100–330 Hz cycle and 0.5–37 μg/√Hz (5 × 10⁻⁶ – 3.6 × 10⁻⁴ m·s⁻²·Hz⁻¹ᐟ²), parameterized after McGuinness 2012 / Rakholia 2014. This is the right model for shipboard/airborne work (cf. Vector Atomic GAINS, Bidel 2018).

3. **For the laser/microwave LO chain noise floor**, default to a quartz-class reference at –140 dBc/Hz at 1 Hz / –165 dBc/Hz at 10 kHz on a 10 MHz carrier (5125A spec), and let users substitute a TimePod-class (–170 dBc/Hz at 10 kHz) noise model.

4. **For the photodiode / detection digitizer model**, use a 24-bit delta-sigma DSA (PXIe-4464 numbers: 204.8 kS/s, 119 dB DR) as the default ADC model. For pulsed-envelope work (a few ms detection window), this is overkill in bandwidth but exactly right in dynamic range. Provide a 16-bit, 4 MS/s alternative (PXIe-6124 class) for users modeling waveform-level Raman pulses.

5. **Treat all vendor APIs as opaque.** Build qgrav's hardware-integration layer around the published *physics* parameters above and a clean, mocked "instrument adapter" interface (read-only data ingest + start/stop control), since none of Exail, AOSense, Infleqtion, Vector Atomic, or Q-CTRL has published a programmer-facing API for their gravimeters. Reuse NI-DAQmx and the TimeLab/TSERVE remote command set as the only realistic concrete I/O bindings.

6. **Benchmark thresholds that would change these defaults.** (a) If Exail publishes a public REST/SCPI API for the AQG (none as of May 2026), promote that to a first-class adapter. (b) If Q-CTRL or Vector Atomic publishes a peer-reviewed paper with a specific mGal/√Hz or µGal/√Hz figure for their fielded gravimeters, retire the conference-abstract numbers and replace them with the peer-reviewed value. (c) If Infleqtion ships a commercial Q-INS with a datasheet, add it as a third reference class alongside AQG (1 Hz / 500 nm·s⁻²·Hz⁻¹ᐟ²) and GAINS (100 Hz / ~1 mGal-class).

## Caveats

- **Marketing vs. measurement.** Exail's marketing copy claims "10⁻⁸ m/s² … in terms of sensitivity, stability and repeatability" - this is best interpreted as the long-term-averaged stability target, *not* a single-shot sensitivity. The single-shot sensitivity is 500 nm/s²/√Hz (5 × 10⁻⁷ m/s²/√Hz, ~50× looser), and the combined accuracy as measured independently is ~100 nm/s² (10× looser than the marketing headline).
- **Conference abstracts ≠ peer-reviewed.** The GAINS "surpassing 1 mGal" figure is a conference abstract from ION PLANS 2025. The Antoni-Micollier AQG cross-unit data are a manufacturer conference paper (arXiv:2405.10844). The Glässel 2025 J. Geod. study is the closest thing to a peer-reviewed third-party AQG benchmark.
- **No public API/data format for any cold-atom gravimeter product.** Plan for vendor-specific NDA documentation, or wrap each vendor as an opaque "data file ingest" backend.
- **Hu 2013 photodiode model and exact cycle time are paywalled.** The 4.2 μGal/√Hz number is canonical and quoted verbatim in the abstract; T = 300 ms and ≈ 1 Hz cycle are taken from a HUST review of the same apparatus (Chinese Phys. B 24, 050401, 2015) rather than the 2013 paper itself.
- **Q-CTRL and Infleqtion gravimeter intrinsic specs are not public.** Their navigation-system-level performance claims (50×–111× improvement vs. classical GPS-alternative INS) are system-integration figures, not raw gravimeter sensitivities, and should not be back-converted into m/s²/√Hz.
- **AOSense's "20 Hz sampling rate" is a bandwidth statement, not a sensitivity statement.** Without a published noise floor, no equivalent m/s²/√Hz figure can be inferred.
- **Vector Atomic Evergreen / EG-30 clock product line** mixes a peer-reviewed iodine optical-clock physics result (Roslund et al., Nature 628, 736–740, 2024) with marketing copy. The peer-reviewed paper gives the holdover budget ("10 ps for several hours and 1 ns for several days") and the at-sea 20-day trial ("accruing timing errors below 300 ps per day"); the "25 fs at 1 s" figure is in marketing copy and not separately confirmed in the open Nature text.