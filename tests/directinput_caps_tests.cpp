// Tests for runtime/input/directinput_caps.hpp with authored DIDEVCAPS fixtures. The force-feedback
// fixture copies the shape of a racing wheel's report (attached, polled, force feedback with its
// effect options); the plain fixture is a joystick without force feedback. These establish the
// host's report only; the game's reaction to it is documented in the header, not tested here.
#include "input/directinput_caps.hpp"

#include <cstdio>
#include <cstring>

namespace {
unsigned failures;

void check(bool condition, const char *what) {
    if (!condition) {
        std::fprintf(stderr, "failed: %s\n", what);
        ++failures;
    }
}

DIDEVCAPS wheel_caps() {
    DIDEVCAPS caps{};
    caps.dwSize = sizeof(caps);
    caps.dwFlags = DIDC_ATTACHED | DIDC_POLLEDDEVICE | DIDC_FORCEFEEDBACK | DIDC_FFATTACK |
                   DIDC_FFFADE | DIDC_SATURATION | DIDC_POSNEGCOEFFICIENTS | DIDC_POSNEGSATURATION |
                   DIDC_DEADBAND | DIDC_STARTDELAY;
    caps.dwDevType = DIDEVTYPE_JOYSTICK | (DIDEVTYPEJOYSTICK_WHEEL << 8) | DIDEVTYPE_HID;
    caps.dwAxes = 3;
    caps.dwButtons = 13;
    caps.dwPOVs = 1;
    caps.dwFFSamplePeriod = 1000;
    caps.dwFFMinTimeResolution = 1000;
    caps.dwFirmwareRevision = 0x2b;
    caps.dwHardwareRevision = 0x19;
    caps.dwFFDriverVersion = 0x500;
    return caps;
}
} // namespace

int main() {
    static_assert(sizeof(DIDEVCAPS) == 44, "the game asks for the 44-byte DirectInput 5 layout");

    // A force-feedback device reaches the game as the same device without force feedback.
    DIDEVCAPS wheel = wheel_caps();
    const DIDEVCAPS reported = wheel;
    check(mw34::directinput::hide_force_feedback(wheel), "the wheel's force feedback is reported");
    check((wheel.dwFlags & DIDC_FORCEFEEDBACK) == 0, "DIDC_FORCEFEEDBACK is cleared");
    check((wheel.dwFlags & mw34::directinput::force_feedback_flags) == 0,
          "every force-feedback option flag is cleared");
    check(wheel.dwFlags == (DIDC_ATTACHED | DIDC_POLLEDDEVICE), "input flags are kept");
    check(wheel.dwFFSamplePeriod == 0 && wheel.dwFFMinTimeResolution == 0 &&
              wheel.dwFFDriverVersion == 0,
          "force-feedback timing and driver fields read as zero");
    check(wheel.dwSize == reported.dwSize && wheel.dwDevType == reported.dwDevType &&
              wheel.dwAxes == reported.dwAxes && wheel.dwButtons == reported.dwButtons &&
              wheel.dwPOVs == reported.dwPOVs &&
              wheel.dwFirmwareRevision == reported.dwFirmwareRevision &&
              wheel.dwHardwareRevision == reported.dwHardwareRevision,
          "device type, controls and revisions are unchanged");

    // A joystick without force feedback is reported exactly as the device reported it.
    DIDEVCAPS plain{};
    plain.dwSize = sizeof(plain);
    plain.dwFlags = DIDC_ATTACHED | DIDC_EMULATED;
    plain.dwDevType = DIDEVTYPE_JOYSTICK | (DIDEVTYPEJOYSTICK_GAMEPAD << 8);
    plain.dwAxes = 6;
    plain.dwButtons = 16;
    plain.dwPOVs = 1;
    const DIDEVCAPS plain_reported = plain;
    check(!mw34::directinput::hide_force_feedback(plain), "a plain joystick reports none");
    check(std::memcmp(&plain, &plain_reported, sizeof(plain)) == 0,
          "a device without force feedback is unchanged");

    // The flag word sits inside the 24-byte DirectInput 3 layout, so a short guest request copied
    // from the cleared report also carries no force-feedback flags.
    DIDEVCAPS short_request = wheel_caps();
    short_request.dwSize = 24;
    check(mw34::directinput::hide_force_feedback(short_request),
          "a short request's force feedback is reported");
    DWORD short_flags{};
    std::memcpy(&short_flags, reinterpret_cast<const unsigned char *>(&short_request) + 4,
                sizeof(short_flags));
    check((short_flags & mw34::directinput::force_feedback_flags) == 0,
          "the DirectInput 3 prefix carries no force-feedback flags");

    if (failures)
        return 1;
    std::puts("DirectInput force-feedback capability checks passed");
    return 0;
}
