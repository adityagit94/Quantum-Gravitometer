# docs/RESEARCH_REAL_DATA_SOURCES.md

# Real Instrument & Public Data Sources for Validating `qgrav` (Atom‑Interferometric Gravimetry Simulator)

*Compiled May 28, 2026. All quotes are verbatim from the cited primary source. Units converted to SI in‑line; "vague" numbers are reported verbatim. The three regression targets are Freier 2016 (GAIN/Humboldt), Hu 2013 (HUST Wuhan), and Ménoret 2018 (Muquans AQG).*

---

## 1. IGETS — International Geodynamics and Earth Tide Service

**TL;DR.** IGETS is the authoritative open archive of superconducting‑gravimeter (SG) time series. As of the IAG GGOS IGETS page (last modified 2025‑09‑22), "The observation network of today comprises 47 stations some of which recording continuously already several decades." Boy et al. (2020) cite "more than 40 stations and 60 different sensors." Data are in monthly ASCII files in GGP File Format V5 (`*.ggp`), at 1 s (SEC), 1 min (MIN), and 1 h (HOUR) cadence, served via SFTP (migrated from FTP in May 2025) on `igetsftp.gfz-potsdam.de` after free registration, with DOI landing pages on `dataservices.gfz-potsdam.de/igets/`. This is the single best public benchmark for cross‑validating an absolute/atom‑interferometric gravimeter against a co‑located reference (tides, hydrology, ocean loading).

### 1.1 Authoritative documentation
- **Voigt, C., Förste, C., Wziontek, H., Crossley, D., Meurers, B., Pálinkáš, V., Hinderer, J., Boy, J.-P., Barriot, J.-P., Sun, H. (2016)** *Report on the Data Base of the International Geodynamics and Earth Tide Service (IGETS)*, GFZ Scientific Technical Report STR 16/08. DOI **10.2312/GFZ.b103-16087**. Full text: https://d-nb.info/1121017096/34
- **Boy, J.-P. et al. (2020)** "Achievements of the First 4 Years of the International Geodynamics and Earth Tide Service (IGETS) 2015–2019", *IAG Symposia* 152. DOI **10.1007/1345_2020_94**.
- GFZ ISDC landing page: https://isdc.gfz.de/igets-data-base/ (last modified 13 January 2026)
- IGETS Central Bureau (Strasbourg): http://igets.u-strasbg.fr/
- IAG GGOS service page (https://geodesy.science/item/igets/), verbatim: "The observation network of today comprises 47 stations some of which recording continuously already several decades."

### 1.2 Data products (3 levels)
Verbatim from GFZ ISDC (https://isdc.gfz.de/igets-data-base/):
> "Raw gravity and local pressure records sampled at 1 or 2 seconds, in addition to the same records decimated at 1‑minute samples (Level 1 products). Gravity and pressure data corrected for instrumental perturbations, ready for tidal analysis. This product is derived from the previous datasets, and is computed by one or several Analysis Centers (Level 2 products). Gravity residuals after particular geophysical corrections (including solid Earth tides, polar motion, tidal and non‑tidal loading effects). This product is also derived from the previous dataset and is computed by one or several Analysis Centers (Level 3 products)."

Analysis Centres: Level 2 at the University of French Polynesia (Tahiti); Level 3 at EOST Strasbourg.

### 1.3 File naming convention (STR 16/08, §7)
Verbatim:
> "IGETS-\<instrument\>-\<type\>-\<sensor\>-\<year\>\<month\>\<code\>.\<extension\>"

Instrument codes: `SG` (observatory SG), `IOSG` (new‑generation observatory SG), `IGRAV` (transportable iGrav), `LCR` (LaCoste & Romberg spring gravimeter). Type codes: `SEC` (Level‑1 1 s), `MIN` (Level‑1 1 min), `AUX` (auxiliary), `STATLOG`, `CAL`, `CORMIN` (Level‑2 corrected min), `HOUR` (Level‑2 hourly), `RESHOUR` (Level‑3 hourly residuals). Extensions: `.ggp`, `.aux`, `.log`, `.cal`, `.zip`.

Verbatim worked examples from STR 16/08:
> "IGETS-SG-SEC-su052-20160100.ggp for Level 1 second file with repair code '00' from January 2016 observed with SG 052 at Sutherland and IGETS-SG-CORMIN-we030-1-20160122.ggp for Level 2 minute file with repair code '22' from January 2016 observed with the lower sensor of dual SG 030 at Wettzell."

### 1.4 File header / channels (STR 16/08, §9.1)
Seven‑line header followed by the fixed column header line:
> "yyyymmdd hhmmss gravity(V) pressure(V)"
followed by
> "C***********************************"

Data block delimiters: `77777777 0.0 0.0` (start of record), `99999999` (end of file). Data lines use Fortran format `(i4,2i2,1x,3i2,2f10.6)`. **Level‑1 units are volts** (`gravity(V)`, `pressure(V)`). Level‑2 (CORMIN/HOUR) gravity is calibrated to **nm/s²** (1 nm/s² = 1 × 10⁻⁹ m/s² = 0.1 µGal). Calibration files (`.cal`) hold the amplitude calibration `gcal` in **nm/s²/V**, pressure calibration `pcal` in **hPa/V**, and a phase time lag in **seconds**.

Unit conversion check: 1 µGal = 1 × 10⁻⁸ m/s² = 10 nm/s². Free‑air gravity gradient ≈ 3.086 × 10⁻⁶ s⁻² ≈ 0.3086 mGal/m = 3086 nm/s²/m.

### 1.5 Access (post‑May 2025 SFTP)
STR 16/08 (verbatim):
> "The new user access for browsing and downloading the IGETS data is realized by a FTP server, which can be accessed by ftp://igetsftp.gfz-potsdam.de."

> "The directory structure for all SG products on the FTP server ftp://igetsftp.gfz-potsdam.de for all SG data products is /\<station\>/\<sensor\>/\<level\>/\<year\>/"

Post‑2025 transition documented by Wang et al. (2025) "IDDS: a software to download IGETS data", *Earth Science Informatics*, DOI **10.1007/s12145-025-02067-6** (verbatim):
> "traditional methods for accessing IGETS data via the File Transfer Protocol (FTP), and transitioning to the Secure File Transfer Protocol (SFTP) by May 2025, require cumbersome dedicated client software like FileZilla."

Registration is mandatory and free. Licence: most station DOI landing pages (e.g. Larzac, Membach, Bad Homburg) declare **CC BY 4.0**.

### 1.6 Current station coverage (selection relevant to qgrav)
From the GFZ ISDC table (https://isdc.gfz.de/igets-data-base/), highlights:

| Station | Sensor | Start | Notes / Relevance |
|---|---|---|---|
| Bad Homburg (BH) | GWR SG044 | 2007– | DOI 10.5880/igets.bh.l1.001; AG/SG inter‑comparison reference for Germany |
| Wettzell (WE) | CD029/CD030/iGrav006 | 1998– | DOI 10.5880/igets.we.l1.001 and 10.5880/igets.we.gfz.l1.001; **co‑location with Freier 2016 GAIN campaigns** |
| Onsala (OS) | OSG 054 | 2009– | DOI 10.5880/igets.os.l1.001; **co‑location with Freier 2016 GAIN campaigns** |
| Strasbourg (ST) | C026 / iOSG23 | 1996– | DOI 10.5880/igets.st.l1.001 |
| Larzac (LA) | iGrav#002 | 2011– | DOI 10.5880/igets.la.l1.001; **co‑located with Ménoret 2018 AQG‑A01 evaluation** (verbatim from the Larzac LA DOI page: "Research activities are aimed at both validate gravimeters (eg Gphone in Fores et al., 2019 or AQG-A in Menoret et al., 2018)") |
| Membach (MB) | C021 | 1995–2024 | DOI 10.5880/igets.mb.l1.001; longest continuous SG record |
| Wuhan | OSG 065 | 2013– | Co‑location with the **Hu/HUST cold‑atom group** |
| Sutherland (SU), Bad Homburg, Potsdam, Apache Point, ~40 more | various | — | full table at https://isdc.gfz.de/igets-data-base/ |

Boy et al. (2020) verbatim:
> "IGETS collects, archives and distributes long time series from geodynamic sensor, in particular superconducting gravimeter data currently from more than 40 stations and 60 different sensors."

Luan et al. (2025) GJI 243, ggaf206 (DOI 10.1093/gji/ggaf206) verbatim status snapshot:
> "59 SG time-series from 42 worldwide stations for the interval July 1997–February 2024 (status September 2024)."

### 1.7 Relevance to `qgrav`
**Direct.** IGETS is the highest‑quality public benchmark for the *output* of an absolute/atom gravimeter at ≥1‑minute timescales: tides (M2 ~ 10⁻⁶ m/s² range), polar motion, ocean‑tide loading, atmospheric pressure loading, and local hydrology. The three regression targets all sit next to IGETS SGs (Larzac iGrav#002 → Ménoret 2018; Wettzell CD029 and Onsala OSG054 → Freier 2016; Wuhan OSG 065 → Hu 2013 lab). Recommended use: load monthly `.ggp` files via a small Python reader, decimate to 1 min if needed, and compare residual time series after solid‑earth‑tide and atmospheric correction.

---

## 2. GRACE‑FO Level‑2 Monthly Gravity Fields

**TL;DR.** GRACE‑FO Level‑2 monthly spherical‑harmonic geopotential coefficients (GSM, plus GAA/GAB/GAC/GAD background) are openly distributed by NASA PO.DAAC (Earthdata) and GFZ ISDC, produced independently by CSR, JPL and GFZ; current release is **RL06.3** for JPL and GFZ. The native product is spherical‑harmonic coefficients up to degree/order 96; per the NASA GRACE Tellus FAQ (grace.jpl.nasa.gov/about/faq/), "The sensitivity of the measurement is such that we can resolve approx. 1 – 2 cm of water‑height changes across spatial scales of 300 km, which is the smallest 'native' spatial scale at which we can resolve a mass change signal." Cadence: monthly. **For a point absolute gravimeter, GRACE‑FO is *not* a point‑validation source** — it constrains regional mass change (basin‑averaged terrestrial water storage, ice mass, ocean bottom pressure), but it can validate the large‑spatial‑scale, slowly varying component of `qgrav` residuals after tides.

### 2.1 Primary product (NASA PO.DAAC)
- **GRACE‑FO Level‑2 Monthly Geopotential Spherical Harmonics JPL RL06.0** — landing page https://podaac.jpl.nasa.gov/dataset/GRACEFO_L2_JPL_MONTHLY_0060
- **GRACE‑FO L2 Monthly JPL RL06.3** — DOI **10.5067/GFL20-MJ063** (current as of 2025)
- **GRACE‑FO L2 Monthly GFZ RL06.3** — landing https://podaac.jpl.nasa.gov/dataset/GRACEFO_L2_GFZ_MONTHLY_0060 ; release notes https://isdc-data.gfz.de/grace-fo/DOCUMENTS/RELEASE_NOTES/GRACE-FO_GFZ_L2_Release_Notes_for_RL06.3.pdf
- **PO.DAAC dataset description (verbatim):** "This dataset contains estimates of the total month-by-month geopotential of the Earth, derived from the Gravity Recovery and Climate Experiment Follow-On (GRACE-FO) mission measurements... The data are provided in spherical harmonic coefficients, averaged over approximately a month."

### 2.2 Products & file naming (GFZ release notes RL06.1/RL06.3, verbatim)
> "GSM-2_YYYYDDD-YYYYDDD_GRFO_GFZOP_BC01_0601 ... Unconstrained monthly gravity field solution estimated up to degree/order 96."
> "GAA-2 ... The average of the 'atm' coefficients from the AOD1B RL06 product up to degree/order 180 over the same time span as the GSM products."
> "GAB-2 ... The average of the 'ocn' coefficients ..."
> "GAC-2 ... The average of the 'glo' coefficients ... used as background model during Level-2 processing."
> "GAD-2 ... [ocean bottom pressure equivalent]"

### 2.3 Access methods
- NASA Earthdata (login required for downloads, account free): https://podaac.jpl.nasa.gov + Earthdata `cmr` API, `podaac-data-subscriber`, and S3 buckets on AWS `us-west-2`.
- GFZ ISDC FTP: `ftp://isdcftp.gfz-potsdam.de/grace-fo/Level-2/` (verbatim from RL06.1 release notes: "available here: ftp://isdcftp.gfz-potsdam.de/grace-fo/Level-2/GFZ/RL06.1_NEQs_SINEX/"); HTTPS mirror `https://isdc-data.gfz.de/grace-fo/Level-2/`.
- **ICGEM** (http://icgem.gfz-potsdam.de/) provides a uniform `.gfc` (spherical harmonic coefficients) format with online evaluation of geoid, equivalent water height, and gravity anomalies on user grids — cite Ince et al. (2019) DOI **10.5194/essd-11-647-2019**, verbatim:
> "The International Centre for Global Earth Models (ICGEM, http://icgem.gfz-potsdam.de/...) hosted at the GFZ German Research Centre for Geosciences (GFZ) is one of the five services coordinated by the International Gravity Field Service (IGFS) of the International Association of Geodesy (IAG). The goal of the ICGEM service is to provide the scientific community with a state-of-the-art archive of static and temporal global gravity field models of the Earth, and develop and operate interactive calculation and visualization services of gravity field functionals on user-defined grids or at a list of particular points via its website."
- **GravIS** (https://gravis.gfz.de/) provides user‑friendly Level‑3 (gridded mass anomaly) products. Reference: Dahle et al. (2025) ESSD DOI **10.5194/essd-17-611-2025**.

### 2.4 Units, spatial/temporal resolution
- Native L2: dimensionless Stokes coefficients C̄ₗₘ, S̄ₗₘ to degree 96.
- Practical spatial resolution (NASA GRACE Tellus FAQ, verbatim): "approx. 1 – 2 cm of water‑height changes across spatial scales of 300 km, which is the smallest 'native' spatial scale at which we can resolve a mass change signal."
- Derived: equivalent water height (m or mm w.e.), geoid height (m or mm), gravity anomaly (mGal or m/s²). Conversion: 1 mGal = 1 × 10⁻⁵ m/s² = 10⁴ nm/s². Typical month‑to‑month gravity changes at basin scale are sub‑µGal (sub‑10 nm/s²) — well below SG noise floor of ~1 nm/s² but at the spatial scale (≥300 km) of GRACE‑FO.
- Temporal: nominally one solution per calendar month; gaps during short‑repeat orbits.

### 2.5 Relevance to `qgrav` — honest caveats
**Indirect.** A ground atom gravimeter at a single point measures local *g* with all wavelengths (mountain, terrain, ground water within metres). GRACE‑FO returns the **regionally averaged** time‑variable component over ≥300 km footprints. They agree only at long‑wavelength, long‑timescale common modes (continental hydrology, large ice sheets, polar motion). Do **not** treat GRACE‑FO as a point reference; use it (or its GravIS Level‑3 gridded mass anomalies) to model and subtract the expected hydrological signal at the atom gravimeter site, as in Freier 2016 cross‑validation campaigns at Wettzell.

---

## 3. Public Cold‑Atom / Atom‑Interferometer Gravimeter Datasets

**TL;DR.** **Very little raw or processed atom‑interferometer gravimeter data is openly published.** The three regression‑target papers (Freier 2016, Hu 2013, Ménoret 2018) do **not** release the underlying time series. A handful of recent LNE‑SYRTE / Observatoire de Paris papers (Janvier 2022; Gautier 2025; Sidorenkov 2024) have deposited raw Raman fringe data on Zenodo. The BIPM Key‑Comparison reports (CCM.G‑K1, CCM.G‑K2, CCM.G‑K2.2017) publish summary g‑values and uncertainties only.

### 3.1 What exists publicly
- **Sidorenkov / Gautier (LNE‑SYRTE) 2024**, *Nature Communications* "Atom interferometry at arbitrary orientations and rotation rates", DOI **10.1038/s41467-024-50804-0**. Raw data on Zenodo: **https://doi.org/10.5281/zenodo.11543715**. Verbatim README:
  > "Data are sorted by figures and by date (format YYYYMMDD). Data corresponding to the interference fringes (population ratios, phases) are in folders called 'Raman'. Signals of the classical sensors (accelerometers and gyroscopes) are in folders called 'Streaming'."
  This is the **only publicly available raw Raman‑fringe atom‑interferometer dataset** identified.
- **Gautier et al. 2024**, *Science Advances* "Quantum sensing of acceleration and rotation by interfering magnetically launched atoms", DOI **10.1126/sciadv.adq4498**. Raw data: **https://zenodo.org/records/11241234** ("Raw data are available at the following repository").
- **BIPM CCM Key Comparisons** (https://www.bipm.org/en/committees/cc/ccm/key-comparisons):
  - CCM.G‑K1 (ICAG2009) — final report in KCDB; verbatim from abstract: "the data (raw absolute gravity measurements and their uncertainties) submitted by the participants ... are presented including the degrees of equivalence (DoE) of the absolute gravimeters and the key comparison reference values (KCRVs)."
  - CCM.G‑K2 (2013) — Published 2015.
  - CCM.G‑K2.2017 — Published 2020, full PDF: https://www.bipm.org/documents/20126/48150829/CCM.G-K2.2017.pdf — provides per‑instrument g‑values at site reference heights, expanded uncertainties, and DoE. Verbatim: "the FG5#228 showed a degree of equivalence of 3 nm s⁻² with the 12 other absolute gravimeters and 55 nm s⁻² uncertainty within 95 % confidence."
- **Freier 2016 (J. Phys. Conf. Ser. 723 012050)** "Mobile quantum gravity sensor with unprecedented stability" reports the GAIN figures used as a regression target: "an uncertainty of 39 nm/s², a long-term stability of 0.5 nm/s² and a short-term noise of 96 nm s⁻²Hz⁻¹/² " (paraphrased by Schilling et al. 2025 *J. Geod.* DOI 10.1007/s00190-025-01995-x). **Underlying time series are not in any public repository identified.**
- **Hu, Z.-K. et al. (2013) Phys. Rev. A 88, 043610**, DOI **10.1103/PhysRevA.88.043610**. Reports 4.2 µGal/√Hz = 42 nm/s²/√Hz short‑term sensitivity. **No public raw data**.
- **Ménoret, V. et al. (2018)** *Sci. Rep.* 8, 12300, DOI **10.1038/s41598-018-30608-1**, arXiv **1809.04908**. AQG‑A01 evaluation; comparison with FG5#228 and iGrav#002 at Larzac. **No raw data deposited** (paper has no Data Availability link to a repository for the fringe data; only summary plots).
- **Cooke et al. (2021)** *Geosci. Instrum. Method. Data Syst.* 10, 65–79, DOI **10.5194/gi-10-65-2021** — AQG‑B01 evaluation at Larzac; cites Larzac iGrav#002 (IGETS DOI 10.5880/igets.la.l1.001) and FG5#228 — again, no raw fringe data deposited.

### 3.2 What clearly does NOT exist publicly (May 2026)
- No public raw photodiode trace, MOT‑loading trace, or Raman‑pulse population fraction time series from Freier 2016 / Hauth 2013 (GAIN, Humboldt Berlin).
- No public raw data from Hu 2013 / HUST‑QG (Huazhong University of Science and Technology, Wuhan).
- No public raw data from the Muquans/iXblue/Exail AQG‑A01 nor AQG‑B01 used in Ménoret 2018 and Cooke 2021.
- No public dataset from Stanford (Kasevich), AOSense, NIST, or PTB cold‑atom gravimeters.
- ICAG / CCM.G key comparisons publish *adjusted g‑values and uncertainties*, not the underlying drop‑level data.

### 3.3 Relevance to `qgrav`
**Critical caveat:** for the three named regression targets you can validate `qgrav` only against the **published summary statistics** (Allan deviation curves, sensitivities, biases) reproduced from the papers, not against time series. Recommended secondary‑target strategy: use the Sidorenkov‑Gautier 2024 Zenodo dataset (https://doi.org/10.5281/zenodo.11543715) as the canonical open raw‑fringe benchmark for fringe‑demodulation and inertial‑hybrid algorithms, even though it is a rotation/acceleration sensor rather than a strict vertical gravimeter.

---

## 4. PhysioNet‑Style Curated Benchmark for Gravimetry

**TL;DR.** **No direct analog of PhysioNet exists for gravimetry or atom interferometry.** There is no openly licensed, versioned, challenge‑driven benchmark repository of gravimeter time series. The closest functional analogs — none of which combine all four PhysioNet features (curation, versioning, open licence, paired challenges) — are IGETS (curated, partial DOIs, registration‑gated), EarthScope/IRIS (curated seismic, CoreTrustSeal), ORFEUS/EIDA, PANGAEA, Zenodo communities, and the BIPM CCM Key Comparison Database.

### 4.1 PhysioNet reference (for contrast)
Goldberger et al. (2000) *Circulation* 101(23): e215–e220 (RRID:SCR_007345). Verbatim from physionet.org: "PhysioNet provides free web access to over 50 collections of recorded physiologic signals and time series ... PhysioNet's annual open engineering challenges stimulate rapid progress on unsolved or poorly solved questions of basic or clinical interest, by focusing attention on achievable solutions that can be evaluated and compared objectively using freely available reference data."

### 4.2 Closest analogs for gravimetry/geophysics

| Repository | What it covers | Curation | Open licence | Challenges? |
|---|---|---|---|---|
| **IGETS** (GFZ) | SG gravity, pressure (Levels 1/2/3) | Yes (Voigt 2016) | CC BY 4.0 (per‑station DOI pages) | No |
| **EarthScope/IRIS DMC** (now NSF SAGE) | Seismic, strain, gravimeter event data | CoreTrustSeal certified | Open access waveform | No formal challenges; PIs run "Quakes" workshops |
| **ORFEUS / EIDA** | European seismic waveforms | FDSN‑certified | Open via FDSN web services | No |
| **PANGAEA** (AWI/MARUM) | Georeferenced earth‑system data | CoreTrustSeal, FAIR | Open access, DOI per dataset | No |
| **Zenodo communities** (`zenodo.org/communities`) | Ad hoc deposits (e.g. SYRTE Raman fringes) | None | CC0/CC BY | No |
| **BIPM KCDB** (`kcdb.bipm.org`) | NMI key‑comparison results incl. CCM.G | Curated by BIPM | Open final reports | No (single‑shot comparisons, not iterative challenges) |
| **GFZ Data Services / ICGEM** | Static & temporal gravity models | DOI‑assigned | Open | No |

### 4.3 Recommendation
For `qgrav`, **state explicitly in the project README that no PhysioNet equivalent exists** and define your own internal benchmark suite by combining (i) IGETS LA/WE/OS L2 segments around the Freier 2016 and Ménoret 2018 campaigns, (ii) co‑located IRIS/EarthScope BHZ/LHZ/VHZ data for vibration injection (§5), (iii) the Sidorenkov‑Gautier Zenodo fringe dataset for atom‑interferometer demodulation tests (§3), and (iv) published Allan‑deviation curves digitised from Freier 2016, Hu 2013, Ménoret 2018 as regression targets. Publish that bundle as a Zenodo deposit with a DOI to *create* the missing analog.

---

## 5. Public Seismic / Ground‑Noise Data (IRIS / EarthScope / ORFEUS / USGS)

**TL;DR.** Vibration / Newtonian‑noise benchmarks for `qgrav` should pull broadband seismic data via the **FDSN web services** (`fdsnws-dataselect`, `fdsnws-station`, `fdsnws-event`) from EarthScope (formerly IRIS DMC) and ORFEUS/EIDA, using ObsPy's `Client("IRIS"|"EARTHSCOPE"|...)` interface. The relevant noise band for atom‑gravimeter vibration rejection comprises the **primary microseism (~0.07 Hz peak) and secondary microseism (~0.14 Hz peak)** — per Teixidó et al. (2002) *Geophys. J. Int.* 149(3):589, citing Aki & Richards (1980): "two maxima of the power spectrum, at about 0.07 Hz, the primary peak, and 0.14 Hz, the secondary peak, are typical features of almost all the recordings at seismic stations." Cultural noise dominates above ~1 Hz. Reference noise model: **Peterson (1993) NLNM/NHNM**, DOI **10.3133/ofr93322**.

### 5.1 Peterson 1993 (canonical reference)
Verbatim USGS catalog entry: "Peterson, J.R., 1993, Observations and modeling of seismic background noise: U.S. Geological Survey Open-File Report 93-322, 94 p., https://doi.org/10.3133/ofr93322." Landing page: https://pubs.usgs.gov/publication/ofr93322 . The report defines the **New Low Noise Model (NLNM)** and **New High Noise Model (NHNM)** as PSDs of ground acceleration in dB referenced to (m/s²)²/Hz, spanning 0.1 mHz to 10 Hz.

### 5.2 FDSN web service APIs
ObsPy 1.5.0 (current release March 13, 2026 per PyPI / Zenodo DOI **10.5281/zenodo.19005357**; documentation at https://docs.obspy.org/) verbatim example:
> "client = Client('IRIS') ... FDSN Webservice Client (base url: http://service.iris.edu) Available Services: 'dataselect' (v...), 'event' (v...), 'station' (v...), 'available_event_catalogs', 'available_event_contributors' ..."

The three FDSN service endpoints:
- `fdsnws-dataselect` — miniSEED waveform retrieval. Example: `client.get_waveforms("IU", "ANMO", "00", "LHZ", t1, t2)`.
- `fdsnws-station` — StationXML inventories with response info. `client.get_stations(...)`.
- `fdsnws-event` — earthquake catalog. `client.get_events(...)`.

EarthScope service base URL: https://service.iris.edu (post‑2023 IRIS/UNAVCO merger). ORFEUS Federator: https://www.orfeus-eu.org/eidaws/routing/1/.

Verbatim from EarthScope (https://ds.iris.edu/ds/nodes/dmc/data/types/waveform-data/):
> "The EarthScope DMC archives waveform (time-series) data from stations around the world. ... SEED is an international standard format for the exchange of digital seismological data."

Verbatim from ORFEUS (https://www.orfeus-eu.org/data/eida/webservices/):
> "ORFEUS EIDA implements the following webservices to provide standardized and open access to data. ... FDSNWS-Dataselect ... FDSNWS-Station ... FDSNWS-Availability ... EIDAWS-Routing ... EIDAWS-WFCatalog."

### 5.3 Relevant channels
SEED channel naming (band code + instrument code + orientation):
- `BHZ` — broadband, high‑gain, vertical (sampling 10–80 Hz)
- `LHZ` — long‑period, high‑gain, vertical (1 Hz)
- `VHZ` — very long‑period (0.1 Hz)
- `HHZ` — high broadband (≥80 Hz) — best for vibration injection above the microseism

For Newtonian / vibration noise close to an atom gravimeter, prefer co‑located broadband (BHZ/HHZ) plus a tilt/strain channel if available.

### 5.4 Microseism band (peer‑reviewed verbatim)
From Tanimoto et al. (2023) Prog. Earth Planet. Sci., DOI **10.1186/s40645-023-00587-7** (verbatim):
> "The largest peak in Fig. 1 is the secondary microseism whose frequency range is approximately between 0.1 and 0.4 Hz. The small peak at about 0.05–0.07 Hz that shows up on the lower frequency side (left) of this peak is the primary microseism."

From PMC5713174 (verbatim): "primary microseisms (0.02–0.1 Hz), and secondary microseisms (0.1–1 Hz)".

Disagreement note: precise band edges vary by source (0.05–0.1 vs 0.02–0.1 Hz for primary; 0.1–0.4 vs 0.1–1 Hz for secondary). Use 0.05–0.5 Hz as the safe combined‑microseism band for `qgrav` vibration injection.

### 5.5 Units
Acceleration PSD in (m/s²)²/Hz, or dB referenced thereto (Peterson convention). Conversion: 0 dB ref 1 (m/s²)²/Hz = 1 (m/s²)²/Hz; NLNM minimum around –184 dB ≈ 4 × 10⁻¹⁹ (m/s²)²/Hz at ~100 s period.

### 5.6 Relevance to `qgrav`
**Direct.** Inject real BHZ traces from a station co‑located with each regression‑target site (Wettzell `IU.WTZ` for GAIN, Wuhan `IC.ENH` regional for HUST, Larzac region for AQG) as ground‑noise input to the bench's vibration‑isolation simulation. Compare measured short‑term sensitivity against an `eff = T² · k_eff · σ_a` shot‑noise‑plus‑vibration estimate using the PSD computed from those traces.

---

## 6. Public Photodiode / I‑Q / Atom‑Interferometer Fringe Data

**TL;DR.** **There is no curated public repository of atom‑interferometer photodiode I/Q signals or raw fringe time series**. The single ad hoc deposit identified is the SYRTE Zenodo record 11543715 (Raman population ratios, accelerometer/gyroscope streams, not photodiode‑level). The closest substitute analogs are LIGO open seismic noise data (gravitational‑wave‑detector context) and the SYRTE Zenodo deposits. Treat this as a known gap that `qgrav` should fill by publishing its own synthetic fringe benchmarks.

### 6.1 What exists
- **Zenodo 10.5281/zenodo.11543715** — Sidorenkov, R.; et al. (LNE‑SYRTE) "Atom interferometry at arbitrary orientations and rotation rates" (linked to *Nat. Commun.* 2024 paper, DOI 10.1038/s41467-024-50804-0). Contents (verbatim): "Data corresponding to the interference fringes (population ratios, phases) are in folders called 'Raman'. Signals of the classical sensors (accelerometers and gyroscopes) are in folders called 'Streaming'." **This is at the population‑fraction level (i.e. post‑imaging), not raw photodiode counts.**
- **Zenodo records/11241234** — Gautier et al. (2024) raw data for *Sci. Adv.* "Quantum sensing of acceleration and rotation by interfering magnetically launched atoms".
- **LIGO Open Science Center / GWOSC** (gwosc.org) — seismic and auxiliary channel data for the LIGO interferometers (optical, not matter‑wave, but I/Q‑level photodetector signals with documented response).

### 6.2 What does NOT exist
- No raw photodiode trace from any cold‑atom gravimeter (Freier 2016, Hu 2013, Ménoret 2018, Bidel et al., Stanford, AOSense).
- No raw MOT‑fluorescence camera frames published as a benchmark dataset.
- No open I/Q demodulated signals from Raman lock loops.
- No challenge competitions in this space (cf. §4).

### 6.3 Recommendation
1. Generate `qgrav` synthetic photodiode I/Q traces with documented noise models (shot noise, Raman intensity noise, RIN, vibration mirror phase noise) and deposit a versioned bundle on Zenodo with a CC BY 4.0 licence and DOI — this *creates* the missing benchmark.
2. Where real data is required, use the SYRTE Zenodo deposit at the population‑ratio level and treat raw photodiode‑level validation as a synthetic‑only target.
3. For inertial‑noise injection into the simulated photodiode signal, draw from the GWOSC auxiliary seismic channels or EarthScope BHZ traces (§5).

---

## Cross‑cutting recommendations for `qgrav` validation

1. **Bench‑output validation:** download monthly IGETS L2 `.ggp` files for Wettzell (`we`), Onsala (`os`), Larzac (`la`), and Wuhan; build a Python reader (~50 lines) following the 7‑line header and `(i4,2i2,1x,3i2,2f10.6)` data format of GGP V5; compare `qgrav` residuals against L2 corrected gravity (nm/s²) and L3 residuals (geophysical‑correction‑applied).
2. **Long‑wavelength sanity check:** subtract a GravIS Level‑3 hydrology mass‑anomaly time series (gridded equivalent water height at the gravimeter pixel) from `qgrav` residuals and verify residual variance reduction; do **not** demand point agreement with GRACE‑FO.
3. **Vibration noise:** stream BHZ traces (10–40 Hz, miniSEED) through ObsPy 1.5.0 (`Client("EARTHSCOPE")`) from EarthScope `IU.WTZ`, ORFEUS for European sites; inject these as ground‑noise driving the simulated mirror.
4. **Regression targets:** since Freier 2016, Hu 2013, Ménoret 2018 raw data are unavailable, regress against the **published summary metrics** (short‑term sensitivity, Allan deviation slopes, final uncertainty) — store those as YAML "spec" files in `tests/regression/`, not as time series.
5. **Open the benchmark:** publish `qgrav`‑generated synthetic fringe + I/Q traces and a small replay of IGETS L2 segments (where the per‑station CC BY 4.0 licence permits redistribution; otherwise link, do not mirror) on Zenodo with a DOI, to establish the PhysioNet‑style resource that does not currently exist for atom‑interferometric gravimetry.

## Caveats & disagreements between sources

- **Microseism band edges differ** between Tanimoto 2023 (0.1–0.4 Hz secondary; 0.05–0.07 Hz primary), PMC5713174 (0.1–1 Hz secondary; 0.02–0.1 Hz primary) and the canonical Aki & Richards spectral peaks at 0.07 / 0.14 Hz quoted by Teixidó et al. (2002). `qgrav` should default to a combined 0.05–0.5 Hz band with peaks at 0.07 and 0.14 Hz and document the choice.
- **IGETS station count** in different sources: IAG GGOS IGETS page (2025‑09‑22) — "47 stations"; Boy et al. 2020 — ">40 stations and 60 different sensors"; Luan et al. 2025 — "59 SG time-series from 42 worldwide stations (status September 2024)". This reflects genuine growth and different counting conventions (stations vs sensors vs active series); cite the live ISDC table for the up‑to‑date number.
- **Hu 2013 sensitivity reporting:** PRA 88 043610 reports 4.2 µGal/√Hz = 42 nm/s²/√Hz (corrected from earlier "best reported value" by factor 2). One Chinese‑language secondary source rounds this; cite the PRA original.
- **GRACE‑FO release version drift:** PO.DAAC currently shows JPL RL06.0, RL06.1, and RL06.3 with the latter (DOI 10.5067/GFL20-MJ063) as current; older versions are marked "Please Note: This dataset is retired".
- **Atom‑gravimeter raw data:** the absence of public raw fringe data for the three regression targets is a hard limitation. Treat any "benchmark" against Freier/Hu/Ménoret as a regression against *published numbers*, never against series.
- **No PhysioNet analog exists** — stated explicitly; do not invent one.