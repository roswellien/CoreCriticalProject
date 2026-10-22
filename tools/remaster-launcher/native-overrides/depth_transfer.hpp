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
// Depth begins at the next four-byte boundary after the color payload. Callers
// validate allocation sizes and leave room for this alignment before transfer.
inline std::size_t offset(std::size_t color_bytes) { return (color_bytes + 3) & ~std::size_t(3); }
inline void upload(unsigned char *destination, const std::uint16_t *source,
                   std::size_t sample_count) {
    // count is depth samples, not bytes. memcpy permits an unaligned staging
    // destination without casting it to float*. Buffer bounds belong to callers.
    for (std::size_t i = 0; i < sample_count; ++i) {
        const float value = float(source[i]) / 65535.f;
        std::memcpy(destination + i * sizeof(float), &value, sizeof(value));
    }
}
inline void readback(std::uint16_t *destination, const unsigned char *source,
                     std::size_t sample_count) {
    // Clamp finite normalized depth before quantizing to the guest's 16-bit ABI.
    // Reject NaN/Inf visibly. This loop is not transactional: an invalid later
    // sample can leave an already converted prefix in the destination.
    for (std::size_t i = 0; i < sample_count; ++i) {
        float value;
        std::memcpy(&value, source + i * sizeof(float), sizeof(value));
        if (!std::isfinite(value))
            throw std::runtime_error("Non-finite Vulkan depth readback");
        destination[i] = std::uint16_t(std::lround(std::clamp(value, 0.f, 1.f) * 65535.f));
    }
}
} // namespace mw34::depth
