#pragma once
#include <optional>
#include <string>

namespace mw34::vehicle_lighting {
struct Node {
    std::string name;
    unsigned parent{}, flags{};
};
struct State {
    unsigned vehicle{}, healthy{};
    bool alive{};
};
// Original vehicle destruction switches healthy/destroyed branches. The active
// bit is semantic scene activation, not a camera-frustum visibility bit.
template <class ReadNode> State inspect(unsigned node, ReadNode read) {
    unsigned healthy = 0;
    bool healthy_active = false, destroyed = false;
    for (unsigned depth = 0; node && depth < 32; ++depth) {
        const auto current = read(node);
        if (!current) return {};
        if (current->name == "healthy") {
            healthy = node;
            healthy_active = (current->flags & 4) != 0;
        }
        if (current->name == "destroyed") destroyed = true;
        if (current->name.starts_with("veh_"))
            return {node, healthy, healthy && healthy_active && !destroyed && (current->flags & 4)};
        node = current->parent;
    }
    return {};
}
inline bool headlamp(const std::string& name) {
    return name == "tredtruck09" || name == "TREDTRUCK09";
}
} // namespace mw34::vehicle_lighting
