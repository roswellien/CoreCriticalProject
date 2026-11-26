#include "mech3/arena_log.h"

#include <algorithm>
#include <cmath>
#include <fstream>
#include <iterator>

#include "gamez/zsound/zsnd.h"
#include "gamez/zweapon/zweapon.h"
#include "gamez/zweapon/zwep_init.h"
#include "mech3/app_mech.h"
#include "mech3/mech.h"
#include "mech3/mech_anim.h"
#include "mech3/mech_control.h"
#include "mech3/mech_data.h"
#include "mech3/mech_move.h"
#include "mech3/mech_parts.h"
#include "mech3/sound_extra.h"
#include "mech3/weapon.h"
#include "mech3/zai_attack.h"
#include "mech3/zai_brain.h"
#include "mech3/zai_hunt.h"

namespace mech3::arena {

namespace {
std::FILE* g_file = nullptr;
int32_t g_frame_ms = 0;
bool g_detail = true;
bool g_record_every_update = false;

// The match being logged: its mechs (the hooks look an object up in them),
// the time of the last state lines, and each mech's standing last frame.
const std::vector<ArenaMech>* g_mechs = nullptr;
float g_now = 0;
float g_next_state = 0;
std::vector<bool> g_was_standing;
std::vector<RouteSeen> g_routes;  // #289: each mech's, by index in the match's list
std::vector<DecisionBook> g_decisions;  // #289: likewise
bool g_hooked = false;
ShotStarts g_shot_starts;
RoundBook g_rounds;
decltype(WeaponCalls::net_event) g_kept_shot = nullptr;
decltype(DamageCalls::controls_hit) g_kept_hit = nullptr;
// #289 version 2's hooks, each passing on to what was installed before.
decltype(MoveCalls::action_started) g_kept_action = nullptr;
decltype(ai::RadioCalls::line) g_kept_radio = nullptr;
decltype(zwep::HitHooks::impact_seen) g_kept_impact = nullptr;
constexpr int kLimpBlendSlot = 11;  // anims[11], the walk/limp blend (mech_move.cpp kLimpBlend)

void write_line(const nlohmann::json& record) {
  if (!g_file) return;
  const std::string line = record.dump();
  std::fwrite(line.data(), 1, line.size(), g_file);
  std::fputc('\n', g_file);
  std::fflush(g_file);
}

// Three decimals: enough for meters, radians and seconds, and a third of the
// size of a float's full digits.
double rounded(float value) { return std::round(static_cast<double>(value) * 1000.0) / 1000.0; }

// The arena id of a mech, a weapon's owner or an attacker; -1 for anything
// else (a turret, a building, nothing).
int id_of(const void* object) {
  if (!g_mechs || !object) return -1;
  for (const ArenaMech& entry : *g_mechs)
    if (entry.mech == object) return entry.id;
  return -1;
}

// The arena id of a vehicle handle (a contact's vehicle, a brain's), -1 for
// anything not an arena mech.
int id_of_vehicle(zgame::Handle vehicle) {
  if (!vehicle || !g_mechs) return -1;
  ai::BrainHooks& hooks = ai::brain_hooks();
  for (const ArenaMech& entry : *g_mechs)
    if (hooks.vehicle_handle(entry.mech) == vehicle) return entry.id;
  return -1;
}

int id_of_contact(const ai::Contact* contact) {
  return contact ? id_of_vehicle(ai::brain_hooks().contact_vehicle(contact)) : -1;
}

// The arena id of what a mech's AI has targeted, -1 for none.
int target_id(const Mech* mech) { return id_of_contact(mech->target); }

int side_of(int id) {
  if (!g_mechs) return -1;
  for (const ArenaMech& entry : *g_mechs)
    if (entry.id == id) return entry.side;
  return -1;
}

// #289: the follower of the order a brain is running: the hunt's, the
// fight's or the follow's NavWay; other orders walk without one.
const ai::nav::Follower* current_follower(const ai::BehaviourState* state) {
  if (auto* hunt = dynamic_cast<const ai::HuntState*>(state)) return &hunt->nav.follow;
  if (auto* fight = dynamic_cast<const ai::FightState*>(state)) return &fight->nav.follow;
  if (auto* follow = dynamic_cast<const ai::FollowState*>(state)) return &follow->nav.follow;
  return nullptr;
}

// The order a mech's brain is running and how many it has stacked; a null
// state and 0 for a mech with no AI brain or no orders. The one place the
// log finds a bot's order, so a new kind of order is added once.
struct CurrentOrder {
  const ai::BehaviourState* state = nullptr;
  size_t count = 0;
};
CurrentOrder current_order(const Mech* mech) {
  auto* controls = dynamic_cast<AiControls*>(mech->controls);
  ai::Brain* brain = controls ? controls->brain.get() : nullptr;
  if (!brain || brain->orders.empty()) return {};
  return {brain->current().state.get(), brain->orders.size()};
}

// #289: the route and contact fields of the ai record.
void add_ai_detail(const Mech* mech, int self_side, nlohmann::json* ai) {
  const ai::nav::Follower* follower = current_follower(current_order(mech).state);
  (*ai)["at"] = follower ? follower->at : -1;
  nlohmann::json contacts = nlohmann::json::array();
  for (const ai::Contact* contact : mech->contacts) {
    const int id = id_of_contact(contact);
    if (id < 0 || side_of(id) == self_side) continue;
    constexpr uint8_t kDetected = 1;  // Contact::flags bit 0: the sensors detect it now (zai_target.h)
    contacts.push_back({{"id", id}, {"seen", (contact->flags & kDetected) != 0}});
  }
  (*ai)["contacts"] = contacts;
}

// #289 version 2: the anim record's phase (0..1 through the loop), cps
// (loops a second), blend weight and limping leg. A limp plays the walk/limp
// blend while anim_index stays at the step/walk slot, so those come from the
// blend; "index" and "t" stay the slot's, as version 1 wrote them.
void add_anim_detail(const Mech* m, const MechAnim* slot_anim, nlohmann::json* anim) {
  const MechAnim* playing = m->limp_playing >= 0 ? m->anims[kLimpBlendSlot] : slot_anim;
  float phase = 0.0f, cps = 0.0f, weight = 0.0f;
  if (playing && playing->loop_time > 0.0f) {
    // set_speed keeps rate * t fixed, so rate * t is the time into the loop.
    const float loops = playing->rate * playing->t / playing->loop_time;
    phase = loops - std::floor(loops);
    cps = playing->rate / playing->loop_time;
  }
  if (const auto* blend = dynamic_cast<const BlendAnim*>(playing)) weight = blend->weight;
  (*anim)["phase"] = rounded(phase);
  (*anim)["cps"] = rounded(cps);
  (*anim)["weight"] = rounded(weight);
  (*anim)["limp"] = m->limp_playing;
}

const char* hunt_rule_name(const ai::HuntState& hunt) {
  switch (hunt.goal.rule) {  // a switch, so a new rule can't be logged under another's name
    case ai::HuntRule::kContact: return "contact";
    case ai::HuntRule::kLastSeen: return "last_seen";
    case ai::HuntRule::kFallback: return "fallback";
  }
  return "unknown";
}

// Which of the game's own combat states (zai_attack.h) a mech is in, for the
// log's "move": the attack closes in (FightState), then takes the move its
// pilot's mode picks; the manoeuvre and the attack's three closing orders
// come around it. Null for a state that is not one of them.
const char* stock_move_name(const ai::BehaviourState* state) {
  if (dynamic_cast<const ai::FightState*>(state)) return "close";
  if (dynamic_cast<const ai::CircleState*>(state)) return "circle";
  if (dynamic_cast<const ai::OrbitState*>(state)) return "orbit";
  if (dynamic_cast<const ai::VeerState*>(state)) return "veer";
  if (dynamic_cast<const ai::StationState*>(state)) return "station";
  if (dynamic_cast<const ai::FollowState*>(state)) return "follow";
  if (dynamic_cast<const ai::ManoeuvreState*>(state)) return "hop";  // brake, face a target, hop on the jets
  if (dynamic_cast<const ai::AttackReturnState*>(state)) return "return";
  if (dynamic_cast<const ai::AttackRearmState*>(state) || dynamic_cast<const ai::AttackEndState*>(state) ||
      dynamic_cast<const ai::AfterManoeuvreState*>(state))
    return "end";
  return nullptr;
}

// The order a mech's brain is running: its own hunt, the stock fight (with
// the combat state it is in), or another of the game's.
nlohmann::json ai_record(const Mech* mech) {
  nlohmann::json ai = nlohmann::json::object();
  const ai::BehaviourState* state = current_order(mech).state;
  if (!state) return ai;
  if (auto* hunt = dynamic_cast<const ai::HuntState*>(state)) {
    ai["order"] = "hunt";
    ai["goal_rule"] = hunt_rule_name(*hunt);
    ai["goal"] = {rounded(hunt->goal.at[0]), rounded(hunt->goal.at[1]), rounded(hunt->goal.at[2])};
  } else if (const char* move = stock_move_name(state)) {
    ai["order"] = "fight";
    ai["move"] = move;
  } else {
    ai["order"] = "other";
  }
  return ai;
}

nlohmann::json rounded3(float x, float y, float z) { return {rounded(x), rounded(y), rounded(z)}; }

// A weapon def's name as the log writes it: its NAME, else its key.
std::string weapon_name(const zwep::WeaponDef* def) {
  if (!def) return "";
  if (def->name) return def->name;
  return def->key ? def->key : "";
}

const Mech* mech_of(int id) {
  if (!g_mechs || id < 0) return nullptr;
  for (const ArenaMech& entry : *g_mechs)
    if (entry.id == id) return entry.mech;
  return nullptr;
}

// #289: what the shot line adds, and the round or beam it started.
void log_shot_detail(int id, Weapon& weapon, ShotStarts::Report report, nlohmann::json* shot) {
  const std::string name = weapon_name(weapon.def);
  if (shot) {
    const Mech* shooter = mech_of(id);
    (*shot)["weapon"] = name;
    (*shot)["beam"] = weapon.is_beam();
    (*shot)["target"] = shooter ? target_id(shooter) : -1;
    (*shot)["locked"] = weapon.locked;
    (*shot)["muzzle"] = rounded3(weapon.muzzle.x, weapon.muzzle.y, weapon.muzzle.z);
    (*shot)["dir"] = rounded3(weapon.direction.x, weapon.direction.y, weapon.direction.z);
  }
  if (weapon.is_beam()) {
    // is_beam() is only overridden by BeamWeapon (weapon.h).
    const auto* beam_weapon = static_cast<const BeamWeapon*>(&weapon);
    if (report == ShotStarts::Report::kNewShot) g_rounds.beam_on(beam_weapon, id, name);
    if (report == ShotStarts::Report::kEnded) {
      g_rounds.beam_off(beam_weapon);
      write_line({{"type", "beam_end"}, {"t", rounded(g_now)}, {"id", id}, {"weapon", name}});
    }
    return;
  }
  // zwep::spawn put the new round on the front of its def's list just before
  // this report, at age 0. A refused spawn leaves an older round in front,
  // which is already older than 0, so it is never taken for this shot.
  const zwep::Projectile* fired = weapon.def ? weapon.def->active : nullptr;
  if (report == ShotStarts::Report::kNewShot && fired && fired->age == 0.0f) g_rounds.shot(fired, fired->owner, id, name);
}

void on_shot(Handle owner, int32_t kind, Weapon* weapon) {
  const int id = id_of(owner);
  if (id >= 0) {
    const ShotStarts::Report report = g_shot_starts.report(weapon);
    nlohmann::json shot = {{"type", "shot"}, {"t", rounded(g_now)}, {"id", id}};
    const bool is_new_shot = report == ShotStarts::Report::kNewShot;
    if (g_detail && weapon) log_shot_detail(id, *weapon, report, is_new_shot ? &shot : nullptr);
    if (is_new_shot) write_line(shot);
  }
  if (g_kept_shot) g_kept_shot(owner, kind, weapon);
}

void on_hit(Mech& mech, WeaponDef* def, Collision* collision, float damage, Handle attacker) {
  const int id = id_of(&mech);
  if (id >= 0) {
    nlohmann::json hit = {{"type", "hit"}, {"t", rounded(g_now)}, {"id", id}, {"by", id_of(attacker)}, {"damage", rounded(damage)}};
    if (g_detail && def) hit["weapon"] = weapon_name(def);
    if (g_detail && collision && collision->has_point)
      hit["at"] = rounded3(collision->point[0], collision->point[1], collision->point[2]);
    write_line(hit);
  }
  if (g_kept_hit) g_kept_hit(mech, def, collision, damage, attacker);
  else if (mech.controls) mech.controls->on_hit(attacker);  // what take_damage does with no hook
}

// #289 version 2: an "action" line when a logged mech's fall, landing,
// get-up or collapse first starts.
void on_action(Mech& mech, int kind) {
  const int id = id_of(&mech);
  const char* name = action_name(kind);
  if (id >= 0 && name) write_line({{"type", "action"}, {"t", rounded(g_now)}, {"id", id}, {"name", name}});
  if (g_kept_action) g_kept_action(mech, kind);
}

// The arena mech whose AI brain is `brain`, -1 for none.
int id_of_brain(const ai::Brain& brain) {
  if (!g_mechs) return -1;
  for (const ArenaMech& entry : *g_mechs) {
    auto* controls = dynamic_cast<AiControls*>(entry.mech->controls);
    if (controls && controls->brain.get() == &brain) return entry.id;
  }
  return -1;
}

// #289 version 2: a "voice" line for each radio line a logged bot says,
// "dropped" when the line's MINDELAY makes the game skip it.
void on_radio(ai::Brain& brain, int32_t event) {
  if (g_kept_radio) g_kept_radio(brain, event);
  const int id = id_of_brain(brain);
  if (id < 0) return;
  nlohmann::json voice = {{"type", "voice"}, {"t", rounded(g_now)}, {"id", id}, {"event", event}};
  auto* sound = brain.radio ? static_cast<zsnd::Object*>(brain.radio->sounds[event]) : nullptr;
  if (sound) {
    auto* extra = static_cast<const SoundExtra*>(zsnd::user_data(sound));
    if (sound_extra_blocked(extra ? *extra : default_extra())) voice["dropped"] = true;
  }
  write_line(voice);
}

// #289 version 2: every impact zWeapon makes; a tracked round keeps where it
// hit. Anything not a mech's node counts as terrain.
void on_impact(const zwep::Projectile* round, const zwep::HitRecord* hit, int32_t soil) {
  if (round && hit) {
    const float at[3] = {hit->point.x, hit->point.y, hit->point.z};
    const bool terrain = node_owner(hit->node) == nullptr;  // no vehicle or mech part owns the node
    g_rounds.impact(round, at, terrain);
  }
  if (g_kept_impact) g_kept_impact(round, hit, soil);
}

// #289: the DecisionNote the AI's sites call during a match: the reason goes
// to that bot's book until the frame's comparison.
void on_decision(zgame::Handle vehicle, ai::Decision why) {
  const int id = id_of_vehicle(vehicle);
  if (!g_mechs || id < 0) return;
  for (size_t i = 0; i < g_mechs->size() && i < g_decisions.size(); ++i)
    if ((*g_mechs)[i].id == id) g_decisions[i].note(why);
}

// #289: a "decision" line for each order or target change this frame.
void log_decisions(float now, const std::vector<ArenaMech>& mechs) {
  if (g_decisions.size() != mechs.size()) g_decisions.assign(mechs.size(), DecisionBook{});
  for (size_t i = 0; i < mechs.size(); ++i) {
    const Mech* mech = mechs[i].mech;
    const CurrentOrder current = current_order(mech);
    const OrderKey order = {current.state, current.count};
    const char* hunt_rule = nullptr;
    if (auto* hunt = dynamic_cast<const ai::HuntState*>(current.state)) hunt_rule = hunt_rule_name(*hunt);
    for (nlohmann::json& record : g_decisions[i].frame(order, target_id(mech), hunt_rule)) {
      record["type"] = "decision";
      record["t"] = rounded(now);
      record["id"] = mechs[i].id;
      write_line(record);
    }
  }
}

// #289: a "route" line for each bot whose route changed this frame: its
// follower's waypoints, empty when its order has no follower or no path.
void log_routes(float now, const std::vector<ArenaMech>& mechs) {
  if (g_routes.size() != mechs.size()) g_routes.assign(mechs.size(), RouteSeen{});
  for (size_t i = 0; i < mechs.size(); ++i) {
    const ai::nav::Follower* follower = current_follower(current_order(mechs[i].mech).state);
    if (!route_changed(g_routes[i], follower)) continue;
    nlohmann::json points = nlohmann::json::array();
    if (follower)
      for (const auto& point : follower->path) points.push_back(rounded3(point[0], point[1], point[2]));
    write_line({{"type", "route"}, {"t", rounded(now)}, {"id", mechs[i].id}, {"points", points}});
  }
}

// #289: the state line's "rounds", from every non-beam weapon def's list of
// shots in flight (the list at +0x7c holds Beams for beam defs instead); the
// rounds that ended since the last state line are written first.
nlohmann::json rounds_in_flight(float now) {
  std::vector<RoundSeen> flying;
  for (const zwep::WeaponDef& def : zwep::state().defs) {
    if (def.flags & zwep::kBeam) continue;
    for (const zwep::Projectile* round = def.active; round; round = round->next) {
      if (round->state != 1) continue;  // 1 flying; 2 a dormant mine
      flying.push_back(
          {round, round->age, {round->position.x, round->position.y, round->position.z}, round->owner});
    }
  }
  std::vector<nlohmann::json> ended;
  nlohmann::json rounds = g_rounds.walk(flying, &ended);
  for (nlohmann::json& record : ended) {
    record["t"] = rounded(now);
    write_line(record);
  }
  return rounds;
}

// #289: the state line's "beams": each beam weapon on, read through the
// weapon, which holds its zWeapon beam while it fires. One that stopped with
// no stop report (its part destroyed) ends here.
nlohmann::json beams_held(float now) {
  nlohmann::json beams = nlohmann::json::array();
  const std::vector<RoundBook::HeldBeam> held = g_rounds.beams();
  for (const RoundBook::HeldBeam& entry : held) {
    if (!entry.weapon->is_firing()) {
      // Both books forget it, so a later stop report can't end it twice.
      g_rounds.beam_off(entry.weapon);
      g_shot_starts.beams_on.erase(entry.weapon);
      write_line({{"type", "beam_end"}, {"t", rounded(now)}, {"id", entry.shooter}, {"weapon", entry.name}});
      continue;
    }
    const auto* beam = static_cast<const zwep::Beam*>(entry.weapon->beam);
    if (!beam || !beam->origin || !beam->dir) continue;
    const zwep::Vec3f3& from = *beam->origin;
    const zwep::Vec3f3& dir = *beam->dir;
    beams.push_back({{"by", entry.shooter},
                     {"weapon", entry.name},
                     {"from", rounded3(from.x, from.y, from.z)},
                     {"to", rounded3(from.x + dir.x * beam->length, from.y + dir.y * beam->length,
                                     from.z + dir.z * beam->length)}});
  }
  return beams;
}

void unhook() {
  g_rounds.clear();  // its weapons and pool slots belong to the mission that is ending
  if (ai::decision_note() == on_decision) ai::set_decision_note(nullptr);
  if (!g_hooked) return;
  g_hooked = false;
  // Put back only while ours is still the one installed: something that
  // wrapped ours since (the tests' counters) puts ours back itself, and ours
  // with no match does nothing but pass each call on.
  if (weapon_calls().net_event == on_shot) weapon_calls().net_event = g_kept_shot;
  if (damage_calls().controls_hit == on_hit) damage_calls().controls_hit = g_kept_hit;
  if (move_calls().action_started == on_action) move_calls().action_started = g_kept_action;
  if (ai::radio_calls().line == on_radio) ai::radio_calls().line = g_kept_radio;
  if (zwep::hit_hooks().impact_seen == on_impact) zwep::hit_hooks().impact_seen = g_kept_impact;
}
}  // namespace

void set_arena_log(std::FILE* file, int32_t frame_ms) {
  g_file = file;
  g_frame_ms = frame_ms;
}

// Ours (#289)
void set_arena_log_detail(bool on) { g_detail = on; }

// Ours (#287)
nlohmann::json mech_state_record(const ArenaMech& entry, const std::vector<ArenaMech>& mechs) {
  const std::vector<ArenaMech>* kept = g_mechs;
  g_mechs = &mechs;
  const Mech* m = entry.mech;
  float pos[3] = {};
  program_vehicle_centre(const_cast<Mech*>(m), pos);
  // The orientation is a yaw-only quaternion (w, x, y, z): forward is -z.
  const float heading = 2.0f * std::atan2(m->orientation[2], m->orientation[0]);
  nlohmann::json arms = nlohmann::json::array();
  for (const Arm* arm : m->arms)
    arms.push_back(arm ? nlohmann::json{{"yaw", rounded(arm->aim_yaw)}, {"pitch", rounded(arm->aim_pitch)}}
                       : nlohmann::json(nullptr));
  nlohmann::json parts = nlohmann::json::array();
  for (const MechPart* part : m->parts)
    if (part && part->id >= 0)
      parts.push_back({{"id", part->id}, {"armor", rounded(part->armor)}, {"internal", rounded(part->internal)},
                       {"destroyed", part->destroyed}});
  const int slots = static_cast<int>(std::size(m->anims));
  const MechAnim* anim = m->anim_index >= 0 && m->anim_index < slots ? m->anims[m->anim_index] : nullptr;
  nlohmann::json record = {
      {"id", entry.id},
      {"side", entry.side},
      {"pos", {rounded(pos[0]), rounded(pos[1]), rounded(pos[2])}},
      {"heading", rounded(heading)},
      {"speed", rounded(-m->vec_3c.z)},  // forward is the mech's -z: walking ahead is positive
      {"torso", {{"twist", rounded(m->torso ? m->torso->yaw : 0.0f)}, {"pitch", rounded(m->torso ? m->torso->pitch : 0.0f)}}},
      {"arms", arms},
      {"anim", {{"index", m->anim_index}, {"t", rounded(anim ? anim->t : 0.0f)}}},
      {"jumping", m->airborne()},
      {"fallen", m->anim_state == kAnimFallenBack || m->anim_state == kAnimFallenFront},
      {"standing", arena_standing(m)},
      {"heat", rounded(m->heat)},
      {"parts", parts},
      {"target", target_id(m)},
      {"ai", ai_record(m)},
  };
  if (g_detail) {
    add_ai_detail(m, entry.side, &record["ai"]);
    add_anim_detail(m, anim, &record["anim"]);
  }
  g_mechs = kept;
  return record;
}

// Ours (#287)
void log_match_start(const Setup& setup, const std::vector<ArenaMech>& mechs) {
  g_mechs = &mechs;
  g_now = 0;
  g_next_state = 0;
  g_record_every_update = setup.record_every_update;
  g_was_standing.assign(mechs.size(), true);
  g_routes.assign(mechs.size(), RouteSeen{});
  g_decisions.assign(mechs.size(), DecisionBook{});
  if (!g_file) return;
  nlohmann::json sides = nlohmann::json::array();
  for (const std::vector<Bot>& bots : setup.sides) {
    nlohmann::json side = nlohmann::json::array();
    for (const Bot& bot : bots)
      side.push_back({{"mech", bot.mech_name},
                      {"loadout", bot.loadout},
                      {"preset", {{"world", bot.preset.world}, {"mission", bot.preset.mission}, {"record", bot.preset.record}}}});
    sides.push_back(side);
  }
  nlohmann::json ids = nlohmann::json::array();
  for (const ArenaMech& entry : mechs) {
    nlohmann::json mech = {{"id", entry.id}, {"side", entry.side}, {"spot", entry.spot}};
    // #289 version 2: the radio voice ("dom", ...), for the 3D replay's chatter.
    auto* controls = dynamic_cast<AiControls*>(entry.mech->controls);
    const ai::Brain* brain = controls ? controls->brain.get() : nullptr;
    if (g_detail && brain && brain->params.sound_tag) mech["voice"] = brain->params.sound_tag;
    ids.push_back(mech);
  }
  nlohmann::json start = {{"type", "start"},
                          {"version", kLogVersion},
                          {"map", setup.map},
                          {"minutes", setup.minutes},
                          {"seed", arena_seed()},
                          {"frame_ms", g_frame_ms},
                          {"sides", sides},
                          {"mechs", ids}};
  if (g_record_every_update) start["record_every_update"] = true;
  write_line(start);
  // Ours may still be installed from the last match (something that wrapped
  // it put it back after we left): then what it passes on stays as it was,
  // never ours, which would call itself.
  if (weapon_calls().net_event != on_shot) g_kept_shot = weapon_calls().net_event;
  if (damage_calls().controls_hit != on_hit) g_kept_hit = damage_calls().controls_hit;
  weapon_calls().net_event = on_shot;
  damage_calls().controls_hit = on_hit;
  g_shot_starts.clear();
  g_rounds.clear();
  if (g_detail) {
    ai::set_decision_note(on_decision);
    // As above: keep what was there unless it is ours left from the last match.
    if (move_calls().action_started != on_action) g_kept_action = move_calls().action_started;
    if (ai::radio_calls().line != on_radio) g_kept_radio = ai::radio_calls().line;
    if (zwep::hit_hooks().impact_seen != on_impact) g_kept_impact = zwep::hit_hooks().impact_seen;
    move_calls().action_started = on_action;
    ai::radio_calls().line = on_radio;
    zwep::hit_hooks().impact_seen = on_impact;
  }
  g_hooked = true;
}

// Ours (#287)
ShotStarts::Report ShotStarts::report(const Weapon* weapon) {
  if (!weapon || !weapon->is_beam()) return Report::kNewShot;
  if (!weapon->is_firing()) return beams_on.erase(weapon) > 0 ? Report::kEnded : Report::kHeld;
  return beams_on.insert(weapon).second ? Report::kNewShot : Report::kHeld;
}

// Ours (#289)
void DecisionBook::note(ai::Decision why) {
  switch (why) {
    case ai::Decision::kEngage: order_code_ = "engage"; break;
    case ai::Decision::kTargetVolley: target_code_ = "target_volley"; break;
    case ai::Decision::kTargetLost: target_code_ = "target_lost"; break;
  }
}

// Ours (#289)
std::vector<nlohmann::json> DecisionBook::frame(const OrderKey& order, int target, const char* hunt_rule) {
  std::vector<nlohmann::json> records;
  if (started_) {
    if (!(order == order_)) {
      std::string code = "order_other";
      if (hunt_rule) code = std::string("hunt_") + hunt_rule;
      else if (order_code_) code = order_code_;
      records.push_back({{"code", code}});
    }
    if (target != target_) records.push_back({{"code", target_code_ ? target_code_ : "target_other"}, {"target", target}});
  }
  started_ = true;
  order_ = order;
  target_ = target;
  order_code_ = nullptr;
  target_code_ = nullptr;
  return records;
}

// Ours (#289)
bool route_changed(RouteSeen& last, const ai::nav::Follower* follower) {
  RouteSeen now;
  if (follower) now = {follower, follower->paths, follower->repaths};
  const bool changed = now.follower != last.follower || now.paths != last.paths || now.repaths != last.repaths;
  last = now;
  return changed;
}

// Ours (#289)
nlohmann::json RoundBook::end_record(const Round& round) const {
  nlohmann::json record = {{"type", "round_end"}, {"round", round.id}, {"pos", {round.pos[0], round.pos[1], round.pos[2]}}};
  if (round.has_at) {
    record["at"] = {round.at[0], round.at[1], round.at[2]};
    record["terrain"] = round.terrain;
  }
  return record;
}

// Ours (#289)
void RoundBook::impact(const void* round, const float at[3], bool terrain) {
  for (Round& known : rounds_) {
    if (known.slot != round) continue;
    known.has_at = true;
    for (int axis = 0; axis < 3; ++axis) known.at[axis] = rounded(at[axis]);
    known.terrain = terrain;
    return;
  }
}

// Ours (#289)
void RoundBook::shot(const void* round, const void* owner, int shooter, std::string weapon) {
  for (auto it = rounds_.begin(); it != rounds_.end(); ++it) {
    if (it->slot != round) continue;
    if (it->id >= 0) ended_by_reuse_.push_back(end_record(*it));
    rounds_.erase(it);
    break;
  }
  Round fired;
  fired.slot = round;
  fired.owner = owner;
  fired.shooter = shooter;
  fired.weapon = std::move(weapon);
  rounds_.push_back(std::move(fired));
}

// Ours (#289)
void RoundBook::beam_on(const BeamWeapon* weapon, int shooter, std::string name) {
  beam_off(weapon);
  beams_.push_back({weapon, shooter, std::move(name)});
}

// Ours (#289)
void RoundBook::beam_off(const BeamWeapon* weapon) {
  for (auto it = beams_.begin(); it != beams_.end(); ++it)
    if (it->weapon == weapon) {
      beams_.erase(it);
      return;
    }
}

// Ours (#289)
nlohmann::json RoundBook::walk(const std::vector<RoundSeen>& flying, std::vector<nlohmann::json>* ended) {
  for (nlohmann::json& record : ended_by_reuse_) ended->push_back(std::move(record));
  ended_by_reuse_.clear();
  for (Round& round : rounds_) round.done = true;  // until seen flying
  nlohmann::json entries = nlohmann::json::array();
  for (const RoundSeen& seen : flying) {
    Round* round = nullptr;
    for (Round& known : rounds_)
      if (known.slot == seen.round) round = &known;
    if (!round) continue;
    // A slot taken over by a shot the hook never saw: another shooter, or the
    // same one firing again (its age went down).
    const bool slot_reused = seen.owner != round->owner || (round->id >= 0 && seen.age < round->age);
    if (slot_reused) continue;  // stays done: ended below, and the new shot is not ours
    round->done = false;
    if (round->id < 0) round->id = next_id_++;
    round->age = seen.age;
    for (int axis = 0; axis < 3; ++axis) round->pos[axis] = rounded(seen.pos[axis]);
    entries.push_back({{"id", round->id},
                       {"by", round->shooter},
                       {"weapon", round->weapon},
                       {"pos", {round->pos[0], round->pos[1], round->pos[2]}}});
  }
  for (const Round& round : rounds_)
    if (round.done && round.id >= 0) ended->push_back(end_record(round));
  rounds_.erase(std::remove_if(rounds_.begin(), rounds_.end(), [](const Round& round) { return round.done; }),
                rounds_.end());
  return entries;
}

// Ours (#289)
void RoundBook::clear() {
  rounds_.clear();
  ended_by_reuse_.clear();
  beams_.clear();
  next_id_ = 0;
}

// Ours (#287)
void log_match_frame(float now, const std::vector<ArenaMech>& mechs) {
  g_mechs = &mechs;
  g_now = now;
  if (g_was_standing.size() != mechs.size()) g_was_standing.assign(mechs.size(), true);
  for (size_t i = 0; i < mechs.size(); ++i) {
    const bool standing = arena_standing(mechs[i].mech);
    if (g_was_standing[i] && !standing)
      write_line({{"type", "destroyed"}, {"t", rounded(now)}, {"id", mechs[i].id}, {"by", id_of(mechs[i].mech->attacker)}});
    g_was_standing[i] = standing;
  }
  if (g_detail && g_file) {
    log_routes(now, mechs);
    log_decisions(now, mechs);
  }
  if (!g_record_every_update && now < g_next_state) return;
  // Keep the default scheduler unchanged. Benchmark recording observes the
  // update directly, including its float clock precision, without resampling.
  if (!g_record_every_update)
    while (g_next_state <= now) g_next_state += kLogStatePeriod;
  if (!g_file) return;
  const double state_time = g_record_every_update ? static_cast<double>(now) : rounded(now);
  nlohmann::json state = {{"type", "state"}, {"t", state_time}, {"mechs", nlohmann::json::array()}};
  for (const ArenaMech& entry : mechs) state["mechs"].push_back(mech_state_record(entry, mechs));
  if (g_detail) {
    state["rounds"] = rounds_in_flight(now);
    state["beams"] = beams_held(now);
  }
  write_line(state);
}

// Ours (#287)
void log_match_end(const Result& result) {
  // #289: every round still flying and beam still held ends before the end
  // line, so a viewer never has one left open (unhook forgets them).
  if (g_detail) {
    std::vector<nlohmann::json> ended;
    g_rounds.walk({}, &ended);  // nothing flying: every round with an id ends
    for (nlohmann::json& record : ended) {
      record["t"] = rounded(result.time);
      write_line(record);
    }
    for (const RoundBook::HeldBeam& entry : g_rounds.beams())
      write_line({{"type", "beam_end"}, {"t", rounded(result.time)}, {"id", entry.shooter}, {"weapon", entry.name}});
  }
  unhook();
  write_line({{"type", "end"},
              {"winner", result.winner == 0 ? "A" : result.winner == 1 ? "B" : "draw"},
              {"t", rounded(result.time)},
              {"lost", {result.lost[0], result.lost[1]}}});
  g_mechs = nullptr;
}

void log_match_stop() {
  unhook();
  g_mechs = nullptr;
}

// Ours (#287)
LogRead read_arena_log(const std::string& path) {
  LogRead read;
  std::ifstream in(path, std::ios::binary);
  if (!in) return read;
  read.opened = true;
  std::string line;
  while (std::getline(in, line)) {
    if (line.empty()) continue;
    nlohmann::json record = nlohmann::json::parse(line, nullptr, false);
    if (record.is_discarded() || !record.is_object()) {
      ++read.bad_lines;
      continue;
    }
    read.records.push_back(std::move(record));
  }
  // A line's type, or "" when it has none or a type that isn't text (a
  // damaged log must be refused with a message, never throw).
  const auto type_of = [](const nlohmann::json& record) -> std::string {
    const auto it = record.find("type");
    return it != record.end() && it->is_string() ? it->get<std::string>() : std::string();
  };
  const nlohmann::json* start = read.records.empty() ? nullptr : &read.records.front();
  const bool has_start = start && type_of(*start) == "start";
  const bool has_version = has_start && start->contains("version") && (*start)["version"].is_number_integer();
  if (!has_start) {
    read.error = "no readable start line (empty or damaged log)";
  } else if (!has_version) {
    read.error = "no whole-number format version (a log from before #289)";
  } else {
    const int version = (*start)["version"].get<int>();
    if (version < kOldestLogVersion || version > kLogVersion)
      read.error = "format version " + std::to_string(version) + ", this build reads versions " +
                   std::to_string(kOldestLogVersion) + " and " + std::to_string(kLogVersion);
  }
  if (!read.error.empty()) {
    read.records.clear();
    return read;
  }
  read.complete = type_of(read.records.back()) == "end";
  return read;
}

}  // namespace mech3::arena
