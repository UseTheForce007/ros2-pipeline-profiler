#pragma once

#include <atomic>
#include <cstdint>
#include <mutex>
#include <string>
#include <unordered_map>

#include "builtin_interfaces/msg/time.hpp"
class MessageIdFactory
{
   public:
	static MessageIdFactory& getInstance()
	{
		static MessageIdFactory instance;
		return instance;
	}
	uint64_t generate()
	{
		return next_id_++;
	}

   private:
	MessageIdFactory() = default;
	std::atomic<uint64_t> next_id_{1};
};

enum class EventType
{
	PUBLISH,
	RECEIVE,
	PROCESS_START,
	PROCESS_END
};

struct Metadata {
	uint64_t message_id;
	uint64_t parent_message_id;
	builtin_interfaces::msg::Time origin_timestamp;
	builtin_interfaces::msg::Time send_timestamp;
	uint16_t source_node_id;
	uint16_t hop_count;
};

class NodeRegistry
{
   public:
	static NodeRegistry& getInstance();

	uint16_t registerNode(const std::string& name);
	uint16_t getNodeId(const std::string& name) const;

   private:
	std::unordered_map<std::string, uint16_t> map_;
	mutable std::mutex mutex_;
	uint16_t next_id_{1};
};
