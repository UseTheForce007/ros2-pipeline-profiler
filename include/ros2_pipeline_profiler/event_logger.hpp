#pragma once

#include <atomic>
#include <condition_variable>
#include <cstdint>
#include <deque>
#include <fstream>
#include <string>
#include <thread>

#include "ros2_pipeline_profiler/profiler_common.hpp"
class EventLogger
{
   public:
	EventLogger(const std::string& node_name);
	~EventLogger();
	void log(EventType type, uint64_t message_id, uint64_t parent_message_id,
			 uint16_t source_node_id, const std::string& source_node_name, const std::string& topic,
			 const std::string& original_type);
	void enable();
	void disable();

   private:
	void writerLoop();
	std::mutex mutex_;
	std::condition_variable cv_;
	std::deque<std::string> queue_;
	std::ofstream file_;
	std::thread writer_thread_;
	std::atomic<bool> shutdown_;
	std::atomic<bool> enable_{true};
	std::string node_name_;
};
