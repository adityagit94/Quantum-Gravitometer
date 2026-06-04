# RESEARCH_JOSS_SUBMISSION.md

**Topic 7 (Phase 19) — JOSS submission requirements and similar published packages, for qgrav v1.0.1 (https://github.com/adityagit94/Quantum-Gravitometer)**

## TL;DR (overall)

- **Submit qgrav to JOSS only after the GitHub repository has ≥6 months of iterative public commit history**, an OSI license file, automated tests in CI, a documented Statement of Need, demonstrated research use (at minimum a worked physics example reproducing a published gravimetry result such as the Peters–Chu Δg/g ≈ 3×10⁻⁹ measurement [Peters, Chung & Chu, *Nature* **400**, 849–852 (1999)]), and an explicit "AI Usage Disclosure" — these are now hard pre-review gates as of the 2025 JOSS scope update. A submission that does not meet all four pre-review gates will be desk-rejected.
- **Closest precedents in JOSS are GPUE (BEC/Gross–Pitaevskii solver, 10.21105/joss.01037) and RydIQule v2 (Rydberg-atom quantum sensor modelling, 10.21105/joss.08539).** Adjacent state-of-the-field tools that qgrav must cite — PyLCP, AtomECS, ARC, QuTiP, ElecSus, atomSmltr — were *not* published in JOSS but in Computer Physics Communications / SciPost; qgrav should benchmark itself explicitly against these to satisfy the "State of the Field" required section.
- **Aim for a 750–1100-word paper** (per the current JOSS paper-format spec, which mandates 750–1750 words), formatted to JOSS's `paper.md` template, with 2 suggested reviewers drawn from the atomic-physics reviewer pool surfaced below (e.g., @nikolasibalic, @mgalloy, @wcwitt) and 1 from the Bose–Einstein-condensate or quantum-optics neighborhood.

---

## 1. JOSS submission checklist (current 2025/2026)

### TL;DR
JOSS now operates with **four hard pre-review "must-meet" gates** (6-month public history; demonstrated research impact; good OSS practices; iterative development) plus a longer set of paper-content requirements that, since the 2025 scope update, includes explicitly labelled **Summary, Statement of Need, State of the Field, Software Design, Research Impact, and AI Usage Disclosure** sections. The paper must be **750–1750 words**. The reviewer checklist is published at joss.readthedocs.io and is used verbatim by reviewers in the joss-reviews GitHub repository.

### Authoritative sources
- Submission guidelines: https://joss.readthedocs.io/en/latest/submitting.html
- Paper format: https://joss.readthedocs.io/en/latest/paper.html
- Review criteria: https://joss.readthedocs.io/en/latest/review_criteria.html
- Review checklist: https://joss.readthedocs.io/en/latest/review_checklist.html

### 1.1 Pre-review gates (must meet ALL — failing any = desk rejection)
Verbatim from joss.readthedocs.io/en/latest/submitting.html:

1. **Sufficient public development history.** "The repository must have been public for more than six months prior to submission, with active development spanning that period. A repository made public immediately before submission, or one showing development concentrated into a few days or weeks, will not be accepted. We run automated checks on commit distribution — a repo dump is not a history."
2. **Demonstrated research impact.** "There must be evidence that the software is being used for research — at minimum by the developers themselves, and ideally by others. Acceptable signals include: references in published papers or preprints, DOIs linking to the software, documented adoption by other research groups, or clear integration into research workflows. Aspirational statements about future use are not sufficient."
3. **Good open source practices.** "For multi-author projects this means evidence of issues, pull requests, and public discussion. For single-author projects … *multiple* indicators must be present at submission time: a meaningful public commit history over time, tagged releases or a changelog, tests and CI, clear documentation, a CONTRIBUTING file, and stated support or governance expectations."
4. **Iterative development over time.** "A repository where all significant work was added in a concentrated window is a signal that the project was not developed iteratively."

### 1.2 Scope / significance (what "research software" means)
"JOSS publishes articles about software that demonstrates clear research impact or credible scholarly significance. Your software should represent a meaningful contribution to the research community rather than being a one-off tool for a single analysis." JOSS also requires that the software "should be feature-complete (i.e., no half-baked solutions), packaged appropriately according to common community standards for the programming language being used (e.g., Python), and designed for maintainable extension … 'Minor utility' packages, including 'thin' API clients, and single-function packages are not acceptable."

### 1.3 Software requirements (reviewer-checked, from review_criteria.html)
- **License:** "There should be an OSI approved license included in the repository. … Acceptable: A plain-text LICENSE or COPYING file with the contents of an OSI approved license. Not acceptable: A phrase such as 'MIT license' in a README file."
- **Installation:** Python packages should be "`pip install`able" and follow packaging.python.org conventions.
- **Tests:** "Good: An automated test suite hooked up to continuous integration (GitHub Actions, Circle CI, or similar). OK: Documented manual steps … Bad (not acceptable): No way for you, the reviewer, to objectively assess whether the software works."
- **API documentation:** "Good: All functions/methods are documented including example inputs and outputs. OK: Core API functionality is documented. Bad (not acceptable): API is undocumented."
- **Community guidelines:** "clear guidelines for third-parties wishing to: Contribute to the software; Report issues or problems …; Seek support."

### 1.4 Paper format — length and required sections (paper.html, verbatim)

> **"The paper should be between 750-1750 words. Authors submitting papers significantly longer than 1750 words may be asked to reduce the length of their paper."**

Required, labelled sections in `paper.md`:

1. **Summary** — "A description of the high-level functionality and purpose of the software for a diverse, *non-specialist audience*."
2. **Statement of need** — "Clearly state what problems the software is designed to solve, who the target audience is, and its relation to other work."
3. **State of the field** — "A description of how this software compares to other commonly-used packages in the research area. If related tools exist, provide a clear 'build vs. contribute' justification explaining your unique scholarly contribution and why existing alternatives are insufficient."
4. **Software design** — "An explanation of the trade-offs you weighed, the design/architecture you chose, and why it matters for your research application. This should demonstrate meaningful design thinking beyond a superficial code structure description."
5. **Research impact statement** — "Evidence of realized impact (publications, external use, integrations) or credible near-term significance (benchmarks, reproducible materials, community-readiness signals). The evidence should be compelling and specific, not aspirational."
6. **AI usage disclosure** — "Transparent disclosure of any use of generative AI in the software creation, documentation, or paper authoring. If no AI tools were used, state this explicitly. If AI tools were used, describe how they were used and how the quality and correctness of AI-generated content was verified."

Plus author list with affiliations (ROR ids encouraged), key references, mention of past/ongoing research projects using the software, and acknowledgement of any financial support.

### 1.5 Reviewer grading
"We ask that reviewers grade submissions in one of three categories: 1) Accept 2) Minor Revisions 3) Major Revisions. Unlike some journals we do not reject outright submissions requiring major revisions."

### 1.6 Practical implications for qgrav
- The current GitHub repo (adityagit94/Quantum-Gravitometer) **must show ≥6 months of iterative commit history** before a JOSS submission can pass the pre-review gate. If the project went public recently, do not submit yet.
- A CONTRIBUTING.md, CODE_OF_CONDUCT.md, a CHANGELOG, tagged releases (v1.0.1 already exists per the question — good), and CI (GitHub Actions running `pytest` with coverage) are *all* required signals.
- An OSI license **file** (e.g., MIT, BSD-3, Apache-2.0, GPL-3.0) — not a README mention.
- At least one citation/usage example: an arXiv preprint reproducing the Peters–Chu g-measurement (*Nature* **400**, 849–852, 1999) using qgrav, a Zenodo DOI for v1.1.0, or documented usage in a teaching/research workflow.
- The paper.md must contain a labelled "AI Usage Disclosure" section since v1.0.1 was developed in 2025–2026.

---

## 2. JOSS atomic-physics / quantum-sensing precedents

### TL;DR
Two JOSS papers are direct precedents for qgrav: **GPUE** (BEC simulator, 2018) and **RydIQule v2** (Rydberg-atom sensor modelling, 2026). Four quantum-information / many-body packages — **quimb**, **toqito**, **qujax**, and **QuantNBody** — are useful structural models for the paper format. Several of the most important atomic-physics simulation packages qgrav must cite (PyLCP, AtomECS, ARC, ElecSus, QuTiP, atomSmltr) were NOT published in JOSS; they appeared in Computer Physics Communications or SciPost.

### 2.1 GPUE: Graphics Processing Unit Gross–Pitaevskii Equation solver
- **DOI:** 10.21105/joss.01037 — https://joss.theoj.org/papers/10.21105/joss.01037
- **Authors:** James R. Schloss, Lee J. O'Riordan (OIST, Japan)
- **Year/volume:** 2018, JOSS 3(32), 1037
- **Repo:** https://github.com/GPUE-group/GPUE
- **Editor / Reviewers:** @labarba (Lorena Barba) / @mgalloy, @markbasham
- **Description:** GPU-based split-operator solver for the linear and non-linear Gross–Pitaevskii equation, focused on superfluid vortex dynamics in BECs.
- **Style:** ~500-word body, single "Summary" section that combines functionality, comparators (GPELab/XMDS2/Trotter–Suzuki), feature list, and acknowledgements. Predates the 2025 required-sections format and is below the current 750-word floor; qgrav cannot imitate this layout exactly.
- **Verbatim opening (de-facto statement of need):** "Bose–Einstein Condensates (BECs) are superfluid systems consisting of bosonic atoms that have been cooled and condensed into a single, macroscopic ground state … Numerical simulations of BECs that directly mimic experiments are valuable to fundamental research in these areas and allow for theoretical advances before experimental validation."

### 2.2 RydIQule Version 2: Enhancing graph-based modeling of Rydberg atoms
- **DOI:** 10.21105/joss.08539 — https://joss.theoj.org/papers/10.21105/joss.08539
- **Authors:** Benjamin N. Miller, David H. Meyer, Carter A. Montag, Omar Nagib, Teemu Virtanen, Peter K. Elgee, Kevin C. Cox (DEVCOM Army Research Laboratory)
- **Year/volume:** Submitted 13 March 2025; **Published 11 February 2026**, JOSS 11(118), 8539
- **Editor:** Sophie Beck. **Reviewers:** @a-eghrari, @nikolasibalic
- **Description:** Python package for forward-modelling Rydberg atomic RF sensors using a graph-based Lindblad master-equation formalism; v2 adds magnetic sublevel structure, analytic Doppler averaging, and improved ARC integration.
- **Style:** ~800-word body, *contains all five required sections* including a "Related Packages and Work" subsection that explicitly distinguishes RydIQule from QuTiP, ElecSus, PyLCP, and Mathematica's Atomic Density Matrix — **this is the single best modern template for qgrav.**
- **Verbatim statement of need:** "The unique quantum properties of Rydberg atoms offer distinct advantages in the fields of sensing, communication, and quantum information (Adams et al., 2019). However, the breadth of possible configurations and experimental parameters makes general modeling of an experiment difficult."

### 2.3 quimb: a python library for quantum information and many-body calculations
- **DOI:** 10.21105/joss.00819 — joss-reviews issue #819
- **Author:** Johnnie Gray
- **Year:** 2018
- **Repo:** https://github.com/jcmgray/quimb
- **Editor / Reviewers:** @jedbrown / @dalcinl, @sunqm
- **Description:** Tensor-network, exact-diagonalization and many-body solver in Python. Citation count not independently verified in this research session; treat as "widely used" rather than a specific number.

### 2.4 toqito — Theory of Quantum Information Toolkit
- **DOI:** 10.21105/joss.03082 — joss-reviews issue #3082
- **Author:** Vincent Russo
- **Year:** 2021
- **Repo:** https://github.com/vprusso/toqito
- **Editor / Reviewers:** @poulson / @rurz, @jameshclrk, @marwahaha
- **Description:** Python package for quantum-information-theoretic computations (entanglement, channels, nonlocal games, SDP).

### 2.5 qujax: Simulating quantum circuits with JAX
- **JOSS paper hash:** bd448465a308f0897c35e56fe7ca2740 — joss-reviews issue #5504
- **Author:** Samuel Duffield (Quantinuum/CQC)
- **Year:** 2023
- **Repo:** https://github.com/CQCL/qujax
- **Editor / Reviewers:** @lucydot / @jmiszczak, @amitkumarj441, @meandmytram
- **Description:** JAX-based differentiable quantum-circuit simulator.

### 2.6 QuantNBody — many-body operators and wavefunctions for quantum chemistry/physics
- **DOI:** 10.21105/joss.04759
- **Author:** Saad Yalouz et al.
- **Year:** Submitted 5 August 2022; Published 15 December 2022, JOSS 7(80), 4759
- **Repo:** https://github.com/SYalouz/QuantNBody
- **Editor / Reviewers:** @jarvist (Jarvist Moore Frost) / @wcwitt, @erikkjellgren
- **Description:** Python toolkit for many-body bosonic/fermionic operator and wavefunction construction.

### 2.7 Non-JOSS precedents qgrav MUST cite (state-of-the-field)
| Package | Venue / DOI | Why qgrav must cite it |
|---|---|---|
| **PyLCP** (Eckel, Barker, Norrgard, Scherschligt) | Computer Physics Communications **270**, 108166 (2022); arXiv:2011.07979 | Closest Python sibling: laser-cooling physics, OBE/rate-eq simulator from NIST. |
| **AtomECS** (Chen, Zeuner, Schneider, Foot, Harte, Bentine) | SciPost Physics Codebases submission (arXiv:2105.06447), submitted 24 Aug 2021; SciPost contributor record shows "latest activity 2022-11-11" with no published DOI — the submission is effectively dormant. **Not in JOSS.** | Rust ECS simulator of MOTs and Zeeman slowers, used by the AION programme. |
| **ARC / ARC 3.0** (Šibalić, Pritchard, Adams, Weatherill; Robertson et al.) | Computer Physics Communications **220**, 319 (2017); **261**, 107814 (2021) | Standard Alkali-atom Rydberg calculator; routinely cited by RydIQule and PyLCP. |
| **ElecSus** (Keaveney, Adams, Hughes) | Computer Physics Communications **224**, 311 (2018) | Atomic-magnetometer / vapor spectroscopy calculator. |
| **QuTiP / QuTiP 2** (Johansson, Nation, Nori) | Computer Physics Communications **184**, 1234 (2013) | Standard open-quantum-system solver, cited by both PyLCP and RydIQule v2. |
| **atomSmltr** (Weill, Bertoldi, Dareau — Institut d'Optique / LP2N, Université Bordeaux, CNRS) | SciPost Physics Codebases, arXiv:2511.20596; v1 submitted 25 Nov 2025, v2 resubmitted 18–19 Feb 2026 after two referee reports (Dr Bentine, Dr Jones); **under review, not yet published** as of May 2026. | Newest Python laser-cooling simulator with modular MOT geometry — direct competitor to PyLCP. |
| **Peters–Chu g-measurement** (A. Peters, K.Y. Chung, S. Chu) | *Nature* **400**, 849–852 (1999); achieved Δg/g ≈ 3×10⁻⁹ | The canonical published gravimetry benchmark qgrav should reproduce as its "research impact" demonstration. |

**For atom-interferometric gravimetry specifically, no published JOSS paper exists** as of May 2026. This is a positive for qgrav: it can credibly claim to fill an open niche. The closest published gravimetry-instrument paper outside JOSS is Ménoret et al., "Gravity measurements below 10⁻⁹ g with a transportable absolute quantum gravimeter," *Scientific Reports* (PMC6098009).

---

## 3. Reviewer-pool identification

### TL;DR
Suggested reviewer pool drawn from JOSS atomic-physics and quantum-software review history. JOSS asks authors to suggest 2-5 reviewers; below are 10 high-confidence candidates with their reviewing track records.

### 3.1 Primary candidates (already reviewed atomic / quantum-simulation JOSS papers)

| GitHub handle | Real name / affiliation (where known) | Reviewed |
|---|---|---|
| **@nikolasibalic** | Nikola Šibalić — co-author of ARC (Alkali Rydberg Calculator) | RydIQule v2 (joss.08539) |
| **@a-eghrari** | — | RydIQule v2 (joss.08539) |
| **@mgalloy** | Michael Galloy (IDL/Python scientific computing) | GPUE (joss.01037) |
| **@markbasham** | Mark Basham (Diamond / Rosalind Franklin Institute) | GPUE (joss.01037) |
| **@wcwitt** | William C. Witt (Cambridge; electronic-structure software) | QuantNBody (joss.04759) |
| **@erikkjellgren** | Erik Kjellgren (quantum chemistry) | QuantNBody (joss.04759) |
| **@dalcinl** | Lisandro Dalcin (mpi4py, scientific computing) | quimb (joss.00819) |
| **@sunqm** | Qiming Sun (PySCF lead) | quimb (joss.00819) |
| **@jmiszczak** | Jarosław Miszczak (quantum-information software) | qujax (joss-reviews #5504) |
| **@rurz** | — | toqito (joss.03082) |

### 3.2 Suggested editors to request as handling editor
- **Sophie Beck** — handled RydIQule v2; clearly active in atomic-physics-adjacent submissions (Track 3 PE).
- **@labarba** (Lorena Barba) — handled GPUE; long-time JOSS editor with physics expertise.
- **@jarvist** (Jarvist Moore Frost) — handled QuantNBody; condensed-matter/computational-chemistry editor.

### 3.3 Caveats
- JOSS routinely declines reviewer suggestions that look like co-authors or close collaborators; choose candidates with no co-publication ties to qgrav's author(s).
- **@nikolasibalic** is both an ARC co-author *and* a recent JOSS reviewer for atomic-physics submissions — almost certainly the single best primary suggestion.
- The reviewer pool for "atom-interferometric gravimetry specifically" is essentially empty in JOSS history; expect editors to recruit reviewers from the BEC / laser-cooling / Rydberg neighborhoods.
- The QuantNBody [REVIEW] issue number (as opposed to PRE-REVIEW #4656) could not be retrieved; reviewer handles are confirmed via the published paper's joss.theoj.org metadata page.
- "Sophie Beck" is the editor name printed on the RydIQule v2 paper; the corresponding GitHub handle was not confirmed in this research session.

---

## 4. Reasonable scope analysis — minimum vs. comprehensive JOSS paper

### TL;DR
JOSS papers are formally bounded at **750–1750 words** of body prose (per joss.readthedocs.io/en/latest/paper.html). Published physics tools cluster around **~500–900 words** (some legacy papers like GPUE are below the current floor and would have to be expanded under today's rules). RydIQule v2 (2026, ~800 words) is the strongest comprehensive template.

### 4.1 What JOSS says (verbatim)
> "The paper should be between 750-1750 words. Authors submitting papers significantly longer than 1750 words may be asked to reduce the length of their paper." — https://joss.readthedocs.io/en/latest/paper.html

### 4.2 Bare-bones model — GPUE (10.21105/joss.01037)
- **~500-word body**, one "Summary" section that combines functionality description, comparison to GPELab/XMDS2/Trotter-Suzuki, list of features (4 bullets), and acknowledgements.
- Predates the 2025 required-sections format AND falls below today's 750-word floor; qgrav cannot imitate this format exactly — the modern minimum is 750 words.

### 4.3 Comprehensive model — RydIQule v2 (10.21105/joss.08539)
- **~800-word body** with the modern section layout: Summary → Statement of Need → Handling Sublevel Structure (software design) → Improved Calculation of Atomic Properties → Analytic Doppler Averaging → Related Packages and Work → Acknowledgements → References.
- Demonstrates use by external groups via 5 citing publications in the Statement of Need / Related Work sections.
- Best modern template for qgrav.

### 4.4 Recommended target for qgrav v1.1.0
- **750–1100 words**, comfortably above the 750-word floor and well below the 1750-word ceiling.
- Section budget: Summary 200w, Statement of Need 200w, State of the Field 250w, Software Design 250w, Research Impact 100w, AI Usage Disclosure 50w (≈ 1050 words). Acknowledgements + references are not counted against the limit.

---

## 5. Statement-of-Need templates — verbatim from physics JOSS papers

### TL;DR
Five well-written Statement-of-Need (or de-facto SoN) passages from JOSS physics papers, with citations, that qgrav can use as structural templates.

### 5.1 RydIQule v2 — Statement of Need (Miller et al. 2026, 10.21105/joss.08539)
> "The unique quantum properties of Rydberg atoms offer distinct advantages in the fields of sensing, communication, and quantum information (Adams et al., 2019). However, the breadth of possible configurations and experimental parameters makes general modeling of an experiment difficult. One challenge is that many atomic energy levels consist of numerous magnetic sublevels that arise from the different possible orientations of the electron's and nucleus's angular momentum. These sublevels have different responses to applied magnetic and electric fields which leads to measureable differences for most real-world atomic sensors."

**Why it works:** opens with a domain-motivation citation, immediately states a concrete modelling difficulty, gives a worked physical example (sublevel structure), and motivates the software's main feature.

### 5.2 GPUE — de-facto Statement of Need (Schloss & O'Riordan 2018, 10.21105/joss.01037)
> "Numerical simulations of BECs that directly mimic experiments are valuable to fundamental research in these areas and allow for theoretical advances before experimental validation. … No software packages are available using this method on GPU devices that allow for user-configurable simulations and a variety of different system types; however, several software packages exist to simulate BECs with other methods and on different architectures, including GPELab (Antoine & Duboscq, 2014), the Massively Parallel Trotter-Suzuki Solver (Wittek & Cucchietti, 2013), and XMDS (Dennis, Hope, & Johnsson, 2013)."

**Why it works:** clean two-sentence "value of simulation" framing followed by a direct "no software package does X" gap statement that cites every reasonable comparator.

### 5.3 RydIQule v2 — Related Packages and Work (10.21105/joss.08539)
> "Modeling quantum systems using the semi-classical Lindblad formalism is a common task that has been implemented by many physicists for their bespoke problems. Other tools that implement this type of simulation for specific types of problems include: qubits in QuTiP (Johansson et al., 2013), atomic magnetometers in ElecSus (Keaveney et al., 2018), and laser cooling in PyLCP (Eckel et al., 2022). Ultimately, the goal of RydIQule has not been to develop a new modeling technique, but rather to make a common, flexible, and most importantly efficient tool that solves a ubiquitous problem."

**Why it works:** explicit "build vs. contribute" justification (the 2025-required language) that names every adjacent package in the field, then disarms the "why didn't you just contribute to QuTiP?" question in a single sentence.

### 5.4 PyLCP — Introduction (Eckel et al. 2022, Computer Physics Communications 270, 108166; non-JOSS but the closest sibling)
> "We introduce an open-source, Python-based program that computes the movement of atoms or molecules with complex level structures in arbitrary optical (laser) and magnetic fields. The pylcp package allows multiple levels of approximation from the complete OBEs through to a simple heuristic model. Like other quantum dynamics packages, pylcp can solve the optical Bloch equations, but it focuses on simulating the laser cooling of atoms and molecules. Importantly, for the user's given laser geometry, atomic level structure, and magnetic field configuration, our code automatically generates the governing equations for the atom."

**Why it works:** the "Like X, but focused on Y" sentence (a contrast clause + a single-sentence USP) is the most efficient way to satisfy both the Statement-of-Need and State-of-the-Field requirements in two sentences.

### 5.5 AtomECS — Introduction (Chen et al., arXiv:2105.06447; submitted to SciPost — non-JOSS but a strong rhetorical template)
> "When designing an apparatus, simulations are an important tool for optimising the performance and characteristics of Zeeman slowers and magneto-optical traps. The performance of such techniques depends on many parameters, and the fraction of incident atoms that are captured and cooled may be less than 0.1%, so computational speed is critical when using simulations to optimise and explore the wide parameter space."

**Why it works:** quantifies the need ("less than 0.1%") and converts a physics fact into a software requirement ("computational speed is critical") — a pattern qgrav should imitate (e.g., "atom-interferometer phase shifts at the 10⁻⁹ g level require Monte-Carlo ensembles of ≥10⁵ atoms; naïve pure-Python loops are infeasible…").

---

## Key Findings (synthesis)

1. **JOSS in 2026 is stricter than in 2018.** The 2025 scope update added the four "must-meet" pre-review gates and six required paper sections; old short papers like GPUE (~500 words, single Summary) would not pass today's 750-word floor or section-labelling rules.
2. **The atom-interferometric-gravimetry niche in JOSS is empty.** This both helps (qgrav has clear novelty) and hurts (no direct reviewer pool — editors will likely recruit from BEC, laser-cooling, and Rydberg-sensor neighborhoods).
3. **The strongest single template is RydIQule v2** (10.21105/joss.08539). It is the most recent, follows the new required-section format exactly, and addresses a structurally similar problem (forward-modelling an atomic quantum sensor).
4. **qgrav must cite — and benchmark against — PyLCP, AtomECS, ARC, atomSmltr, QuTiP, ElecSus** in the State-of-the-Field section, even though none of these are themselves JOSS papers, to satisfy the new "build vs. contribute" requirement.

## Recommendations (staged, actionable)

### Now (before any JOSS submission)
1. **Audit the GitHub repo for the four pre-review gates.** If the commit history is <6 months old or shows a recent dump-style import, *do not submit* — continue iterating publicly until the 6-month threshold passes.
2. **Add or verify the required repo artefacts:** OSI LICENSE file (MIT/BSD-3/Apache-2.0 recommended), CONTRIBUTING.md, CODE_OF_CONDUCT.md, CHANGELOG.md, GitHub Actions CI running `pytest` + coverage, tagged v1.0.x and v1.1.x releases on GitHub *and* on PyPI.
3. **Generate at least one piece of "demonstrated research impact" evidence:** an arXiv preprint reproducing the Peters–Chu g-measurement (*Nature* **400**, 849–852, 1999) using qgrav, a Zenodo DOI for v1.1.0, or documented usage in another group's repository.

### Pre-submission (paper.md drafting)
4. **Use the RydIQule v2 paper as the structural template.** Copy its section ordering: Summary → Statement of Need → Software Design subsections → Related Packages and Work → Acknowledgements → References, then add an explicit "AI Usage Disclosure" section.
5. **Target 750–1100 words of body prose.** Hard floor 750, hard cap 1750.
6. **Write the State-of-the-Field section to explicitly distinguish qgrav from PyLCP, AtomECS, atomSmltr, ARC, ElecSus, and any closed-source/Mathematica gravimetry models.** Use a "Like X, but focused on Y" sentence pattern (see §5.4).
7. **Use the Open Journals GitHub Action** (https://github.com/marketplace/actions/open-journals-pdf-generator) on the paper branch so a PDF artefact is built on every commit and you can be sure the paper compiles.

### Submission
8. **Suggest reviewers in this order:** @nikolasibalic (ARC co-author; reviewed RydIQule v2), @mgalloy (reviewed GPUE), @wcwitt (reviewed QuantNBody), with @a-eghrari and @markbasham as fallbacks. Suggest Sophie Beck or @labarba as preferred handling editor.
9. **Submit via https://joss.theoj.org/papers/new** with the `paper.md` hosted in a Git branch off `main` of the qgrav repo.

### Benchmarks that would change the staging
- If the GitHub repo has <6 months of public iterative history at the time of submission: **delay until threshold met**.
- If qgrav has no external citing publication, preprint, or third-party adoption: **delay until at least one preprint exists**, or pre-empt the question by writing a benchmark companion preprint reproducing Peters–Chu (1999).
- If the JOSS scope is updated again before submission (the front page warns "JOSS has updated its submission scope requirements"): **re-read joss.readthedocs.io/en/latest/submitting.html and paper.html before any final draft**.

## Caveats

- I could not directly fetch joss.theoj.org's search interface (returns binary/JS-rendered content not parseable by the fetch tool); JOSS precedent counts are therefore lower-bound. There may be additional atomic-physics JOSS papers not surfaced here.
- AtomECS's SciPost Physics Codebases submission has been dormant since November 2022 with no published DOI; treat its citation as "submitted to SciPost, not yet published" rather than "published".
- atomSmltr (arXiv:2511.20596) was still under review at SciPost Physics Codebases as of May 2026; cite the arXiv preprint, not a SciPost DOI.
- Exact body-text word counts for GPUE and RydIQule v2 are estimates from PDF extraction, not tokenised counts; treat ±50 words as the uncertainty band.
- The QuantNBody REVIEW issue number (as opposed to PRE-REVIEW #4656) could not be retrieved; reviewer handles are confirmed only via the published paper's metadata page.
- "Sophie Beck" is the editor name printed on the RydIQule v2 paper; her GitHub handle was not confirmed in this research session — to find it, check the joss-reviews issue for joss.08539.
- The "widely cited" claim for quimb is qualitative; an exact citation count was not independently verified.
- JOSS's reviewer-suggestion process does not guarantee selection; editors choose freely from the reviewer pool.
- The first JOSS pre-review for qgrav may be rejected if the paper claims novelty without a benchmark; mitigate by including a reproducible Peters–Chu validation notebook in the repo at submission time.