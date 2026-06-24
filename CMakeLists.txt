cmake_minimum_required(VERSION 3.16)
project(ros2_pipeline_profiler)

if(CMAKE_COMPILER_IS_GNUCXX OR CMAKE_CXX_COMPILER_ID MATCHES "Clang")
  add_compile_options(-Wall -Wextra -Wpedantic)
endif()

set(CMAKE_EXPORT_COMPILE_COMMANDS ON)

find_package(ament_cmake REQUIRED)
find_package(rclcpp REQUIRED)
find_package(std_msgs REQUIRED)
find_package(sensor_msgs REQUIRED)
find_package(builtin_interfaces REQUIRED)
find_package(rosidl_default_generators REQUIRED)

# -- custom messages --
set(msg_files
  "msg/ProfilerEnvelope.msg"
)

rosidl_generate_interfaces(${PROJECT_NAME}
  ${msg_files}
  DEPENDENCIES builtin_interfaces
)

# -- dummy node to test the build --
add_executable(main
  src/main.cpp
  src/event_logger.cpp
  src/profiler_common.cpp
)
target_include_directories(main PRIVATE ${CMAKE_CURRENT_SOURCE_DIR}/include)
ament_target_dependencies(main rclcpp std_msgs)
rosidl_get_typesupport_target(cpp_typesupport_target ${PROJECT_NAME} "rosidl_typesupport_cpp")
target_link_libraries(main ${cpp_typesupport_target})

install(TARGETS main
DESTINATION lib/${PROJECT_NAME}
)

# -- demo pipeline --
add_executable(sensor_node src/demo/sensor_node.cpp
  src/event_logger.cpp
  src/profiler_common.cpp
)
target_include_directories(sensor_node PRIVATE ${CMAKE_CURRENT_SOURCE_DIR}/include)
ament_target_dependencies(sensor_node rclcpp sensor_msgs)
rosidl_get_typesupport_target(cpp_typesupport_target ${PROJECT_NAME} "rosidl_typesupport_cpp")
target_link_libraries(sensor_node ${cpp_typesupport_target})
install(TARGETS sensor_node DESTINATION lib/${PROJECT_NAME})

add_executable(processing_node src/demo/processing_node.cpp
  src/event_logger.cpp
  src/profiler_common.cpp
)
target_include_directories(processing_node PRIVATE ${CMAKE_CURRENT_SOURCE_DIR}/include)
ament_target_dependencies(processing_node rclcpp std_msgs sensor_msgs)
rosidl_get_typesupport_target(cpp_typesupport_target2 ${PROJECT_NAME} "rosidl_typesupport_cpp")
target_link_libraries(processing_node ${cpp_typesupport_target2})
install(TARGETS processing_node DESTINATION lib/${PROJECT_NAME})

add_executable(control_node src/demo/control_node.cpp
  src/event_logger.cpp
  src/profiler_common.cpp
)
target_include_directories(control_node PRIVATE ${CMAKE_CURRENT_SOURCE_DIR}/include)
ament_target_dependencies(control_node rclcpp std_msgs)
rosidl_get_typesupport_target(cpp_typesupport_target3 ${PROJECT_NAME} "rosidl_typesupport_cpp")
target_link_libraries(control_node ${cpp_typesupport_target3})
install(TARGETS control_node DESTINATION lib/${PROJECT_NAME})

install(DIRECTORY launch DESTINATION share/${PROJECT_NAME})

if(BUILD_TESTING)
  find_package(ament_lint_auto REQUIRED)
  ament_lint_auto_find_test_dependencies()
endif()

ament_package()
