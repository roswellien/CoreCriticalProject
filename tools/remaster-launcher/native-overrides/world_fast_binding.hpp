#pragma once
#include <cstdint>

namespace mw34::world {
// Conservative admission for an unchanged original polygon submission. The
// caller still checks source ownership, corner count and reversed UV order.
inline bool unchanged_polygon(std::uint32_t clip_mask, std::uint32_t flags,
                              std::uint32_t depth_bias, std::uint32_t layers,
                              std::uint32_t special) {
    return !(clip_mask & 0x3f) && !(flags & 0x400) && !depth_bias && !layers && !special;
}
}
