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

    std::cout << "DirectInput joystick identity selection checks passed.\n";
}
