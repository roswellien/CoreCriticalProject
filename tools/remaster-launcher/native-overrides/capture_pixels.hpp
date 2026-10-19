#pragma once
#include <cstdint>
#include <span>
#include <stdexcept>

namespace mw34::capture {
enum class ColorFormat { rgb565, rgba8 };

// Vulkan copies tightly packed source pixels. PNG/video consumers use BGRA8.
// Validate both extents before touching either buffer; never read padding as pixels.
inline void to_bgra(std::span<const std::uint8_t> source,
                    std::span<std::uint8_t> target, ColorFormat format) {
    const auto stride = format == ColorFormat::rgba8 ? 4U : 2U;
    if (target.size() % 4 || source.size() != target.size() / 4 * stride)
        throw std::runtime_error("Capture pixel buffer extent mismatch");
    for (std::size_t i = 0; i < target.size() / 4; ++i) {
        auto* out = target.data() + i * 4;
        if (format == ColorFormat::rgba8) {
            const auto* in = source.data() + i * 4;
            out[0] = in[2]; out[1] = in[1]; out[2] = in[0]; out[3] = 255;
        } else {
            const unsigned pixel = source[i * 2] | (unsigned(source[i * 2 + 1]) << 8);
            out[0] = std::uint8_t((pixel & 31) * 255 / 31);
            out[1] = std::uint8_t(((pixel >> 5) & 63) * 255 / 63);
            out[2] = std::uint8_t(((pixel >> 11) & 31) * 255 / 31);
            out[3] = 255;
        }
    }
}
}
