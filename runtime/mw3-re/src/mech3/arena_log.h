#pragma once

#include <cstdint>
#include <cstdio>
#include <string>
#include <vector>

#include <nlohmann-json/json.hpp>

#include "mech3/arena.h"

// Ours, not the exe's (#287, docs/arena.md): the arena match log, one JSON
// object a line. A "start" line (the setup, seed and frame time), "state"
// lines ten times a second of game time (every mech's pose, heat, parts,
// target and AI order), "shot", "hit" and "destroyed" lines as they happen,
// and an "end" line once the match is decided. Every line is flushed as it
// is written, so a run that stops early leaves a readable log with no end
// line, which the reader reports as incomplete. Ids are each mech's index in
// setup order (ArenaMech::id), never a handle, and times are game seconds
// from the first Core frame, so the same seed writes the same bytes.

namespace mech3::arena {

// Seconds between state lines.
constexpr float kLogStatePeriod = 0.1f;

// Called by the match (arena.cpp): the start line and the shot and hit hooks
// on, at the first Core frame; each frame's state lines when due and the
// destroyed lines of mechs that fell this frame; the end line and the hooks
// off once decided. `now` is game seconds from the first Core frame.
void log_match_start(const Setup& setup, const std::vector<ArenaMech>& mechs);
void log_match_frame(float now, const std::vector<ArenaMech>& mechs);
void log_match_end(const Result& result);
// The hooks off without an end line (a match cleared before it was decided).
void log_match_stop();

// One mech's state record, as the log writes it at `now`.
nlohmann::json mech_state_record(const ArenaMech& entry, const std::vector<ArenaMech>& mechs);

// A log read back: every line that parsed, in order, and whether it ends with
// an "end" line. Lines that do not parse are counted, not kept; fields the
// reader does not know are kept as they are in each record.
struct LogRead {
  bool opened = false;
  std::vector<nlohmann::json> records;
  int bad_lines = 0;
  bool complete = false;  // the last record is an "end"
};
LogRead read_arena_log(const std::string& path);

}  // namespace mech3::arena
