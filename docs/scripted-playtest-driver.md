# Scripted playtest driver investigation

Issue [#55](https://github.com/roswellien/MW3Recomp-Private/issues/55), investigated
October 29, 2026 against `develop` commit
`630e487`. This is a source review, not a new game run or a reproduction of the
reported menu-transition crash.

The native host already drives scripted keyboard/mouse input, schedules frame
captures and writes execution logs. The useful next step is a small coordinator
around those facilities: validate one scenario, launch an identified native
runtime, collect its checkpoints, and fail when the scenario does not complete.
Building another graphics replay system would not cover live menu/mission
transitions. No runtime execution boundary changes in this investigation.

## Existing facilities

The maintained implementation is
[`tools/m4-crt-heap-carry/host/`](../tools/m4-crt-heap-carry/host/), as described in
[the host build guide](../tools/m4-crt-heap-carry/HOST_BUILD.md). The older files
beside that directory and `native-overrides/` are historical inputs; changing
them alone does not change the maintained host.

| Need | Existing implementation | Limit for an unattended playtest |
| --- | --- | --- |
| Launch native gameplay | [`play_native.ps1`](../tools/remaster-launcher/play_native.ps1) selects the profile's native executable, rejects an existing game session, creates a fresh run directory and redirects stdout/stderr | Requires a prepared local profile/runtime and original installation; waits indefinitely without a separate watchdog |
| Drive the player | [`main_v2.inc`](../tools/m4-crt-heap-carry/host/main_v2.inc) parses `MW34_INPUT_SCRIPT`; [`mfc_stage.hpp`](../tools/m4-crt-heap-carry/host/mfc_stage.hpp) implements `script_due`, immediate and buffered DirectInput reads | Frame/time scheduling, not named screen readiness or mission assertions; no scripted joystick path |
| Save periodic images | [`vdd.inc`](../tools/m4-crt-heap-carry/host/vdd.inc), `present` / `dump_frame`, uses `MW34_FRAME_DUMP` | Guest-sized RGB565 PPMs, not necessarily the final enhanced display; no named checkpoint receipt |
| Save selected full-resolution images | `vdd.inc` uses `MW34_HIRES_DUMP_FRAMES` and `MW34_HIRES_DUMP_DIR`; [`vk_scene.hpp`](../tools/m4-crt-heap-carry/host/vk_scene.hpp), `dump_fullres`, writes PPM | Runs only on the direct GPU presentation branch; a requested menu frame can produce no file |
| F9 PNG capture | [`photo_replay_stage.inc`](../tools/m4-crt-heap-carry/host/photo_replay_stage.inc) calls `capture_fullres_bgra` and the PNG encoder | F9 is detected through host `GetAsyncKeyState`, not the scripted DirectInput stream |
| Record progress and outcome | `MW34_FRAME_TIMES`, `MW34_DRAW_LOG`, native stdout/stderr and the launcher's `run.json` | Frame/draw counts do not prove which menu or mission was reached; a draw hash is not a complete pixel/state comparison |
| Observe crashes and window health | [`game-monitor`](../tools/game-monitor/README.md) records process exits, optional debug exceptions, logs and OS window responsiveness | Its CLI admits the original MW3 executable hash, not a newly built native host; collection success is separate from target success |
| Compare saved graphics | [`graphics-trace`](../tools/graphics-trace/README.md), `package_replay.py`, `compare_replay.py` and `compare_capture_scenes.py` | Original-process diagnostics and offline comparisons do not execute native game transitions |
| Display a replay | [`Launch Vulkan Replay.cmd`](../launchers/Launch%20Vulkan%20Replay.cmd) invokes [`vulkan-windowed/run.ps1`](../tools/vulkan-windowed/run.ps1) | Opens a captured scene in the viewer, not the native game; its optional auto-close is a viewer timer |

## Input and clock contract

The existing input grammar is:

```text
# Frame number, relative mouse movement, button mask
40 mouse -35 19 0
68 mouse 0 0 1
72 mouse 0 0 0
# Keyboard scan codes are hexadecimal; press and release are separate events
110 key 01 down
112 key 01 up
# Milliseconds since the first 3D scene, NOT since process launch
+1000 key 11 down
+1500 key 11 up
```

This illustrates syntax only; it is not a validated MW3 navigation scenario.
All frame events must precede timed events, and each group must be ascending.
Mouse deltas accumulate until the device is read; the last button mask remains
held. Keyboard state remains held until a corresponding release. The cursor is
virtual during scripted input, so this does not move the desktop mouse.

`script_due` compares frame events with completed presentations. Timed events
use `scene_t0`, set when `render_scene` first processes a scene containing draws in
[`d3d_provider.inc`](../tools/m4-crt-heap-carry/host/d3d_provider.inc). A 3D preview
can establish that origin before a mission; entering another mission does not
establish a new scenario clock. Do not interpret `+MS` as mission elapsed time.

`play_native.ps1 -Script` sets `MW34_VIRTUAL_CLOCK=50`. The host permits a
1–1000 ms step only with a script; time advances at presentation, on time queries
and on guest sleeps. This is useful for repeatable comparisons, but it changes
timing and cannot validate real-time performance or exclude timing-sensitive
crashes. Keep separate real-clock runs for those questions.

The [historical host notes](../tools/m4-crt-heap-carry/README.md) record repeated
Training and Instant Action frame comparisons. They are previous observations,
not fresh validation of this checkout. The committed
[Pirate's Moon menu/options/quit script](../tools/pirates-moon/input-menu-options-quit.txt)
is a reusable grammar example, not an MW3 mission fixture. No maintained MW3
scenario with explicit completion/checkpoint requirements was identified in
the reviewed launch, host and trace entry points.

## Captures and failure detection need explicit contracts

`MW34_FRAME_DUMP=N` saves frame 1 and every Nth presentation when N is nonzero.
On a flip that needs a dump, `vdd.inc` disables direct presentation and synchronizes
the surface to CPU memory. The resulting `frames/frame-<number>.ppm` covers the
guest surface; it does not certify high-resolution menus or postprocessing.

For the direct GPU path, `MW34_HIRES_DUMP_FRAMES=300,600` with an existing
`MW34_HIRES_DUMP_DIR` writes `target-300.ppm` and `target-600.ppm` only if those
frames actually take that path. A periodic guest dump on the same flip disables
that path, so combining both schedules can suppress the full-resolution capture.
`dump_fullres` also returns silently when opening the output file fails. The
coordinator must verify every requested file, its dimensions and complete pixel
payload; an absent or truncated image must fail the run.

The [October 19 readback repair](archive/screenshot-readback-fix-2026-10-19.md)
fixes RGB565/RGBA8 conversion into BGRA8 for PNG/video consumers. It supplies a
correct conversion primitive, not a scheduled screenshot API. Scripted F9 does
not trigger physical-key polling. A future unified checkpoint capture should
call the existing capture/encoding functions at a defined presentation boundary,
including the menu path, and report write failure. It should not synthesize
desktop hotkeys or reintroduce the private key-injection experiment.

Other distinctions needed for a trustworthy result:

- `MW34_FRAME_BUDGET` deliberately stops the host with
  `unresolved_translation` and the text `Presentation frame budget reached`.
  This is a bounded diagnostic stop, not normal shutdown. A crash or unrelated
  unsupported service must never be accepted merely because the exit is nonzero.
- [`monitor.py`](../tools/game-monitor/monitor.py) returns failure for a collector
  error; a collected nonzero target exit is an event and can accompany collector
  exit zero. Its duration/stop operation detaches and leaves the target alive.
  Do not use that return code or timeout as the scenario verdict or cleanup.
- Frame timing is flushed per presentation, while the draw log is buffered.
  A crash can lose the draw-log tail. Preserve stdout/stderr and the last flushed
  progress record; log silence alone is not proof of a hang.
- [`compare_replay.py`](../tools/graphics-trace/compare_replay.py) produces pixel
  error measurements and a difference image. It has no mismatch failure threshold.
  [`compare_capture_scenes.py`](../tools/graphics-trace/compare_capture_scenes.py)
  reports capture diversity, not semantic gameplay success. Neither CLI's exit
  zero is a regression verdict. Use explicit, reviewed expectations; do not
  silently resize images or tune tolerances until a candidate passes.

## First implementation scope

Start in **area: runtime**, with **area: renderer** for capture completion and
**area: ci** only when adding fixture execution. Keep the first scenario bounded:
main menu -> Options -> main menu, repeated several times -> normal Quit.
Then add Training start -> a short input sequence -> return to menu -> re-enter
Training -> normal Quit, using a locally established route for that game build.
The latter addresses the reported transition crash; this investigation neither
reproduces nor fixes it.

The first driver should meet these requirements:

1. Accept an explicit prepared native runtime/profile, scenario input file,
   checkpoint schedule and wall-clock deadline. Reject malformed, out-of-order
   or out-of-range events before launch; the current host parser skips some
   malformed lines and is not a strict scenario validator. Retain the existing
   game admission and host-initialized loader path with no fallback.
2. Use a fresh ignored output directory, an isolated writable game profile and
   registry overlay (`MW34_REG_OVERLAY`), and a controlled child environment.
   Record the source SHA, executable/translated-module hashes, input-script hash,
   settings, clock mode and asset identities. Do not reuse the player's writable
   saves or silently inherit unrelated capture/timing overrides.
3. Reuse `MW34_INPUT_SCRIPT` for player actions and periodic guest PPMs for the
   initial baseline. Label those images by capture surface. Use a narrowly scoped
   host change when final-display menu/mission checkpoints are required; missing
   captures must fail, not be substituted with the previous frame.
4. Capture stdout/stderr, frame timing, actual target exit and all required
   images. A pass requires each declared checkpoint, demonstrated screen/mission
   expectations and the declared shutdown outcome. A frame counter or zero exit
   alone is insufficient. Distinguish unexpected exit, deadline, missing output,
   comparison failure and deliberate budget stop in a small run summary.
5. Own the launched process identity through its lifetime. On deadline or
   cancellation, preserve diagnostics and clean up only that run's processes.
   Reject concurrent game runs, do not kill by executable name, and leave the
   existing composer, watcher and graphics/asset jobs untouched.
6. Run the same local scenario twice with a frozen profile to establish its
   baseline. Validate checkpoint identity before adopting pixel/hash expectations.
   Repeat the transition scenario on a real clock; a virtual-clock pass alone
   does not establish that the reported crash is absent.

This adds the missing scenario-completion criterion around existing runtime
facilities. It does not need another startup verifier, interpreter, replay
engine or broad monitoring framework. Passive native-host observation can be
added by extending the monitor's admission/identity contract explicitly; do not
weaken its original-game hash check to make arbitrary executables pass.

## CI and local validation

CI must require no game installation, original captures or translated module.
Reuse [`tests/test_game_monitor.py`](../tests/test_game_monitor.py) and its
authored Windows probe for collector behavior. Portable cases run without that
probe; Windows integration cases skip unless it has been built. Those tests
already distinguish a captured crash from collector failure and check that
detachment leaves the target alive. They do not drive a native game scenario.

For the new coordinator, an authored child process should really emit progress,
write a tiny authored image, and exit, crash or stall as selected. Exercise the
driver's actual launch/collection/deadline path against it, including incomplete
images, missing checkpoints, nonzero exit, timeout cleanup and output-directory
reuse. Mark fixture results as fixture execution, never live native gameplay.
Use the existing [capture-pixel fixture](../tools/remaster-launcher/test_capture_pixels.cpp)
for conversion coverage; if extending it for canonical host capture, ensure it
tests the maintained implementation rather than only the historical header.
Follow [the test contribution rules](../CONTRIBUTING.md#tests), including showing
that changed checks fail when their covered behavior is broken.

Real menu/Training runs remain opt-in and local, with original data and generated
code outside Git. Keep screenshots, traces, saves and logs under ignored local
outputs. PRs can state the source/build identities, scenario, checkpoints reached,
exit outcome and known limits; review/redact any evidence before sharing it under
[the distribution policy](legal.md). CI fixture success is not real-installation
compatibility or release validation.

This investigation changes documentation only. It adds no scenario runner,
new CI job, release artifact, gameplay fidelity claim or crash fix. Implementing
and validating the two scenarios above remains follow-up work.
