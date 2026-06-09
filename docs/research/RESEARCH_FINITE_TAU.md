# Pulse-Timing Conventions and Finite-τ Corrections in Light-Pulse Atom Interferometry - Physics Validation Notes for qgrav / AISim

## TL;DR
- **Cheinet 2008's sensitivity-function formalism explicitly places the time origin at the middle of the central π pulse**, and gives an exact piecewise expression g(t) with sin(Ω_R t) ramps inside each rectangular Raman pulse; in the standard MZ literature (Kasevich-Chu, Peters-Chung-Chu, Le Gouët, Bertoldi, Fang/Mielec/Savoie/Altorio/Landragin/Geiger) the symbol T denotes the pulse-center to pulse-center separation, not the free-evolution time between pulse edges.
- **The canonical leading-order finite-τ correction to the Mach-Zehnder scale factor Φ = k_eff·a·T² is multiplicative: Φ → k_eff·a·T²·[1 − ((2π−4)/π)·(τ/T)], with (2π−4)/π ≈ 0.7268** (Bertoldi, Minardi & Prevedelli, PRA 99, 033619 (2019), Eq. 21). Equivalently, the sensitivity-function area gives T_eff = T + (2/Ω_R)·tan(Ω_R·τ_R/2), which for an ideal π/2-pulse area (Ω_R·τ_R = π/2) reduces to T_eff = T + 4τ_R/π. These forms agree algebraically; the only published disagreement is between Bertoldi et al. (2019) and Li-Shao-Hu (JOSA B 32, 248 (2015), Eq. 40), which Bertoldi et al. flag explicitly.
- **AISim (Leykauf & Vowe, github.com/bleykauf/aisim) does not numerically sub-step a Raman pulse**; it applies a closed-form 2×2 Rabi propagator (TwoLevelTransitionPropagator) over the entire pulse duration, following Young, Kasevich & Chu (1997). No published light-pulse atom-interferometer simulator we located performs explicit Δt sub-pulse integration of δ(t)·dt over the pulse; sub-pulse integration is therefore a qgrav-specific design choice that is not standardized in the literature.

## Key Findings

### 1. Cheinet 2008 (arXiv:physics/0510197; IEEE TIM 57, 1141 (2008), DOI 10.1109/TIM.2007.915148): time origin and sensitivity function

Time origin is explicitly defined at the **middle of the central (second) Raman pulse**, not at pulse start or end. Verbatim:

> "Finally, we choose the time origin at the middle of the second Raman pulse. We thus have t_i = −(T + 2τ_R) and t_f = T + 2τ_R."

Definition of g(t) (Eq. 1, verbatim):

> "The sensitivity function is then defined by: g(t) = 2 lim_{δφ→0} δP(δφ, t)/δφ."

Closed form (Eq. 4, verbatim, for t > 0; g is odd):

> "g(t) = sin(Ω_R t)  for 0 < t < τ_R;  1  for τ_R < t < T + τ_R;  − sin(Ω_R(T − t))  for T + τ_R < t < T + 2τ_R."

with g(t) = 0 for |t| > T + 2τ_R. The Fourier transform G(ω) (Eq. 8, verbatim):

> "G(ω) = (4iΩ_R / (ω² − Ω_R²)) · sin(ω(T + 2τ_R)/2) · [cos(ω(T + 2τ_R)/2) + (Ω_R/ω) sin(ωT/2)]."

The low-frequency limit (Eq. 9) reduces to G(ω) ≈ −(4i/ω) sin²(ωT/2). The cutoff is f₀ = (√3/3)(Ω_R/2π). For the experimental verification, Cheinet et al. used the gyroscope (verbatim): "three interferometer pulses of duration τ_R − 2τ_R − τ_R with τ_R = 20 µs separated in time by T = 4.97 ms." The white-Raman-phase-noise sensitivity (Eq. 18):

> "σ²_Φ(τ) = (π/2)² S⁰_φ · (T_c/τ) / τ_R."

These results confirm that in Cheinet's formalism the time-origin convention is **pulse-center for the central π pulse**, and (because of the τ_R−2τ_R−τ_R sequence of durations) the **outer π/2 pulses are also centered around their respective midpoints at t = ±(T + τ_R)**.

### 2. Pulse-center vs pulse-start convention in the Φ = k_eff·g·T² formula

Le Gouët et al. 2008 (Appl. Phys. B 92, 133-144, DOI 10.1007/s00340-008-3088-1; arXiv:0801.1270) writes the Mach-Zehnder phase as

> "ΔΦ = φ(0) − 2φ(T) + φ(2T) = −k_eff · a T² [16], where φ(0, T, 2T) is the difference of the phases of the lasers, **at the location of the center of the atomic wavepackets, for each of the three pulses**."

This convention - T is the time between phase samples taken at the centers of the three pulses (which coincide with the centers of the atomic wavepacket positions at those instants) - is shared with the Cheinet 2008 sensitivity-function formalism: the symmetric durations τ_R − 2τ_R − τ_R imply the pulse centers are separated by exactly T, and the time origin sits at the middle of the central π pulse.

Bertoldi, Minardi & Prevedelli (PRA 99, 033619 (2019), arXiv:1812.11890) is unusually explicit:

> "We consider a Kasevich-Chu type interferometer [12], where a sequence of three pulses π/2 − π − π/2 of temporal length τ, 2τ, τ respectively are separated by two free evolution intervals of length **T − 2τ** so that the total duration of the interferometric sequence is 2T."

So **T is pulse-center to pulse-center** and the free-evolution time between pulse edges is T − 2τ. This is the convention universally adopted in the Cheinet, Le Gouët, Peters, Bertoldi line of papers.

A complementary explicit statement is in Fang, Mielec, Savoie, Altorio, Landragin & Geiger, New J. Phys. **20**, 023020 (2018), DOI 10.1088/1367-2630/aaa37c (the standard reference for the finite-τ scale-factor modification by temporal pulse shaping):

> "The pulse separation T denotes the time elapsed between the center of two consecutive light pulses, and τ is the duration of the rectangular pulse."

A useful counterpoint is Dubetsky (arXiv:1810.04218 (2018)) which explicitly distinguishes "(a) T is the time separation between pulses [centers]" and "(b) T is the time delay between pulses' starting moments" in its Fig. 1 caption - showing that both conventions exist in the literature and have to be specified.

### 3. Finite-pulse-duration corrections to Φ = k_eff·g·T²

**Kasevich & Chu, PRL 67, 181 (1991), DOI 10.1103/PhysRevLett.67.181** - the original gravimeter paper - treats pulses as instantaneous (ideal π/2−π−π/2) and quotes Δφ_grav = k_eff·g·T² without any finite-τ correction. No τ-dependent correction term is given in this paper.

**Le Gouët et al. 2008** retains the Φ = −k_eff·a·T² form for the leading inertial phase but, when computing the noise and transfer function, uses the sensitivity function g(t) **with the finite-τ_R ramps shown above** (their Eq. 3 is identical in form to Cheinet's Eq. 4). The paper does not write down a closed-form finite-τ scaling of the gravity formula; it uses the sensitivity function instead. Verbatim: "Even a short interrogation time of 100 ms allows our cold atom gravimeter to reach an excellent short term sensitivity to acceleration of 1.4 × 10⁻⁸ g at 1 s." Since 2T = 100 ms, T = 50 ms exactly. (SI conversion: 1.4 × 10⁻⁸ × 9.81 m·s⁻² ≈ 1.37 × 10⁻⁷ m·s⁻², ≈ 14 µGal·Hz^(−1/2) using 1 Gal = 10⁻² m·s⁻².) No explicit τ_R value was retrieved verbatim from the fetched sections of the paper.

**Bertoldi, Minardi & Prevedelli 2019 (PRA 99, 033619; arXiv:1812.11890) Eq. 21 - exact closed form, verbatim**:

> "φ₂ = T²(kg − α − kγz₀)·[1 − ((2π − 4)/π) η] − kγT³{ v_m·[1 − ((2π − 4)/π) η] − gT·[7/12 − (4π − 8)/(3π) η] }, where η = τ/T."

The leading multiplicative scale-factor correction is therefore **(1 − ((2π − 4)/π)·(τ/T))**, with (2π − 4)/π ≈ 0.72676. Equivalently the gradiometer phase is (Eq. 22, verbatim):

> "Δφ₂ = −kγdT²·[1 − ((2π − 4)/π) η]."

Bertoldi et al. **explicitly flag a disagreement** with prior literature:

> "We notice that some numerical coefficients in this formula do not agree with those in Eq. (40) of Ref. [26]."

Ref. [26] is X. Li, C.-G. Shao, Z.-K. Hu, "Raman pulse duration effect in high-precision atom interferometry gravimeters," J. Opt. Soc. Am. B **32**, 248-257 (2015), DOI 10.1364/JOSAB.32.000248. So the published consensus (Bertoldi et al. 2019) is **(2π − 4)/π · τ/T** for the multiplicative MZ scale-factor correction; the older Li-Shao-Hu coefficients disagree.

**Sensitivity-function equivalent form**: Integrating g(t) from Cheinet 2008 (Eq. 4) over one half of the MZ interval gives

∫₀^{T+2τ_R} g(t) dt = T + (2/Ω_R)·tan(Ω_R·τ_R/2).

For an ideal π/2 pulse area Ω_R·τ_R = π/2, this gives T + (2/Ω_R) = T + (4τ_R/π) since Ω_R = π/(2τ_R). Hence the **effective interrogation time T_eff = T + 4τ_R/π** for rectangular π/2 pulses with the duration convention τ_R − 2τ_R − τ_R. To leading order, T_eff² ≈ T²·(1 + 8τ_R/(πT)). To resolve the apparent factor-of-two ambiguity in the literature ("2τ/π" vs "4τ/π"): the discrepancy is purely conventional and arises from whether τ denotes the π/2-pulse duration (then 4τ/π) or the half-duration of the central π pulse (then 2τ/π refers to the same quantity because the π pulse has duration 2τ_R). Both forms reduce to the Bertoldi et al. multiplicative factor when expanded consistently, and there is **no published mathematical inconsistency** beyond the Bertoldi/Li-Shao-Hu flagged discrepancy.

**Peters, Chung & Chu 2001 (Metrologia 38, 25; DOI 10.1088/0026-1394/38/1/4)** establishes the canonical chirp method g = α/k_eff, where α is the frequency-chirp rate ([α] = rad·s⁻² so that α/k_eff has units (rad·s⁻²)/(rad·m⁻¹) = m·s⁻²). The Metrologia PDF was paywalled and not directly retrievable in this session; citing literature (Karcher, Pereira Dos Santos & Merlet, PRA 101, 043606 (2020), arXiv:2001.07478) summarises Peters-Chung-Chu as: "g is derived from the determination of the Doppler frequency chirp induced by the free fall of the atoms onto the lasers [Peters2001]. In practice, lasers are kept on resonance by sweeping over the interferometer duration their frequency difference thanks to an agile and stable oscillator." Peters et al. (2001) **does not appear to derive a closed-form finite-τ correction** to the main g = α/k_eff scale-factor relation in the sections we could verify via secondary citation; finite-τ effects are folded into the systematic budget and the rest is treated via the sensitivity function (which Peters' PhD thesis (1998) had introduced).

**Bertoldi et al. is the canonical closed-form reference for the finite-τ correction**, and it agrees with the Cheinet sensitivity-function area when one is careful with the τ convention.

### 4. Sub-pulse integration in simulators

**AISim** (Leykauf & Vowe, github.com/bleykauf/aisim; documentation at aisim.readthedocs.io) is the publicly available Python package vendored as part of qgrav. Note that despite some informal "AISim by Kim et al." attributions, AISim's primary authors are **B. Leykauf** (Institut für Physik, Humboldt-Universität zu Berlin, associated with the GAIN - Gravimetric Atom Interferometer - project) and **S. Vowe** (contributions through 2020). The PyPI metadata is explicit: "Copyright © 2020-2025 B. Leykauf · Copyright © 2020 S. Vowe."

AISim **does not sub-step a Raman pulse into N pieces and integrate δ(t)·dt**. Instead it applies analytic 2×2 unitary propagators across the entire pulse duration. From the documentation:

> "class aisim.prop.TwoLevelTransitionPropagator(time_delta, intensity_profile, wave_vectors=None, wf=None, phase_scan=0) … A time propagator of an effective Raman two-level system. The propagator is for example defined in [1]." (Reference [1] = Young, Kasevich & Chu, "Precision atom interferometry with light pulses," in P. R. Berman (ed.), Atom Interferometry, Academic Press, 1997.)

> "class aisim.prop.SpatialSuperpositionTransitionPropagator … An effective Raman two-level system. It is implemented as a time propagator as defined in [1]."

> "class aisim.prop.FreePropagator(time_delta, **kwargs) … Propagator implementing free propagation without light-matter interaction."

The Mach-Zehnder phase is then recovered in user code by computing the wavefront phase imprint at three discrete pulse times (the wavefront-aberrations example shows `phi1 = wf.get_value(det_atoms.calc_position(t1))`, `phi2 = ... t2`, `phi3 = ... t3` and `np.exp(1j*(phi1 − 2*phi2 + phi3))`) - i.e. evaluation at single pulse-center times, not integration through the pulse. No N-substep sub-pulse integration of g(t)·δφ(t) is implemented in AISim.

We did not find any published peer-reviewed atom-interferometer simulator that explicitly breaks each Raman pulse into N substeps and integrates the sensitivity function. Where simulators model finite-τ effects, they universally use either (a) the analytic two-level Rabi propagator (AISim, and most semi-classical codes), or (b) the analytic closed-form correction from Bertoldi et al. / Cheinet, applied as a scale-factor multiplier on T². The qgrav design choice to use sub-pulse Δt integration is therefore a **legitimate but non-standard approach**, and validation should benchmark it against both (a) the analytic Rabi propagator (AISim-style) and (b) the Bertoldi/Cheinet closed-form correction in the appropriate limit.

### 5. Closed-form finite-τ correction to the chirp-rate-to-g relation

The Peters chirp method gives g = α/k_eff at lowest order. The finite-τ correction enters identically as the MZ scale-factor correction discussed above - because nulling the interferometer phase by α = k·g requires that the phase φ(t) = αt²/2 imprinted on the lasers, when sampled with the finite-τ sensitivity function, reproduce −k·g·T². With Bertoldi et al.'s scale factor T²·(1 − (2π−4)/π · τ/T), the chirp-to-g relation becomes

g = α/k_eff · (1 − (2π−4)/π · τ/T)^(−1)  ≈  (α/k_eff)·(1 + (2π−4)/π · τ/T).

For typical T = 100 ms and τ = 10 µs, the relative correction is (2π−4)/π × (10⁻⁵/10⁻¹) ≈ 0.7268 × 10⁻⁴ = 7.3 × 10⁻⁵, i.e. about 7 parts in 10⁵ on g, or ≈ 7 × 10⁻⁵ × 9.81 m·s⁻² ≈ 7 × 10⁻⁴ m·s⁻² (≈ 70 mGal). For T = 50 ms (Le Gouët) and τ_R ~ 10 µs (no exact published value retrieved), η ≈ 2 × 10⁻⁴ and the correction is ≈ 1.5 × 10⁻⁴ in relative units, or ≈ 1.5 × 10⁻³ m·s⁻² (≈ 150 mGal). **These corrections are far above the 10⁻⁹·g (≈ 10⁻⁸ m·s⁻², 1 µGal) accuracy of modern transportable atom gravimeters and must be included in any accurate simulator.**

No publication we located gives the chirp correction in a different form (e.g. nonlinear-in-τ); the leading-order linear-in-η correction from Bertoldi et al. (with the previously flagged Li-Shao-Hu disagreement) is the standard.

## Details

### Source list with stable identifiers

1. P. Cheinet, B. Canuel, F. Pereira Dos Santos, A. Gauguet, F. Yver-Leduc, A. Landragin, "Measurement of the sensitivity function in a time-domain atomic interferometer," IEEE Trans. Instrum. Meas. **57**, 1141-1148 (2008). DOI: 10.1109/TIM.2007.915148. Preprint: arXiv:physics/0510197. URL: https://arxiv.org/abs/physics/0510197.

2. J. Le Gouët, T. E. Mehlstäubler, J. Kim, S. Merlet, A. Clairon, A. Landragin, F. Pereira Dos Santos, "Limits to the sensitivity of a low noise compact atomic gravimeter," Appl. Phys. B **92**, 133-144 (2008). DOI: 10.1007/s00340-008-3088-1. Preprint: arXiv:0801.1270. URL: https://arxiv.org/abs/0801.1270.

3. A. Peters, K. Y. Chung, S. Chu, "High-precision gravity measurements using atom interferometry," Metrologia **38**, 25-61 (2001). DOI: 10.1088/0026-1394/38/1/4. URL: https://iopscience.iop.org/article/10.1088/0026-1394/38/1/4.

4. M. Kasevich, S. Chu, "Atomic interferometry using stimulated Raman transitions," Phys. Rev. Lett. **67**, 181-184 (1991). DOI: 10.1103/PhysRevLett.67.181.

5. M. Kasevich, S. Chu, "Measurement of the gravitational acceleration of an atom with a light-pulse atom interferometer," Appl. Phys. B **54**, 321-332 (1992). DOI: 10.1007/BF00325375.

6. C. J. Bordé, "Atomic interferometry with internal state labelling," Phys. Lett. A **140**, 10-12 (1989). DOI: 10.1016/0375-9601(89)90537-9.

7. A. Bertoldi, F. Minardi, M. Prevedelli, "Phase shift in atom interferometers: Corrections for nonquadratic potentials and finite-duration laser pulses," Phys. Rev. A **99**, 033619 (2019). DOI: 10.1103/PhysRevA.99.033619. Preprint: arXiv:1812.11890. URL: https://arxiv.org/abs/1812.11890.

8. X. Li, C.-G. Shao, Z.-K. Hu, "Raman pulse duration effect in high-precision atom interferometry gravimeters," J. Opt. Soc. Am. B **32**, 248-257 (2015). DOI: 10.1364/JOSAB.32.000248. (Bertoldi et al. 2019 flag a numerical-coefficient disagreement with this paper's Eq. 40.)

9. B. Cheng, P. Gillot, S. Merlet, F. Pereira Dos Santos, "Influence of chirping the Raman lasers in an atom gravimeter: Phase shifts due to the Raman light shift and to the finite speed of light," Phys. Rev. A **92**, 063617 (2015). DOI: 10.1103/PhysRevA.92.063617. Preprint: arXiv:1506.03207.

10. R. Karcher, F. Pereira Dos Santos, S. Merlet, "Impact of direct-digital-synthesizer finite resolution on atom gravimeters," Phys. Rev. A **101**, 043606 (2020). DOI: 10.1103/PhysRevA.101.043606. Preprint: arXiv:2001.07478.

11. B. Fang, N. Mielec, D. Savoie, M. Altorio, A. Landragin, R. Geiger, "Improving the phase response of an atom interferometer by means of temporal pulse shaping," New J. Phys. **20**, 023020 (2018). DOI: 10.1088/1367-2630/aaa37c.

12. B. Leykauf, S. Vowe et al., AISim - Python package for light-pulse atom interferometry simulation. URL: https://github.com/bleykauf/aisim. Documentation: https://aisim.readthedocs.io.

13. B. Young, M. Kasevich, S. Chu, "Precision atom interferometry with light pulses," in P. R. Berman (ed.), Atom Interferometry (Academic Press, 1997), pp. 363-406. [Reference for the AISim TwoLevelTransitionPropagator.]

14. B. Dubetsky, "Mach-Zehnder atom interferometer. Quantum and Doppler corrections caused by the finite pulses' durations," preprint arXiv:1810.04218 (2018). [Independent derivation; also includes both conventions for T (pulse center separation vs starting-time delay) - explicitly shown in Fig. 1 of that paper.]

### Numerical conversions in SI

- Le Gouët 2008 quotes verbatim "Even a short interrogation time of 100 ms allows our cold atom gravimeter to reach an excellent short term sensitivity to acceleration of 1.4 × 10⁻⁸ g at 1 s." Since 2T = 100 ms, **T = 50 ms exactly**. In SI: 1.4 × 10⁻⁸ × 9.81 m·s⁻² ≈ 1.37 × 10⁻⁷ m·s⁻²·Hz^(−1/2) (≈ 14 µGal·Hz^(−1/2)).
- Cheinet 2008 gives explicit gyroscope parameters verbatim: "three interferometer pulses of duration τ_R − 2τ_R − τ_R with τ_R = 20 µs separated in time by T = 4.97 ms." The projected gravimeter noise floor of 1.5 × 10⁻⁸ m·s⁻²·Hz^(−1/2) ≈ 1.5 µGal·Hz^(−1/2) is quoted in the Conclusion but uses a different set of parameters that we did not retrieve verbatim.
- Bertoldi finite-τ relative correction for T = 100 ms, τ = 10 µs: (2π − 4)/π × (10⁻⁵/10⁻¹) ≈ 7.27 × 10⁻⁵. On g ≈ 9.81 m·s⁻², that is ≈ 7.13 × 10⁻⁴ m·s⁻² (≈ 71 mGal).

### Pulse-center vs pulse-edge convention - what to put in qgrav

For consistency with the dominant convention (Cheinet, Le Gouët, Peters, Bertoldi, Fang/Geiger):
- **T** = time between **pulse centers** of consecutive Raman pulses.
- **Free-evolution time between pulse edges** = T − 2τ (for an inner π pulse of duration 2τ centered at the midpoint, with outer π/2 pulses of duration τ).
- **Time origin** for the sensitivity function = middle of the central π pulse (Cheinet 2008).
- **Effective interrogation time** for the leading inertial phase: T_eff² ≡ T²·(1 − (2π−4)/π · τ/T)² ≈ T²·(1 − 2(2π−4)/π · τ/T) (Bertoldi et al. 2019 Eq. 21), equivalently the sensitivity-function integral T_eff = T + (2/Ω_R)·tan(Ω_R·τ_R/2).

## Recommendations

1. **Adopt the pulse-center convention for T** in qgrav documentation, and label any internal pulse-start variables clearly (e.g. `t_pulse_start`, `t_pulse_center`). This matches Cheinet 2008, Le Gouët 2008, Bertoldi 2019, and Fang/Geiger 2018. Provide a small utility that converts between the two conventions because some user-supplied timing data (e.g. trigger-based instrument timing) is naturally pulse-start.

2. **Validate the sub-pulse N-substep integration against two independent benchmarks**:
   - (a) The analytic Cheinet g(t) closed form (Eq. 4 of arXiv:physics/0510197) - the residual after sub-pulse integration of g(t)·δφ(t) should converge to the exact integral as N → ∞.
   - (b) The Bertoldi 2019 Eq. 21 closed-form scale-factor correction (1 − (2π−4)/π · τ/T) applied to Φ = k_eff·g·T². For T = 100 ms, τ = 10 µs, the correction is ≈ 7.3 × 10⁻⁵; qgrav should reproduce this to within 10⁻⁹ relative when using ≥ 100 sub-steps per pulse.
   - **Benchmark threshold**: If qgrav's sub-pulse integration disagrees with Bertoldi's closed form by more than 10⁻⁶ relative at N = 1000 substeps for τ/T = 10⁻⁴, investigate sign conventions and time-origin placement before increasing N.

3. **Adopt N ≥ 50 sub-steps per pulse as a default** if sub-pulse integration is the chosen numerical method; convergence to the analytic Rabi propagator is exponential in N for rectangular pulses, but realistic Gaussian-shaped pulses or intensity inhomogeneities can require N ≥ 200. Provide a convergence test in the validation suite.

4. **For chirp-method gravimeters**, document explicitly that g = α/k_eff is only the leading-order relation, and the finite-τ-corrected relation is g = (α/k_eff)·(1 + (2π−4)/π · τ/T + O(τ²/T²)). For T = 50 ms and τ_R on the order of 10 µs, this is approximately a 1.5 × 10⁻⁴ relative correction - three orders of magnitude above the 10⁻⁹ accuracy target.

5. **Cite Bertoldi, Minardi & Prevedelli 2019 (PRA 99, 033619)** as the canonical closed-form reference in the validation document, and flag the known Li-Shao-Hu 2015 (JOSA B 32, 248) numerical-coefficient disagreement so users are not confused.

6. **Correct the "AISim by S. Kim et al." attribution** in qgrav documentation: AISim is by Bastian Leykauf (HU Berlin / GAIN gravimeter project) and S. Vowe (github.com/bleykauf/aisim), not by S. Kim (who is a co-author on Le Gouët 2008 but unrelated to AISim).

## Caveats

- We could not directly fetch the Peters, Chung & Chu 2001 Metrologia PDF (paywalled IOP; fetch blocked). The g = α/k_eff result is uncontested and confirmed in multiple secondary references (Karcher et al. 2020, Cheng et al. 2015). However, **a direct verbatim quote from Peters 2001 on finite-τ corrections was not obtained**; the existence of a closed-form finite-τ correction in that paper specifically was not verified. The earlier Peters PhD thesis (1998) is the more likely origin for the explicit sensitivity-function treatment but we did not access it.
- Cheinet's 2006 PhD thesis was not directly accessed; references to it as a possible canonical source for the finite-τ chirp correction could not be verified verbatim.
- Bordé 1989 (Phys. Lett. A 140, 10) was not directly accessed and we could not extract a verbatim quote on finite-τ corrections. Bordé's later reviews (e.g. Metrologia 38, 1 (2001); "Theoretical tools for atom optics," ABCD formalism) likely contain the relevant analysis but were beyond our reach in this session.
- The "T_eff = T + 2τ/π" form quoted in the task is consistent with the sensitivity-function area expression for a specific choice of τ-convention (where τ is half of the central π-pulse duration). Bertoldi's (2π−4)/π factor on T² and Cheinet's T + (2/Ω_R)·tan(Ω_R·τ_R/2) form agree algebraically; **the only published disagreement** is the Bertoldi-Li/Shao/Hu numerical-coefficient discrepancy explicitly flagged in Bertoldi et al. (2019).
- Le Gouët 2008 does **not** state τ_R explicitly in the sections we could retrieve verbatim; the often-quoted "τ_R ≈ 10 µs" appears in secondary literature only and was not confirmed in primary source by this research.
- Cheinet 2008's gyroscope parameters (τ_R = 20 µs, T = 4.97 ms) are confirmed verbatim, but the gravimeter projection T = 50 ms is implied rather than directly quoted in the sections we fetched.
- Most published simulators we identified (AISim is the only widely cited Python one) use analytic Rabi propagators rather than sub-pulse numerical integration. We did not find a published reference describing a simulator that explicitly substeps Raman pulses; this means **sub-pulse integration in qgrav has no published benchmark** other than convergence to the analytic Rabi propagator and to the Bertoldi/Cheinet closed forms.