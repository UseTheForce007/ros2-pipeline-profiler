from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def generate_launch_description():
    return LaunchDescription([
        DeclareLaunchArgument("reliability", default_value="reliable"),
        DeclareLaunchArgument("depth", default_value="10"),

        Node(
            package="ros2_pipeline_profiler",
            executable="sensor_node",
            name="sensor_node",
            parameters=[{
                "reliability": LaunchConfiguration("reliability"),
                "depth": LaunchConfiguration("depth"),
            }],
            output="screen",
        ),
        Node(
            package="ros2_pipeline_profiler",
            executable="processing_node",
            name="processing_node",
            parameters=[{
                "reliability": LaunchConfiguration("reliability"),
                "depth": LaunchConfiguration("depth"),
            }],
            output="screen",
        ),
        Node(
            package="ros2_pipeline_profiler",
            executable="control_node",
            name="control_node",
            output="screen",
        ),
    ])
