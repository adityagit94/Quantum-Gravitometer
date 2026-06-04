# `docs/RESEARCH_RECENT_BENCHMARKS.md`

# Recent Atom-Gravimeter Benchmarks (2020–2025): Survey for qgrav v1.0.1 → v1.1.0 Regression Targets

**Bottom line up front.** No published atom-gravimeter result from 2020–2025 supersedes Freier 2016 (HU Berlin GAIN, 0.5 nm/s² long-term stability) or Hu 2013 (HUST, 4.2 μGal/√Hz short-term lab sensitivity) on the metric each is best at. Ménoret 2018 (Exail/Muquans AQG) is now triply validated by independent user evaluations (Cooke 2021, Antoni-Micollier 2022, Glässel 2025). qgrav v1.1.0 should **retain all three** existing regression targets and **add two** new 2020+ targets - Xu 2022 (HUST-QG, transportable; *Metrologia*) and Wu 2019 (Berkeley mobile; *Sci. Adv.*) - to broaden coverage to transportable and mobile/field regimes. Stray 2022 (Birmingham, *Nature*) is recommended as an optional gradiometer target.

**Scope and unit conventions.** This document surveys peer-reviewed atom-interferometric gravimeter (AIG) literature 2020–2025. Sensitivity (short-term noise floor) is reported in m/s²/√Hz; long-term stability/accuracy in m/s². 1 μGal = 1×10⁻⁸ m/s²; 1 nm/s² = 1×10⁻⁹ m/s²; 1 E (Eötvös) = 1×10⁻⁹ s⁻². Conversion arithmetic is shown inline.

---

## Topic 1 - State of the art atom gravimeters as of 2025

**TL;DR.** As of mid-2025 the lowest published *long-term stability* of any mobile atom gravimeter remains 0.5 nm/s² (Freier 2016, GAIN, HU Berlin) - unsuperseded. The best *transportable* 2020+ benchmark is HUST-QG (Xu et al. 2022, *Metrologia*) at 24 μGal/√Hz = 2.4×10⁻⁷ m/s²/√Hz with 3 μGal combined uncertainty. Commercial Exail AQG units hit 500 nm/s²/√Hz with 10 nm/s² precision after 1 h on quiet sites.

| Instrument | Group | Sensitivity (m/s²/√Hz) | Stability / accuracy | T (ms) | Species / k_eff | Context |
|---|---|---|---|---|---|---|
| GAIN | HU Berlin / PTB (Freier, Peters) | 9.6×10⁻⁸ (96 nm/s²/√Hz) | 0.5 nm/s² long-term; 39 nm/s² accuracy | ~260 | ⁸⁷Rb, 2ℏk Raman | transportable lab |
| HUST-QG | Huazhong USTC (Hu, Xu) | 2.4×10⁻⁷ (24 μGal/√Hz) | 3 μGal combined U; 1.3 μGal ICAG | ~300 | ⁸⁷Rb, 2ℏk Raman | transportable |
| CAG (LNE-SYRTE, ultracold) | Obs. de Paris (Pereira dos Santos, Merlet) | ~5.6×10⁻⁷ | 10 nm/s² stat. + 13 nm/s² syst. | 80 | ⁸⁷Rb, 2ℏk Raman | lab metrology |
| Berkeley mobile | UC Berkeley (Müller) | 3.7×10⁻⁷ (37 μGal/√Hz) lab | <2 μGal in ~30 min | ~130 | ⁸⁷Rb, 2ℏk Raman | mobile/field |
| Exail AQG-A02 / B10 | Exail (industrial) | 5.0×10⁻⁷ (500 nm/s²/√Hz) | 10 nm/s² @ 1 h; ~100 nm/s² combined U | ~60 | ⁸⁷Rb, 2ℏk Raman | field-deployed |
| GIRAFE2 (static lab) | ONERA (Bidel) | 8×10⁻⁶ (0.8 mGal/√Hz) | 0.17 mGal lab; 0.6–1.3 mGal airborne | 20 | ⁸⁷Rb, 2ℏk Raman | shipborne/airborne |
| Lattice AI (Berkeley) | UC Berkeley (Panda, Müller) | 6×10⁻⁷ m/s² per shot, 2T=200 ms | 6.2 nm/s² overall accuracy on source-mass; 1-minute coherence demonstrated | up to 70 s hold | Cs, lattice + Bragg | lab dark-energy probe |

**Supporting quotes / sources.**
- Glässel, Wziontek, Falk et al., *J. Geod.* 99, 73 (2025), DOI: 10.1007/s00190-025-01995-x - "Our measurements confirm a sensitivity of 500 nm s⁻² Hz⁻¹/² at a quiet site, as specified, equivalent to a precision of 10 nm/s² after 1-h integration time, and a combined uncertainty on the order of 100 nm/s²". The same paper independently re-attests Freier 2016 GAIN performance: "demonstrating an uncertainty of 39 nm/s², a long-term stability of 0.5 nm/s² and a short-term noise of 96 nm s⁻² Hz⁻¹/²".
- Xu et al., *Metrologia* 59, 055001 (2022), DOI: 10.1088/1681-7575/ac8258 - "HUST-QG exhibited a short-term sensitivity of 24 μGal Hz⁻¹/² and a combined uncertainty of 3 μGal… the degree of equivalence for HUST-QG in this comparison is 1.3 μGal, which supports our evaluation." (24 μGal/√Hz = 2.4×10⁻⁷ m/s²/√Hz; 3 μGal = 3.0×10⁻⁸ m/s²; 1.3 μGal = 1.3×10⁻⁸ m/s².)
- Panda et al., *Nature* 631, 515 (2024), DOI: 10.1038/s41586-024-07561-3 - "We measure the attraction of a miniature source mass to be amass = 33.3 ± 5.6stat ± 2.7syst nm s⁻², consistent with Newtonian gravity… The overall accuracy of 6.2 nm s⁻² surpasses by more than a factor of four the best similar measurements with atoms in free fall." (6.2 nm/s² = 6.2×10⁻⁹ m/s².)
- Panda et al., *Nat. Phys.* 20, 1234 (2024), DOI: 10.1038/s41567-024-02518-9 - "Up to one minute of coherence times are realized by suspending the spatially separated atomic wave packets in an optical lattice that is mode-filtered by an optical cavity. This trapped configuration suppresses phase variance due to vibrations by four to five orders of magnitude…"

---

## Topic 2 - Cold-atom Sr (strontium) gravimeters

**TL;DR.** Sr-based gravimeters using the ¹S₀–³P₀ single-photon clock transition (Tino group, Florence) achieved a relative gravity sensitivity of δg/g = 1.7×10⁻⁵ - roughly three orders of magnitude worse than Rb/Cs Raman gravimeters - but offer immunity to laser-phase noise critical for long-baseline architectures (AION, MAGIS-100). They are not viable Earth-gravity benchmark targets today.

- Hu, Wang, Salvi, Tinsley, Tino, Poli, arXiv:1907.10537 - "We use this new quantum sensor to measure the gravitational acceleration with a relative sensitivity of 1.7×10⁻⁵, representing the first realisation of an atomic interferometry gravimeter based on a single-photon transition." Per-shot: 1.7×10⁻⁵ × 9.81 m/s² = 1.7×10⁻⁴ m/s²; 2T = 30 ms. Dominant noise: interferometry laser phase noise.
- Mazzoni, Zhang, Del Aguila, Salvi, Poli, Tino, *Phys. Rev. A* 92, 053619 (2015), DOI: 10.1103/PhysRevA.92.053619 - ⁸⁸Sr Bragg LMT gravimeter: "We demonstrate large momentum transfer to the atoms up to eight photon recoils and the use of the interferometer as a gravimeter with a sensitivity δg/g = 4×10⁻⁸." Per-shot: 4×10⁻⁸ × 9.81 = 3.9×10⁻⁷ m/s². Pre-2020; included for context.

No published Sr gravimeter post-2020 beats Rb/Cs Raman gravimeters on Earth gravity in m/s²/√Hz. JILA and NIST Sr work in this period emphasises optical clocks, not gravity sensing.

---

## Topic 3 - Cold-atom interferometers in microgravity

**TL;DR.** The most consequential 2020+ microgravity AI milestone is NASA's Cold Atom Lab (CAL) on the ISS: the first Mach–Zehnder interferometer in space (Williams et al., *Nat. Commun.* 2024) - but at T = 0.5 ms it is *not* yet a gravimetry benchmark. MAIUS-1 demonstrated BEC and matter-wave interferometry on a sounding rocket (Lachmann et al., *Nat. Commun.* 2021); **MAIUS-2 launched at 08:30 LT on 2 December 2023 from Esrange (Sweden)** - Rb BEC was produced in flight but K BEC did not form as planned; MAIUS-3 remains pending. ICE (parabolic flight) demonstrated dual-species K–Rb interferometry in microgravity but at the ~10⁻⁴ Eötvös-parameter level - far from Earth-gravimeter precision.

- Williams et al., *Nat. Commun.* 15, 6414 (2024), DOI: 10.1038/s41467-024-50585-6 - "A three-pulse Mach–Zehnder interferometer was studied to understand the influence of ISS vibrations. Additionally, Ramsey shear-wave interferometry was used to manifest interference patterns in a single run that were observable for over 150 ms free-expansion time. Finally, the CAL AI was used to remotely measure the Bragg laser photon recoil as a demonstration of the first quantum sensor using matter-wave interferometry in space." ⁸⁷Rb; Bragg; T = 0.5 ms; limited by ISS vibrations.
- Lachmann et al., *Nat. Commun.* 12, 1317 (2021), DOI: 10.1038/s41467-021-21628-z - "On 23 January 2017, as part of the sounding-rocket mission MAIUS-1, we created Bose–Einstein condensates in space and conducted 110 experiments central to matter-wave interferometry, including laser cooling and trapping of atoms in the presence of the large accelerations experienced during launch."
- MAIUS-2: SSC Space Center press release: "At 08:30 LT on December 2, 2023, the MAIUS-2 rocket was launched from the Esrange Space Center outside Kiruna" - confirmed by Leibniz Universität Hannover. Rb BEC produced; K BEC did not form. MAIUS-3 launch pending.
- Barrett, Condon et al., *AVS Quantum Sci.* 4, 014401 (2022), DOI: 10.1116/5.0076502 - ICE parabolic flight ⁸⁷Rb/³⁹K simultaneous interferometer; Eötvös parameter measured to ~3×10⁻⁴ in 0-g.

These platforms are not yet gravimetry benchmark targets (their interrogation times and demonstrated phase noise are outside the gravimetry regime), but their published noise/T parameters are useful for qgrav microgravity-mode simulation cross-checks.

---

## Topic 4 - Spaceborne missions using atom interferometers

**TL;DR.** No spaceborne atom gravimeter is yet operating. CARIOQA (ESA/EU Horizon Europe) is in Phase A/B (2024–2026) targeting a pathfinder launch within this decade. MAGIS-100 is under construction at Fermilab as a 100-m vertical Sr clock-transition gradiometer; AION-10 is the UK counterpart. China's space-station cold-atom interferometer has been on orbit since December 2022 for equivalence-principle tests, not gravimetry.

- CARIOQA - CORDIS project IDs 101135075 (Phase A) and 101189541 (Phase B). EU Horizon Europe target language: "the [Quantum Space Gravimetry] Pathfinder mission shall be launched within this decade, paving the way for the deployment of an EU [Quantum Space Gravimetry] mission within the next decade." Forward-looking; no in-flight benchmark numbers exist yet.
- Léveque et al. (CNES), arXiv:2211.01215; SPIE 12777, 127773L (2023), DOI: 10.1117/12.2690536 - "The main objective of the CARIOQA Pathfinder Mission is to demonstrate the operation of a quantum accelerometer in space using a simplified payload. The purpose of this mission is to increase the TRL of the instrument up to 8."
- MAGIS-100: Abe et al., *Quantum Sci. Technol.* 6, 044003 (2021), DOI: 10.1088/2058-9565/abf719 - 100 m Sr clock-transition baseline at Fermilab. Temples (Fermilab), "MAGIS-100: Current Status and Outlook," OSTI 2432450 (Aug 2024).
- AION: Badurina et al., *JCAP* 05, 011 (2020), arXiv:1911.11755, DOI: 10.1088/1475-7516/2020/05/011 - "AION-100, we assume T = 1.4 s, which corresponds to a 10 m atom interferometer setup in launch mode." Cold-Sr architecture.
- China Space Station CAI: Liu et al., *npj Microgravity* 9, 58 (2023), DOI: 10.1038/s41526-023-00306-y - equivalence-principle test payload on Mengtian module from Dec 2022. Passed sinusoidal vibration (5.6 g peak), random vibration (4.28 g RMS), thermal 15–32 °C; 2-year planned lifetime. Not a gravimeter per se.

These spaceborne projects do *not* yet provide a regression target with published in-space m/s²/√Hz numbers, and their architectures (clock transition, single-photon, T > 1 s) differ substantially from qgrav's Rb Raman model.

---

## Topic 5 - Industry / commercial atom gravimeters with published specs

**TL;DR.** Only the Exail (formerly Muquans / iXblue) AQG product line has peer-reviewed, third-party-validated performance numbers. Three independent peer-reviewed evaluations (Cooke 2021, Antoni-Micollier 2022, Glässel 2025) confirm ~500 nm/s²/√Hz sensitivity and ~10 nm/s² 1-h precision. AOSense, ColdQuanta/Infleqtion, and Vector Atomic do not publish peer-reviewed sensitivity benchmarks for their gravimeters as of mid-2025.

- **Ménoret et al., *Sci. Rep.* 8, 12300 (2018)**, DOI: 10.1038/s41598-018-30608-1 - "The resulting sensor measures gravity at a 2 Hz repetition rate with a sensitivity of 500 nm·s⁻²·Hz⁻¹/² and a long term stability below 10 nm·s⁻² with a short installation and warm-up time." (500 nm/s²/√Hz = 5.0×10⁻⁷ m/s²/√Hz; 10 nm/s² = 1.0×10⁻⁸ m/s².) Already in regression set.
- **Cooke et al.**, AQG-B01 first user evaluation (2021) - "We report the repeatability to be better than 50 nm s⁻²." (50 nm/s² = 5.0×10⁻⁸ m/s².)
- **Antoni-Micollier et al., *Geophys. Res. Lett.* 49, e2022GL097814 (2022)** - Mt Etna volcanic monitoring, "world's first detection of gravity changes induced by volcanic processes" with a quantum gravimeter.
- **Glässel et al., *J. Geod.* 99, 73 (2025)**, DOI: 10.1007/s00190-025-01995-x - quoted above; AQG-A02 and AQG-B10 confirmed at 500 nm/s²/√Hz and 10 nm/s² @ 1 h; combined uncertainty ~100 nm/s² vs. the BKG FG5 reference.
- **Janvier et al., arXiv:2201.03345 (2022) / *Phys. Rev. A*** - Exail DQG (differential quantum gravimeter); arXiv:2405.10844: "long-term stability of 0.15 E = 1.5×10⁻¹⁰ s⁻²" (gradiometer mode); "a sensitivity of about 60 E/√τ for the gradient with a long-term stability around 1 E."

AOSense and Infleqtion datasheets describe instruments but do not publish independently validated sensitivity numbers (flagged **manufacturer-only**).

---

## Topic 6 - Industry players: AOSense, Q-CTRL, Vector Atomic

**TL;DR.** None of these three companies has published a peer-reviewed atom-gravimeter sensitivity number to the level of detail Exail does. They should **not** be used as quantitative regression targets in qgrav. They are nonetheless important for ecosystem context.

- **Vector Atomic** (GAINS gravimeter, Pleasanton, CA): operates an 8-L strapdown ⁸⁷Rb Raman gravimeter; field-validated at RIMPAC 2022. Per Vector Atomic / BusinessWire press release dated 27 March 2023 ("Vector Atomic Validates Quantum Navigation Sensor at Sea"): "GAINS was operated continuously at-sea for 20+ days as part of the TTCP Alternative PNT Challenge at RIMPAC 2022, the world's largest international maritime exercise." The ION GNSS+ 2023 abstract (paper ID 15240) states GAINS performance "surpassing 1 mGal gravimeter precision and accuracy for all relevant navigation timescales" (1 mGal = 1×10⁻⁵ m/s²). Conference-grade, not peer-reviewed.
- **Q-CTRL** (Sydney) - focuses on quantum-control optimisation of LMT pulses rather than complete gravimeters. Saywell et al., *Nat. Commun.* 14, 7626 (2023), DOI: 10.1038/s41467-023-43374-0 - "Enhancing the sensitivity of atom-interferometric inertial sensors using robust control" reports software-defined Bragg-pulse fidelity improvements (no end-to-end gravimeter sensitivity number competitive with Freier/Hu/Ménoret). Marketing material claims "over 500× improvements in the ability of quantum sensors for gravity based on cold atoms to resist the interference caused when they're operated on real platforms like airplanes or ships" - flagged as **not peer-reviewed**.
- **AOSense** (Sunnyvale, CA): product page states "delivered its first commercial compact gravimeter to an aerospace customer in 2010" and a "20 Hz sampling rate". No peer-reviewed sensitivity benchmark published; **manufacturer spec only**.

---

## Topic 7 - Top-cited atom-gravimeter sensitivity benchmarks post-2018

**TL;DR.** Five papers dominate citations as 2018–2024 atom-gravimeter benchmarks: Ménoret 2018 (AQG, *Sci. Rep.*), Wu 2019 (mobile, *Sci. Adv.*), Bidel 2018/2020 (marine/airborne, *Nat. Commun./J. Geod.*), Stray 2022 (gradiometer cartography, *Nature*), and Xu 2022 (HUST-QG, *Metrologia*). Panda 2024 (*Nature*, lattice AI) is the most-cited 2024 result.

1. **Ménoret et al., *Sci. Rep.* 8, 12300 (2018), DOI: 10.1038/s41598-018-30608-1.** Already in regression set. 500 nm/s²/√Hz = 5.0×10⁻⁷ m/s²/√Hz; <10 nm/s² over 1 month. T ≈ 60 ms. ⁸⁷Rb; 2ℏk.
2. **Wu, Pagel, Malek, Nguyen, Zi, Scheirer, Müller, *Sci. Adv.* 5, eaax0800 (2019), DOI: 10.1126/sciadv.aax0800.** Verbatim: "The tidal gravity measurements achieve a sensitivity of 37 μGal/√Hz (1 μGal = 10 nm/s²) and a long-term stability of better than 2 μGal, revealing ocean tidal loading effects and recording several distant earthquakes." Field: "the mobility allows us to measure gravity in the field with a resolution of around 0.5 mGal/√Hz, depending on environmental noise." Conversions: 37 μGal/√Hz = 3.7×10⁻⁷ m/s²/√Hz; 0.5 mGal/√Hz = 5.0×10⁻⁶ m/s²/√Hz; 2 μGal = 2.0×10⁻⁸ m/s². T = 130 ms; ⁸⁷Rb; 2ℏk; pyramidal MOT. Limiting noise: vibration (field), Raman phase noise (lab).
3. **Bidel et al., *Nat. Commun.* 9, 627 (2018) (marine), DOI: 10.1038/s41467-018-03040-2** and **Bidel et al., *J. Geod.* 94, 20 (2020) (airborne), DOI: 10.1007/s00190-020-01350-2**. Static lab: 0.8 mGal/√Hz = 8.0×10⁻⁶ m/s²/√Hz, 0.17 mGal lab accuracy; airborne errors 0.6–1.3 mGal under filtering. T = 20 ms (intentionally short for dynamic operation).
4. **Stray, Lamb, Kaushik et al., *Nature* 602, 590 (2022), DOI: 10.1038/s41586-021-04315-3.** Birmingham field gradiometer: "average short-term sensitivity of (466 ± 8) E/√Hz and a statistical uncertainty of 20 E within 10 min of measurement." 466 E/√Hz = 4.66×10⁻⁷ s⁻²/√Hz (gradient - not directly comparable to gravimeter m/s²/√Hz). T = 145 ms; ⁸⁷Rb; outdoor field demonstration.
5. **Xu et al., *Metrologia* 59, 055001 (2022), DOI: 10.1088/1681-7575/ac8258.** HUST-QG: 24 μGal/√Hz = 2.4×10⁻⁷ m/s²/√Hz; combined uncertainty 3 μGal = 3.0×10⁻⁸ m/s²; ICAG degree of equivalence 1.3 μGal = 1.3×10⁻⁸ m/s². T ≈ 300 ms; ⁸⁷Rb; 2ℏk Raman.
6. **Panda, Tao, Ceja, Khoury, Tino, Müller, *Nature* 631, 515 (2024), DOI: 10.1038/s41586-024-07561-3.** Berkeley lattice interferometer / source-mass attraction: 6.2 nm/s² accuracy = 6.2×10⁻⁹ m/s². Cs; optical lattice held atoms for up to 70 s. Limiting noise: laser-beam tilt jitter, mitigated by resonant cavity filtering.
7. **Hu et al., *Phys. Rev. A* 88, 043610 (2013), DOI: 10.1103/PhysRevA.88.043610** (already in regression set; pre-2020 anchor) - verbatim: "a short-term sensitivity of about 4.2 μGal/√Hz (1 μGal = 1×10⁻⁸ m/s²) is reached, which improves the sensitivity by a factor of 2 compared with the former best reported value." Conversion: 4.2 μGal/√Hz = 4.2×10⁻⁸ m/s²/√Hz. ⁸⁷Rb; 2ℏk Raman.
8. **Freier et al., *J. Phys. Conf. Ser.* 723, 012050 (2016), DOI: 10.1088/1742-6596/723/1/012050** (already in regression set) - abstract: "the best-reported performance of mobile atomic gravimeters to date with an accuracy of 39 nm/s² and long-term stability of 0.5 nm/s², short-term noise of 96 nm/s²/√Hz." Re-verified by Glässel 2025: "demonstrating an uncertainty of 39 nm/s², a long-term stability of 0.5 nm/s² and a short-term noise of 96 nm s⁻² Hz⁻¹/²."

---

## Recommendations for qgrav v1.1.0 regression targets

**TL;DR.** Retain all three existing targets (Freier 2016, Hu 2013, Ménoret 2018) - each is still best-in-class for its niche. Add **two** new 2020+ benchmark targets to broaden coverage: HUST-QG 2022 (transportable, full ICAG cross-validation) and Wu 2019 (mobile/field). Optionally add Stray 2022 if gradiometer simulation is in scope, and Karcher 2018 if accuracy-budget modelling is in scope.

| Action | Target | Rationale |
|---|---|---|
| **Keep** | Freier 2016 (DOI 10.1088/1742-6596/723/1/012050) | Still the published record for long-term stability of any mobile atom gravimeter (0.5 nm/s²). No 2020+ paper from HU Berlin or any other lab supersedes it. Re-verified in 2025 by BKG (Glässel et al.). |
| **Keep** | Hu 2013 (DOI 10.1103/PhysRevA.88.043610) | Still the published record for short-term sensitivity of a laboratory ⁸⁷Rb Raman gravimeter (4.2 μGal/√Hz = 4.2×10⁻⁸ m/s²/√Hz). HUST-QG 2022 is intentionally degraded for transportability. |
| **Keep** | Ménoret 2018 (DOI 10.1038/s41598-018-30608-1) | Canonical industrial reference; now triply validated by Cooke 2021, Antoni-Micollier 2022, and Glässel 2025. |
| **Add - Tier 1** | Xu 2022, HUST-QG (DOI 10.1088/1681-7575/ac8258) | First modern transportable gravimeter with rigorous full systematic budget and an ICAG metrology anchor. 24 μGal/√Hz, 3 μGal combined U, 1.3 μGal ICAG equivalence. Excellent regression target for transportable-class qgrav configurations. |
| **Add - Tier 1** | Wu 2019, Berkeley mobile (DOI 10.1126/sciadv.aax0800) | Best mobile/field benchmark with peer-reviewed lab *and* field sensitivity numbers; bridges qgrav lab and mobile regimes. 37 μGal/√Hz lab, 0.5 mGal/√Hz field. |
| **Add - Tier 2 (optional)** | Stray 2022, Birmingham gradiometer (DOI 10.1038/s41586-021-04315-3) | Only if qgrav supports gradiometer mode. 466 E/√Hz outdoor field. |
| **Add - Tier 2 (optional)** | Karcher 2018, LNE-SYRTE ultracold CAG (DOI 10.1088/1367-2630/aaf07d) | Best published accuracy budget (13 nm/s² systematic from wavefront aberrations, 10 nm/s² statistical) for validating qgrav's systematic-error modelling. |

**Trigger thresholds for future updates.**
- If CARIOQA pathfinder publishes in-space data with verified ≤10⁻⁸ m/s²/√Hz (expected late this decade per CORDIS), adopt as the first true spaceborne benchmark.
- If Panda/Müller (Berkeley → Arizona) publish a free-running gravimetric sensitivity in m/s²/√Hz from the lattice AI (currently only per-shot and source-mass-accuracy numbers exist), add as a lattice-mode target.
- If Vector Atomic or AOSense publish a peer-reviewed sensitivity number in m/s²/√Hz (presently only conference and marketing), reconsider for industrial-deployment regression coverage.

---

## Caveats

1. Most published "sensitivity" numbers are Allan deviations referenced to 1 s and do not necessarily extrapolate cleanly to longer integration times due to vibration spectra, MOT-load drift, and Coriolis aliasing. Match qgrav simulations to the *integration time at which the source paper actually quoted the number*.
2. Gradiometer numbers (E/√Hz) and gravimeter numbers (m/s²/√Hz) are different observables and must **not** be cross-compared directly in regression suites.
3. Industry datasheets without peer review (AOSense, Infleqtion, Vector Atomic gravimeter) are flagged as **manufacturer spec** and should not anchor regression tests. The Q-CTRL "500×" improvement language is also **not peer-reviewed**.
4. Sr / clock-transition / lattice / spaceborne instruments use architectures (single-photon recoil, optical-lattice hold, T > 1 s) that may or may not be in qgrav's modelling scope - verify before adopting.
5. The CARIOQA timeline ("launched within this decade") is forward-looking strategy language from EU/CNES documents, not a published commitment.
6. MAIUS-2 launched on 2 December 2023 but the K BEC component did not form as planned; a peer-reviewed performance paper has not yet appeared as of this writing. Treat MAIUS-2 as "launched, partial success, no published gravimetry benchmark."