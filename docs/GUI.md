# GUI Guide

Launch the desktop workbench with:

```bash
qgrav gui                                  # the GUI subcommand
qgrav gui --config configs/example.yaml    # pre-load a specific config
qgrav-gui                                  # equivalent standalone entry point
python -m qgrav.gui                        # equivalent module form
```

> If `qgrav` is "command not found", the package isn't installed in the Python
> on your PATH — install it editable with `pip install -e .` from the repo root,
> and make sure that `pip` and your `python` belong to the *same* interpreter.

The window opens on the **Setup & Run** tab with a bundled example already
loaded, so you can press **Run Pipeline** immediately.

> The GUI is a Tkinter desktop app and loads its bundled examples, sample data,
> and in-app documents from the qgrav source checkout. Run it from a clone of
> the repository (an editable `pip install -e .` is fine).

## Tabs

### 1. Setup & Run
A guided form. Pick a **workflow** first and the form shows only the relevant
controls:

- **real_data** — analyse measured gravity data (IGETS / Larzac / CSV / `.ggp`).
- **synthetic** — run the AISim atom-interferometer engine.
- **advanced** — drive everything from raw YAML.

For synthetic studies the **Study model** dropdown now offers all five engine
models:

| Model | What it computes |
|-------|------------------|
| `rabi_scan` | excited fraction vs pulse duration (pulse-area calibration) |
| `mach_zehnder_phase_scan` | one 3-pulse fringe vs applied laser phase |
| `gravity_sweep` | fringe phase vs gravity *g* (emergent-gravity check) |
| `multi_drop_cycle` | **flagship** — repeated drops with a noise budget + servo → ASD / Allan |
| `vibration_sensitivity_sweep` | contrast / phase vs reference-mirror vibration |

Two collapsible sections expose the full physics surface (hover any field for a
tooltip explaining it):

- **Advanced physics** — random seed, single-photon (Raman) detuning, gravity
  propagation (ballistic + chirped laser), lock-to-mid-fringe, gravity gradient,
  and a Zernike wavefront (coefficients + radius).
- **Multi-drop noise budget & servo** — drops per cycle, cycle time, true *g*,
  detection σ_p, Raman/vibration phase noise, correlated seismic vibration
  (Peterson NLNM/NHNM) with an isolation cut-off, fringe-visibility fitting, and
  a fringe-lock servo (`integrator` or full `pid` with k_p/k_i/k_d).

The right pane shows recommended next steps, a live run summary, and a run log.
**Pull from editor** / **Apply controls to editor** keep the form and the YAML
in sync.

### 2. Data Browser
Scan a directory or ZIP archive of superconducting-gravimeter data, list station
codes, preview a station (time series, histogram, PSD, Allan deviation), inspect
gap statistics, and push the selection into Setup or create a config from it.
**Use sample** loads the bundled IGETS sample station (no download).

### 3. Config Editor
Raw YAML view for precise, reproducible runs. This is the source of truth for a
run — the Run button always uses the editor contents.

### 4. Results & Visuals
Metric cards, a full metrics tree, interactive plots (single plots first, then
the dashboard), and one-click access to the HTML report, `metrics.json`, and
`SUMMARY.md`.

### 5. Validation
- **Published reference library** — the registry of measured values from
  published atom-gravimeter papers that the automated regression suite checks
  against. Click a row for its description, source, tolerance band, and DOI.
- **Reproduce a published measurement (one click)** — a table of the five
  reference instruments (Freier 2016, Hu 2013, Ménoret 2018, Xu 2022, Wu 2019)
  showing each paper's published short-term ASD, qgrav's predicted ASD, the
  ratio, and whether it is within the documented band. Select a paper, optionally
  raise the atom count for fidelity, then **Load into editor** or **Load & Run**
  to build and execute a `multi_drop_cycle` config from that paper's parameters
  and noise budget. Freier 2016 is the primary regression target.
- **Independent cross-check (QuTiP)** — recompute the single Raman-pulse dynamics
  a different way and report the disagreement with qgrav's closed-form matrix.
  *AISim vs analytic* needs no extra packages (expect ~1e-15); *Full QuTiP
  cross-check* integrates the Schrödinger equation independently
  (`pip install qgrav[qutip]`, expect ~1e-6).

### 6. Guides
A navigable in-app guide: **Quick start, Workflows, Study models, Noise &
realism, Validation & reproducing a paper, Interpreting results, Independent
cross-checks, How to move ahead, Glossary, Common mistakes** — plus a
**Project documents** section that opens the on-disk guides (GUIDE, complete
guide, v1 physics upgrade, scientific-package evaluation, physics review packet,
performance notes, roadmap, changelog).

## Recommended workflow

**Reproduce a published instrument**
1. Open **Validation**, select e.g. *Freier 2016*.
2. Set **Atoms** to ~4000 for a faithful (slower) run.
3. **Load & Run**.
4. Read the ASD / Allan deviation and report in **Results & Visuals**.

**Analyse real gravimetry data**
1. **Data Browser → Use sample** (or browse to your own dataset) → **Scan**.
2. Preview a station, then **Use in Setup**.
3. **Run Pipeline**, inspect PSD / Allan / coverage in **Results & Visuals**.

## Honesty note
The one-click reproductions match *published numbers*, not raw laboratory data,
and have not yet had an independent expert physics review. The QuTiP cross-check
validates the single-pulse quantum dynamics, not the noise budget or
systematics. See **Guides → How to move ahead** for the steps that change that.
