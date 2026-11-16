#include "frontend/sdl/replay_ui.h"

#include <SDL3_ttf/SDL_ttf.h>

#include <algorithm>
#include <cmath>
#include <cstdio>
#include <cstdlib>
#include <fstream>
#include <sstream>

#include "gamez/zutil/zutl_path.h"

namespace sdlfe {

using mech3::replay::Frame;
using mech3::replay::MechPose;
using mech3::replay::ReplayLog;
using mech3::replay::Vec3;

SDL_FColor ui_color(uint8_t r, uint8_t g, uint8_t b, uint8_t a) {
  return {r / 255.0f, g / 255.0f, b / 255.0f, a / 255.0f};
}
const SDL_FColor kSideColor[2] = {ui_color(80, 150, 255), ui_color(255, 90, 80)};

std::string clock_text(float seconds) {
  const int whole = static_cast<int>(seconds);
  char buf[32];
  std::snprintf(buf, sizeof buf, "%d:%02d.%d", whole / 60, whole % 60, static_cast<int>((seconds - whole) * 10));
  return buf;
}

SDL_FPoint screen_direction(float yaw) { return {-std::sin(yaw), std::cos(yaw)}; }

const MechPose* pose_of(const Frame& frame, int id) {
  for (const MechPose& p : frame.mechs)
    if (p.id == id) return &p;
  return nullptr;
}

// --- ReplayDraw ---------------------------------------------------------

void ReplayDraw::dashed(SDL_FPoint a, SDL_FPoint b, const SDL_FColor& c, float dash) {
  const float dx = b.x - a.x, dy = b.y - a.y;
  const float length = std::sqrt(dx * dx + dy * dy);
  if (length < 1) return;
  for (float s = 0; s < length; s += 2 * dash) {
    const float e = std::min(s + dash, length);
    line({a.x + dx * s / length, a.y + dy * s / length}, {a.x + dx * e / length, a.y + dy * e / length}, c);
  }
}

void ReplayDraw::cross(SDL_FPoint center, float size, const SDL_FColor& c) {
  line({center.x - size, center.y - size}, {center.x + size, center.y + size}, c);
  line({center.x - size, center.y + size}, {center.x + size, center.y - size}, c);
}

// --- Clock ----------------------------------------------------------------

float ReplayClock::step(float elapsed, bool held) {
  const float before = t;
  if (playing && !held) t += elapsed * speed;
  if (t >= duration) t = duration, playing = false;
  return t - before;
}

void ReplayClock::toggle_play() {
  if (t >= duration) t = 0;
  playing = !playing;
}

void ReplayClock::jump(float seconds) { t = std::clamp(t + seconds, 0.0f, duration); }
void ReplayClock::seek_fraction(float fraction) { t = std::clamp(fraction, 0.0f, 1.0f) * duration; }
void ReplayClock::seek(float seconds) { t = std::clamp(seconds, 0.0f, duration); }
void ReplayClock::slower() { speed = std::max(kMinSpeed, speed / 2); }
void ReplayClock::faster() { speed = std::min(kMaxSpeed, speed * 2); }

float frame_elapsed(uint64_t* last_ns, bool scripted) {
  const uint64_t now = SDL_GetTicksNS();
  const float elapsed = scripted ? 1.0f / 60 : std::min(static_cast<float>(now - *last_ns) / 1e9f, 0.1f);
  *last_ns = now;
  return elapsed;
}

// --- Overlays, panel and bar ---------------------------------------------

void draw_overlays(const Frame& frame, const Overlays& overlays, ReplayDraw& draw, const Projector& projector) {
  const auto screen = [&](const Vec3& v, SDL_FPoint* out) { return projector.to_screen(v, out); };
  for (size_t i = 0; i < frame.mechs.size(); ++i) {
    const MechPose& m = frame.mechs[i];
    SDL_FPoint at;
    if (!m.standing || !screen(m.pos, &at)) continue;
    if (overlays.on[kRoute] && !frame.routes[i].points.empty()) {
      // The legs already walked dim, the waypoint it is heading for ringed,
      // the rest from the mech on.
      const auto& points = frame.routes[i].points;
      const size_t at_point = static_cast<size_t>(std::max(m.at, 0));
      for (size_t k = 1; k < points.size() && k <= at_point; ++k) {
        SDL_FPoint a, b;
        if (screen(points[k - 1], &a) && screen(points[k], &b)) draw.line(a, b, ui_color(255, 230, 90, 70));
      }
      SDL_FPoint prev = at;
      bool prev_ok = true;
      for (size_t k = at_point; k < points.size(); ++k) {
        SDL_FPoint p;
        const bool ok = screen(points[k], &p);
        if (ok && prev_ok) draw.line(prev, p, ui_color(255, 230, 90, 200));
        if (ok) draw.circle(p, k == at_point ? 5.0f : 2.5f, ui_color(255, 230, 90, k == at_point ? 255 : 200));
        prev = p, prev_ok = ok;
      }
    }
    SDL_FPoint p;
    if (overlays.on[kGoal] && m.has_goal && screen(m.goal, &p)) {
      draw.dashed(at, p, ui_color(255, 255, 255, 110), 4.0f);
      draw.cross(p, 5, ui_color(255, 255, 255, 220));
    }
    if (overlays.on[kContacts])
      for (const auto& contact : m.contacts)
        if (const MechPose* other = pose_of(frame, contact.id); other && screen(other->pos, &p)) {
          const SDL_FColor c = ui_color(150, 255, 150, 120);
          if (contact.seen) draw.line(at, p, c);
          else draw.dashed(at, p, c);
        }
    if (overlays.on[kTarget] && m.target >= 0)
      if (const MechPose* target = pose_of(frame, m.target); target && screen(target->pos, &p))
        draw.line(at, p, ui_color(255, 150, 40, 230));
  }
}

void draw_panel(const ReplayLog& log, const Frame& frame, int selected, float screen_width, ReplayDraw& draw) {
  if (selected < 0 || selected >= static_cast<int>(frame.mechs.size())) return;
  const MechPose& m = frame.mechs[selected];
  const mech3::replay::MechInfo* info = log.info_of(m.id);
  std::vector<std::string> lines;
  lines.push_back("mech " + std::to_string(m.id) + "  " + (info ? info->chassis : std::string("?")) + "  side " +
                  (!info ? "?" : info->side == 0 ? "A" : "B"));
  lines.push_back(m.standing ? "standing" : "destroyed");
  char buf[96];
  std::snprintf(buf, sizeof buf, "heat %.0f", m.heat);
  lines.push_back(buf);
  lines.push_back("target " + (m.target >= 0 ? std::to_string(m.target) : std::string("none")));
  lines.push_back("order " + (m.order.empty() ? std::string("none") : m.order));
  const auto& decision = frame.last_decision[selected];
  lines.push_back("last reason " +
                  (decision.code.empty() ? std::string("none") : decision.code + " at " + clock_text(decision.t)));
  for (const auto& part : m.parts) {
    std::snprintf(buf, sizeof buf, "part %d  armor %.2f  internal %.2f%s", part.id, part.armor, part.internal,
                  part.destroyed ? "  destroyed" : "");
    lines.push_back(buf);
  }
  const float w = 300, line_h = 17, h = 12 + line_h * lines.size();
  const float x = screen_width - w - 10, y = 10;
  draw.rect({x, y, w, h}, ui_color(0, 0, 0, 190));
  for (size_t i = 0; i < lines.size(); ++i) draw.text(lines[i], x + 8, y + 6 + line_h * i);
}

void draw_bar(const ReplayClock& clock, const Overlays& overlays, float screen_width, float screen_height,
              ReplayDraw& draw) {
  const float top = bar_top(screen_height), w = screen_width;
  draw.rect({0, top, w, kSeekBarHeight}, ui_color(0, 0, 0, 200));
  const float done = clock.duration > 0 ? clock.t / clock.duration : 0;
  draw.rect({0, top, w * done, 4}, ui_color(255, 150, 40));
  char buf[96];
  std::snprintf(buf, sizeof buf, "%s  %s / %s  %gx (< >)   1 route  2 target  3 goal  4 contacts  5 reasons",
                clock.playing ? "playing" : "paused", clock_text(clock.t).c_str(), clock_text(clock.duration).c_str(),
                clock.speed);
  draw.text(buf, 8, top + 7);
  std::string on;
  for (int i = 0; i < kOverlays; ++i) on += overlays.on[i] ? static_cast<char>('1' + i) : '-';
  draw.text("overlays " + on, w - 120, top + 7);
}

// --- Text -----------------------------------------------------------------

TextRenderer::~TextRenderer() {
  if (font_) TTF_CloseFont(font_);
  if (ttf_ok_) TTF_Quit();
}

void TextRenderer::open() {
  ttf_ok_ = TTF_Init();
  if (!ttf_ok_) return;
  // The game's own Arial when a mount has it, else the system's.
  const std::vector<std::string> tries = {zutl::find("arial.ttf"), "C:/Windows/Fonts/arial.ttf",
                                          "/System/Library/Fonts/Supplemental/Arial.ttf",
                                          "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
                                          "/usr/share/fonts/TTF/DejaVuSans.ttf"};
  for (const std::string& path : tries)
    if (!path.empty() && (font_ = TTF_OpenFont(path.c_str(), 14.0f)) != nullptr) return;
  std::fprintf(stderr, "mw3: replay: no font found, drawing without text\n");
}

SDL_Surface* TextRenderer::render(const std::string& s, SDL_Color c) const {
  if (!font_ || s.empty()) return nullptr;
  return TTF_RenderText_Blended(font_, s.c_str(), 0, c);
}

// --- SdlRendererDraw --------------------------------------------------------

SdlRendererDraw::~SdlRendererDraw() { clear_text(); }

void SdlRendererDraw::set(const SDL_FColor& c) { SDL_SetRenderDrawColorFloat(renderer_, c.r, c.g, c.b, c.a); }

void SdlRendererDraw::line(SDL_FPoint a, SDL_FPoint b, const SDL_FColor& c) {
  set(c);
  SDL_RenderLine(renderer_, a.x, a.y, b.x, b.y);
}

void SdlRendererDraw::circle(SDL_FPoint c, float radius, const SDL_FColor& fill) {
  constexpr int kSegments = 16;
  std::vector<SDL_Vertex> v;
  for (int i = 0; i < kSegments; ++i) {
    const float a0 = 2 * kReplayPi * i / kSegments, a1 = 2 * kReplayPi * (i + 1) / kSegments;
    v.push_back({c, fill, {0, 0}});
    v.push_back({{c.x + radius * std::cos(a0), c.y + radius * std::sin(a0)}, fill, {0, 0}});
    v.push_back({{c.x + radius * std::cos(a1), c.y + radius * std::sin(a1)}, fill, {0, 0}});
  }
  SDL_RenderGeometry(renderer_, nullptr, v.data(), static_cast<int>(v.size()), nullptr, 0);
}

void SdlRendererDraw::rect(const SDL_FRect& r, const SDL_FColor& fill) {
  set(fill);
  SDL_RenderFillRect(renderer_, &r);
}

void SdlRendererDraw::outline(const SDL_FRect& r, const SDL_FColor& c) {
  set(c);
  SDL_RenderRect(renderer_, &r);
}

void SdlRendererDraw::arrow(SDL_FPoint from, SDL_FPoint dir, float length, const SDL_FColor& c) {
  const SDL_FPoint tip = {from.x + dir.x * length, from.y + dir.y * length};
  line(from, tip, c);
  const float head = length * 0.35f;
  for (const float side : {1.0f, -1.0f}) {
    // Back from the tip, 30 degrees off the shaft.
    const float bx = -dir.x * 0.866f - side * dir.y * 0.5f, by = -dir.y * 0.866f + side * dir.x * 0.5f;
    line(tip, {tip.x + bx * head, tip.y + by * head}, c);
  }
}

void SdlRendererDraw::cone(SDL_FPoint from, float yaw, float half_angle, float length, const SDL_FColor& c) {
  const SDL_FPoint left = screen_direction(yaw + half_angle), right = screen_direction(yaw - half_angle);
  const SDL_Vertex v[3] = {{from, c, {0, 0}},
                           {{from.x + left.x * length, from.y + left.y * length}, c, {0, 0}},
                           {{from.x + right.x * length, from.y + right.y * length}, c, {0, 0}}};
  SDL_RenderGeometry(renderer_, nullptr, v, 3, nullptr, 0);
}

float SdlRendererDraw::text(const std::string& s, float x, float y, SDL_Color c) {
  if (!text_renderer_.ready() || s.empty()) return 0;
  if (cache_.size() > 2000) clear_text();  // a long replay's labels; rebuilt as needed
  const std::string key = s + "#" + std::to_string(c.r) + "," + std::to_string(c.g) + "," + std::to_string(c.b);
  SDL_Texture*& tex = cache_[key];
  if (!tex) {
    SDL_Surface* surface = text_renderer_.render(s, c);
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

void SdlRendererDraw::clear_text() {
  for (auto& [key, tex] : cache_) SDL_DestroyTexture(tex);
  cache_.clear();
}

// --- Script -----------------------------------------------------------------

namespace {

SDL_Keycode script_key(const std::string& name) {
  if (name == "space") return SDLK_SPACE;
  if (name == "left") return SDLK_LEFT;
  if (name == "right") return SDLK_RIGHT;
  if (name == "comma") return SDLK_COMMA;
  if (name == "period") return SDLK_PERIOD;
  if (name == "escape") return SDLK_ESCAPE;
  if (name == "enter") return SDLK_RETURN;
  if (name == "f12") return SDLK_F12;
  if (name.size() == 1 && name[0] >= '1' && name[0] <= '5') return SDLK_1 + (name[0] - '1');
  if (name.size() == 1 && name[0] >= 'a' && name[0] <= 'z') return SDLK_A + (name[0] - 'a');
  return SDLK_UNKNOWN;
}

SDL_Scancode script_scancode(SDL_Keycode key) { return SDL_GetScancodeFromKey(key, nullptr); }

void push_key(bool down, const std::string& name) {
  SDL_Event e{};
  e.type = down ? SDL_EVENT_KEY_DOWN : SDL_EVENT_KEY_UP;
  e.key.key = script_key(name);
  e.key.scancode = script_scancode(e.key.key);
  e.key.down = down;
  SDL_PushEvent(&e);
}

void push_button(Uint32 type, float x, float y) {
  SDL_Event e{};
  e.type = type;
  e.button.button = SDL_BUTTON_LEFT;
  e.button.down = type == SDL_EVENT_MOUSE_BUTTON_DOWN;
  e.button.x = x, e.button.y = y;
  SDL_PushEvent(&e);
}

}  // namespace

bool ReplayScript::load(const std::string& path) {
  std::ifstream in(path);
  if (!in) return false;
  for (std::string line; std::getline(in, line);) {
    std::istringstream words(line);
    std::vector<std::string> command;
    for (std::string w; words >> w;) command.push_back(w);
    if (!command.empty() && command[0][0] != '#') lines_.push_back(command);
  }
  return true;
}

bool ReplayScript::run(const ScriptActions& actions) {
  if (wait_frames_ > 0) {
    --wait_frames_;
    return true;
  }
  while (next_ < lines_.size()) {
    const std::vector<std::string>& c = lines_[next_++];
    const auto num = [&](size_t i) { return i < c.size() ? std::strtof(c[i].c_str(), nullptr) : 0.0f; };
    if (c[0] == "wait") {
      wait_frames_ = static_cast<int>(num(1) * 60);
      return true;
    } else if (c[0] == "key" && c.size() > 1) {
      push_key(true, c[1]);
    } else if (c[0] == "keyup" && c.size() > 1) {
      push_key(false, c[1]);
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
      if (actions.shot) actions.shot(c[1]);
    } else if (c[0] == "seek" && c.size() > 1) {
      if (actions.seek) actions.seek(num(1));
    } else if (c[0] == "camera" && c.size() > 5) {
      if (actions.camera) actions.camera(num(1), num(2), num(3), num(4), num(5));
    } else if (c[0] == "follow" && c.size() > 1) {
      if (actions.follow) actions.follow(static_cast<int>(num(1)));
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

}  // namespace sdlfe
