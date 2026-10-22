// Project-authored process bootstrap. The compiler and Python are bundled;
// no game code or media are embedded in this executable.
#define WIN32_LEAN_AND_MEAN
#include <windows.h>
#include <cstdio>
#include <string>
#include <vector>

static std::wstring quote(const std::wstring &argument) {
    std::wstring result = L"\"";
    unsigned slashes = 0;
    for (const wchar_t value : argument) {
        if (value == L'\\') { ++slashes; continue; }
        if (value == L'\"') result.append(slashes * 2 + 1, L'\\');
        else result.append(slashes, L'\\');
        slashes = 0;
        result.push_back(value);
    }
    result.append(slashes * 2, L'\\');
    return result + L"\"";
}

int wmain(int argc, wchar_t **argv) {
    std::vector<wchar_t> filename(32768);
    const DWORD count = GetModuleFileNameW(nullptr, filename.data(), static_cast<DWORD>(filename.size()));
    if (!count || count >= filename.size()) return 2;
    const std::wstring full(filename.data(), count);
    const auto split = full.find_last_of(L"\\/");
    if (split == std::wstring::npos) return 2;
    const auto directory = full.substr(0, split);
    const auto python = directory + L"\\RuntimeBase\\python\\python.exe";
    std::wstring command = quote(python) + L" -B -u " + quote(directory + L"\\prepare_runtime.py");
    for (int index = 1; index < argc; ++index) command += L" " + quote(argv[index]);
    SetEnvironmentVariableW(L"PYTHONHOME", nullptr);
    SetEnvironmentVariableW(L"PYTHONPATH", nullptr);
    SetEnvironmentVariableW(L"PYTHONNOUSERSITE", L"1");
    STARTUPINFOW startup{};
    startup.cb = sizeof(startup);
    startup.dwFlags = STARTF_USESTDHANDLES;
    startup.hStdOutput = GetStdHandle(STD_OUTPUT_HANDLE);
    startup.hStdError = GetStdHandle(STD_ERROR_HANDLE);
    startup.hStdInput = GetStdHandle(STD_INPUT_HANDLE);
    PROCESS_INFORMATION process{};
    if (!CreateProcessW(python.c_str(), command.data(), nullptr, nullptr, TRUE, CREATE_NO_WINDOW,
                        nullptr, directory.c_str(), &startup, &process)) {
        std::fprintf(stderr, "The bundled native preparation runtime could not start (Windows error %lu).\n", GetLastError());
        return 2;
    }
    CloseHandle(process.hThread);
    WaitForSingleObject(process.hProcess, INFINITE);
    DWORD code = 2;
    GetExitCodeProcess(process.hProcess, &code);
    CloseHandle(process.hProcess);
    return static_cast<int>(code);
}
