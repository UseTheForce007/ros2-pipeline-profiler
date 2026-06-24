# Experiment 4: Threading Fix

## Setup
- **Pipeline:** 640×480 mono8 Image @ 30Hz → **thread-pooled** 3-pass Gaussian blur → control node
- **Config:** Fast DDS, reliable depth 10
- **Duration:** 15s

## Fix applied
Split the blur's horizontal pass across N threads. Each thread processes a
contiguous band of rows. Vertical pass similarly parallelized.
Result: ~49ms → ~15ms (below the 33ms sensor interval).

## Expected behavior
Processing completes before the next frame arrives. Queue never builds.
Zero drops. Transport latency returns to baseline (~0.3ms).

## Observed behavior
<!-- Fill in after running -->

| Metric | Before (single-threaded) | After (threaded) |
|---|---|---|
| process_processing_node p50 | 48.9 ms | — |
| transport_/image p50 | 312.8 ms | — |
| e2e p50 | 362.0 ms | — |
| e2e p99 | 379.4 ms | — |
| Drops | 146 | — |

## Root cause
<!-- Fill in -->

## Portfolio takeaway
<!-- Fill in -->
