# Benchmark Results

This directory documents all performance experiments run on the ROS2 Pipeline Profiler.
Each subdirectory contains one experiment with findings, raw data, and HTML reports.

## Experiments

| # | Experiment | Status | Key Finding |
|---|---|---|---|
| 1 | [DDS Comparison](01_dds_comparison/) | ✅ Complete | Cyclone DDS has 30% better transport p99 for large payloads |
| 2 | [QoS Heatmap](02_qos_heatmap/) | ⬜ Pending | Vary reliability × depth across both RMWs |
| 3 | [Bottleneck Diagnosis](03_bottleneck_diagnosis/) | ✅ Complete | 3-pass blur at 30Hz causes 146 drops, 313ms queue |
| 4 | [Threading Fix](04_threading_fix/) | ⬜ Pending | Parallelize blur to eliminate the bottleneck |

## Summary

[View the consolidated summary table](SUMMARY.md)
