#!/usr/bin/env bash
set -euo pipefail
qgrav run --config configs/example_aisim_phase_scan.yaml
qgrav run --config configs/example_aisim_gravity_sweep.yaml
qgrav run --config configs/example_aisim_vibration_sweep.yaml
