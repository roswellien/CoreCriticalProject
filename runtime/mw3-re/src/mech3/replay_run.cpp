#include "mech3/replay_run.h"

#include <set>

#include "gamez/znetwork/znet_session.h"
#include "mech3/arena.h"
#include "mech3/arena_setup.h"
#include "mech3/mech.h"
#include "mech3/mech_names.h"

namespace mech3::replay {

std::string replay_map_refusal(const std::string& map) {
  std::string dir;
  int32_t number = 0;
  if (!arena::split_map(map, &dir, &number))
    return "--replay3d: the log's map \"" + map + "\" is not a multiplayer map (<world>mp<N>)";
  return "";
}

ReplayRun::ReplayRun() = default;

ReplayRun::~ReplayRun() {
  if (!hub_) return;
  world().arena_spectating = false;
  znet::shutdown();
  hub_.reset();
}

bool ReplayRun::read(const std::string& path, std::string* message) {
  return load_log(path, message) && check_game_files(message);
}

bool ReplayRun::load_log(const std::string& path, std::string* message) {
  if (!log_.load(path, message)) {
    *message = "--replay3d: " + *message;
    return false;
  }
  if (const std::string refused = replay_map_refusal(log_.map()); !refused.empty()) {
    *message = refused;
    return false;
  }
  return true;
}

bool ReplayRun::check_game_files(std::string* message) const {
  std::string dir;
  int32_t number = 0;
  arena::split_map(log_.map(), &dir, &number);
  if (!arena::map_reader_ships(dir, number)) {
    *message = "--replay3d: the log's map \"" + log_.map() + "\" is not in the game files";
    return false;
  }
  // Every chassis known before any puppet is made.
  for (const MechInfo& mech : log_.mechs()) {
    if (mech_index(mech.chassis.c_str()) < 0) {
      *message = "--replay3d: mech " + std::to_string(mech.id) + " has an unknown chassis \"" + mech.chassis + "\"";
      return false;
    }
  }
  return true;
}

bool ReplayRun::open(std::string* message) {
  hub_ = std::make_unique<znet::Hub>();
  if (!arena::arena_open_session(*hub_)) {
    *message = "--replay3d: the in-process session failed";
    hub_.reset();
    return false;
  }
  world().arena_spectating = true;  // no player mech: the stock player-only rules stay off
  return true;
}

}  // namespace mech3::replay
