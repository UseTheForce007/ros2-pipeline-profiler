# Experiment 2: QoS Heatmap

## Setup
- **Pipeline:** 640×480 mono8 Image @ 15Hz → Gaussian blur → control node
- **Configs:** Both RMWs × {reliable, best_effort} × {depth 10, 100}
- **Duration:** 2 trials × 20s each
- **Output:** `qos_heatmap.html` — heatmap grid of RMW × QoS per metric

## Expected behavior
BestEffort should reduce transport overhead. Larger depth should buffer more
messages but hide backpressure. The heatmap makes the pattern visible at a glance.

## Observed behavior
<!-- Fill in after running qos_heatmap.html -->
| Config | transport_/image p99 | drops |
|---|---|---|
| Fast DDS, reliable depth 10 | — | — |
| Fast DDS, reliable depth 100 | — | — |
| Fast DDS, best_effort depth 10 | — | — |
| Cyclone DDS, reliable depth 10 | — | — |
| Cyclone DDS, reliable depth 100 | — | — |
| Cyclone DDS, best_effort depth 10 | — | — |

## Root cause
<!-- Fill in -->

## Portfolio takeaway
<!-- Fill in -->
