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

} // namespace mw34::input
