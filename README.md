# ros2-pipeline-profiler

## Update 1:

- Custom msg type for profiling added:

uint64 message_id
uint64 parent_message_id
builtin_interfaces/Time origin_timestamp
builtin_interfaces/Time send_timestamp
uint16 source_node_id
uint16 hop_count
string original_type
uint8[] serialized_data

- A simpler publisher to test the message added 

## Update 2:

- Core profiler library components added:
  - `MessageIdFactory` — singleton generating globally unique message IDs
  - `EventType` enum — PUBLISH, RECEIVE, PROCESS_START, PROCESS_END
  - `Metadata` struct — bundles message_id, parent_message_id, timestamps, source_node_id, hop_count
  - `NodeRegistry` — singleton mapping node names to uint16 IDs (1-based, 0 = no parent)
  - `EventLogger` — thread-safe CSV writer with background writer thread; logs to `profiler_<node>_<timestamp>.csv`
