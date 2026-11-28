#pragma once
#include <cmath>

// The game's frame in the window (FIX (B), behind zfix any_resolution;
// resolution.md step 2): the frame (the display rect, 640x480 or a mode's
// size) keeps its shape, as the largest centred rect of its aspect, with
// black bars where the window's shape differs (pillarbox or letterbox).
// Without the fix the frame is stretched over the whole window, as before.
// Pure geometry, no SDL, so the tests check it headless.
namespace sdlfe {

struct FrameShape {
  int frame_w = 640, frame_h = 480;  // the frame the game draws (its render rect)
  bool fit = false;                  // any_resolution: keep the frame's shape
  // The 2D canvas over it (the display rect, resolution.md step 4: the frame
  // over the art scale); 0: the frame's own size. The cursor is in its pixels.
  int canvas_w = 0, canvas_h = 0;
  // True when menu_frame_shape anchors uniform 4:3 scaling at the centered
  // 640x480 dialog origin inside a wider native menu canvas.
  bool menu = false;
  // Shared live-menu layout flag set by SdlScreen2D while live GPU menu
  // policy owns presentation and input mapping, even across CPU fallbacks.
  mutable bool menu_layout_active = false;
  int client_w() const { return canvas_w > 0 ? canvas_w : frame_w; }
  int client_h() const { return canvas_h > 0 ? canvas_h : frame_h; }
};

struct FitRect {
  float x = 0, y = 0, w = 0, h = 0;
};

inline constexpr int kMenuLogicalWidth = 640;
inline constexpr int kMenuLogicalHeight = 480;

// Where the frame sits in a window of win_w x win_h (pixels or points alike).
// When s.menu is true, the central min(640, client_w) x min(480, client_h)
// dialog occupies the largest centered 4:3 (or tiny fixture) rectangle in the
// window, and the returned full-canvas rectangle expands uniformly from that
// centered integer dialog_origin so native pixels stay square.
inline FitRect fit_rect(float win_w, float win_h, const FrameShape& s) {
  if (!s.fit || s.frame_w <= 0 || s.frame_h <= 0 || win_w <= 0 || win_h <= 0) return {0, 0, win_w, win_h};
  if (s.menu) {
    const int client_width = s.client_w();
    const int client_height = s.client_h();
    if (client_width <= 0 || client_height <= 0) return {0, 0, win_w, win_h};
    const int dialog_width = client_width < kMenuLogicalWidth ? client_width : kMenuLogicalWidth;
    const int dialog_height = client_height < kMenuLogicalHeight ? client_height : kMenuLogicalHeight;
    const float scale = std::fmin(win_w / static_cast<float>(dialog_width),
                                  win_h / static_cast<float>(dialog_height));
    const float centered_width = std::round(static_cast<float>(dialog_width) * scale);
    const float centered_height = std::round(static_cast<float>(dialog_height) * scale);
    const float centered_x = std::floor((win_w - centered_width) / 2.0f);
    const float centered_y = std::floor((win_h - centered_height) / 2.0f);
    const int dialog_origin_x = (client_width - dialog_width) / 2;
    const int dialog_origin_y = (client_height - dialog_height) / 2;
    return {centered_x - static_cast<float>(dialog_origin_x) * scale,
            centered_y - static_cast<float>(dialog_origin_y) * scale,
            static_cast<float>(client_width) * scale,
            static_cast<float>(client_height) * scale};
  }
  const float scale = std::fmin(win_w / s.frame_w, win_h / s.frame_h);
  const float w = std::round(s.frame_w * scale), h = std::round(s.frame_h * scale);
  return {std::floor((win_w - w) / 2), std::floor((win_h - h) / 2), w, h};
}

// A window position as a client (canvas) pixel, and back (the cursor's mapping).
inline void window_to_frame(float wx, float wy, float win_w, float win_h, const FrameShape& s, float* fx, float* fy) {
  const FitRect r = fit_rect(win_w, win_h, s);
  *fx = r.w > 0 ? (wx - r.x) * s.client_w() / r.w : 0;
  *fy = r.h > 0 ? (wy - r.y) * s.client_h() / r.h : 0;
}
inline void frame_to_window(float fx, float fy, float win_w, float win_h, const FrameShape& s, float* wx, float* wy) {
  const FitRect r = fit_rect(win_w, win_h, s);
  *wx = r.x + fx * r.w / s.client_w();
  *wy = r.y + fy * r.h / s.client_h();
}

// The relative mouse's scale: window motion to client pixels, so a mickey is
// a game pixel at any window size (the exe's 640x480 window: one to one).
inline float mickey_scale(float win_w, float win_h, const FrameShape& s) {
  const FitRect r = fit_rect(win_w, win_h, s);
  return r.w > 0 ? s.client_w() / r.w : 1.0f;
}

// Active menu layout policy: marks menu=true and forces fit=true so the
// central 640x480 dialog sits in the largest centered 4:3 window rectangle
// with square native pixels, while client_w()/client_h() retain the full
// native canvas dimensions.
inline FrameShape menu_frame_shape(const FrameShape& s, int canvas_w = 0, int canvas_h = 0) {
  FrameShape menu = s;
  const int client_width = canvas_w > 0 ? canvas_w : s.client_w();
  const int client_height = canvas_h > 0 ? canvas_h : s.client_h();
  menu.canvas_w = client_width;
  menu.canvas_h = client_height;
  menu.frame_w = client_width < kMenuLogicalWidth ? client_width : kMenuLogicalWidth;
  menu.frame_h = client_height < kMenuLogicalHeight ? client_height : kMenuLogicalHeight;
  menu.fit = true;
  menu.menu = true;
  return menu;
}

inline FitRect menu_fit_rect(float win_w, float win_h, const FrameShape& s, int canvas_w = 0,
                             int canvas_h = 0) {
  return fit_rect(win_w, win_h, menu_frame_shape(s, canvas_w, canvas_h));
}

inline void menu_window_to_frame(float wx, float wy, float win_w, float win_h, const FrameShape& s,
                                 float* fx, float* fy, int canvas_w = 0, int canvas_h = 0) {
  window_to_frame(wx, wy, win_w, win_h, menu_frame_shape(s, canvas_w, canvas_h), fx, fy);
}

inline void menu_frame_to_window(float fx, float fy, float win_w, float win_h, const FrameShape& s,
                                 float* wx, float* wy, int canvas_w = 0, int canvas_h = 0) {
  frame_to_window(fx, fy, win_w, win_h, menu_frame_shape(s, canvas_w, canvas_h), wx, wy);
}

inline float menu_mickey_scale(float win_w, float win_h, const FrameShape& s, int canvas_w = 0,
                               int canvas_h = 0) {
  return mickey_scale(win_w, win_h, menu_frame_shape(s, canvas_w, canvas_h));
}

// Ours (#559, docs/fmv.md section 9): where an HD movie's frame goes in the
// window. The same rule GameEngine::fmv_stretch (app_fmv.cpp) gives the
// 16-bit movies on a wide buffer, here on the window's pixels: on a window
// wider than 4:3, the movie's rows `src_top`..`src_bottom` (its letterboxed
// picture, movie_shape.h) fill the width, capped at the window's height;
// otherwise, or with no rows (-1), the whole frame in the largest centred
// 4:3 rectangle.
inline FitRect movie_frame_fit(float win_w, float win_h, int clip_w, int clip_h, int src_top, int src_bottom) {
  if (win_w <= 0 || win_h <= 0 || clip_w <= 0 || clip_h <= 0) return {0, 0, win_w, win_h};
  const bool wider_than_4_3 = win_w * 3 > win_h * 4;
  const bool has_rows = src_top >= 0 && src_bottom >= src_top && src_bottom < clip_h;
  float w = 0, h = 0;
  if (wider_than_4_3 && has_rows) {
    const float rows = static_cast<float>(src_bottom - src_top + 1);
    w = win_w, h = win_w * rows / clip_w;
    if (h > win_h) h = win_h, w = win_h * clip_w / rows;
  } else {
    w = std::fmin(win_w, win_h * 4.0f / 3.0f), h = w * 3.0f / 4.0f;
  }
  return {(win_w - w) / 2.0f, (win_h - h) / 2.0f, w, h};
}

// The window a frame asks for when --window is not given: the frame itself,
// doubled while it is under 1280 wide (640x480 opens at 1280x960, as before).
inline void default_window(const FrameShape& s, int* w, int* h) {
  int k = 1;
  while (s.frame_w * k < 1280) ++k;
  *w = s.frame_w * k, *h = s.frame_h * k;
}

}  // namespace sdlfe
