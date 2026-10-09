# Live game diagnostics

A local Windows collector for the admitted MW3 1.2 executable. Default file
polling is **20 ms**, process/window-health sampling is **1 second**, status
snapshots refresh every **200 ms**, and watch refreshes every **100 ms**.
Records have UTC timestamps, monotonic
elapsed time, sequence cursors and a session identity. No external service,
administrator privileges, package installation or game binary modification is
needed. The current game is closed; implementing this tool does not relaunch it.

## Start a monitored session

For the helper replacement with monitoring, double-click
`Launch MW3 with Hook.cmd` in the project root. It builds and self-tests the
replacement, creates a fresh evidence directory, then starts hook mode below.
The double-click launcher defaults to **passive monitoring**: helper events,
game files, process/window health and exit codes remain available, while Windows
exception/debug-message capture is disabled. The first real monitored launch
exited at the menu with `STATUS_INVALID_HANDLE` after debugger attachment and
before any actual helper calls. Debug attachment can change invalid `CloseHandle`
behavior ([Microsoft documentation](https://learn.microsoft.com/en-us/windows/win32/api/handleapi/nf-handleapi-closehandle)).
Use `Launch MW3 with Hook.cmd --debug` only for a controlled debugger experiment.
The passive retry reached the main menu, confirmed by the user, and was then
closed by the user with exit code 0. It still has zero actual `game_call` records;
Training or mission loading remains the next helper-validation step.
Close any ordinary MW3 session first. The raw launcher executable requires
arguments and should not be double-clicked directly.
The double-click wrapper uses the installed Python runtime directly, so it
does not depend on Windows PowerShell allowing `.ps1` files. It waits for a
monitor status handshake and records the exact collector/session/log paths.
`Launch MW3 with Hook.cmd --prepare-only` tests preparation without starting MW3.

From the repository root:

```powershell
# Start a baseline game plus a hidden collector; print the session directory.
./tools/game-monitor/start.ps1

# Passive monitoring without debugger exception/debug-message capture.
./tools/game-monitor/start.ps1 -Passive

# Observe an already-running game without injecting or attaching a debugger.
./tools/game-monitor/start.ps1 -Mode attach -GamePid <PID>

# Opt in to Windows debug-event capture for an existing session.
./tools/game-monitor/start.ps1 -Mode attach -GamePid <PID> -DebugAttach
```

The baseline default uses Windows debugging APIs to capture `OutputDebugStringA/W`,
module loads, exception addresses/codes/chance, and exits. Only the initial loader
breakpoint is handled by the collector. Application exceptions are returned to
the original handlers with `DBG_EXCEPTION_NOT_HANDLED`; first-chance exceptions
can be handled successfully and are not proof of a crash. Second-chance
exceptions are critical alerts. Debug events briefly suspend the target, so use
passive mode when comparing timing/performance. Debugger monitoring and the
hook launcher's temporary startup debugger cannot both attach to one process.
The first observed first-chance WOW64 breakpoint is recorded as informational
and forwarded unchanged; subsequent ones and all second-chance exceptions remain
visible alerts. This keeps ordinary 32-bit startup from looking like a game error.

For the authored replacement, prepare its normal build/self-test run **without**
`-Launch`, then use the printed fresh run directory:

```powershell
./tools/in-game-hook/build.ps1
./tools/game-monitor/start.ps1 -Mode hook -HookRun reports/mw3-in-game/<run>
```

Hook mode captures `game.jsonl`, launcher output, game logs, exits and process
health. It validates the game/DLL/launcher build hashes and binds the PID from
the fresh `installed` event to the expected executable. After the hook launcher
finishes and releases its startup debugger, the collector attaches its own
debugger for subsequent messages and exceptions. Events before that late
attachment can be unavailable. Use `-Passive` to retain only passive signals.
An already attached debugger produces a visible collector error. The separate
[helper verifier](../in-game-hook/README.md) still decides whether real helper
calls passed; a logging session alone is not in-game function proof.

`start.ps1` refuses a duplicate running game. The underlying CLI can also run
in the foreground with `monitor.py launch` or `monitor.py attach --pid <PID>`.
`launch --no-debug`, `--poll-ms`, `--duration` and repeatable `--log <path>` allow
controlled diagnostic sessions. A duration limit detaches the observer and
leaves the target alive. `--game` must match the admitted image's full hash.

## Read while the game runs

Replace `<session>` with the directory printed at startup:

```powershell
C:/Python314/python.exe tools/game-monitor/monitor.py status <session>
C:/Python314/python.exe tools/game-monitor/monitor.py read <session> --after 0 --limit 200
C:/Python314/python.exe tools/game-monitor/monitor.py watch <session> --after 0 --alerts-only --duration 30
```

The assistant can run the same commands directly and use `next_cursor` for the
next read/watch. The watch command streams new alerts as they arrive and returns
a cursor within 30 seconds by default (60 seconds maximum). No scheduled task
is needed. `status.json` holds current metrics, recent alerts, source capabilities
and collector state; the CLI flags an aged heartbeat. Status alone does not prove
that an unresponsive game is healthy or that a collector PID is still alive.

Add a manual marker to correlate an observed problem with the timeline:

```powershell
C:/Python314/python.exe tools/game-monitor/monitor.py mark <session> "Geometry distorted near cliff"
C:/Python314/python.exe tools/game-monitor/monitor.py stop <session>
```

Stopping the collector leaves the game running and detaches its debugger. It
does not close or terminate MW3. An unexpected collector exit is configured not
to kill the game. The explicit game-close request remains a separate action.

## Signals and limits

- Original `mech3.out`, extra explicitly selected logs, stdout/stderr and hook
  JSON events are classified and recorded. Malformed, oversized, truncated and
  replaced sources produce visible notices. Existing file history is skipped
  on attach; new hook runs are read from their beginning.
- Hook fatal/mismatch reports become critical alerts. Unknown plain messages
  use conservative keyword classification; retain the original text to review
  false positives. Nonzero exits are errors with their exact unsigned code, not
  automatically labeled crashes.
- Windows `IsHungAppWindow` records OS-reported message-pump unresponsiveness
  and recovery transitions. It does not measure FPS, GPU progress or simulation
  correctness. CPU idleness and log silence are never called hangs.
- Process samples include CPU time/usage, working set and private memory. The
  process handle and creation identity distinguish it from a later reused PID.
- Original game logs can be buffered internally. Receipt timestamps describe
  when the observer saw an event; polling cannot make unflushed messages visible.
  Debug messages and already-flushed hook events are the faster sources.
- Silent geometry glitches, incorrect physics, stutter and device problems that
  emit no signal require later renderer/simulation instrumentation. This tool
  does not claim to detect every possible issue or validate playable Training.

The collector writes only under ignored `reports/`. Timeline retention defaults
to eight 8 MiB segments (about 64 MiB), with explicit cursor gaps if old segments
are removed. The latest 50 alerts stay in the status snapshot. Source game logs
and raw `launcher-output.log` are separate files and are **not** capped by this
timeline policy. Logs may contain local paths/debug text; keep them private.
Status is replaced atomically and events are flushed by the observer. The tool
does not add disk flushes to the game; the existing helper verification probe
still has its own synchronous per-call logging overhead.

## Verification

Portable tests cover partial lines, stale history, rewrites/rotation, oversized
and malformed records, severity, retention gaps, cursor paging and admission.
Optional authored Win32 probes exercise real debug messages (including Unicode),
handled/unhandled exceptions, exit codes, hidden unresponsive windows and recovery,
live reader/marker/stop commands, and detachment with the target still alive.
These tests contain no game code and never launch MW3.

```powershell
& '<VS>/Common7/IDE/CommonExtensions/Microsoft/CMake/CMake/bin/cmake.exe' -S tools/game-monitor -B build/game-monitor -A Win32
& '<VS>/Common7/IDE/CommonExtensions/Microsoft/CMake/CMake/bin/cmake.exe' --build build/game-monitor --config Release
C:/Python314/python.exe -m unittest discover -s tests -p test_game_monitor.py -v
C:/Python314/python.exe -m unittest discover -s tests -p test_monitor_invalid_handle.py -v
```

With no probe build, Windows integration cases are explicitly skipped; the
portable tests still run in ordinary CTest/CI. Local evidence is in
`reports/monitor-tests/`. The initial 100 ms configuration measured 91 ms from an
authored debug emission to its receipt; the final 20 ms configuration measured
12 ms in the local probe. These are local results, not a latency
guarantee for buffered original-game messages.

Windows API semantics follow Microsoft's references for
[WaitForDebugEventEx](https://learn.microsoft.com/windows/win32/api/debugapi/nf-debugapi-waitfordebugeventex),
[ContinueDebugEvent](https://learn.microsoft.com/windows/win32/api/debugapi/nf-debugapi-continuedebugevent),
and [IsHungAppWindow](https://learn.microsoft.com/windows/win32/api/winuser/nf-winuser-ishungappwindow).
