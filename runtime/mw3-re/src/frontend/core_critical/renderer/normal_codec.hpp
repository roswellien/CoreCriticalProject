#pragma once
#include "platform/loading.hpp"
#include <cstddef>
#include <cstdint>
#include <cstring>
#include <stdexcept>
#include <string>
#include <vector>

// The non-Windows header contract is also compiled by MSVC without POSIX
// headers. Optional disk storage must not make the codec depend on that OS.
#if defined(_WIN32) || __has_include(<sys/file.h>)
#include "platform/derived_cache.hpp"
#define MW3_NORMAL_DISK_CACHE_AVAILABLE 1
#endif

namespace mw34::materials {
// BWNRM3 lossless channel-delta/byte-run codec. Decode directly into the final
// interleaved pixel allocation; malformed tokens cannot grow that allocation.
inline void decode_normal_pixels(const std::vector<unsigned char> &encoded, unsigned char *output,
                                 std::size_t pixel_bytes) {
    platform::loading::Measure timing(platform::loading::Work::normal, pixel_bytes);
    auto fail = [] { throw std::runtime_error("Invalid compressed normal pixels"); };
    if (!pixel_bytes || pixel_bytes % 4 || pixel_bytes > 256ULL * 1024 * 1024 || encoded.empty() ||
        encoded.size() > pixel_bytes * 2)
        fail();

#if defined(MW3_NORMAL_DISK_CACHE_AVAILABLE)
    // Key over full encoded input plus pixel_bytes and codec version/domain.
    std::string cache_key;
    bool key_valid = false;
    try {
        if (platform::derived_cache::default_cache().is_enabled()) {
            platform::derived_cache::KeyBuilder kb("mw34_bwnrm3_normal_pixels_v1");
            const uint64_t pb = static_cast<uint64_t>(pixel_bytes);
            kb.update_pod(pb);
            kb.update(encoded.data(), encoded.size());
            cache_key = kb.hex();
            key_valid = true;
        }
    } catch (...) {
        key_valid = false;
    }

    if (key_valid) {
        try {
            if (platform::derived_cache::default_cache().read(cache_key, output, pixel_bytes)) {
                timing.hit = true;
                return;
            }
        } catch (...) {
            // Fall through to decode on cache read error
        }
    }

#endif
    const auto pixels = pixel_bytes / 4;
    std::size_t cursor{}, decoded{};
    unsigned char previous[4]{};
    std::size_t checkpoint_at = 0;
    while (cursor < encoded.size()) {
        if (decoded >= checkpoint_at) {
            platform::loading::checkpoint();
            checkpoint_at = decoded + 65536;
        }
        const auto token = encoded[cursor++];
        const std::size_t count = (token & ((token & 128) ? 63 : 127)) + 1;
        if (count > pixel_bytes - decoded)
            fail();
        const bool nibble = token >= 192;
        const bool repeat = token >= 128 && !nibble;
        const auto stored = nibble ? (count + 1) / 2 : repeat ? 1 : count;
        if (stored > encoded.size() - cursor)
            fail();
        if (nibble && count % 2 && (encoded[cursor + stored - 1] & 15))
            fail();
        for (std::size_t i = 0; i < count; ++i) {
            const auto channel = decoded / pixels;
            const auto index = decoded % pixels;
            unsigned value = encoded[cursor + (nibble ? i / 2 : repeat ? 0 : i)];
            if (nibble) {
                value = (value >> (i % 2 ? 0 : 4)) & 15;
                if (value >= 8)
                    value += 240;
            }
            previous[channel] = static_cast<unsigned char>(previous[channel] + value);
            output[index * 4 + channel] = previous[channel];
            ++decoded;
        }
        cursor += stored;
    }
    if (decoded != pixel_bytes)
        fail();

#if defined(MW3_NORMAL_DISK_CACHE_AVAILABLE)
    // Cache only after successful decode; malformed tokens never reach this point.
    if (key_valid) {
        try {
            platform::derived_cache::default_cache().write(cache_key, output, pixel_bytes);
        } catch (...) {
            // Non-fatal write failure
        }
    }
#endif
}
} // namespace mw34::materials

namespace mw34::normals {
using mw34::materials::decode_normal_pixels;
} // namespace mw34::normals
