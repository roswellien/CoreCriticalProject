#pragma once
#include <memory>
#include <string>

#include "mech3/replay_log.h"

namespace znet {
class Hub;
}

// Ours (#289, docs/arena.md): mw3 --replay3d, an arena match log played back
// in the game's own world, as main needs it, in the order it needs it. Kept
// apart from ArenaRun so each run has one mode. Every failure is a message
// for stderr; nothing is set until open() succeeds, and the destructor
// clears whatever open() set.
namespace mech3::replay {

// The log's map, refused unless it is a multiplayer map "<world>mp<N>": a
// log can never start a campaign or Instant Action mission. "" when it may
// go on. Game-free; whether the map ships is read() with the files mounted.
std::string replay_map_refusal(const std::string& map);

class ReplayRun {
 public:
  ReplayRun();
  ReplayRun(const ReplayRun&) = delete;
  ReplayRun& operator=(const ReplayRun&) = delete;
  ~ReplayRun();

  // With the install mounted: the log read, its map checked and found in the
  // game files, and every chassis known.
  bool load_log(const std::string& path, std::string* message);
  bool check_game_files(std::string* message) const;
  bool read(const std::string& path, std::string* message);
  // Before the engine runs: the in-process session opened, with no bots,
  // and the host seated as a spectator.
  bool open(std::string* message);

  const ReplayLog& log() const { return log_; }
  const std::string& map() const { return log_.map(); }

 private:
  ReplayLog log_;
  std::unique_ptr<znet::Hub> hub_;  // outlives the engine: znet::shutdown() first
};

}  // namespace mech3::replay
