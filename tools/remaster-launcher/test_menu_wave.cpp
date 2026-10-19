#include "menu_wave.hpp"

#include <cstdlib>
#include <iostream>

namespace {
void check(bool condition, const char *message) {
    if (!condition) {
        std::cerr << message << '\n';
        std::exit(1);
    }
}
} // namespace

int main() {
    mw34::menu::Wave wave{133, 136, 17, 53, 5, 12.0f, 9.424782752990723f};
    const auto map = mw34::menu::wave_map(wave);
    std::vector<std::uint32_t> source(640 * 480);
    for (std::size_t i = 0; i < source.size(); ++i)
        source[i] = 0xff000000u | std::uint32_t(i);
    std::vector<std::uint32_t> result;
    mw34::menu::warp_rgba(source, result, 640, 480, map);
    unsigned changed = 0;
    for (unsigned y = 0; y < 480; ++y) {
        for (unsigned x = 0; x < 640; ++x) {
            const auto d = map[y * 640 + x];
            const int sx = int(x) + d.x, sy = int(y) + d.y;
            check(sx >= 0 && sx < 640 && sy >= 0 && sy < 480, "Wave read outside canvas");
            check(result[y * 640 + x] == source[std::size_t(sy) * 640 + unsigned(sx)],
                  "Logical-resolution warp changed original sample coordinates");
            changed += result[y * 640 + x] != source[y * 640 + x];
        }
    }
    check(changed > 1000, "Wave did not deform the canvas");
    check(result[136 * 640 + 133] == source[136 * 640 + 133], "Inner area was distorted");
    wave.amplitude = 0;
    mw34::menu::warp_rgba(source, result, 640, 480, mw34::menu::wave_map(wave));
    check(result == source, "Finished wave left a residual distortion");
    wave.amplitude = 6;
    wave.x = 2;
    wave.y = 3;
    wave.inner = -10;
    const auto edge = mw34::menu::wave_map(wave);
    for (unsigned y = 0; y < 480; ++y) {
        for (unsigned x = 0; x < 640; ++x) {
            const auto d = edge[y * 640 + x];
            check(int(x) + d.x >= 0 && int(x) + d.x < 640 && int(y) + d.y >= 0 &&
                      int(y) + d.y < 480,
                  "Clipped wave read outside canvas");
        }
    }
    wave.period = 0;
    check(!wave.valid(), "Invalid period accepted");
    mw34::menu::warp_rgba(source, result, 640, 480, mw34::menu::wave_map(wave));
    check(result == source, "Invalid wave changed pixels");
    std::vector<std::uint32_t> hd(1280 * 960, 0xff785634u);
    mw34::menu::warp_rgba(hd, result, 1280, 960, map);
    check(result == hd, "HD resampling changed a constant canvas");
    std::vector<mw34::menu::Offset> handoff(640 * 480);
    handoff[0].raster = true;
    auto raster = source;
    raster[0] = 0xff123456u;
    mw34::menu::warp_rgba(source, result, 640, 480, handoff, &raster);
    check(result[0] == raster[0] && result[1] == source[1],
          "Clipped scratch pixel was lost or leaked into a neighboring pixel");
    std::cout << "Menu wave: logical sampling, fade-out, clipping and HD interpolation passed\n";
}
