cmake_minimum_required(VERSION 3.16)
project(ros2_pipeline_profiler)

if(CMAKE_COMPILER_IS_GNUCXX OR CMAKE_CXX_COMPILER_ID MATCHES "Clang")
  add_compile_options(-Wall -Wextra -Wpedantic)
endif()

set(CMAKE_EXPORT_COMPILE_COMMANDS ON)

find_package(ament_cmake REQUIRED)
find_package(rclcpp REQUIRED)
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
ament_target_dependencies(main rclcpp)
rosidl_get_typesupport_target(cpp_typesupport_target ${PROJECT_NAME} "rosidl_typesupport_cpp")
target_link_libraries(main ${cpp_typesupport_target})

install(TARGETS main
DESTINATION lib/${PROJECT_NAME}
)

if(BUILD_TESTING)
  find_package(ament_lint_auto REQUIRED)
  ament_lint_auto_find_test_dependencies()
endif()

ament_package()
