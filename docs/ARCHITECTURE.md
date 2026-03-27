# Architecture

## Layered design

### 1. Simulation layer
- `src/qgrav/sim_ai/simple_ai.py`
- `src/qgrav/sim_ai/aisim_adapter.py`

### 2. Bench layer
- `src/qgrav/bench_ifo/virtual_ifo.py`
- `src/qgrav/bench_ifo/real_ifo.py`

### 3. Estimation layer
- `src/qgrav/algorithms/`

### 4. Metrics layer
- `src/qgrav/metrics/`

### 5. Orchestration + reporting
- `src/qgrav/pipeline.py`
- `src/qgrav/reporting/report.py`
- `src/qgrav/gui.py`
- `src/qgrav/visuals.py`
