template <typename T>
ProfilerSubscriber<T>::ProfilerSubscriber(rclcpp::Node& node, const std::string& topic,
										  const rclcpp::QoS& qos, Callback callback,
										  EventLogger& logger)
  : callback_(callback), logger_(logger), node_name_(node.get_name())
{
	node_id_ = NodeRegistry::getInstance().registerNode(node_name_);
	subscription_ = node.create_subscription<ros2_pipeline_profiler::msg::ProfilerEnvelope>(
		topic, qos,
		std::bind(&ProfilerSubscriber::onEnvelope, this, std::placeholders::_1));
}

template <typename T>
void
ProfilerSubscriber<T>::onEnvelope(
	const ros2_pipeline_profiler::msg::ProfilerEnvelope::SharedPtr envelope)
{
	Metadata meta;
	meta.message_id = envelope->message_id;
	meta.parent_message_id = envelope->parent_message_id;
	meta.origin_timestamp = envelope->origin_timestamp;
	meta.send_timestamp = envelope->send_timestamp;
	meta.source_node_id = envelope->source_node_id;
	meta.hop_count = envelope->hop_count;

	logger_.log(EventType::RECEIVE, meta.message_id, meta.parent_message_id, meta.source_node_id,
				node_name_, subscription_->get_topic_name(), envelope->original_type);

	rclcpp::SerializedMessage serialized(envelope->serialized_data.size());
	auto& rcl_msg = serialized.get_rcl_serialized_message();
	std::memcpy(rcl_msg.buffer, envelope->serialized_data.data(), envelope->serialized_data.size());
	rcl_msg.buffer_length = envelope->serialized_data.size();

	auto msg = std::make_shared<T>();
	serializer_.deserialize_message(&serialized, msg.get());

	logger_.log(EventType::PROCESS_START, meta.message_id, meta.parent_message_id,
				meta.source_node_id, node_name_, subscription_->get_topic_name(),
				envelope->original_type);

	try {
		callback_(msg, meta);
	} catch (...) {
		logger_.log(EventType::PROCESS_END, meta.message_id, meta.parent_message_id,
					meta.source_node_id, node_name_, subscription_->get_topic_name(),
					envelope->original_type);
		throw;
	}

	logger_.log(EventType::PROCESS_END, meta.message_id, meta.parent_message_id,
				meta.source_node_id, node_name_, subscription_->get_topic_name(),
				envelope->original_type);
}
