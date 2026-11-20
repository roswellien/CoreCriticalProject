#pragma once
#include <cstdint>
#include <vector>

namespace zimg { struct Texture; }

// The software 2D blits zTwoD draws with (docs/twod.md, Drawing). Original
// file unknown: between zreader.cpp and zrndr_draw.c (0x0055b1f0..0x0055bbe0),
// next to the 2D target they draw into.
namespace zrndr {

// The locked 16-bit buffer (0x008007c8..0x008007d4), set by the video lock.
struct Target2D {
  uint8_t* base = nullptr;         // 0x008007c8
  uint32_t width = 0;              // 0x008007cc  pixels
  uint32_t height = 0;             // 0x008007d0
  uint32_t pitch = 0;              // 0x008007d4  bytes
  int32_t format = 6;              // 0x0074a738  6: RGB565, else RGB555 (the alpha blend)
};
Target2D& target2d();

struct BlitRect;
struct MenuBackgroundBlit {
  int32_t destination_x{}, destination_y{}, source_x{}, source_y{}, width{}, height{};
};
void set_menu_background_source(const zimg::Texture*);
// A cleared frame: the recorded pieces start again and age out after two frames without one.
void begin_menu_background_frame();
// A presented frame (ours, the flip): the next background draw starts a new list of pieces.
// The menus redraw the scrolling background over the last frame without clearing it, so
// without this the list grew by every frame's pieces for as long as a menu stayed open.
// Unlike begin_menu_background_frame, the last pieces stay current: a frame that does not
// redraw the background (the message box over a menu) still shows them in the buffer.
void end_menu_background_frame();
const zimg::Texture* menu_background_source();
const std::vector<MenuBackgroundBlit>& menu_background_blits();
// The SDL HUD adapter observes owned draw recipes while the native buffer is
// still maintained for reads/grabs. It never receives guest addresses or state.
class DrawObserver {
 public:
  virtual ~DrawObserver() = default;
  virtual void image(const zimg::Texture*, int32_t x, int32_t y, uint16_t key, const BlitRect*) = 0;
  virtual void pixel(const uint16_t* destination, uint16_t colour) = 0;
  virtual void span(const uint16_t* destination, uint32_t count, uint16_t colour) = 0;
  virtual void resolved_region(const uint16_t* destination, uint32_t width, uint32_t height,
                               uint32_t pitch_bytes, const char* operation) {
    (void)width, (void)height, (void)pitch_bytes;
    framebuffer_write(destination, operation);
  }
  virtual void framebuffer_write(const void* target, const char* operation) = 0;
  // HD menu stage D: true when the observer draws alpha-plane images itself
  // from their source pixels (with blit16's thresholds), so blit16 hands it the
  // image instead of reporting each blended run as a resolved region.
  virtual bool wants_source_alpha_images() const { return false; }
};
DrawObserver* draw_observer();
void set_draw_observer(DrawObserver*);
void observe_framebuffer_write(const void* target, const char* operation);
void observe_resolved_region(const uint16_t* destination, uint32_t width, uint32_t height,
                             uint32_t pitch_bytes, const char* operation);

// HD menu presentation policy (owner decisions, 2026-11-19). The original
// menus were authored for a 4:3 screen, so their controls, text and cursor
// stay in that 4:3 layout and scale together with it; only the background
// image fills the whole output resolution (cover scaling, no pillarbox).
// Keeping text and the cursor on the menu's scale is what keeps visible
// controls and hit testing in agreement at any window size.
inline constexpr bool kMenuKeepsFourByThreeLayout = true;
inline constexpr bool kMenuBackgroundFillsScreen = true;
inline constexpr bool kMenuTextScalesWithMenu = true;
// Cursor draws and restores share the menu's logical coordinate space so
// hotspot offsets, screen-edge clipping and hit testing agree. Setting this
// false (a physical-pixel cursor) is not implemented and falls back visibly.
inline constexpr bool kCursorUsesMenuLogicalTransform = true;

class ScopedMuteDrawObserver {
 public:
  ScopedMuteDrawObserver();
  ~ScopedMuteDrawObserver();
  ScopedMuteDrawObserver(const ScopedMuteDrawObserver&) = delete;
  ScopedMuteDrawObserver& operator=(const ScopedMuteDrawObserver&) = delete;

 private:
  DrawObserver* saved_;
};

// FIX (A): the program's 16-bit layer over the Direct3D frame (app_engine)
// starts as `key`, not the frame the original's locked back buffer held, so
// an alpha blend there would mix with the key colour. While `alpha` is set
// (the layer's lock), a blend records each pixel's coverage and the colour it
// wrote, and the overlay draws that pixel with that alpha (docs/render-frame.md).
struct LayerCover {
  uint8_t* alpha = nullptr;        // per pixel, as the target; 0: none recorded
  uint16_t* colour = nullptr;      // the colour the blend wrote
  uint16_t key = 0;                // the layer's untouched colour
};
LayerCover& layer_cover();
void cover_opaque(uint16_t* pixel);  // an opaque write into the 2D target: its recorded blend ended

// A source rectangle, as a Win32 RECT.
struct BlitRect {
  int32_t left, top, right, bottom;
};

// Mech3.exe 1.2 @ 0x0055b3c0, the 16-bit target's blit ([0x00800824]):
// `image` at (x, y), all of it or `src`'s part, clipped to the target. Pixels
// are 16-bit or palette indices; with an alpha plane each pixel blends by its
// alpha (none at 0..3, or 0..7 in 555; all from 0xfc), else with flag 0x02 the
// colour (or index) `key` is transparent.
void blit16(const zimg::Texture* image, int32_t x, int32_t y, uint16_t key, const BlitRect* src);

// Mech3.exe 1.2 @ 0x00563b80, the 16-bit target's line ([0x008008c0], behind
// 0x00562940): from (x0, y0) to (x1, y1) inclusive, stepping the longer axis.
void line16(int32_t x0, int32_t y0, int32_t x1, int32_t y1, uint16_t pixel);

}  // namespace zrndr
