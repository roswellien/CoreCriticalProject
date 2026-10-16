#pragma once
#include <algorithm>
#include <cmath>
#include <stdexcept>

namespace mw34::frontend {
// Shared fit/inverse for an original logical canvas. A future reflow layout
// can choose different logical bounds without changing presentation or input.
struct CanvasFit {
    int x{}, y{}, width{}, height{};
    unsigned logical_width{}, logical_height{};
    static CanvasFit fit(unsigned lw, unsigned lh, unsigned pw, unsigned ph) {
        if (!lw || !lh || !pw || !ph) throw std::runtime_error("Frontend canvas has zero dimensions");
        const double scale = std::min(double(pw) / lw, double(ph) / lh);
        const int w = int(std::lround(lw * scale)), h = int(std::lround(lh * scale));
        if (w <= 0 || h <= 0) throw std::runtime_error("Frontend canvas cannot fit its output");
        return {(int(pw) - w) / 2, (int(ph) - h) / 2, w, h, lw, lh};
    }
    static int logical_axis(int physical, int origin, int extent, unsigned logical) {
        const double value=double(physical-origin)*logical/extent;
        if(physical<origin)return int(std::floor(value));
        if(physical>=origin+extent)return int(std::ceil(value));
        return std::clamp(int(std::lround(value)),0,int(logical)-1);
    }
    int logical_x(int physical) const { return logical_axis(physical,x,width,logical_width); }
    int logical_y(int physical) const { return logical_axis(physical,y,height,logical_height); }
    int physical_x(int logical) const { return x + int(std::lround(double(logical) * width / logical_width)); }
    int physical_y(int logical) const { return y + int(std::lround(double(logical) * height / logical_height)); }
};
}
