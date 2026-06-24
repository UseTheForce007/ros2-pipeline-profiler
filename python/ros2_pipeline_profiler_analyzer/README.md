# ROS 2 Pipeline Profiler Analyzer

Standalone Python tool (no ROS deps) that reads profiler CSV logs from `ros2-pipeline-profiler` nodes and generates an interactive HTML report with latency breakdowns.

## Quick Start

```bash
pip install -e /path/to/python/
ros2-pipeline-profiler-analyzer --log-dir . --output report.html
```

Requires `pandas` and `plotly`.

## Input CSV Format

Each node writes a CSV with these columns:

| Column | Description |
|---|---|
| `timestamp_ns` | `steady_clock` nanoseconds (monotonic per process, used for intra-node timing) |
| `sys_timestamp_ns` | `system_clock` nanoseconds (wall clock, comparable across processes) |
| `event_type` | 0=PUBLISH, 1=RECEIVE, 2=PROCESS_START, 3=PROCESS_END |
| `message_id` | Unique ID per message (atomic counter across the node) |
| `parent_message_id` | Links forwarded messages to their origin (0 = root) |
| `source_node_name` | Name of the node that logged the event |
| `source_node_id` | Numeric node ID (internal) |
| `topic` | Topic the message was published/received on |
| `original_type` | ROS message type (e.g. `sensor_msgs/msg/LaserScan`) |

## What Is Analyzed

### Message Chains

A chain is a sequence of messages linked by `parent_message_id`. A root message (`parent_message_id=0`) is published by a sensor node. When a processing node receives it and publishes a new result, the new message carries the original's ID as `parent_message_id`. The analyzer traces this lineage end-to-end.

### Stage Latencies

Processing time inside each subscriber node: `PROCESS_END - PROCESS_START` per `(message_id, node)`. Uses `timestamp_ns` (steady clock — valid since both timestamps are from the same process).

### Transport Latencies

Pub/sub wire delay per topic: `RECEIVE - PUBLISH` per `message_id`. Uses `sys_timestamp_ns` (system clock — comparable across publisher and subscriber processes).

### End-to-End Latency

Total time from a root message's PUBLISH to the last event of its chain leaf. Uses `sys_timestamp_ns` to span all nodes in the chain.

### Dropped Messages

Detected as gaps in `message_id` sequences within each node's PUBLISH events.

## Report Sections

| Section | Description |
|---|---|
| **Summary** | Table of count, mean, p50/p90/p99, min/max for every metric |
| **Latency Waterfall** | Stacked horizontal bars — one row per chain, segments show each node's contribution |
| **Latency Distribution** | Histogram per node (processing time) |
| **Latency Over Time** | Scatter plot + rolling average per node |
| **CDF Curve** | Cumulative distribution per node |
| **Box Plot** | Side-by-side distribution comparison per node |
