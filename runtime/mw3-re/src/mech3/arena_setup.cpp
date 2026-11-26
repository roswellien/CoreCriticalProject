#include "mech3/arena_setup.h"

#include <cstdlib>
#include <cstring>
#include <filesystem>
#include <fstream>
#include <map>
#include <sstream>

#include <nlohmann-json/json.hpp>

#include "gamez/zreader/zreader.h"
#include "gamez/zutil/zutl_path.h"
#include "gamez/zutil/zutl_zar.h"
#include "mech3/mech_config.h"
#include "mech3/mech_names.h"
#include "mech3/mech_reader.h"
#include "mech3/mission.h"
#include "mech3/zrdraiv.h"

namespace mech3::arena {

namespace {

using Json = nlohmann::json;

// The setup's folders are the game's world folders (mission_dir: c1 c2 c3
// c4 c4b t1 ..., and a mod's).
bool is_world(const std::string& dir) { return mission_dir_index(dir.c_str()) >= 0; }

bool all_digits(const std::string& s, size_t from) {
  return from < s.size() && s.find_first_not_of("0123456789", from) == std::string::npos;
}

}  // namespace

// Ours (#287; public since #289, for the replay viewer's terrain).
bool split_map(const std::string& map, std::string* dir, int32_t* number) {
  const size_t mp = map.rfind("mp");
  if (mp == std::string::npos || mp == 0 || !all_digits(map, mp + 2)) return false;
  *dir = map.substr(0, mp);
  *number = std::atoi(map.c_str() + mp + 2);
  return is_world(*dir) && *number > 0;
}

namespace {

// A reader's mission part: m<N> (campaign), ia<N> (Instant Action) or mp<N>.
bool is_reader_mission(const std::string& m) {
  if (m.rfind("ia", 0) == 0 || m.rfind("mp", 0) == 0) return all_digits(m, 2);
  return m.rfind('m', 0) == 0 && all_digits(m, 1);
}

bool fail(std::string* error, const std::string& message) {
  if (error) *error = message;
  return false;
}

bool parse_preset(const Json& j, const std::string& field, Preset* out, std::string* error) {
  if (!j.is_object()) return fail(error, field + ": needs {\"world\", \"mission\", \"record\"}");
  const auto text = [&](const char* key, std::string* value) {
    const auto it = j.find(key);
    if (it == j.end() || !it->is_string() || it->get<std::string>().empty()) return false;
    *value = it->get<std::string>();
    return true;
  };
  if (!text("world", &out->world) || !is_world(out->world))
    return fail(error, field + ".world: not a game world (c1 c2 c3 c4 ...)");
  if (!text("mission", &out->mission) || !is_reader_mission(out->mission))
    return fail(error, field + ".mission: not a reader (m<N>, ia<N> or mp<N>)");
  if (!text("record", &out->record)) return fail(error, field + ".record: needs the aiv record's name");
  return true;
}

bool parse_bot(const Json& j, const std::string& field, Bot* out, std::string* error) {
  if (!j.is_object()) return fail(error, field + ": needs {\"mech\", \"preset\"}");
  const auto mech = j.find("mech");
  if (mech == j.end() || !mech->is_string()) return fail(error, field + ".mech: needs a mech name");
  out->mech_name = mech->get<std::string>();
  out->mech = mech_index(out->mech_name.c_str());
  // "notmech" (mech_name's answer for a bad index) is not in the roster, so
  // mech_index refuses it too.
  if (out->mech < 0) return fail(error, field + ".mech: unknown mech \"" + out->mech_name + "\"");
  const auto preset = j.find("preset");
  if (preset == j.end()) return fail(error, field + ".preset: needs a pilot preset");
  // Optional: which stock loadout (0 the first); the count is checked once the
  // game files are mounted.
  if (const auto loadout = j.find("loadout"); loadout != j.end()) {
    if (!loadout->is_number_integer() || loadout->get<int64_t>() < 0 || loadout->get<int64_t>() > 15)
      return fail(error, field + ".loadout: needs a whole number, 0 to 15");
    out->loadout = static_cast<int32_t>(loadout->get<int64_t>());
  }
  return parse_preset(*preset, field + ".preset", &out->preset, error);
}

}  // namespace

std::string reader_path(const std::string& world, const std::string& mission) {
  return "zbd\\" + world + "\\reader" + mission + ".zbd";
}

// zrdr::load can't be used: it reads from the game's open archives, which are
// not open before launch, and aiv.zrd is one name in every reader.
AivTree::~AivTree() {
  if (root) zrdr::free_node(root);
}

bool AivTree::read(const std::string& reader) {
  zutl_zar::Archive archive;
  zutl_zar::init(archive);
  if (!zutl_zar::open(archive, reader.c_str())) {
    zutl_zar::destroy(archive);
    return false;
  }
  uint32_t length = 0;
  if (std::FILE* f = zutl_zar::seek(archive, zutl_zar::find(archive, "aiv.zrd"), &length)) {
    root = zrdr::new_nodes(zrdr::List, 1);
    zrdr::read_node(f, root);
  }
  zutl_zar::destroy(archive);  // closes the file, frees the table and the path
  return root != nullptr;
}

zrdr::Node* AivTree::find(const char* name) const { return root ? zrdr::find(root, name) : nullptr; }

// Ours (#287): the definitions live in zbd\reader.zbd, which the game opens at
// start-up (app.cpp); before that no archive is open and zrdr::load finds
// nothing. So when none is open, that one is opened for the read and closed
// again; the definition stays cached in mech_dfn's table for the game.
const MechDfn* arena_mech_dfn(int32_t mech) {
  if (!zrdr::state().archives.empty()) return mech_dfn(mech);
  zrdr::init();
  if (!zrdr::open_archive("zbd\\reader.zbd", false)) return nullptr;
  const MechDfn* dfn = mech_dfn(mech);
  zrdr::close_archives(true);
  return dfn;
}

// Ours (#287): stock configs come first in the list (read_configurations, in
// file order); a player's saved ones (player_made) are appended after them,
// and the training ones are flagged.
int32_t stock_loadout_count(int32_t mech) {
  const MechDfn* dfn = arena_mech_dfn(mech);
  if (!dfn || !dfn->configs) return -1;
  int32_t count = 0;
  for (const Config* c : dfn->configs->configs) {
    if (!c || c->player_made) break;
    if (c->training) break;
    ++count;
  }
  return count;
}

// Ours (#289): whether the multiplayer map's reader ships in the game files.
bool map_reader_ships(const std::string& dir, int32_t number) {
  AivTree map;
  return map.read(reader_path(dir, "mp" + std::to_string(number)));
}

// Ours (#507)
const char* time_of_day_lighting(const std::string& name) {
  for (const TimeOfDay& t : kTimesOfDay)
    if (name == t.name) return t.lighting_mission;
  return nullptr;
}

// Ours (#287): the setup file's fields, each refused by name.
bool parse_arena_setup(const std::string& json_text, Setup* out, std::string* error) {
  *out = Setup{};
  const Json j = Json::parse(json_text, nullptr, false);
  if (j.is_discarded() || !j.is_object()) return fail(error, "setup: not a JSON object");

  const auto map = j.find("map");
  if (map == j.end() || !map->is_string()) return fail(error, "map: needs a lobby map id (c1mp1 ...)");
  out->map = map->get<std::string>();
  if (!split_map(out->map, &out->dir, &out->number))
    return fail(error, "map: unknown map \"" + out->map + "\"");

  const auto minutes = j.find("minutes");
  if (minutes == j.end() || !minutes->is_number_integer() || minutes->get<int64_t>() <= 0 ||
      minutes->get<int64_t>() > 600)
    return fail(error, "minutes: needs a whole number of minutes, 1 to 600");
  out->minutes = static_cast<int32_t>(minutes->get<int64_t>());

  const auto folder = j.find("out");
  if (folder == j.end() || !folder->is_string() || folder->get<std::string>().empty())
    return fail(error, "out: needs the match log's folder");
  out->out = folder->get<std::string>();

  // Optional (#507); absent or null is the map's own lighting.
  if (const auto time = j.find("time_of_day"); time != j.end() && !time->is_null()) {
    std::string names;
    for (const TimeOfDay& t : kTimesOfDay) names += std::string(names.empty() ? "" : ", ") + t.name;
    if (!time->is_string() || !time_of_day_lighting(time->get<std::string>()))
      return fail(error, "time_of_day: needs one of " + names + " (or null for the map's own lighting)");
    out->time_of_day = time->get<std::string>();
  }

  const auto sides = j.find("sides");
  if (sides == j.end() || !sides->is_array() || sides->size() != kSides)
    return fail(error, "sides: needs two lists of bots");
  for (int side = 0; side < kSides; ++side) {
    const Json& list = (*sides)[side];
    const std::string field = "sides[" + std::to_string(side) + "]";
    if (!list.is_array() || list.empty()) return fail(error, field + ": needs at least one bot");
    if (list.size() > kMaxBotsPerSide)
      return fail(error, field + ": " + std::to_string(list.size()) + " bots, at most " +
                             std::to_string(kMaxBotsPerSide));
    for (size_t i = 0; i < list.size(); ++i) {
      Bot bot;
      if (!parse_bot(list[i], field + "[" + std::to_string(i) + "]", &bot, error)) return false;
      out->sides[side].push_back(bot);
    }
  }
  return true;
}

// Ours (#287)
bool read_arena_setup(const std::string& path, Setup* out, std::string* error) {
  std::ifstream f(path, std::ios::binary);
  if (!f) return fail(error, "setup: cannot read " + path);
  std::stringstream text;
  text << f.rdbuf();
  return parse_arena_setup(text.str(), out, error);
}

// Ours (#287): the first refused option, in the order the usage lists them.
std::string arena_refusal(const Flags& f) {
  if (f.host) return "--arena: --host is refused (the arena opens no network)";
  if (f.join) return "--arena: --join is refused (the arena opens no network)";
  if (f.net_upnp) return "--arena: --net-upnp is refused (the arena opens no network)";
  if (f.original) return "--arena: --original is refused (the arena needs the bug fixes)";
  if (f.mission) return "--arena: --mission is refused (the setup's map is the mission)";
  if (f.net_minutes) return "--arena: --net-minutes is refused (the setup's minutes are the clock)";
  if (f.net_soak) return "--arena: --net-soak is refused";
  if (f.net_drive) return "--arena: --net-drive is refused";
  if (f.frames) return "--arena: --frames is refused (the match runs to its end)";
  if (f.fire) return "--arena: --fire is refused (there is no player mech)";
  if (f.net_walk) return "--arena: --net-walk is refused (there is no player mech)";
  if (f.net_ahead) return "--arena: --net-ahead is refused (there is no player mech)";
  if (f.briefing) return "--arena: --briefing is refused (the arena opens no menus)";
  if (f.lab_mech) return "--arena: --lab-mech is refused (the arena opens no menus)";
  if (!f.seed) return "--arena: needs --seed (a match log must repeat)";
  if (!f.frame_ms) return "--arena: needs --frame-ms (a match log must repeat)";
  return {};
}

// Ours (#287): the map and the presets from the player's game files.
bool read_arena_game_files(Setup* setup, std::string* error) {
  AivTree map;
  if (!map.read(reader_path(setup->dir, "mp" + std::to_string(setup->number))))
    return fail(error, "map: unknown map \"" + setup->map + "\" (no reader in the game files)");
  for (int spot = 0; spot < kSpawnSpots; ++spot)
    if (!map.find(("remote_" + std::to_string(spot)).c_str()))
      return fail(error, "map: \"" + setup->map + "\" has no 16 remote_ spawn spots");

  // Each reader once, however many bots name it.
  std::map<std::string, std::unique_ptr<AivTree>> readers;
  for (int side = 0; side < kSides; ++side) {
    for (size_t i = 0; i < setup->sides[side].size(); ++i) {
      Bot& bot = setup->sides[side][i];
      const std::string at = "sides[" + std::to_string(side) + "][" + std::to_string(i) + "]";
      // Loadout 0 is every chassis' first stock one, so only another needs
      // the definition read here; a setup without loadouts reads nothing new
      // before launch (the in-process repeat test, arena_log_detail_*, showed
      // an early read changes a later match in the same process).
      const int32_t stock = bot.loadout == 0 ? 1 : stock_loadout_count(bot.mech);
      if (bot.loadout >= stock)
        return fail(error, at + ".loadout: " + std::to_string(bot.loadout) + " is not a stock loadout of " +
                               bot.mech_name + " (it has " + std::to_string(stock < 0 ? 0 : stock) + ")");
      const std::string field = at + ".preset";
      const std::string reader = reader_path(bot.preset.world, bot.preset.mission);
      std::unique_ptr<AivTree>& tree = readers[reader];
      if (!tree) {
        tree = std::make_unique<AivTree>();
        tree->read(reader);
      }
      if (!tree->root) return fail(error, field + ": cannot read " + reader);
      zrdr::Node* value = tree->find(bot.preset.record.c_str());
      if (!value) return fail(error, field + ": no record \"" + bot.preset.record + "\" in " + reader);
      // parse reads the record as a mission start does (ranges squared, the
      // yaw in radians); its raw block, pilot and voice are kept.
      ai::AivRecord record;
      record.parse(value, bot.preset.record.c_str());
      std::memcpy(bot.params.data(), record.raw, bot.params.size());
      bot.pilot = record.pilot ? record.pilot : "";
      bot.voice = record.sound_tag ? record.sound_tag : "";
      bot.params_read = true;
    }
  }
  return true;
}

// Ours (#287): "x" opens only a file that does not exist yet, so two runs
// with the same seed and folder never write one log.
LogFile create_arena_log(const Setup& setup, int64_t seed, std::string* path, std::string* error) {
  std::error_code ec;
  std::filesystem::create_directories(setup.out, ec);
  const std::string file = (std::filesystem::path(setup.out) / ("match-" + std::to_string(seed) + ".jsonl")).string();
  if (path) *path = file;
  if (std::filesystem::exists(file, ec)) {
    fail(error, "out: " + file + " already exists (left as it is)");
    return nullptr;
  }
  LogFile f(std::fopen(file.c_str(), "wbx"));
  if (!f) fail(error, "out: cannot create " + file);
  return f;
}

}  // namespace mech3::arena
