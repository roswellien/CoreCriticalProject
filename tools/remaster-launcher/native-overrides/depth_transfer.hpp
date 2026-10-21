#pragma once
#include <algorithm>
#include <cmath>
#include <cstddef>
#include <cstdint>
#include <cstring>
#include <stdexcept>

namespace mw34::depth {
// Guest DirectDraw surfaces retain their 16-bit ABI. Vulkan staging and
// attachments carry normalized 32-bit floats, including at scaled resolutions.
inline std::size_t offset(std::size_t color_bytes) { return (color_bytes + 3) & ~std::size_t(3); }
inline void upload(unsigned char* dst, const std::uint16_t* src, std::size_t count) {
    for (std::size_t i = 0; i < count; ++i) {
        const float value = float(src[i]) / 65535.f;
        std::memcpy(dst + i * sizeof(float), &value, sizeof(value));
    }
}
inline void readback(std::uint16_t* dst, const unsigned char* src, std::size_t count) {
    for (std::size_t i = 0; i < count; ++i) {
        float value;
        std::memcpy(&value, src + i * sizeof(float), sizeof(value));
        if (!std::isfinite(value)) throw std::runtime_error("Non-finite Vulkan depth readback");
        dst[i] = std::uint16_t(std::lround(std::clamp(value, 0.f, 1.f) * 65535.f));
    }
}
}
