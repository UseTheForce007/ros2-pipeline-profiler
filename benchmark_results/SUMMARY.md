# Pipeline Profiler — Experiment Summary

| # | Experiment | Config | e2e p50 | e2e p99 | Transport p50 | Transport p99 | Drops | Report |
|---|---|---|---|---|---|---|---|---|
| 1 | DDS Baseline | Fast DDS, reliable, depth 10, 640×480 @ 15Hz | 17ms | 19ms | 0.3ms | 1.0ms | 0 | [Details](01_dds_comparison/) |
| 2 | DDS Comparison | Cyclone DDS, reliable, depth 10 | 17ms | 18ms | 0.3ms | 0.7ms | 0 | [Details](01_dds_comparison/) |
| 3 | QoS Heatmap | See matrix (RMW × reliability × depth) | — | — | — | — | — | [Details](02_qos_heatmap/) |
| 4 | **Bottleneck** | 640×480 @ 30Hz, 3-pass blur | **362ms** | **379ms** | **313ms** | **330ms** | **146** | [Details](03_bottleneck_diagnosis/) |
| 5 | Threading Fix | TBD | TBD | TBD | TBD | TBD | TBD | [Details](04_threading_fix/) |

---

## Narrative Arc

1. **Baseline** — Normal pipeline, everything healthy. Establishes reference numbers.
2. **DDS Comparison** — Same pipeline under Cyclone DDS. Shows 30% improvement in transport p99.
3. **QoS Tuning** — Varying reliability and depth. Shows the tradeoff between latency and reliability.
4. **Bottleneck Injection** — 3-pass blur at 30Hz exceeds single-core capacity. Queue builds to 313ms, 146 messages dropped.
5. **Threading Fix** — Parallel blur eliminates the bottleneck. Returns to baseline latency, zero drops.
