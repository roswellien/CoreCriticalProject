#include "version_resource.hpp"
#include <array>
#include <iostream>
#include <stdexcept>
#include <windows.h>

int main() {
    try {
        std::array<unsigned char, 256> bytes{};
        auto word = [&](unsigned p, unsigned v) {
            bytes[p] = static_cast<unsigned char>(v);
            bytes[p + 1] = static_cast<unsigned char>(v >> 8);
        };
        word(0, unsigned(bytes.size()));
        word(2, 52);
        constexpr std::string_view key = "VS_VERSION_INFO";
        for (unsigned i = 0; i < key.size(); ++i)
            word(6 + 2 * i, static_cast<unsigned char>(key[i]));
        word(40, 0x04bd);
        word(42, 0xfeef);
        if (mw34::version_resource::raw_root_extent(bytes) != bytes.size())
            throw std::runtime_error("Authored raw resource rejected");
        const auto before = bytes;
        void *value{};
        UINT length{};
        if (!::VerQueryValueA(bytes.data(), "\\", &value, &length) || value != bytes.data() + 40 ||
            length != 52 || bytes != before)
            throw std::runtime_error(
                "Real Windows raw-root query differs from the supported contract");
        for (unsigned variant = 0; variant < 5; ++variant) {
            bytes = before;
            if (variant == 0)
                word(0, 300);
            if (variant == 1)
                word(0, 90);
            if (variant == 2)
                word(2, 51);
            if (variant == 3)
                word(6, 'X');
            if (variant == 4)
                word(40, 0);
            if (mw34::version_resource::raw_root_extent(bytes))
                throw std::runtime_error("Malformed/unsupported raw resource admitted");
        }
        std::cout << "Raw version resource: Windows oracle and 5 rejection controls pass\n";
        return 0;
    } catch (const std::exception &error) {
        std::cerr << error.what() << '\n';
        return 1;
    }
}
