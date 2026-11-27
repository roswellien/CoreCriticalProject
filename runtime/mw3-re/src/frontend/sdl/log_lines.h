#pragma once
// Ours (#521): how RunLog (run_log.h) turns what mw3 prints into log lines.
// Plain code with no files or threads, so it is built and tested on every
// system (tests/test_log_lines.cpp).
//
// Each whole line becomes "[<seconds since launch>] <level> <text>\n": the
// stream's default level (I for both in the game: run_log.cpp says why),
// unless the line starts with a level marker (log.h), which is taken off. The console gets the text with markers taken
// off and nothing added. Problem lines (W, E, and the header and health event
// lines the launcher reads) also go to the problems log, which stops at its
// cap with one line saying more was dropped.
#include <cstddef>
#include <cstdio>
#include <string>

#include "frontend/sdl/log.h"

namespace sdlfe {

struct LogOutput {
  std::string console;   // for the console, as printed, markers off
  std::string log;       // stamped lines for mw3.log
  std::string problems;  // stamped problem lines for mw3-problems.log
};

class LineStamper {
 public:
  // `default_level`: the level of a line without a marker.
  explicit LineStamper(char default_level) : default_level_(default_level) {}

  // Takes `n` bytes read at `seconds` since launch; adds what they finish to `out`.
  void feed(const char* data, std::size_t n, double seconds, LogOutput& out) {
    for (std::size_t i = 0; i < n; ++i) {
      const char c = data[i];
      if (line_.empty() && pending_marker_) {
        pending_marker_ = false;
        if (c == 'I' || c == 'W' || c == 'E') {
          level_ = c;
          continue;
        }
        line_.push_back(log::kMarker);  // not a level after all: kept as printed
      }
      if (c == log::kMarker) {
        // A marker mid-line: another print began before this one's newline. The part so far ends here
        // as a line of its own, so the marked line keeps its level.
        if (!line_.empty() || level_ != 0) finish(seconds, out);
        pending_marker_ = true;
        continue;
      }
      if (c == '\n') {
        finish(seconds, out);
        continue;
      }
      line_.push_back(c);
      // A line that never ends (a progress line redrawn with \r) is written in parts, not held forever;
      // a UTF-8 character cut by the part's end goes on to the next part whole.
      if (line_.size() >= kMaxLine) {
        const std::size_t keep = incomplete_utf8_tail(line_);
        const std::string carried = line_.substr(line_.size() - keep);
        line_.resize(line_.size() - keep);
        const char level = level_;
        finish(seconds, out);
        line_ = carried;
        level_ = level;
      }
    }
  }

  // Ends a line left without its newline (the end of the stream, or a crash).
  void flush(double seconds, LogOutput& out) {
    if (!line_.empty() || level_ != 0) finish(seconds, out);
  }

  static constexpr std::size_t kMaxLine = 8192;

  // How many bytes at the end of `text` are the start of a UTF-8 character still missing its last bytes.
  static std::size_t incomplete_utf8_tail(const std::string& text) {
    std::size_t continuation = 0;
    while (continuation < 3 && continuation < text.size() &&
           (static_cast<unsigned char>(text[text.size() - 1 - continuation]) & 0xC0) == 0x80)
      ++continuation;
    if (continuation == text.size()) return 0;
    const unsigned char lead = static_cast<unsigned char>(text[text.size() - 1 - continuation]);
    const std::size_t length = lead >= 0xF0 ? 4 : lead >= 0xE0 ? 3 : lead >= 0xC0 ? 2 : 1;
    return continuation + 1 < length ? continuation + 1 : 0;
  }

 private:
  void finish(double seconds, LogOutput& out) {
    if (!line_.empty() && line_.back() == '\r') line_.pop_back();
    const char level = level_ ? level_ : default_level_;
    out.console += line_;
    out.console += '\n';
    char stamp[48];
    std::snprintf(stamp, sizeof stamp, "[%.3f] %c ", seconds < 0 ? 0.0 : seconds, level);
    std::string stamped = stamp + line_ + "\n";
    out.log += stamped;
    if (is_problem(level, line_)) out.problems += stamped;
    line_.clear();
    level_ = 0;
  }

  static bool is_problem(char level, const std::string& text) {
    // The first-frame line too: the launcher counts only problems stamped after it (GameProblemsLog.cs).
    return level == 'W' || level == 'E' || text.find("mw3: header ") != std::string::npos ||
           text.find("mw3: health event ") != std::string::npos ||
           text.find("mw3: first frame shown ") != std::string::npos;
  }

  char default_level_;
  char level_ = 0;  // the marker's level for the line being read, 0 for none
  bool pending_marker_ = false;
  std::string line_;
};

// mw3-problems.log stops growing at its cap: the last line written says more was dropped.
class ProblemsCap {
 public:
  explicit ProblemsCap(std::size_t cap_bytes) : cap_(cap_bytes) {}
  // The part of `lines` (whole lines) that may still be written.
  std::string take(const std::string& lines, double seconds) {
    if (full_ || lines.empty()) return {};
    std::string out;
    std::size_t start = 0;
    while (start < lines.size()) {
      std::size_t end = lines.find('\n', start);
      end = end == std::string::npos ? lines.size() : end + 1;
      const std::size_t len = end - start;
      // Room is kept for the closing note, so the file never passes the cap.
      if (written_ + len + kNoteRoom > cap_) {
        char note[96];
        std::snprintf(note, sizeof note, "[%.3f] W mw3: problems log full at %zu bytes; later problems are only in mw3.log\n",
                      seconds, cap_);
        out += note;
        full_ = true;
        break;
      }
      out.append(lines, start, len);
      written_ += len;
      start = end;
    }
    return out;
  }

  static constexpr std::size_t kNoteRoom = 128;  // the "problems log full" line is under 128 bytes

 private:
  std::size_t cap_;
  std::size_t written_ = 0;
  bool full_ = false;
};

}  // namespace sdlfe
