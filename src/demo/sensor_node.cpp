#include <chrono>
#include <random>

#include "rclcpp/rclcpp.hpp"
#include "ros2_pipeline_profiler/event_logger.hpp"
#include "ros2_pipeline_profiler/profiler_publisher.hpp"
#include "sensor_msgs/msg/laser_scan.hpp"

int
main(int argc, char* argv[])
{
	rclcpp::init(argc, argv);
	auto node = std::make_shared<rclcpp::Node>("sensor_node");

	EventLogger logger(node->get_name());
	ProfilerPublisher<sensor_msgs::msg::LaserScan> pub(*node, "/scan", rclcpp::QoS(10), logger);

	std::mt19937 rng{std::random_device{}()};
	std::uniform_real_distribution<float> dist{0.0f, 1.0f};

	auto timer = node->create_wall_timer(std::chrono::milliseconds(100), [&]() {
		auto msg = sensor_msgs::msg::LaserScan();
		msg.header.stamp = node->now();
		msg.header.frame_id = "laser";
		msg.angle_min = -M_PI;
		msg.angle_max = M_PI;
		msg.angle_increment = M_PI / 180;
		msg.time_increment = 1.0 / 360.0;
		msg.scan_time = 0.1;
		msg.range_min = 0.1;
		msg.range_max = 10.0;
		msg.ranges.resize(360);
		for (auto& r : msg.ranges) r = dist(rng);

		pub.publish(msg);
		RCLCPP_INFO(node->get_logger(), "published scan");
	});

	rclcpp::spin(node);
	rclcpp::shutdown();
	return 0;
}
