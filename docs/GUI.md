# GUI Guide

## Main tabs

### Experiment
Quick controls for:
- bench type
- Allan backend
- data type
- PSD method
- source paths
- AISim parameters

### Data Browser
Use this when working with superconducting gravimeter datasets.
It can:
- scan a directory or ZIP archive,
- list station codes,
- preview a selected station,
- show gap statistics,
- create a config for the selected station.

### Config Editor
Raw YAML view for precise reproducibility.

### Results & Visuals
Interactive plots and artifact access.

### Guides
Embedded documentation.

## Recommended GUI workflow

1. Open **Data Browser** and scan the dataset.
2. Select one station and preview it.
3. Click **Create config**.
4. Go to **Experiment** and verify stats settings.
5. Run the pipeline.
6. Inspect the report in **Results & Visuals**.


## AISim study presets

The GUI toolbar now includes quick-load buttons for:

- **AISim Rabi**
- **AISim Phase**
- **AISim Gravity**
- **AISim Vibration**

These load the bundled YAML examples for the four available AISim study modes. The quick controls panel also exposes the most important study-level parameters:

- model selection
- atom count
- sweep point count
- interferometer time `T`
- gravity center/span
- vibration frequency and maximum amplitude

For advanced parameters such as explicit phase ranges or phase bias, edit the YAML directly in the Config Editor tab.
