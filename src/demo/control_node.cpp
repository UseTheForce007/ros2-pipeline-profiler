#include "rclcpp/rclcpp.hpp"
#include "std_msgs/msg/float64.hpp"
#include "ros2_pipeline_profiler/event_logger.hpp"
#include "ros2_pipeline_profiler/profiler_subscriber.hpp"

int
main(int argc, char* argv[])
{
	rclcpp::init(argc, argv);
	auto node = std::make_shared<rclcpp::Node>("control_node");

	EventLogger logger(node->get_name());

	ProfilerSubscriber<std_msgs::msg::Float64> sub(
		*node, "/processed", rclcpp::QoS(10),
		[&](std::shared_ptr<std_msgs::msg::Float64> msg, const Metadata& meta) {
	auto now = rclcpp::Clock(RCL_SYSTEM_TIME).now();
		rclcpp::Time origin(meta.origin_timestamp, RCL_SYSTEM_TIME);
		auto e2e = (now - origin).nanoseconds() / 1e6;

			RCLCPP_INFO(node->get_logger(), "received: %.3f (e2e=%.2fms, msg_id=%lu, hop=%u)",
						msg->data, e2e, meta.message_id, meta.hop_count);
		},
		logger);

	rclcpp::spin(node);
	rclcpp::shutdown();
	return 0;
}
