#pragma once

#include <cstdint>

namespace mw34::vkscene {

// What a renderer texture holds. It is set once, when the frontend makes the
// texture, and read by the texture memory line and by the rule for which
// textures may be stored at 16 bits (#518).
enum class TextureSource : std::uint8_t {
  guest,         // a game surface or named texture, including pack replacements
  prepared_skin, // a prepared model's albedo image (mech skins and the like)
  normal,        // a normal map: real 8-bit data, never narrowed
  canvas,        // an image the HUD or menus draw into each frame
  height,        // a parallax height image (R8)
};

} // namespace mw34::vkscene
