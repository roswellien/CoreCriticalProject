#pragma once
#include <cstdint>

#include "platform/prepared_hud.h"
#include "platform/render3d.h"

// HD menu stage D (docs/hd-menu-port-plan-2026-11-17.md): menu text and
// sprites are drawn as GPU quads at output resolution from their source
// textures, instead of being painted into the 16-bit menu canvas and scaled up
// with it. The original menu code still chooses every image, crop and position;
// this file only holds the pure geometry and policy so tests can check it
// without a renderer. GpuHud applies it (gpu_hud_menu_sprites.cpp).
namespace sdlfe {

// Setting this environment variable to 0, off, false or no turns stage D off
// for a run: menu images are then drawn from their native-resolution pixels
// exactly as before (still through the GPU HUD when the live menu switch is
// on, otherwise through the CPU canvas). Any other value, or no value, leaves
// stage D on.
inline constexpr const char* kMenuSpritesEnvironment = "MW3_HD_MENU_SPRITES";
bool menu_sprites_allowed_by(const char* environment_value);
// Reads kMenuSpritesEnvironment once per process.
bool menu_sprites_allowed_by_environment();

// The uniform scale of the menu's 4:3 layout in the output (owner decision,
// 2026-11-19: the menu keeps its 4:3 layout and text scales with it). The
// central min(640, canvas) x min(480, canvas) dialog fills the largest centred
// 4:3 rectangle of the output, so a 640x480 canvas in a 1920x1080 window has
// scale 2.25 and a 1147x480 wide canvas in the same window has the same 2.25.
// Never below 1: the menu is not rasterised smaller than its native pixels.
float menu_presentation_scale(int canvas_width, int canvas_height, int output_width,
                              int output_height);

// Where a drawn menu image came from, which decides how it is sampled.
enum class MenuSpriteSource {
  // Text re-rasterised at output scale by the text host (hud_text_image).
  kOutputText,
  // A registered high-resolution MW3H-v1 artwork image from a menu/HUD pack.
  kArtwork,
  // The game's own native-resolution pixels.
  kNative,
};

// Sampling choice:
// - Re-rasterised text already has one texel per output pixel, so nearest keeps
//   its antialiased edges exactly as rasterised; linear would only blur them
//   when the quad lands on a fractional output position.
// - Native text images (no output-scale raster available, for example at 1x)
//   use nearest too so letters stay crisp, as the original GDI text was.
// - Artwork and other native images (photos, portraits, buttons, icons) use
//   linear, as the previous HD menu runtime did for non-text images.
platform::TextureFilter menu_sprite_filter(MenuSpriteSource source, bool native_is_text);

// One menu image quad: canvas coordinates (the menu's logical pixels, which
// the canvas scene maps to output pixels) and texture coordinates.
struct MenuSpriteQuad {
  float x0{}, y0{}, x1{}, y1{};
  float u0{}, v0{}, u1{}, v1{};
};

// The quad for blit16's visible part of a source_width x source_height image:
// source columns [left, right) and rows [top, bottom), already clipped, drawn
// with its top-left source pixel at canvas (destination_x, destination_y).
// `image` is the texture actually sampled; its UV rectangle stands for the
// whole source image, whatever its resolution.
//
// With linear filtering, an edge of the crop that lies inside the source image
// (a frame of a sprite sheet, a button state) is moved in by half a texel of
// the sampled texture so the filter cannot pull in the neighbouring frame.
// Edges on the image border need no inset: the canvas sampler clamps there.
// Nearest sampling keeps the exact crop, so at 1x it reproduces blit16.
MenuSpriteQuad menu_sprite_quad(int64_t destination_x, int64_t destination_y, int64_t left,
                                int64_t top, int64_t right, int64_t bottom, int source_width,
                                int source_height, const platform::HudImage& image,
                                platform::TextureFilter filter);

// blit16's per-pixel transparency, exactly (Mech3.exe 1.2 @ 0x0055b3c0, RGB565
// target): an alpha plane value at or below 3 is not drawn and one at or above
// 0xfc is drawn opaque; without an alpha plane, a colour-keyed image (flag 0x02)
// skips pixels equal to the key (the palette index for indexed images).
// Returns the alpha the GPU texel must carry: 0, 255 or the blend in between.
unsigned menu_sprite_alpha(bool has_alpha_plane, uint8_t alpha_plane_value, bool keyed,
                           uint16_t compared_value, uint16_t key);

}  // namespace sdlfe
