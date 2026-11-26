#include "frontend/sdl/replay3d_view.h"

#include "frontend/sdl/arena_benchmark.h"

#include <limits>

#include <algorithm>
#include <cmath>
#include <cstdio>
#include <cstring>
#include <filesystem>
#include <map>
#include <set>
#include <string_view>
#include <vector>

#include "frontend/sdl/replay_ui.h"
#include "frontend/sdl/sdl_render3d.h"
#include "gamez/zclass/camera.h"
#include "gamez/zeffect/zeff_anim_init.h"
#include "gamez/zeffect/zeff_anim_run.h"
#include "gamez/zmath/zmth_matrix.h"
#include "gamez/zmodel/gmod_draw.h"
#include "gamez/zmodel/gmod_screen.h"
#include "gamez/zsound/zsnd.h"
#include "gamez/zutil/ztimer.h"
#include "gamez/zvideo/zvid_ddd3d.h"
#include "gamez/zweapon/zweapon.h"
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

// The longest step the game's action lists (effect animations) take in one
// frame: a slow frame or a fast replay speed runs them in pieces no longer
// than this, as the game's own frame would, so no effect jumps ahead.
constexpr float kMaxListStep = 0.1f;
// How far ahead a death looks for a thigh lost with it: the log's state lines
// are 0.1 s apart (arena_log.cpp), so two of them.
constexpr float kLegKillLookahead = 0.25f;
constexpr float kRingMeters = 6.0f;    // the side ring at each mech's feet
constexpr float kLabelMeters = 13.0f;  // the id label above each mech
constexpr float kLabelNearPixels = 160.0f;  // a mech this tall on a 720-line screen gets full-size text
constexpr float kLabelMinSize = 0.55f;      // the smallest a far mech's label gets
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
  // Called once at the start of each frame's overlay. A full text cache is
  // emptied here, never inside text(): draws are only recorded until the end
  // of the scene, so freeing a texture mid-frame drew the text already queued
  // that frame as white boxes.
  void begin_frame(platform::Render3D* render) {
    if (render != render_ || cache_.size() > kTextCacheMax) clear_text();
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
  float text(const std::string& s, float x, float y, SDL_Color c = {235, 235, 235, 255},
             float size = 1.0f) override {
    if (!render_ || !text_.ready() || s.empty()) return 0;
    const std::string key = s + "#" + std::to_string(c.r) + "," + std::to_string(c.g) + "," + std::to_string(c.b);
    auto found = cache_.find(key);
    if (found == cache_.end()) {
      Uploaded up = upload(s, c);
      if (up.handle < 0) return 0;
      found = cache_.emplace(key, up).first;
    }
    const Uploaded& t = found->second;
    const float left = std::round(x), top = std::round(y);
    const float w = static_cast<float>(t.w) * size, h = static_cast<float>(t.h) * size;
    const platform::TLVertex v[4] = {vertex(left, top, 0xffffffffu, 0, 0), vertex(left + w, top, 0xffffffffu, 1, 0),
                                     vertex(left + w, top + h, 0xffffffffu, 1, 1),
                                     vertex(left, top + h, 0xffffffffu, 0, 1)};
    render_->draw(platform::Primitive::kFan, v, 4, overlay_state(t.handle));
    return w;
  }

 protected:
  void scale_changed(float scale) override {
    text_.set_scale(scale);
    clear_text();
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

zwep::Vec3f3 f3(const Vec3& v) { return {v.x, v.y, v.z}; }

// The node rotation a direction gives, as zwep_shot.cpp's pitch_of and yaw_of.
void rotation_of(const zwep::Vec3f3& d, float out[3]) {
  out[0] = std::asin(std::clamp(d.y, -1.0f, 1.0f));
  out[1] = std::atan2(-d.x, -d.z);
  out[2] = 0;
}

// A logged beam drawn with the game's own beam node (zwep::beam_make: the
// weapon's FLYOUT model on a node stretched along the beam). It is never
// started, so the game's weapon tick never casts it or deals damage: the
// log's from and to place it, and its pulse is beam_update's.
struct LiveBeam {
  zwep::Beam* beam = nullptr;
  zwep::Handle light = nullptr;
  float age = 0;
  bool seen = false;
};

// A logged round drawn as the game draws a projectile (zwep_shot.cpp
// pool_take and spawn): a node with the FLYOUT model under it (a pooled copy
// when the model is animated) and the FLYOUT animation following it, moved to
// the log's positions instead of flown.
struct LiveRound {
  zwep::WeaponDef* def = nullptr;
  zwep::Handle node = nullptr, model = nullptr, flyout_anim = nullptr, attached_anim = nullptr, model_anim = nullptr;
  bool pooled_model = false, has_last = false, seen = false;
  Vec3 last;
};

// The beam's origin and direction pointers: beam_make keeps them for
// beam_update, which a replay beam never reaches, so one still pair serves all.
const zwep::Vec3f3 kStillOrigin{}, kStillDir{0, 0, 1};

}  // namespace

struct Replay3dView::State {
  const mech3::replay::ReplayRun* run = nullptr;
  const ReplayLog* log = nullptr;
  FrameRenderer* render = nullptr;
  benchmark::Run* benchmark_run = nullptr;
  bool startup_frame = true;
  double playback_elapsed = 0;
  float event_cursor = 0;
  std::function<void()> request_quit;
  std::string screenshot_dir;  // F12's screenshots: the script's folder, else the current one

  ReplayScript script;
  bool scripted = false, script_read = true;
  ScriptActions actions;

  ReplayClock clock;
  Overlays overlays;
  uint64_t last_ns = 0;
  float real_dt = 0, real_elapsed = 0;
  float posed_t = -1;  // the replay time the puppets show, -1 before the first
  bool started = false, quit_box_open = false, seek_pending = false;

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
  std::string pending_screenshot, screenshot_in_flight;
  // The script's seek, camera and follow, applied as the next frame starts,
  // as its keys are: a shot before them shows the frame before them.
  std::vector<std::function<void()>> next_frame;

  // The shots in flight, by (shooter, weapon, nth of that pair) and round id.
  std::map<std::string, LiveBeam> live_beams;
  std::map<int, LiveRound> live_rounds;
  std::set<zeff::AnimDef*> impact_animations;

  // Lets go of every held key, the mouse look and a seek drag, for when the
  // releases can't reach handle(): the quit box takes the input, or the
  // window loses focus. The pointer is never captured (the input layer leaves
  // it free in a replay, mw3_main.cpp), so there is nothing else to let go.
  void release_input() {
    std::fill(std::begin(held), std::end(held), false);
    looking = seeking = false;
  }

  void pose();
  void sync_shots(float dt);
  void sync_beams(float dt);
  void sync_rounds();
  bool make_round(zwep::WeaponDef* def, LiveRound* made);
  void free_round(LiveRound& r);
  void start_effects(const Event& e);
  void start_missile_explosion(const zwep::Vec3f3& at);
  void fly(float dt);
  void seek_at(float window_x);
  void pick(float window_x, float window_y);
  void to_screen_px(float window_x, float window_y, float* x, float* y) const;
};

Replay3dView::Replay3dView(const mech3::replay::ReplayRun& run, FrameRenderer* render,
                           const std::string& script_path, std::function<void()> request_quit,
                           benchmark::Run* benchmark_run)
    : s_(new State()) {
  State& s = *s_;
  s.run = &run;
  s.log = &run.log();
  s.render = render;
  s.benchmark_run = benchmark_run;
  s.request_quit = std::move(request_quit);
  s.clock.duration = s.log->duration() + ReplayClock::kEndHoldSeconds;
  s.scripted = !script_path.empty();
  if (s.scripted) s.script_read = s.script.load(script_path);
  s.screenshot_dir = script_path.empty() ? std::string(".") : std::filesystem::path(script_path).parent_path().string();
  s.actions.shot = [this](const std::string& path) { s_->pending_screenshot = path; };
  s.actions.seek = [this](float t) { s_->next_frame.push_back([this, t] { s_->clock.seek(t); }); };
  s.actions.camera = [this](float x, float y, float z, float yaw, float pitch) {
    s_->next_frame.push_back([this, x, y, z, yaw, pitch] {
      State& st = *s_;
      st.eye[0] = x, st.eye[1] = y, st.eye[2] = z;
      st.yaw = yaw, st.pitch = pitch;
      st.follow_id = -1;
    });
  };
  // As a click on the mech: followed and selected (its panel and lines).
  s.actions.follow = [this](int id) {
    s_->next_frame.push_back([this, id] {
      State& st = *s_;
      st.follow_id = id, st.selected = -1;
      for (size_t i = 0; i < st.frame.mechs.size(); ++i)
        if (st.frame.mechs[i].id == id) st.selected = static_cast<int>(i);
    });
  };
  if (!s.benchmark_run) s.draw.open_text();
}

// The beams and rounds in flight are not freed here: their nodes are in the
// mission's world, which a replay leaves to the process's end (mw3_main.cpp,
// after app.run), so freeing them now would touch a world being torn down.
Replay3dView::~Replay3dView() = default;

bool Replay3dView::ready(std::string* message) const {
  if (s_->script_read) return true;
  *message = "--replay-script: cannot read the script";
  return false;
}

void Replay3dView::scene_load_enter() {
  if (auto* run = s_->benchmark_run) {
    run->scene_load_entry = benchmark::monotonic_seconds();
    s_->render->benchmark_load();
  }
}

void Replay3dView::start() {
  State& s = *s_;
  s.started = true;
  if (s.benchmark_run) s.clock.t = float(s.benchmark_run->log_start_time);
  s.frame = s.log->frame_at(s.clock.t);
  for (const auto& info : s.log->mechs()) {
    const MechPose* pose = pose_of(s.frame, info.id);
    if (!pose) continue;
    std::string error;
    auto puppet = Puppet::create(info.chassis, info.side, *pose, &error);
    if (!puppet) {
      std::fprintf(stderr, "mw3: replay3d: mech %d (%s): %s\n", info.id, info.chassis.c_str(), error.c_str());
      if (s.benchmark_run) s.benchmark_run->invalidate({}, "replay puppet creation failed");
      continue;
    }
    s.puppets[info.id] = std::move(puppet);
  }
  // The camera starts behind the first mech (a map-wide view from above is
  // lost in the maps' fog); any fly key or a look lets it go.
  if (!s.benchmark_run && !s.frame.mechs.empty()) s.follow_id = s.frame.mechs[0].id;
  s.last_ns = SDL_GetTicksNS();
  std::printf("mw3: replay3d: %zu puppets, %.1f s of match\n", s.puppets.size(), s.clock.duration);
}

bool Replay3dView::before_lists(bool quit_box_open) {
  State& s = *s_;
  if (auto* run = s.benchmark_run) {
    if (s.startup_frame && !run->failed()) {
      // Present the initial pose and camera once outside the scoring epoch.
      s.startup_frame = false;
      s.real_dt = ztimer::state().dt;
      return true;
    }
    if (!run->armed() && !run->failed()) {
      if (s.render->benchmark_ready()) {
        run->arm();
        s.event_cursor = float(run->log_start_time);
        // At an explicit cut, fire only events on the boundary. Older
        // impacts are over, while frame_at still restores in-flight shots.
        const float previous = run->scene.start_seconds
            ? std::nextafter(s.event_cursor, -std::numeric_limits<float>::infinity())
            : -std::numeric_limits<float>::infinity();
        for (const Event& event : s.log->fire_between(previous, s.event_cursor))
          s.start_effects(event);
      } else {
        run->invalidate({}, "benchmark presenter was not ready after startup");
      }
    }
    if (run->failed()) {
      s.request_quit();
      return false;
    }
    const double elapsed = run->elapsed();
    if (elapsed >= run->scene.end()) {
      run->finish_window();
      s.request_quit();
      return false;
    }
    s.real_dt = ztimer::state().dt;
    ztimer::state().dt = std::min(float(elapsed - s.playback_elapsed), kMaxListStep);
    s.playback_elapsed = elapsed;
    const double replay_time = run->replay_time(elapsed);
    s.clock.t = float(replay_time);
    s.render->set_benchmark_time(replay_time);
    return true;
  }
  s.quit_box_open = quit_box_open;
  for (const auto& apply : s.next_frame) apply();
  s.next_frame.clear();
  // Every seek (keys, the bar, the script) lands before this frame's step:
  // a clock away from the shown time is one, however long the frame was.
  s.seek_pending = s.posed_t >= 0 && s.clock.t != s.posed_t;
  if (quit_box_open) s.release_input();
  s.real_elapsed = frame_elapsed(&s.last_ns, s.scripted);
  // The replay pauses under the quit box; the lists then run on a 0 step.
  const float moved = quit_box_open ? 0.0f : s.clock.step(s.real_elapsed, s.seeking);
  s.real_dt = ztimer::state().dt;
  ztimer::state().dt = std::clamp(moved, 0.0f, kMaxListStep);
  return true;
}

void Replay3dView::after_lists() {
  State& s = *s_;
  if (!s.benchmark_run) ztimer::state().dt = s.real_dt;
  if (s.scripted && s.started && !s.script.run(s.actions)) {
    std::fprintf(stderr, "mw3: replay3d: the script failed\n");
    if (s.request_quit) s.request_quit();
  }
  mech3::mech_set_game_time(s.clock.t);
  if (!s.started) return;
  s.pose();
  if (s.benchmark_run && s.benchmark_run->armed()) {
    for (auto anim = s.impact_animations.begin(); anim != s.impact_animations.end();) {
      if (!zeff::anim_is_playing(*anim)) anim = s.impact_animations.erase(anim);
      else ++anim;
    }
    s.render->set_benchmark_effects(static_cast<unsigned>(s.live_beams.size()),
                                     static_cast<unsigned>(s.impact_animations.size()));
  }
  if (!s.benchmark_run && !s.quit_box_open) s.fly(s.real_elapsed);
}

void Replay3dView::after_frame() {
  if (s_->benchmark_run) ztimer::state().dt = s_->real_dt;
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
    // Parts come back, and a death is undone, only by making the mech again.
    if (seeked && puppet->needs_rebuild(*p, lost)) {
      std::string error;
      if (!puppet->rebuild(*p, &error)) std::fprintf(stderr, "mw3: replay3d: mech %d: %s\n", id, error.c_str());
    }
    const bool live = !first && !seeked;
    // A thigh's loss shows in the state line after the death: looked for a
    // little ahead, so a leg kill gets the limb's explosion alone.
    bool leg_kill = false;
    if (live && !p->standing)
      for (const int part : log->parts_lost_by(id, t + kLegKillLookahead))
        if ((part == 4 || part == 5) && std::find(lost.begin(), lost.end(), part) == lost.end()) leg_kill = true;
    puppet->set(*p, lost, live ? t - posed_t : 1.0f / 60, live, leg_kill);
  }
  if (benchmark_run) {
    if (benchmark_run->armed()) {
      for (const Event& e : log->fire_between(event_cursor, t)) start_effects(e);
      event_cursor = t;
    }
  } else if (!first && !seeked && t > posed_t) {
    for (const Event& e : log->fire_between(posed_t, t)) start_effects(e);
  }
  sync_shots(first || seeked ? 0.0f : std::max(0.0f, t - posed_t));
  posed_t = t;
}

// The frame's weapon shots in flight made, placed or freed; a seek lands the
// same way, since each frame names every beam and round in flight.
void Replay3dView::State::sync_shots(float dt) {
  sync_beams(dt);
  sync_rounds();
}

// Beams have no id in the log: one is known by its shooter, its weapon and
// which of that pair it is this frame (a mech can fire two of one laser).
void Replay3dView::State::sync_beams(float dt) {
  zwep::RunHooks& rh = zwep::run_hooks();
  for (auto& [key, b] : live_beams) b.seen = false;
  std::map<std::string, int> nth;
  for (const auto& logged : frame.beams) {
    std::string key = std::to_string(logged.by) + "/" + logged.weapon;
    key += "/" + std::to_string(nth[key]++);
    auto it = live_beams.find(key);
    if (it == live_beams.end()) {
      zwep::WeaponDef* def = zwep::find_def(logged.weapon.c_str());
      if (!def) continue;
      LiveBeam made;
      made.beam = zwep::beam_make(def, nullptr, nullptr, &kStillOrigin, &kStillDir, 1);
      if (def->flags & zwep::kDesignate) {
        const zwep::Vec3f3 color{def->target_heat[3], def->target_heat[4], def->target_heat[5]};
        made.light = zwep::light_take(&color);
        if (made.light && rh.light_range)
          rh.light_range(made.light, def->target_heat[0], def->target_heat[1]);
      }
      it = live_beams.emplace(key, made).first;
    }
    LiveBeam& b = it->second;
    b.seen = true;
    b.age += dt;
    zwep::BeamSegment& seg = b.beam->segments[0];
    const zwep::Vec3f3 from = f3(logged.from), to = f3(logged.to);
    zwep::Vec3f3 dir{to.x - from.x, to.y - from.y, to.z - from.z};
    const float length = std::sqrt(dir.x * dir.x + dir.y * dir.y + dir.z * dir.z);
    if (length <= 0.0f) continue;
    dir = {dir.x / length, dir.y / length, dir.z / length};
    seg.start = from, seg.dir = dir, seg.length = length;
    zwep::beam_draw(&seg);
    if (b.light) {
      if (rh.light_position) rh.light_position(b.light, to.x, to.y, to.z);
      if (rh.set_active) rh.set_active(b.light, 1);
    }
    // beam_update's pulse: the beam's opacity swings between PULSE's two
    // values at its rate (the hook is named set_uniform_scale, but the game
    // wires it to object3d_set_opacity, app_weapons.cpp).
    const zwep::WeaponDef* def = b.beam->def;
    const float wave = std::sin(b.age * def->pulse_rate * 2.0f * kReplayPi);
    const float pulse = (def->pulse[1] - def->pulse[0]) * ((wave + 1.0f) * 0.5f) + def->pulse[0];
    if (rh.set_uniform_scale) rh.set_uniform_scale(seg.node, pulse);
  }
  for (auto it = live_beams.begin(); it != live_beams.end();) {
    if (it->second.seen) {
      ++it;
      continue;
    }
    if (it->second.light) zwep::light_return(it->second.light);
    zwep::beam_free(it->second.beam);
    it = live_beams.erase(it);
  }
}

// A round's node as zwep_shot.cpp's pool_take and spawn make one: the weapon's
// FLYOUT model under it (a pooled copy when the model is animated), in the
// world, with the FLYOUT animation following it.
bool Replay3dView::State::make_round(zwep::WeaponDef* def, LiveRound* made) {
  zwep::RunHooks& rh = zwep::run_hooks();
  if (!def || !rh.object3d_create) return false;
  made->def = def;
  made->node = rh.object3d_create();
  const zwep::Effect& flyout = def->flyout;
  if (flyout.model) {
    made->pooled_model = flyout.model_animation != nullptr;
    made->model = made->pooled_model ? zwep::model_take(def) : flyout.model;
    if (made->model && rh.obj_add_child) rh.obj_add_child(made->node, made->model);
  }
  if (rh.add_child) rh.add_child(zwep::state().world, made->node);
  if (flyout.animation && rh.anim_follow) made->flyout_anim = rh.anim_follow(flyout.animation, made->node);
  if (flyout.animation_attached && rh.anim_attached)
    made->attached_anim = rh.anim_attached(flyout.animation_attached, made->node, nullptr);
  if (made->pooled_model && rh.anim_model) made->model_anim = rh.anim_model(flyout.model_animation, made->model);
  return true;
}

// Rounds have the log's id; each is moved to its logged spot.
void Replay3dView::State::sync_rounds() {
  zwep::RunHooks& rh = zwep::run_hooks();
  for (auto& [id, r] : live_rounds) r.seen = false;
  for (const auto& logged : frame.rounds) {
    auto it = live_rounds.find(logged.id);
    if (it == live_rounds.end()) {
      LiveRound made;
      if (!make_round(zwep::find_def(logged.weapon.c_str()), &made)) continue;
      it = live_rounds.emplace(logged.id, made).first;
    }
    LiveRound& r = it->second;
    r.seen = true;
    const zwep::WeaponDef& def = *r.def;
    // spawn and commit_one turn the node only for an unlit model, an
    // animation with no model, or a falling shot; the rest keep the model's own.
    const bool turns = ((def.flags & zwep::kFlyoutUnlit) && def.flyout.model) ||
                       (def.flyout.animation && !def.flyout.model) ||
                       (def.gravity != 0.0f && !(def.flags & zwep::kFixedRotate));
    if (turns && r.has_last && rh.set_rotation) {
      zwep::Vec3f3 d{logged.pos.x - r.last.x, logged.pos.y - r.last.y, logged.pos.z - r.last.z};
      const float n = std::sqrt(d.x * d.x + d.y * d.y + d.z * d.z);
      if (n > 0.0f) {
        float rot[3];
        rotation_of({d.x / n, d.y / n, d.z / n}, rot);
        rh.set_rotation(r.node, rot[0], rot[1], rot[2]);
      }
    }
    if (rh.set_translation) rh.set_translation(r.node, logged.pos.x, logged.pos.y, logged.pos.z);
    r.last = logged.pos, r.has_last = true;
  }
  for (auto it = live_rounds.begin(); it != live_rounds.end();) {
    if (it->second.seen) {
      ++it;
      continue;
    }
    free_round(it->second);
    it = live_rounds.erase(it);
  }
}

// As zwep_shot.cpp's retire and pool_release: the animations stopped, the node
// out of the world, its model taken off (a pooled copy back to the pool), and
// the node destroyed.
void Replay3dView::State::free_round(LiveRound& r) {
  zwep::RunHooks& rh = zwep::run_hooks();
  if (r.flyout_anim && rh.anim_stop) rh.anim_stop(r.flyout_anim);
  if (r.attached_anim && rh.anim_stop) rh.anim_stop(r.attached_anim);
  if (rh.remove_child) rh.remove_child(zwep::state().world, r.node);
  if (r.model) {
    if (r.pooled_model) {
      zwep::Projectile p;
      p.node = r.node, p.model = r.model, p.model_anim = r.model_anim;
      zwep::model_return(r.def, &p);
    } else if (rh.obj_remove_child) {
      rh.obj_remove_child(r.node, r.model);
    }
  }
  if (rh.node_destroy) rh.node_destroy(r.node);
}

// Whether an impact is a missile's: every missile weapon's soil impact is
// impact_missle_mech or impact_lrm_min (weapons.zrd), animations that only
// tint the screen within 20 m of the player (docs/anim-run.md) and draw
// nothing in the world.
static bool is_missile_impact(const zwep::Effect& effect) {
  const auto* animation = static_cast<const zeff::AnimDef*>(effect.animation);
  if (!animation) return false;
  const std::string_view name = animation->name();
  return name.rfind("impact_missle", 0) == 0 || name.rfind("impact_lrm", 0) == 0;
}

// Ours (replay only, not the original): a missile impact also plays the
// game's own small fireball, fire_explode_tiny, so a replay watched from a
// chase camera shows where the missiles land.
void Replay3dView::State::start_missile_explosion(const zwep::Vec3f3& at) {
  // Looked up each time: a map load replaces the animation table.
  zeff::AnimDef* const fireball = zeff::anim_find("fire_explode_tiny");
  if (!fireball) return;
  static const float kZero[3] = {};
  const float pos[3] = {at.x, at.y, at.z};
  zeff::AnimDef* playing = zeff::anim_start_at(fireball, nullptr, pos, kZero, kZero);
  if (playing && benchmark_run) impact_animations.insert(playing);
}

// A logged shot's fire effect and sound at its muzzle, or a hit's impact
// effect where it struck (the default soil), from the weapon's own def.
void Replay3dView::State::start_effects(const Event& e) {
  zwep::WeaponDef* def = zwep::find_def(e.weapon.c_str());
  if (!def) return;
  const zwep::Effect* effect = nullptr;
  float rot[3] = {};
  static const float kZero[3] = {};
  const bool impact = (e.type == "hit" || (e.type == "round_end" && e.terrain)) && e.has_at;
  Vec3 position;
  if (e.type == "shot") {
    effect = &def->fire;
    position = e.muzzle;
    rotation_of(f3(e.dir), rot);
  } else if (impact && def->impacts) {
    effect = &def->impacts[zwep::kSoilDefault];
    position = e.at;
  }
  // A hit on a mech plays the weapon's damage animation instead of the soil
  // impact, as apply_damage (zweapon.cpp, 0x00583480) chooses one or the
  // other. The log has no health after the hit, so the game's starting value
  // (1.0) picks the first entry at or above it; none matching plays nothing.
  // A missile's impact draws nothing in the world (is_missile_impact), so the
  // replay adds a fireball, counted as the impact's explosion in its place.
  const bool missile = impact && def->impacts && is_missile_impact(def->impacts[zwep::kSoilDefault]);
  if (missile) start_missile_explosion(f3(e.at));
  if (e.type == "hit" && e.has_at && def->damage_anim_count > 0) {
    constexpr int32_t kDamageAnimSlots = 4;  // WeaponDef::damage_anims
    const int32_t count = std::min<int32_t>(def->damage_anim_count, kDamageAnimSlots);
    for (int32_t i = 0; i < count; ++i) {
      const bool reached = !(1.0f > def->damage_anims[i].health);
      if (!reached) continue;
      if (zwep::Handle damage_anim = def->damage_anims[i].anim) {
        const float at[3] = {e.at.x, e.at.y, e.at.z};
        zeff::AnimDef* damage = zeff::anim_start_at(static_cast<zeff::AnimDef*>(damage_anim),
                                                    nullptr, at, kZero, kZero);
        if (damage && benchmark_run && !missile) impact_animations.insert(damage);
      }
      return;
    }
  }
  if (!effect) return;
  const float pos[3] = {position.x, position.y, position.z};
  zeff::AnimDef* playing = nullptr;
  if (effect->animation && (impact || !effect->effect))
    playing = zeff::anim_start_at(static_cast<zeff::AnimDef*>(effect->animation), nullptr,
                                  pos, rot, kZero);
  if (impact && effect->surface_animation) {
    // The recording has the contact position but no surface normal.
    const zwep::Vec3f3 up{0, 1, 0};
    if (zwep::hit_hooks().surface_angles) zwep::hit_hooks().surface_angles(&up, rot);
    auto* surface = zeff::anim_start_at(static_cast<zeff::AnimDef*>(effect->surface_animation),
                                       nullptr, pos, rot, kZero);
    if (!playing) playing = surface;
  }
  if (effect->effect && zwep::hit_hooks().impact_effect) {
    const auto point = f3(position);
    zwep::hit_hooks().impact_effect(effect->effect, &point);
  }
  if (impact && playing && benchmark_run && !missile) impact_animations.insert(playing);
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
  if (s.benchmark_run && s.benchmark_run->scene.shots.empty()) {
    const auto key = benchmark::sample_camera(s.benchmark_run->scene.track, s.playback_elapsed);
    for (int axis = 0; axis < 3; ++axis) s.eye[axis] = float(key.position[axis]);
    s.yaw = float(key.yaw);
    s.pitch = float(key.pitch);
  } else {
    const benchmark::CameraShot default_follow{benchmark::ShotType::chase, s.follow_id,
                                               0, 0, kFollowBack, kFollowUp + kFollowAim, 0};
    const auto& shot = s.benchmark_run
        ? benchmark::shot_at(s.benchmark_run->scene.shots, s.playback_elapsed)
        : default_follow;
    if (const MechPose* subject = pose_of(s.frame, shot.mech)) {
      const auto& pos = subject->pos;
      const auto camera_pose = benchmark::sample_shot(shot, {pos.x, pos.y, pos.z},
                                                       subject->heading, s.playback_elapsed);
      for (int axis = 0; axis < 3; ++axis) s.eye[axis] = float(camera_pose.position[axis]);
      s.yaw = float(camera_pose.yaw);
      s.pitch = float(camera_pose.pitch);
    }
  }
  // As a debug launch places the mission's camera (app_mission.cpp).
  zcls::camera_set_rotation(camera, -s.pitch, s.yaw + kReplayPi, 0.0f);
  zcls::camera_set_position(camera, s.eye[0], s.eye[1], s.eye[2]);
}

void Replay3dView::draw_overlay() {
  if (s_->benchmark_run) return;
  State& s = *s_;
  if (!s.started) return;
  s.draw.begin_frame(zvid::render3d());
  const float* rect = zmod::draw_state().point_rect;
  if (rect[2] > rect[0]) s.screen_w = rect[2] + 1, s.screen_h = rect[3] + 1;
  s.draw.set_scale_for_height(s.screen_h);

  // Side rings and id labels, then the shared overlays, panel and bar.
  LabelPlacer labels;
  for (size_t index = 0; index < s.frame.mechs.size(); ++index) {
    const MechPose& m = s.frame.mechs[index];
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
    // The label's size follows how big the mech looks: the screen height of
    // the 13 m from its feet to the label, against kLabelNearPixels for
    // full size, held between kLabelMinSize and 1, so far labels shrink and
    // each reads as its own mech's.
    SDL_FPoint label, feet;
    if (s.projector.to_screen({m.pos.x, m.pos.y + kLabelMeters, m.pos.z}, &label)) {
      float size = 1.0f;
      if (s.projector.to_screen(m.pos, &feet))
        size = std::clamp((feet.y - label.y) / (kLabelNearPixels * s.draw.scale()), kLabelMinSize, 1.0f);
      labels.draw(s.draw, label.x - 4, label.y - 8, std::to_string(m.id),
                  s.overlays.on[kReasons] ? doing_word(m) : "", size);
    }
  }
  draw_overlays(s.frame, s.overlays, s.selected, s.draw, s.projector);
  if (!s.quit_box_open) draw_legend(s.overlays, s.draw);  // the box's notice takes the corner
  draw_panel(*s.log, s.frame, s.selected, s.screen_w, s.draw);
  draw_bar(s.clock, s.overlays, s.screen_w, s.screen_h, s.draw);
  if (s.quit_box_open) s.draw.text("paused: the quit box is open", 8, 8);
  if (!s.pending_screenshot.empty() && s.render) {
    // The renderer keeps the path's pointer until the frame is shown.
    s.screenshot_in_flight = s.pending_screenshot;
    s.render->capture_next(s.screenshot_in_flight.c_str());
    std::printf("mw3: replay3d: shot %s at %.2f s\n", s.screenshot_in_flight.c_str(), s.clock.t);
    s.pending_screenshot.clear();
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
  if (auto* run = s_->benchmark_run) {
    const auto invalidate = [&](const char* reason) {
      if (run->armed()) run->invalidate(run->next_frame(run->replay_time(s_->playback_elapsed)), reason);
    };
    switch (e.type) {
      case SDL_EVENT_WINDOW_FOCUS_LOST:
        invalidate("benchmark window lost focus");
        return false;
      case SDL_EVENT_WINDOW_MINIMIZED:
        invalidate("benchmark window minimized");
        return false;
      case SDL_EVENT_WINDOW_RESIZED:
      case SDL_EVENT_WINDOW_PIXEL_SIZE_CHANGED:
        if (e.window.data1 != run->width || e.window.data2 != run->height)
          invalidate("benchmark window or drawable resized");
        return false;
      default:
        // The pump still owns window and quit events.
        return e.type >= SDL_EVENT_KEY_DOWN && e.type < SDL_EVENT_FINGER_DOWN;
    }
  }
  State& s = *s_;
  if (!s.started) return false;
  if (e.type == SDL_EVENT_WINDOW_FOCUS_LOST) {
    s.release_input();
    return false;  // the game's own handling of it goes on
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
        case SDLK_H:
          s.overlays.legend = !s.overlays.legend;
          return true;
        case SDLK_F12: {
          char name[64];
          std::snprintf(name, sizeof name, "replay3d-%07.2f.bmp", s.clock.t);
          s.pending_screenshot = (std::filesystem::path(s.screenshot_dir) / name).string();
          return true;
        }
        // Escape and every other key go to the game: Escape opens its quit
        // box, and a replay's mechs are puppets, so no game command acts.
        default: return false;
      }
    case SDL_EVENT_KEY_UP:
      if (!is_fly_key(e.key.scancode)) return false;
      s.held[e.key.scancode] = false;
      return true;
    case SDL_EVENT_MOUSE_BUTTON_DOWN:
      if (e.button.button == SDL_BUTTON_RIGHT) {
        s.looking = true;  // the motion's own deltas turn the camera; the pointer stays shown
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
