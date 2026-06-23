#include "rclcpp/rclcpp.hpp"
#include "ros2_pipeline_profiler/event_logger.hpp"
#include "ros2_pipeline_profiler/profiler_publisher.hpp"
#include "ros2_pipeline_profiler/profiler_subscriber.hpp"
#include "std_msgs/msg/string.hpp"

int main(int argc, char* argv[])
{
	rclcpp::init(argc, argv);
	auto node = std::make_shared<rclcpp::Node>("test_pub_sub");

	EventLogger logger(node->get_name());

	ProfilerPublisher<std_msgs::msg::String> pub(*node, "test_topic", rclcpp::QoS(10), logger);

	ProfilerSubscriber<std_msgs::msg::String> sub(
		*node, "test_topic", rclcpp::QoS(10),
		[&](std::shared_ptr<std_msgs::msg::String> msg, const Metadata& meta) {
			RCLCPP_INFO(node->get_logger(), "received: '%s' (msg_id=%lu, hop=%u)",
						msg->data.c_str(), meta.message_id, meta.hop_count);
		},
		logger);

	auto timer = node->create_wall_timer(std::chrono::seconds(1), [&]() {
		auto msg = std_msgs::msg::String();
		msg.data = "hello";
		pub.publish(msg);
		RCLCPP_INFO(node->get_logger(), "published");
	});

	rclcpp::spin(node);
	rclcpp::shutdown();
}
