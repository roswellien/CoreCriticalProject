#include "frontend/sdl/replay3d_view.h"

#include <algorithm>
#include <cmath>
#include <cstdio>
#include <cstring>
#include <filesystem>
#include <map>
#include <vector>

#include "frontend/sdl/replay_ui.h"
#include "frontend/sdl/sdl_render3d.h"
#include "gamez/zclass/camera.h"
#include "gamez/zeffect/zeff_anim_run.h"
#include "gamez/zmath/zmth_matrix.h"
#include "gamez/zmodel/gmod_draw.h"
#include "gamez/zmodel/gmod_screen.h"
#include "gamez/zsound/zsnd.h"
#include "gamez/zutil/ztimer.h"
#include "gamez/zvideo/zvid_ddd3d.h"
#include "gamez/zweapon/zwep_init.h"
#include "mech3/app_mech.h"
#include "mech3/replay_puppet.h"
#include "mech3/replay_run.h"
#include "mech3/sound_extra.h"

namespace sdlfe {

namespace {

using mech3::replay::Event;
using mech3::replay::Frame;
using mech3::replay::MechPose;
using mech3::replay::Puppet;
using mech3::replay::ReplayLog;
using mech3::replay::Vec3;

constexpr float kMaxListStep = 0.1f;   // the action lists' longest replay step (plan step 7)
constexpr float kRingMeters = 6.0f;    // the side ring at each mech's feet
constexpr float kLabelMeters = 13.0f;  // the id label above each mech
constexpr float kFollowBack = 25.0f, kFollowUp = 8.0f, kFollowAim = 6.0f;
constexpr float kPickPixels = 40.0f;
constexpr float kLookRate = 0.004f;  // radians per mouse count, as the debug fly camera
constexpr float kMinFly = 5.0f, kMaxFly = 500.0f;
constexpr float kLineWidth = 2.0f;
constexpr size_t kTextCacheMax = 500;

uint32_t argb(const SDL_FColor& c) {
  const auto byte = [](float v) { return static_cast<uint32_t>(std::clamp(v, 0.0f, 1.0f) * 255.0f + 0.5f); };
  return byte(c.a) << 24 | byte(c.r) << 16 | byte(c.g) << 8 | byte(c.b);
}

platform::TLVertex vertex(float x, float y, uint32_t color, float u = 0, float v = 0) {
  // Depth 1 (nearest, reversed) with ZFUNC ALWAYS; specular alpha 255 is no fog.
  return {x, y, 1.0f, 1.0f, color, 0xff000000u, u, v};
}

platform::DrawState overlay_state(int32_t texture) {
  platform::DrawState s;
  s.texture = texture;
  s.blend = true;
  s.depth_write = false;
  s.depth_always = true;
  s.alpha_modulate = texture >= 0;
  s.address_u = s.address_v = 3;  // clamp
  return s;
}

// ReplayDraw through the game's Render3D: screen-pixel quads and fans in the
// frame's 2D pass, text as textures made once per string and color.
class Render3dDraw : public ReplayDraw {
 public:
  ~Render3dDraw() override { clear_text(); }
  void open_text() { text_.open(); }
  void set_render(platform::Render3D* render) {
    if (render != render_) clear_text();
    render_ = render;
  }

  void line(SDL_FPoint a, SDL_FPoint b, const SDL_FColor& c) override {
    if (!render_) return;
    const float dx = b.x - a.x, dy = b.y - a.y, length = std::sqrt(dx * dx + dy * dy);
    if (length < 0.5f) return;
    const float nx = -dy / length * kLineWidth / 2, ny = dx / length * kLineWidth / 2;
    const uint32_t col = argb(c);
    const platform::TLVertex v[4] = {vertex(a.x + nx, a.y + ny, col), vertex(b.x + nx, b.y + ny, col),
                                     vertex(b.x - nx, b.y - ny, col), vertex(a.x - nx, a.y - ny, col)};
    render_->draw(platform::Primitive::kFan, v, 4, overlay_state(-1));
  }
  void circle(SDL_FPoint center, float radius, const SDL_FColor& fill) override {
    if (!render_) return;
    constexpr int kSegments = 16;
    const uint32_t col = argb(fill);
    platform::TLVertex v[kSegments + 2];
    v[0] = vertex(center.x, center.y, col);
    for (int i = 0; i <= kSegments; ++i) {
      const float a = 2 * kReplayPi * i / kSegments;
      v[i + 1] = vertex(center.x + radius * std::cos(a), center.y + radius * std::sin(a), col);
    }
    render_->draw(platform::Primitive::kFan, v, kSegments + 2, overlay_state(-1));
  }
  void rect(const SDL_FRect& r, const SDL_FColor& fill) override {
    if (!render_) return;
    const uint32_t col = argb(fill);
    const platform::TLVertex v[4] = {vertex(r.x, r.y, col), vertex(r.x + r.w, r.y, col),
                                     vertex(r.x + r.w, r.y + r.h, col), vertex(r.x, r.y + r.h, col)};
    render_->draw(platform::Primitive::kFan, v, 4, overlay_state(-1));
  }
  float text(const std::string& s, float x, float y, SDL_Color c = {235, 235, 235, 255}) override {
    if (!render_ || !text_.ready() || s.empty()) return 0;
    if (cache_.size() > kTextCacheMax) clear_text();
    const std::string key = s + "#" + std::to_string(c.r) + "," + std::to_string(c.g) + "," + std::to_string(c.b);
    auto found = cache_.find(key);
    if (found == cache_.end()) {
      Uploaded up = upload(s, c);
      if (up.handle < 0) return 0;
      found = cache_.emplace(key, up).first;
    }
    const Uploaded& t = found->second;
    const float left = std::round(x), top = std::round(y);
    const platform::TLVertex v[4] = {vertex(left, top, 0xffffffffu, 0, 0), vertex(left + t.w, top, 0xffffffffu, 1, 0),
                                     vertex(left + t.w, top + t.h, 0xffffffffu, 1, 1),
                                     vertex(left, top + t.h, 0xffffffffu, 0, 1)};
    render_->draw(platform::Primitive::kFan, v, 4, overlay_state(t.handle));
    return static_cast<float>(t.w);
  }

 private:
  struct Uploaded {
    int32_t handle = -1;
    int w = 0, h = 0;
  };
  // The string's surface as tightly packed RGBA8 rows, made a texture.
  Uploaded upload(const std::string& s, SDL_Color c) {
    Uploaded up;
    SDL_Surface* surface = text_.render(s, c);
    if (!surface) return up;
    SDL_Surface* rgba = SDL_ConvertSurface(surface, SDL_PIXELFORMAT_RGBA32);
    SDL_DestroySurface(surface);
    if (!rgba) return up;
    std::vector<uint8_t> pixels(static_cast<size_t>(rgba->w) * rgba->h * 4);
    for (int row = 0; row < rgba->h; ++row)
      std::memcpy(&pixels[static_cast<size_t>(row) * rgba->w * 4],
                  static_cast<const uint8_t*>(rgba->pixels) + static_cast<size_t>(row) * rgba->pitch,
                  static_cast<size_t>(rgba->w) * 4);
    up.w = rgba->w, up.h = rgba->h;
    up.handle = render_->create_texture(up.w, up.h, pixels.data(), 4);  // 4: an alpha plane
    SDL_DestroySurface(rgba);
    return up;
  }
  void clear_text() {
    if (render_)
      for (auto& [key, t] : cache_) render_->release_texture(t.handle);
    cache_.clear();
  }
  platform::Render3D* render_ = nullptr;
  TextRenderer text_;
  std::map<std::string, Uploaded> cache_;
};

// World to screen through the game's own projection of this frame's view.
// A point off the screen or behind the camera is not drawn: the projection
// clamps those to the screen's edge (gmod_screen.h).
class GameProjector : public Projector {
 public:
  bool to_screen(const Vec3& world, SDL_FPoint* out) const override {
    const zmth::Vec3 in = {world.x, world.y, world.z};
    zmth::Vec3 screen{};
    if (zmod::project_point(&in, &screen) != 0) return false;
    *out = {screen.x, screen.y};
    return true;
  }
};

bool is_fly_key(SDL_Scancode code) {
  switch (code) {
    case SDL_SCANCODE_W: case SDL_SCANCODE_A: case SDL_SCANCODE_S:
    case SDL_SCANCODE_D: case SDL_SCANCODE_Q: case SDL_SCANCODE_E:
      return true;
    default:
      return false;
  }
}

// The shots in flight. The puppets play the fire and impact effects, but the
// game draws a beam and a round's model from its weapon object, which a
// replay has none of; so beams are drawn as lines and rounds as dots, always,
// whatever overlays are on.
void draw_shots(const Frame& frame, Render3dDraw& draw, const GameProjector& projector) {
  const SDL_FColor beam_core = ui_color(255, 245, 230), beam_glow = ui_color(255, 90, 60);
  for (const auto& beam : frame.beams) {
    SDL_FPoint a, b;
    if (!projector.to_screen(beam.from, &a) || !projector.to_screen(beam.to, &b)) continue;
    // A glow either side of a bright core, a pixel apart.
    draw.line({a.x, a.y - 1}, {b.x, b.y - 1}, beam_glow);
    draw.line({a.x, a.y + 1}, {b.x, b.y + 1}, beam_glow);
    draw.line(a, b, beam_core);
  }
  const SDL_FColor round_color = ui_color(255, 220, 120);
  for (const auto& round : frame.rounds) {
    SDL_FPoint p;
    if (projector.to_screen(round.pos, &p)) draw.rect({p.x - 2, p.y - 2, 4, 4}, round_color);
  }
}

}  // namespace

struct Replay3dView::State {
  const mech3::replay::ReplayRun* run = nullptr;
  const ReplayLog* log = nullptr;
  FrameRenderer* render = nullptr;
  std::function<void()> request_quit;
  std::string log_path_dir;

  ReplayScript script;
  bool scripted = false, script_read = true;
  ScriptActions actions;

  ReplayClock clock;
  Overlays overlays;
  uint64_t last_ns = 0;
  float real_dt = 0, real_elapsed = 0;
  float posed_t = -1;  // the replay time the puppets show, -1 before the first
  bool started = false, quit_box_open = false, seek_pending = false;
  // Ours, in place of the game's quit box: that one is 640x480 art scaled up
  // to the window, so it shows blurred and blocky at a modern size.
  bool confirm_open = false;

  std::map<int, std::unique_ptr<Puppet>> puppets;  // by mech id
  Frame frame;

  // The camera: flown (Unreal style, as the debug fly camera) or following.
  float eye[3] = {0, 100, 0};
  float yaw = 0, pitch = 0.6f;  // pitch positive looks down
  float fly_speed = 40.0f;      // meters per second
  bool held[SDL_SCANCODE_COUNT] = {};
  bool looking = false, seeking = false;
  int follow_id = -1;
  int selected = -1;  // index in frame.mechs

  Render3dDraw draw;
  GameProjector projector;
  float screen_w = 640, screen_h = 480;
  std::string pending_shot, shot_in_flight;
  // The script's seek, camera and follow, applied as the next frame starts,
  // as its keys are: a shot before them shows the frame before them.
  std::vector<std::function<void()>> next_frame;

  void pose();
  void start_effects(const Event& e);
  void fly(float dt);
  void seek_at(float window_x);
  void pick(float window_x, float window_y);
  void to_screen_px(float window_x, float window_y, float* x, float* y) const;
};

Replay3dView::Replay3dView(const mech3::replay::ReplayRun& run, FrameRenderer* render,
                           const std::string& script_path, std::function<void()> request_quit)
    : s_(new State()) {
  State& s = *s_;
  s.run = &run;
  s.log = &run.log();
  s.render = render;
  s.request_quit = std::move(request_quit);
  s.clock.duration = s.log->duration();
  s.scripted = !script_path.empty();
  if (s.scripted) s.script_read = s.script.load(script_path);
  s.log_path_dir = script_path.empty() ? std::string(".") : std::filesystem::path(script_path).parent_path().string();
  s.actions.shot = [this](const std::string& path) { s_->pending_shot = path; };
  s.actions.seek = [this](float t) { s_->next_frame.push_back([this, t] { s_->clock.seek(t); }); };
  s.actions.camera = [this](float x, float y, float z, float yaw, float pitch) {
    s_->next_frame.push_back([this, x, y, z, yaw, pitch] {
      State& st = *s_;
      st.eye[0] = x, st.eye[1] = y, st.eye[2] = z;
      st.yaw = yaw, st.pitch = pitch;
      st.follow_id = -1;
    });
  };
  s.actions.follow = [this](int id) { s_->next_frame.push_back([this, id] { s_->follow_id = id; }); };
  s.draw.open_text();
}

Replay3dView::~Replay3dView() = default;

bool Replay3dView::ready(std::string* message) const {
  if (s_->script_read) return true;
  *message = "--replay-script: cannot read the script";
  return false;
}

void Replay3dView::start() {
  State& s = *s_;
  s.started = true;
  s.frame = s.log->frame_at(0);
  for (const auto& info : s.log->mechs()) {
    const MechPose* pose = pose_of(s.frame, info.id);
    if (!pose) continue;
    std::string error;
    auto puppet = Puppet::create(info.chassis, info.side, *pose, &error);
    if (!puppet) {
      std::fprintf(stderr, "mw3: replay3d: mech %d (%s): %s\n", info.id, info.chassis.c_str(), error.c_str());
      continue;
    }
    s.puppets[info.id] = std::move(puppet);
  }
  // The camera starts behind the first mech (a map-wide view from above is
  // lost in the maps' fog); any fly key or a look lets it go.
  if (!s.frame.mechs.empty()) s.follow_id = s.frame.mechs[0].id;
  s.last_ns = SDL_GetTicksNS();
  std::printf("mw3: replay3d: %zu puppets, %.1f s of match\n", s.puppets.size(), s.clock.duration);
}

void Replay3dView::before_lists(bool quit_box_open) {
  State& s = *s_;
  s.quit_box_open = quit_box_open || s.confirm_open;
  quit_box_open = s.quit_box_open;
  for (const auto& apply : s.next_frame) apply();
  s.next_frame.clear();
  // Every seek (keys, the bar, the script) lands before this frame's step:
  // a clock away from the shown time is one, however long the frame was.
  s.seek_pending = s.posed_t >= 0 && s.clock.t != s.posed_t;
  if (quit_box_open) {
    // The box takes the input: keys released under it never reach handle().
    std::fill(std::begin(s.held), std::end(s.held), false);
    s.looking = s.seeking = false;
  }
  s.real_elapsed = frame_elapsed(&s.last_ns, s.scripted);
  // The replay pauses under the quit box; the lists then run on a 0 step.
  const float moved = quit_box_open ? 0.0f : s.clock.step(s.real_elapsed, s.seeking);
  s.real_dt = ztimer::state().dt;
  ztimer::state().dt = std::clamp(moved, 0.0f, kMaxListStep);
}

void Replay3dView::after_lists() {
  State& s = *s_;
  ztimer::state().dt = s.real_dt;
  if (s.scripted && s.started && !s.script.run(s.actions)) {
    std::fprintf(stderr, "mw3: replay3d: the script failed\n");
    if (s.request_quit) s.request_quit();
  }
  mech3::mech_set_game_time(s.clock.t);
  if (!s.started) return;
  s.pose();
  if (!s.quit_box_open) s.fly(s.real_elapsed);
}

void Replay3dView::State::pose() {
  const float t = clock.t;
  frame = log->frame_at(t);
  // A seek (seek_pending): the puppets are set straight to the new time and
  // no effect starts for the span skipped.
  const bool first = posed_t < 0;
  const bool seeked = !first && (seek_pending || t < posed_t);
  if (t < posed_t) mech3::sound_extras_rearm();
  for (auto& [id, puppet] : puppets) {
    const MechPose* p = pose_of(frame, id);
    if (!p) continue;
    const std::vector<int> lost = log->parts_lost_by(id, t);
    // Parts come back only by making the mech again (Puppet::rebuild).
    const auto detachable = std::count_if(lost.begin(), lost.end(), Puppet::detachable);
    if (seeked && static_cast<size_t>(detachable) < puppet->detached().size()) {
      std::string error;
      if (!puppet->rebuild(*p, &error)) std::fprintf(stderr, "mw3: replay3d: mech %d: %s\n", id, error.c_str());
    }
    puppet->set(*p, lost, first || seeked ? 1.0f / 60 : t - posed_t);
  }
  if (!first && !seeked && t > posed_t)
    for (const Event& e : log->fire_between(posed_t, t)) start_effects(e);
  posed_t = t;
}

// A logged shot's fire effect and sound at its muzzle, or a hit's impact
// effect where it struck (the default soil), from the weapon's own def.
void Replay3dView::State::start_effects(const Event& e) {
  zwep::WeaponDef* def = zwep::find_def(e.weapon.c_str());
  if (!def) return;
  const zwep::Effect* effect = nullptr;
  float pos[3], dir[3] = {0, 0, 0};
  static const float kZero[3] = {};
  if (e.type == "shot") {
    effect = &def->fire;
    pos[0] = e.muzzle.x, pos[1] = e.muzzle.y, pos[2] = e.muzzle.z;
    dir[0] = e.dir.x, dir[1] = e.dir.y, dir[2] = e.dir.z;
  } else if (e.type == "hit" && e.has_at && def->impacts) {
    effect = &def->impacts[zwep::kSoilDefault];
    pos[0] = e.at.x, pos[1] = e.at.y, pos[2] = e.at.z;
  }
  if (!effect) return;
  if (effect->animation)
    zeff::anim_start_at(static_cast<zeff::AnimDef*>(effect->animation), nullptr, pos, kZero, dir);
  if (effect->sound_count > 0 && effect->sounds[0])
    zsnd::play_at(static_cast<zsnd::Object*>(effect->sounds[0]), pos, 1.0f, nullptr);
}

void Replay3dView::State::fly(float dt) {
  const auto key = [&](SDL_Scancode c) { return held[c] ? 1.0f : 0.0f; };
  const float forward = key(SDL_SCANCODE_W) - key(SDL_SCANCODE_S);
  const float strafe = key(SDL_SCANCODE_D) - key(SDL_SCANCODE_A);
  const float rise = key(SDL_SCANCODE_E) - key(SDL_SCANCODE_Q);
  if (forward == 0 && strafe == 0 && rise == 0) return;
  follow_id = -1;  // any fly key lets go of a followed mech
  // The debug fly camera's axes (debug_states.cpp).
  const float fwd[3] = {std::cos(pitch) * std::sin(yaw), -std::sin(pitch), std::cos(pitch) * std::cos(yaw)};
  const float right[3] = {-std::cos(yaw), 0, std::sin(yaw)};
  const float step = fly_speed * dt;
  for (int i = 0; i < 3; ++i) eye[i] += (forward * fwd[i] + strafe * right[i]) * step;
  eye[1] += rise * step;
}

void Replay3dView::place_camera(zcls::Node* camera) {
  State& s = *s_;
  if (!camera || !s.started) return;
  if (s.follow_id >= 0) {
    if (const MechPose* p = pose_of(s.frame, s.follow_id)) {
      // Behind the mech's heading (its forward axis, -z turned about +y).
      const float ahead[3] = {-std::sin(p->heading), 0, -std::cos(p->heading)};
      const float aim[3] = {p->pos.x, p->pos.y + kFollowAim, p->pos.z};
      s.eye[0] = aim[0] - ahead[0] * kFollowBack;
      s.eye[1] = p->pos.y + kFollowUp + kFollowAim;
      s.eye[2] = aim[2] - ahead[2] * kFollowBack;
      const float d[3] = {aim[0] - s.eye[0], aim[1] - s.eye[1], aim[2] - s.eye[2]};
      const float flat = std::sqrt(d[0] * d[0] + d[2] * d[2]);
      s.yaw = std::atan2(d[0], d[2]);
      s.pitch = std::atan2(-d[1], flat);
    }
  }
  // As a debug launch places the mission's camera (app_mission.cpp).
  zcls::camera_set_rotation(camera, -s.pitch, s.yaw + kReplayPi, 0.0f);
  zcls::camera_set_position(camera, s.eye[0], s.eye[1], s.eye[2]);
}

void Replay3dView::draw_overlay() {
  State& s = *s_;
  if (!s.started) return;
  s.draw.set_render(zvid::render3d());
  const float* rect = zmod::draw_state().point_rect;
  if (rect[2] > rect[0]) s.screen_w = rect[2] + 1, s.screen_h = rect[3] + 1;

  // Side rings and id labels, then the shared overlays, panel and bar.
  for (const MechPose& m : s.frame.mechs) {
    const auto* info = s.log->info_of(m.id);
    const SDL_FColor side = kSideColor[info ? std::clamp(info->side, 0, 1) : 0];
    if (m.standing) {
      constexpr int kSegments = 24;
      SDL_FPoint prev{};
      bool prev_ok = false;
      for (int i = 0; i <= kSegments; ++i) {
        const float a = 2 * kReplayPi * i / kSegments;
        SDL_FPoint p;
        const bool ok = s.projector.to_screen({m.pos.x + kRingMeters * std::cos(a), m.pos.y + 0.2f,
                                               m.pos.z + kRingMeters * std::sin(a)}, &p);
        if (ok && prev_ok) s.draw.line(prev, p, side);
        prev = p, prev_ok = ok;
      }
    }
    SDL_FPoint label;
    if (s.projector.to_screen({m.pos.x, m.pos.y + kLabelMeters, m.pos.z}, &label)) {
      s.draw.text(std::to_string(m.id), label.x - 4, label.y - 8);
      const size_t index = static_cast<size_t>(&m - s.frame.mechs.data());
      if (s.overlays.on[kReasons] && m.standing && !s.frame.last_decision[index].code.empty())
        s.draw.text(s.frame.last_decision[index].code, label.x + 8, label.y - 8, {255, 230, 140, 255});
    }
  }
  draw_overlays(s.frame, s.overlays, s.draw, s.projector);
  draw_panel(*s.log, s.frame, s.selected, s.screen_w, s.draw);
  draw_bar(s.clock, s.overlays, s.screen_w, s.screen_h, s.draw);
  draw_shots(s.frame, s.draw, s.projector);
  if (s.confirm_open) {
    const SDL_FRect box{s.screen_w / 2 - 150, s.screen_h / 2 - 40, 300, 80};
    s.draw.rect(box, ui_color(20, 24, 28));
    s.draw.text("Quit the replay?", box.x + 20, box.y + 18);
    s.draw.text("Y: quit     N or Esc: go back", box.x + 20, box.y + 46, {200, 200, 200, 255});
  } else if (s.quit_box_open) {
    s.draw.text("paused: the quit box is open", 8, 8);
  }
  if (!s.pending_shot.empty() && s.render) {
    // The renderer keeps the path's pointer until the frame is shown.
    s.shot_in_flight = s.pending_shot;
    s.render->capture_next(s.shot_in_flight.c_str());
    std::printf("mw3: replay3d: shot %s at %.2f s\n", s.shot_in_flight.c_str(), s.clock.t);
    s.pending_shot.clear();
  }
}

void Replay3dView::quit() {
  if (s_->request_quit) s_->request_quit();
}

void Replay3dView::State::to_screen_px(float window_x, float window_y, float* x, float* y) const {
  int vx = 0, vy = 0, vw = 0, vh = 0;
  if (render) render->viewport(&vx, &vy, &vw, &vh);
  if (vw <= 0 || vh <= 0) {
    *x = window_x, *y = window_y;
    return;
  }
  *x = (window_x - vx) * screen_w / vw;
  *y = (window_y - vy) * screen_h / vh;
}

void Replay3dView::State::seek_at(float window_x) {
  float x = 0, y = 0;
  to_screen_px(window_x, 0, &x, &y);
  clock.seek_fraction(x / screen_w);
}

void Replay3dView::State::pick(float window_x, float window_y) {
  float x = 0, y = 0;
  to_screen_px(window_x, window_y, &x, &y);
  int best = -1;
  float best_d = kPickPixels;
  for (size_t i = 0; i < frame.mechs.size(); ++i) {
    const MechPose& m = frame.mechs[i];
    SDL_FPoint p;
    if (!projector.to_screen({m.pos.x, m.pos.y + kLabelMeters / 2, m.pos.z}, &p)) continue;
    const float d = std::hypot(p.x - x, p.y - y);
    if (d <= best_d) best_d = d, best = static_cast<int>(i);
  }
  selected = best;
  follow_id = best >= 0 ? frame.mechs[best].id : -1;
}

bool Replay3dView::handle(const SDL_Event& e) {
  State& s = *s_;
  if (!s.started) return false;
  if (s.confirm_open) {
    // The box takes every key and click while it is up.
    if (e.type == SDL_EVENT_KEY_DOWN) {
      if (e.key.key == SDLK_Y) {
        if (s.request_quit) s.request_quit();
      } else if (e.key.key == SDLK_N || e.key.key == SDLK_ESCAPE) {
        s.confirm_open = false;
      }
    }
    return e.type == SDL_EVENT_KEY_DOWN || e.type == SDL_EVENT_KEY_UP || e.type == SDL_EVENT_MOUSE_BUTTON_DOWN ||
           e.type == SDL_EVENT_MOUSE_BUTTON_UP || e.type == SDL_EVENT_MOUSE_MOTION || e.type == SDL_EVENT_MOUSE_WHEEL;
  }
  if (s.quit_box_open) return false;
  switch (e.type) {
    case SDL_EVENT_KEY_DOWN:
      if (is_fly_key(e.key.scancode)) {
        s.held[e.key.scancode] = true;
        return true;
      }
      switch (e.key.key) {
        case SDLK_SPACE: s.clock.toggle_play(); return true;
        case SDLK_LEFT: s.clock.jump(-ReplayClock::kJumpSeconds); return true;
        case SDLK_RIGHT: s.clock.jump(ReplayClock::kJumpSeconds); return true;
        case SDLK_COMMA: case SDLK_LESS: s.clock.slower(); return true;
        case SDLK_PERIOD: case SDLK_GREATER: s.clock.faster(); return true;
        case SDLK_1: case SDLK_2: case SDLK_3: case SDLK_4: case SDLK_5:
          s.overlays.toggle(static_cast<int>(e.key.key - SDLK_1));
          return true;
        case SDLK_F12: {
          char name[64];
          std::snprintf(name, sizeof name, "replay3d-%07.2f.bmp", s.clock.t);
          s.pending_shot = (std::filesystem::path(s.log_path_dir) / name).string();
          return true;
        }
        case SDLK_ESCAPE:
          s.confirm_open = true;
          if (s.looking)
            if (SDL_Window* w = SDL_GetWindowFromID(e.key.windowID)) SDL_SetWindowRelativeMouseMode(w, false);
          return true;
        default: return false;  // the rest: the game's (no command fires, plan step 7)
      }
    case SDL_EVENT_KEY_UP:
      if (!is_fly_key(e.key.scancode)) return false;
      s.held[e.key.scancode] = false;
      return true;
    case SDL_EVENT_MOUSE_BUTTON_DOWN:
      if (e.button.button == SDL_BUTTON_RIGHT) {
        s.looking = true;
        if (SDL_Window* w = SDL_GetWindowFromID(e.button.windowID)) SDL_SetWindowRelativeMouseMode(w, true);
        return true;
      }
      if (e.button.button != SDL_BUTTON_LEFT) return false;
      {
        float x = 0, y = 0;
        s.to_screen_px(e.button.x, e.button.y, &x, &y);
        if (y >= bar_top(s.screen_h)) s.seeking = true, s.seek_at(e.button.x);
        else s.pick(e.button.x, e.button.y);
      }
      return true;
    case SDL_EVENT_MOUSE_MOTION:
      if (s.looking) {
        // Yaw grows toward +x, which is the camera's left (fly()'s right is -x
        // at yaw 0), so a mouse moved right turns it the other way.
        s.yaw -= e.motion.xrel * kLookRate;
        s.pitch = std::clamp(s.pitch + e.motion.yrel * kLookRate, -1.5f, 1.5f);
        s.follow_id = -1;
      }
      if (s.seeking) s.seek_at(e.motion.x);
      return s.looking || s.seeking;
    case SDL_EVENT_MOUSE_BUTTON_UP:
      if (e.button.button == SDL_BUTTON_RIGHT) {
        s.looking = false;
        if (SDL_Window* w = SDL_GetWindowFromID(e.button.windowID)) SDL_SetWindowRelativeMouseMode(w, false);
        return true;
      }
      if (e.button.button == SDL_BUTTON_LEFT) {
        s.seeking = false;
        return true;
      }
      return false;
    case SDL_EVENT_MOUSE_WHEEL:
      s.fly_speed = std::clamp(s.fly_speed * std::pow(1.25f, e.wheel.y), kMinFly, kMaxFly);
      return true;
    default:
      return false;
  }
}

}  // namespace sdlfe
