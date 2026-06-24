# ROS2 Pipeline Profiler — DDS Benchmark

## Prerequisites

```bash
sudo apt install ros-jazzy-rmw-cyclonedds-cpp
```

## Usage

```bash
# Default: Fast DDS + Cyclone DDS, 3 trials each, 30s per trial
python3 benchmark/run_benchmark.py

# Customize
python3 benchmark/run_benchmark.py \
    --rmw-list rmw_fastrtps_cpp,rmw_cyclonedds_cpp \
    --trials 5 \
    --duration 60 \
    --output-dir my_benchmark
```

## Output

```
benchmark_results/
├── compare_report.html      ← Main output: side-by-side CDFs, box plots, bar charts, summary table
├── rmw_fastrtps_cpp/
│   ├── run_1/
│   │   ├── profiler_*.csv
│   │   ├── report.html
│   │   └── results.json
│   ├── run_2/
│   └── run_3/
└── rmw_cyclonedds_cpp/
    ├── run_1/
    ├── run_2/
    └── run_3/
```

## Interpreting the comparison report

- **CDF curves**: higher = more messages completed within that latency. The steeper the curve, the more predictable the latency.
- **Box plots**: wider = more jitter. If one RMW has a longer upper whisker, it has worse tail latency.
- **Bar charts**: direct p50/p90/p99 comparison per metric. Green-highlighted cells in the table are the best value for that row.
