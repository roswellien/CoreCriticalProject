#define NOMINMAX
#include <windows.h>
#include <winioctl.h>
#include "native-overrides/large_texture_seek.hpp"
#include <array>
#include <iostream>
#include <stdexcept>

int main() {
    using mw34::texture_banks::unsigned_archive_seek;
    unsigned checks = 0;
    auto check = [&](bool value) {
        ++checks;
        if (!value) throw std::runtime_error("Large texture seek check failed");
    };
    constexpr std::array<unsigned, 3> chain{0x518e08, 0x78022662, 0x78012115};
    constexpr std::array<unsigned, 1> unrelated{0x78012115};
    for (unsigned at : {0x80000040U, 0xba0b0000U, 0xffffff00U}) {
        check(unsigned_archive_seek(true, at, 0, FILE_BEGIN, chain));
        check(!unsigned_archive_seek(false, at, 0, FILE_BEGIN, chain));
        check(!unsigned_archive_seek(true, at, 4, FILE_BEGIN, chain));
        check(!unsigned_archive_seek(true, at, 0, FILE_CURRENT, chain));
        check(!unsigned_archive_seek(true, at, 0, FILE_END, chain));
        check(!unsigned_archive_seek(true, at, 0, FILE_BEGIN, unrelated));
    }
    check(!unsigned_archive_seek(true, 0x7fffffff, 0, FILE_BEGIN, chain));
    const std::array<unsigned, 1> no_crt{0x518e08};
    check(!unsigned_archive_seek(true, 0x80000040, 0, FILE_BEGIN, no_crt));

    wchar_t directory[MAX_PATH], name[MAX_PATH];
    check(GetTempPathW(MAX_PATH, directory) != 0);
    check(GetTempFileNameW(directory, L"mws", 0, name) != 0);
    HANDLE file = CreateFileW(name, GENERIC_READ | GENERIC_WRITE, 0, nullptr,
                             CREATE_ALWAYS, FILE_ATTRIBUTE_TEMPORARY | FILE_FLAG_DELETE_ON_CLOSE,
                             nullptr);
    check(file != INVALID_HANDLE_VALUE);
    try {
        DWORD count = 0;
        check(DeviceIoControl(file, FSCTL_SET_SPARSE, nullptr, 0, nullptr, 0, &count, nullptr));
        // An authored 16-byte descriptor, stored beyond the signed-long limit.
        constexpr std::array<unsigned, 4> header{5, 0x00400040, 0, 0};
        constexpr unsigned offset = 0xba0b0000;
        LARGE_INTEGER position{};
        position.QuadPart = offset;
        check(SetFilePointerEx(file, position, nullptr, FILE_BEGIN));
        check(WriteFile(file, header.data(), sizeof header, &count, nullptr) && count == sizeof header);
        check(SetFilePointer(file, 0, nullptr, FILE_BEGIN) == 0);
        SetLastError(0);
        check(SetFilePointer(file, LONG(offset), nullptr, FILE_BEGIN) == INVALID_SET_FILE_POINTER);
        check(GetLastError() == ERROR_NEGATIVE_SEEK);
        LONG high = 0;
        check(SetFilePointer(file, LONG(offset), &high, FILE_BEGIN) == offset && high == 0);
        std::array<unsigned, 4> actual{};
        check(ReadFile(file, actual.data(), sizeof actual, &count, nullptr));
        check(actual == header && count == sizeof header);
        check(SetFilePointer(file, -16, nullptr, FILE_CURRENT) == offset);
    } catch (...) {
        CloseHandle(file);
        throw;
    }
    check(CloseHandle(file));
    std::cout << "large texture seek checks=" << checks << " failures=0\n";
}
