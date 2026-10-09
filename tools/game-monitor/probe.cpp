// Authored Windows diagnostic fixture. Contains no game code or assets.
#include <cstdio>
#include <cstdint>
#include <cstdlib>
#include <filesystem>
#include <fstream>
#include <string>
#include <windows.h>

static LRESULT CALLBACK window_proc(HWND window, UINT message, WPARAM wparam, LPARAM lparam) {
    return DefWindowProcW(window, message, wparam, lparam);
}

static void pump() {
    MSG message{};
    while (PeekMessageW(&message, nullptr, 0, 0, PM_REMOVE)) {
        TranslateMessage(&message);
        DispatchMessageW(&message);
    }
}

static void handled_exception() {
    __try {
        RaiseException(0xe0003434, 0, 0, nullptr);
    } __except (EXCEPTION_EXECUTE_HANDLER) {
        OutputDebugStringA("MW34 probe: handled exception returned normally");
    }
}

int wmain(int argc, wchar_t **argv) {
    SetErrorMode(SEM_FAILCRITICALERRORS | SEM_NOGPFAULTERRORBOX);
    if (argc != 3) {
        return 2;
    }
    const std::wstring mode = argv[1];
    std::ofstream log(std::filesystem::path(argv[2]), std::ios::binary);
    log << "probe starting\n" << std::flush;
    Sleep(500);
    FILETIME now{};
    GetSystemTimePreciseAsFileTime(&now);
    const auto ticks =
        (static_cast<unsigned long long>(now.dwHighDateTime) << 32) | now.dwLowDateTime;
    char message[128];
    std::snprintf(message, sizeof(message), "MW34_LATENCY_UTC_MS=%llu",
                  ticks / 10000 - 11644473600000ULL);
    OutputDebugStringA(message);
    OutputDebugStringW(L"MW34 unicode probe: \u03a9");
    handled_exception();
    log << "ERROR: authored probe reports a recoverable issue\n" << std::flush;
    log << "partial" << std::flush;
    Sleep(200);
    log << " line complete\n" << std::flush;
    if (mode == L"crash") {
        // Raise an unhandled diagnostic exception; the debugger must not swallow it.
        RaiseException(0xe0003435, EXCEPTION_NONCONTINUABLE, 0, nullptr);
    } else if (mode == L"invalid-handle") {
        // A deliberately invalid, non-pseudo handle tests debugger-sensitive API behavior.
        // Do not handle the exception here: the debugger must forward it to the process.
        log << "probe closing deliberately invalid non-pseudo handle\n" << std::flush;
        SetLastError(ERROR_SUCCESS);
        const BOOL closed =
            CloseHandle(reinterpret_cast<HANDLE>(static_cast<std::uintptr_t>(0x34343434)));
        const DWORD error = GetLastError();
        log << "CloseHandle result=" << closed << " error=" << error << "\n" << std::flush;
        if (closed || error != ERROR_INVALID_HANDLE) {
            return 6;
        }
    } else if (mode == L"hang") {
        WNDCLASSW klass{};
        klass.hInstance = GetModuleHandleW(nullptr);
        klass.lpfnWndProc = window_proc;
        klass.lpszClassName = L"MW34MonitorHiddenProbe";
        if (!RegisterClassW(&klass)) {
            return 3;
        }
        const auto window =
            CreateWindowW(klass.lpszClassName, L"MW34 hidden test fixture", WS_OVERLAPPEDWINDOW, 0,
                          0, 160, 120, nullptr, nullptr, klass.hInstance, nullptr);
        if (!window) {
            return 4;
        }
        for (unsigned i = 0; i < 40; ++i) {
            pump();
            Sleep(50);
        }
        OutputDebugStringA("MW34 probe: deliberately stop pumping messages");
        Sleep(8000);
        for (unsigned i = 0; i < 40; ++i) {
            pump();
            Sleep(50);
        }
        DestroyWindow(window);
    } else if (mode == L"linger") {
        Sleep(30000);
    } else if (mode != L"normal") {
        return 5;
    }
    log << "probe done\n" << std::flush;
    return 0;
}
