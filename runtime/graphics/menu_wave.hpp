#pragma once

#include <algorithm>
#include <bit>
#include <cmath>
#include <cstdint>
#include <vector>

namespace mw34::menu {

// Presentation companion to the original rollover rasterizer (VA 0x558DD0).
// The game owns the trigger, radii and phase. This map only transports its
// displacement to the enhanced canvas; it never advances animation time.
struct Wave {
    int x{}, y{}, inner{}, outer{}, amplitude{};
    float period{}, phase{};
    int left{}, top{}, right{639}, bottom{479};

    bool valid() const {
        return x >= -512 && x <= 1152 && y >= -512 && y <= 992 && outer >= 0 && outer <= 512 &&
               amplitude >= 0 && amplitude <= 64 && std::isfinite(period) && period > 0 &&
               std::isfinite(phase) && left >= 0 && top >= 0 && right >= left && bottom >= top &&
               right <= 640 && bottom <= 480;
    }
};

struct Offset {
    int x{}, y{};
    bool raster{};
};

inline std::vector<Offset> wave_map(const Wave &wave) {
    std::vector<Offset> result(640 * 480);
    if (!wave.valid())
        return result;
    const int outer = wave.outer;
    const int inner = std::clamp(wave.inner, 0, outer);
    if (inner == outer || !wave.amplitude)
        return result;
    std::vector<double> scale(static_cast<std::size_t>(outer) + 1);
    for (int r = std::max(1, inner - 1); r <= outer; ++r) {
        const float sine = static_cast<float>(
            std::sin(double(r) / double(wave.period) + double(wave.phase)) * wave.amplitude);
        const float inverse = 1.0f / static_cast<float>(r);
        scale[static_cast<std::size_t>(r)] = double(sine) * double(inverse);
    }
    for (int y = std::max(wave.top, wave.y - outer); y < std::min(wave.bottom, wave.y + outer);
         ++y) {
        // Preserve the rasterizer's absolute-coordinate inner-square copy gate.
        if (y >= -inner && y <= inner)
            continue;
        const int begin = std::max(wave.left, wave.x - outer);
        const int end = std::min(wave.right, wave.x + outer);
        // Skipped columns do not advance the original copy pointers. Its
        // resulting copied interval starts at begin and is shortened at right.
        const int skipped = std::clamp(inner + 1 - begin, 0, std::max(0, end - begin));
        for (int x = begin; x < end - skipped; ++x) {
            const int rx = x - wave.x, ry = y - wave.y;
            const int squared = rx * rx + ry * ry;
            if (squared <= inner * inner || squared >= outer * outer)
                continue;
            // The original uses this float-bit radius estimate, not sqrt().
            const auto bits = (std::bit_cast<std::uint32_t>(float(squared)) >> 1) + 0x1fc00000u;
            const int radius = std::min(outer, int(std::bit_cast<float>(bits)));
            const double amount = scale[static_cast<std::size_t>(radius)];
            const Offset offset{int(amount * rx), int(amount * ry)};
            const int sx = x + offset.x, sy = y + offset.y;
            if (sx < wave.left || sx >= wave.right || sy < wave.top || sy >= wave.bottom) {
                // The clipped rasterizer leaves an old scratch pixel here.
                // Its real post-call pixel must be retained by the presenter.
                result[static_cast<std::size_t>(y) * 640 + x].raster = true;
                continue;
            }
            result[static_cast<std::size_t>(y) * 640 + x] = offset;
        }
    }
    return result;
}

// Source and destination must differ: every displacement samples the same
// pre-wave canvas, including when several waves overlap in one frame.
inline void warp_rgba(const std::vector<std::uint32_t> &source,
                      std::vector<std::uint32_t> &destination, unsigned width, unsigned height,
                      const std::vector<Offset> &map,
                      const std::vector<std::uint32_t> *raster = nullptr) {
    if (source.size() != std::size_t(width) * height || !width || !height ||
        map.size() != 640 * 480)
        return;
    destination = source;
    unsigned left = 640, top = 480, right = 0, bottom = 0;
    for (unsigned y = 0; y < 480; ++y) {
        for (unsigned x = 0; x < 640; ++x) {
            const auto d = map[y * 640 + x];
            if (!d.x && !d.y && !d.raster)
                continue;
            left = std::min(left, x);
            top = std::min(top, y);
            right = std::max(right, x + 1);
            bottom = std::max(bottom, y + 1);
        }
    }
    if (left == 640)
        return;
    // Expand for interpolation between the logical displacement samples.
    const unsigned xbegin = unsigned(std::max(0.0, std::floor((double(left) - 1) * width / 640)));
    const unsigned xend = std::min(width, unsigned(std::ceil((double(right) + 1) * width / 640)));
    const unsigned ybegin = unsigned(std::max(0.0, std::floor((double(top) - 1) * height / 480)));
    const unsigned yend =
        std::min(height, unsigned(std::ceil((double(bottom) + 1) * height / 480)));
    for (unsigned y = ybegin; y < yend; ++y) {
        const double gy = std::clamp((double(y) + .5) * 480 / height - .5, 0.0, 479.0);
        const unsigned y0 = unsigned(gy), y1 = std::min(y0 + 1, 479u);
        const double fy = gy - y0;
        for (unsigned x = xbegin; x < xend; ++x) {
            const double gx = std::clamp((double(x) + .5) * 640 / width - .5, 0.0, 639.0);
            const unsigned x0 = unsigned(gx), x1 = std::min(x0 + 1, 639u);
            const double fx = gx - x0;
            const Offset q[]{map[y0 * 640 + x0], map[y0 * 640 + x1], map[y1 * 640 + x0],
                             map[y1 * 640 + x1]};
            const unsigned nearest = unsigned(gy + .5) * 640 + unsigned(gx + .5);
            if (map[nearest].raster && raster && raster->size() == map.size()) {
                destination[std::size_t(y) * width + x] = (*raster)[nearest];
                continue;
            }
            auto mix = [&](bool vertical) {
                auto v = [&](unsigned i) { return vertical ? q[i].y : q[i].x; };
                return (v(0) * (1 - fx) + v(1) * fx) * (1 - fy) +
                       (v(2) * (1 - fx) + v(3) * fx) * fy;
            };
            const double dx = mix(false), dy = mix(true);
            if (dx == 0 && dy == 0)
                continue;
            const double sx = std::clamp(double(x) + dx * width / 640, 0.0, double(width - 1));
            const double sy = std::clamp(double(y) + dy * height / 480, 0.0, double(height - 1));
            const unsigned ix = unsigned(sx), iy = unsigned(sy);
            const unsigned jx = std::min(ix + 1, width - 1), jy = std::min(iy + 1, height - 1);
            const double tx = sx - ix, ty = sy - iy;
            const std::uint32_t pixels[]{
                source[std::size_t(iy) * width + ix], source[std::size_t(iy) * width + jx],
                source[std::size_t(jy) * width + ix], source[std::size_t(jy) * width + jx]};
            std::uint32_t color = 0xff000000u;
            for (unsigned k = 0; k < 3; ++k) {
                auto c = [&](unsigned i) { return double((pixels[i] >> (8 * k)) & 255); };
                const double value =
                    (c(0) * (1 - tx) + c(1) * tx) * (1 - ty) + (c(2) * (1 - tx) + c(3) * tx) * ty;
                color |= std::uint32_t(value + .5) << (8 * k);
            }
            destination[std::size_t(y) * width + x] = color;
        }
    }
}

} // namespace mw34::menu
