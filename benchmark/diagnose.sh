#!/usr/bin/env bash
# Diagnose the bottleneck pipeline
# Run this after running the demo pipeline with the bottleneck (640x480, 30Hz, 3-pass blur)

set -e

cd /home/darth-yoseph/ros2_personal_ws

echo "=== Step 1: Install dependencies ==="
pip install --break-system-packages -e src/ros2-pipeline-profiler/python 2>&1 | tail -3
pip install --break-system-packages plotly pandas 2>&1 | tail -3

echo ""
echo "=== Step 2: Analyze the CSVs ==="
python3 -m ros2_pipeline_profiler_analyzer.cli analyze \
    --log-dir . \
    --output drops_report.html \
    --rmw-label "bottleneck" \
    --save-results drops_results.json \
    --pipeline-name "640x480 @ 30Hz - 3-pass blur (bottleneck)"

echo ""
echo "=== Done ==="
echo "Open drops_report.html in a browser to see the full report."
