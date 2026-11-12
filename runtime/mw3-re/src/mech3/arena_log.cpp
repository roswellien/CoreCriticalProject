#include "mech3/arena_log.h"

#include <cmath>
#include <fstream>

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
bool g_hooked = false;
ShotStarts g_shot_starts;
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

// The arena id of what a mech's AI has targeted, -1 for none.
int target_id(const Mech* mech) {
  const ai::Contact* contact = mech->target;
  if (!contact || !g_mechs) return -1;
  ai::BrainHooks& hooks = ai::brain_hooks();
  const zgame::Handle seen = hooks.contact_vehicle(contact);
  for (const ArenaMech& entry : *g_mechs)
    if (hooks.vehicle_handle(entry.mech) == seen) return entry.id;
  return -1;
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
    static const char* const kRules[] = {"contact", "last_seen", "fallback"};
    ai["order"] = "hunt";
    ai["goal_rule"] = kRules[static_cast<int>(hunt->goal.rule)];
    ai["goal"] = {rounded(hunt->goal.at[0]), rounded(hunt->goal.at[1]), rounded(hunt->goal.at[2])};
  } else if (dynamic_cast<const ai::FightState*>(state)) {
    ai["order"] = "fight";
  } else {
    ai["order"] = "other";
  }
  return ai;
}

void on_shot(Handle owner, int32_t kind, Weapon* weapon) {
  const int id = id_of(owner);
  if (id >= 0 && g_shot_starts.is_new_shot(weapon)) write_line({{"type", "shot"}, {"t", rounded(g_now)}, {"id", id}});
  if (g_kept_shot) g_kept_shot(owner, kind, weapon);
}

void on_hit(Mech& mech, WeaponDef* def, Collision* collision, float damage, Handle attacker) {
  const int id = id_of(&mech);
  if (id >= 0)
    write_line({{"type", "hit"}, {"t", rounded(g_now)}, {"id", id}, {"by", id_of(attacker)}, {"damage", rounded(damage)}});
  if (g_kept_hit) g_kept_hit(mech, def, collision, damage, attacker);
  else if (mech.controls) mech.controls->on_hit(attacker);  // what take_damage does with no hook
}

void unhook() {
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
  g_mechs = kept;
  return record;
}

// Ours (#287)
void log_match_start(const Setup& setup, const std::vector<ArenaMech>& mechs) {
  g_mechs = &mechs;
  g_now = 0;
  g_next_state = 0;
  g_was_standing.assign(mechs.size(), true);
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
  g_hooked = true;
}

// Ours (#287)
bool ShotStarts::is_new_shot(const Weapon* weapon) {
  if (!weapon || !weapon->is_beam()) return true;
  if (!weapon->is_firing()) {
    beams_on.erase(weapon);
    return false;
  }
  return beams_on.insert(weapon).second;
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
  if (now < g_next_state) return;
  // Each due time once, on the first frame at or past it: the same seed and
  // frame time give the same frames, so the same lines.
  while (g_next_state <= now) g_next_state += kLogStatePeriod;
  if (!g_file) return;
  nlohmann::json state = {{"type", "state"}, {"t", rounded(now)}, {"mechs", nlohmann::json::array()}};
  for (const ArenaMech& entry : mechs) state["mechs"].push_back(mech_state_record(entry, mechs));
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
