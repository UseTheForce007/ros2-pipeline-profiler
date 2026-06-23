#pragma once

#include <cstdint>
#include <functional>
#include <memory>
#include <string>

#include "rclcpp/rclcpp.hpp"
#include "rclcpp/serialization.hpp"
#include "ros2_pipeline_profiler/event_logger.hpp"
#include "ros2_pipeline_profiler/msg/profiler_envelope.hpp"
#include "ros2_pipeline_profiler/profiler_common.hpp"

template <typename T>
class ProfilerSubscriber
{
   public:
	using Callback = std::function<void(std::shared_ptr<T>, const Metadata&)>;

	ProfilerSubscriber(rclcpp::Node& node, const std::string& topic, const rclcpp::QoS& qos,
					   Callback callback, EventLogger& logger);

   private:
	void onEnvelope(const ros2_pipeline_profiler::msg::ProfilerEnvelope::SharedPtr envelope);

	rclcpp::Subscription<ros2_pipeline_profiler::msg::ProfilerEnvelope>::SharedPtr subscription_;
	rclcpp::Serialization<T> serializer_;
	Callback callback_;
	EventLogger& logger_;
	std::string node_name_;
	uint16_t node_id_;
};

#include "ros2_pipeline_profiler/profiler_subscriber_impl.hpp"
