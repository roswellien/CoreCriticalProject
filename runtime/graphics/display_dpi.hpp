#pragma once
#include <cstdio>
#include <stdexcept>
#include <windows.h>

namespace mw34::display {
// The embedded manifest establishes the coordinate space before any HWND or
// original initialization runs. Do not attempt a late process DPI-mode switch.
inline void require_native_coordinates() {
    const DWORD saved_error = ::GetLastError();
    const auto context = ::GetThreadDpiAwarenessContext();
    const bool native = ::AreDpiAwarenessContextsEqual(
                            context, DPI_AWARENESS_CONTEXT_PER_MONITOR_AWARE_V2) != FALSE;
    std::fprintf(stderr, "Native display coordinates: PerMonitorV2=%u\n", unsigned(native));
    ::SetLastError(saved_error);
    if (!native)
        throw std::runtime_error(
            "Native display DPI awareness is unavailable. Remove any Windows High DPI "
            "compatibility override for entry_commandline.exe and retry.");
}
} // namespace mw34::display
