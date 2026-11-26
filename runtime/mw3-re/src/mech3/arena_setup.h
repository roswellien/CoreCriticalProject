#pragma once

#include <array>
#include <cstdint>
#include <cstdio>
#include <memory>
#include <string>
#include <vector>

#include "gamez/zreader/zreader.h"
#include "mech3/zai_params.h"

// Ours, not the exe's (#287, docs/arena.md): the arena run's setup file and
// every check that refuses a run (exit 2) before the engine starts. The setup
// is read game-free; the map's spawn spots and the pilot presets are read from
// the player's own game files once the install is mounted, and the match log
// is created last, so a refused run loads nothing and writes nothing.

namespace mech3 {
struct MechDfn;
}

namespace mech3::arena {

// A pilot preset: a shipped aiv record, named by the reader it lives in
// (zbd\<world>\reader<mission>.zbd, for example world "c1", mission "ia1")
// and its record name. Only the name is kept in the setup; the values are
// read from the player's files at run time and never committed.
struct Preset {
  std::string world;
  std::string mission;
  std::string record;
};

struct Bot {
  std::string mech_name;  // as the setup gives it
  int32_t mech = -1;      // mech_index(mech_name)
  // Which of the chassis' stock loadouts it gets: an index into its config
  // list (MechDfn::configs, AiParams +0xbc), 0 the first. Checked against the
  // game files in read_arena_game_files: only the stock ones, never a
  // player's saved loadout or a training one.
  int32_t loadout = 0;
  Preset preset;
  // The preset record's AI params (AiParams::raw), filled by
  // read_arena_game_files. Raw bytes so the setup never holds a live record
  // (an AivRecord keeps a reference on the mission's aiv.zrd).
  std::array<uint8_t, ai::AiParams::kEnd> params = {};
  bool params_read = false;
  // The record's pilot name and radio voice (AiParams::pilot, sound_tag), kept
  // as text for the same reason; empty when the record has none.
  std::string pilot, voice;
};

constexpr int kSides = 2;
constexpr int kMaxBotsPerSide = 8;  // two lances
constexpr int kSpawnSpots = 16;     // remote_0 .. remote_15, as net_respawn_point walks them

// Ours (#507): the arena's times of day, each the campaign mission whose
// lighting profile (sun, ambient, sky and haze, campaign_lighting.hpp) a
// watched match borrows. Outdoor missions only. Visual only: the simulation
// never reads it.
struct TimeOfDay {
  const char* name;
  const char* lighting_mission;
};
inline constexpr TimeOfDay kTimesOfDay[] = {
    {"dawn", "t1m1"},   // Training 1, dawn
    {"day", "c3m1"},    // high noon
    {"dusk", "t1m4"},   // Training 4, dusk
    {"night", "c1m3"},  // dead of night
};
// The lighting mission for a name in kTimesOfDay; null for any other.
const char* time_of_day_lighting(const std::string& name);

struct Setup {
  std::string map;      // the lobby map id, e.g. "c1mp1"
  std::string dir;      // its world folder, "c1"
  int32_t number = 0;   // its multiplayer map number, 1
  int32_t minutes = 0;  // the time limit
  std::string out;      // the match log's folder
  // Optional (#507): one of kTimesOfDay's names; empty for the map's own lighting.
  std::string time_of_day;
  std::vector<Bot> sides[kSides];
};

// "c1mp1": world folder "c1", multiplayer map 1. False unless the folder is
// one of the game's worlds and the number is above 0; whether the map ships
// (and has its 16 spawn spots) is read from the game files later.
bool split_map(const std::string& map, std::string* dir, int32_t* number);
// Ours (#289): whether multiplayer map `number` of world `dir` has its reader
// in the game files (the install mounted).
bool map_reader_ships(const std::string& dir, int32_t number);
// Ours (#287): how many stock loadouts the chassis has, the first of its
// config list; -1 when its definition can't be read. Its loadouts are the
// indices below that.
int32_t stock_loadout_count(int32_t mech);
// Ours (#287): the chassis' definition (mech_dfn), readable before launch too.
const MechDfn* arena_mech_dfn(int32_t mech);

// Ours (#287): one reader's aiv.zrd as a node tree, read straight from its
// archive (the game's archives are not open before launch), freed with it.
struct AivTree {
  zrdr::Node* root = nullptr;
  AivTree() = default;
  AivTree(const AivTree&) = delete;
  AivTree& operator=(const AivTree&) = delete;
  ~AivTree();
  bool read(const std::string& reader);
  // As the game's aiv_read_named finds it (zrdr::find, anywhere in the file).
  zrdr::Node* find(const char* name) const;
};
// "zbd\<world>\reader<mission>.zbd"
std::string reader_path(const std::string& world, const std::string& mission);

// Reads the setup's JSON text. False with *error naming the field (for
// example "sides[1][0].mech: unknown mech \"notmech\"") on any bad value.
bool parse_arena_setup(const std::string& json_text, Setup* out, std::string* error);
// The same from a file; a file that cannot be read is an error naming it.
bool read_arena_setup(const std::string& path, Setup* out, std::string* error);

// Which command-line options came with --arena. The arena owns the session,
// the map, the clock and the run's length, and must repeat, so these refuse.
struct Flags {
  bool host = false, join = false, net_upnp = false, original = false, mission = false;
  bool net_minutes = false, net_soak = false, net_drive = false, frames = false;
  bool seed = false, frame_ms = false;
  // Options that drive the player's mech or a menu screen; the arena has neither.
  bool fire = false, net_walk = false, net_ahead = false, briefing = false, lab_mech = false;
};
// "" when the run may go on, else the message naming the option.
std::string arena_refusal(const Flags& f);

// With the install mounted: the map's reader and its 16 remote_ spawn spots,
// and every bot's preset record, copied into Bot::params. False with *error
// naming the field.
bool read_arena_game_files(Setup* setup, std::string* error);

// <out>/match-<seed>.jsonl, created only when it does not exist yet (the
// folder made first). Null with *error when it exists or cannot be made; an
// existing file is left as it is.
struct FileClose {
  void operator()(std::FILE* f) const {
    if (f) std::fclose(f);
  }
};
using LogFile = std::unique_ptr<std::FILE, FileClose>;
LogFile create_arena_log(const Setup& setup, int64_t seed, std::string* path, std::string* error);

}  // namespace mech3::arena
