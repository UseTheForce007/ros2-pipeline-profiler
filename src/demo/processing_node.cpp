#include <chrono>
#include <numeric>

#include "rclcpp/rclcpp.hpp"
#include "sensor_msgs/msg/laser_scan.hpp"
#include "std_msgs/msg/float64.hpp"
#include "ros2_pipeline_profiler/event_logger.hpp"
#include "ros2_pipeline_profiler/profiler_publisher.hpp"
#include "ros2_pipeline_profiler/profiler_subscriber.hpp"

int
main(int argc, char* argv[])
{
	rclcpp::init(argc, argv);
	auto node = std::make_shared<rclcpp::Node>("processing_node");

	EventLogger logger(node->get_name());
	ProfilerPublisher<std_msgs::msg::Float64> pub(*node, "/processed", rclcpp::QoS(10), logger);

	ProfilerSubscriber<sensor_msgs::msg::LaserScan> sub(
		*node, "/scan", rclcpp::QoS(10),
		[&](std::shared_ptr<sensor_msgs::msg::LaserScan> msg, const Metadata& meta) {
			// Simulate processing delay
			std::this_thread::sleep_for(std::chrono::milliseconds(2));

			float mean = std::accumulate(msg->ranges.begin(), msg->ranges.end(), 0.0f) /
						 static_cast<float>(msg->ranges.size());

			auto out = std_msgs::msg::Float64();
			out.data = mean;
			pub.publish(out, meta.message_id, meta);

			RCLCPP_INFO(node->get_logger(), "processed: mean=%.3f (msg_id=%lu, hop=%u)", mean,
						meta.message_id, meta.hop_count);
		},
		logger);

	rclcpp::spin(node);
	rclcpp::shutdown();
	return 0;
}
