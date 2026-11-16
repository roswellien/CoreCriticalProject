#include "frontend/sdl/replay_view.h"

#include <SDL3/SDL.h>

#include <algorithm>
#include <cmath>
#include <cstdio>
#include <filesystem>
#include <string>
#include <vector>

#include "frontend/sdl/replay_ui.h"
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
constexpr float kMinZoom = 0.25f, kMaxZoom = 16.0f;  // pixels per meter
constexpr float kZoomStep = 1.25f;
constexpr float kPickPixels = 10.0f;
constexpr float kStreakMeters = 15.0f;

// The map is seen from above: world x to the right, world z up the screen.
struct Camera : Projector {
  float center_x = 0, center_z = 0;
  float zoom = 1;  // pixels per meter
  float width = 1, height = 1;
  SDL_FPoint to_screen(float x, float z) const {
    return {width / 2 + (x - center_x) * zoom, height / 2 - (z - center_z) * zoom};
  }
  SDL_FPoint to_screen(const Vec3& v) const { return to_screen(v.x, v.z); }
  bool to_screen(const Vec3& v, SDL_FPoint* out) const override {
    *out = to_screen(v);
    return true;
  }
  void to_world(float sx, float sy, float* x, float* z) const {
    *x = center_x + (sx - width / 2) / zoom;
    *z = center_z - (sy - height / 2) / zoom;
  }
};

// The viewer's state between frames.
struct Viewer {
  const ReplayLog* log = nullptr;
  Terrain terrain;
  SDL_Texture* terrain_texture = nullptr;
  Camera camera;
  ReplayClock clock;
  Overlays overlays;
  int selected = -1;  // a mech's index in the log, -1 for none
  bool seeking = false, panning = false;
  float press_x = 0, press_y = 0;
  std::string log_path;

  void seek_to(float sx) { clock.seek_fraction(sx / camera.width); }
};

// The terrain as one texture, its walls and cliffs darkened in. The grids are
// freed once uploaded (drawing needs only the placement): at the cell cap
// they hold about 150 MB. A failure sets terrain->error, which the window shows.
SDL_Texture* make_terrain_texture(SDL_Renderer* renderer, Terrain* terrain) {
  if (terrain->width <= 0 || terrain->height <= 0) return nullptr;
  for (size_t i = 0; i < terrain->outline.size(); ++i)
    if (terrain->outline[i]) terrain->rgba[i * 4] = terrain->rgba[i * 4 + 1] = terrain->rgba[i * 4 + 2] = 24;
  SDL_Texture* tex =
      SDL_CreateTexture(renderer, SDL_PIXELFORMAT_RGBA32, SDL_TEXTUREACCESS_STATIC, terrain->width, terrain->height);
  if (tex) {
    SDL_UpdateTexture(tex, nullptr, terrain->rgba.data(), terrain->width * 4);
    SDL_SetTextureScaleMode(tex, SDL_SCALEMODE_LINEAR);
  } else {
    terrain->error = std::string("cannot make the terrain texture: ") + SDL_GetError();
  }
  for (auto* grid : {&terrain->rgba, &terrain->outline}) grid->clear(), grid->shrink_to_fit();
  terrain->heights.clear(), terrain->heights.shrink_to_fit();
  return tex;
}

void fit_camera(Camera* camera, const float box[4]) {
  if (box[0] > box[2]) return;
  camera->center_x = (box[0] + box[2]) / 2, camera->center_z = (box[1] + box[3]) / 2;
  const float span_x = std::max(box[2] - box[0], 50.0f), span_z = std::max(box[3] - box[1], 50.0f);
  camera->zoom = std::clamp(std::min(camera->width / span_x, bar_top(camera->height) / span_z) * 0.9f,
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

void draw_world(Viewer& v, const Frame& frame, SdlRendererDraw& paint) {
  const Camera& cam = v.camera;
  if (v.terrain_texture) {
    const SDL_FPoint top_left = cam.to_screen(v.terrain.x0, v.terrain.z_top);
    const SDL_FRect dst = {top_left.x, top_left.y, v.terrain.width * v.terrain.cell * cam.zoom,
                           v.terrain.height * v.terrain.cell * cam.zoom};
    SDL_RenderTexture(paint.renderer(), v.terrain_texture, nullptr, &dst);
  }
  const auto side_of = [&](int id) {
    const auto* info = v.log->info_of(id);
    return info ? std::clamp(info->side, 0, 1) : 0;
  };

  // Trails.
  for (const MechPose& m : frame.mechs) {
    const std::vector<Vec3> trail = v.log->trail(m.id, v.clock.t, kTrailSeconds);
    SDL_FColor c = kSideColor[side_of(m.id)];
    c.a = 0.45f;
    for (size_t k = 1; k < trail.size(); ++k) paint.line(cam.to_screen(trail[k - 1]), cam.to_screen(trail[k]), c);
  }
  draw_overlays(frame, v.overlays, v.selected, paint, cam);
  for (const auto& beam : frame.beams)
    paint.line(cam.to_screen(beam.from), cam.to_screen(beam.to), ui_color(120, 255, 255));
  for (const auto& round : frame.rounds) paint.circle(cam.to_screen(round.pos), 1.5f, ui_color(255, 240, 200));
  for (const auto& e : frame.recent) {
    if (e.type == "shot" && !e.beam) {
      const Vec3 end = {e.muzzle.x + e.dir.x * kStreakMeters, 0, e.muzzle.z + e.dir.z * kStreakMeters};
      paint.line(cam.to_screen(e.muzzle), cam.to_screen(end), ui_color(255, 240, 200, 200));
    } else if (e.type == "hit") {
      if (const MechPose* hit = pose_of(frame, e.id))
        paint.circle(cam.to_screen(hit->pos), 9, ui_color(255, 220, 80, 110));
    }
  }
  LabelPlacer labels;
  for (size_t i = 0; i < frame.mechs.size(); ++i) {
    const MechPose& m = frame.mechs[i];
    const SDL_FPoint at = cam.to_screen(m.pos);
    const SDL_FColor side = kSideColor[side_of(m.id)];
    if (!m.standing) {
      paint.cross(at, 7, ui_color(170, 170, 170));
    } else {
      SDL_FColor cone = side;
      cone.a = 0.35f;
      paint.cone(at, m.heading + m.twist, 15.0f * kReplayPi / 180.0f, 36, cone);  // where the guns point
      paint.circle(at, 6, side);
      paint.arrow(at, screen_direction(m.heading), 16, ui_color(255, 255, 255));  // where the legs walk
    }
    if (static_cast<int>(i) == v.selected) paint.outline({at.x - 10, at.y - 10, 20, 20}, ui_color(255, 255, 255));
    labels.draw(paint, at.x + 8, at.y - 18, std::to_string(m.id), v.overlays.on[kReasons] ? doing_word(m) : "");
  }
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
  std::snprintf(name, sizeof name, "replay-%07.2f.bmp", v.clock.t);
  return (std::filesystem::path(v.log_path).parent_path() / name).string();
}

// One input event; false when the viewer should close.
bool handle(Viewer& v, const SDL_Event& e, const Frame& frame) {
  switch (e.type) {
    case SDL_EVENT_QUIT:
      return false;
    case SDL_EVENT_KEY_DOWN:
      switch (e.key.key) {
        case SDLK_ESCAPE: return false;
        case SDLK_SPACE: v.clock.toggle_play(); break;
        case SDLK_LEFT: v.clock.jump(-ReplayClock::kJumpSeconds); break;
        case SDLK_RIGHT: v.clock.jump(ReplayClock::kJumpSeconds); break;
        // "<" and ">": shifted , and . on a US layout, their own key on many others.
        case SDLK_COMMA: case SDLK_LESS: v.clock.slower(); break;
        case SDLK_PERIOD: case SDLK_GREATER: v.clock.faster(); break;
        case SDLK_1: case SDLK_2: case SDLK_3: case SDLK_4: case SDLK_5:
          v.overlays.toggle(static_cast<int>(e.key.key - SDLK_1));
          break;
        case SDLK_H:
          v.overlays.legend = !v.overlays.legend;
          break;
        default: break;
      }
      break;
    case SDL_EVENT_MOUSE_BUTTON_DOWN:
      if (e.button.button != SDL_BUTTON_LEFT) break;
      v.press_x = e.button.x, v.press_y = e.button.y;
      if (e.button.y >= bar_top(v.camera.height)) v.seeking = true, v.seek_to(e.button.x);
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
  ReplayScript script;
  const bool scripted = !script_path.empty();
  bool script_failed = false;
  if (scripted && !script.load(script_path)) {
    std::fprintf(stderr, "mw3: --replay-script: cannot read %s\n", script_path.c_str());
    return 2;
  }
  Viewer v;
  v.log = &log;
  v.log_path = log_path;
  v.clock.duration = log.duration() + ReplayClock::kEndHoldSeconds;
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
  v.terrain_texture = make_terrain_texture(renderer, &v.terrain);
  {
    SdlRendererDraw paint(renderer);
    paint.open_text();
    ScriptActions actions;  // the map has no 3D camera: camera and follow are ignored
    actions.shot = [&](const std::string& path) { save_screenshot(renderer, path); };
    actions.seek = [&](float t) { v.clock.seek(t); };
    int w = 0, h = 0;
    SDL_GetRenderOutputSize(renderer, &w, &h);
    v.camera.width = static_cast<float>(w), v.camera.height = static_cast<float>(h);
    fit_camera(&v.camera, box);
    uint64_t last = SDL_GetTicksNS();
    for (bool open = true; open;) {
      v.clock.step(frame_elapsed(&last, scripted), v.seeking);
      const Frame frame = log.frame_at(v.clock.t);
      SDL_Event e;
      while (SDL_PollEvent(&e)) {
        if (e.type == SDL_EVENT_KEY_DOWN && e.key.key == SDLK_F12) save_screenshot(renderer, shot_path(v));
        else if (!handle(v, e, frame)) open = false;
      }
      SDL_GetRenderOutputSize(renderer, &w, &h);
      v.camera.width = static_cast<float>(w), v.camera.height = static_cast<float>(h);
      paint.set_scale_for_height(v.camera.height);
      paint.rect({0, 0, v.camera.width, v.camera.height}, ui_color(70, 70, 70));  // gray ground when there is no terrain
      draw_world(v, frame, paint);
      float legend_top = 10;
      if (!v.terrain.error.empty()) {
        const float banner_h = 24 * paint.scale();
        paint.rect({0, 0, v.camera.width, banner_h}, ui_color(120, 30, 30, 220));
        paint.text("no terrain: " + v.terrain.error, 8, 4 * paint.scale());
        legend_top += banner_h;
      }
      draw_legend(v.overlays, paint, legend_top);
      draw_panel(log, frame, v.selected, v.camera.width, paint);
      draw_bar(v.clock, v.overlays, v.camera.width, v.camera.height, paint);
      if (scripted && !script.run(actions)) open = false, script_failed = true;
      SDL_RenderPresent(renderer);
    }
  }
  if (v.terrain_texture) SDL_DestroyTexture(v.terrain_texture);
  SDL_DestroyRenderer(renderer);
  SDL_DestroyWindow(window);
  return script_failed ? 2 : 0;  // a test script with a bad command fails its run
}

}  // namespace sdlfe
