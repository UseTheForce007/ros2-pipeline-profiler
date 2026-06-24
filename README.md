# ROS2 Pipeline Profiler

Per-message latency tracing for ROS2 pipelines. Instruments any ROS2 node with
templated `ProfilerPublisher<T>` / `ProfilerSubscriber<T>` wrappers, logs every
publish/receive/process event to CSV with nanosecond timestamps, and produces
interactive HTML reports with waterfall charts, CDF curves, histograms, and box plots.

Designed for diagnosing bottlenecks, comparing DDS implementations, and tuning QoS
in real-time robotics systems.

---

## Pipeline

```
sensor_node ──/image──► processing_node ──/processed──► control_node
(320×240 mono8   |   (separable 5×5       (computes e2e
 @ 15 Hz)        |    Gaussian blur)       latency)
                 ▼
          ProfilerEnvelope wraps every message with:
          message_id, parent_message_id, timestamps,
          source_node_id, hop_count, serialized payload
```

Each node writes `profiler_<node>_<timestamp>.csv` with event logs.
The Python analyzer reads all CSVs, reconstructs message flow chains,
and generates an interactive HTML report.

---

## Quick Start

### Build

```bash
cd ~/ros2_personal_ws
colcon build --packages-select ros2_pipeline_profiler
source install/setup.bash
```

### Run the pipeline

```bash
ros2 launch ros2_pipeline_profiler demo.launch.py
```

Let it run for 10-30 seconds, then Ctrl-C. CSV files appear in the working directory.
Optional QoS parameters:

```bash
ros2 launch ros2_pipeline_profiler demo.launch.py reliability:=best_effort depth:=100
```

### Analyze

```bash
pip install --break-system-packages plotly pandas
pip install --break-system-packages -e python/

ros2-pipeline-profiler-analyzer analyze \
    --log-dir . \
    --output report.html \
    --rmw-label fastrtps \
    --save-results results.json
```

Open `report.html` in a browser.

---

## DDS Comparison Benchmark

Compares Fast DDS and Cyclone DDS on the same pipeline with identical payloads.

### Install Cyclone DDS

```bash
sudo apt install ros-jazzy-rmw-cyclonedds-cpp
```

### Run benchmark

```bash
cd src/ros2-pipeline-profiler
python3 benchmark/run_benchmark.py --duration 20 --trials 2
```

Iterates over all RMW × QoS × depth combinations (configurable via flags),
collects results into `benchmark_results/`, and produces:

| Report | Description |
|---|---|
| `compare_report.html` | Side-by-side CDFs, box plots, bar charts |
| `qos_heatmap.html` | RMW × QoS heatmap with p99 values |

### Flags

```bash
python3 benchmark/run_benchmark.py \
    --rmw-list rmw_fastrtps_cpp,rmw_cyclonedds_cpp \
    --qos-list reliable,best_effort \
    --depth-list 10,100 \
    --trials 3 \
    --duration 30 \
    --output-dir benchmark_results
```

### Key Findings

- **Cyclone DDS ~30% better p99 transport latency on large payloads** (307KB images)
  vs Fast DDS (0.71ms vs 1.01ms), while median latency was identical.
- **Small messages show no RMW difference** — DDS implementation only matters
  when payloads stress serialization and memory management.
- **BestEffort QoS reduces transport latency 10-20%** compared to Reliable,
  at the cost of potential message drops under load.
- See `benchmark_results/findings.md` for the full analysis.

---

## CLI Reference

```bash
# Single analysis
ros2-pipeline-profiler-analyzer analyze \
    --log-dir <path> \
    --output report.html \
    --rmw-label <name> \
    --save-results results.json \
    --pipeline-name "My Pipeline"

# Compare multiple results
ros2-pipeline-profiler-analyzer compare \
    --results r1.json r2.json r3.json \
    --labels "Fast DDS trial 1,Fast DDS trial 2,Cyclone DDS trial 1" \
    --output compare.html

# Generate QoS heatmap
ros2-pipeline-profiler-analyzer heatmap \
    --results-dir benchmark_results \
    --output qos_heatmap.html
```

---

## Project Structure

```
msg/ProfilerEnvelope.msg      # Custom ROS2 message with tracing fields
include/ros2_pipeline_profiler/
  profiler_common.hpp         # MessageIdFactory, NodeRegistry, Metadata, EventType
  event_logger.hpp            # Thread-safe CSV writer with background flusher
  profiler_publisher.hpp      # ProfilerPublisher<T> template
  profiler_subscriber.hpp     # ProfilerSubscriber<T> template
src/
  event_logger.cpp            # EventLogger implementation
  profiler_common.cpp         # NodeRegistry implementation
  demo/
    sensor_node.cpp           # Image publisher (configurable QoS)
    processing_node.cpp       # Gaussian blur (configurable QoS)
    control_node.cpp          # End-to-end latency logging
python/ros2_pipeline_profiler_analyzer/
  reader.py                   # CSV reader
  analyzer.py                 # Latency computation, chain reconstruction
  visualizer.py               # Plotly HTML report generation
  comparator.py               # Multi-RMW comparison reports
  heatmap.py                  # RMW × QoS heatmap reports
  cli.py                      # CLI entry point
benchmark/
  run_benchmark.py            # Benchmark orchestration script
  README.md                   # Benchmark documentation
```

---

## Why This Matters in Robotics

Real-time robotics pipelines suffer from unpredictable latency. This tool makes
latency visible at every stage — publish, transport, process — enabling targeted
optimization. The DDS comparison demonstrates that middleware choice directly
affects tail latency for large payloads, which is critical for control loops
operating near their deadline.
