# Scientific-package integration — honest evaluation

This document records which third-party scientific packages were evaluated for
integration into qgrav, and the reasoning for each decision. It exists because
a request to "integrate QuTiP / Qiskit / GEANT4 / LAMMPS" should be answered
honestly: only one of those four genuinely fits light-pulse atom-interferometric
gravimetry, and saying so is more useful than building four integrations of
wildly varying value.

## Summary

| Package | Domain | Fit to qgrav | Decision |
|---------|--------|--------------|----------|
| **QuTiP** | Open quantum systems / Lindblad dynamics | **Strong** | **Integrated (v1.2.1)** |
| Qiskit | Gate-based quantum computing | Weak (novelty only) | Deferred / optional |
| GEANT4 | Radiation & particle transport (Monte Carlo) | None for the core problem | Documented, not built |
| LAMMPS | Classical molecular dynamics | None | Documented, not built |

## QuTiP — integrated (v1.2.1)

**Why it fits.** qgrav's core physical object is a driven two-level (effective
Raman) system whose internal state evolves under Rabi dynamics, with optional
decoherence (spontaneous emission, dephasing). That is *exactly* what QuTiP is
built for. QuTiP integrates the Schrödinger equation (`sesolve`) and the Lindblad
master equation (`mesolve`) numerically — a completely independent code path
from qgrav's closed-form 2×2 propagator matrix.

**What we built.** `src/qgrav/validation/qutip_crosscheck.py`:
- `aisim_rabi_population` vs `qutip_rabi_population` vs `analytic_rabi_population`
  over a grid of (Ω_eff, δ, τ). Result: qgrav's matrix matches the closed form
  to ~3×10⁻¹⁶ (machine precision) and QuTiP's numerical integrator agrees to
  ~1.6×10⁻⁶. **This is the independent-simulator validation the v1.0
  honest-assessment asked for** (caveat C14, partial): a second, unrelated
  engine reproduces qgrav's Raman dynamics.
- `qutip_spontaneous_emission_loss` (Lindblad `mesolve` with a decay collapse
  operator) gives an order-of-magnitude cross-check on the analytic
  `spontaneous_emission_loss_probability`.

**Status.** Optional dependency (`pip install qgrav[qutip]`); tests gated with
`pytest.importorskip("qutip")` so the core suite is unaffected when QuTiP is
absent.

## Qiskit — deferred (novelty, not physics)

**Why it does not fit (yet).** Qiskit models gate-based quantum *computation* on
qubit registers. A light-pulse atom interferometer is not a gate circuit; the
three-pulse Mach–Zehnder is a continuous-time Rabi/free-evolution sequence on a
momentum-state ladder, not a discrete gate sequence on logical qubits.

One could *map* the MZ sequence onto a 1-qubit circuit (π/2 → √X-like, free
evolution → Rz, π → X) purely for **pedagogy or visualization**, but it would
compute nothing the AISim/QuTiP path does not already give, and it risks
implying a quantum-computing capability the project does not have. Deferred as
an optional outreach/teaching feature, not a v1.2 deliverable.

## GEANT4 — not applicable

GEANT4 is a Monte-Carlo toolkit for the passage of particles (and radiation)
through matter — detectors, dosimetry, high-energy physics. The only conceivable
touch-point with an atom gravimeter is modelling stray-light or cosmic-ray
backgrounds in the detection region, which is a third-order systematic far below
anything qgrav currently models and is not part of the gravimetric phase
measurement at all. Integrating GEANT4 would be a large, C++-toolkit-bridging
effort with no path to the published-reference validation bar. **Not built;
documented here so the decision is on record.**

## LAMMPS — not applicable

LAMMPS is a classical molecular-dynamics engine for dense systems of interacting
classical particles (materials, biomolecules). Cold-atom interferometry operates
on a dilute, ultracold *quantum* gas where the relevant dynamics are
single-atom quantum evolution and (at most) mean-field BEC physics — neither of
which LAMMPS addresses. The only superficial overlap (the classical MOT-loading
cloud) is already captured by qgrav's thermal-ensemble sampling. **Not built.**

## If the scope changes

- A **Qiskit circuit view** of the MZ for teaching could be added as
  `qgrav/visuals/circuit_view.py` (optional dep) without affecting the physics.
- **BEC-source** modelling (for instruments like the HUST BEC gravimeter) would
  be a better use of effort than any of GEANT4/LAMMPS, and would reuse the
  existing ensemble/source layer rather than a new external engine.
