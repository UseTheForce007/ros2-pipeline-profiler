# Experiment 1: DDS Comparison

## Setup
- **Pipeline:** 640×480 mono8 Image @ 15Hz → Gaussian blur → control node
- **Configs:** Fast DDS vs Cyclone DDS, both reliable depth 10
- **Duration:** 2 trials × 20s each
- **Runs:** `../../benchmark_results/rmw_fastrtps_cpp/reliable_depth_10/` and `rmw_cyclonedds_cpp/reliable_depth_10/`

## Expected behavior
Same CPU, same code — only the DDS serialization/transport layer differs.
Differences should only appear on the `/image` topic (307KB payloads).

## Observed behavior

| Metric | Fast DDS | Cyclone DDS | Delta |
|---|---|---|---|
| transport_/image p50 | 0.30 ms | 0.29 ms | ~identical |
| transport_/image p90 | 0.46 ms | 0.45 ms | ~identical |
| transport_/image p99 | **1.01 ms** | **0.71 ms** | **30% better** |
| transport_/processed p99 | 0.62 ms | 0.68 ms | no meaningful diff |
| process_processing_node | 4.2 ms | 4.1 ms | identical (same code) |
| e2e | 5.4 ms | 5.7 ms | processing-dominant |

## Root cause
Cyclone DDS handles large-payload serialization and delivery more predictably
under CPU contention. The tight CDF curve means fewer "slow messages" at the tail.

For small messages (8-byte Float64 on `/processed`), DDS implementation doesn't matter.

## Portfolio takeaway
> Chosing Cyclone DDS over Fast DDS improved p99 transport latency by 30%
> for 307KB image payloads, with identical median performance.
