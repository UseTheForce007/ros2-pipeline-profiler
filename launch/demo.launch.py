from launch import LaunchDescription
from launch_ros.actions import Node


def generate_launch_description():
    return LaunchDescription([
        Node(
            package="ros2_pipeline_profiler",
            executable="sensor_node",
            name="sensor_node",
            output="screen",
        ),
        Node(
            package="ros2_pipeline_profiler",
            executable="processing_node",
            name="processing_node",
            output="screen",
        ),
        Node(
            package="ros2_pipeline_profiler",
            executable="control_node",
            name="control_node",
            output="screen",
        ),
    ])
