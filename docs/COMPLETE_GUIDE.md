# qgrav - The Complete Guide

**Quantum Gravimeter R&D Platform**

*A software-first research workbench for simulating, benchmarking, and analyzing quantum gravity sensors.*

**Author:** Aditya Prakash  
**License:** GPL-3.0

> **Reader's note:** sections 1-15 below describe the core feature
> set and remain accurate; those workflows are unchanged. The later
> capabilities (emergent-gravity simulation, multi-drop cycle with servo &
> correlated noise, AC Stark, wavefront aberrations, published-reference
> validation, QuTiP cross-check, performance harness) are summarised in
> [§16: What's new since v1.0](#16-whats-new-since-v10-capabilities-map) and
> detailed in [V1_PHYSICS_UPGRADE.md](V1_PHYSICS_UPGRADE.md),
> [AISIM_GRAVIMETER_STUDIES.md](AISIM_GRAVIMETER_STUDIES.md),
> [SCIENTIFIC_PACKAGE_EVALUATION.md](SCIENTIFIC_PACKAGE_EVALUATION.md),
> [PERFORMANCE.md](PERFORMANCE.md), and [CHANGELOG.md](../CHANGELOG.md).

---

## Table of Contents

1. [What Is This Software?](#1-what-is-this-software)
2. [The Science - Explained Simply](#2-the-science---explained-simply)
3. [Installation](#3-installation)
4. [Quick Start - Your First Run in 2 Minutes](#4-quick-start---your-first-run-in-2-minutes)
5. [The Three Modes of Operation](#5-the-three-modes-of-operation)
6. [The GUI - Screen by Screen](#6-the-gui---screen-by-screen)
7. [The Command Line Interface](#7-the-command-line-interface)
8. [Configuration Reference](#8-configuration-reference)
9. [Understanding the Output](#9-understanding-the-output)
10. [The Simulation Engine (AISim)](#10-the-simulation-engine-aisim)
11. [Metrics and What They Mean](#11-metrics-and-what-they-mean)
12. [Real-World Gravity Data](#12-real-world-gravity-data)
13. [Architecture and Code Map](#13-architecture-and-code-map)
14. [Troubleshooting](#14-troubleshooting)
15. [Glossary](#15-glossary)

---

## 1. What Is This Software?

qgrav is a desktop research platform that lets you **design, simulate, and validate quantum gravity sensors** - entirely in software, before you ever build hardware.

It answers questions like:

- "If I build an atom interferometer with these parameters, how sensitive will it be to gravity?"
- "How does my sensor's noise compare to existing superconducting gravimeters?"
- "What happens to my measurement if the lab floor vibrates?"
- "Can my algorithm extract a 4-nanometer displacement signal buried in noise?"

The platform connects four stages into a single pipeline:

```
Simulation  →  Bench (data source)  →  Algorithms  →  Metrics & Report
```

You configure everything in a single YAML file (or through the GUI), click "Run Pipeline", and get a timestamped report folder with plots, metrics, and an interactive HTML report.

### Who Is This For?

- **Physics researchers** designing atom interferometer gravimeters
- **Metrology engineers** benchmarking sensor performance against published standards
- **Students** learning about quantum sensing, signal processing, and gravimetry
- **Anyone** who wants to understand how gravity is measured at the nanoscale

---

## 2. The Science - Explained Simply

### What Is Gravity Measurement?

Gravity - the force that keeps you on the ground - is not perfectly uniform across Earth's surface. It varies by tiny amounts depending on what is underground (rock, water, oil, voids), your altitude, tides, and even nearby buildings.

Measuring these tiny variations is called **gravimetry**. It matters for:

- **Mineral and oil exploration** - dense deposits change local gravity
- **Earthquake and volcano monitoring** - mass movement underground shifts gravity
- **Navigation** - submarines use gravity maps when GPS is unavailable
- **Fundamental physics** - testing whether gravity behaves as Einstein predicted

The variations we care about are incredibly small. We measure them in **microGals** (µGal), where:

> **1 µGal = 0.00000001 m/s²** - about one ten-billionth of the gravity you feel standing up.

### How Do Atom Interferometers Measure Gravity?

Traditional gravimeters use springs or superconducting spheres. Atom interferometers use something more exotic: **clouds of atoms cooled to near absolute zero**.

Here is the idea, step by step:

**Step 1 - Cool the atoms.**  
A cloud of about 1,000 rubidium-87 atoms is cooled to microkelvin temperatures (millionths of a degree above absolute zero). At this temperature, atoms behave more like waves than particles - a quantum mechanical effect.

**Step 2 - Split the wave.**  
A precisely timed laser pulse (called a **π/2 pulse**, lasting about 23 microseconds) puts each atom into a **superposition** - it simultaneously travels along two different paths. Think of it like splitting a beam of light with a half-mirror, except with matter.

> **Superposition** means the atom is in two states at once. It is not "half here, half there" - it is genuinely in both places simultaneously until you measure it. This is the core weirdness of quantum mechanics, and also what makes the measurement so sensitive.

**Step 3 - Let them fall.**  
For about 260 milliseconds (a quarter of a second), the two paths of each atom fall freely under gravity. During this time, gravity accelerates the atoms, and each path accumulates a different quantum **phase** - a kind of internal clock tick.

**Step 4 - Recombine.**  
A second laser pulse (a **π pulse** - the mirror) redirects the paths, and a third pulse (another π/2 pulse) recombines them. The atoms interfere with themselves - just like light waves creating bright and dark fringes.

**Step 5 - Count.**  
You count how many atoms end up in each output port. The ratio depends on the **phase difference** between the two paths - and that phase difference is directly proportional to gravity:

```
Phase difference = k_eff × g × T²
```

Where:
- **k_eff** is the effective wave vector of the laser (~16 million radians per meter for rubidium)
- **g** is gravitational acceleration (~9.81 m/s²)
- **T** is the free-fall time (0.26 seconds in our default setup)

This three-pulse sequence is called a **Mach-Zehnder interferometer** - named after the optical interferometer it resembles, not the physicist Ernst Mach (well, actually, it is named after him - the same Mach from "Mach number").

### What Is a Virtual Interferometer?

Before building an atom interferometer (which costs millions and takes years), you want to know: will my design work? How sensitive will it be? What noise sources will dominate?

qgrav's **virtual interferometer** generates synthetic measurement data - fake but physically realistic I/Q signals (in-phase and quadrature) with configurable:

- Displacement signals (nanometer-scale sine waves)
- Measurement noise
- DC drift (slow baseline wandering)
- Amplitude drift

This lets you test your signal processing algorithms against a known truth. If your algorithm can extract a 4-nanometer, 3 Hz signal from noisy virtual data, it will probably work on real data too.

### What Is a Superconducting Gravimeter?

A superconducting gravimeter (SG) is the current gold standard for continuous gravity monitoring. It levitates a small niobium sphere in a magnetic field produced by superconducting coils. Changes in gravity change the sphere's position, which is measured with extreme precision.

SGs achieve noise floors below 1 nanoGal/√Hz - better than any atom interferometer built so far. The qgrav platform lets you analyze real SG data (in GGP format) and compare its noise characteristics against your proposed atom interferometer design.

> **GGP** stands for Global Geodynamics Project format - a standard text format for sharing gravity measurements between observatories worldwide.

---

## 3. Installation

### Requirements

- **Python 3.11, 3.12, or 3.13** - all three are tested in CI on Linux and Windows
- Works on Windows, macOS, and Linux
- No GPU required

> **Note:** The continuous-integration matrix runs the full test suite against
> Python 3.11, 3.12, and 3.13. Any of the three is fine; 3.12 remains a safe
> default if a dependency lacks 3.13 wheels on your platform.

### Step-by-Step Install

```bash
# 1. Clone the repository
git clone https://github.com/adityagit94/Quantum-Gravitometer.git
cd Quantum-Gravitometer

# 2. Create a virtual environment (recommended)
python -m venv .venv

# 3. Activate it
# On Windows:
.venv\Scripts\activate
# On macOS/Linux:
source .venv/bin/activate

# 4. Install in development mode
pip install -e .
```

That is it. All dependencies (NumPy, SciPy, Matplotlib, PyYAML, Jinja2) install automatically.

### Verify Installation

```bash
qgrav --help
```

You should see:

```
usage: qgrav [-h] {run,gui,convert-ggp,validate-data,info} ...
Quantum gravimeter R&D platform
```

---

## 4. Quick Start - Your First Run in 2 Minutes

### Option A: The GUI (Recommended for Beginners)

```bash
qgrav gui
```

This opens the **qgrav Research Workbench** - a desktop application. It loads a default virtual interferometer example automatically. Click **"Run Pipeline"** in the top toolbar.

Within a few seconds, you will see:

- Metric cards at the top showing RMSE, SNR, and Allan deviation minimum
- Plots in the Results tab: dashboard, raw signals, displacement, PSD, Allan deviation
- A timestamped report folder in `runs/`

### Option B: The Command Line

```bash
qgrav run --config configs/example.yaml
```

This runs the same virtual interferometer pipeline and prints the path to the generated report:

```
Report written: runs/example_20260512_143022/report.html
Open in browser: E:\quantum-grav-platform\runs\example_20260512_143022\report.html
```

Open `report.html` in your browser for the full interactive report.

### Option C: Try a Gravity Sweep Simulation

```bash
qgrav run --config configs/example_aisim_gravity_sweep.yaml
```

This runs a full atom interferometer simulation: creates 600 virtual atoms, runs them through a three-pulse Mach-Zehnder sequence, sweeps gravity across 61 points, and tells you exactly how sensitive your design would be - in µGal/√Hz.

---

## 5. The Three Modes of Operation

qgrav has three bench types - three different sources of data that feed into the analysis pipeline.

### Mode 1: Virtual Interferometer (`bench.type: virtual`)

**What it does:** Generates synthetic I/Q (in-phase/quadrature) signals from a simulated optical interferometer.

**When to use it:**
- Testing and comparing signal processing algorithms
- Benchmarking against known truth (you know exactly what displacement was injected)
- Quick experiments without any real data

**How it works:**
You define displacement signals as a stack of sine waves (e.g., "4 nanometers at 3 Hz plus 2 nanometers at 21 Hz"). The simulator converts these into I/Q quadrature signals - the same kind of signals a real optical interferometer produces - and adds realistic noise, DC offset drift, and amplitude drift.

Two algorithms then try to recover the original displacement:
- **Baseline:** Simple arctangent demodulation with global offset subtraction
- **Improved:** Adaptive offset tracking (exponential moving average) plus phase smoothing (Savitzky-Golay filter)

The pipeline compares both algorithms against the known truth and reports RMSE, MAE, SNR, and bias.

> **I/Q signals:** In an optical interferometer, you split a laser beam and recombine it. The output intensity depends on the path difference (displacement). By using two detectors 90° apart, you get two signals - I (in-phase, proportional to cosine of the phase) and Q (quadrature, proportional to sine). Together, they let you unambiguously extract the phase, even through multiple rotations.

### Mode 2: Real Interferometer (`bench.type: real`)

**What it does:** Reads real experimental I/Q data from a CSV file.

**When to use it:**
- Analyzing data from your actual lab interferometer
- Comparing your bench measurements against the virtual model

**Input format:** A CSV file with columns `I_meas`, `Q_meas`, and optionally `t` (time) and `x_true` (ground truth displacement). If you have ground truth, the pipeline computes error statistics just like virtual mode.

### Mode 3: Real Gravity (`bench.type: real_gravity`)

**What it does:** Analyzes gravity residual time-series from superconducting gravimeters or other gravity sensors.

**When to use it:**
- Benchmarking your atom interferometer design against real-world gravity data
- Analyzing noise characteristics of existing gravity stations
- Learning what "good" gravity data looks like

**Input formats supported:**
- `.ggp` files (Global Geodynamics Project format)
- Directories of `.ggp` files
- `.zip` archives containing `.ggp` files
- Pre-converted CSV with `timestamp` and `gravity_residual` columns

The pipeline automatically handles data gaps, identifies the longest contiguous segment, and reports gap statistics (how many samples missing, how many duplicates, the largest clean block).

---

## 6. The GUI - Screen by Screen

Launch the GUI with:

```bash
qgrav gui
# Or with a specific config:
qgrav gui --config configs/example_real_gravity.yaml
```

### The Top Bar

Across the top of the window, you will find:

| Element | What It Does |
|---------|-------------|
| **Title bar** | Shows "qgrav Research Workbench" and a subtitle: "simulation → validation → statistics → report" |
| **Config path** | Shows the path to the currently loaded YAML config file |
| **Browse** | Opens a file picker to select a YAML config |
| **Load** | Loads the config file shown in the path field into the editor |
| **Validate** | Checks the YAML in the editor for structural errors without running anything |
| **Save As** | Saves the current editor content to a new YAML file |
| **Examples** | Dropdown with 7 pre-built example configs you can load instantly |
| **Run Pipeline** | The main action button - runs the full pipeline on the current config |
| **Progress bar** | Animates while a pipeline run is in progress |
| **Metric cards** | After a run, shows key numbers: RMSE, SNR, Allan minimum, etc. |

### Tab 1: Setup & Run

This is where you configure your experiment through visual controls instead of editing YAML.

**Start Here - Workflow Selector**

Choose one of three workflows:

| Workflow | What It Shows | Best For |
|----------|--------------|----------|
| `real_data` | Real-data input controls, analysis settings | Analyzing `.ggp` gravity data or real interferometer CSV |
| `synthetic` | AISim simulation controls, atom parameters | Running atom interferometer simulations |
| `advanced` | All controls visible, direct YAML editing | Power users who want full control |

The interface hides irrelevant controls based on your workflow choice. If you pick `real_data`, you will not see atom count or pulse duration fields - they do not apply.

**Analysis Settings**

| Control | What It Means |
|---------|--------------|
| Run name | A label for your output folder (e.g., "my_first_run") |
| Allan backend | Which implementation computes Allan deviation: `auto` (fast custom), `custom`, or `allantools` |
| Allan data type | Whether input data represents `freq` (frequency deviations) or `phase` (displacement/phase series) |
| PSD method | `welch` (smoother, recommended) or `periodogram` (simpler, noisier) |
| Compare Allan backends | Check this to run both custom and allantools and cross-validate |

**Real-Data Input**

| Control | What It Means |
|---------|--------------|
| Bench type | `real_gravity` for gravity data, `real` for interferometer CSV |
| Gravity source | Path to your `.ggp` file, directory, `.zip`, or CSV |
| Station code | The station identifier (e.g., `ap046` for a station in Arizona) |
| Use browser selection | Copies the station you picked in the Data Browser tab |

**Synthetic Gravimeter Study**

| Control | What It Means |
|---------|--------------|
| Enable AISim module | Turns on atom interferometer simulation |
| Study model | Which simulation to run: `rabi_scan`, `mach_zehnder_phase_scan`, `gravity_sweep`, `multi_drop_cycle`, or `vibration_sensitivity_sweep` (see Section 10) |
| Atoms | Number of atoms in the simulated cloud (more = less noise, slower) |
| π/2 pulse duration | How long each beam-splitter pulse lasts (seconds) |
| Interferometer T | Free-fall time between pulses - the most important sensitivity parameter |
| Gravity center | The gravity value to simulate around (9.81 m/s² for Earth) |
| Gravity span | How wide a range of gravity to sweep (in m/s²) |

Two collapsible sections (collapsed by default) expose the full physics surface.
Every field shows a hover tooltip explaining it:

- **Advanced physics** - random seed, single-photon (Raman) detuning, gravity
  propagation (the ballistic + chirped-laser "emergent gravity" path),
  lock-to-mid-fringe, gravity gradient, and a Zernike wavefront (coefficients +
  radius). These apply to `mach_zehnder_phase_scan`, `gravity_sweep`, and
  `multi_drop_cycle`.
- **Multi-drop noise budget & servo** (for `multi_drop_cycle`) - drops per cycle,
  cycle time, true *g*, detection σ_p, Raman/vibration phase noise, correlated
  seismic vibration (Peterson NLNM/NHNM) with an isolation cut-off, fringe-
  visibility fitting, and a fringe-lock servo (`integrator` or full `pid`).

Anything not surfaced as a control (e.g. cloud/detector geometry, temperatures)
can still be set directly in the **Config Editor** tab.

**Actions**

| Button | What It Does |
|--------|-------------|
| Pull from editor | Reads the YAML in the Config Editor tab and updates these controls |
| Apply controls to editor | Writes these control values back into the YAML editor |
| Open report | Opens the HTML report from the last run in your browser |
| Open run folder | Opens the output folder in your file manager |

**Right Side**

- **Recommended next steps** - contextual guidance based on your workflow
- **Run summary** - after a run, shows the text summary (SUMMARY.md content)
- **Live run log** - real-time messages during pipeline execution

### Tab 2: Data Browser

This tab lets you explore gravity datasets before committing to a full pipeline run.

**How to use it:**

1. Enter or browse to a data source (a directory of `.ggp` files, a `.zip` archive, or click "Use sample" for the bundled example)
2. Click **Scan** - the left panel populates with all stations found, showing station code, longitude, and latitude
3. Click a station in the list - details appear below (sample count, time span, gap report)
4. Click **Preview selected** - the right panel shows a quick time-series plot and histogram for data quality inspection
5. If the data looks good, click **Use in Setup** or **Create config** to generate a ready-to-run YAML configuration

This workflow prevents you from running a 30-minute pipeline on bad data. Always preview first.

### Tab 3: Config Editor

A full-featured YAML text editor. This is the ground truth for what the pipeline actually runs - every control in the Setup tab just modifies this YAML.

You can:
- Edit any config key directly
- Paste in a config from elsewhere
- Use the **Validate** button to check for errors
- Save your modifications with **Save As**

If you are comfortable with YAML, this is the fastest way to work.

### Tab 4: Results & Visuals

After a pipeline run completes, this tab shows everything:

**Left Panel - Metrics Browser**

A tree view showing every computed metric. For a virtual run, this includes:
- Error statistics (RMSE, MAE, SNR, bias) for both baseline and improved algorithms
- Allan deviation minimum (the optimal averaging time)
- Noise type identification (what kind of noise dominates)
- PSD parameters

For a gravity run:
- Station metadata (code, coordinates, sample rate)
- Gap report (total samples, gaps found, contiguous segment size)
- Allan deviation values
- Noise classification

Quick-access buttons: **Open HTML** (interactive report), **Run folder**, **Metrics JSON** (raw data), **Summary** (text report).

**Right Panel - Interactive Visuals**

A plot selector dropdown with all available plot types:

| Plot Kind | What It Shows | Available In |
|-----------|--------------|-------------|
| `dashboard` | 2×2 grid of key plots (overview) | All modes |
| `raw` | Raw I and Q time-series | Virtual, Real IFO |
| `displacement` | Recovered displacement vs. truth | Virtual, Real IFO |
| `gravity_series` | Full gravity residual time-series | Real Gravity |
| `histogram` | Distribution of gravity values | Real Gravity |
| `psd` | Power Spectral Density (log-log) | All modes |
| `allan` | Allan Deviation vs. averaging time | All modes |
| `error_hist` | Error distribution histogram | Virtual (with truth) |
| Simulation plots | Model-specific (Rabi curves, fringes, etc.) | AISim runs |

Every plot is interactive - you can zoom, pan, and save using the matplotlib toolbar below the plot.

**Bottom - Run Log**

A detailed text log of everything that happened during the run: configuration loaded, data generated, algorithms applied, metrics computed, files saved.

### Tab 5: Validation

This tab connects the simulation to the published literature and to an
independent solver.

**Published reference library** - the registry of measured values from
published atom-gravimeter papers that the automated regression suite checks
against. Click any row to see its description, source, tolerance band, and DOI.

**Reproduce a published measurement (one click)** - a table of five reference
instruments (Freier 2016, Hu 2013, Ménoret 2018, Xu 2022, Wu 2019). For each it
shows the paper's published short-term ASD, qgrav's predicted ASD, the ratio,
and whether it is within the documented band. Select a paper, optionally raise
the atom count for fidelity, then **Load into editor** or **Load & Run** to
build and execute a `multi_drop_cycle` config from that paper's parameters and
noise budget. Freier 2016 is the primary regression target.

**Independent cross-check (QuTiP)** - recomputes the single Raman-pulse dynamics
a different way and reports the disagreement with qgrav's closed-form matrix.
*AISim vs analytic* needs no extra packages (expect ~1e-15); *Full QuTiP
cross-check* integrates the Schrödinger equation independently
(`pip install qgrav[qutip]`, expect ~1e-6). Both run in a background thread.

> The reproductions match *published numbers*, not raw laboratory data, and have
> not yet had an independent expert physics review. The QuTiP check validates the
> single-pulse quantum dynamics, not the noise budget or systematics.

### Tab 6: Guides

A navigable in-app reference. The left panel lists topics; the right panel shows
the content. Topics include:
- Quick start, Workflows, Study models, Noise & realism (multi-drop)
- Validation & reproducing a paper, Interpreting results, Independent cross-checks
- **How to move ahead** (the review / publish / JOSS roadmap)
- Glossary and Common mistakes

A **Project documents** section opens the on-disk guides (this guide, the v1
physics upgrade, the scientific-package evaluation, the physics review packet,
the performance notes, the roadmap, and the changelog).

---

## 7. The Command Line Interface

qgrav provides five CLI commands: `run`, `gui`, `convert-ggp`, `validate-data`,
and `info`. The three you will use most are below; `validate-data` prints a
dataset quality summary without running a full pipeline, and `info` prints the
qgrav version and environment.

### `qgrav run` - Run a Pipeline

```bash
qgrav run --config path/to/config.yaml
```

Runs the full pipeline (data generation or loading → algorithms → metrics → plots → report) and prints the output path. All plots are saved to disk as PNGs, and the interactive report is generated as HTML.

### `qgrav gui` - Launch the Desktop Application

```bash
qgrav gui                                    # Opens with default example
qgrav gui --config configs/example.yaml      # Opens with a specific config pre-loaded
```

### `qgrav convert-ggp` - Convert Gravity Data

```bash
qgrav convert-ggp --source data/raw/sg_sample --out output.csv --station ap046
```

Converts `.ggp` gravimetry data to a standard CSV format. Useful for preprocessing data before analysis, or for importing into other tools.

| Flag | Required | Description |
|------|----------|-------------|
| `--source` | Yes | Path to `.ggp` file, directory, or `.zip` archive |
| `--out` | Yes | Output CSV file path |
| `--station` | No | Station code (required if source has multiple stations) |
| `--metadata` | No | Path to `SG station.txt` metadata file |

---

## 8. Configuration Reference

Every qgrav run is controlled by a YAML configuration file. Here is the complete reference.

### Minimal Example (Virtual Mode)

```yaml
output:
  runs_dir: runs
  name: my_first_run

bench:
  type: virtual

bench_virtual_ifo:
  wavelength_m: 1.55e-6
  sample_rate_hz: 2000
  duration_s: 5.0
  displacement_sines:
    - amplitude_m: 4.0e-9
      freq_hz: 3.0
      phase_rad: 0.0
  measurement_noise_std: 0.03

algorithms:
  improved:
    offset_tracking_alpha: 0.003
    phase_smooth_window: 21

stats:
  metrics_backend: auto
  psd_method: welch
  welch_nperseg: 512
  welch_noverlap: 256

simulation:
  enabled: false
```

### Minimal Example (Real Gravity Mode)

```yaml
output:
  runs_dir: runs
  name: gravity_analysis

bench:
  type: real_gravity

bench_real_gravity:
  source_path: data/raw/sg_sample
  station_code: ap046
  segment_strategy: longest_contiguous

stats:
  metrics_backend: auto
  psd_method: welch
  welch_nperseg: 128
  welch_noverlap: 64
```

### Section-by-Section Reference

#### `output` - Where Results Go

| Key | Type | Description |
|-----|------|-------------|
| `runs_dir` | string | Base directory for run output folders. Default: `runs` |
| `name` | string | Human-readable name. Used in the folder name: `{name}_{timestamp}/` |

#### `bench` - Data Source Selection

| Key | Values | Description |
|-----|--------|-------------|
| `type` | `virtual`, `real`, `real_gravity` | Which data source to use |

#### `bench_virtual_ifo` - Synthetic Interferometer

*Required when `bench.type: virtual`*

| Key | Type | Description | Example |
|-----|------|-------------|---------|
| `wavelength_m` | float | Laser wavelength in meters | `1.55e-6` (1550 nm infrared) |
| `sample_rate_hz` | float | Measurement samples per second | `2000` |
| `duration_s` | float | Total data collection time | `5.0` |
| `displacement_sines` | list | Sine wave components to inject | See below |
| `measurement_noise_std` | float | Gaussian noise level on I/Q channels | `0.03` |
| `amplitude` | float | Peak I/Q signal amplitude | `1.0` |
| `dc_offset` | float | Constant offset on I channel | `0.2` |
| `offset_drift_std_per_s` | float | Random-walk rate of DC drift | `0.04` |
| `amplitude_drift_std_per_s` | float | Random-walk rate of amplitude drift | `0.01` |
| `seed` | int | Random seed for reproducibility | `7` |

Each entry in `displacement_sines`:

| Key | Type | Description | Example |
|-----|------|-------------|---------|
| `amplitude_m` | float | Peak displacement in meters | `4.0e-9` (4 nanometers) |
| `freq_hz` | float | Oscillation frequency | `3.0` Hz |
| `phase_rad` | float | Initial phase offset in radians | `0.0` |

#### `bench_real_ifo` - Real Interferometer CSV

*Required when `bench.type: real`*

| Key | Type | Description |
|-----|------|-------------|
| `csv_path` | string | Path to CSV file with I/Q data |
| `delimiter` | string | Column separator (`,` or `;`) |
| `has_header` | bool | Whether the first row is a header |
| `wavelength_m` | float | Laser wavelength used in the experiment |
| `sample_rate_hz` | float | Sample rate (only needed if no `t` column) |

CSV must contain columns: `I_meas`, `Q_meas`. Optional: `t` (time), `x_true` (ground truth).

#### `bench_real_gravity` - Gravimetry Data

*Required when `bench.type: real_gravity`*

| Key | Type | Description |
|-----|------|-------------|
| `source_path` | string | Path to `.ggp` file, directory, `.zip`, or CSV |
| `station_code` | string | Station identifier (e.g., `ap046`) |
| `segment_strategy` | string | How to handle data gaps. Use `longest_contiguous` |
| `metadata_path` | string | Optional path to `SG station.txt` metadata file |
| `apply_corrections` | bool | Master switch for the residual-correction stage (default: `false`) |
| `igets_level` | string | Force IGETS product level: `auto`, `1`, `2`, `3` (default: `auto`) |
| `tide_backend` | string | Tide model: `auto`, `pygtide`, `internal_hw95` (default: `auto`) |
| `pressure_csv_path` | string | Path to co-located pressure CSV (columns: `unix_seconds`, `pressure_hpa`) |
| `pressure_admittance_nm_s2_per_hpa` | float | Barometric admittance (default: `-3.0`) |
| `corrections.polar_motion.enabled` | bool | Pole-tide (polar-motion) correction (default: `false`) |
| `corrections.polar_motion.xp_arcsec` / `yp_arcsec` | float or list | IERS C04 pole coordinates (constant or per-sample) |
| `corrections.polar_motion.gravimetric_factor` | float | IERS gravimetric δ factor (default: `1.164`) |
| `corrections.ocean_loading.enabled` | bool | Ocean tidal-loading correction (default: `false`) |
| `corrections.ocean_loading.constituents` | list | Onsala-BLQ entries `{name, amplitude_nm_s2, phase_deg}` |

> Tide and pressure are the workhorse corrections; polar motion and ocean
> loading complete the standard SG residual chain and are both off by default.
> They are config-driven and fully offline - you supply the IERS pole
> coordinates and the Onsala free-ocean-loading constituents. The full nested
> `corrections:` block is documented in
> [REAL_GRAVITY_DATA.md](REAL_GRAVITY_DATA.md).

#### `algorithms` - Signal Processing

*Used only for virtual and real interferometer modes*

| Key | Type | Description | Default |
|-----|------|-------------|---------|
| `improved.offset_tracking_alpha` | float | EWMA smoothing factor for DC tracking. Lower = smoother. | `0.003` |
| `improved.phase_smooth_window` | int | Moving average window for phase smoothing (must be odd) | `21` |

#### `stats` - Metrics Configuration

| Key | Values | Description |
|-----|--------|-------------|
| `metrics_backend` | `auto`, `custom`, `allantools` | Allan deviation implementation |
| `allan_data_type` | `freq`, `phase` | How to interpret input data |
| `psd_method` | `welch`, `periodogram` | Power spectrum estimation method |
| `welch_nperseg` | int | FFT segment size for Welch method (power of 2) |
| `welch_noverlap` | int | Overlap between segments (typically half of nperseg) |
| `compare_allan_backends` | bool | Run both backends and cross-check |
| `comparison_backend` | string | Which backend is the secondary one |

#### `simulation` - Atom Interferometer Studies

| Key | Type | Description |
|-----|------|-------------|
| `enabled` | bool | Turn simulation on or off |
| `backend` | string | Simulation engine (currently only `aisim`) |
| `model` | string | Study type (see Section 10) |
| `seed` | int | Random seed |
| `n_atoms` | int | Number of atoms in the cloud |

Additional model-specific parameters are documented in Section 10.

---

## 9. Understanding the Output

Every pipeline run creates a timestamped folder:

```
runs/my_run_20260512_143022/
├── config_used.yaml        ← Exact config that produced this run
├── data.npz                ← All numerical arrays (NumPy format)
├── metrics.json            ← Every computed metric as structured JSON
├── SUMMARY.md              ← Human-readable text summary
├── report.html             ← Interactive HTML report (open in browser)
└── plots/
    ├── dashboard.png       ← 2×2 overview of key plots
    ├── allan.png           ← Allan deviation with noise annotation
    ├── psd.png             ← Power spectral density
    └── ...                 ← Additional mode-specific plots
```

### config_used.yaml

An exact snapshot of the configuration. You can re-run any experiment by feeding this file back:

```bash
qgrav run --config runs/my_run_20260512_143022/config_used.yaml
```

### data.npz

A NumPy archive containing all arrays from the run. Load it in Python:

```python
import numpy as np
data = np.load("runs/my_run_20260512_143022/data.npz")
print(list(data.keys()))  # ['t', 'I_meas', 'Q_meas', 'x_true', 'x_baseline', 'x_improved', ...]
```

### metrics.json

Structured metrics. Example for a virtual run:

```json
{
  "qgrav_output_format_version": "1.0",
  "qgrav_version": "1.5.1",
  "error_stats": {
    "baseline": {"rmse_m": 1.2e-9, "mae_m": 0.9e-9, "snr_db": 15.3, "bias_m": 0.05e-9},
    "improved": {"rmse_m": 0.4e-9, "mae_m": 0.3e-9, "snr_db": 24.1, "bias_m": 0.01e-9}
  },
  "allan_deviation": {"tau_s": ["..."], "adev_m": ["..."]},
  "noise_identification": {
    "method": "lag1_autocorrelation",
    "noise_type": "white frequency modulation",
    "alpha_int": 0,
    "legacy_slope_method": {"slope": -0.52, "noise_type": "white frequency modulation"}
  },
  "allan_minimum": {"optimal_tau_s": 0.025, "minimum_adev_m": 2.1e-10}
}
```

For real gravity runs with corrections enabled, additional keys appear:

```json
{
  "data_product_level_at_analysis": 1,
  "corrections_applied": ["tide", "pressure"],
  "correction_metrics": {
    "tide_rms_subtracted_ugal": 85.3,
    "tide_backend_used": "internal_hw95",
    "pressure_rms_subtracted_ugal": 1.2
  }
}
```

### report.html

The crown jewel. Open this in any browser. It contains:
- A summary of what was run and why
- All plots rendered at high resolution
- A formatted metrics table
- The full configuration used
- A copy of the text summary

### plots/

Individual plot images (PNG) for use in papers, presentations, or reports.

---

## 10. The Simulation Engine (AISim)

qgrav includes a vendored copy of **AISim** - an atom interferometer simulator that models individual atoms as quantum mechanical wave packets.

### Study Model 1: Rabi Scan (`rabi_scan`)

**What it does:** Drives a two-level atomic transition with pulses of increasing duration and records the excited-state population.

**Why it matters:** Before you can run an interferometer, you need to know your pulse parameters. A Rabi scan tells you: "At what pulse duration does my atom flip from ground to excited state?" This calibrates the π/2 and π pulse times that the interferometer needs.

**What you see:** An oscillating curve (Rabi oscillations) - population swinging between 0% and 100% as pulse duration increases. The first peak tells you the π pulse time.

**Key parameters:**

| Parameter | Meaning | Typical Value |
|-----------|---------|---------------|
| `n_atoms` | Atoms in the cloud | 300-500 |
| `tau_step_s` | Time step between pulse durations | `1.0e-6` (1 µs) |
| `n_steps` | Number of points in the scan | 30-60 |
| `center_rabi_freq_hz` | Expected Rabi frequency | 15,000 Hz |

### Study Model 2: Mach-Zehnder Phase Scan (`mach_zehnder_phase_scan`)

**What it does:** Runs the full three-pulse interferometer sequence while sweeping an artificial phase offset from 0 to 2π.

**Why it matters:** This measures your **fringe visibility** (contrast) - how cleanly you can distinguish constructive from destructive interference. Higher visibility = better sensitivity. Real-world effects (atom temperature, beam quality, timing errors) reduce visibility.

**What you see:** A sinusoidal fringe pattern. The amplitude of the sine tells you the contrast (ideally 1.0, realistically 0.7-0.9). The pipeline fits a sine curve and reports visibility and fit quality.

**Key parameters:**

| Parameter | Meaning | Typical Value |
|-----------|---------|---------------|
| `n_atoms` | Atoms in the cloud | 600 |
| `tau_pi_half_s` | Duration of each π/2 beam-splitter pulse | `2.3e-5` (23 µs) |
| `interferometer_time_s` | Free-fall time T between pulses | `0.26` (260 ms) |
| `n_phase_points` | Points in the phase sweep | 61 |

### Study Model 3: Gravity Sweep (`gravity_sweep`)

**What it does:** Combines AISim's atom-optics simulation with analytical gravity phase to answer: "If gravity changes by X µGal, how does my atom interferometer's output change?"

**Why it matters:** This is the core gravimeter question. The output tells you your **gravity sensitivity** - how small a gravity change you can detect. This is the number you would put in a research paper.

**How it works:**

1. AISim creates the atom cloud and simulates the three-pulse sequence (computing realistic contrast)
2. For each gravity value in the sweep, the analytical phase `k_eff × g × T²` is computed
3. The atom populations in each output port are recorded
4. The pipeline extracts the mid-fringe slope (sensitivity) and converts it to µGal/√Hz

**Key parameters:**

| Parameter | Meaning | Typical Value |
|-----------|---------|---------------|
| `gravity_center_m_s2` | Center of the gravity sweep | `9.81` |
| `gravity_span_m_s2` | Width of sweep (±) | `6.0e-6` (±6 µGal) |
| `n_gravity_points` | Points in the sweep | 61 |
| `lock_to_midfringe` | Bias phase to steepest point of fringe | `true` |

**Output metrics:**
- Shot-noise sensitivity in m/s²/√Hz and µGal/√Hz
- Fringe visibility (contrast)
- Systematic effect estimates (gravity gradient, Coriolis)

### Study Model 4: Vibration Sensitivity Sweep (`vibration_sensitivity_sweep`)

**What it does:** Simulates a vibrating reference mirror and measures how much the vibration corrupts the gravity measurement.

**Why it matters:** Real labs have vibrations - from traffic, HVAC systems, earthquakes, even people walking. This study tells you: "If my mirror vibrates at frequency f with amplitude A, what equivalent gravity error does that create?"

**The physics:**

The three-pulse interferometer samples the mirror position at three times: t=0, t=T, and t=2T. The vibration-induced phase is:

```
Phase_vibration = k_eff × [z(0) - 2×z(T) + z(2T)]
```

This is a second-difference operation - the same operation a digital accelerometer performs. It makes the interferometer sensitive to mirror acceleration, not position or velocity.

**Key parameters:**

| Parameter | Meaning | Typical Value |
|-----------|---------|---------------|
| `vibration_frequency_hz` | Mirror vibration frequency | `1.0` Hz |
| `amplitude_max_m` | Maximum mirror displacement | `5.0e-8` (50 nm) |
| `n_amplitude_points` | Points in the amplitude sweep | 41 |
| `gravity_ref_m_s2` | Background gravity value | `9.81` |

### Study Model 5: Multi-Drop Cycle (`multi_drop_cycle`)

**What it does:** Simulates a full repeated-drop gravimeter campaign. The same
three-pulse interferometer is run for many successive drops with a realistic
per-shot noise budget and an optional fringe-lock servo, producing a gravity
time series from which the pipeline computes an amplitude spectral density (ASD)
and Allan deviation - the same observables real transportable gravimeters report.

**Why it matters:** This is the **fully simulated** path. The recovered *g*
emerges from the microscopic atom-optics (with `gravity_propagation: true`,
from a ballistic trajectory under a chirped Raman laser), not from a closed-form
phase formula. It is what the Validation tab's one-click reproductions drive.

**Key parameters:**

| Parameter | Meaning | Typical Value |
|-----------|---------|---------------|
| `n_drops` | Number of measurement drops | `100` |
| `cycle_time_s` | Time per drop (sets the ASD/Allan time axis) | `1.0`-`1.5` |
| `gravity_true_m_s2` | Ground-truth *g* to recover | `9.81` |
| `detection_sigma_p` | Per-shot detection noise on the excited fraction | `6e-3` |
| `raman_phase_noise_rad` | Per-shot laser + vibration phase noise | `1.2e-2` |
| `projection_noise` | Draw each drop's count from `Binomial(N_det, P)` so the quantum projection-noise floor emerges from single-atom statistics (off by default) | `true` |
| `raman_substeps` | Integrate each finite-τ Raman pulse as N composed slices (1 = exact previous behaviour) | `8` |
| `fit_visibility` | Fit contrast and use it in the P→g inversion | `true` |
| `servo_enabled` / `servo_type` | Fringe-lock loop (`integrator` or `pid`) | `true` / `integrator` |

The short-term sensitivity is set by the noise budget, not the atom number - but
too few atoms raises the 1/√N projection-noise floor and can swamp the budget,
so a faithful reproduction uses several thousand atoms.

> **v1.5 emergent refinements.** With `projection_noise: true`, the shot-noise
> floor is no longer added analytically - each drop's detected count is drawn
> from `Binomial(N_det, P)` via the run's seeded RNG, and the measured floor
> matches `σ_g = 1/(√N_det·k_eff·T²)` to ~0.2 %. With `raman_substeps: N` (N > 1),
> the finite-duration Raman pulses are integrated sub-pulse, with ballistic fall
> *during* each pulse, so the finite-τ physics converges numerically to the
> Bertoldi 2019 closed form. Both are off by default (exact previous behaviour)
> and exposed in the GUI's multi-drop noise-budget section.

---

## 11. Metrics and What They Mean

### Error Statistics (Virtual/Real IFO Modes)

| Metric | Full Name | What It Tells You |
|--------|-----------|-------------------|
| **RMSE** | Root Mean Square Error | Average error magnitude between recovered and true displacement. Lower is better. Units: meters. |
| **MAE** | Mean Absolute Error | Similar to RMSE but less sensitive to outliers. Units: meters. |
| **SNR** | Signal-to-Noise Ratio | How much signal power vs. noise power, in decibels. Higher is better. 20 dB = signal is 10× larger than noise. |
| **Bias** | Systematic offset | Constant error in the recovered displacement. Should be near zero. Units: meters. |

### Allan Deviation

**What it is:** A measure of measurement stability versus averaging time.

Imagine you take gravity readings every second. If you average 10 readings together, is your answer more stable? What about 100? 1,000?

Allan deviation answers this. You plot it on a log-log scale:

- **X-axis:** Averaging time τ (tau) - from one sample period to a large fraction of total measurement time
- **Y-axis:** Allan deviation σ(τ) - the typical fluctuation at that averaging time

**What to look for:**

- The curve should decrease as τ increases (averaging helps)
- It reaches a **minimum** - the optimal averaging time for your sensor
- After the minimum, it may increase again (due to long-term drift)

The **minimum Allan deviation** is one of the most important numbers. It tells you the best stability your sensor can achieve.

### Noise Type Identification

qgrav uses two complementary methods to identify the dominant noise type:

**ACF method (primary, v0.8):** The lag-1 autocorrelation method (Riley 2004) works directly on the time series. It computes the autocorrelation at lag 1 and maps it to a noise type. This is more robust than slope-fitting, especially for mixed noise or short datasets. The result appears in `metrics.json` under `noise_identification`.

**Slope method (legacy):** Fits the log-log slope of the Allan deviation curve. The slope reveals the noise type:

| Slope | Noise Type | Meaning |
|-------|-----------|---------|
| −1.0 | White phase noise | Random, uncorrelated measurement errors |
| −0.75 | Flicker phase noise | Low-frequency measurement fluctuations |
| −0.5 | White frequency noise | Random walk in phase - ideal sensor behavior |
| −0.25 | Flicker frequency noise | Low-frequency instability |
| +0.5 | Random walk frequency | Long-term drift - sensor is wandering |

The slope result is preserved in `metrics.json` under `noise_identification.legacy_slope_method` for cross-checking.

**White frequency noise (slope = −0.5)** is the best case for a gravimeter - it means your noise is purely statistical and averages down as expected.

### Power Spectral Density (PSD)

**What it is:** Shows how noise power is distributed across frequencies.

- **X-axis:** Frequency (Hz) - from very slow variations to half the sample rate
- **Y-axis:** Power density (m²/Hz or equivalent) - how much noise at each frequency

**What to look for:**

- Flat PSD = white noise (good)
- Rising toward low frequencies = 1/f noise or drift (common, manageable)
- Sharp peaks = specific interference sources (vibration at a known frequency, electrical pickup)

**Welch vs. Periodogram:**
- **Welch method:** Divides data into overlapping segments, computes PSD for each, and averages. Smoother, more reliable. Recommended for publication-quality results.
- **Periodogram:** Single FFT of the entire dataset. Noisier but preserves frequency resolution. Useful for spotting narrow peaks.

### Shot-Noise Sensitivity (AISim Modes)

The fundamental quantum limit on your gravity measurement:

```
Δg = 1 / (C × k_eff × T² × √(N / T_cycle))
```

| Symbol | Meaning |
|--------|---------|
| C | Fringe visibility (0 to 1) - higher is better |
| k_eff | Effective wave vector (~16 million rad/m) |
| T | Free-fall time between pulses |
| N | Number of atoms per shot |
| T_cycle | Total time per measurement cycle |

Reported in two units:
- **m/s²/√Hz** - SI standard
- **µGal/√Hz** - practical unit (1 µGal = 10⁻⁸ m/s²)

Typical values for a well-designed atom gravimeter: 0.1-10 µGal/√Hz.

### Systematic Effects

Order-of-magnitude estimates for two major error sources:

**Gravity gradient:** Earth's gravity decreases with altitude at ~3.086 µGal per meter. During the 260 ms free fall, atoms drop ~0.33 m, experiencing a slightly different gravity at the top vs. bottom of their trajectory. Effect: ~1 µGal.

**Coriolis force:** Earth's rotation causes a sideways force on falling atoms. Depends on latitude and atomic velocity. Effect: 1-10 µGal.

These are estimates - the actual values depend on your specific setup.

### Sensitivity Function and Vibration Noise Budget (v0.8)

The Mach-Zehnder sensitivity function g_s(t) (Cheinet 2008) quantifies how laser-phase perturbations or mirror vibrations translate into interferometer phase shift. This is the foundation for vibration noise budgets.

Available functions in `qgrav.physics.sensitivity_function`:

- `sensitivity_function_time_domain(t, *, interferometer_time_s, pulse_duration_s=0)` - returns g_s(t): -1 on [0,T], +1 on [T,2T] for instantaneous pulses, or continuous ramps for finite-duration pulses.
- `transfer_function_vibration(f_hz, ...)` - returns |G(2pif)|^2. Has notches at f = n/T (the interferometer is blind to vibrations at these frequencies) and rolls off as 1/f^2 above 1/T.
- `acceleration_to_phase_transfer_function_sq(f_hz, *, ..., k_eff_rad_per_m)` - converts acceleration PSD to phase variance: |H_a|^2 = 16 k_eff^2 sin^4(pi f T) / (2 pi f)^4.
- `integrate_vibration_noise(psd, f_hz, ...)` - integrates an acceleration PSD against the transfer function and returns the equivalent gravity noise in m/s^2 and uGal.

Built-in Peterson 1993 NLNM/NHNM seismic noise models (`interpolate_psd(f, model="nlnm")`) provide reference acceleration PSDs for estimating vibration-limited performance at quiet and noisy sites.

### Real-Gravimetry Residual Chain (v0.8, completed in v1.5)

For real gravity data at IGETS Level 1 or Level 2, enable `apply_corrections: true`
to run the standard superconducting-gravimeter residual chain, in order:

1. **Solid-earth body tide** - using PyGTide (if installed) or the internal 20-constituent HW95 model
2. **Atmospheric pressure loading** - linear admittance model (-3 nm/s^2/hPa, Crossley 1995)
3. **Polar motion (pole tide)** - from user-supplied IERS C04 pole coordinates and the IERS gravimetric δ factor *(off by default, v1.5)*
4. **Ocean tidal loading** - from user-supplied Onsala-BLQ constituent amplitudes and phases, reusing the HW95 astronomical-argument machinery *(off by default, v1.5)*

Each stage follows the `corrected = observed − effect` convention and is recorded
in `metrics.json` under `correction_metrics`. Without at least the tide
correction, the Allan deviation is dominated by the ~100 µGal body-tide signal
rather than instrument noise. See the `bench_real_gravity` configuration keys in
Section 8, and [REAL_GRAVITY_DATA.md](REAL_GRAVITY_DATA.md) for the full nested
`corrections:` block.

---

## 12. Real-World Gravity Data

### Bundled Sample Data

qgrav ships with a sample dataset in `data/raw/sg_sample/`:

- `ap046.ggp` - Real gravity data from station AP046
- `SG station.txt` - Metadata file listing station code, longitude, and latitude

### Using Your Own Data

#### GGP Files

Place your `.ggp` files in a directory and point `source_path` to it. The GGP format is simple:

```
YYYYMMDD HHMMSS value
20230101 000000 14.2345
20230101 001000 14.2346
```

Each value is a gravity residual. The pipeline auto-detects the sample rate from the timestamps.

#### ZIP Archives

Many data repositories distribute GGP data as ZIP files. Point `source_path` directly to the `.zip` file - qgrav will extract and parse it automatically, including searching for the `SG station.txt` metadata file inside.

#### CSV Files

If your data is already in CSV format, use columns named `timestamp` and `gravity_residual`. Optional columns: `station_code`, `longitude`, `latitude`.

### Data Quality

The pipeline automatically reports:

| Metric | What It Means |
|--------|--------------|
| Median interval | Expected time between samples |
| Total samples | How many data points in the file |
| Duplicate timestamps | Rows with identical timestamps (should be 0) |
| Reverse-time rows | Rows where time goes backward (should be 0) |
| Gap count | Number of gaps in the time-series |
| Estimated missing samples | How many data points should exist but don't |
| Contiguous segment size | Length of the longest gap-free block (used for analysis) |

### Converting GGP to CSV

```bash
qgrav convert-ggp --source data/raw/sg_sample --out station_ap046.csv --station ap046
```

The output CSV has columns: `timestamp`, `gravity_residual`, `station_code`.

---

## 13. Architecture and Code Map

```
src/qgrav/
├── __init__.py              Version string (1.5.1)
├── cli.py                   Command-line interface (run, gui, convert-ggp, validate-data, info)
├── config.py                YAML loading, validation (incl. corrections keys)
├── types.py                 Shared dataclasses / type aliases
├── pipeline/                Run orchestration (split package)
│   ├── _interferometer.py   Virtual / real IFO path
│   ├── _gravity.py          Real-gravity path + corrections stage
│   ├── _simulation.py       AISim study dispatch
│   ├── _plots.py            Per-run figure generation
│   └── _common.py           Shared run scaffolding, output_format_version
│
├── bench_ifo/               Data source layer
│   ├── virtual_ifo.py       Synthetic I/Q signal generator
│   ├── real_ifo.py          CSV reader for real interferometer data
│   └── real_gravity.py      Wrapper for gravimetry dataset loading
│
├── algorithms/              Signal processing
│   ├── baseline.py          Simple arctangent demodulation
│   └── improved.py          Adaptive offset tracking + phase smoothing
│
├── metrics/                 Statistical analysis
│   ├── allan.py             Allan deviation, noise ID (ACF + slope), Allan minimum
│   ├── psd.py               Power spectral density (Welch + periodogram)
│   └── summary.py           Error stats (RMSE, MAE, SNR, bias), improvement %
│
├── physics/                 Physical models and constants
│   ├── constants.py         Physical constants registry
│   ├── sensitivity_function.py  MZ sensitivity + vibration transfer functions
│   ├── _seismic_models.py   Peterson NLNM/NHNM noise floor models
│   ├── phase_models.py      Gravity phase, vibration phase, shot-noise sensitivity
│   ├── systematics.py       Gravity gradient, Coriolis effect (uses constants module)
│   ├── noise_models.py      White noise, random walk, outlier injection
│   ├── readout_models.py    Output port population + servo models
│   ├── atom_source.py       Atom-cloud source distributions
│   ├── ground_truth.py      Truth-signal generation for benchmarking
│   └── pulse_sequence.py    Three-pulse Mach-Zehnder timing
│
├── sim_ai/                  Simulation engine (AISim adapter, split package)
│   ├── aisim_adapter.py     Facade re-exporting every historical name
│   ├── _adapter_core.py     Shared cloud/pulse helpers, study_scope labels
│   ├── _scans.py            Rabi scan, MZ phase scan
│   ├── _sweeps.py           Gravity sweep, vibration sensitivity sweep
│   ├── _multi_drop.py       Multi-drop cycle, projection noise, fringe-lock servo
│   ├── _config_run.py       YAML-driven study dispatch
│   ├── _aisim_overrides.py  Integrated-phase propagator, chirped wavevectors, sub-pulse
│   └── simple_ai.py         Lightweight analytic fallback model
│
├── datasets/                Data format handling
│   ├── gravimetry.py        GGP parsing, station metadata, gap detection, CSV conversion
│   ├── corrections.py       Tide, pressure, polar-motion & ocean-loading; IGETS level detection
│   └── _tides_hw95.py       20-constituent HW95 internal tide model
│
├── validation/              Published references and truth checks
│   ├── published_references.py  14 benchmark values with DOI links
│   ├── freier_2016_setup.py … wu_2019_setup.py  Per-paper reproduction setups (5)
│   ├── qutip_crosscheck.py  Independent QuTiP Schrödinger cross-check
│   ├── truth_checks.py      Per-study pass/fail checks
│   └── compare.py           R-squared, Pearson correlation, curve comparison
│
├── reporting/               HTML report generation
│   └── report.py            Jinja2 templates (scope panel, corrections, level banner)
├── visuals.py               Plot generation (dashboard, individual, simulation plots)
│
├── gui/                     Desktop application
│   ├── __main__.py          GUI entry point
│   ├── app.py               QGravApp - assembles the per-tab mixins
│   ├── _tab_setup_run.py … _tab_guides.py  Per-tab mixin modules (6 tabs)
│   └── widgets/             Custom widgets (MetricCards, ScrollableFrame, Tooltip, Collapsible)
│
└── vendor/                  Vendored dependencies
    ├── aisim/               Atom interferometer simulator
    └── allantools/          Allan deviation library
```

### Pipeline Flow

```
config.yaml
    │
    ▼
load_config() ──→ validate_config_structure()
    │
    ▼
run_pipeline()
    │
    ├──→ [virtual] generate_virtual_ifo() → estimate_displacement_baseline()
    │                                     → estimate_displacement_improved()
    │                                     → compute error stats
    │
    ├──→ [real]    load_real_ifo_csv()    → same algorithms as virtual
    │
    ├──→ [real_gravity] load_real_gravity_dataset() → gap analysis
    │                       │
    │                       ▼
    │                   detect_igets_level()
    │                       │
    │                       ▼  (if apply_corrections: true)
    │                   tide → pressure → polar motion → ocean loading
    │
    ├──→ [if simulation.enabled] run_aisim_*() → study_scope labels
    │
    ├──→ allan_deviation_overlapping() ─→ identify_noise_type_acf()
    ├──→ compute_psd()
    │
    ▼
save outputs:
    metrics.json  (qgrav_output_format_version: "1.0")
    data.npz, plots/, SUMMARY.md
    report.html   (study-scope panel, corrections section, level banner)
```

---

## 14. Troubleshooting

### "ModuleNotFoundError: No module named 'qgrav'"

You need to install the package:

```bash
pip install -e .
```

Make sure you are in the project root directory (where `pyproject.toml` lives) and using the correct Python version.

### "Unsupported gravimetry source: C:\Users\...\AppData\Local\Temp\..."

This was a known bug (fixed in v0.7.0). The GUI was resolving relative paths against a temp directory instead of the project root. Solution: update to the latest version (`git pull`).

### "Configuration root must be a YAML mapping (dictionary)"

The YAML editor is empty or contains invalid YAML. Load a config file first (use **Browse** or the **Examples** menu).

### Python 3.13+ / 3.14 Issues

Some dependencies (especially those using C extensions) may not have wheels for Python 3.13+. If you encounter build errors, use Python 3.12:

```bash
# Windows - specify Python version explicitly
py -3.12 -m venv .venv
```

### GUI Does Not Launch

If you see a Tcl/Tk error:

1. Make sure your Python installation includes tkinter (it is included by default on Windows and macOS; on Linux, install `python3-tk`)
2. Try running from a non-virtual-environment Python first to isolate the issue

### Matplotlib Font Warnings

qgrav sets a custom matplotlib config directory (`~/.qgrav_mpl`) to avoid permission issues. Font cache warnings on first run are normal and harmless.

### Tests Fail with "Real gravity sample data not found"

The 3 real-gravity tests require sample data in `data/raw/sg_sample/`. This directory is gitignored, so fresh clones may not have it. The tests will skip automatically with a clear message. This is expected behavior.

---

## 15. Glossary

| Term | Definition |
|------|-----------|
| **Allan deviation** | A measure of measurement stability over different averaging times. Standard tool in precision measurement science. |
| **Atom interferometer** | A device that exploits quantum superposition of atoms to measure accelerations (including gravity) with extreme precision. |
| **Body-tide elasticity** | Factor (delta ~ 1.16) by which the solid Earth amplifies the direct tidal acceleration due to elastic deformation of the mantle and crust. |
| **Contrast / Visibility** | How well the interferometer distinguishes between constructive and destructive interference. Ranges from 0 (useless) to 1 (perfect). |
| **Coriolis effect** | A deflection caused by Earth's rotation. Affects falling atoms because they have a horizontal velocity component. |
| **Doodson number** | Six-integer code identifying each harmonic constituent of the tidal potential. Used in the HW95 catalogue. |
| **EWMA** | Exponentially Weighted Moving Average - a filter that tracks slow changes while ignoring fast noise. |
| **Fringe** | The oscillating output pattern of an interferometer as the phase difference changes. Like light and dark bands in an optical experiment. |
| **GGP** | Global Geodynamics Project - a standard text format for sharing gravity time-series data between observatories. |
| **Gravimetry** | The science of measuring gravitational acceleration and its spatial/temporal variations. |
| **HW95** | Hartmann-Wenzel 1995 tidal potential catalogue (~12,000 constituents). qgrav uses a simplified 20-constituent version. |
| **I/Q signals** | In-phase and Quadrature - two signals 90° apart that together encode the full phase of an interferometric measurement. |
| **IGETS** | International Geodynamics and Earth Tide Service. Distributes superconducting gravimeter data at three processing levels (L1: raw, L2: minute, L3: hourly corrected). |
| **k_eff** | Effective wave vector - the momentum kick atoms receive from laser pulses. For rubidium-87: ~16 million rad/m. |
| **Mach-Zehnder** | A three-pulse interferometer geometry: split → redirect → recombine. The standard design for atom gravimeters. |
| **microGal (µGal)** | Unit of gravitational acceleration. 1 µGal = 10⁻⁸ m/s². Typical gravity variations of interest are 0.1-100 µGal. |
| **nanoGal (nGal)** | 1 nGal = 10⁻¹¹ m/s². The sensitivity floor of the best superconducting gravimeters. |
| **NLNM / NHNM** | New Low/High Noise Models (Peterson 1993). Acceleration PSD bounds for seismically quiet and noisy sites worldwide. |
| **PSD** | Power Spectral Density - shows how noise power is distributed across frequency. |
| **Sensitivity function** | g_s(t) - the time-domain function relating a laser-phase perturbation to the resulting interferometer phase shift. |
| **Tide correction** | Subtracting the predicted solid-earth body tide from a gravity residual time series so that instrument noise is revealed. |
| **Transfer function** | Frequency-domain representation of how input noise (laser phase or mirror acceleration) maps to interferometer output phase. |
| **π pulse** | A laser pulse that flips an atom from ground to excited state (or vice versa). Acts as a "mirror" in the interferometer. |
| **π/2 pulse** | A laser pulse that puts an atom into a 50/50 superposition. Acts as a "beam splitter." |
| **Rabi oscillation** | The oscillation of an atom between ground and excited states when driven by a resonant laser pulse. |
| **RMSE** | Root Mean Square Error - the standard measure of how far estimated values are from true values. |
| **Shot noise** | The fundamental quantum noise limit from counting discrete atoms. Scales as 1/√N. |
| **SNR** | Signal-to-Noise Ratio - in decibels (dB). Every 6 dB roughly doubles the signal-to-noise. |
| **Superposition** | A quantum state where a particle exists in multiple states simultaneously. Collapses to one state upon measurement. |
| **Superconducting gravimeter (SG)** | A gravity sensor that levitates a superconducting sphere in a magnetic field. Current gold standard for continuous gravity monitoring. |
| **T (interferometer time)** | Free-fall time between pulses in a Mach-Zehnder sequence. The single most important parameter for sensitivity - sensitivity scales as T². |
| **Welch method** | A PSD estimation technique that averages multiple overlapping FFT windows. Produces smoother, more reliable spectra. |
| **YAML** | "YAML Ain't Markup Language" - a human-readable configuration file format used by qgrav. |

---

## 16. What's new since v1.0 (capabilities map)

Sections 1-15 describe the v0.8 foundation. The v1.0-v1.5 releases added a full
emergent-gravity simulation, sub-pulse Raman integration, realistic and emergent
noise, the complete real-data residual chain, published-reference validation, an
independent cross-check, and release infrastructure. Use this section as the
index into those capabilities; each links to its detailed doc.

### Emergent-gravity simulation (v1.0)

The gravimetric phase is no longer injected as `k_eff·g·T²`. Atoms propagate
ballistically (`GravityFreePropagator`) between Raman pulses; a chirped laser
(`ChirpedWavevectors`) tracks the fall; the integrated-phase propagator yields
`k_eff·(g − g_chirp)·T²` from first principles. Enable per study with
`gravity_propagation: true` in the simulation config block. Details:
[V1_PHYSICS_UPGRADE.md](V1_PHYSICS_UPGRADE.md). Honest scope labels
(`FULLY_SIMULATED` / `HYBRID` / `ANALYTICAL_ONLY`) accompany every result.

### Noise & systematics (v1.0-v1.2)

- **Multi-drop measurement cycle** (`multi_drop_cycle` model): N independent
  drops, detection noise, correlated NLNM/NHNM seismic vibration, a
  fringe-locking **integrator or PID servo** (with anti-windup), and an
  overlapping Allan deviation. Config keys: `n_drops`, `cycle_time_s`,
  `detection_sigma_p`, `raman_phase_noise_rad`, `correlated_vibration`,
  `seismic_model`, `vibration_isolation_cutoff_hz`, `fit_visibility`,
  `servo_type`, `servo_kp/ki/kd`.
- **AC Stark / light shift** (`single_photon_detuning_hz`) and **wavefront
  aberrations** (`wavefront_zernike_coeffs`, `wavefront_radius_m`) are
  configurable for the `gravity_sweep` and `mach_zehnder_phase_scan` models. The
  wavefront effect is the curvature systematic (second-order in inter-pulse
  drift); see [AISIM_GRAVIMETER_STUDIES.md](AISIM_GRAVIMETER_STUDIES.md).

### Published-reference validation (v1.1-v1.2)

Automated regressions reproduce five published instruments - **Freier 2016**
(primary, 96 nm/s²/√Hz), **Hu 2013**, **Ménoret 2018**, **Xu 2022**, **Wu
2019** - each curated in `qgrav.validation.<name>_setup`. Run with
`pytest -m slow`. The instrument parameters and noise budgets are sourced
verbatim in `docs/research/`.

### Independent cross-validation (v1.2.1)

An optional **QuTiP** backend (`pip install qgrav[qutip]`) reproduces the Raman
dynamics by independent numerical Schrödinger/Lindblad integration, agreeing
with qgrav's closed-form propagator to ~1.6×10⁻⁶. Why QuTiP and not
Qiskit/GEANT4/LAMMPS: [SCIENTIFIC_PACKAGE_EVALUATION.md](SCIENTIFIC_PACKAGE_EVALUATION.md).

### Real-data validation (v1.3)

qgrav's Allan/PSD analysis chain is validated on **real superconducting-
gravimeter data** (IGETS station `ap046`, bundled). Note this validates the
analysis chain, not the atom-interferometer simulation against hardware (no
public atom-gravimeter raw data exists).

### Performance & release infrastructure (v1.2-v1.3)

- **Performance:** single MZ ~1.3 ms, 60-pt sweep ~0.1-0.2 s, 100-drop cycle
  ~0.3 s. Harness: `pytest -m benchmark`; numbers in [PERFORMANCE.md](PERFORMANCE.md).
- **CI/packaging:** GitHub Actions (Linux + Windows × Python 3.11-3.13),
  nightly slow + QuTiP + benchmark runs, PyPI Trusted-Publishing release
  workflow, a Docker image, and this MkDocs site.

### Emergent pulse physics & complete residual chain (v1.5)

- **Sub-pulse Raman integration** (`raman_substeps: N`, default 1): each
  finite-duration Raman pulse is applied as N composed slices with ballistic
  fall *during* the pulse and midpoint-evaluated Rabi/Doppler/chirp, so the
  finite-τ physics emerges numerically. φ(N) converges to the Bertoldi 2019 /
  Fang 2018 closed form (within 2×10⁻³ relative at η = 0.04) and the
  g-independent calibration artefact falls ≈1/N. Implemented entirely in the
  override layer; the vendored AISim core is untouched.
- **Emergent Monte-Carlo quantum projection noise** (`projection_noise: true`,
  off by default): each drop's detected count is drawn from `Binomial(N_det, P)`
  via the run's seeded RNG, so the QPN floor emerges from single-atom
  statistics and matches `σ_g = 1/(√N_det·k_eff·T²)` to 0.2 %.
- **Polar-motion and ocean-loading reductions** complete the standard SG
  residual chain (tide → pressure → polar motion → ocean loading). Both are off
  by default, config-driven, and fully offline. See Sections 8 and 11 and
  [REAL_GRAVITY_DATA.md](REAL_GRAVITY_DATA.md).
- **GUI multi-run Allan-curve comparison** (Results tab): a `Compare runs…`
  dialog overlays σ(τ) from any number of run folders on one log-log figure,
  with optional normalization to each curve's σ(τ=1 s) and PNG export.
- **Internal modularization:** the ~2,000-line `aisim_adapter` and ~2,650-line
  `gui/app.py` were split into private per-concern modules and per-tab mixins,
  preserving every public and historical import path.

### Epistemic status

What qgrav can be quoted for, and what still requires an independent expert
review, is laid out honestly in [PHYSICS_REVIEW_PACKET.md](PHYSICS_REVIEW_PACKET.md),
[SCIENTIFIC_HARDENING.md](SCIENTIFIC_HARDENING.md), and
[AI_USAGE_DISCLOSURE.md](AI_USAGE_DISCLOSURE.md).

---

*This guide covers qgrav through v1.5.1 (Sections 1-15 describe the stable v0.8
foundation; Section 16 maps the v1.0-v1.5 additions). For the latest version,
visit [github.com/adityagit94/Quantum-Gravitometer](https://github.com/adityagit94/Quantum-Gravitometer).*
