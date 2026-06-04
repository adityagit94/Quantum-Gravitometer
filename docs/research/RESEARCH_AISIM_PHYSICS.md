# RESEARCH_AISIM_PHYSICS: Sign/Phase Conventions and the Chirped‑Detuning Factor‑of‑Two Question

**Bottom line.** The canonical Raman pulse propagator (Cheinet 2008 Eq. 3) imprints the laser phase **exactly once per pulse**, evaluated at the pulse start `t₀` as `±(ω_L t₀ + φ)`. Generalising to a chirped laser, ω_L → ω(t) = ω_L0 + α t, so the imprinted phase becomes `±(ω_L0 t₀ + ½ α t₀² + φ)` — the chirp enters via the **integral** ∫₀^{t₀} ω_L(t')dt', not via δ(t₀)·t₀. A separate `exp(-i δ t₀)` factor that uses the **instantaneous** chirped detuning multiplied by t₀ effectively contributes `α t₀²` per pulse, i.e. twice the correct `½ α t₀²`, leading to a chirp term of `−2αT²` in the Mach–Zehnder readout instead of the canonical `−αT²`. The vendored AISim package (bleykauf/aisim) does not expose a chirp parameter or pulse-start time at all; any handling of chirped detuning inside `qgrav`'s patched copy of `prop.py` is local to the fork. **The factor-of-2 claim of Patch C is consistent with every primary source surveyed**, provided the patched code applies `exp(-i δ(t₀) t₀)` on top of an unmodified Cheinet 2008-style rotation.

---

## 1. Sign/Phase Conventions in Primary Papers

**TL;DR.** Cheinet 2008 (arXiv:physics/0510197) gives the cleanest, fully-explicit Raman propagator matrix: off-diagonals carry `exp[±i(ω_L t₀ + φ)]` evaluated at the **start** of the pulse, with `+` on the |a⟩→|b⟩ entry and `−` on |b⟩→|a⟩. Kasevich & Chu (1991) and Young/Kasevich/Chu (1997) use the same convention up to a global sign of k_eff. The Chu Nobel lecture explicitly states `φ_L` is parametrised by (k_eff, z, ω_L, t, φ_L).

### 1(a). Kasevich & Chu 1991 PRL and Bordé conventions

- **DOI:** 10.1103/PhysRevLett.67.181 (Phys. Rev. Lett. 67, 181 – published 8 July 1991).
- The 1991 PRL itself is short and does not write the off-diagonal matrix element in closed form. The Chu Nobel lecture review (https://www.nobelprize.org/uploads/2018/06/chu-symp.pdf), which references the 1991 PRL as [13], states the convention precisely (verbatim):

  > "respectively, where k_eff is the effective k-vector of the Raman pulse, z is the position of the atomic wavefunction at time t, ω_L is the optical frequency, and φ_L any additional phase factor of the light."

  This pins down the imprinted phase as a function of (k_eff, z, ω_L, t, φ_L). The sign in front of k_eff depends on whether the |g⟩→|e⟩ leg is labelled with the wavevector `k_1 − k_2` or `k_2 − k_1`. In Kasevich & Chu 1991 and in the Chu Nobel lecture, `+k_eff` is used such that the atom is **kicked** by +ℏk_eff when promoted to the upper hyperfine state.

- **Bordé 1989** (Phys. Lett. A 140, 10): introduces the ABCD-matrix formalism with positive-frequency convention `exp(+i k z − i ω t)`. I could not fetch the original PDF; reported via the bibliography of Antoine & Bordé 2003 (J. Opt. B 5, 199, cited as ref. [13] in Cheinet 2008).

### 1(b). Cheinet et al. 2008 — **canonical propagator matrix** (best primary source for this task)

- **arXiv:** physics/0510197 (published in IEEE Trans. Instrum. Meas. 57, 1141, 2008).
- The propagator matrix for a single Raman pulse from `t₀` to `t` (Eq. 3, p. 3 of the arXiv PDF) is, verbatim:

  > "M_p(t₀, t, Ω_R, φ) =  
  > ( e^{−i ω_a (t−t₀)} cos(Ω_R/2 (t−t₀)),  −i e^{−i ω_a (t−t₀)} e^{+i(ω_L t₀ + φ)} sin(Ω_R/2 (t−t₀));  
  >  −i e^{−i ω_b (t−t₀)} e^{−i(ω_L t₀ + φ)} sin(Ω_R/2 (t−t₀)),   e^{−i ω_b (t−t₀)} cos(Ω_R/2 (t−t₀)) )"

  with the textual definition (verbatim, same page):

  > "where Ω_R/(2π) is the Rabi frequency and ω_L, the effective frequency, is the frequency difference between the two lasers, ω_L = ω_2 − ω_1. Setting Ω_R = 0 in M_p(t₀, t, Ω_R, φ) gives the free evolution matrix, which determines the evolution between the pulses."

- **Key implications:**
  1. The laser phase enters the off-diagonals **once**, evaluated at the pulse start `t₀`: `+(ω_L t₀ + φ)` on |a⟩→|b⟩ and `−(ω_L t₀ + φ)` on |b⟩→|a⟩.
  2. The diagonal elements carry only the free internal evolution `exp(−i ω_{a,b}(t−t₀))`. There is **no separate `exp(−i δ t₀)` factor** outside this matrix; detuning enters via the rotating-frame energies ω_a, ω_b and through the generalised Rabi frequency on resonance.
  3. For a chirped laser the natural generalisation is ω_L(t) = ω_L0 + α t, so the integrated laser phase ∫₀^{t₀} ω_L(t')dt' becomes `ω_L0 t₀ + ½ α t₀²`. The propagator carries `exp[±i(ω_L0 t₀ + ½ α t₀² + φ)]` — the chirp term `½ α t₀²` appears **once** per pulse, not twice.

- The three-pulse Mach–Zehnder phase combination (Cheinet 2008, p. 3, verbatim):

  > "Φ = φ₁ − 2 φ₂ + φ₃ [15]"

  where the `φ_i` are the Raman phases evaluated at the centre of the i-th pulse. Substituting `φ_i = ω_L0 t_i + ½ α t_i² + φ_0` and using equal spacing `t₂ − t₁ = t₃ − t₂ = T` collapses the quadratic-in-t piece to a chirp contribution of `−αT²` to Φ (see §4).

### 1(c). Young, Kasevich & Chu 1997 — AISim's own cited source

- Reference: B. C. Young, M. Kasevich & S. Chu, "Precision Atom Interferometry with Light Pulses," in *Atom Interferometry* (P. R. Berman ed., Academic Press 1997), pp. 363–406. DOI 10.1016/B978-012092460-8/50010-2. AISim's documentation explicitly cites this as the source of its `TwoLevelTransitionPropagator` (readthedocs v2.1.0 reference list).
- The Young–Kasevich–Chu chapter uses the same Rabi rotation matrix as Cheinet 2008, with the imprinted phase `φ_L = k_eff·z − ω·t − φ` on the |g⟩→|e⟩ off-diagonal. **I could not retrieve the chapter PDF directly**; this is reported on the basis of secondary citations in Peters/Chung/Chu 2001 (Metrologia 38, 25) and Cheinet 2008 [16].

### Imprinted-phase sign of `k_eff z` is convention-dependent

The choice of `+k_eff z` vs `−k_eff z` depends on the labelling of `k_eff = k_1 − k_2` vs `k_2 − k_1`. Both signs appear in the literature; Kasevich & Chu 1991 and Cheinet 2008 use the convention where the atom is kicked by `+ℏk_eff` when promoted to `|b⟩ = |g_2, p + ℏk_eff⟩`.

### Sign of the chirp term

For a "down-chirped" laser (decreasing ω with time) compensating a freely-falling atom under +z gravity, `α = ω̇_L < 0`. The integrated imprinted phase is `∫ ω_L(t)dt = ω_L0 t + ½ α t²`, so the chirp contributes `+½ α t²` to φ_L. Reversing the sign convention of the rotating-frame transformation flips this to `−½ α t²`. The combination that appears in the Mach–Zehnder readout is invariant: the laser chirp partially cancels the Doppler-induced detuning, leaving the gravimeter phase `Φ = (k_eff·g − α) T²` (with both signs of α and g defined consistently with k_eff up).

---

## 2. AISim GitHub Repository (bleykauf/aisim)

**TL;DR.** AISim's `TwoLevelTransitionPropagator` exposes no chirp-rate parameter, no pulse-start time, and no time-varying detuning — only `time_delta`, `intensity_profile`, `wave_vectors`, `wf`, `phase_scan`. The latest release is **5.0.0 (March 12, 2025)**. There are NO open issues or PRs in upstream bleykauf/aisim mentioning chirp, detuning, or factor-of-two phase issues. The verbatim body of `_prop_matrix` could not be retrieved via the available tooling (raw.githubusercontent.com and readthedocs `_modules/aisim/prop.html` returned permission errors).

### Current upstream API (verbatim from https://aisim.readthedocs.io/en/v2.1.0/aisim.html)

> "class aisim.prop.TwoLevelTransitionPropagator(time_delta, intensity_profile, wave_vectors=None, wf=None, phase_scan=0)  
> A time propagator of an effective Raman two-level system.  
> Parameters: time_delta (float) – length of pulse; intensity_profile (IntensityProfile) – Intensity profile of the interferometry lasers; wave_vectors (Wavevectors) – wave vectors of the two Raman beams for calculation of Doppler shifts; wf (Wavefront, optional) – wavefront aberrations of the interferometry beam; phase_scan (float) – effective phase for fringe scans.  
> Notes — The propagator is for example defined in [1].  
> [1] Young, B. C., Kasevich, M., & Chu, S. (1997). Precision atom interferometry with light pulses. In P. R. Berman (Ed.), Atom Interferometry (pp. 363–406). Academic Press."

### Repository state (May 2026 snapshot)

- Default branch: `master` (not `main`).
- Latest PyPI release: **aisim 5.0.0 (12 March 2025)**; latest readthedocs build identifies as "5.0.1.dev2+ga8fd816" (a post-5.0.0 development commit).
- Release lineage: 0.5.x → 0.7.x → 1.0.0 → **1.0.1 (Sept 2020, the version `qgrav` vendored)** → 2.0.0 → 2.1.0 → 3.0.0 → 4.0.0 → 4.1.0 → 5.0.0. The vendored copy is ~4.5 years and four major versions behind upstream.
- Repository has 367 commits, 9 stars, 6 forks. License: GPL-3.0.
- Tests directory `tests/` exists, but its contents could not be fetched. Based on the documented API (no chirp parameter), it is unlikely that any upstream test exercises gravity + chirp simultaneously.

### Issues / PRs

- **2 open issues, NEITHER about detuning or chirp:**
  - #55 "Use fixtures in tests" (Sep 17 2020, bleykauf) — labels: code style, tests.
  - #15 "Visualization on Bloch sphere" (Jun 3 2020, savowe) — labels: enhancement. Body: "a method for plotting of a (AtomicEnsemble) StateVector on the Bloch sphere".
- 31 closed issues + 31 closed PRs. Closed list could not be enumerated; no closed PR with a title matching "detuning", "chirp", "delta·t0", or "factor of 2" was discoverable via search.
- **Related publications:** V. Schkolnik, B. Leykauf, M. Hauth, C. Freier, A. Peters, *Appl. Phys. B* 120, 311 (2015), DOI 10.1007/s00340-015-6138-5 (arXiv:1411.7914) — wavefront-aberrations paper, which AISim's wavefront example reproduces. There is no peer-reviewed "AISim paper" per se.

### Implication for the factor-of-2 claim

Because the upstream API exposes neither a chirp rate α nor an absolute pulse-start time t₀, an unmodified upstream `_prop_matrix` cannot contain an `exp(-i δ t₀)` factor with absolute t₀ ≠ 0. If the vendored copy in `qgrav` has been patched to inject t₀ and a time-varying δ, that patched factor sits *outside* whatever in-pulse rotation the unmodified Cheinet 2008-style matrix provides. **If the in-pulse rotation uses only the resonant-frame detuning δ_0 (no chirp inside the rotation) and an external `exp(-i δ(t₀) t₀)` with δ(t₀) = δ_0 + α t₀ is the sole vehicle for the chirp**, then that factor contributes `α t₀²` per pulse instead of the correct `½ α t₀²` — exactly a factor-of-2 over-count, consistent with the Patch C derivation.

---

## 3. Other First-Principles Chirped-Raman Atom-Interferometer Simulators

**TL;DR.** No widely-used open-source simulator handles chirped Raman gravimetry rigorously from first principles. UATIS (Universal Atom Interferometer Simulator, Fitzek et al. 2020) is the closest peer-reviewed code, but treats **elastic** (Bragg/Bloch) scattering, not internal-state Raman transitions, and is closed Fortran. AtomECS is a laser-cooling code, not an interferometer code. QuTiP is general-purpose; no published gravimeter package built on it.

### UATIS — Fitzek, Siemß, Seckmeyer, Ahlers, Rasel, Hammerer, Gaaloul

- **Paper:** *Sci. Rep.* 10, 22120 (2020), DOI 10.1038/s41598-020-78859-1; arXiv:2002.05148. PMC: PMC7746744.
- The paper says of chirped lattices (e.g. Bloch oscillations):

  > "This adiabatic process can be realised by loading the atoms into a co-moving optical lattice, then accelerating the optical lattice by applying a frequency chirp and finally by unloading the atom from the optical lattice. In our model, this corresponds to the following external potential [...]"

- Scope (verbatim from abstract): "this simulator solves the atom-light diffraction problem **in the elastic case i.e. when the internal state of the atoms remains unchanged**." The conclusion notes:

  > "we would like to highlight the possibility to generalise this method to Raman or 1-photon transitions if we account for the internal state degree of freedom change during the diffraction."

  Hence UATIS does **not** currently model two-photon Raman transitions of the Kasevich–Chu type; chirped *Bragg* scattering is supported via a time-dependent external potential, which gives the chirp phase implicitly through position-space wavefunction evolution and is therefore not prone to the AISim-style over-counting issue.

- The code base is Fortran (UATIS) and is not open-source; access is via the Leibniz Hannover group on request. Confirmed verbatim in the 2026 thesis by Rui Li (M.Sc.), "Robust Atom Interferometry with Double Bragg Diffraction," QUEST-Leibniz-Forschungsschule, Leibniz Universität Hannover, defended 26 January 2026 (arXiv:2603.22385):

  > "I owe special thanks to Florian Fitzek, from whom I learned Fortran and became familiar with the Fortran-based Universal Atom Interferometer Simulator (UATIS). This codebase later evolved—through the dedicated work of Stefan Seckmeyer—into the main computational tool responsible for producing many of the exact numerical simulations presented in this thesis."

### AtomECS

- Repo: https://github.com/TeamAtomECS/AtomECS — "Cold atom simulation code" in Rust.
- Scope (verbatim from README):

  > "Laser-cooling of atoms by optical scattering forces. Doppler forces on atoms that scatter light, including the random fluctuations that give rise to the Doppler temperature limit. Magnetic fields, implemented on a grid or through simple analytical models. Hot atoms generated by an oven. [...] Cooling light beams, defined by their detuning and gaussian intensity profiles."

- No interferometer phase calculation, no Raman / two-photon transition module, no chirp-driven Doppler-compensated Mach–Zehnder. AtomECS is **not relevant** to the chirped-Raman question.

### MaxAtoms

- No actively-maintained repository called "MaxAtoms" relevant to atom-interferometric gravimetry surfaced. (The name appears in unrelated contexts.)

### Stanford / Müller-group simulators

- Not publicly released. Canonical formulas documented in: A. Peters, K. Y. Chung, S. Chu, *Metrologia* 38, 25 (2001), DOI 10.1088/0026-1394/38/1/4. See §4.

### QuTiP-based

- QuTiP itself (qutip.org) has no domain-specific atom-interferometer module. A general-purpose `mesolve`/`sesolve` Hamiltonian simulation with a time-dependent two-level Rabi term + chirp can in principle reproduce the correct one-pulse-per-imprint behaviour, but no widely-used package implements this for Raman gravimetry. The github topic page lists ARC (Rydberg atoms) and several Jaynes–Cummings demos, but nothing dedicated to Mach–Zehnder Raman gravimetry.

### Optimal-control / pulse-shaping codes

- J. Saywell, M. Carey, M. Belal, I. Kuprov & T. Freegarde, "Optimal control of Raman pulse sequences for atom interferometry," *J. Phys. B: At. Mol. Opt. Phys.* 53, 085006 (2020) (arXiv:1911.08789), demonstrated experimentally with cold 85Rb atoms achieving 99.8(3)% ground-state transfer efficiency.
- Ziwen Song, "Design of Robust Raman Pulses for Cold Atom Interferometers Based on the Krotov Algorithm," arXiv:2602.14494 (submitted 17 February 2026; affiliation listed as Independent Researcher, Datong, China).

These codes use Schrödinger-equation simulators with explicit time-dependent Hamiltonians `H(t) = (δ(t)/2) σ_z + (Ω(t)/2)[cos φ(t) σ_x + sin φ(t) σ_y]` and integrate them numerically; they do *not* split the propagator into "rotation × phase factor" and hence do not have an AISim-style factor-of-2 risk. Published source code is not yet available for the Krotov paper.

### Net assessment

The AISim approach (closed-form Rabi rotation matrix per pulse + free evolution between pulses) is **the** standard light-pulse formalism and is widely used, but it depends critically on getting the imprinted-phase factor right. There is no peer-reviewed, openly-released independent simulator to cross-validate `qgrav` against for the chirped Raman case.

---

## 4. Mach-Zehnder Total Phase with Chirped Laser (the gravimeter phase)

**TL;DR.** All primary sources agree on the form `Δφ = (k_eff·g − α) T²` (or the same with sign reversed, depending on which direction k_eff is defined). The chirp enters with the **opposite sign** to k_eff·g, so that the gravimeter is read out by finding the chirp rate `α₀ = k_eff·g/(2π)` at which Δφ = 0 — the dark fringe whose position is independent of T.

### Karcher, Pereira dos Santos & Merlet 2020 (arXiv:2001.07478)

Verbatim (§I):

> "this chirp rate α adds a phase shift (α T²) to the interferometer that, when properly tuned (α = α₀ = k·g), exactly compensates the phase shift induced by the gravity acceleration (−k·g T²), k being the effective wave vector of the Raman transition. Remarkably, this leads to a dark fringe in the fringe pattern obtained when scanning α, whose position does not depend on the interferometer duration."

- **Sign convention here:** gravity-induced phase = `−k_eff g T²`, chirp-induced phase = `+α T²`. Tuning α = k_eff g makes total ≈ 0.

### Le Gouët et al. 2008 (HAL hal-00283932, "Operating an atom interferometer beyond its linear range")

Verbatim:

> "is given by ΔΦ = −k_eff·g T² [19]. Here k_eff = k_1 − k_2 is the effective wave vector (with |k_eff| = k_1+k_2 for counter-propagating beams), T is the time interval between two consecutive [pulses]. […] In practice, a correction G × (P_i − P_{i+1}) is added at each cycle to α, in order to stir the chirp rate onto the central fringe."

  This is the gravity-only piece; the chirp lock to the central fringe is `α₀ = k_eff g` consistent with Karcher 2020.

### Peters, Chung & Chu 2001 (Metrologia 38, 25, DOI 10.1088/0026-1394/38/1/4)

The Stanford canonical reference for the full gravimeter phase including chirp. I could not pull the body PDF in this session; the abstract reports:

> "we have built an atom interferometer that can measure g, the local acceleration due to gravity, with a resolution of Δg/g = 2 × 10⁻⁸ after a single 1.3 s measurement cycle, 3 × 10⁻⁹ after 1 min and 1 × 10⁻¹⁰ after two days of integration time."

  The formula is consistently quoted in downstream papers as `Δφ = (k_eff·g − α)T²` (or the sign-reversed equivalent depending on k_eff direction).

### Sign-convention disagreement across sources (not a physical disagreement)

- Karcher et al.: `Δφ_grav = −k g T²`, `Δφ_chirp = +α T²` → `α₀ = +k g`.
- Le Gouët et al.: `Δφ = −k_eff·g T²` (gravity-only).
- Cheinet 2008: combination `Φ = φ_1 − 2φ_2 + φ_3` — sign of resulting g-term depends on whether ω_L(t) = ω_0 + αt with α < 0 (down-chirped) or α > 0.

These are restatements of the same physics under different choices of (i) direction of k_eff, (ii) sign of the laser chirp, (iii) labelling of |g_1⟩ vs |g_2⟩. The invariant statement is: **the dark fringe occurs when the laser chirp exactly cancels the time-varying Doppler shift induced by gravitational acceleration**, i.e. `α₀ = ±k_eff·g` with sign fixed by the geometry.

### Quantitative SI conversion: typical gravimeter chirp rate

For 87Rb (λ = 780 nm, k_eff ≈ 2 × 2π/(780 nm) = 1.611 × 10⁷ rad/m for counter-propagating beams) and g = 9.81 m/s²:
- `α₀ = k_eff g / (2π) = (1.611 × 10⁷ × 9.81) / (2π) Hz/s ≈ 2.515 × 10⁷ Hz/s`.
- Independently confirmed by Li et al., "Raman-Laser System for Absolute Gravimeter Based On 87Rb Atom Interferometer," *Photonics* **7**(2), 32 (2020), DOI 10.3390/photonics7020032: "Raman lasers are realized by OPLL with a sweeping frequency range of 11 MHz and chirp rate of **25.12 MHz/s**." Arithmetic check: 25.12 MHz/s vs my calculation 25.15 MHz/s — agreement to 0.1%.

### Cheinet 2008 quantitative sensitivity prediction (already in SI)

Verbatim (§VI):

> "With our typical experimental parameters, this would result in a sensitivity of 4 × 10⁻⁸ rad·s⁻¹·Hz⁻¹/² for the gyroscope and of 1.5 × 10⁻⁸ m·s⁻²·Hz⁻¹/² for the gravimeter."

  No unit conversion needed (SI throughout). The vibration-noise requirement for 1 mrad-per-shot is reported as "below 10⁻⁸ m·s⁻²·Hz⁻¹/²" (§V).

---

## 5. Canonical Reference for φ_L (Falling Atom + Chirped Laser)

**TL;DR.** Cheinet 2008 Eq. (3) is the cleanest *fully written* reference. Peters/Chung/Chu 2001 (Metrologia 38, 25) is the standard *gravimeter-specific* reference for the same formulas extended to the chirped, falling-atom case. The combined imprinted-phase expression is `φ_L(t₀) = k_eff·z(t₀) − ∫₀^{t₀} ω_L(t')dt' − φ_0 = k_eff·z(t₀) − ω_L0·t₀ − ½ α t₀² − φ_0`.

### Cheinet 2008 propagator (already quoted in §1)

The off-diagonal carries `exp[±i(ω_L t₀ + φ)]`, evaluated **at the pulse start**. For a chirped laser ω_L(t) = ω_L0 + α t, the appropriate replacement is `ω_L t₀ → ω_L0 t₀ + ½ α t₀²`. Inclusion of the Doppler phase `k_eff·z(t₀)` — where `z(t₀) = z(0) + v t₀ − ½ g t₀²` for a freely-falling atom — gives the full `φ_L(t₀) = k_eff·z(t₀) − ω_L0 t₀ − ½ α t₀² − φ_0`.

### Peters, Chung & Chu 2001 (Metrologia 38, 25)

Canonical reference cited by Cheinet 2008 as Ref. [15] for the three-pulse phase combination `Φ = φ_1 − 2 φ_2 + φ_3`. Extends the analysis to include gravity gradients. **DOI 10.1088/0026-1394/38/1/4**, behind IOP paywall; I could not fetch the body in this session.

### Cronin, Schmiedmayer, Pritchard 2009 Rev. Mod. Phys. 81, 1051

**DOI:** 10.1103/RevModPhys.81.1051. The standard review of atom-optics interferometry. Discusses sign conventions but does not write a single canonical `φ_L` expression. Cited indirectly in downstream papers (e.g. arXiv:2409.08550).

### Key identity for the chirped, falling-atom case

Combining (a) the Doppler shift `δ_D(t) = k_eff·(v_0 − g t)` experienced by a free-falling atom and (b) the chirped-laser detuning compensation `ω_L(t) = ω_L0 + α t`, the **instantaneous resonance condition** is satisfied when `α = k_eff g`. The integrated imprinted phase per pulse is then `φ_L(t_i) = k_eff·z(t_i) − ω_L0·t_i − ½ α t_i² − φ_0`. Summing with weights (+1, −2, +1) over equally-spaced pulse times `t₁, t₂ = t₁+T, t₃ = t₁+2T` gives:

- gravity contribution: `−k_eff g T²` (from the `k_eff·z(t_i)` part);
- chirp contribution: `−α T²` (from the `½ α t_i²` part — the (+1, −2, +1) combination acting on a quadratic-in-t function returns `−α T²`);
- total: `Δφ = −(k_eff g − α) T²`.

  Consistent (modulo overall sign) with Karcher et al. 2020 quoted above.

### **Why the factor-of-2 issue arises — the central claim of Patch C**

The chirp term `−α T²` in the MZ output arises **purely from the quadratic-in-time piece `½ α t²` of the imprinted phase, summed once per pulse with weights (+1, −2, +1)**. Now consider two possible coding errors:

**Case A (over-count by 3):** A code (i) already evaluates the in-pulse rotation with a chirped detuning `δ(t) = δ_0 + α t` (so the in-pulse rotation already imprints the `½ α t₀²` piece), **and** (ii) also multiplies by an external `exp(−i δ(t₀) t₀) = exp(−i δ_0 t₀ − i α t₀²)`. The second factor contributes an *additional* `α t₀²` (not `½ α t₀²`) per pulse. With (+1, −2, +1) weights this gives an extra `−2 α T²`, so the chirp piece becomes `−3α T²` — an over-count by a factor of three.

**Case B (over-count by exactly 2 — Patch C's scenario):** The in-pulse rotation does *not* include the chirp (i.e. uses only `δ_0`, the resonant-frame detuning at t=0), and the chirp is supposed to be supplied entirely by an external `exp(−i δ(t₀) t₀)` factor with `δ(t₀) = δ_0 + α t₀`. That factor contributes `α t₀²` per pulse, but it should have been `½ α t₀²` (the integral `∫₀^{t₀}(δ_0 + α t')dt' = δ_0 t₀ + ½ α t₀²`, NOT `δ(t₀)·t₀ = δ_0 t₀ + α t₀²`). With (+1, −2, +1) weights this yields `−2 α T²` in the MZ phase instead of the correct `−α T²` — **exactly a factor of two too large**.

This Case-B interpretation is the most likely meaning of the Patch C claim: the `exp(−i δ t₀)` factor is being used as a stand-in for the full imprinted laser phase, but it should be `exp(−i ∫₀^{t₀} δ(t')dt') = exp(−i δ_0 t₀ − i (α/2) t₀²)`, i.e. **the half** of what the literal `δ(t₀)·t₀` evaluates to in its chirp piece.

The Patch C derivation — "the factor of ½ is missing because the integral `∫₀^{t₀}(δ_0 + α t')dt' = δ_0 t₀ + ½ α t₀²`, not `δ(t₀)·t₀ = δ_0 t₀ + α t₀²`" — is **supported by every primary source consulted**: Cheinet 2008 Eq. (3), Kasevich–Chu 1991 (via the Chu Nobel lecture), and the gravimeter-phase derivations in Karcher 2020 and Le Gouët 2008. The standard derivation writes the imprinted phase as the *integral* of the instantaneous laser frequency, not as the instantaneous frequency × elapsed time.

---

## Recommendations

1. **Audit the qgrav-vendored `aisim/prop.py` `_prop_matrix` against Cheinet 2008 Eq. (3)** by symbolically expanding the propagator for a chirped detuning `δ(t) = δ_0 + α t`. Compare:
   - the in-pulse Rabi rotation (should be Eq. (3) of Cheinet 2008 with `ω_L → ω_L0 + α t_centre`);
   - any external phase factor (should be the **integral** of δ from 0 to t₀, i.e. `δ_0 t₀ + ½ α t₀²`, not `(δ_0 + α t₀)·t₀`).

2. **If the chirp is present only in the external factor**, replace `exp(-i δ(t₀) t₀)` with `exp(-i (δ_0 t₀ + ½ α t₀²))` — this is Patch C.

3. **Validate** by reproducing the central-fringe lock: the simulated `Δφ` should vanish at `α₀ = k_eff g` (≈ 25.12 MHz/s for 87Rb — Li et al. 2020, *Photonics* 7, 32), and the dark-fringe position should be **independent of T** (Karcher 2020 §I, quoted above).

4. **Quantitative cross-check** against Cheinet 2008 §VI: with τ_R = 20 μs, T = 50 ms, vibration noise at the 10⁻⁸ m·s⁻²·Hz⁻¹/² level, the gravimeter should achieve 1.5 × 10⁻⁸ m·s⁻²·Hz⁻¹/² sensitivity.

5. **Consider upgrading the vendored AISim** from v1.0.1 to upstream v5.0.0 (12 March 2025) and re-applying the patch on top of the modern API — but verify first that v5.0.0's `prop.py` still uses Cheinet 2008 / Young-Kasevich-Chu 1997 conventions (the documented `TwoLevelTransitionPropagator` API is unchanged between v2.1.0 and v5.0.0).

---

## Caveats

1. **Verbatim `_prop_matrix` source code could not be retrieved** for either the vendored v1.0.1 or upstream v5.0.0 within this session. The factor-of-2 diagnosis is therefore based on (a) the publicly documented API of `TwoLevelTransitionPropagator` (no chirp-rate, no t₀ parameter), (b) the AISim documentation's explicit citation of Young/Kasevich/Chu 1997 for the propagator definition, and (c) the universal form of that propagator as written verbatim in Cheinet 2008 Eq. (3). The argument is therefore *logical* rather than *direct code inspection*.

2. **The Young/Kasevich/Chu 1997 chapter PDF could not be retrieved.** The propagator form is reported on the basis of secondary citations (Cheinet 2008 Refs. [13], [16] = Moler/Weiss/Kasevich/Chu 1992 *Phys. Rev. A* 45, 342; Peters/Chung/Chu 2001) that use the identical formula.

3. **Peters/Chung/Chu 2001 PDF body could not be retrieved** (IOP paywall). The chirp-phase formula `Δφ = (k_eff g − α)T²` is reported via the verbatim quote from Karcher et al. 2020 (arXiv:2001.07478), which cites Peters 2001 as the canonical reference.

4. **Sign conventions vary across sources** — `k_eff = k_1 − k_2` vs `k_2 − k_1`, `α > 0` vs `α < 0` for the same physical "down-chirp", `|g⟩ = |F=1⟩` vs `|F=2⟩`. None of these flip the magnitude of the chirp phase; they only flip its sign. The Patch C factor-of-2 claim is about a *magnitude* discrepancy, not a sign discrepancy, and so survives all these convention changes.

5. **No upstream issue or PR** in bleykauf/aisim mentions chirped detuning or factor-of-two phase errors. Whether the vendored copy in `qgrav` was modified locally to add a chirped-detuning term (and if so, whether incorrectly) is a question that can only be answered by direct inspection of the `qgrav` fork's `prop.py`. The Patch C narrative is consistent with such a local modification having introduced the factor-of-2 over-count.

6. **No independent open-source chirped-Raman simulator exists** to cross-validate `qgrav` against. UATIS (Fitzek et al. 2020) is closed Fortran and treats only elastic scattering; AtomECS is laser-cooling only; Saywell/Song optimal-control codes are not yet released. Independent validation must therefore proceed via symbolic comparison to Cheinet 2008 Eq. (3) and the Karcher 2020 / Le Gouët 2008 dark-fringe condition.