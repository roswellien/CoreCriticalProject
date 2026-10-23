#pragma once
#include "fixture_shadow.hpp"

namespace mw34::shadow_clip_reuse {
// Retain the existing corner transformation and plane arithmetic exactly.
// A corner has the same clip coordinates for all six planes of this face.
inline bool outside(const fixture_shadow::Clip& clip, const fixture_shadow::Bounds& bounds) {
    std::array<std::array<float, 4>, 8> corners{};
    for (unsigned corner = 0; corner < 8; ++corner) {
        const std::array<float, 4> p{
            (corner & 1) ? bounds.high[0] : bounds.low[0],
            (corner & 2) ? bounds.high[1] : bounds.low[1],
            (corner & 4) ? bounds.high[2] : bounds.low[2], 1};
        for (unsigned r = 0; r < 4; ++r)
            for (unsigned c = 0; c < 4; ++c)
                corners[corner][r] += clip[r * 4 + c] * p[c];
    }
    for (unsigned plane = 0; plane < 6; ++plane) {
        bool all = true;
        for (const auto& q : corners) {
            const float d = plane == 0 ? q[0] + q[3] : plane == 1 ? q[3] - q[0] :
                            plane == 2 ? q[1] + q[3] : plane == 3 ? q[3] - q[1] :
                            plane == 4 ? q[2] : q[3] - q[2];
            all &= d < 0;
        }
        if (all) return true;
    }
    return false;
}
} // namespace mw34::shadow_clip_reuse
