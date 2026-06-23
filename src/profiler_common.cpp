#include "ros2_pipeline_profiler/profiler_common.hpp"

#include <cstdint>
#include <iterator>
#include <mutex>
#include <string>

NodeRegistry&
NodeRegistry::getInstance()
{
	static NodeRegistry instance;
	return instance;
}

uint16_t
NodeRegistry::registerNode(const std::string& name)
{
	std::lock_guard<std::mutex> lock(mutex_);
	auto it = map_.find(name);
	if (it != map_.end())
		return it->second;
	map_[name] = next_id_++;
	return map_[name];
}

uint16_t
NodeRegistry::getNodeId(const std::string& name) const
{
	std::lock_guard<std::mutex> lock(mutex_);
	auto it = map_.find(name);
	return it != map_.end() ? it->second : 0;
}
