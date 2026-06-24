template <typename T>
ProfilerPublisher<T>::ProfilerPublisher(rclcpp::Node& node, const std::string& topic,
										const rclcpp::QoS& qos, EventLogger& logger)
  : logger_(logger), node_name_(node.get_name())
{
	node_id_ = NodeRegistry::getInstance().registerNode(node_name_);
	publisher_ = node.create_publisher<ros2_pipeline_profiler::msg::ProfilerEnvelope>(topic, qos);
}

template <typename T>
void
ProfilerPublisher<T>::publish(const T& msg, uint64_t parent_message_id,
							  const Metadata& origin_meta)
{
	rclcpp::SerializedMessage serialized;
	serializer_.serialize_message(&msg, &serialized);

	auto now = rclcpp::Clock(RCL_SYSTEM_TIME).now();

	auto envelope = ros2_pipeline_profiler::msg::ProfilerEnvelope();
	envelope.message_id = (static_cast<uint64_t>(node_id_) * 1000ULL) +
						  MessageIdFactory::getInstance().generate();
	envelope.parent_message_id = parent_message_id;
	envelope.send_timestamp = now;

	if (parent_message_id == 0) {
		envelope.origin_timestamp = now;
		envelope.hop_count = 0;
	} else {
		envelope.origin_timestamp = origin_meta.origin_timestamp;
		envelope.hop_count = origin_meta.hop_count + 1;
	}

	envelope.source_node_id = node_id_;
	envelope.original_type = rosidl_generator_traits::name<T>();
	auto& rcl_msg = serialized.get_rcl_serialized_message();
	envelope.serialized_data.assign(rcl_msg.buffer, rcl_msg.buffer + rcl_msg.buffer_length);

	int64_t send_ns = rclcpp::Time(envelope.send_timestamp).nanoseconds();
	int64_t origin_ns = rclcpp::Time(envelope.origin_timestamp).nanoseconds();
	logger_.log(EventType::PUBLISH, envelope.message_id, envelope.parent_message_id,
				envelope.source_node_id, node_name_, publisher_->get_topic_name(),
				envelope.original_type, send_ns, origin_ns);

	publisher_->publish(envelope);
}
