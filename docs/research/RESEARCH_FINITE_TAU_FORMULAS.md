# Finite-τ Sensitivity Function and Phase Corrections in Atom-Interferometric Gravimetry

*Research dossier for `docs/RESEARCH_FINITE_TAU_FORMULAS.md` (qgrav / AISim). Every equation below is transcribed from the cited primary source with a verbatim supporting quote. Symbols: k_eff = effective Raman wave vector (rad/m); a or g = acceleration (m/s²); T = interpulse / interrogation time (s, center-to-center unless flagged); τ or τ_R = Raman pulse duration (s); Ω_R / Ω_eff = effective Rabi frequency (rad/s); f = Fourier frequency (Hz); ω = 2πf (rad/s); η = τ/T.*

## TL;DR (overall)
- **The Cheinet 2008 piecewise sensitivity function g(t)** — with sin(Ω_R t) ramps during the finite Raman pulses and ±1 plateaus during free evolution — is exact, published, and directly code-ready; its Fourier transform G(ω) (Eq. 8), low-frequency limit (Eq. 9), and transfer function H(ω)=ωG(ω) follow in closed form.
- **The finite-τ correction to the Mach-Zehnder gravity phase is published in two equivalent closed forms:** the scale factor S_rec = k_eff(T+τ/2)(T+(4/π−3/2)τ) (Fang/Mielec 2018, citing Cheinet's 2006 thesis), equivalent at leading order to the τ/T-expansion Δφ = −(α+k·g)T²(1−2τ/T+4τ/πT) (Shao 2015 / Bertoldi 2019).
- **The Bertoldi 2019 Heisenberg-picture derivation** gives the velocity-averaged finite-τ phase (Eq. 21, factor 1−(2π−4)/π·η on the gravity phase) plus a residual single-shot term δφ₂ = −4θ²(T)sin2φ₂(T) (Eq. 32) that averages to zero over the velocity distribution. The "T+(4/Ω)tan(Ωτ/2)" effective-time form requested in the brief is **not** found in Peters/Chung/Chu 2001 or Le Gouët 2008 and should not be attributed to them.

---

## 1. CHEINET 2008 — Time-domain sensitivity function g(t)

**TL;DR:** g(t) is odd; it equals ±1 during the free-evolution periods and rises sinusoidally as sin(Ω_R t) during the finite Raman pulses. Use Eq. 4 verbatim.

**Source:** P. Cheinet, B. Canuel, F. Pereira Dos Santos, A. Gauguet, F. Yver-Leduc, A. Landragin, "Measurement of the Sensitivity Function in a Time-Domain Atomic Interferometer," *IEEE Trans. Instrum. Meas.* **57**(6), 1141–1148 (2008). Preprint: arXiv:physics/0510197 (https://arxiv.org/abs/physics/0510197).

**The sensitivity function (their Eq. 4)** — time origin at the middle of the central π pulse, valid for t>0, with g odd so g(−t)=−g(t):

```
g(t) =  sin(Ω_R · t)            for   0      < t < τ_R
g(t) =  1                        for   τ_R    < t < T + τ_R
g(t) = −sin(Ω_R · (T − t))       for   T + τ_R < t < T + 2τ_R
g(t) =  0                        for   |t| > T + 2τ_R
```

**Verbatim:** "It is an odd function, whose expression is given here for t > 0: g(t) = { sin(ΩRt) 0 < t < τR ; 1 τR < t < T + τR ; − sin(ΩR(T − t)) T + τR < t < T + 2τR. When the phase jump occurs outside the interferometer, the change in the transition probability is null, so that g(t) = 0 for |t| > T + 2τR."

**Supporting definitions (verbatim):** Definition of g(t) (their Eq. 1): "g(t) = 2 lim δφ→0 δP(δφ, t)/δφ." Pulse sequence: "Three laser pulses, of durations τR − 2τR − τR, separated in time by T, respectively split, redirect and recombine the atomic wave-packets." Rabi frequency: "where ΩR/2π is the Rabi frequency." Operating point: "Usually, the interferometer is operated at Φ = π/2, for which the transition probability is 1/2, to get the highest sensitivity." Time bounds: "We thus have ti = −(T + 2τR) and tf = T + 2τR."

**Underlying single-pulse evolution matrix (their Eq. 3),** from which g(t) is derived (the cos(Ω_R(t−t₀)/2) and sin(Ω_R(t−t₀)/2) terms generate the sinusoidal ramps); setting Ω_R=0 gives the free-evolution matrix. Verbatim: "Setting ΩR = 0 in Mp(t0, t, ΩR, φ) gives the free evolution matrix, which determines the evolution between the pulses."

**Assumptions (verbatim):** "First, the laser waves are considered as pure plane waves... Second, we restrict our calculation to the case of a constant Rabi frequency (square pulses). Third, we assume the resonance condition is fulfilled."

**Units:** g(t) is dimensionless. Ω_R in rad/s; τ_R, T in s. No SI conversion required.

---

## 2. Acceleration-to-phase transfer function |H(ω)|² and its finite-τ correction

**TL;DR:** Cheinet gives the EXACT Fourier transform G(ω) including finite-τ terms (Eq. 8); for ω≪Ω_R it reduces to the familiar sin² form (Eq. 9), giving |H(2πf)|² ∝ sin⁴(πfT). The finite-τ correction is (a) the replacement T→T+2τ_R in the oscillation envelope, and (b) a **first-order** low-pass roll-off with cutoff f₀=(√3/3)(Ω_R/2π) — there is no single multiplicative cos² factor; the exact correction is the full bracket plus the (ω²−Ω_R²) prefactor in Eq. 8.

**Exact Fourier transform of g(t) (their Eq. 8):**

```
G(ω) = [4i·Ω_R / (ω² − Ω_R²)] · sin(ω(T+2τ_R)/2) · [ cos(ω(T+2τ_R)/2) + (Ω_R/ω)·sin(ωT/2) ]
```

**Verbatim:** "We calculate the Fourier transform of the sensitivity function and find: G(ω) = 4iΩR/(ω² − Ω²R) sin(ω(T + 2τR)/2)(cos(ω(T + 2τR)/2) + ΩR/ω sin(ωT/2))."

**Low-frequency approximation (their Eq. 9), ω≪Ω_R:**

```
G(ω) = −(4i/ω)·sin²(ωT/2)
```

**Verbatim:** "At low frequency, where ω << ΩR, the sensitivity function can be approximated by G(ω) = − 4i/ω sin²(ωT/2)."

**Transfer function (verbatim):** "The transfer function is thus given by H(ω) = ωG(ω)." Therefore in the low-frequency limit |H(ω)| = 4 sin²(ωT/2) and **|H(2πf)|² = 16 sin⁴(πfT)**. The familiar acceleration transfer function 16·k_eff²·sin⁴(πfT)/(2πf)⁴ is obtained by multiplying the phase response by k_eff² and dividing by ω⁴ when converting the phase response to an acceleration response (the noise-weighting variance relation is their Eq. 7: (σ_Φ^rms)² = ∫₀^∞ |H(ω)|² S_φ(ω) dω).

**Finite-τ features (verbatim):** "It has two important features: the first one is an oscillating behavior at a frequency given by 1/(T + 2τR), leading to zeros at frequencies given by fk = k/(T+2τR). The second is a low pass first order filtering due to the finite duration of the Raman pulses, with an effective cutoff frequency f0, given by f0 = √3/3 · ΩR/2π."

**Filter order — attributed corroboration:** Per V. D. Nagornyi, "Response functions of atom gravimeters" (arXiv:1211.5598), this class behaves as a first-order filter: "In filtering the vibrations these instruments are equivalent to the first-order lowpass filters, while other atom gravimeters are equivalent to the second-order low-pass filters."

**Worked SI conversion for the cutoff** (using Cheinet's own figure parameters, T = 4.97 ms and τ_R = 20 µs, with Ω_R = π/(2τ_R) as stated in the Fig. 3 caption: "for a three pulses interferometer with a Rabi frequency ΩR = π/2τR"):
- Ω_R = π / (2 × 20×10⁻⁶ s) = π / (4×10⁻⁵ s) = 7.854×10⁴ rad/s
- Ω_R/2π = 1.250×10⁴ Hz
- f₀ = (√3/3) × 1.250×10⁴ Hz = 0.5774 × 1.250×10⁴ Hz ≈ **7.2×10³ Hz (7.2 kHz)**

**Experimental validation of the Ω_R-dependent cutoff/zero (verbatim):** the effective Rabi frequency "is measured with an uncertainty of about 1 %. It had to be corrected by only 1.5 % in order for the theoretical and experimental positions of the second zero to match," confirming the f₀ model and the second zero's critical dependence on Ω_R ("Its position depends critically on the value of the Rabi frequency").

**Conflict note:** No source contradicts Eq. 8/9. The "ideal delta-pulse" sin⁴ form is the ω≪Ω_R limit of the exact finite-τ Eq. 8; the only finite-τ modifications are the T→T+2τ_R envelope shift and the first-order roll-off above f₀.

---

## 3. BERTOLDI 2019 — finite-τ Mach-Zehnder phase correction

**TL;DR:** Bertoldi, Minardi & Prevedelli derive a finite-τ phase (Eq. 21) whose leading correction multiplies the gravity phase by [1 − (2π−4)/π · η], η=τ/T, plus a residual single-shot term δφ₂ = −4θ²(T)sin2φ₂(T) (Eq. 32) that averages to zero over the velocity distribution. The leading correction equals 1 − 2τ/T + 4τ/(πT), agreeing with Shao 2015.

**Source:** A. Bertoldi, F. Minardi, M. Prevedelli, "Phase shift in atom interferometers: corrections for non-quadratic potentials and finite-duration laser pulses," *Phys. Rev. A* **99**, 033619 (2019). DOI 10.1103/PhysRevA.99.033619. Preprint arXiv:1812.11890 (https://arxiv.org/abs/1812.11890).

**Main finite-τ result (their Eq. 21),** to first order in η=τ/T:

```
φ₂ = T²(k g − α − k γ z₀)(1 − (2π−4)/π · η)
     − k γ T³ [ v_m (1 − (2π−4)/π · η) − g T (7/12 − (4π−8)/(3π) · η) ]
```

For the pure gravimetric term (gradient γ=0):

```
φ₂ = T²(k g − α)·(1 − (2π−4)/π · τ/T)
```

so the **multiplicative finite-τ correction factor on the gravity phase is (1 − (2π−4)/π · τ/T)**.

**Verbatim:** "Here we report only an approximate expression using Eq. (13), keeping only terms up to the first order in the small parameter η = τ/T. This expression depends only on the area, not on the actual shape, of the pulses: φ2 = T²(kg − α − kγz0)(1 − (2π−4)/π η) − kγT³[vm(1 − (2π−4)/π η) − gT(7/12 − (4π−8)/3π η)]. We notice that some numerical coefficients in this formula do not agree with those in Eq. (40) of Ref. [26]." (η scale, verbatim: "typical experimental values for η are in the 10⁻⁴ ∼ 10⁻⁵ range.")

**Pulse sequence convention (verbatim):** "a sequence of three pulses π/2−π−π/2 of temporal length τ, 2τ, τ respectively are separated by two free evolution intervals of length T − 2τ so that the total duration of the interferometric sequence is 2T."

**Residual single-shot correction (their Eq. 32),** θ(t) ≡ τδ(t)/2:

```
δφ₂ = −4 θ²(T) · sin(2 φ₂(T)) + O(θ³)
```

**Verbatim:** "After some algebra we obtain δφ2 = −4θ²(T) sin 2φ2(T) + O(θ³). This is one of the main results of our analysis, showing that the interferometric phase shift carries an additional contribution due to the evolution during the laser pulses, actually dominated by the central π pulse at time t = T. However, this contribution is easily washed out by averaging over the velocity distribution of the sample... As a consequence, δφ2 averages to zero over the atomic sample and the phase shift evaluated in Eq. (21) still holds."

**Gradiometer differential form (their Eq. 22):** Δφ₂ = −kγdT²(1 − (2π−4)/π · η).

**Cross-source consistency / explicit disagreement flag:**
- Bertoldi states its coefficients differ from Eq. (40) of Ref. [26] (X. Li, C.-G. Shao, Z.-K. Hu, *J. Opt. Soc. Am. B* **32**, 248, 2015) — verbatim: "some numerical coefficients in this formula do not agree with those in Eq. (40) of Ref. [26]."
- The τ/T-expansion in Shao et al. (arXiv:1503.01199) is, verbatim: "Δφ = −(α + k·g)T²(1 − 2τ/T + 4τ/πT), where α is the chirp rate ... τ is the duration of a π/2 pulse, and T is the interval time between two Raman pulses." Since (2π−4)/π = 2 − 4/π, the Bertoldi factor 1 − (2π−4)/π·(τ/T) = 1 − 2τ/T + 4τ/(πT) — so **the leading gravity-phase corrections of Bertoldi and Shao AGREE.**
- B. Dubetsky (arXiv:1810.04218) reports, verbatim: "φ_g = (k·g − α)T(T + τ(4/π + 2))" using a different definition of T (and noting "we omit the term of the relative weight (τ/T)²"); the apparent sign/coefficient difference is a known **convention dependence on how T is defined** (center-to-center vs. edge), not a physics disagreement.

---

## 4. CHU / KASEVICH / PETERS foundational papers and the effective-time form

**TL;DR:** Kasevich & Chu 1991 establish the π/2–π–π/2 geometry and the delta-pulse phase; Peters/Chung/Chu 2001 give Φ = k_eff·g·T² plus the gravity-gradient extension but do **not** publish a T+(4/Ω)tan(Ωτ/2) effective-time formula. The literal tan(Ωτ/2)/Ω structure appears as a finite-pulse wavepacket displacement in SYRTE's arXiv:2006.14354, not in the foundational gravimetry papers.

**Kasevich & Chu (1991)** — "Atomic interferometry using stimulated Raman transitions," *Phys. Rev. Lett.* **67**, 181–184 (1991), DOI 10.1103/PhysRevLett.67.181. Establishes the sequence but no finite-τ closed form. Verbatim (OSA conference companion record): "We have created an interferometer by applying a π/2-π-π/2 Raman pulse sequence: a first π/2 pulse coherently splits the atomic wave packet by putting it in a superposition of states |1> and |2>, a second π pulse occurring a time Δt later redirects each wave packet..."

**Peters, Chung & Chu (2001)** — "High-precision gravity measurements using atom interferometry," *Metrologia* **38**, 25–61 (2001), DOI 10.1088/0026-1394/38/1/4. Canonical source for Φ = k_eff·g·T² (delta-pulse) and the gravitational-gradient extension (verbatim from abstract context: "We extend previous methods of analysing the interferometer to include the effects of a gravitational gradient"). **Per targeted review, this paper does NOT state a T_eff = T + (4/Ω_eff)·tan(Ω_eff τ/2) effective-time formula.**

**Le Gouët et al. (2008)** — "Limits to the sensitivity of a low noise compact atomic gravimeter," *Appl. Phys. B* **92**, 133–144 (2008), DOI 10.1007/s00340-008-3088-1; arXiv:0801.1270. Reproduces Cheinet's g(t) and the delta-pulse phase but contains no tan-based effective time. Verbatim: "φ(2T) = −k_eff · a T² [16] ... Here k_eff = k1 − k2 is the effective wave vector (with |k_eff| = k1 + k2 for counter-propagating...)" and "of three pulses π/2 − π − π/2 of duration τR − 2τR − τR and a time origin chosen at the center of the π pulse, g is an odd function whose expression was first derived in [18]."

**Origin of the tan(Ωτ/2)/Ω structure** — "Velocity-dependent phase shift in a light-pulse atom interferometer" (SYRTE/LKB), arXiv:2006.14354: the finite-pulse wavepacket displacement is ⟨x(τ)⟩ = −v_R·tan(Ωτ/2)/Ω (their Eq. 7), v_R = ħk_R/m. This makes (1/Ω)·tan(Ωτ/2) the natural "effective half-time" of a single finite Raman pulse — but it is a wavepacket-displacement result, not the gravity-phase effective time.

**Flag (important for code):** The exact "T + (4/Ω_eff)·tan(Ω_eff τ/2)" effective-time expression as posed in the brief was **not found verbatim** in Peters/Chung/Chu 2001, Le Gouët 2008, or the accessible portions of Cheinet's 2006 thesis. **Do not implement a tan-based effective time as if sourced to Peters/Chung/Chu.** The published, implementable finite-τ corrections take the τ/T-expansion form (Section 3) or the scale-factor product form (Section 5b).

---

## 5. BORDÉ ABCD / Antoine–Bordé exact phase shifts

**TL;DR:** The Bordé ABCDξ matrix formalism yields exact analytical phase shifts for at-most-quadratic Hamiltonians, expressed via the wavepacket-center coordinates and momenta at the interaction vertices. It does **not** by itself output a simple closed-form (1+τ/T) finite-τ correction: finite pulse duration enters through the beam-splitter ("ttt") modeling, not the ABCDξ propagation stage.

**References (verified):**
- C. J. Bordé, "Atomic interferometry with internal state labelling," *Phys. Lett. A* **140**, 10–12 (1989), DOI 10.1016/0375-9601(89)90537-9. (Reference and pagination 10–12 confirmed across multiple citing works; ScienceDirect PII 0375960189905379.) Note: this is C. J. Bordé (Christian J. Bordé). The frequently co-cited "J. Phys. France 50, 909" is a *separate* Bordé-related work and should not be conflated with the Phys. Lett. A 140 paper.
- Ch. Antoine, Ch. J. Bordé, "Exact phase shifts for atom interferometry," *Phys. Lett. A* **306**, 277–284 (2003); arXiv:physics/0210083 (https://arxiv.org/abs/physics/0210083).
- Ch. Antoine, Ch. J. Bordé, "Quantum theory of atomic clocks and gravito-inertial sensors: an update," *J. Opt. B: Quantum Semiclass. Opt.* **5**, S199–S207 (2003).

**Verbatim (Antoine & Bordé 2003, "Exact phase shifts"):** "In the case of an external Hamiltonian at most quadratic in position and momentum operators, we use the ABCDξ formulation of atom optics to establish an exact analytical phase shift expression for atom interferometers with arbitrary spatial or temporal beam splitter configurations. This result is expressed in terms of coordinates and momenta of the wave packet centers at the interaction vertices only."

**Two-stage structure (verbatim):** "For the theory of atom interferometers two basic stages are required: 1. a proper description of the propagation of wave packets between the beam splitters 2. an adequate modelization of the beam splitters themselves. The first stage is achieved through the ABCDξ theorem whose main results are briefly recalled in section 2. The second problem is addressed by the ttt theorem which provides a simple model for the phase introduced by the splitting process."

**Conclusion for code:** The ABCDξ formalism is exact but does not itself produce the τ/T correction in closed form; finite-pulse-duration corrections are captured through the ttt beam-splitter model. For directly implementable finite-τ corrections, use Sections 3 and 5b.

---

## 5b. Directly implementable finite-τ scale factor (Fang/Mielec 2018, citing Cheinet thesis)

**TL;DR:** The single most code-ready finite-τ scale factor is **S_rec = k_eff(T+τ/2)(T+(4/π−3/2)τ)**. It involves only T and τ — NOT a tan(Ωτ/2) term and NOT Ω explicitly. The coefficient (4/π−3/2) is a pure number ≈ −0.2268.

**Source:** B. Fang, N. Mielec, D. Savoie, M. Altorio, A. Landragin, R. Geiger, "Improving the phase response of an atom interferometer by means of temporal pulse shaping," *New J. Phys.* **20**, 023020 (2018); arXiv:1712.08110 (https://arxiv.org/abs/1712.08110). The closed form is attributed (their ref. [45]) to P. Cheinet, PhD thesis, Université Pierre et Marie Curie – Paris VI (2006), Eq. (2.45), p. 38, "with T defined as the time elapsed between the centre of adjacent pulses."

**Verbatim:** "The finite duration τ of the (rectangular) pulses modifies the scale factor of an atom accelerometer from Φ = keffT²a to Φ = Srec a, with Srec = keff(T + τ/2)(T + (4/π − 3/2)τ) [45]. For experiments where the inertial effect is inferred from a phase measurement, such a change of scale factor has to be taken into account when evaluating the accuracy budget." (Pulse-timing definition, verbatim: "The pulse separation T denotes the time elapsed between the center of two consecutive light pulses, and τ is the duration of the rectangular pulse.")

**Plain-text, code-ready:**
```
S_rec = k_eff · (T + τ/2) · (T + (4/π − 3/2)·τ)
```
with T = center-to-center pulse spacing, τ = π/2 pulse duration. Numerically 4/π − 3/2 = −0.22676. Expanded to first order in τ:
```
S_rec ≈ k_eff · [ T² + (4/π − 1)·T·τ ]   ,   (4/π − 1) = 0.27324
```
(since ½ + 4/π − 3/2 = 4/π − 1). Phase: Φ = S_rec · a.

**Cross-source consistency:** Writing S_rec as a τ/T expansion, S_rec/(k_eff T²) ≈ 1 + (4/π − 1)τ/T. Compare Bertoldi's gravity-phase factor 1 − (2π−4)/π·τ/T = 1 − (2 − 4/π)τ/T. These differ in sign of the linear-τ term **only because of the differing definition of T** (Fang/Cheinet: center-to-center; some τ/T-expansion papers measure between pulse edges/starts). Both reduce to the same physical scale factor when a consistent T convention is applied — this is the recurring convention issue flagged throughout.

---

## Recommendations (staged, for the qgrav/AISim implementation)

1. **Sensitivity function module (do first).** Implement g(t) exactly as Cheinet Eq. 4 (Section 1), piecewise with the sin(Ω_R t) ramps. Unit-test the odd symmetry and the boundary continuity at t=τ_R (sin(Ω_R τ_R) should match the plateau value 1 when Ω_R τ_R = π/2 for a π/2 edge pulse). **Threshold:** if your simulated g(t) deviates from Eq. 4 by more than the contrast-normalized 78% measured in Cheinet, revisit the constant-Rabi/square-pulse assumption.
2. **Transfer-function module.** Build G(ω) from the exact Eq. 8 (Section 2) and provide the Eq. 9 low-ω limit as a fast path. Validate the two diagnostic features: zeros at f_k = k/(T+2τ_R), and the first-order roll-off at f₀ = (√3/3)(Ω_R/2π). **Benchmark:** for T=4.97 ms, τ_R=20 µs (Cheinet's figure parameters), f₀ ≈ 7.2 kHz.
3. **Gravity-phase scale factor (this replaces empirical calibration).** Implement S_rec = k_eff(T+τ/2)(T+(4/π−3/2)τ) (Section 5b) as the primary analytical τ-correction; cross-check it against the Bertoldi/Shao factor 1−2τ/T+4τ/(πT) (Section 3) **after** harmonizing the T convention. Adopt one explicit T definition project-wide (recommend center-to-center, matching Cheinet/Fang) and document it at the top of the module.
4. **Residual single-shot term.** Implement Bertoldi Eq. 32 (δφ₂ = −4θ²(T)sin2φ₂(T)) only if AISim models single-shot, finite-velocity-class behavior; for velocity-averaged accuracy budgets it vanishes and can be omitted.
5. **Do NOT** hard-code a "T+(4/Ω)tan(Ωτ/2)" effective time attributed to Peters/Chung/Chu — it is not in those papers (Section 4). If a tan-based half-time is desired physically, cite arXiv:2006.14354 Eq. 7 as the wavepacket-displacement origin and treat it as a modeling choice, not an established gravimetry benchmark.

**Benchmark thresholds that would change the above:** (i) For accuracy targets coarser than ~10⁻⁸ g, the leading linear-τ scale-factor correction (~(4/π−1)τ/T ≈ 2.7×10⁻⁴ × τ/T, i.e. ~5×10⁻⁹ for τ=10 µs, T=0.5 s) may be negligible — verify against your target budget. (ii) For gradiometers / G-measurement-class accuracy (10⁻¹⁰ g and below, or the −49 to −54.5 ppm offsets reported by Shao for the Rosi *et al.* Nature 510, 518 (2014) configuration), the gradient-coupled finite-τ terms in Bertoldi Eq. 21/22 become mandatory.

## Caveats
- **T-convention dependence is the dominant source of apparent literature disagreement.** Center-to-center vs. edge definitions change the linear-τ coefficient (Fang/Cheinet "+(4/π−1)" vs. Shao/Bertoldi "−(2−4/π)"); the physics agrees once T is defined consistently. Always document the convention in code.
- **Explicit author-flagged disagreement:** Bertoldi 2019 states its Eq. 21 coefficients "do not agree with those in Eq. (40) of Ref. [26]" (Li/Shao/Hu JOSAB 2015). Treat the Bertoldi (Heisenberg/Magnus) and Cheinet/Fang (sensitivity-function) forms as the cross-validated pair.
- **Cheinet 2006 PhD thesis Eq. (2.45) was not retrieved directly** (HAL access-blocked in this session); the S_rec form is taken verbatim from Fang et al. (NJP 20, 023020), which cites it. This is a secondary-but-named-source for that one equation.
- All other equations (Cheinet Eqs. 1, 3, 4, 8, 9; Bertoldi Eqs. 21, 32; Shao Eq. 1; Antoine–Bordé) are quoted directly from the primary sources (arXiv full texts) listed in each section.
- The "ideal delta-pulse" |H|² ∝ sin⁴(πfT) is rigorously the ω≪Ω_R limit of Cheinet Eq. 8, not an independent result; the finite-τ corrections are the T→T+2τ_R envelope shift and the first-order f₀ roll-off (corroborated as first-order filter behavior by Nagornyi, arXiv:1211.5598).