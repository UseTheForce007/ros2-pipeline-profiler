# Experiment 3: Bottleneck Diagnosis

## Setup
- **Pipeline:** 640×480 mono8 Image **@ 30Hz** → **3-pass** Gaussian blur → control node
- **Config:** Fast DDS, reliable depth 10
- **Duration:** 15s

## Expected behavior
Single-threaded 3-pass blur takes ~49ms. Sensor fires every 33ms.
Processing cannot keep up → DDS queue fills → messages dropped.

## Observed behavior

| Metric | Baseline (15Hz, 1-pass) | Bottleneck (30Hz, 3-pass) |
|---|---|---|
| process_processing_node p50 | ~~4.1 ms~~ | **48.9 ms** |
| transport_/image p50 | ~~0.3 ms~~ | **312.8 ms** |
| e2e p50 | ~~5 ms~~ | **362.0 ms** |
| e2e p99 | ~~6 ms~~ | **379.4 ms** |
| Messages dropped | 0 | **146** |

The transport_/image latency rising from 0.3ms to 313ms is the queue buildup —
messages sit in DDS buffers waiting for the blur to finish.

Every 3rd message is dropped (IDs 1021, 1024, 1027...), which is consistent with
~49ms processing vs ~33ms sensor interval.

## Root cause
The 3-pass separable Gaussian blur at 640×480 is CPU-bound at ~49ms per frame,
exceeding the 33ms sensor interval. The DDS queue (depth=10) fills in ~300ms,
then subsequent messages are silently dropped.

## Takeaway
> A single-threaded image processor running at 30Hz caused 146 dropped messages
> and 313ms queue buildup — nearly 10× the processing latency. The waterfall
> chart and cross-node drop detection made the bottleneck immediately visible.
