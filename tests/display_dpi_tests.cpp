#include "graphics/display_dpi.hpp"
#include <cassert>
#include <cstdio>

int main() {
    ::SetLastError(4321);
    mw34::display::require_native_coordinates();
    assert(::GetLastError() == 4321);
    // A hidden authored window checks that native client and screen coordinates
    // agree. It never captures, clips or moves the user's real mouse.
    HWND window = ::CreateWindowExW(0, L"STATIC", L"DPI coordinate fixture",
                                  WS_POPUP, 20, 30, 400, 300,
                                  nullptr, nullptr, ::GetModuleHandleW(nullptr), nullptr);
    assert(window);
    assert(::AreDpiAwarenessContextsEqual(::GetWindowDpiAwarenessContext(window),
                                         DPI_AWARENESS_CONTEXT_PER_MONITOR_AWARE_V2));
    RECT client{};
    assert(::GetClientRect(window, &client));
    assert(client.right == 400 && client.bottom == 300);
    POINT center{200, 150};
    assert(::ClientToScreen(window, &center));
    assert(center.x == 220 && center.y == 180);
    assert(::ScreenToClient(window, &center));
    assert(center.x == 200 && center.y == 150);
    const unsigned dpi = ::GetDpiForWindow(window);
    assert(::DestroyWindow(window));
    // Explicit compatibility overrides must be diagnosed before guest startup.
    auto previous = ::SetThreadDpiAwarenessContext(DPI_AWARENESS_CONTEXT_UNAWARE);
    assert(previous);
    bool rejected = false;
    try { mw34::display::require_native_coordinates(); }
    catch (const std::runtime_error&) { rejected = true; }
    assert(rejected);
    assert(::SetThreadDpiAwarenessContext(previous));
    std::printf("Native DPI context, hidden-window center, override rejection and last-error preservation passed (local monitor DPI %u).\n", dpi);
}
