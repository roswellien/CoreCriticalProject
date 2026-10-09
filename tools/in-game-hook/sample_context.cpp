// Read-only diagnostic for the admitted user-owned game; no patch is installed.
#include "identity.hpp"
#include <psapi.h>
#include <algorithm>
#include <iostream>
using namespace mw34::hook;
int wmain(int argc, wchar_t **argv) {
    try {
        if (argc != 3) throw std::runtime_error("Usage: sample-context <MW3 pid> <thread id>");
        const auto pid = std::stoul(argv[1]); const auto tid = std::stoul(argv[2]);
        const auto process = OpenProcess(PROCESS_QUERY_INFORMATION | PROCESS_VM_READ, FALSE, pid);
        if (!process) throw std::runtime_error("Game process unavailable");
        std::array<wchar_t, 32768> path{};
        if (!GetModuleFileNameExW(process, nullptr, path.data(), static_cast<DWORD>(path.size())))
            throw std::runtime_error("Game filename unavailable");
        const auto image = admitted_image(path.data()); (void)image;
        const auto thread = OpenThread(THREAD_SUSPEND_RESUME | THREAD_GET_CONTEXT | THREAD_QUERY_INFORMATION, FALSE, tid);
        if (!thread || GetProcessIdOfThread(thread) != pid) throw std::runtime_error("Thread does not belong to admitted game");
        if (SuspendThread(thread) == static_cast<DWORD>(-1)) throw std::runtime_error("Thread sample hold failed");
        CONTEXT context{}; context.ContextFlags = CONTEXT_CONTROL | CONTEXT_INTEGER;
        const auto read = GetThreadContext(thread, &context);
        const auto resumed = ResumeThread(thread);
        CloseHandle(thread);
        if (!read || resumed == static_cast<DWORD>(-1)) throw std::runtime_error("Thread sample capture/resume failed");
        std::cout << std::hex << "EIP=" << context.Eip << " ESP=" << context.Esp << " EBP=" << context.Ebp
            << " EAX=" << context.Eax << " ECX=" << context.Ecx << " EDX=" << context.Edx
            << " EBX=" << context.Ebx << " ESI=" << context.Esi << " EDI=" << context.Edi << '\n';
        auto frame = context.Ebp;
        for (unsigned i = 0; i < 16; ++i) {
            std::uint32_t words[2]{}; SIZE_T read_bytes{};
            if (!ReadProcessMemory(process, reinterpret_cast<void *>(frame), words, sizeof(words), &read_bytes) || read_bytes != sizeof(words)) break;
            std::cout << "Frame=" << frame << " return=" << words[1] << '\n';
            if (words[0] <= frame || words[0] - frame > 0x100000) break;
            frame = words[0];
        }
        HMODULE modules[1024]{}; DWORD bytes{};
        if (EnumProcessModules(process, modules, sizeof(modules), &bytes)) {
            for (unsigned i = 0; i < std::min<unsigned>(bytes / sizeof(HMODULE), 1024); ++i) {
                MODULEINFO info{};
                if (GetModuleInformation(process, modules[i], &info, sizeof(info))) {
                    const auto base = reinterpret_cast<std::uintptr_t>(info.lpBaseOfDll);
                    if (context.Eip >= base && context.Eip < base + info.SizeOfImage) {
                        GetModuleFileNameExW(process, modules[i], path.data(), static_cast<DWORD>(path.size()));
                        std::wcout << "Module=" << path.data() << " RVA=" << context.Eip - base << '\n';
                    }
                }
            }
        }
        CloseHandle(process); return 0;
    } catch (const std::exception &e) { std::cerr << e.what() << '\n'; return 1; }
}
