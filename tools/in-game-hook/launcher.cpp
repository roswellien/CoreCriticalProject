#include "identity.hpp"
#include <tlhelp32.h>
#include <iostream>

using namespace mw34::hook;
struct Handle {
    HANDLE value{};
    ~Handle() { if (value && value != INVALID_HANDLE_VALUE) CloseHandle(value); }
};
using Entry = DWORD(WINAPI *)(void *);
static std::uintptr_t remote_module(DWORD pid, const std::wstring &name) {
    HANDLE raw = INVALID_HANDLE_VALUE;
    for (unsigned attempt = 0; attempt < 100; ++attempt) {
        raw = CreateToolhelp32Snapshot(TH32CS_SNAPMODULE, pid);
        if (raw != INVALID_HANDLE_VALUE || GetLastError() != ERROR_BAD_LENGTH) break;
        Sleep(10); // Documented retry for a module list changing during capture.
    }
    Handle snapshot{raw};
    if (snapshot.value == INVALID_HANDLE_VALUE) throw std::runtime_error("Remote module snapshot failed");
    MODULEENTRY32W module{}; module.dwSize = sizeof(module);
    for (BOOL found = Module32FirstW(snapshot.value, &module); found; found = Module32NextW(snapshot.value, &module))
        if (_wcsicmp(module.szModule, name.c_str()) == 0) return reinterpret_cast<std::uintptr_t>(module.modBaseAddr);
    throw std::runtime_error("Required remote system module unavailable");
}
static DWORD remote_call(HANDLE process, std::uintptr_t entry, void *argument) {
    Handle thread{CreateRemoteThread(process, nullptr, 0, reinterpret_cast<LPTHREAD_START_ROUTINE>(entry), argument, 0, nullptr)};
    if (!thread.value) throw std::runtime_error("Research initialization thread failed");
    if (WaitForSingleObject(thread.value, 30000) != WAIT_OBJECT_0) throw std::runtime_error("Research initialization timed out");
    DWORD result{};
    if (!GetExitCodeThread(thread.value, &result)) throw std::runtime_error("Research initialization result unavailable");
    return result;
}
static void write_breakpoint_byte(HANDLE process, std::uint8_t value) {
    auto *entry = reinterpret_cast<void *>(0x5ac3a0);
    DWORD old{}, ignored{}; SIZE_T written{};
    if (!VirtualProtectEx(process, entry, 1, PAGE_EXECUTE_READWRITE, &old) ||
        !WriteProcessMemory(process, entry, &value, 1, &written) || written != 1 ||
        !VirtualProtectEx(process, entry, 1, old, &ignored) ||
        !FlushInstructionCache(process, entry, 1))
        throw std::runtime_error("Temporary entry breakpoint update failed");
}
static void initialize_loader(DWORD pid, DWORD main_tid, HANDLE main_thread, HANDLE process) {
    // Initial loader breakpoints may occur while the loader lock is held.
    // Break at the exact admitted game entry instead: initialization has then
    // completed on the normal thread and LoadLibrary can run on a helper thread.
    const auto deadline = GetTickCount64() + 30000;
    std::uint8_t original{};
    bool breakpoint_installed = false;
    while (GetTickCount64() < deadline) {
        DEBUG_EVENT event{};
        if (!WaitForDebugEvent(&event, 1000)) {
            if (GetLastError() == ERROR_SEM_TIMEOUT) continue;
            throw std::runtime_error("Pre-entry debug event failed");
        }
        if (event.dwDebugEventCode == CREATE_PROCESS_DEBUG_EVENT && event.u.CreateProcessInfo.hFile)
            CloseHandle(event.u.CreateProcessInfo.hFile);
        if (event.dwDebugEventCode == CREATE_PROCESS_DEBUG_EVENT) {
            SIZE_T read{};
            if (reinterpret_cast<std::uintptr_t>(event.u.CreateProcessInfo.lpBaseOfImage) != 0x400000 ||
                !ReadProcessMemory(process, reinterpret_cast<void *>(0x5ac3a0), &original, 1, &read) || read != 1)
                throw std::runtime_error("Admitted game entry is unavailable");
            write_breakpoint_byte(process, 0xcc);
            breakpoint_installed = true;
        }
        if (event.dwDebugEventCode == LOAD_DLL_DEBUG_EVENT && event.u.LoadDll.hFile)
            CloseHandle(event.u.LoadDll.hFile);
        const bool ready = event.dwDebugEventCode == EXCEPTION_DEBUG_EVENT &&
            event.u.Exception.ExceptionRecord.ExceptionCode == EXCEPTION_BREAKPOINT &&
            reinterpret_cast<std::uintptr_t>(event.u.Exception.ExceptionRecord.ExceptionAddress) == 0x5ac3a0 &&
            event.dwThreadId == main_tid && event.dwProcessId == pid;
        const bool exited = event.dwDebugEventCode == EXIT_PROCESS_DEBUG_EVENT;
        if (ready) {
            if (!breakpoint_installed) throw std::runtime_error("Unexpected game entry breakpoint");
            CONTEXT context{}; context.ContextFlags = CONTEXT_CONTROL;
            if (!GetThreadContext(main_thread, &context) || context.Eip != 0x5ac3a1)
                throw std::runtime_error("Game entry context differs from breakpoint contract");
            write_breakpoint_byte(process, original);
            context.Eip = 0x5ac3a0;
            if (!SetThreadContext(main_thread, &context) || SuspendThread(main_thread) == static_cast<DWORD>(-1))
                throw std::runtime_error("Pre-entry main thread hold failed");
        }
        const bool system_break = event.dwDebugEventCode == EXCEPTION_DEBUG_EVENT &&
            event.u.Exception.ExceptionRecord.ExceptionCode == EXCEPTION_BREAKPOINT;
        const auto status = event.dwDebugEventCode == EXCEPTION_DEBUG_EVENT && !system_break ? DBG_EXCEPTION_NOT_HANDLED : DBG_CONTINUE;
        if (!ContinueDebugEvent(event.dwProcessId, event.dwThreadId, status))
            throw std::runtime_error("Pre-entry debug continuation failed");
        if (exited) throw std::runtime_error("Game exited before loader breakpoint");
        if (ready) {
            if (!DebugActiveProcessStop(pid)) throw std::runtime_error("Pre-entry debugger detach failed");
            return;
        }
    }
    throw std::runtime_error("Pre-entry loader breakpoint timed out");
}
int wmain(int argc, wchar_t **argv) {
    try {
        const bool selftest = argc == 5 && std::wstring(argv[1]) == L"--selftest";
        if ((!selftest && argc != 4) || (selftest && argc != 5))
            throw std::runtime_error("Usage: launcher [--selftest] <Mech3.exe> <authored-hook.dll> <new-log.jsonl>");
        const auto index = selftest ? 2 : 1;
        const auto game = std::filesystem::absolute(argv[index]).wstring();
        const auto dll = std::filesystem::absolute(argv[index + 1]).wstring();
        const auto log = std::filesystem::absolute(argv[index + 2]).wstring();
        // Full supported-image admission always precedes creation of a game process.
        const auto image = admitted_image(game);
        (void)image;
        if (std::filesystem::exists(log)) throw std::runtime_error("Log already exists; use a fresh run directory");
        if (!SetEnvironmentVariableW(L"MW34_GAME_FILE", game.c_str()) || !SetEnvironmentVariableW(L"MW34_HOOK_LOG", log.c_str()))
            throw std::runtime_error("Research environment setup failed");
        // This is our built DLL. Its DllMain performs no installation or I/O.
        auto local = LoadLibraryW(dll.c_str());
        if (!local) throw std::runtime_error("Authored hook DLL could not load");
        const auto selftest_entry = reinterpret_cast<Entry>(GetProcAddress(local, "mw34_selftest"));
        const auto install_entry = GetProcAddress(local, "mw34_install");
        if (!selftest_entry || !install_entry) throw std::runtime_error("Authored hook exports missing");
        if (selftest) {
            const auto result = selftest_entry(nullptr);
            std::cout << "Selftest status: " << result << '\n';
            FreeLibrary(local);
            return result == 0 ? 0 : 1;
        }
        STARTUPINFOW startup{}; startup.cb = sizeof(startup);
        wchar_t desktop[] = L"WinSta0\\Default";
        startup.lpDesktop = desktop;
        PROCESS_INFORMATION info{};
        auto command = L"\"" + game + L"\"";
        const auto working = std::filesystem::path(game).parent_path().wstring();
        if (!CreateProcessW(game.c_str(), command.data(), nullptr, nullptr, FALSE, DEBUG_ONLY_THIS_PROCESS,
                            nullptr, working.c_str(), &startup, &info))
            throw std::runtime_error("Pre-entry game launch failed");
        Handle process{info.hProcess}, main_thread{info.hThread};
        try {
            initialize_loader(info.dwProcessId, info.dwThreadId, main_thread.value, process.value);
            // Resolve the actual owning DLL (LoadLibraryW may be forwarded), then
            // use the matching remote module base and export offset.
            const auto loader = GetProcAddress(GetModuleHandleW(L"kernel32.dll"), "LoadLibraryW");
            HMODULE owner{};
            if (!loader || !GetModuleHandleExW(GET_MODULE_HANDLE_EX_FLAG_FROM_ADDRESS | GET_MODULE_HANDLE_EX_FLAG_UNCHANGED_REFCOUNT,
                    reinterpret_cast<LPCWSTR>(loader), &owner))
                throw std::runtime_error("Loader owner unavailable");
            std::array<wchar_t, 32768> owner_path{};
            if (!GetModuleFileNameW(owner, owner_path.data(), static_cast<DWORD>(owner_path.size())))
                throw std::runtime_error("Loader owner filename unavailable");
            const auto remote_owner = remote_module(info.dwProcessId, std::filesystem::path(owner_path.data()).filename().wstring());
            const auto remote_loader = remote_owner + reinterpret_cast<std::uintptr_t>(loader) - reinterpret_cast<std::uintptr_t>(owner);
            const auto size = (dll.size() + 1) * sizeof(wchar_t);
            auto *remote_name = VirtualAllocEx(process.value, nullptr, size, MEM_RESERVE | MEM_COMMIT, PAGE_READWRITE);
            SIZE_T written{};
            if (!remote_name || !WriteProcessMemory(process.value, remote_name, dll.c_str(), size, &written) || written != size)
                throw std::runtime_error("Research DLL path staging failed");
            const auto remote_dll = remote_call(process.value, remote_loader, remote_name);
            VirtualFreeEx(process.value, remote_name, 0, MEM_RELEASE);
            if (!remote_dll) throw std::runtime_error("Research DLL did not load in game");
            const auto initializer = remote_dll + reinterpret_cast<std::uintptr_t>(install_entry) - reinterpret_cast<std::uintptr_t>(local);
            if (remote_call(process.value, initializer, nullptr) != 0)
                throw std::runtime_error("Hash-bound hook installation/selftest failed");
            if (ResumeThread(main_thread.value) == static_cast<DWORD>(-1)) throw std::runtime_error("Game resume failed");
            std::cout << "Hook installed before entry point; game resumed. PID=" << info.dwProcessId << '\n';
            std::wcout << "Evidence log: " << log << '\n';
        } catch (...) {
            // Only this launcher's own, still-suspended process is canceled.
            TerminateProcess(process.value, 92);
            WaitForSingleObject(process.value, 5000);
            throw;
        }
        FreeLibrary(local);
        return 0;
    } catch (const std::exception &error) {
        std::cerr << "Hook launcher failed: " << error.what() << " (Win32 " << GetLastError() << ")\n";
        return 1;
    }
}
