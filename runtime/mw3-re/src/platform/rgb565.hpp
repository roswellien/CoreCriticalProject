#pragma once

#include <cstdint>

// How the remaster widens 16-bit RGB565 color to 8 bits per channel. Each
// channel becomes value * 255 / max, rounded down, where max is the channel's
// largest value (31 for 5 bits, 63 for 6). Every widening outside the game's
// own code uses this one: pack replacement images and prepared skins, the
// renderer's 16-bit texture and frame inputs, frame dumps and captures, the HUD
// and menu images, and the arena's mech pictures.
//
// The renderer relies on it (#518): it stores a texture widened this way back
// on the card at 16 bits by dropping each channel's low bits, which undoes this
// widening exactly. tests/test_texture_storage.cpp checks that for every value,
// so changing the rounding here means changing that packing too.
//
// Two widenings repeat each channel's bits instead and are not this one: the
// game's own texture decode (gamez/zvideo/zvid_ddd3d.cpp, texture_rgba), which
// matches the original game, and the 2D screen layer
// (frontend/sdl/sdl_platform.cpp, rgba_of).
namespace platform::rgb565 {

// One channel widened to 8 bits. The renderer's ARGB1555 and ARGB4444 inputs
// use it too, with max 31 and 15 (for 15 it equals value * 17).
constexpr unsigned widen_channel(unsigned value, unsigned max) { return value * 255 / max; }

struct Channels {
  unsigned red;
  unsigned green;
  unsigned blue;
};

constexpr Channels widen(std::uint16_t color) {
  const unsigned value = color;
  return {widen_channel(value >> 11, 31), widen_channel((value >> 5) & 63, 63),
          widen_channel(value & 31, 31)};
}

// RGBA8 as the renderer's textures hold it: red in the low byte, alpha in the top.
constexpr std::uint32_t to_rgba8(std::uint16_t color, unsigned alpha = 255) {
  const Channels channels = widen(color);
  return channels.red | channels.green << 8 | channels.blue << 16 | alpha << 24;
}

// The same with each channel multiplied by alpha / 255, rounded to nearest. The
// HUD and the menu images both build their textures with it, so the same pixels
// make the same texture and share one cache entry.
constexpr std::uint32_t to_premultiplied_rgba8(std::uint16_t color, unsigned alpha) {
  const Channels channels = widen(color);
  const auto premultiply = [alpha](unsigned channel) { return (channel * alpha + 127) / 255; };
  return premultiply(channels.red) | premultiply(channels.green) << 8 |
         premultiply(channels.blue) << 16 | alpha << 24;
}

} // namespace platform::rgb565
