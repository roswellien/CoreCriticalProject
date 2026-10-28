#pragma once

#include <optional>
#include <string>
#include <string_view>
#include <vector>

namespace mw34::input {

struct DirectInputJoystickIdentity {
    std::wstring instance_guid;
    std::wstring product_name;
};

inline std::optional<std::size_t> find_selected_joystick(
    const std::vector<DirectInputJoystickIdentity> &joysticks, std::wstring_view instance_guid,
    std::wstring_view product_name) {
    if (!instance_guid.empty()) {
        for (std::size_t index = 0; index < joysticks.size(); ++index) {
            if (joysticks[index].instance_guid == instance_guid) {
                return index;
            }
        }
    }

    if (!product_name.empty()) {
        for (std::size_t index = 0; index < joysticks.size(); ++index) {
            if (joysticks[index].product_name == product_name) {
                return index;
            }
        }
    }

    return std::nullopt;
}

inline bool should_forward_directinput_device(bool filter_joysticks, bool is_joystick,
                                              bool has_selected, bool selected_guid_matches,
                                              bool selected_already_forwarded) {
    if (!filter_joysticks || !is_joystick) {
        return true;
    }

    return has_selected && selected_guid_matches && !selected_already_forwarded;
}

} // namespace mw34::input
