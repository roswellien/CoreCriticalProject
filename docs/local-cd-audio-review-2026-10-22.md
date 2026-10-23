# Local CD audio review (2026-10-22)

Scope: `runtime/audio/local_cd_audio.hpp`, reviewed against `runtime/audio/README.md`.
Areas covered: request synchronization, shutdown during playback, WaveOut buffer
lifetime, partial initialization failures, playback cursor accuracy, and completion
and abort notifications. The review also checked whether hardware failures reach
callers.

This was a review only. No production code was changed and the game was not launched.
No system audio setting was read or written. The acceptance count stays at 131/144.

## Method

- **Mock harness** (`mock_harness.cpp`). It includes the unmodified header and
  redirects these calls to a scripted fake driver: `waveOut*`, `SetEvent`,
  `WaitForMultipleObjects`, `IsWindow` and `PostMessageA`. It writes its own
  fixture: a canonical MW3CD1 manifest with a 2 s track 2 and a 1 s track 3. Each
  PCM sample encodes its timeline frame, so the first sample of a write shows where
  playback restarted. No audio device is opened.
- **Silent WaveOut probe** (`silent_probe.cpp`). It opens `WAVE_MAPPER` on this
  machine and plays only zero-valued PCM. It sets no volume or mixer level. It
  answers some driver-behavior questions for this machine's Windows 11 audio stack.
- **Source copies:** the shared side-session notes folder `local-cd-audio-review/`
  (not in the repo). Build each file with MSVC 18:
  `cl /std:c++20 /EHsc /I <repo>\runtime <file>.cpp winmm.lib user32.lib`.

Control checks in the harness pass. These cover range completion with
`MCI_NOTIFY_SUCCESSFUL` after the final buffer drains, mode STOP after completion,
`MCI_NOTIFY_ABORTED` on STOP, a cursor equal to the play base plus returned frames,
and a clean CLOSE. The normal paths behave as the README describes. The findings
below concern failure paths.

## Fix status (2026-10-23)

All four confirmed defects are fixed in `runtime/audio/local_cd_audio.hpp`. The
reproductions are kept as the regression test `tests/local_cd_audio_tests.cpp`. It is
registered for Windows only as the ctest `local_cd_audio_failures`, because the
provider uses WinMM. The finding text below is kept as found; this section records
what changed and how it was checked.

| Finding | Change | Test group |
| --- | --- | --- |
| F1 | When `close_output()` fails, MCI_CLOSE now calls `failed_play()`. Refilling stops, the pending notification gets FAILURE, any `MCI_WAIT` is released, and the fault blocks commands until STOP or a successful retried CLOSE. | `close` |
| F2 | The new `abandon_play()` runs on worker failure paths: it reads the device position, falls back to the returned-buffer lower bound (`keep_returned_position()`), then resets. The command-level `position()` failure path applies the lower bound too. | `cursor` (F2a: position readable, F2b: position also fails) |
| F3 | If `SetEvent` fails for Shutdown, `invoke()` wakes the worker with `QueueUserAPC`, and the worker wait is now alertable (`WaitForMultipleObjectsEx`). If both signals fail, the destructor prints an error and calls `std::abort()`. It does not join forever, and it does not detach a worker that would use freed state. | `shutdown` |
| F4 | `WAIT_FAILED` now stops any active range with FAILURE, releases `MCI_WAIT`, and sets `worker_fault_`, which STOP does not clear. The worker retries the wait every 50 ms (`SleepEx`, alertable) and keeps completing queued requests with `MCIERR_HARDWARE`. The stderr message prints once. | `wait` (F4a transient, F4b `MCI_WAIT`, F4c persistent) |

**Verification:**
- **Before the fix:** the test was built against an unmodified copy of the original
  header. Every reproduction group failed: F1 3 checks, F2 4 checks, F4a 4 checks,
  and F4b and F3 deadlocked and hit the test's watchdog. F4c was not reached in that
  run because F4b deadlocked first; the original harness had recorded about 420,000
  spins in 200 ms for it.
- **After the fix:** all groups pass, including the controls (completion,
  STOP-abort, cursor and clean CLOSE). The full suite passed 5 consecutive times.
  Under persistent wait failure the worker made 6–8 waits in 300 ms.
- **Builds:** MSVC 18 with `/W4 /WX /permissive-`, clang-cl 21.1.8 with `/W4 /WX`,
  and CMake Debug with `MW34_WARNINGS_AS_ERRORS=ON` plus ctest
  (`local_cd_audio_failures` passed). clang-format 21.1.8 reports no changes.

**Remaining limitations:**
- These are mocked tests. They show the provider's logic under injected failures.
  They do not show how a real driver behaves: whether `waveOutReset` really returns
  buffers before an unprepare failure, what a removed device returns, or whether
  `QueueUserAPC` can fail while `SetEvent` does. None of these fixes were exercised
  against real hardware or in the game.
- **F4 behavior change:** after any worker wait failure, the service stays faulted
  for its lifetime. Only CLOSE succeeds, and MCI_OPEN and the AUX volume calls report
  `MCIERR_HARDWARE` / `MMSYSERR_ERROR`. This was chosen because the wait handles are
  owned by the service, so a failure means corruption, not a recoverable device
  condition.
- **F3:** the path where both signals fail ends in `std::abort()`, which is not
  covered by an in-process test. The APC path relies on `std::thread::native_handle()`
  being a Win32 `HANDLE`. That holds for the MSVC STL used by both MSVC and clang-cl,
  but not for a MinGW/winpthreads build.
- **F2:** when the position query fails, the cursor falls back to returned buffers.
  It can then trail actual playback by up to the queued audio, which is 40 ms.
- **Staged hosts:** existing native host builds keep the old header until they are
  rebuilt. `tools/remaster-launcher/native-overrides/source-sha256.json` still
  records the hashes of an older audio header publication, which already did not
  match HEAD before this change. No script reads it, and it was left unchanged.
- **Open questions:** Q1–Q7 below are unchanged and still unverified; none was
  addressed by these fixes.

## Confirmed defects

Each finding below was reproduced with the mock harness. Line numbers refer to the
reviewed revision (`7f77bdb`), before the fixes.

### F1. A failed MCI_CLOSE restarts playback (medium)

- **Location:** `close_output()` lines 356–367 and `MCI_CLOSE` lines 696–699, together
  with the worker refill at lines 757–758.
- **Trigger:** MCI_CLOSE during PLAY. `waveOutReset` succeeds, then
  `waveOutUnprepareHeader` fails on the first slot.
- **Consequence:** `reset()` has already cleared every slot's `queued` flag, but
  `mode_` stays `MCI_MODE_PLAY` and `opened_` stays true. The caller correctly gets
  `MCIERR_HARDWARE`. The worker loop then calls `fill()` on the still-prepared slots.
  Harness result: 4 new `waveOutWrite` calls after the failed CLOSE, and STATUS MODE
  still returns PLAY (526). Audio resumes from the cursor after the game asked to
  close. The pending play notification stays armed and later reports SUCCESSFUL, and
  an `MCI_WAIT` play stays blocked. A failed `waveOutClose` follows the same path, but
  there the slots are unprepared, so the refill fails with `WAVERR_UNPREPARED` and
  posts `MCI_NOTIFY_FAILURE` after the CLOSE.
- **Fix:** once `reset()` succeeds in `close_output()`, set `mode_ = MCI_MODE_STOP`
  before unpreparing, because playback has stopped by then. Alternatively, call
  `failed_play(e)` on the MCI_CLOSE error path so the pending notification and any
  `MCI_WAIT` are resolved and `fault_` blocks commands until a successful STOP or
  CLOSE.

### F2. A mid-playback WaveOut failure rewinds the cursor (medium)

- **Location:** worker refill failure at lines 757–762, `reset()` at line 346. The
  `position()` failure path at lines 575–577 behaves the same way.
- **Trigger:** `waveOutWrite` fails while the worker refills a returned slot, for
  example `MMSYSERR_NODRIVER` after the device is removed.
- **Consequence:** `cursor_` is only refreshed when a command arrives. The failure
  path calls `reset()`, which sets `submitted_ = completed_ = cursor_` and so
  discards `completed_`, which already reflects returned audio. Harness result: 100
  buffers (75 CD frames, 1 s) had played and been returned, yet after the FAILURE
  notification and STOP, STATUS POSITION reports 0. A following PLAY without FROM,
  the README's continuation path, restarts at timeline frame 0 instead of about
  frame 44100. The failure itself is reported correctly (FAILURE notification, then
  `MCIERR_HARDWARE` until STOP); only the position is wrong.
- **Fix:** before `reset()` on worker failure paths, call `reap()` and set
  `cursor_ = std::min(play_end_, std::max(cursor_, completed_))`. A best-effort
  `position()` first would be more accurate. The lower bound could also live in
  `reset()` itself, since every caller that sets an explicit cursor afterwards
  overwrites it.

### F3. The destructor deadlocks if `SetEvent` fails (low)

- **Location:** `invoke()` lines 231–233 and `~LocalCdAudio()` lines 810–811.
- **Trigger:** `SetEvent(control_)` fails while the Shutdown request is queued.
- **Consequence:** `invoke()` pops the Shutdown request and returns
  `MCIERR_HARDWARE`. The destructor ignores that result and calls `worker_.join()`,
  but the worker never received Shutdown. Harness result: the destructor had not
  returned after 2 s. `~Host()` resets `local_cd` first, so process teardown hangs.
  The failure is very unlikely with a valid handle, but the hang is unconditional
  once it happens.
- **Fix:** check the result of `invoke()` in the destructor. On failure, log it,
  then retry or `detach()` the worker and deliberately leak it, as the existing
  "retaining its live buffers" path does. Do not join a worker that was never told
  to stop.

### F4. A worker wait failure leaves inconsistent state and can spin (low)

- **Location:** lines 718–722, with STOP clearing `fault_` at line 690.
- **Trigger:** `WaitForMultipleObjects` returns `WAIT_FAILED`.
- **Consequences:**
  - **Transient failure:** `fault_ = MCIERR_HARDWARE` is set, but playback is not
    stopped, no FAILURE notification is posted and any `MCI_WAIT` stays pending.
    Harness result: 8 more buffers were written and played while STATUS MODE
    returned `MCIERR_HARDWARE` (262). The game sees errors while the music keeps
    playing.
  - **Persistent failure:** the loop retries immediately. Harness result: about
    420,000 iterations in 200 ms, each printing to stderr. STOP then clears `fault_`
    and later commands succeed, so a broken worker loop looks healthy.
- **Fix:** treat `WAIT_FAILED` as a play failure (`reset()` + `failed_play()`). Keep
  a worker-level fault that STOP does not clear, or exit the loop after a bounded
  number of retries with a back-off. Rate-limit the stderr message.

## Hardware or contract dependent questions

None of these were reproduced as defects.

### Q1. Does pause survive `waveOutReset` on other drivers?

- **Location:** lines 620–627, 674–678 and 686–689.
- **Path:** PAUSE, then PLAY FROM, SEEK or STOP followed by PLAY. Each takes the
  `reset()` + `fill()` path and never calls `waveOutRestart`.
- **Risk:** if a driver keeps the device paused across a reset, playback is silent,
  STATUS MODE reports PLAY, the notification never fires and `MCI_WAIT` blocks
  forever.
- **Silent probe on this machine:** the reset cleared the pause. A buffer queued
  after reset-while-paused completed without a restart. The Windows 11 stack is fine.
- **Still unverified:** other WinMM implementations, such as Wine/Proton or legacy
  drivers.
- **Fix:** call `waveOutRestart` after `reset()` whenever a range starts. It is a
  no-op when the device is not paused.

### Q2. Can the cursor run past submitted data during starvation?

- **Location:** line 335. The cursor is bounded by `play_end_` but not by
  `submitted_`.
- **Probe:** after 700 ms of starvation, the position stayed exactly at the 4410
  submitted frames, so there is no overrun on this machine.
- **Fix:** if other stacks keep advancing their clock, also clamp with
  `std::min(submitted_, …)`.

### Q3. Is shortening `dwBufferLength` after prepare safe?

- **Location:** line 446. The final partial buffer shortens the header length after
  `waveOutPrepareHeader`, and a later unprepare sees the short length.
- **Probe:** a short write played 441 frames, and unpreparing the shortened header
  returned 0. It works on this machine. WAVEHDR documentation expects the length to
  be set before prepare, so other drivers are unverified.

### Q4. Is 40 ms of queued audio enough?

- **Location:** line 38: 4 × 441 frames.
- **Risk:** any worker stall longer than about 40 ms underruns: a slow `fflush` in
  `trace()` with `MW34_MUSIC_LOG` set, scheduler contention while the recompiled
  game holds the CPU, or a WASAPI emulation period near 10–20 ms. The cursor stays
  correct because it is position-based, but music gaps would be audible.
- **Status:** not measured. It needs a live listening or timing check, which was out
  of scope.

### Q5. What happens to requests during or after Shutdown?

- **Location:** lines 729–756 and 806–811.
- **Behavior:** requests in the same batch after Shutdown still execute after
  `exit = true`. A racing MCI_OPEN would reopen the device and leave it open,
  reported through the "failed driver cleanup" message. Requests that `invoke()`
  queues after the worker exits wait forever, because `enabled_` stays true.
- **Status:** the header documents that callers stop first. `~Host()` destroys the
  service before the rest of host teardown, so this is only a defect if a guest or
  host thread can still call `music()` at that point.
- **Hardening:** set a `stopping_` flag under `queue_mutex_` in the destructor. Have
  `invoke()` return `MCIERR_DEVICE_NOT_READY` once it is set, and have the worker
  complete any remaining batch entries with an error.

### Q6. Does PAUSE or RESUME match MCICDA notification semantics?

- **Location:** line 652 (PAUSE keeps the pending play notification) and line 663
  (RESUME with `MCI_NOTIFY` supersedes it and becomes the range-completion
  notification).
- **Question:** whether the original game depends on Windows MCICDA's exact
  PAUSE/RESUME notification behavior. Confirm with an original-game trace before
  changing anything.

### Q7. What should an interrupted `MCI_WAIT` play return?

- **Location:** lines 679, 691 and 700. STOP, SEEK or CLOSE completes a blocked
  `MCI_WAIT` PLAY with `MCIERR_DEVICE_NOT_READY`.
- **Question:** real MCI may return 0 here. The guest-visible result matters only if
  the game issues `MCI_WAIT` plays from one thread and STOP from another.

## Checked without findings

- **Request handoff:** the queue and the manual-reset event are serialized under one
  mutex, so no wakeup is lost. Each request completes under its own lock, and the
  `shared_ptr` keeps a waiter's request alive across worker completion. `send()`
  reads `r->answer` only after a successful `invoke()`.
- **Buffer lifetime:** buffers are freed only after a successful `waveOutClose`, and
  they are leaked on failure. Unprepare skips headers that were never prepared.
  Failures during `open_output()` close only what was created. No `WAVEHDR` is freed
  while the driver could still own it.
- **Constructor failures:** load, log, event and thread failures each release what
  was already created and throw. No worker starts with bad data.
- **Notification ordering:** a new range aborts the old notification, and the same
  range supersedes it. STOP, SEEK, CLOSE and Shutdown abort it. A play failure posts
  FAILURE. A failed `PostMessageA` sets a visible `MCIERR_NO_WINDOW`.
- **Hardware errors:** every waveOut call except those in the paths above returns
  `MCIERR_HARDWARE` to the caller. No path invents success for a failed device call.
- **PCM gain:** the worst case, -32768 × 65535, fits in `int32_t`. The AUX
  left/right words follow `auxSetVolume`.
