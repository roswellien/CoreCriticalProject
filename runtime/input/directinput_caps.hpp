#pragma once
// Device capabilities the native host reports to the game's DirectInput joystick.
//
// MW3 1.2 (Mech3.exe SHA-256 95bc2c11...d916bf) reads DIDEVCAPS once after creating its joystick
// (GetCapabilities at VA 0x51d587) and decides force feedback from dwFlags & DIDC_FORCEFEEDBACK
// alone (0x51d59a). When that bit is set it opens the device exclusively and loads force_eff.ifr
// through IFORCE2.dll (VA 0x4807dc -> 0x433090); when it is clear it opens the device
// non-exclusively and never calls IFORCE2. The host implements no IFORCE2 service and no
// DirectInput effect objects, so it reports every device without force-feedback capabilities.
// The game then takes its own plain-joystick path instead of reaching an unimplemented service;
// nothing pretends an effect API succeeded.
#ifndef DIRECTINPUT_VERSION
#define DIRECTINPUT_VERSION 0x0700 // the version the native host's com_ddraw.hpp builds against
#endif
#include <windows.h>

#include <dinput.h>

namespace mw34::directinput {
// Every DIDEVCAPS flag that describes force-feedback support (DirectInput 5 and 7 headers).
inline constexpr DWORD force_feedback_flags =
    DIDC_FORCEFEEDBACK | DIDC_FFATTACK | DIDC_FFFADE | DIDC_SATURATION | DIDC_POSNEGCOEFFICIENTS |
    DIDC_POSNEGSATURATION | DIDC_DEADBAND | DIDC_STARTDELAY;

// Clears force-feedback support from a provider's successful report and returns whether the device
// reported any. Input fields stay as the device reported them; the force-feedback timing and driver
// fields read as zero, as they do for a device without force feedback.
inline bool hide_force_feedback(DIDEVCAPS &caps) {
    if (!(caps.dwFlags & force_feedback_flags))
        return false;
    caps.dwFlags &= ~force_feedback_flags;
    caps.dwFFSamplePeriod = 0;
    caps.dwFFMinTimeResolution = 0;
    caps.dwFFDriverVersion = 0;
    return true;
}
} // namespace mw34::directinput
