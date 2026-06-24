#include "ros2_pipeline_profiler/profiler_common.hpp"

#include <cstdint>
#include <functional>
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

	// Known demo nodes get clean sequential IDs (sorted alphabetically)
	static const char* known[] = {"sensor_node", "processing_node", "control_node"};
	uint16_t id = 0;
	for (int i = 0; i < 3; i++) {
		if (name == known[i]) {
			id = i + 1;
			break;
		}
	}
	if (id == 0) {
		// Unknown node — deterministic hash, ensure odd so 0 is reserved
		id = (static_cast<uint16_t>(std::hash<std::string>{}(name) & 0xFFFE)) + 1;
	}
	map_[name] = id;
	return id;
}

uint16_t
NodeRegistry::getNodeId(const std::string& name) const
{
	std::lock_guard<std::mutex> lock(mutex_);
	auto it = map_.find(name);
	return it != map_.end() ? it->second : 0;
}
