#include "rclcpp/rclcpp.hpp"
#include "ros2_pipeline_profiler/msg/profiler_envelope.hpp"

int main(int argc, char* argv[])
{
  rclcpp::init(argc, argv);
  auto node = std::make_shared<rclcpp::Node>("pub");
  auto pub = node->create_publisher<ros2_pipeline_profiler::msg::ProfilerEnvelope>("topic", 10);
  auto timer = node->create_wall_timer(std::chrono::milliseconds(500), [node, pub]() {
    pub->publish(ros2_pipeline_profiler::msg::ProfilerEnvelope());
    RCLCPP_INFO(node->get_logger(), "pub");
  });
  rclcpp::spin(node);
  rclcpp::shutdown();
}
