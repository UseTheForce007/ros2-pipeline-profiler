#include <chrono>
#include <cstdint>
#include <vector>

#include "rclcpp/rclcpp.hpp"
#include "sensor_msgs/msg/image.hpp"
#include "std_msgs/msg/float64.hpp"
#include "ros2_pipeline_profiler/event_logger.hpp"
#include "ros2_pipeline_profiler/profiler_publisher.hpp"
#include "ros2_pipeline_profiler/profiler_subscriber.hpp"

static int
clamp(int v, int lo, int hi)
{
	return v < lo ? lo : (v > hi ? hi : v);
}

int
main(int argc, char* argv[])
{
	rclcpp::init(argc, argv);
	auto node = std::make_shared<rclcpp::Node>("processing_node");

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
	ProfilerPublisher<std_msgs::msg::Float64> pub(*node, "/processed", qos, logger);

	ProfilerSubscriber<sensor_msgs::msg::Image> sub(
		*node, "/image", qos,
		[&](std::shared_ptr<sensor_msgs::msg::Image> msg, const Metadata& meta) {
			int w = msg->width;
			int h = msg->height;
			int step = msg->step;
			const uint8_t* data = msg->data.data();

			// Separable 5x5 Gaussian blur: kernel = [1, 4, 6, 4, 1] / 16
			const int kernel[5] = {1, 4, 6, 4, 1};

			// Three sequential blur passes to ensure processing exceeds sensor rate
			std::vector<uint8_t> buf(h * step);
			std::vector<uint8_t> output(h * step);
			const uint8_t* src = data;

			for (int pass = 0; pass < 3; ++pass) {
				// Horizontal pass
				for (int i = 0; i < h; ++i) {
					for (int j = 0; j < w; ++j) {
						int sum = 0;
						for (int k = -2; k <= 2; ++k) {
							int col = clamp(j + k, 0, w - 1);
							sum += kernel[k + 2] * src[i * step + col];
						}
						buf[i * step + j] = sum / 16;
					}
				}

				// Vertical pass
				for (int i = 0; i < h; ++i) {
					for (int j = 0; j < w; ++j) {
						int sum = 0;
						for (int k = -2; k <= 2; ++k) {
							int row = clamp(i + k, 0, h - 1);
							sum += kernel[k + 2] * buf[row * step + j];
						}
						output[i * step + j] = sum / 16;
					}
				}

				src = output.data();
			}

			// Mean of blurred result
			uint64_t total = 0;
			for (auto& p : output) {
				total += p;
			}
			float mean = static_cast<float>(total) / output.size();

			auto out = std_msgs::msg::Float64();
			out.data = mean;
			pub.publish(out, meta.message_id, meta);

			RCLCPP_INFO(node->get_logger(), "processed: mean=%.2f (msg_id=%lu, hop=%u)", mean,
						meta.message_id, meta.hop_count);
		},
		logger);

	rclcpp::spin(node);
	rclcpp::shutdown();
	return 0;
}
