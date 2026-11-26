#include "mech3/replay_puppet.h"

#include <algorithm>
#include <cmath>
#include <cstring>

#include "gamez/zclass/cls_node.h"
#include "gamez/zclass/object3d.h"
#include "gamez/zeffect/zeff_anim_run.h"
#include "gamez/zmath/zmth_matrix.h"
#include "mech3/app_mech.h"
#include "mech3/mech.h"
#include "mech3/mech_anim.h"
#include "mech3/mech_lod.h"
#include "mech3/mech_names.h"
#include "mech3/mech_parts.h"
#include "mech3/zai_hunt.h"
#include "mech3/zai_params.h"
#include "mech3/zrdraiv.h"

namespace mech3::replay {

namespace {

// The skis divide by the frame time, so a paused or seeking replay still
// steps by at least this much.
constexpr float kMinStep = 1.0f / 240.0f;

constexpr int kStateStand = 1;        // anim_state: standing or moving on the gait
constexpr int kTorsoFrozen = 2;       // Torso::mode: neither the AI nor the player aims it
constexpr int kWalkSlot = 4;          // anims[4], the walk
constexpr int kLimpBlendSlot = 11;    // anims[11], the walk/limp blend once start_limp made it
constexpr int kAnimSlots = 13;

// An action's kind, 1 fallf .. 8 collapser (mech_data.cpp action_name), 0
// for a name the log should never hold.
int action_kind(const std::string& name) {
  static const char* const kNames[] = {"fallf",  "fallb",  "landf",     "landb",
                                       "getupf", "getupb", "collapsel", "collapser"};
  for (int i = 0; i < 8; ++i)
    if (name == kNames[i]) return i + 1;
  return 0;
}

// The gait clip at `phase` of its loop, running at `cps` loops a second,
// so that after the coming advance(dt) it is exactly there. The rate is set
// outright, not by set_speed, which would multiply by the stride multiplier
// again. A blend's two clips are set the same way, so they stay in step.
void set_phase(MechAnim* anim, float phase, float cps, float dt) {
  if (!anim) return;
  anim->rate = cps * anim->loop_time;
  // Walking backward runs the clip at a negative rate; t then counts down
  // the same way, so rate * t still lands on the phase.
  if (anim->rate != 0.0f) anim->t = phase * anim->loop_time / anim->rate - dt;
  else anim->t = phase * anim->loop_time;  // still: the advance is a no-op on rate * t
  if (auto* blend = dynamic_cast<BlendAnim*>(anim)) {
    set_phase(blend->a, phase, cps, dt);
    set_phase(blend->b, phase, cps, dt);
  }
}

}  // namespace

bool Puppet::detachable(int id) {
  switch (id) {
    case 2: case 3: case 9: case 10:            // arms and hands
    case 4: case 5: case 11: case 12: case 13: case 14:  // thighs, calves and feet
      return true;
    default:
      return false;
  }
}

std::unique_ptr<Puppet> Puppet::create(const std::string& chassis, int side, const MechPose& start,
                                       std::string* error) {
  std::unique_ptr<Puppet> puppet(new Puppet());
  puppet->chassis_ = chassis;
  puppet->side_ = side;
  puppet->roster_ = mech_index(chassis.c_str());
  if (puppet->roster_ < 0) {
    *error = "unknown chassis \"" + chassis + "\"";
    return nullptr;
  }
  if (!puppet->make(start, error)) return nullptr;
  return puppet;
}

Puppet::~Puppet() { free_mech(); }

// The jet flame first: Mech::release stops the mech's sounds but not that
// effect, which would go on updating the freed jet node. The damage effects
// too (stop_effects): Mech::release frees the flown-off limbs before the
// parts stop the effects riding them.
void Puppet::free_mech() {
  if (!mech_) return;
  stop_effects();
  mech_->jet_effects(false);
  mech_free_in_play(mech_);
  mech_ = nullptr;
}

// Every effect a part or the torso still runs (blow_off, explode), stopped
// and forgotten while the nodes it rides are alive.
void Puppet::stop_effects() {
  const FreeCalls& f = free_calls();
  const auto stop = [&](Handle& effect) {
    if (effect && f.stop_effect) f.stop_effect(effect);
    effect = nullptr;
  };
  // The end callback is cleared first: a stopped effect can stay held, and a
  // later stop (the mission's end) would call back into the freed part.
  const auto forget = [&](Handle& effect) {
    if (effect) zeff::anim_set_callback(static_cast<zeff::AnimDef*>(effect), nullptr, nullptr);
    stop(effect);
  };
  for (MechPart* part : mech_->parts) {
    if (!part) continue;
    forget(part->debris_effect);
    forget(part->trail_effect);
  }
  if (mech_->torso) {
    forget(mech_->torso->death_effect);
    forget(mech_->torso->death_effect2);
  }
}

bool Puppet::make(const MechPose& start, std::string* error) {
  // The record the AI mech path reads: where it stands, its team (side A 1,
  // side B 2, as the arena's), and the first configuration. No pilot reads
  // the rest.
  ai::AivRecord record;
  record.put<float>(0x08, start.pos.x);
  record.put<float>(0x0c, start.pos.y);
  record.put<float>(0x10, start.pos.z);
  record.put<float>(0x14, start.heading);
  record.put<int32_t>(0x18, side_ + 1);
  record.put<int32_t>(0xbc, 0);
  // create_ai_mech wants a net; the replay controls never read it.
  ai::HuntNet* net = ai::hunt_net();
  if (!net) {
    const float at[3] = {start.pos.x, start.pos.y, start.pos.z};
    net = ai::make_hunt_net(at);
  }
  name_ = "replay_" + std::to_string(start.id);
  mech_ = static_cast<Mech*>(program_create_replay_mech(roster_, name_.c_str(), net, &record));
  if (!mech_) {
    *error = "the " + chassis_ + " for mech " + std::to_string(start.id) + " could not be made";
    return false;
  }
  mech_->set_team(record.team());
  mech_->detail = kPuppetDetail;
  mech_->x690 = 0;  // the full model
  mech_->arena_bot = true;
  mech_->remote = true;  // no landing damage or knockdown in ground_step
  if (mech_->torso) mech_->torso->set_mode(kTorsoFrozen);
  for (Arm* arm : mech_->arms)
    if (arm) arm->aim_rate = 0.0f;  // the aim stays where set() puts it
  action_.clear();
  detached_.clear();
  limp_started_ = false;
  was_standing_ = start.standing;
  exploded_ = false;
  handled_.clear();
  place(start);
  return true;
}

bool Puppet::rebuild(const MechPose& pose, std::string* error) {
  free_mech();
  return make(pose, error);
}

// The node to the logged place and heading. The heading is a yaw-only
// quaternion, as the log read it (arena_log.cpp: 2 atan2(y, w)).
void Puppet::place(const MechPose& pose) {
  Mech& m = *mech_;
  m.orientation[0] = std::cos(pose.heading * 0.5f);
  m.orientation[1] = 0.0f;
  m.orientation[2] = std::sin(pose.heading * 0.5f);
  m.orientation[3] = 0.0f;
  zmth::quat_matrix(m.orientation, m.transform);
  zcls::object3d_set_translation(static_cast<zcls::Node*>(m.node), pose.pos.x, pose.pos.y, pose.pos.z);
  m.entity_moved();
}

// The part hidden and marked destroyed (the game's own flag: a destroyed arm
// stops aiming). It is not unlinked: the game unlinks a part only to hand its
// node to the flying debris, and a mech freed with an unlinked part keeps a
// dangling reference to it.
void Puppet::detach(int id) {
  MechPart* part = part_by_id(*mech_, id);
  if (!part || !part->node) return;
  zcls::node_set_active(static_cast<zcls::Node*>(part->node), 0);
  part->destroyed = true;
  mark_detached(id);
}

void Puppet::mark_detached(int id) {
  if (std::find(detached_.begin(), detached_.end(), id) == detached_.end()) detached_.push_back(id);
}

bool Puppet::needs_rebuild(const MechPose& pose, const std::vector<int>& lost) const {
  if (exploded_ && pose.standing) return true;
  for (const int id : handled_)
    if (std::find(lost.begin(), lost.end(), id) == lost.end()) return true;
  return false;
}

// A limb lost while the replay plays: the game's own destroy (mech_parts.cpp),
// so it flies off as debris with its explosion and leaves a smoking stump.
// An arm's destroy takes its hand along. A thigh's is MechPart's alone plus
// Leg::destroy's tail without its fall() and die(): the log poses the fall,
// and die() would change the puppet's state for the rest of the replay.
// Damage never applies: puppets are remote, so their take_damage is a no-op.
// The variant (which of the two debris effects) isn't logged; the id picks it.
void Puppet::blow_off(int id) {
  MechPart* part = part_by_id(*mech_, id);
  if (!part || part->destroyed) {  // gone with its arm or thigh already
    mark_detached(id);
    return;
  }
  // The Elemental's parts kill it as they go (on_part_destroyed runs its
  // Torso::destroy and die()), so its parts are only hidden.
  constexpr int32_t kElementalRoster = 7;  // mech_names.cpp: "elemental"
  const bool flies = (id == kLeftArm || id == kRightArm || id == kLeftThigh || id == kRightThigh);
  if (roster_ == kElementalRoster || !flies) {
    detach(id);  // a hand, calf or foot alone: hidden, as the game has no effect for it
    return;
  }
  const int variant = id % 2;
  if (id == kLeftArm || id == kRightArm) {
    part->destroy(variant, 1);
    mark_detached(id + 7);  // its hand (9, 10) went with it
  } else if (auto* leg = dynamic_cast<Leg*>(part)) {
    if (leg->foot && leg->foot->node) zcls::node_set_active(static_cast<zcls::Node*>(leg->foot->node), 0);
    leg->MechPart::destroy(variant, 1);
    if (leg->foot) leg->foot->lose_contents(), leg->foot->detach();
    if (leg->calf) leg->calf->lose_contents(), leg->calf->detach();
    mark_detached(id + 7), mark_detached(id + 9);  // its calf (11, 12) and foot (13, 14)
  }
  mark_detached(id);
}

// A mech destroyed while the replay plays: Torso::destroy's death effect, by
// the fall the log shows (fallf: forward, fallb: backward, else the slow
// collapse), without its fall, die() or contents (the log poses the fall).
void Puppet::explode(const std::string& action) {
  Mech& m = *mech_;
  if (!m.torso || !m.pilot) return;
  const int effect = action == "fallf" ? 2 : action == "fallb" ? 3 : 0;
  const Handle def = m.pilot->death_effects[effect];
  DamageCalls& calls = damage_calls();
  if (calls.node_set_name) calls.node_set_name(m.node, "deadmech");  // as the game names a wreck
  if (!def || !calls.spawn_effect_at) return;
  // A replay played again from the start shows the death again: the last
  // one's effect is stopped first, so only one is ever held.
  if (Handle& last = m.torso->death_effect2; last) {
    zeff::anim_set_callback(static_cast<zeff::AnimDef*>(last), nullptr, nullptr);
    if (free_calls().stop_effect) free_calls().stop_effect(last);
    last = nullptr;
  }
  m.torso->death_effect2 = calls.spawn_effect_at(def, m.node, 0.0f, 0.0f, 0.0f);
  exploded_ = true;
  // Cleared when it ends, as the game's own (so stop_effects never stops a
  // finished one).
  if (m.torso->death_effect2 && calls.on_effect_end) calls.on_effect_end(m.torso->death_effect2, *m.torso);
}

void Puppet::set(const MechPose& pose, const std::vector<int>& lost, float dt, bool live, bool leg_kill) {
  if (!mech_) return;
  Mech& m = *mech_;
  dt = std::max(dt, kMinStep);
  std::vector<int> newly_lost;
  for (const int id : lost) {
    if (!detachable(id) || std::find(handled_.begin(), handled_.end(), id) != handled_.end()) continue;
    handled_.push_back(id);
    if (live) newly_lost.push_back(id);  // flown off once posed, below
    else if (std::find(detached_.begin(), detached_.end(), id) == detached_.end()) detach(id);
  }

  place(pose);
  m.vec_3c = m.push = m.impulse = mech3::Vec3{0, 0, 0};
  std::fill(std::begin(m.blocked), std::end(m.blocked), false);
  if (m.torso) {
    m.torso->yaw = pose.twist;
    m.torso->pitch = pose.pitch;
    m.torso->refresh_turn();
  }
  for (int i = 0; i < 2; ++i) {
    if (!m.arms[i] || !pose.has_arm[i]) continue;
    m.arms[i]->aim_yaw = pose.arm_yaw[i];
    m.arms[i]->aim_pitch = pose.arm_pitch[i];
  }

  // An action plays while it runs, and holds its last frame while the mech
  // lies fallen or dead.
  const int kind = action_kind(pose.action);
  MechAction* act = kind ? m.action_objects[kind] : nullptr;
  const bool down = pose.fallen || !pose.standing;
  const bool in_action = act && (pose.action_elapsed < act->loop_time || down);
  if (in_action) play_action(pose, dt);
  else play_gait(pose, dt);
  m.animate_torso_hip(dt);
  m.animate_limbs(dt);

  // The log wins over root motion.
  place(pose);
  // Posed first, so the debris and effects start where the limb is drawn.
  // An arm's or thigh's blow_off marks its hand, calf and foot, which the log
  // lists too: those are skipped here.
  for (const int id : newly_lost)
    if (std::find(detached_.begin(), detached_.end(), id) == detached_.end()) blow_off(id);
  // The game's death effect is the torso's (Torso::destroy); a mech killed
  // by a lost thigh (Leg::destroy) has only the limb's explosion.
  if (live && was_standing_ && !pose.standing && !leg_kill) explode(pose.action);
  was_standing_ = pose.standing;
  m.jet_effects(pose.jumping);
}

void Puppet::play_action(const MechPose& pose, float dt) {
  Mech& m = *mech_;
  const int kind = action_kind(pose.action);
  MechAction* act = m.action_objects[kind];
  if (action_ != pose.action) {
    m.begin_action(act, kind);
    action_ = pose.action;
  }
  // So that the coming advance lands on the logged time, held at the end.
  const float at = std::clamp(pose.action_elapsed, 0.0f, act->loop_time);
  act->t = std::max(at - dt, 0.0f);
  act->done = false;
  m.animate_action(dt, act, kind);
}

void Puppet::play_gait(const MechPose& pose, float dt) {
  Mech& m = *mech_;
  if (!action_.empty()) {
    // Back on its feet: the fall hid the shadows.
    m.legs[0]->foot->show_shadow(true);
    m.legs[1]->foot->show_shadow(true);
    action_.clear();
  }
  m.anim_state = m.prev_state = kStateStand;
  m.gait_frames = 0;  // no blend-in of the root motion after an action
  int slot = pose.anim >= 0 && pose.anim < kAnimSlots ? pose.anim : kWalkSlot;
  if (pose.limp == 0 || pose.limp == 1) {
    if (!limp_started_) limp_started_ = m.start_limp(pose.limp, false);
    if (m.anims[kLimpBlendSlot]) slot = kLimpBlendSlot;
  }
  MechAnim* anim = m.anims[slot] ? m.anims[slot] : m.anims[kWalkSlot];
  if (!anim) return;
  anim->set_blend(pose.weight);
  set_phase(anim, pose.phase, pose.cps, dt);
  const mech3::Vec3 saved = m.vec_3c;
  m.advance_gait(dt, anim);
  m.animate_gait(dt, anim, pose.jumping ? 1 : 0, saved);
  if (pose.jumping) m.pose_jump();
}

}  // namespace mech3::replay
