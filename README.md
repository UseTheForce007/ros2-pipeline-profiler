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

## Update 3:

- `ProfilerPublisher<T>` — template class that wraps any ROS message in a `ProfilerEnvelope`:
  1. Serializes the original message to bytes
  2. Generates a unique `message_id` and fills metadata (timestamps, node ID, hop count)
  3. Logs a `PUBLISH` event to CSV
  4. Publishes the envelope on the topic

- `parent_message_id` explained:
  - `0` = root message (new chain, no parent)
  - Any other number = this message was produced as a result of processing message with that ID
  - Enables the analyzer to reconstruct message flow chains across nodes

- Tested: `ProfilerPublisher<std_msgs::msg::String>` publishes 3 messages/second; CSV output verified with correct metadata

## Update 4:

- `ProfilerSubscriber<T>` — template class that receives `ProfilerEnvelope` and restores the original message:
  1. Logs `RECEIVE` event on arrival
  2. Deserializes `serialized_data` bytes back to the original type `T`
  3. Logs `PROCESS_START` before calling user callback
  4. Logs `PROCESS_END` after callback returns (even if it throws)
  5. Passes deserialized message + `Metadata` (timestamps, hop_count, message_id chain) to the callback

- Full round-trip tested: publish → envelope → receive → deserialize → callback; CSV output shows all 4 event types per message

## Update 5:

- **Node IDs**: deterministic, sequential — sensor=1, processing=2, control=3
- **Message IDs**: `node_id * 1000 + counter` — readable IDs like 1001, 2001, 3001
- **CSV columns added**: `sys_timestamp_ns` (system_clock), `send_timestamp_ns` (envelope send time), `origin_timestamp_ns` (root origin time)
- **Subscriber node_id fix**: RECEIVE/PROCESS_START/PROCESS_END log the subscriber's own node_id, not the sender's
- **Python analyzer**: uses `send_timestamp_ns`/`origin_timestamp_ns` for cross-node timing; filters negative latencies; fixed waterfall chart via `events_by_id`
- **Launch file**: `ros2 launch ros2_pipeline_profiler demo.launch.py` runs all 3 nodes
- **Python package README**: `python/ros2_pipeline_profiler_analyzer/README.md` documents input format, metrics, and report sections
