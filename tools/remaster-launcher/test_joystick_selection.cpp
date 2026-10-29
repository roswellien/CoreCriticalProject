#include "native-overrides/joystick_selection.hpp"

#include <iostream>
#include <stdexcept>

namespace {

void require(bool condition, const char *message) {
    if (!condition) {
        throw std::runtime_error(message);
    }
}

} // namespace

int main() {
    const std::vector<mw34::input::DirectInputJoystickIdentity> joysticks{
        {L"{first}", L"Flight stick"}, {L"{chosen}", L"Flight stick"}, {L"{other}", L"Gamepad"}};

    const auto exact = mw34::input::find_selected_joystick(joysticks, L"{chosen}", L"Flight stick");
    require(exact == 1, "Instance GUID must take precedence over a duplicate product name");

    const auto fallback = mw34::input::find_selected_joystick(joysticks, L"{missing}", L"Flight stick");
    require(fallback == 0, "Product name must select the first fallback match");

    const auto missing = mw34::input::find_selected_joystick(joysticks, L"{missing}", L"Unknown");
    require(!missing, "An unavailable selection must not choose another joystick");

    const auto no_identity = mw34::input::find_selected_joystick(joysticks, L"", L"");
    require(!no_identity, "An empty explicit selection must not choose a joystick");

    require(mw34::input::should_forward_directinput_device(false, true, false, false, false),
            "The default mode must preserve the original device list.");
    require(!mw34::input::should_forward_directinput_device(true, true, false, false, false),
            "None must omit every joystick.");
    require(mw34::input::should_forward_directinput_device(true, false, false, false, false),
            "Joystick selection must not filter unrelated device classes.");
    require(mw34::input::should_forward_directinput_device(true, true, true, true, false),
            "The selected joystick must be forwarded.");
    require(!mw34::input::should_forward_directinput_device(true, true, true, false, false),
            "Unselected joysticks must be omitted.");
    require(!mw34::input::should_forward_directinput_device(true, true, true, true, true),
            "Duplicate instance matches must not be forwarded twice.");

    std::cout << "DirectInput joystick identity selection checks passed.\n";
}
