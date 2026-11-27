#pragma once
// mw3.log (ours, not original code; docs/program.md, The log): everything mw3
// prints, on stdout and stderr, copied to <write dir>/mw3.log, made new each
// start; the last start's is kept as mw3.old.log, so a crash's log survives
// the restart a player makes before reporting it. Each line is stamped with
// seconds since launch and a level (log_lines.h), and problem lines are also
// written to mw3-problems.log (#521). With no console (the launcher's runs on
// Windows) the files are the only output; with one, the console keeps every
// line as printed.
#include <memory>
#include <string>

namespace sdlfe {

class RunLog {
 public:
  RunLog();
  // <name>.log in `dir` (the last start's kept as <name>.old.log), and with
  // `problems` also <name>-problems.log; false (and no log) when it cannot be made.
  bool open(const std::string& dir, const std::string& name = "mw3", bool problems = true);
  ~RunLog();  // the last lines written, the console's own handles back
  const std::string& path() const { return path_; }

  struct Impl;  // run_log.cpp; named here for run_log_drain

 private:
  std::unique_ptr<Impl> impl_;
  std::string path_;
};

// For the crash handler (crash_report.cpp): waits up
// to `max_ms` for the open log to take in what is in its pipes, then writes out
// any line still missing its newline. Nothing happens without an open log.
void run_log_drain(unsigned max_ms);

}  // namespace sdlfe
