#include "ros2_pipeline_profiler/event_logger.hpp"

#include <chrono>
#include <cstdint>
#include <ctime>
#include <deque>
#include <iomanip>
#include <mutex>
#include <sstream>
#include <string>
#include <thread>

#include "ros2_pipeline_profiler/profiler_common.hpp"

static constexpr size_t batch_size_ = 100;

EventLogger::EventLogger(const std::string& node_name) : shutdown_(false), node_name_(node_name)
{
	auto now = std::chrono::system_clock::now();
	auto tt = std::chrono::system_clock::to_time_t(now);
	std::stringstream ss;
	ss << "profiler_" << node_name << "_" << std::put_time(std::gmtime(&tt), "%Y%m%d_%H%M%S")
	   << ".csv";

	file_.open(ss.str());
	file_ << "timestamp_ns,event_type,message_id,parent_message_id,"
			 "source_node_id,source_node_name,topic,original_type,"
			 "sys_timestamp_ns,send_timestamp_ns,origin_timestamp_ns\n";
	file_.flush();

	writer_thread_ = std::thread(&EventLogger::writerLoop, this);
}

EventLogger::~EventLogger()
{
	{
		std::lock_guard<std::mutex> lock(mutex_);
		shutdown_ = true;
	}
	cv_.notify_one();
	writer_thread_.join();
}

void
EventLogger::enable()
{
	enable_ = true;
}

void
EventLogger::disable()
{
	enable_ = false;
}

void
EventLogger::log(EventType type, uint64_t message_id, uint64_t parent_message_id,
				 uint16_t source_node_id, const std::string& source_node_name,
				 const std::string& topic, const std::string& original_type,
				 int64_t send_timestamp_ns, int64_t origin_timestamp_ns)
{
	if (!enable_) return;
	int64_t now = static_cast<int64_t>(
		std::chrono::steady_clock::now().time_since_epoch().count());
	int64_t sys_now = static_cast<int64_t>(
		std::chrono::duration_cast<std::chrono::nanoseconds>(
			std::chrono::system_clock::now().time_since_epoch())
			.count());
	std::stringstream row;
	row << now << "," << static_cast<int>(type) << "," << message_id << "," << parent_message_id
		<< "," << source_node_id << "," << source_node_name << "," << topic << "," << original_type
		<< "," << sys_now << "," << send_timestamp_ns << "," << origin_timestamp_ns << "\n";
	std::lock_guard<std::mutex> lock(mutex_);
	queue_.push_back(row.str());
	if (queue_.size() >= batch_size_) {
		cv_.notify_one();
	}
}

void
EventLogger::writerLoop()
{
	std::unique_lock<std::mutex> lock(mutex_);
	while (!shutdown_) {
		cv_.wait_for(lock, std::chrono::milliseconds(100),
					 [this] { return shutdown_ || queue_.size() >= batch_size_; });
		auto batch = std::deque<std::string>{};
		std::swap(queue_, batch);
		lock.unlock();
		for (auto& row : batch) file_ << row;
		file_.flush();
		lock.lock();
	}
	// Drain any remaining events on shutdown
	if (!queue_.empty()) {
		auto batch = std::deque<std::string>{};
		std::swap(queue_, batch);
		lock.unlock();
		for (auto& row : batch) file_ << row;
		file_.flush();
	}
}
