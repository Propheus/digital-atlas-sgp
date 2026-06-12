#!/bin/bash
# Run all data_prep scripts in sequence. Expected runtime: <2 minutes total.
# Writes cache/*.parquet files under scenario_sim/cache/.
set -e
cd "$(dirname "$0")"
echo "=== scenario_sim data_prep ==="
python3 01_subzone_state.py
python3 02_centroids.py
python3 03_rail_graph.py
python3 04_travel_matrix.py
python3 05_facilities.py
echo
echo "=== cache contents ==="
ls -lh ../cache/
