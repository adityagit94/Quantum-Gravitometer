#!/usr/bin/env bash
set -euo pipefail

qgrav run --config configs/example.yaml
qgrav run --config configs/example_custom_allan.yaml

echo "Generated both AllanTools and custom-backend example runs."
