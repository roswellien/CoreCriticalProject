#pragma once
#include <cstddef>
#include <cstdint>
#include <optional>
#include <span>
#include <string_view>

namespace mw34::version_resource {
// Raw RT_VERSION root queried by PM at 4B3043, without GetFileVersionInfo's
// extra ANSI conversion workspace. Only the fixed-info root query is admitted.
inline std::optional<std::size_t> raw_root_extent(std::span<const unsigned char> bytes) {
    if (bytes.size() < 92)
        return std::nullopt;
    const auto word = [&](std::size_t p) {
        return unsigned(bytes[p]) | (unsigned(bytes[p + 1]) << 8);
    };
    const unsigned length = word(0);
    if (length < 92 || length > bytes.size() || word(2) != 52 || word(4) != 0)
        return std::nullopt;
    constexpr std::string_view key = "VS_VERSION_INFO";
    for (std::size_t i = 0; i < key.size(); ++i)
        if (word(6 + 2 * i) != static_cast<unsigned char>(key[i]))
            return std::nullopt;
    if (word(6 + 2 * key.size()) != 0 || word(40) != 0x04bd || word(42) != 0xfeef)
        return std::nullopt;
    return length;
}
} // namespace mw34::version_resource
