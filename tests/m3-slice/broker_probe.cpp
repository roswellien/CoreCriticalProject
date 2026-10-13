// Asset-free executable: exercise pre-CRT reservations without guest code.
#include "../../tools/m3-slice/original_broker.hpp"
#include <cstring>

int main(int argc, char **argv) {
    try {
        using namespace mw34::original_broker;
        if (argc == 2 && std::string_view(argv[1]) == "--unbrokered") {
            try {
                reserve_or_adopt(0x558000);
            } catch (const std::exception &) {
                std::cout << "Unbrokered reservation rejected\n";
                return 0;
            }
            throw std::runtime_error("Unbrokered reservation admitted");
        }
        if (auto result = dispatch(argc, argv, 3))
            return *result;
        require(argc == 3 && std::string_view(argv[1]) == "--probe", "Probe CLI differs");
        require(adopting, "Positive probe executed without child reservation proof");
        unsigned checks{};
        for (const auto base : bases) {
            auto *region = reserve_or_adopt(base);
            ++checks;
            auto *page = VirtualAlloc(region, 4096, MEM_COMMIT, PAGE_READWRITE);
            require(page == region, "Probe exact child commit failed");
            ++checks;
            std::memset(page, 0x34, 4096);
            require(static_cast<unsigned char *>(page)[4095] == 0x34,
                    "Probe committed memory differs");
            ++checks;
            MEMORY_BASIC_INFORMATION remaining{};
            require(VirtualQuery(static_cast<unsigned char *>(region) + 4096, &remaining,
                                 sizeof(remaining)) == sizeof(remaining) &&
                        remaining.AllocationBase == region && remaining.State == MEM_RESERVE &&
                        remaining.AllocationProtect == PAGE_NOACCESS,
                    "Probe surrounding guard reservation changed");
            ++checks;
        }
        try {
            reserve_or_adopt(0x33000000);
        } catch (const std::exception &) {
            ++checks;
        }
        require(checks == 17, "Probe unreviewed reservation admitted");
        std::cout << "Broker reservation controls: " << checks << "\n";
        if (std::string_view(argv[2]) == "return17")
            return 17;
        require(std::string_view(argv[2]) == "return0", "Probe exit request differs");
        return 0;
    } catch (const std::exception &error) {
        std::cerr << error.what() << '\n';
        return 1;
    }
}
