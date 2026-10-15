#include "common.hpp"
#include <iostream>
using namespace mw34::m4_cmd_native;
static std::vector<std::byte> sentinel{std::byte{0x51}, std::byte{0x82}, std::byte{0xa3}};
static void create(const std::filesystem::path &p) {
    HANDLE h = CreateFileW(p.c_str(), GENERIC_WRITE, 0, nullptr, CREATE_NEW, FILE_ATTRIBUTE_NORMAL,
                           nullptr);
    require(h != INVALID_HANDLE_VALUE, "Own control sentinel creation failed");
    DWORD n{};
    require(WriteFile(h, sentinel.data(), 3, &n, nullptr) && n == 3 && CloseHandle(h),
            "Control sentinel write/close failed");
}
int main(int argc, char **argv) {
    try {
        require(argc == 2, "Private fresh publisher control dir");
        auto d = std::filesystem::path(argv[1]);
        require(!std::filesystem::exists(d), "Fresh publisher dir required");
        std::filesystem::create_directory(d);
        auto name = d / "result.bin";
        auto stage = std::filesystem::path(name.string() + ".cmd-stage-" +
                                           std::to_string(GetCurrentProcessId()));
        create(stage);
        bool reject{};
        try {
            Output out(name.string());
        } catch (const std::exception &) {
            reject = true;
        }
        require(reject && !std::filesystem::exists(name) && readfile(stage, 3) == sentinel,
                "Foreign stage deleted/changed or result published");
        std::filesystem::remove(stage);
        create(name);
        reject = false;
        try {
            Output out(name.string());
        } catch (const std::exception &) {
            reject = true;
        }
        require(reject && readfile(name, 3) == sentinel && !std::filesystem::exists(stage),
                "Foreign result deleted/changed");
        std::filesystem::remove(name);
        {
            Output out(name.string());
            out.write(sentinel.data(), 3);
            out.commit();
        }
        require(readfile(name, 3) == sentinel && !std::filesystem::exists(stage),
                "Normal exact output publication failed");
        std::cout << "{\"passed\":true,\"foreign_stage_preserved\":true,\"foreign_result_"
                     "preserved\":true,\"normal_owned_publication\":true}\n";
        return 0;
    } catch (const std::exception &e) {
        std::cerr << e.what() << '\n';
        return 1;
    }
}
