#include "native-overrides/capture_pixels.hpp"
#include "native-overrides/photo_replay_math.hpp"
#include <array>
#include <cassert>
#include <cstdio>

int main(int argc, char** argv) {
    using namespace mw34::capture;
    // Two rows, odd width, distinct adjacent pixels: catches the half-width /
    // duplicate-row error as well as red/blue channel reversal.
    const std::array<std::uint8_t,12> packed{0x00,0xf8,0xe0,0x07,0x1f,0x00,
                                          0xff,0xff,0x00,0x00,0xe0,0xff};
    const std::array<std::uint8_t,24> expected{0,0,255,255, 0,255,0,255, 255,0,0,255,
                                            255,255,255,255, 0,0,0,255, 0,255,255,255};
    std::array<std::uint8_t,24> out{};
    to_bgra(packed,out,ColorFormat::rgb565); assert(out==expected);
    const std::array<std::uint8_t,24> rgba{255,0,0,0, 0,255,0,1, 0,0,255,2,
                                        255,255,255,3, 0,0,0,4, 255,255,0,5};
    to_bgra(rgba,out,ColorFormat::rgba8); assert(out==expected);
    if(argc==2)assert(mw34::photo_replay::encode_and_save_png_bgra(argv[1],out.data(),3,2));
    out.fill(17);bool denied=false;
    try { to_bgra(std::span(packed).first(10),out,ColorFormat::rgb565); }
    catch(const std::runtime_error&) { denied=true; }
    assert(denied);for(auto b:out)assert(b==17);
    denied=false;
    try { to_bgra(packed,std::span(out).first(23),ColorFormat::rgb565); }
    catch(const std::runtime_error&) { denied=true; }
    assert(denied);
    std::puts("Capture RGB565/RGBA8 to BGRA8 pixel checks passed");
}
