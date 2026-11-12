#include "mech3/arena_log.h"

#include <algorithm>
#include <cmath>
#include <fstream>

#include "gamez/zweapon/zweapon.h"
#include "gamez/zweapon/zwep_init.h"
#include "mech3/app_mech.h"
#include "mech3/mech.h"
#include "mech3/mech_anim.h"
#include "mech3/mech_control.h"
#include "mech3/mech_parts.h"
#include "mech3/weapon.h"
#include "mech3/zai_attack.h"
#include "mech3/zai_hunt.h"

namespace mech3::arena {

namespace {
std::FILE* g_file = nullptr;
int32_t g_frame_ms = 0;
bool g_detail = true;

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

const ai::BehaviourState* current_state(const Mech* mech) {
  auto* controls = dynamic_cast<AiControls*>(mech->controls);
  ai::Brain* brain = controls ? controls->brain.get() : nullptr;
  if (!brain || brain->orders.empty()) return nullptr;
  return brain->current().state.get();
}

// #289: the route and contact fields of the ai record.
void add_ai_detail(const Mech* mech, int self_side, nlohmann::json* ai) {
  const ai::nav::Follower* follower = current_follower(current_state(mech));
  (*ai)["at"] = follower ? follower->at : -1;
  nlohmann::json contacts = nlohmann::json::array();
  for (const ai::Contact* contact : mech->contacts) {
    const int id = id_of_contact(contact);
    if (id < 0 || side_of(id) == self_side) continue;
    contacts.push_back({{"id", id}, {"seen", (contact->flags & 1) != 0}});  // bit 0: the sensors detect it now (zai_target.h)
  }
  (*ai)["contacts"] = contacts;
}

const char* hunt_rule_name(const ai::HuntState& hunt) {
  static const char* const kRules[] = {"contact", "last_seen", "fallback"};
  return kRules[static_cast<int>(hunt.goal.rule)];
}

// The order a mech's brain is running: its own hunt, the stock fight, or
// another of the game's.
nlohmann::json ai_record(const Mech* mech) {
  nlohmann::json ai = nlohmann::json::object();
  auto* controls = dynamic_cast<AiControls*>(mech->controls);
  ai::Brain* brain = controls ? controls->brain.get() : nullptr;
  if (!brain || brain->orders.empty()) return ai;
  const ai::BehaviourState* state = brain->current().state.get();
  if (auto* hunt = dynamic_cast<const ai::HuntState*>(state)) {
    ai["order"] = "hunt";
    ai["goal_rule"] = hunt_rule_name(*hunt);
    ai["goal"] = {rounded(hunt->goal.at[0]), rounded(hunt->goal.at[1]), rounded(hunt->goal.at[2])};
  } else if (dynamic_cast<const ai::FightState*>(state)) {
    ai["order"] = "fight";
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
  if (report == ShotStarts::Report::kNewShot && fired && fired->age == 0.0f) g_rounds.shot(fired, id, name);
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
    write_line(hit);
  }
  if (g_kept_hit) g_kept_hit(mech, def, collision, damage, attacker);
  else if (mech.controls) mech.controls->on_hit(attacker);  // what take_damage does with no hook
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
    auto* controls = dynamic_cast<AiControls*>(mech->controls);
    ai::Brain* brain = controls ? controls->brain.get() : nullptr;
    OrderKey order;
    const char* hunt_rule = nullptr;
    if (brain && !brain->orders.empty()) {
      const ai::BehaviourState* state = brain->current().state.get();
      order = {state, brain->orders.size()};
      if (auto* hunt = dynamic_cast<const ai::HuntState*>(state)) hunt_rule = hunt_rule_name(*hunt);
    }
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
    const ai::nav::Follower* follower = current_follower(current_state(mechs[i].mech));
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
      flying.push_back({round, round->age, {round->position.x, round->position.y, round->position.z}});
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
      g_rounds.beam_off(entry.weapon);
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
}
}  // namespace

void set_arena_log(std::FILE* file, int32_t frame_ms) {
  g_file = file;
  g_frame_ms = frame_ms;
}

// Ours (#289)
void set_arena_log_detail(bool on) { g_detail = on; }
bool arena_log_detail() { return g_detail; }

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
  const MechAnim* anim = m->anim_index >= 0 && m->anim_index < 13 ? m->anims[m->anim_index] : nullptr;
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
  if (g_detail) add_ai_detail(m, entry.side, &record["ai"]);
  g_mechs = kept;
  return record;
}

// Ours (#287)
void log_match_start(const Setup& setup, const std::vector<ArenaMech>& mechs) {
  g_mechs = &mechs;
  g_now = 0;
  g_next_state = 0;
  g_was_standing.assign(mechs.size(), true);
  g_routes.assign(mechs.size(), RouteSeen{});
  g_decisions.assign(mechs.size(), DecisionBook{});
  if (!g_file) return;
  nlohmann::json sides = nlohmann::json::array();
  for (const std::vector<Bot>& bots : setup.sides) {
    nlohmann::json side = nlohmann::json::array();
    for (const Bot& bot : bots)
      side.push_back({{"mech", bot.mech_name},
                      {"preset", {{"world", bot.preset.world}, {"mission", bot.preset.mission}, {"record", bot.preset.record}}}});
    sides.push_back(side);
  }
  nlohmann::json ids = nlohmann::json::array();
  for (const ArenaMech& entry : mechs) ids.push_back({{"id", entry.id}, {"side", entry.side}, {"spot", entry.spot}});
  write_line({{"type", "start"},
              {"version", kLogVersion},
              {"map", setup.map},
              {"minutes", setup.minutes},
              {"seed", arena_seed()},
              {"frame_ms", g_frame_ms},
              {"sides", sides},
              {"mechs", ids}});
  // Ours may still be installed from the last match (something that wrapped
  // it put it back after we left): then what it passes on stays as it was,
  // never ours, which would call itself.
  if (weapon_calls().net_event != on_shot) g_kept_shot = weapon_calls().net_event;
  if (damage_calls().controls_hit != on_hit) g_kept_hit = damage_calls().controls_hit;
  weapon_calls().net_event = on_shot;
  damage_calls().controls_hit = on_hit;
  g_shot_starts.clear();
  g_rounds.clear();
  if (g_detail) ai::set_decision_note(on_decision);
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
  return {{"type", "round_end"}, {"round", round.id}, {"pos", {round.pos[0], round.pos[1], round.pos[2]}}};
}

// Ours (#289)
void RoundBook::shot(const void* round, int shooter, std::string weapon) {
  for (auto it = rounds_.begin(); it != rounds_.end(); ++it) {
    if (it->slot != round) continue;
    if (it->id >= 0) ended_by_reuse_.push_back(end_record(*it));
    rounds_.erase(it);
    break;
  }
  Round fired;
  fired.slot = round;
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
    const bool slot_reused = round->id >= 0 && seen.age < round->age;
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
  if (g_detail) {
    log_routes(now, mechs);
    log_decisions(now, mechs);
  }
  if (now < g_next_state) return;
  // Each due time once, on the first frame at or past it: the same seed and
  // frame time give the same frames, so the same lines.
  while (g_next_state <= now) g_next_state += kLogStatePeriod;
  if (!g_file) return;
  nlohmann::json state = {{"type", "state"}, {"t", rounded(now)}, {"mechs", nlohmann::json::array()}};
  for (const ArenaMech& entry : mechs) state["mechs"].push_back(mech_state_record(entry, mechs));
  if (g_detail) {
    state["rounds"] = rounds_in_flight(now);
    state["beams"] = beams_held(now);
  }
  write_line(state);
}

// Ours (#287)
void log_match_end(const Result& result) {
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
  const nlohmann::json* start = read.records.empty() ? nullptr : &read.records.front();
  const bool has_version = start && start->value("type", "") == "start" && start->contains("version") &&
                           (*start)["version"].is_number_integer();
  if (!has_version) {
    read.error = "no format version (a log from before #289)";
  } else if ((*start)["version"].get<int>() != kLogVersion) {
    read.error = "format version " + std::to_string((*start)["version"].get<int>()) + ", this build reads " +
                 std::to_string(kLogVersion);
  }
  if (!read.error.empty()) {
    read.records.clear();
    return read;
  }
  read.complete = read.records.back().value("type", "") == "end";
  return read;
}

}  // namespace mech3::arena
