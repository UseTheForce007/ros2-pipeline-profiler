#pragma once

#include <cstdint>

#include "rclcpp/rclcpp.hpp"
#include "rclcpp/serialization.hpp"
#include "ros2_pipeline_profiler/event_logger.hpp"
#include "ros2_pipeline_profiler/msg/profiler_envelope.hpp"
#include "ros2_pipeline_profiler/profiler_common.hpp"

template <typename T>
class ProfilerPublisher
{
   public:
	ProfilerPublisher(rclcpp::Node& node, const std::string& topic, const rclcpp::QoS& qos,
					  EventLogger& logger);

	void publish(const T& msg, uint64_t parent_message_id = 0,
				 const Metadata& origin_meta = Metadata());

   private:
	rclcpp::Publisher<ros2_pipeline_profiler::msg::ProfilerEnvelope>::SharedPtr publisher_;
	rclcpp::Serialization<T> serializer_;
	EventLogger& logger_;
	std::string node_name_;
	uint16_t node_id_;
};

#include "ros2_pipeline_profiler/profiler_publisher_impl.hpp"
