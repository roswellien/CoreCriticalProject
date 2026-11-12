#include "frontend/sdl/replay_view.h"

#include <SDL3/SDL.h>
#include <SDL3_ttf/SDL_ttf.h>

#include <algorithm>
#include <cmath>
#include <cstdio>
#include <cstdlib>
#include <filesystem>
#include <fstream>
#include <map>
#include <sstream>
#include <string>
#include <vector>

#include "gamez/zutil/zutl_path.h"
#include "mech3/replay_log.h"
#include "mech3/replay_terrain.h"

namespace sdlfe {

namespace {

using mech3::replay::Frame;
using mech3::replay::MechPose;
using mech3::replay::ReplayLog;
using mech3::replay::Terrain;
using mech3::replay::Vec3;

constexpr float kTrailSeconds = 10.0f;
constexpr float kJumpSeconds = 5.0f;
constexpr float kMinSpeed = 0.25f, kMaxSpeed = 8.0f;
constexpr float kMinZoom = 0.25f, kMaxZoom = 16.0f;  // pixels per meter
constexpr float kZoomStep = 1.25f;
constexpr float kSeekBarHeight = 28.0f;
constexpr float kPickPixels = 10.0f;
constexpr float kStreakMeters = 15.0f;
constexpr float kPi = 3.14159265f;

// The overlays, in key order 1 to 5.
enum Overlay { kRoute, kTarget, kGoal, kContacts, kReasons, kOverlays };

SDL_FColor color(uint8_t r, uint8_t g, uint8_t b, uint8_t a = 255) {
  return {r / 255.0f, g / 255.0f, b / 255.0f, a / 255.0f};
}
const SDL_FColor kSideColor[2] = {color(80, 150, 255), color(255, 90, 80)};

// The map is seen from above: world x to the right, world z up the screen.
struct Camera {
  float center_x = 0, center_z = 0;
  float zoom = 1;  // pixels per meter
  float width = 1, height = 1;
  SDL_FPoint to_screen(float x, float z) const {
    return {width / 2 + (x - center_x) * zoom, height / 2 - (z - center_z) * zoom};
  }
  SDL_FPoint to_screen(const Vec3& v) const { return to_screen(v.x, v.z); }
  void to_world(float sx, float sy, float* x, float* z) const {
    *x = center_x + (sx - width / 2) / zoom;
    *z = center_z - (sy - height / 2) / zoom;
  }
};

// A hull or torso yaw as a direction on the screen. The log's heading turns
// the mech's forward axis, -z (arena_log.cpp's state line), about +y.
SDL_FPoint screen_direction(float yaw) { return {-std::sin(yaw), std::cos(yaw)}; }

// The few shapes the viewer draws, over SDL's 2D renderer.
struct Painter {
  SDL_Renderer* renderer = nullptr;

  void set(const SDL_FColor& c) {
    SDL_SetRenderDrawColorFloat(renderer, c.r, c.g, c.b, c.a);
  }
  void line(SDL_FPoint a, SDL_FPoint b, const SDL_FColor& c) {
    set(c);
    SDL_RenderLine(renderer, a.x, a.y, b.x, b.y);
  }
  void dashed(SDL_FPoint a, SDL_FPoint b, const SDL_FColor& c, float dash = 6.0f) {
    const float dx = b.x - a.x, dy = b.y - a.y;
    const float length = std::sqrt(dx * dx + dy * dy);
    if (length < 1) return;
    set(c);
    for (float s = 0; s < length; s += 2 * dash) {
      const float e = std::min(s + dash, length);
      SDL_RenderLine(renderer, a.x + dx * s / length, a.y + dy * s / length, a.x + dx * e / length,
                     a.y + dy * e / length);
    }
  }
  void circle(SDL_FPoint c, float radius, const SDL_FColor& fill) {
    constexpr int kSegments = 16;
    std::vector<SDL_Vertex> v;
    for (int i = 0; i < kSegments; ++i) {
      const float a0 = 2 * kPi * i / kSegments, a1 = 2 * kPi * (i + 1) / kSegments;
      v.push_back({c, fill, {0, 0}});
      v.push_back({{c.x + radius * std::cos(a0), c.y + radius * std::sin(a0)}, fill, {0, 0}});
      v.push_back({{c.x + radius * std::cos(a1), c.y + radius * std::sin(a1)}, fill, {0, 0}});
    }
    SDL_RenderGeometry(renderer, nullptr, v.data(), static_cast<int>(v.size()), nullptr, 0);
  }
  void arrow(SDL_FPoint from, SDL_FPoint dir, float length, const SDL_FColor& c) {
    const SDL_FPoint tip = {from.x + dir.x * length, from.y + dir.y * length};
    line(from, tip, c);
    const float head = length * 0.35f;
    for (const float side : {1.0f, -1.0f}) {
      // Back from the tip, 30 degrees off the shaft.
      const float bx = -dir.x * 0.866f - side * dir.y * 0.5f, by = -dir.y * 0.866f + side * dir.x * 0.5f;
      line(tip, {tip.x + bx * head, tip.y + by * head}, c);
    }
  }
  // A thin wedge from the center along `dir`, `half_angle` each side.
  void cone(SDL_FPoint from, float yaw, float half_angle, float length, const SDL_FColor& c) {
    const SDL_FPoint left = screen_direction(yaw + half_angle), right = screen_direction(yaw - half_angle);
    const SDL_Vertex v[3] = {{from, c, {0, 0}},
                             {{from.x + left.x * length, from.y + left.y * length}, c, {0, 0}},
                             {{from.x + right.x * length, from.y + right.y * length}, c, {0, 0}}};
    SDL_RenderGeometry(renderer, nullptr, v, 3, nullptr, 0);
  }
  void cross(SDL_FPoint c, float size, const SDL_FColor& col) {
    line({c.x - size, c.y - size}, {c.x + size, c.y + size}, col);
    line({c.x - size, c.y + size}, {c.x + size, c.y - size}, col);
  }
  void box(const SDL_FRect& r, const SDL_FColor& c) {
    set(c);
    SDL_RenderFillRect(renderer, &r);
  }
};

// Text through SDL3_ttf; each distinct string becomes a texture once.
class Text {
 public:
  explicit Text(SDL_Renderer* renderer) : renderer_(renderer) {}
  ~Text() {
    clear();
    if (font_) TTF_CloseFont(font_);
    if (ttf_ok_) TTF_Quit();
  }
  void open() {
    ttf_ok_ = TTF_Init();
    if (!ttf_ok_) return;
    // The game's own Arial when a mount has it, else the system's.
    std::vector<std::string> tries = {zutl::find("arial.ttf"), "C:/Windows/Fonts/arial.ttf",
                                      "/System/Library/Fonts/Supplemental/Arial.ttf",
                                      "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
                                      "/usr/share/fonts/TTF/DejaVuSans.ttf"};
    for (const std::string& path : tries)
      if (!path.empty() && (font_ = TTF_OpenFont(path.c_str(), 14.0f)) != nullptr) return;
    std::fprintf(stderr, "mw3: replay: no font found, drawing without text\n");
  }
  // Draws `s` with its top-left at (x, y); returns its width.
  float draw(const std::string& s, float x, float y, SDL_Color c = {235, 235, 235, 255}) {
    if (!font_ || s.empty()) return 0;
    if (cache_.size() > 2000) clear();  // a long replay's labels; rebuilt as needed
    const std::string key = s + "#" + std::to_string(c.r) + "," + std::to_string(c.g) + "," + std::to_string(c.b);
    SDL_Texture*& tex = cache_[key];
    if (!tex) {
      SDL_Surface* surface = TTF_RenderText_Blended(font_, s.c_str(), 0, c);
      if (!surface) return 0;
      tex = SDL_CreateTextureFromSurface(renderer_, surface);
      SDL_DestroySurface(surface);
      if (!tex) return 0;
    }
    float w = 0, h = 0;
    SDL_GetTextureSize(tex, &w, &h);
    const SDL_FRect dst = {std::round(x), std::round(y), w, h};
    SDL_RenderTexture(renderer_, tex, nullptr, &dst);
    return w;
  }

 private:
  void clear() {
    for (auto& [key, tex] : cache_) SDL_DestroyTexture(tex);
    cache_.clear();
  }
  SDL_Renderer* renderer_;
  TTF_Font* font_ = nullptr;
  bool ttf_ok_ = false;
  std::map<std::string, SDL_Texture*> cache_;
};

std::string clock_text(float seconds) {
  const int whole = static_cast<int>(seconds);
  char buf[32];
  std::snprintf(buf, sizeof buf, "%d:%02d.%d", whole / 60, whole % 60, static_cast<int>((seconds - whole) * 10));
  return buf;
}

// The viewer's state between frames.
struct Viewer {
  const ReplayLog* log = nullptr;
  Terrain terrain;
  SDL_Texture* terrain_texture = nullptr;
  Camera camera;
  float t = 0, speed = 1;
  bool playing = true;
  bool overlay[kOverlays] = {true, true, true, true, true};
  int selected = -1;  // a mech's index in the log, -1 for none
  bool seeking = false, panning = false;
  float press_x = 0, press_y = 0;
  std::string log_path;

  float bar_top() const { return camera.height - kSeekBarHeight; }
  void seek_to(float sx) { t = std::clamp(sx / camera.width, 0.0f, 1.0f) * log->duration(); }
  void jump(float seconds) { t = std::clamp(t + seconds, 0.0f, log->duration()); }
};

// The terrain as one texture, its walls and cliffs darkened in.
SDL_Texture* make_terrain_texture(SDL_Renderer* renderer, const Terrain& terrain) {
  if (terrain.width <= 0 || terrain.height <= 0) return nullptr;
  std::vector<uint8_t> pixels = terrain.rgba;
  for (size_t i = 0; i < terrain.outline.size(); ++i)
    if (terrain.outline[i]) pixels[i * 4] = pixels[i * 4 + 1] = pixels[i * 4 + 2] = 24;
  SDL_Texture* tex =
      SDL_CreateTexture(renderer, SDL_PIXELFORMAT_ABGR8888, SDL_TEXTUREACCESS_STATIC, terrain.width, terrain.height);
  if (!tex) return nullptr;
  SDL_UpdateTexture(tex, nullptr, pixels.data(), terrain.width * 4);
  SDL_SetTextureScaleMode(tex, SDL_SCALEMODE_LINEAR);
  return tex;
}

void fit_camera(Camera* camera, const float box[4]) {
  if (box[0] > box[2]) return;
  camera->center_x = (box[0] + box[2]) / 2, camera->center_z = (box[1] + box[3]) / 2;
  const float span_x = std::max(box[2] - box[0], 50.0f), span_z = std::max(box[3] - box[1], 50.0f);
  camera->zoom = std::clamp(std::min(camera->width / span_x, (camera->height - kSeekBarHeight) / span_z) * 0.9f,
                            kMinZoom, kMaxZoom);
}

int pick_mech(const Viewer& v, const Frame& frame, float sx, float sy) {
  int best = -1;
  float best_d = kPickPixels;
  for (size_t i = 0; i < frame.mechs.size(); ++i) {
    const SDL_FPoint p = v.camera.to_screen(frame.mechs[i].pos);
    const float d = std::hypot(p.x - sx, p.y - sy);
    if (d <= best_d) best_d = d, best = static_cast<int>(i);
  }
  return best;
}

const MechPose* pose_of(const Frame& frame, int id) {
  for (const MechPose& p : frame.mechs)
    if (p.id == id) return &p;
  return nullptr;
}

void draw_world(Viewer& v, const Frame& frame, Painter& paint, Text& text) {
  const Camera& cam = v.camera;
  if (v.terrain_texture) {
    const SDL_FPoint top_left = cam.to_screen(v.terrain.x0, v.terrain.z_top);
    const SDL_FRect dst = {top_left.x, top_left.y, v.terrain.width * v.terrain.cell * cam.zoom,
                           v.terrain.height * v.terrain.cell * cam.zoom};
    SDL_RenderTexture(paint.renderer, v.terrain_texture, nullptr, &dst);
  }
  const auto& infos = v.log->mechs();
  const auto side_of = [&](int i) { return i < static_cast<int>(infos.size()) ? std::clamp(infos[i].side, 0, 1) : 0; };

  // Trails.
  for (size_t i = 0; i < frame.mechs.size(); ++i) {
    const std::vector<Vec3> trail = v.log->trail(static_cast<int>(i), v.t, kTrailSeconds);
    SDL_FColor c = kSideColor[side_of(static_cast<int>(i))];
    c.a = 0.45f;
    for (size_t k = 1; k < trail.size(); ++k) paint.line(cam.to_screen(trail[k - 1]), cam.to_screen(trail[k]), c);
  }
  for (size_t i = 0; i < frame.mechs.size(); ++i) {
    const MechPose& m = frame.mechs[i];
    if (!m.standing) continue;
    const SDL_FPoint at = cam.to_screen(m.pos);
    if (v.overlay[kRoute] && !frame.routes[i].points.empty()) {
      const auto& points = frame.routes[i].points;
      SDL_FPoint prev = at;
      for (size_t k = std::max(m.at, 0); k < points.size(); ++k) {
        const SDL_FPoint p = cam.to_screen(points[k]);
        paint.line(prev, p, color(255, 230, 90, 200));
        paint.circle(p, 2.5f, color(255, 230, 90, 200));
        prev = p;
      }
    }
    if (v.overlay[kGoal] && m.has_goal) {
      const SDL_FPoint g = cam.to_screen(m.goal);
      paint.dashed(at, g, color(255, 255, 255, 110), 4.0f);
      paint.cross(g, 5, color(255, 255, 255, 220));
    }
    if (v.overlay[kContacts])
      for (const auto& contact : m.contacts)
        if (const MechPose* other = pose_of(frame, contact.id)) {
          const SDL_FColor c = color(150, 255, 150, 120);
          if (contact.seen) paint.line(at, cam.to_screen(other->pos), c);
          else paint.dashed(at, cam.to_screen(other->pos), c);
        }
    if (v.overlay[kTarget] && m.target >= 0)
      if (const MechPose* target = pose_of(frame, m.target)) paint.line(at, cam.to_screen(target->pos), color(255, 150, 40, 230));
  }
  for (const auto& beam : frame.beams) paint.line(cam.to_screen(beam.from), cam.to_screen(beam.to), color(120, 255, 255));
  for (const auto& round : frame.rounds) paint.circle(cam.to_screen(round.pos), 1.5f, color(255, 240, 200));
  for (const auto& e : frame.recent) {
    if (e.type == "shot" && !e.beam) {
      const Vec3 end = {e.muzzle.x + e.dir.x * kStreakMeters, 0, e.muzzle.z + e.dir.z * kStreakMeters};
      paint.line(cam.to_screen(e.muzzle), cam.to_screen(end), color(255, 240, 200, 200));
    } else if (e.type == "hit") {
      if (const MechPose* hit = pose_of(frame, e.id)) paint.circle(cam.to_screen(hit->pos), 9, color(255, 220, 80, 110));
    }
  }
  for (size_t i = 0; i < frame.mechs.size(); ++i) {
    const MechPose& m = frame.mechs[i];
    const SDL_FPoint at = cam.to_screen(m.pos);
    const SDL_FColor side = kSideColor[side_of(static_cast<int>(i))];
    if (!m.standing) {
      paint.cross(at, 7, color(170, 170, 170));
    } else {
      SDL_FColor cone = side;
      cone.a = 0.35f;
      paint.cone(at, m.heading + m.twist, 15.0f * kPi / 180.0f, 36, cone);  // where the guns point
      paint.circle(at, 6, side);
      paint.arrow(at, screen_direction(m.heading), 16, color(255, 255, 255));  // where the legs walk
    }
    if (static_cast<int>(i) == v.selected) {
      paint.set(color(255, 255, 255));
      const SDL_FRect r = {at.x - 10, at.y - 10, 20, 20};
      SDL_RenderRect(paint.renderer, &r);
    }
    text.draw(std::to_string(m.id), at.x + 8, at.y - 18);
    if (v.overlay[kReasons] && m.standing && !frame.last_decision[i].code.empty())
      text.draw(frame.last_decision[i].code, at.x + 8, at.y + 4, {255, 230, 140, 255});
  }
}

void draw_panel(const Viewer& v, const Frame& frame, Painter& paint, Text& text) {
  if (v.selected < 0 || v.selected >= static_cast<int>(frame.mechs.size())) return;
  const MechPose& m = frame.mechs[v.selected];
  const auto& info = v.log->mechs()[v.selected];
  std::vector<std::string> lines;
  lines.push_back("mech " + std::to_string(m.id) + "  " + info.chassis + "  side " + (info.side == 0 ? "A" : "B"));
  lines.push_back(m.standing ? "standing" : "destroyed");
  char buf[96];
  std::snprintf(buf, sizeof buf, "heat %.0f", m.heat);
  lines.push_back(buf);
  lines.push_back("target " + (m.target >= 0 ? std::to_string(m.target) : std::string("none")));
  lines.push_back("order " + (m.order.empty() ? std::string("none") : m.order));
  const auto& decision = frame.last_decision[v.selected];
  lines.push_back("last reason " + (decision.code.empty() ? std::string("none") : decision.code + " at " + clock_text(decision.t)));
  for (const auto& part : m.parts) {
    std::snprintf(buf, sizeof buf, "part %d  armor %.2f  internal %.2f%s", part.id, part.armor, part.internal,
                  part.destroyed ? "  destroyed" : "");
    lines.push_back(buf);
  }
  const float w = 300, line_h = 17, h = 12 + line_h * lines.size();
  const float x = v.camera.width - w - 10, y = 10;
  paint.box({x, y, w, h}, color(0, 0, 0, 190));
  for (size_t i = 0; i < lines.size(); ++i) text.draw(lines[i], x + 8, y + 6 + line_h * i);
}

void draw_bar(const Viewer& v, Painter& paint, Text& text) {
  const float top = v.bar_top(), w = v.camera.width;
  paint.box({0, top, w, kSeekBarHeight}, color(0, 0, 0, 200));
  const float done = v.log->duration() > 0 ? v.t / v.log->duration() : 0;
  paint.box({0, top, w * done, 4}, color(255, 150, 40));
  char buf[96];
  std::snprintf(buf, sizeof buf, "%s  %s / %s  %gx   1 route  2 target  3 goal  4 contacts  5 reasons",
                v.playing ? "playing" : "paused", clock_text(v.t).c_str(), clock_text(v.log->duration()).c_str(),
                v.speed);
  text.draw(buf, 8, top + 7);
  std::string on;
  for (int i = 0; i < kOverlays; ++i) on += v.overlay[i] ? static_cast<char>('1' + i) : '-';
  text.draw("overlays " + on, w - 120, top + 7);
}

// The window as drawn so far this frame, to a BMP (SDL3 has no PNG writer).
void save_screenshot(SDL_Renderer* renderer, const std::string& path) {
  SDL_Surface* shot = SDL_RenderReadPixels(renderer, nullptr);
  if (!shot) return;
  if (SDL_SaveBMP(shot, path.c_str())) std::printf("mw3: replay: saved %s\n", path.c_str());
  else std::fprintf(stderr, "mw3: replay: cannot save %s: %s\n", path.c_str(), SDL_GetError());
  SDL_DestroySurface(shot);
}

// F12: a shot named by the replay time, beside the log.
std::string shot_path(const Viewer& v) {
  char name[64];
  std::snprintf(name, sizeof name, "replay-%07.2f.bmp", v.t);
  return (std::filesystem::path(v.log_path).parent_path() / name).string();
}

// A test script (replay_view.h): its commands, and how many frames are left
// in the current wait. Scripted runs step a fixed 1/60 s a frame, so the same
// script shows the same times.
struct Script {
  std::vector<std::vector<std::string>> lines;
  size_t next = 0;
  int wait_frames = 0;

  bool load(const std::string& path) {
    std::ifstream in(path);
    if (!in) return false;
    for (std::string line; std::getline(in, line);) {
      std::istringstream words(line);
      std::vector<std::string> command;
      for (std::string w; words >> w;) command.push_back(w);
      if (!command.empty() && command[0][0] != '#') lines.push_back(command);
    }
    return true;
  }
};

SDL_Keycode script_key(const std::string& name) {
  if (name == "space") return SDLK_SPACE;
  if (name == "left") return SDLK_LEFT;
  if (name == "right") return SDLK_RIGHT;
  if (name == "comma") return SDLK_COMMA;
  if (name == "period") return SDLK_PERIOD;
  if (name == "escape") return SDLK_ESCAPE;
  if (name.size() == 1 && name[0] >= '1' && name[0] <= '5') return SDLK_1 + (name[0] - '1');
  return SDLK_UNKNOWN;
}

void push_button(Uint32 type, float x, float y) {
  SDL_Event e{};
  e.type = type;
  e.button.button = SDL_BUTTON_LEFT;
  e.button.down = type == SDL_EVENT_MOUSE_BUTTON_DOWN;
  e.button.x = x, e.button.y = y;
  SDL_PushEvent(&e);
}

// Runs script commands until a wait or the end; events go into the viewer's
// own queue and take effect next frame. False on an unknown command.
bool run_script(Script& s, SDL_Renderer* renderer) {
  if (s.wait_frames > 0) {
    --s.wait_frames;
    return true;
  }
  while (s.next < s.lines.size()) {
    const std::vector<std::string>& c = s.lines[s.next++];
    const auto num = [&](size_t i) { return i < c.size() ? std::strtof(c[i].c_str(), nullptr) : 0.0f; };
    if (c[0] == "wait") {
      s.wait_frames = static_cast<int>(num(1) * 60);
      return true;
    } else if (c[0] == "key" && c.size() > 1) {
      SDL_Event e{};
      e.type = SDL_EVENT_KEY_DOWN;
      e.key.key = script_key(c[1]);
      e.key.down = true;
      SDL_PushEvent(&e);
    } else if (c[0] == "click") {
      push_button(SDL_EVENT_MOUSE_BUTTON_DOWN, num(1), num(2));
      push_button(SDL_EVENT_MOUSE_BUTTON_UP, num(1), num(2));
    } else if (c[0] == "drag") {
      push_button(SDL_EVENT_MOUSE_BUTTON_DOWN, num(1), num(2));
      SDL_Event m{};
      m.type = SDL_EVENT_MOUSE_MOTION;
      m.motion.x = num(3), m.motion.y = num(4);
      m.motion.xrel = num(3) - num(1), m.motion.yrel = num(4) - num(2);
      SDL_PushEvent(&m);
      push_button(SDL_EVENT_MOUSE_BUTTON_UP, num(3), num(4));
    } else if (c[0] == "wheel") {
      SDL_Event w{};
      w.type = SDL_EVENT_MOUSE_WHEEL;
      w.wheel.mouse_x = num(1), w.wheel.mouse_y = num(2), w.wheel.y = num(3);
      SDL_PushEvent(&w);
    } else if (c[0] == "shot" && c.size() > 1) {
      save_screenshot(renderer, c[1]);
    } else if (c[0] == "quit") {
      SDL_Event q{};
      q.type = SDL_EVENT_QUIT;
      SDL_PushEvent(&q);
    } else {
      std::fprintf(stderr, "mw3: replay script: unknown command %s\n", c[0].c_str());
      return false;
    }
  }
  return true;
}

// One input event; false when the viewer should close.
bool handle(Viewer& v, const SDL_Event& e, const Frame& frame) {
  switch (e.type) {
    case SDL_EVENT_QUIT:
      return false;
    case SDL_EVENT_KEY_DOWN:
      switch (e.key.key) {
        case SDLK_ESCAPE: return false;
        case SDLK_SPACE:
          if (v.t >= v.log->duration()) v.t = 0;  // at the end, play again from the start
          v.playing = !v.playing;
          break;
        case SDLK_LEFT: v.jump(-kJumpSeconds); break;
        case SDLK_RIGHT: v.jump(kJumpSeconds); break;
        case SDLK_COMMA: v.speed = std::max(kMinSpeed, v.speed / 2); break;   // the "<" key
        case SDLK_PERIOD: v.speed = std::min(kMaxSpeed, v.speed * 2); break;  // the ">" key
        case SDLK_1: case SDLK_2: case SDLK_3: case SDLK_4: case SDLK_5:
          v.overlay[e.key.key - SDLK_1] = !v.overlay[e.key.key - SDLK_1];
          break;
        default: break;
      }
      break;
    case SDL_EVENT_MOUSE_BUTTON_DOWN:
      if (e.button.button != SDL_BUTTON_LEFT) break;
      v.press_x = e.button.x, v.press_y = e.button.y;
      if (e.button.y >= v.bar_top()) v.seeking = true, v.seek_to(e.button.x);
      else v.panning = true;
      break;
    case SDL_EVENT_MOUSE_MOTION:
      if (v.seeking) v.seek_to(e.motion.x);
      if (v.panning) v.camera.center_x -= e.motion.xrel / v.camera.zoom, v.camera.center_z += e.motion.yrel / v.camera.zoom;
      break;
    case SDL_EVENT_MOUSE_BUTTON_UP:
      if (e.button.button != SDL_BUTTON_LEFT) break;
      // A press that hardly moved is a click: pick a mech, or clear the pick.
      if (v.panning && std::hypot(e.button.x - v.press_x, e.button.y - v.press_y) < 4)
        v.selected = pick_mech(v, frame, e.button.x, e.button.y);
      v.seeking = v.panning = false;
      break;
    case SDL_EVENT_MOUSE_WHEEL: {
      // Zoom about the cursor: the world point under it stays under it.
      float wx = 0, wz = 0;
      v.camera.to_world(e.wheel.mouse_x, e.wheel.mouse_y, &wx, &wz);
      const float factor = std::pow(kZoomStep, e.wheel.y);  // a step per notch, fractions from touchpads
      v.camera.zoom = std::clamp(v.camera.zoom * factor, kMinZoom, kMaxZoom);
      float nx = 0, nz = 0;
      v.camera.to_world(e.wheel.mouse_x, e.wheel.mouse_y, &nx, &nz);
      v.camera.center_x += wx - nx, v.camera.center_z += wz - nz;
      break;
    }
    default:
      break;
  }
  return true;
}

}  // namespace

int run_replay(const std::string& log_path, const std::string& script_path) {
  ReplayLog log;
  std::string error;
  if (!log.load(log_path, &error)) {
    std::fprintf(stderr, "mw3: --replay: %s\n", error.c_str());
    return 2;
  }
  Script script;
  const bool scripted = !script_path.empty();
  if (scripted && !script.load(script_path)) {
    std::fprintf(stderr, "mw3: --replay-script: cannot read %s\n", script_path.c_str());
    return 2;
  }
  Viewer v;
  v.log = &log;
  v.log_path = log_path;
  float box[4];
  log.bounds(box);
  v.terrain = mech3::replay::build_terrain(log.map(), box);
  if (!v.terrain.error.empty()) std::fprintf(stderr, "mw3: replay: no terrain: %s\n", v.terrain.error.c_str());

  if (!SDL_Init(SDL_INIT_VIDEO)) {
    std::fprintf(stderr, "mw3: replay: SDL_Init: %s\n", SDL_GetError());
    return 1;
  }
  SDL_Window* window = nullptr;
  SDL_Renderer* renderer = nullptr;
  const SDL_WindowFlags flags = SDL_WINDOW_RESIZABLE | (scripted ? SDL_WINDOW_HIDDEN : 0);
  if (!SDL_CreateWindowAndRenderer("MW3 replay", 1280, 800, flags, &window, &renderer)) {
    std::fprintf(stderr, "mw3: replay: window: %s\n", SDL_GetError());
    return 1;
  }
  SDL_SetRenderVSync(renderer, 1);
  SDL_SetRenderDrawBlendMode(renderer, SDL_BLENDMODE_BLEND);
  v.terrain_texture = make_terrain_texture(renderer, v.terrain);
  {
    Text text(renderer);
    text.open();
    Painter paint{renderer};
    int w = 0, h = 0;
    SDL_GetRenderOutputSize(renderer, &w, &h);
    v.camera.width = static_cast<float>(w), v.camera.height = static_cast<float>(h);
    fit_camera(&v.camera, box);
    uint64_t last = SDL_GetTicksNS();
    for (bool open = true; open;) {
      const uint64_t now = SDL_GetTicksNS();
      const float elapsed = scripted ? 1.0f / 60 : static_cast<float>(now - last) / 1e9f;
      last = now;
      if (v.playing && !v.seeking) v.t += elapsed * v.speed;
      if (v.t >= log.duration()) v.t = log.duration(), v.playing = false;
      const Frame frame = log.frame_at(v.t);
      SDL_Event e;
      while (SDL_PollEvent(&e)) {
        if (e.type == SDL_EVENT_KEY_DOWN && e.key.key == SDLK_F12) save_screenshot(renderer, shot_path(v));
        else if (!handle(v, e, frame)) open = false;
      }
      SDL_GetRenderOutputSize(renderer, &w, &h);
      v.camera.width = static_cast<float>(w), v.camera.height = static_cast<float>(h);
      paint.box({0, 0, v.camera.width, v.camera.height}, color(70, 70, 70));  // gray ground when there is no terrain
      draw_world(v, frame, paint, text);
      if (!v.terrain.error.empty()) {
        paint.box({0, 0, v.camera.width, 24}, color(120, 30, 30, 220));
        text.draw("no terrain: " + v.terrain.error, 8, 4);
      }
      draw_panel(v, frame, paint, text);
      draw_bar(v, paint, text);
      if (scripted && !run_script(script, renderer)) open = false;
      SDL_RenderPresent(renderer);
    }
  }
  if (v.terrain_texture) SDL_DestroyTexture(v.terrain_texture);
  SDL_DestroyRenderer(renderer);
  SDL_DestroyWindow(window);
  return 0;
}

}  // namespace sdlfe
