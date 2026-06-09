# Template - Email / DM to a prospective physics reviewer

Copy-paste the text below into an email / Slack DM / LinkedIn message. Fill in the bracketed parts.

---

**Subject:** Quick physics review request - atom-interferometer simulation patches (~2 hours of your time)

Dear [Dr / Prof / Name],

I'm a researcher at [IIT Patna / your affiliation] working on **qgrav**, an open-source software platform for atom-interferometer gravimetry R&D. We've recently added a "fully simulated" mode in which the gravity phase emerges from a ballistic trajectory under a chirped Raman laser, rather than being injected via `k_eff·g·T²` as in our previous hybrid approach.

I'm writing because we've made three patches to a vendored copy of the open-source [`aisim`](https://github.com/bleykauf/aisim) atom-interferometer simulator, and before claiming this is "fully simulated" in any publication or talk, I'd like an independent atom-interferometry expert to verify the physics. Specifically:

1. A **`GravityFreePropagator`** that does exact ballistic kinematics under uniform gravity (with optional linear gradient).
2. A **chirped `Wavevectors`** class that adds `chirp_rate · atoms.time` to the two-photon detuning.
3. A patch to **`TwoLevelTransitionPropagator._prop_matrix`** that replaces the upstream `exp(-i·δ·t₀)` phase factor with `exp(-i·(-k_eff·z(t₀) + ½·α·t₀²))`. Our claim is that the upstream formula double-counts gravity and chirp phases in the MZ combination when the detuning is time-varying; we have an empirical (and a symbolic-`sympy`) demonstration of the factor-of-2 over-count.

I've prepared a self-contained **30-page review packet** and a companion **Jupyter notebook** (reproduces every numerical claim in <2 min on a laptop) that lay out:

- The standard derivation (Bordé / Kasevich-Chu) we're trying to reproduce.
- The upstream code and the diff for each patch.
- The factor-of-2 algebra and symbolic verification.
- Cross-validation results between the hybrid and patched modes (rates agree to 0.2%; per-population mismatch ≤ ~25%, attributed to finite-pulse-duration physics).
- A ~2.5 rad gravity-independent constant phase offset we currently remove via an empirical per-sweep calibration, with three competing hypotheses for its physical origin.
- **A structured list of 15 yes/no questions** (§11 of the packet) so you can give targeted feedback rather than open-ended review.

The packet and notebook are at:

- `docs/PHYSICS_REVIEW_PACKET.md` (read-time ~60-90 min; targeted answer of §11 questions ~1.5-2 hr)
- `docs/reviewer_notebook.ipynb` (run-time <2 min)
- Repository: [URL of your GitHub repo / DOI]

I would deeply value your time on this. Any of three outcomes would be useful:

- **You agree the patches are correct**: I'll quote you (with permission, anonymised or not, your choice) in the platform's documentation, and the `FULLY_SIMULATED` study scope label becomes defensible.
- **You spot a bug**: I'll fix it (or revert) and re-test. Without your feedback I'm likely to ship the bug to other users.
- **You think the patches are partially correct but the calibration step is unphysical**: I'll relabel the study scope and continue working on a derivation that eliminates the calibration.

If you don't have time, no pressure - but if you know a PhD student / postdoc who would, a forwarded copy of this email would be hugely helpful.

I'm happy to do a 30-minute video call to walk through the packet first, or to answer questions over email. Reply to me at [your email] / on [your Slack / Twitter / LinkedIn].

Thank you for considering it,

[Your name]
[Affiliation]
[Optional: ORCID, personal page]

---

## Where to send this

Suggested first-line contacts:

| Group / person | Why | Easiest contact |
|----------------|-----|-----------------|
| **AISim upstream maintainer** (Bastian Leykauf, PTB) | Wrote the package you're patching | GitHub issue on `bleykauf/aisim` or email via PTB |
| **Achim Peters / Christian Freier group**, Humboldt | Built the GAIN / QG-1 portable Rb-87 gravimeter (Freier 2016 reference) | Group page contact form |
| **Mark Kasevich group**, Stanford | Original Raman interferometer architects | Postdoc page; PhD students friendlier |
| **SYRTE atom gravimeter group**, Paris | Le Gouët 2008, Cheinet 2008 sensitivity-function papers | sebastien.merlet@obspm.fr is usually open |
| **Holger Müller group**, UC Berkeley | Active modern atom-gravimeter group | Faculty page |
| **Indian Institute of Astrophysics / Raman Research Institute / IUCAA** | Domestic option, faster reply | Direct email |
| **Atom Interferometry Workshop mailing list / iCAP attendees** | Broadcast option | If you've attended a conference |

I'd suggest sending to 3-5 in parallel; the first reply you get back wins.

## After you get a reply

Save the reply (anonymised if requested) into `docs/PHYSICS_REVIEW_RESPONSES.md` as a public record. Update the relevant study-scope labels in code based on the verdict.

---

## Optional add-on: ask for real atom-gravimeter data (v1.3)

If you have rapport with any contacted group, consider adding this paragraph to
the email. qgrav currently validates its *analysis chain* on real
superconducting-gravimeter data (IGETS), but its atom-interferometer
*simulation* is validated only against *published* numbers - because essentially
no raw atom-gravimeter fringe/phase data is public. A shared dataset would
enable the first true hardware-vs-simulation closure test.

> *"Separately: qgrav can ingest raw interferometer output (fringe scans, phase
> time series, or per-shot populations) and compare its simulated Allan
> deviation against a real instrument. If your group has any anonymised raw
> dataset you'd be willing to share (even a single fringe scan or a short
> phase time series with the instrument parameters), it would let us run a
> direct hardware-vs-simulation comparison and we would of course acknowledge
> the contribution. No proprietary calibration details needed - just the raw
> output and the basic sequence parameters (T, τ, cycle time, atom number)."*

If a dataset arrives, drop it under `data/raw/<instrument>/` and we will add a
loader + a real-AI-data regression alongside the existing IGETS one.
