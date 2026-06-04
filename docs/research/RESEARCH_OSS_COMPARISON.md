# Open-Source Software Comparison for qgrav v1.0.1

## TL;DR

- **qgrav occupies a niche that no single existing open-source package fully covers**: an integrated atom-interferometric *gravimetry* simulation that combines light-pulse atom-interferometer physics (where `bleykauf/aisim` is the closest competitor), Allan-deviation noise analysis (vendored from `aewallin/allantools`), and environmental corrections such as Earth tides (`hydrogeoscience/pygtide`) and seismic/vibration data (`obspy/obspy`). Most overlapping packages stop at one layer of the stack.
- **The strongest direct functional overlap is `bleykauf/aisim`** (GPL-3.0, actively maintained through v5.0.0 in March 2025), which qgrav vendors and patches; the other physics packages (`AtomECS`, `PyLCP`, `QuTiP`, `JenaAtomicCalculator`) target adjacent problems (laser cooling, open-quantum-system dynamics, atomic structure) rather than gravimetry, while the metrology/Earth-science packages (`allantools`, `pygtide`, `ObsPy`) are complementary infrastructure rather than competitors.
- **There is no public release of a gravimetry simulation pipeline from the leading experimental groups** (Stanford/Kasevich, Berkeley/Müller, Sandia, NPL, NIST quantum-sensing). The only NIST atom-physics codes are PyLCP (laser cooling) and atomqc (quantum-computing atomistic calculations); NPL's public GitHub contains no metrology or quantum-sensing code; Stanford and Berkeley group websites publish papers but no companion simulation repositories. **This is the central differentiation opportunity for qgrav's JOSS submission.**

---

## Comparison Table

| # | Tool | License (SPDX) | Last release / activity (as of 2026-05-27) | Language(s) | What it does | Key publication | Repo URL |
|---|------|---------------|----------------------|-------------|--------------|------------------|----------|
| 1 | **aisim** (bleykauf) | GPL-3.0-or-later | v5.0.0 released 2025-03-12 | Python | Object-oriented simulation of light-pulse atom interferometers (laser beams, atomic ensemble, detector, propagators) | No peer-reviewed paper or Zenodo DOI located as of May 2026; GitHub repo and Read the Docs are the only citable references | https://github.com/bleykauf/aisim |
| 2 | **AtomECS** (TeamAtomECS) | GPL-3.0 | crate v0.7.1 on crates.io; 667 commits; active (backend migration from `specs` → `bevy` underway) | Rust (with Python/MATLAB wrappers) | High-performance ECS-pattern simulation of laser cooling, MOTs, Zeeman slowers, dipole/magnetic trapping | Chen, Zeuner, Schneider, Foot, Harte, Bentine, *AtomECS: Simulate laser cooling and magneto-optical traps*, arXiv:2105.06447 (SciPost submission, 2021) | https://github.com/TeamAtomECS/AtomECS |
| 3 | **pylcp** (JQIamo/NIST) | "View license" on GitHub (NIST-style; exact SPDX not surfaced) | Activity through Feb 11, 2026; latest tagged release v1.0.2 (Jun 24, 2022) | Python (with Jupyter examples) | Object-oriented laser-cooling-physics simulator: auto-generates OBE/rate/heuristic equations for atom or molecule level structures in arbitrary laser + magnetic field configurations | Eckel, Barker, Norrgard, Scherschligt, *PyLCP: A Python package for computing laser cooling physics*, Comput. Phys. Commun. 270 (2022) 108166, DOI: 10.1016/j.cpc.2021.108166 (arXiv:2011.07979) | https://github.com/JQIamo/pylcp |
| 4 | **QuTiP** (qutip) | BSD-3-Clause | v5.2.3 released 2026-01-26; very active | Python (Cython/NumPy backend) | General-purpose open-quantum-system dynamics: Lindblad master equation, Monte-Carlo solvers, Floquet-Markov, Bloch-Redfield, time-dependent Hamiltonians | Johansson, Nation, Nori, *QuTiP 2: A Python framework for the dynamics of open quantum systems*, Comput. Phys. Commun. 184 (2013) 1234-1240, DOI: 10.1016/j.cpc.2012.11.019 | https://github.com/qutip/qutip |
| 5a | **Atoms.jl** (libAtoms) | MIT | Archived/unmaintained ("This is no longer maintained, please see JuLIP.jl and ASE.jl") | Julia | Originally molecular-simulation data structures | None | https://github.com/libAtoms/Atoms.jl |
| 5b | **AtomicStructure.jl** (JuliaAtoms, formerly Atoms.jl) | MIT | Low-activity Julia AMO ecosystem package | Julia | Atomic structure: orbitals on a radial grid (ContinuumArrays.jl interface) | None primary | https://github.com/JuliaAtoms/AtomicStructure.jl |
| 5c | **JenaAtomicCalculator.jl** (formerly JAC) | MIT | Actively maintained | Julia | Relativistic atomic structure / many-body amplitudes / cascades | Fritzsche, *A fresh computational approach to atomic structures, processes and cascades*, Comput. Phys. Commun. 240 (2019) 1, DOI: 10.1016/j.cpc.2019.01.012 | https://github.com/OpenJAC/JenaAtomicCalculator.jl |
| 5d | **MaxAtoms** | - | **No public repository found** | - | - | - | - |
| 6 | **QInfer** (Bayesian quantum parameter estimation incl. tomography) | BSD-3-Clause | Low recent activity | Python | Sequential Monte-Carlo Bayesian inference; quantum-state and process tomography heuristics | Granade, Ferrie, Hincks, Casagrande, Alexander, Gross, Kononenko, Sanders, *QInfer: Statistical inference software for quantum applications*, Quantum 1 (2017) 5, arXiv:1610.00336 | https://github.com/QInfer/python-qinfer |
| 7 | **AllanTools** (aewallin) | LGPL-3.0-or-later | v2024.06 released 2024-07-04 | Python | Allan deviation and related time-and-frequency stability statistics (ADEV, MDEV, TDEV, OADEV, HDEV, noise ID, Greenhall EDF CIs) | Wallin, *allantools: Allan deviation calculation*, ASCL ID 1804.021 (no peer-reviewed paper) | https://github.com/aewallin/allantools |
| 8 | **PyGTide** (hydrogeoscience) | MPL-2.0 | v0.8.2 released 2026-02-04 | Fortran (76%) / Python (24%) | Python wrapper around ETERNA PREDICT 3.4 (Wenzel/Kudryavtsev) for synthetic Earth-tide time series (gravity, tilt, strain) | Rau, *hydrogeoscience/pygtide: PyGTide*, Zenodo, DOI: 10.5281/zenodo.1346260 | https://github.com/hydrogeoscience/pygtide |
| 9 | **ObsPy** (obspy) | LGPL-3.0 | v1.5.0 released 2026-03-13 (release added 649 commits across 425 files from ≥18 contributors); very active | Python | Seismological data I/O (MiniSEED, SAC, etc.), signal processing, FDSN/ArcLink web-service clients, instrument response handling | Beyreuther, Barsch, Krischer, Megies, Behr, Wassermann, *ObsPy: A Python Toolbox for Seismology*, Seismol. Res. Lett. 81 (2010) 530-533, DOI: 10.1785/gssrl.81.3.530; and Krischer, Megies, Barsch, Beyreuther, Lecocq, Caudron, Wassermann, *ObsPy: a bridge for seismology into the scientific Python ecosystem*, Comput. Sci. Discov. 8 (2015) 014003, DOI: 10.1088/1749-4699/8/1/014003 | https://github.com/obspy/obspy |
| 10 | **Stanford (Kasevich) / Berkeley (Müller) AI simulation code** | - | **No public repository found** | - | Groups publish physics papers but do not release a companion gravimetry simulation package | Representative methodology paper: Kasevich & Chu, *Atomic interferometry using stimulated Raman transitions*, Phys. Rev. Lett. 67 (1991) 181, DOI: 10.1103/PhysRevLett.67.181 | - |
| 11 | **NIST quantum-sensing software** | (varies) | Mixed | Mixed | NIST/JQI release PyLCP (entry #3) and `usnistgov/atomqc` (atomistic calculations on quantum computers, DOI 10.1088/1361-648x/ac1154). **No public atom-interferometric *gravimetry* package located.** | (see #3) | https://github.com/JQIamo/pylcp ; https://github.com/usnistgov/atomqc |
| 12 | **NPL (UK) atom-gravimeter code** | - | **No public repository found** in NPL's GitHub orgs (`NationalPhysicalLaboratory` contains only "Icebreaker", an MS-Teams social app; `npl` and `nplcode` each have a single unrelated repo) | - | - | - | - |

---

## Detailed Tool Analyses (Strength / Weakness vs qgrav)

### 1. bleykauf/aisim - the closest direct competitor and qgrav's vendored dependency

`AISim` describes itself in the README, verbatim, as "AISim is a Python package for simulating light-pulse atom interferometers. It uses dedicated objects to model the laser beams, the atomic ensemble and the detection system and store experimental parameters in a neat way." Authored by Bastian Leykauf and Sascha Vowe (originally affiliated with the GAIN gravimeter at Humboldt-Universität / PTB collaboration), it is licensed GPL-3.0-or-later ("This program is free software: you can redistribute it and/or modify it under the terms of the GNU General Public License as published by the Free Software Foundation, either version 3 of the License, or (at your option) any later version") and was most recently released as **v5.0.0 on 2025-03-12**, with copyright "© 2020-2025 B. Leykauf · © 2020 S. Vowe".

- **Strength relative to qgrav**: First-mover in Python for light-pulse AI physics; clean object model (`AtomicEnsemble`, `Wavevectors`, `Detector`, propagators); contains the validated wavefront-aberration and Doppler-Rabi notebooks that the AI community trusts.
- **Weakness relative to qgrav**: aisim is a *physics-engine* library, not a *gravimetry-instrument-simulator*. It does not bundle Earth-tide corrections, seismic vibration injection, Allan-deviation analysis, or end-to-end *g* extraction. Because qgrav explicitly vendors and patches aisim, this is more accurately framed as "aisim is the kernel, qgrav is the instrument stack around it." **License-compatibility note**: aisim's GPL-3.0 license is copyleft, so qgrav inherits GPL-3.0 obligations on any code that links to or vendors aisim - JOSS reviewers will check this.
- **Active maintenance**: Yes - 26 releases, 367 commits, latest March 2025.

### 2. TeamAtomECS/AtomECS - high-performance laser-cooling, not gravimetry

"AtomECS is a software package that efficiently simulates the motion of neutral atoms experiencing forces exerted by laser radiation, such as in magneto-optical traps and Zeeman slowers. The program is implemented using the Entity-Component-System pattern, which gives excellent performance, flexibility and scalability to parallel computing resources" (Chen et al., arXiv:2105.06447). Released under **GPL-3.0**, Rust + Python/MATLAB wrappers, latest crate `atomecs = "0.7.1"`, with active migration of the backend from `specs` to `bevy`.

- **Strength**: Multi-orders-of-magnitude faster than a pure-Python pipeline; supports dipole + magnetic trapping, collisions, oven sources, and parallelisation across CPU cores.
- **Weakness vs qgrav**: AtomECS stops at the cold-atom *source* - it does not implement Raman/Bragg beamsplitter pulses, Mach-Zehnder interferometer phase accumulation, or gravity-extraction analysis. It also requires Rust toolchain installation, raising the entry barrier for Python-only users.
- **Active maintenance**: Yes - ongoing backend rewrite, 667 commits.

### 3. JQIamo/pylcp - Eckel et al. (NIST/JQI)

"We present a Python object-oriented computer program for simulating various aspects of laser cooling physics. Our software is designed to be both easy to use and adaptable... The program contains three levels of approximation for the motion of the atom" (Eckel, Barker, Norrgard, Scherschligt, Comput. Phys. Commun. 270 (2022) 108166, DOI 10.1016/j.cpc.2021.108166).

- **Strength**: Most rigorous open-source treatment of OBEs for laser cooling; multi-level atomic Hamiltonians; auto-generation of governing equations from user-specified level structure.
- **Weakness vs qgrav**: Same gap as AtomECS - pylcp targets cooling/molasses/MOT physics, not interferometer-phase extraction or gravimetry noise budgets. Last tagged release v1.0.2 was June 2022 (with small maintenance activity visible through Feb 2026), suggesting a slow release tempo.
- **Active maintenance**: Light - small commits visible in Feb 2026, but no new tagged release in roughly four years.

### 4. qutip/qutip - general-purpose, not gravimetry-aware

QuTiP is currently at **v5.2.3 (released 2026-01-26)**, BSD-3-Clause, with 12,582 commits on master and 35 releases. The canonical citation is Johansson, Nation, Nori, *QuTiP 2: A Python framework for the dynamics of open quantum systems*, Comput. Phys. Commun. 184 (2013) 1234-1240, DOI: 10.1016/j.cpc.2012.11.019.

- **Strength**: De-facto standard for open-quantum-system simulation; huge user base; permissive BSD-3-Clause license (no copyleft issues if qgrav linked against it).
- **Weakness vs qgrav**: Entirely general-purpose - no atom-interferometer geometry, no Raman/Bragg beam-splitter primitives, no gravimetry analysis. qgrav can usefully *call* QuTiP for internal-state dynamics but should not be compared head-to-head.
- **Active maintenance**: Yes, very active.

### 5. Julia atomic-physics ecosystem - adjacent but non-overlapping

**MaxAtoms: no public repository was found**, and an honest "package not found" is the correct answer. The closest Julia packages are:
- `libAtoms/Atoms.jl` - **archived** with the README notice: "This is no longer maintained, please see JuLIP.jl and ASE.jl."
- `JuliaAtoms/AtomicStructure.jl` (formerly `Atoms.jl`) - MIT, atomic structure on radial grids; not interferometry.
- `OpenJAC/JenaAtomicCalculator.jl` (JAC) - MIT, very capable relativistic atomic structure code (Fritzsche, Comput. Phys. Commun. 240 (2019) 1, DOI 10.1016/j.cpc.2019.01.012).

None of these target light-pulse interferometry or gravimetry, so they are complementary at best.

### 6. QInfer / quantum-tomography Python packages

`QInfer` (BSD-3-Clause) is the most prominent Python Bayesian quantum-parameter-estimation library, with explicit tomography support: "Tomography is the most common quantum statistical problem... The `qinfer.tomography` module has rich support for many of the common models of tomography including standard distributions and heuristics, and also provides convenient plotting tools." Canonical citation: Granade et al., *QInfer: Statistical inference software for quantum applications*, Quantum 1 (2017) 5, arXiv:1610.00336.

- **Strength**: Mature Bayesian inference engine usable for phase-estimation work; integrates with QuTiP.
- **Weakness vs qgrav**: Tomography of quantum states is orthogonal to gravimeter operation; QInfer would only become relevant if qgrav adds quantum-enhanced (squeezed/entangled) sensing modules.
- **Active maintenance**: Low - repository visible but few recent commits.

### 7. aewallin/allantools - vendored dependency

`AllanTools` (LGPL-3.0-or-later, latest release **2024.06 on 2024-07-04**) is described on its README: "A python library for calculating Allan deviation and related time & frequency statistics. LGPL v3+ license." It has no peer-reviewed paper; the canonical archival reference is the ASCL entry 1804.021.

- **Strength**: Reference implementation tested against Stable32; widely cited in the time-and-frequency community; LGPL-3.0 is permissive enough that qgrav (already GPL-3 via aisim) can safely vendor it.
- **Weakness vs qgrav**: Not a competitor - pure statistics library, no AI physics.
- **For qgrav's JOSS submission**: Confirm that the vendored copy matches upstream 2024.06; any divergence should be documented in `THIRD_PARTY.md`. LGPL-3.0 requires that modifications be released under LGPL-3.0+ and that users can relink - qgrav must preserve that.

### 8. hydrogeoscience/pygtide - Earth-tide corrections

`PyGTide` (MPL-2.0, latest **v0.8.2 released 2026-02-04**) wraps ETERNA PREDICT 3.4 via f2py: "PyGTide is a Python module that wraps around ETERNA PREDICT 3.4 which is compiled from Fortran into an executable using f2py. The original ETERNA PREDICT 3.3 was written by the late Prof. H.-G. Wenzel (Wenzel, 1996)." Cite as Rau, Zenodo DOI: 10.5281/zenodo.1346260.

- **Strength**: Validated, comprehensive earth-tide model (7 tidal potential catalogues including Hartmann-Wenzel 1995); MPL-2.0 license is GPL-compatible (file-level copyleft).
- **Weakness vs qgrav**: Single-purpose; no AI physics. A genuine complement, not a competitor.
- **Active maintenance**: Yes - release Feb 2026 indicates ongoing maintenance.

### 9. obspy/obspy - seismic data infrastructure

`ObsPy` (LGPL-3.0, latest **v1.5.0 released 2026-03-13**, with the 1.5.0 release alone contributing 649 commits across 425 files from ≥18 contributors) is the seismology community's de-facto Python toolbox. Citations: Beyreuther et al., Seismol. Res. Lett. 81 (2010) 530-533 (DOI 10.1785/gssrl.81.3.530); Megies et al., Annals of Geophysics 54 (2011) 47-58 (DOI 10.4401/ag-4838); Krischer et al., Comput. Sci. Discov. 8 (2015) 014003 (DOI 10.1088/1749-4699/8/1/014003).

- **Strength**: Industry-standard seismic data I/O and processing; webservice clients to all major data centres; LGPL-3.0 compatible with qgrav's GPL stack.
- **Weakness vs qgrav**: Pure seismology; no quantum sensing. qgrav would use it to import vibration spectra for the gravimeter noise budget - a complementary integration.
- **Active maintenance**: Very active.

### 10. Stanford (Kasevich) and Berkeley (Müller) groups - no public gravimetry simulation code

Both groups are world-leading experimentalists (Kasevich & Chu's 1991 Raman-AI paper is the foundational reference, DOI 10.1103/PhysRevLett.67.181; the Berkeley group's 2018 fine-structure-constant measurement is Parker, Yu, Zhong, Estey, Müller, *Science* 360 (2018) 191-195). **However, no public companion simulation repository was located** on either group's website, GitHub, or Zenodo. Internal simulation code appears to remain in-house. This is the most important *negative* finding in this review and a genuine niche for qgrav.

### 11. NIST (usnistgov) - partial public footprint

Within `usnistgov`, the only quantum-physics-relevant repositories located are:
- `usnistgov/atomqc` - "Atomistic Calculations on Quantum Computers" (DOI 10.1088/1361-648x/ac1154), targeting electronic-structure simulation on near-term quantum hardware, **not classical AI gravimetry**.
- (Through JQI/Maryland affiliation) `JQIamo/pylcp` - laser cooling, see entry #3.

**No NIST atom-interferometric gravimetry simulator was located.** NIST's "Compact Cold Atom Instruments" program page (https://www.nist.gov/programs-projects/compact-cold-atom-instruments) describes two hardware projects - (i) chip-scale atomic beam clocks (citing Martinez et al., arXiv:2303.11458) and (ii) miniaturized atom-interferometer gyroscopes (citing Chen et al., Phys. Rev. Applied 12 (2019) 014019) - but does not link to any open simulation code.

### 12. NPL (UK) - no public atom-gravimeter code

The official GitHub org `NationalPhysicalLaboratory` contains only an unrelated MS-Teams social app ("Icebreaker is an open-source app for Microsoft Teams that helps the whole team get closer by pairing members up every week"). The `npl` and `nplcode` orgs each have a single unrelated repository. **No public NPL atom-gravimeter code was located.**

---

## Positioning for JOSS

Based on the above survey, qgrav's JOSS "Statement of Need" should highlight four genuine and defensible gaps:

1. **End-to-end gravimeter pipeline, not just a physics engine.** Existing AI simulators (aisim; the Hannover universal-AI simulator of Fitzek, Siemß, Seckmeyer, Ahlers, Rasel, Hammerer & Gaaloul, *Universal atom interferometer simulation of elastic scattering processes*, **Scientific Reports 10, 22671 (2020), DOI: 10.1038/s41598-020-78859-1**; and AtomECS) model *atom-light* physics. None bundle the metrology layer - Allan-deviation noise analysis, Earth-tide subtraction, seismic-vibration injection, and gravity extraction - into one package. qgrav's stack-integration (aisim + allantools + pygtide + ObsPy) is the differentiator.

2. **Bridge between AMO and Earth-science software ecosystems.** No package in this review simultaneously links to ObsPy (seismology) and pygtide (Earth tides) on one side and aisim/QuTiP (AMO physics) on the other. qgrav can credibly position itself as that bridge.

3. **Open-source counterpart to in-house experimental codes.** Major experimental groups (Stanford/Kasevich, Berkeley/Müller, Sandia, NPL) do not release their internal AI-gravimeter simulation pipelines. qgrav can serve as the open reference implementation that smaller groups, educators, and reviewers can use.

4. **Reproducibility focus.** Vendor + patch model (aisim 5.x with documented diffs, allantools 2024.06 verbatim) gives reviewers a clear chain of provenance - a JOSS strength.

## Recommendations

Concrete, staged recommendations for the JOSS submission:

- **(Stage 1, before submission)** Write a one-paragraph "How qgrav differs from aisim, AtomECS, and pylcp" section in `paper.md`. This is the single most likely reviewer demand. **Threshold to change**: if a reviewer is satisfied without an explicit comparison-of-prior-work paragraph, drop it; if any reviewer asks "why not just use aisim?", that paragraph is mandatory.
- **(Stage 1)** Ensure `LICENSE` is GPL-3.0-or-later (inherited from aisim) and that `THIRD_PARTY.md` explicitly states the SPDX identifier of every vendored dependency, the upstream version pinned, and the diff against upstream. **Threshold**: if any vendored copy diverges from upstream by more than ~50 lines, contribute the patch upstream first.
- **(Stage 2, in the JOSS review window)** Include a "comparison-with-prior-work" Jupyter notebook reproducing one aisim example (e.g., wavefront-aberration phase shift) and one AtomECS example (e.g., MOT capture velocity), demonstrating that qgrav's vendored physics matches upstream within numerical tolerance.
- **(Stage 2)** Add a benchmark figure showing Allan-deviation output from qgrav versus a Stable32 reference dataset to validate the vendored AllanTools copy. **Threshold**: ≤1% deviation across all standard estimators (ADEV, MDEV, TDEV, OADEV, HDEV) on the IEEE 1139-2008 test vectors.
- **(Stage 3, after acceptance)** If qgrav's tomography references are aspirational rather than implemented, remove them from the README or move them to "future work" - JOSS reviewers will check that claims map to code.
- **Engagement**: open a courtesy issue on `bleykauf/aisim` informing upstream of qgrav's JOSS submission and offering to upstream any bug fixes - this is good open-source citizenship and reduces the risk of friction at review time.

## Caveats and Source Conflicts

- **qgrav itself was not independently verifiable**: a targeted search for `adityagit94/Quantum-Gravitometer` returned no indexed pages, and a direct fetch was rejected. All claims about qgrav's contents in this report are taken on the user's description rather than from primary inspection of the repository. **JOSS reviewers will require a public, browsable repository.**
- **GitHub "last commit" dates** could not be parsed precisely from JS-rendered file listings for any repo; the dates given derive from release pages, organisation overview pages, and copyright notices. The qualitative "active vs. abandoned" judgment is robust, but exact commit dates may be off by days to weeks.
- **AtomECS license**: this report records **GPL-3.0** based on the `license.txt` file shown in the GitHub repo sidebar; some downstream sources describe AtomECS more loosely. JOSS reviewers should double-check by reading `LICENSE` directly.
- **pylcp license**: the GitHub sidebar shows only a generic "View license" (no SPDX badge). PyLCP is from NIST/JQI, which typically uses a public-domain or NIST-style license, but the precise SPDX string could not be verified without inspecting the `LICENSE` file directly.
- **aisim has no peer-reviewed paper or Zenodo DOI**: as of May 2026, the GitHub repository and Read the Docs page remain the only citable references. qgrav's JOSS paper should cite aisim by GitHub URL + version tag.
- **AllanTools has no peer-reviewed paper either**: the ASCL entry (1804.021) is the canonical archival reference.
- **ObsPy total-commit count**: an exact total-commit number could not be independently confirmed; the ObsPy 1.5.0 release announcement (ObsPy Forum, 2026-03-13) only states the release itself added "649 commits, 425 files modified … from at least 18 contributors". The qualitative "very active" judgment is uncontroversial.
- **"MaxAtoms" was not found** as a public package; this report treats it as non-existent rather than fabricating an entry.
- **Stanford/Berkeley/NPL absence**: the absence of public code is itself an actionable finding for qgrav's positioning, not a search failure - multiple targeted queries returned no hits.