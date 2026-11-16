#pragma once
// #289: what the top-down map viewer (--replay) and the 3D
// viewer (--replay3d) share: the replay clock, the overlay toggles, the
// overlay lines, the selected mech's panel, the seek bar, text rendering and
// the --replay-script runner. Each viewer supplies a ReplayDraw (how a line,
// circle, text or box reaches its screen) and a Projector (where a world point
// lands on it).
#include <SDL3/SDL.h>

#include <algorithm>
#include <functional>
#include <map>
#include <string>
#include <vector>

#include "mech3/replay_log.h"

struct TTF_Font;

namespace sdlfe {

constexpr float kSeekBarHeight = 28.0f;
constexpr float kReplayPi = 3.14159265f;

SDL_FColor ui_color(uint8_t r, uint8_t g, uint8_t b, uint8_t a = 255);
extern const SDL_FColor kSideColor[2];

std::string clock_text(float seconds);

// The few shapes the viewers' shared parts draw, in screen pixels.
class ReplayDraw {
 public:
  virtual ~ReplayDraw() = default;
  virtual void line(SDL_FPoint a, SDL_FPoint b, const SDL_FColor& c) = 0;
  virtual void circle(SDL_FPoint center, float radius, const SDL_FColor& fill) = 0;
  virtual void rect(const SDL_FRect& r, const SDL_FColor& fill) = 0;
  // Draws `s` with its top-left at (x, y); returns its width.
  virtual float text(const std::string& s, float x, float y, SDL_Color c = {235, 235, 235, 255}) = 0;
  // Dashes along a-b, built from line().
  void dashed(SDL_FPoint a, SDL_FPoint b, const SDL_FColor& c, float dash = 6.0f);
  void cross(SDL_FPoint center, float size, const SDL_FColor& c);

  // How big the text and the boxes around it are: 1 on a screen 720 pixels
  // tall, growing with the screen's height, so a 1080-line frame isn't read
  // at a 720-line size. Set once a frame, before drawing.
  void set_scale_for_height(float screen_height) {
    const float wanted = std::clamp(screen_height / 720.0f, 1.0f, 3.0f);
    if (wanted == scale_) return;
    scale_ = wanted;
    scale_changed(scale_);
  }
  float scale() const { return scale_; }

 protected:
  // The text's size follows the scale (its cache is rebuilt at the new size).
  virtual void scale_changed(float) {}

 private:
  float scale_ = 1.0f;
};

// World to screen. False when the point is not on the screen side of the
// camera (the 3D view; the map sees every point).
class Projector {
 public:
  virtual ~Projector() = default;
  virtual bool to_screen(const mech3::replay::Vec3& world, SDL_FPoint* out) const = 0;
};

// The replay's time: play and pause, speed, jumps and seeks.
struct ReplayClock {
  static constexpr float kMinSpeed = 0.25f, kMaxSpeed = 8.0f;
  static constexpr float kJumpSeconds = 5.0f;
  float t = 0, speed = 1, duration = 0;
  bool playing = true;

  // One frame of `elapsed` real seconds (a fixed 1/60 when scripted), held
  // still while the seek bar is dragged. Returns the replay seconds moved.
  float step(float elapsed, bool held);
  void toggle_play();  // at the end, plays again from the start
  void jump(float seconds);
  void seek_fraction(float fraction);  // 0 to 1 along the match
  void seek(float seconds);
  void slower();
  void faster();
};

// Real seconds since the last frame, capped so a stall (Windows stops the
// loop while a window is dragged) doesn't jump the replay ahead.
float frame_elapsed(uint64_t* last_ns, bool scripted);

// The overlays, in key order 1 to 5.
enum Overlay { kRoute, kTarget, kGoal, kContacts, kReasons, kOverlays };
struct Overlays {
  bool on[kOverlays] = {true, true, true, true, true};
  bool legend = true;  // H: the colors' key
  void toggle(int index) { on[index] = !on[index]; }
};

// The AI's lines. With no mech selected, every standing mech's target line
// (who shoots whom) and nothing else, so a crowd stays readable; with one
// selected (`selected`, its index in the frame), that mech's route, goal,
// radar contacts and target, and the other mechs' target lines faint.
void draw_overlays(const mech3::replay::Frame& frame, const Overlays& overlays, int selected, ReplayDraw& draw,
                   const Projector& projector);

// A decision reason code from the log (docs/arena.md, "What the replay
// viewers read") in a few plain words, for the labels: "chasing".
std::string reason_short(const std::string& code);
// The same as a sentence, for the panel: "chasing an enemy its radar sees".
std::string reason_sentence(const std::string& code);

// The key to the overlays' colors at the top left, when overlays.legend is on.
void draw_legend(const Overlays& overlays, ReplayDraw& draw);

// Each mech's label, its id and its decision word, kept from landing on one
// already drawn this frame: a label that would overlap moves down a line
// (up to a few lines; mechs in a tight knot still crowd).
class LabelPlacer {
 public:
  // Draws the label with its top left nearest (x, y) that is free.
  void draw(ReplayDraw& draw, float x, float y, const std::string& id, const std::string& reason);

 private:
  std::vector<SDL_FRect> taken_;
};

// The selected mech's panel at the top right; `selected` is its index in the
// frame, -1 for none.
void draw_panel(const mech3::replay::ReplayLog& log, const mech3::replay::Frame& frame, int selected,
                float screen_width, ReplayDraw& draw);

// The seek bar along the bottom, and where a press on it seeks to.
void draw_bar(const ReplayClock& clock, const Overlays& overlays, float screen_width, float screen_height,
              ReplayDraw& draw);
inline float bar_top(float screen_height) { return screen_height - kSeekBarHeight; }

const mech3::replay::MechPose* pose_of(const mech3::replay::Frame& frame, int id);

// The font and string-to-surface half of drawing text; each backend uploads
// and caches the surfaces its own way.
class TextRenderer {
 public:
  TextRenderer() = default;
  ~TextRenderer();
  TextRenderer(const TextRenderer&) = delete;
  TextRenderer& operator=(const TextRenderer&) = delete;
  static constexpr float kBaseSize = 14.0f;  // pixels at scale 1
  void open();
  bool ready() const { return font_ != nullptr; }
  void set_scale(float scale);  // the font at kBaseSize * scale
  // A new surface the caller destroys, or null.
  SDL_Surface* render(const std::string& s, SDL_Color c) const;

 private:
  TTF_Font* font_ = nullptr;
  bool ttf_ok_ = false;
};

// ReplayDraw over SDL's 2D renderer, with the map viewer's extra shapes.
class SdlRendererDraw : public ReplayDraw {
 public:
  explicit SdlRendererDraw(SDL_Renderer* renderer) : renderer_(renderer) {}
  ~SdlRendererDraw() override;
  void open_text() { text_renderer_.open(); }
  SDL_Renderer* renderer() const { return renderer_; }

 protected:
  void scale_changed(float scale) override {
    text_renderer_.set_scale(scale);
    clear_text();
  }

 public:

  void line(SDL_FPoint a, SDL_FPoint b, const SDL_FColor& c) override;
  void circle(SDL_FPoint center, float radius, const SDL_FColor& fill) override;
  void rect(const SDL_FRect& r, const SDL_FColor& fill) override;
  float text(const std::string& s, float x, float y, SDL_Color c = {235, 235, 235, 255}) override;
  void outline(const SDL_FRect& r, const SDL_FColor& c);
  void arrow(SDL_FPoint from, SDL_FPoint dir, float length, const SDL_FColor& c);
  // A thin wedge from `from` toward screen direction `yaw`, `half_angle` each side.
  void cone(SDL_FPoint from, float yaw, float half_angle, float length, const SDL_FColor& c);

 private:
  void set(const SDL_FColor& c);
  void clear_text();
  SDL_Renderer* renderer_;
  TextRenderer text_renderer_;
  std::map<std::string, SDL_Texture*> cache_;
};

// A hull or torso yaw as a direction on the map's screen. The log's heading
// turns the mech's forward axis, -z (arena_log.cpp's state line), about +y.
SDL_FPoint screen_direction(float yaw);

// What a --replay-script can do beyond pushing input events. A viewer leaves
// a hook empty when it has no such thing (the map viewer has no 3D camera).
struct ScriptActions {
  std::function<void(const std::string& path)> shot;
  std::function<void(float t)> seek;
  std::function<void(float x, float y, float z, float yaw, float pitch)> camera;
  std::function<void(int id)> follow;
};

// A test script: one command per line (see docs/arena.md), # for comments.
// Scripted runs step a fixed 1/60 s a frame, so the same script shows the
// same times.
class ReplayScript {
 public:
  bool load(const std::string& path);
  // Runs commands until a wait or the end; input goes into SDL's queue and
  // takes effect next frame. False on an unknown command.
  bool run(const ScriptActions& actions);

 private:
  std::vector<std::vector<std::string>> lines_;
  size_t next_ = 0;
  int wait_frames_ = 0;
};

}  // namespace sdlfe
