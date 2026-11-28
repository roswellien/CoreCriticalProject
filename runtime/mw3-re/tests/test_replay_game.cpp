// #289: the replay puppet against a live arena mech. Called
// from the arena harness in test_arena_game.cpp (replay_game.h says why).
#include <algorithm>
#include <chrono>
#include <cmath>
#include <cstdio>
#include <string>
#include <vector>

#include "gamez/zclass/class.h"
#include "gamez/zutil/ztimer.h"
#include "mech3/replay_hooks.h"
#include "mech3/app_mech.h"
#include "mech3/arena.h"
#include "mech3/arena_log.h"
#include "mech3/mech.h"
#include "mech3/mech_anim.h"
#include "mech3/mech_parts.h"
#include "mech3/replay_puppet.h"
#include "replay_game.h"

namespace replay_game {

namespace {

constexpr float kStep = 1.0f / 60.0f;
constexpr int kDead = 10;
constexpr int kFirstActionState = 10;  // 0..9 the gaits; 10 on are dead, falling and fallen
constexpr int kCollapseLeft = 7;  // action_objects[7], collapsel

// A node's world position less the mech's center, so a puppet and the live
// mech it copies compare wherever each stands.
bool node_offset(mech3::Mech& m, mech3::Handle node, float out[3]) {
  float at[3], center[3];
  if (!node || !mech3::program_vehicle_centre(&m, center)) return false;
  zcls::node_world_position(static_cast<zcls::Node*>(node), at);
  for (int i = 0; i < 3; ++i) out[i] = at[i] - center[i];
  return true;
}

// die() always calls the weapons_stop hook; wrapped while the collapse
// plays, it counts deaths of the watched mech.
const mech3::Mech* g_watched = nullptr;
int g_deaths = 0;
void (*g_kept_weapons_stop)(mech3::Mech&) = nullptr;
void count_death(mech3::Mech& m) {
  if (&m == g_watched) ++g_deaths;
  if (g_kept_weapons_stop) g_kept_weapons_stop(m);
}

float distance3(const float a[3], const float b[3]) {
  const float dx = a[0] - b[0], dy = a[1] - b[1], dz = a[2] - b[2];
  return std::sqrt(dx * dx + dy * dy + dz * dz);
}

}  // namespace

struct PuppetProbe::State {
  std::unique_ptr<mech3::replay::Puppet> puppet, other;
  PuppetResults r;
};

PuppetProbe::PuppetProbe() : s_(new State()) {}
PuppetProbe::~PuppetProbe() = default;
const PuppetResults& PuppetProbe::results() const { return s_->r; }

void PuppetProbe::frame(int frame, int last_frame) {
  PuppetResults& r = s_->r;
  if (frame >= last_frame) {  // freed before the mission ends
    s_->puppet.reset();
    s_->other.reset();
    return;
  }
  const auto& mechs = mech3::arena::arena_mechs();
  if (mechs.empty()) return;
  const mech3::arena::ArenaMech& live = mechs[0];
  mech3::replay::MechPose pose;
  if (!mech3::replay::parse_pose(mech3::arena::mech_state_record(live, mechs).dump(), &pose)) return;
  std::string error;
  auto& puppet = s_->puppet;
  if (!puppet) {
    // Side -1 puts it on team 0, no one's ally or enemy, so no bot shoots it.
    const auto t0 = std::chrono::steady_clock::now();
    puppet = mech3::replay::Puppet::create("madcat", -1, pose, &error);
    r.create_ms = std::chrono::duration<double, std::milli>(std::chrono::steady_clock::now() - t0).count();
    r.made = puppet != nullptr;
    if (!r.made) std::printf("  puppet: %s\n", error.c_str());
    return;
  }

  // (a) and (b): the puppet follows the live record every frame, as a replay
  // sets it every frame (the feet's ground contact carries from frame to
  // frame); every 50th frame while the live mech is on its feet, its feet,
  // hip, torso and arm are where the live mech has them.
  if (frame < last_frame - 100) puppet->set(pose, {}, kStep);
  if (frame % 50 == 0 && r.samples < 20 && live.mech->anim_state < kFirstActionState) {
    mech3::Mech& p = *puppet->mech();
    mech3::Mech& l = *live.mech;
    const mech3::Handle nodes[2][3] = {{l.legs[0]->foot->node, l.legs[1]->foot->node, l.hip->node},
                                       {p.legs[0]->foot->node, p.legs[1]->foot->node, p.hip->node}};
    float worst_here = 0.0f;
    bool found = true;
    for (int i = 0; i < 3; ++i) {
      float a[3], b[3];
      if (!node_offset(l, nodes[0][i], a) || !node_offset(p, nodes[1][i], b)) found = false;
      else worst_here = std::max(worst_here, distance3(a, b));
    }
    ++r.samples;
    r.worst = std::max(r.worst, worst_here);
    if (found && worst_here < 0.05f) ++r.close_feet;
    const bool angles_match = std::abs(p.torso->yaw - l.torso->yaw) < 0.01f &&
                              std::abs(p.torso->pitch - l.torso->pitch) < 0.01f &&
                              std::abs(p.arms[0]->aim_yaw - l.arms[0]->aim_yaw) < 0.01f;
    if (angles_match) ++r.close_angles;
  }

  // (c): the left arm lost, then a rebuild set to the same time keeps it off.
  if (frame == last_frame - 100) {
    const auto hidden = [&] {
      const mech3::MechPart* arm = mech3::part_by_id(*puppet->mech(), 2);
      const bool node_active = arm && (static_cast<zcls::Node*>(arm->node)->flags() & 4);  // node_set_active's bit
      return arm && arm->destroyed && !node_active;
    };
    puppet->set(pose, {2}, kStep);
    r.part_off = hidden();
    if (puppet->rebuild(pose, &error)) {
      puppet->set(pose, {2}, kStep);
      r.kept_off = hidden() && puppet->detached().size() == 1;
    }
  }

  // (d) and (e): a second puppet jumps and lands with its armor and action
  // queue untouched, then, destroyed with its left thigh gone, plays
  // collapsel to its end and never dies.
  if (frame == last_frame - 50) {
    s_->other = mech3::replay::Puppet::create("madcat", -1, pose, &error);
    if (!s_->other) return;
    mech3::Mech& o = *s_->other->mech();
    const float armor = o.torso->armor;
    const size_t queued = o.actions.size();
    mech3::replay::MechPose jump = pose;
    jump.jumping = true;
    s_->other->set(jump, {}, kStep);
    jump.jumping = false;
    s_->other->set(jump, {}, kStep);
    r.armor_kept = o.torso->armor == armor && o.actions.size() == queued;
    mech3::replay::MechPose dead = pose;
    dead.standing = false;
    dead.action = "collapsel";
    g_watched = &o, g_deaths = 0;
    g_kept_weapons_stop = mech3::damage_calls().weapons_stop;
    mech3::damage_calls().weapons_stop = count_death;
    for (int i = 0; i < 120; ++i) {
      dead.action_elapsed = i * kStep;
      s_->other->set(dead, {4}, kStep);
    }
    mech3::damage_calls().weapons_stop = g_kept_weapons_stop;
    r.never_died = g_deaths == 0;
    const mech3::MechAction* collapse = o.action_objects[kCollapseLeft];
    r.collapsed = collapse && collapse->t > 0.0f && o.anim_state == kDead;
    // Freed now: the game's own loop still updates puppets in this test (the
    // replay keeps it off them), and it would take a collapsed one as a wreck.
    s_->other.reset();
  }
}

namespace {

// A replay's hooks for the test: the action lists run on a fixed step of
// its own clock, and the game time follows that clock.
class TestHooks : public mech3::ReplayHooks {
 public:
  static constexpr float kStep = 0.05f;
  float clock = 0;
  float real_dt = 0;
  int before = 0, after = 0;
  void start() override {}
  bool before_lists(bool) override {
    ++before;
    real_dt = ztimer::state().dt;
    ztimer::state().dt = kStep;
    return true;
  }
  void after_lists() override {
    ++after;
    ztimer::state().dt = real_dt;
    clock += kStep;
    mech3::mech_set_game_time(clock);
  }
  void quit() override {}
};

// What a mech's update would change: where it is and its gait clip's time.
struct MechMark {
  float pos[3] = {};
  float anim_t = 0;
};
MechMark mark(mech3::Mech& m) {
  MechMark k;
  mech3::program_vehicle_centre(&m, k.pos);
  const mech3::MechAnim* anim = m.anim_index >= 0 && m.anim_index < 13 ? m.anims[m.anim_index] : nullptr;
  k.anim_t = anim ? anim->t : 0.0f;
  return k;
}

}  // namespace

struct FrameProbe::State {
  int from = 0, frames = 0;
  bool hooks_on = true;
  TestHooks hooks;
  std::vector<MechMark> marks;
  float real_dt = 0;
  FrameResults r;
};

FrameProbe::FrameProbe(int from, int frames, bool hooks_on) : s_(new State()) {
  s_->from = from;
  s_->frames = frames;
  s_->hooks_on = hooks_on;
}
FrameProbe::~FrameProbe() {
  if (mech3::replay_hooks() == &s_->hooks) mech3::set_replay_hooks(nullptr);
}
const FrameResults& FrameProbe::results() const { return s_->r; }

void FrameProbe::frame(int frame) {
  State& s = *s_;
  const auto& mechs = mech3::arena::arena_mechs();
  const auto take_marks = [&] {
    s.marks.clear();
    for (const auto& entry : mechs) s.marks.push_back(mark(*entry.mech));
  };
  if (frame == s.from) {  // the hooks on, from the next frame
    s.hooks.clock = mech3::world().time;
    if (s.hooks_on) mech3::set_replay_hooks(&s.hooks);
    take_marks();
    return;
  }
  if (frame <= s.from || frame > s.from + s.frames) return;
  ++s.r.frames;
  bool moved = false;
  for (size_t i = 0; i < mechs.size() && i < s.marks.size(); ++i) {
    const MechMark now = mark(*mechs[i].mech);
    for (int c = 0; c < 3; ++c) moved = moved || now.pos[c] != s.marks[i].pos[c];
    moved = moved || now.anim_t != s.marks[i].anim_t;
  }
  if (moved) ++s.r.mechs_moved;
  if (mech3::world().time != s.hooks.clock) ++s.r.time_off_clock;
  if (ztimer::state().dt == TestHooks::kStep) ++s.r.clock_not_real;
  s.r.before = s.hooks.before, s.r.after = s.hooks.after;
  if (frame == s.from + s.frames) mech3::set_replay_hooks(nullptr);
}

}  // namespace replay_game
