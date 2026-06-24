#include <chrono>

#include "rclcpp/rclcpp.hpp"
#include "ros2_pipeline_profiler/event_logger.hpp"
#include "ros2_pipeline_profiler/profiler_publisher.hpp"
#include "sensor_msgs/msg/image.hpp"

int
main(int argc, char* argv[])
{
	rclcpp::init(argc, argv);
	auto node = std::make_shared<rclcpp::Node>("sensor_node");

	node->declare_parameter("reliability", "reliable");
	node->declare_parameter("depth", 10);
	auto reliability = node->get_parameter("reliability").as_string();
	auto depth = node->get_parameter("depth").as_int();

	auto qos = rclcpp::QoS(depth);
	if (reliability == "best_effort") {
		qos.best_effort();
	} else {
		qos.reliable();
	}

	EventLogger logger(node->get_name());
	ProfilerPublisher<sensor_msgs::msg::Image> pub(*node, "/image", qos, logger);

	constexpr int width = 640;
	constexpr int height = 480;
	constexpr int tile = 64;

	auto timer = node->create_wall_timer(std::chrono::milliseconds(33), [&]() {
		auto msg = sensor_msgs::msg::Image();
		msg.header.stamp = node->now();
		msg.width = width;
		msg.height = height;
		msg.encoding = "mono8";
		msg.step = width;
		msg.data.resize(width * height);
		for (int i = 0; i < height; ++i) {
			for (int j = 0; j < width; ++j) {
				msg.data[i * width + j] = ((i / tile) + (j / tile)) % 2 * 255;
			}
		}
		pub.publish(msg);
		RCLCPP_INFO(node->get_logger(), "published image");
	});

	rclcpp::spin(node);
	rclcpp::shutdown();
	return 0;
}
