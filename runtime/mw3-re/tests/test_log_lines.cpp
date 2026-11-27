// Checks for the game's log lines (#521): splitting and stamping, the stderr
// default, level markers, the problems log and its cap, and MW3_LOG's repeat
// counts. The launcher reads these formats (GameProblemsLog.cs).
#include "frontend/sdl/log.h"
#include "frontend/sdl/log_lines.h"

#include <cstdio>
#include <regex>
#include <stdexcept>
#include <string>

namespace {
using namespace sdlfe;

void require(bool condition, const std::string& message) {
  if (!condition) throw std::runtime_error(message);
}

void splitting_and_stamping() {
  LineStamper out_stream('I');
  LogOutput out;
  out_stream.feed("mw3: one\nmw3: tw", 16, 1.5, out);
  require(out.log == "[1.500] I mw3: one\n", "a whole line is stamped, a partial one waits: " + out.log);
  out_stream.feed("o\r\n", 3, 2.25, out);
  require(out.log == "[1.500] I mw3: one\n[2.250] I mw3: two\n", "the rest finishes it, CR dropped: " + out.log);
  require(out.console == "mw3: one\nmw3: two\n", "the console gets the text unstamped");
  require(out.problems.empty(), "info lines are not problems");
  // The launcher's problems-line pattern.
  const std::regex launcher(R"(\[[0-9]{1,9}(\.[0-9]{1,6})?\] [WE] .+)");
  LineStamper err_stream('W');
  LogOutput err;
  err_stream.feed("mw3: cannot open x\n", 19, 12, err);
  require(err.log == "[12.000] W mw3: cannot open x\n", "a stream's default level applies: " + err.log);
  require(err.problems == err.log, "W lines go to the problems log");
  require(std::regex_match(err.problems.substr(0, err.problems.size() - 1), launcher), "the launcher reads it");
}

void markers() {
  LineStamper s('W');
  LogOutput out;
  const std::string text = std::string(1, log::kMarker) + "Imw3: fine\n" + log::kMarker + "Emw3: broken\n";
  // Fed a byte at a time: a marker split across reads still counts.
  for (char c : text) s.feed(&c, 1, 3, out);
  require(out.log == "[3.000] I mw3: fine\n[3.000] E mw3: broken\n", "markers set the level: " + out.log);
  require(out.console == "mw3: fine\nmw3: broken\n", "markers never reach the console");
  require(out.problems == "[3.000] E mw3: broken\n", "only the E line is a problem");
  LogOutput odd;
  const std::string not_level = std::string(1, log::kMarker) + "Xyz\n";
  LineStamper t('I');
  t.feed(not_level.data(), not_level.size(), 0, odd);
  require(odd.console == not_level, "a marker without a level is kept as printed");
  // A marked line that starts while another print's line is still open keeps its level.
  LineStamper mid('I');
  LogOutput split;
  const std::string interleaved = std::string("mw3: half") + log::kMarker + "Emw3: broken\n";
  mid.feed(interleaved.data(), interleaved.size(), 5, split);
  require(split.log == "[5.000] I mw3: half\n[5.000] E mw3: broken\n", "a mid-line marker starts a line: " + split.log);
  require(split.problems == "[5.000] E mw3: broken\n", "and its E reaches the problems log");
  // A line with no newline is written in parts at its cap, not held forever.
  LineStamper endless('I');
  LogOutput parts;
  const std::string progress(LineStamper::kMaxLine + 10, 'x');
  endless.feed(progress.data(), progress.size(), 6, parts);
  require(parts.console.size() == LineStamper::kMaxLine + 1, "the capped part goes out at once");
  // A UTF-8 character (here e-acute, 2 bytes) across the part's end goes on whole to the next part.
  LineStamper utf8('I');
  LogOutput cut;
  std::string long_line(LineStamper::kMaxLine - 1, 'y');
  long_line += "\xC3\xA9z\n";
  utf8.feed(long_line.data(), long_line.size(), 7, cut);
  require(cut.console == std::string(LineStamper::kMaxLine - 1, 'y') + "\n\xC3\xA9z\n",
          "a character cut by the part's end stays whole");
}

void header_and_events_are_problems() {
  LineStamper s('I');
  LogOutput out;
  const std::string text = "mw3: header gpu x\nmw3: health event hitch ms=250 t=45\nmw3: health t=60 frames=1\n";
  s.feed(text.data(), text.size(), 4, out);
  require(out.problems == "[4.000] I mw3: header gpu x\n[4.000] I mw3: health event hitch ms=250 t=45\n",
          "header and health event lines join the problems log: " + out.problems);
}

void flush_ends_a_partial_line() {
  LineStamper s('I');
  LogOutput out;
  s.feed("mw3: last words", 15, 9, out);
  s.flush(9.5, out);
  require(out.log == "[9.500] I mw3: last words\n", "the end of the stream keeps a partial line");
  LogOutput none;
  s.flush(10, none);
  require(none.log.empty(), "nothing left: nothing written");
}

void problems_cap() {
  const std::size_t limit = 200;
  ProblemsCap cap(limit);
  const std::string line = "[1.000] W mw3: twenty-four\n";  // 27 bytes; 2 fit beside the note's room
  std::string file = cap.take(line, 1);
  require(file == line, "under the cap: kept");
  file += cap.take(line, 2);
  require(file == line + line, "still room beside the note: kept");
  const std::string over = cap.take(line, 3);
  file += over;
  require(over.find("problems log full at 200 bytes") != std::string::npos && over.find("twenty") == std::string::npos,
          "over the cap: one line saying so: " + over);
  require(file.size() <= limit, "the file never passes the cap: " + std::to_string(file.size()));
  require(cap.take(line, 4).empty(), "after that, nothing");
}

void repeat_counts() {
  int printed = 0;
  for (uint64_t call = 1; call <= 1000; ++call) printed += log::prints(call);
  // 1..10, then 16, 32, 64, 128, 256, 512.
  require(printed == 16, "first 10, then powers of two: " + std::to_string(printed));
  static log::Site site{"src/frontend/core_critical/renderer/vk_scene.hpp", 42};
  for (int i = 0; i < 20; ++i) log::count(site);
  require(site.skipped == 9, "20 calls skip 9 (11-15, 17-20): " + std::to_string(site.skipped.load()));
  const auto lines = log::skipped_lines(false);
  bool found = false;
  for (const auto& l : lines) found = found || l == "vk_scene.hpp:42 9";
  require(found, "the site's skipped count is reported by file and line");
  for (const auto& l : log::skipped_lines(false)) require(l.rfind("vk_scene.hpp:42", 0) != 0, "reported once per rise");
  for (int i = 0; i < 5; ++i) log::count(site);
  const auto again = log::skipped_lines(false);
  found = false;
  for (const auto& l : again) found = found || l == "vk_scene.hpp:42 5";
  require(found, "only the new skips next time");
  found = false;
  for (const auto& l : log::skipped_lines(true)) found = found || l == "vk_scene.hpp:42 14";
  require(found, "the exit report gives the total");
  require(log::skipped_total() >= 14, "the health line's total");
}

}  // namespace

int main() {
  try {
    splitting_and_stamping();
    markers();
    header_and_events_are_problems();
    flush_ends_a_partial_line();
    problems_cap();
    repeat_counts();
    std::puts("Log line checks passed");
    return 0;
  } catch (const std::exception& error) {
    std::fprintf(stderr, "%s\n", error.what());
    return 1;
  }
}
