# Handoff 2026-10-14: guest SEH dispatch in progress (plus HUD text and FDIV in place)

Historical handoff: the software C++ SEH blocker below was completed later on October 14. See [the daily summary](session-summary-2026-10-14-remaster.md) and [the E0 record](e0-application-execution-path.md) for current results and remaining limits.

Written for the next agent. Everything below is **uncommitted** working-tree state. Do not commit unless the user asks.

## Prompt for the next agent

> Continue MW34 RECOMP at D:\Projects\MW34Recomp. Read `CLAUDE.md`, `docs/faithful-modernization-plan.md`,
> `docs/m4-claude-work-review-2026-10-11.md`, `docs/claude-m4-continuation-handoff.md`,
> `docs/e0-application-execution-path.md` (2026-10-14 sections) and this file first.
>
> Current task: finish **guest SEH dispatch** (blocker 3 in the e0 doc) in `tools/m4-crt-heap-carry/mfc_stage.hpp`.
> - The handled C++ path is implemented and validated.
> - The unhandled path stops on a guest write fault inside MSVCRT `_NMSG_WRITE`/`strcpy` (details below). Diagnose it,
>   fix it without fake success, then validate, relink the play build, document, and report.
>
> Report: code changed, execution reached, validation, fidelity limits, accepted count (131/144) and the next blocker.

## Hard constraints (from the user and CLAUDE.md)

- **No desktop screenshots.** One accidentally captured the user's private windows. Use `MW34_HIRES_DUMP=<frame>` with `MW34_HIRES_DUMP_FILE=<ppm>`, or the replay's frame dumps.
- **MW3 is single-instance.** Check for `entry_commandline` processes first, and don't run game tests while the user plays.
- **Don't change the user's settings.** Leave `InGameVMode 7` in `MW3/mw34-registry.txt`, and the user's pilot file `MW3/pilots/JCB.mw3`, alone.
- **Strict acceptance stays paused** (the user chose this twice).
  - The composer (PID 44416) and watcher (40500) ended; their output closed 2026-10-12.
  - Strict chain v6-r1 failed on a changed pinned doc (`docs/m4-startup-plan.md`).
  - Do not restart it unless the user asks. Accepted count stays **131/144**; the receipt `reports/m4-joint-startup131-root/acceptance-r1/report.json` has SHA `aa9462f3…`, re-verified today.
- **Fidelity rules.**
  - No AFTER seeding, no fake API success, no interpreter or original-code fallback.
  - Unknown services stop typed.
  - Original media and generated code stay local.
  - Don't edit `runtime/memory/guest_memory.cpp`.
- **No downloads without asking.** pip installs count. Local tools exist; for example `local/tools/llvm-21.1.8/clang+llvm-21.1.8-x86_64-pc-windows-msvc/bin/llvm-objdump.exe` disassembles PE files.

## Build and test recipes

- **Test build** (host sources only, about 1-2 min): `powershell -NoProfile -Command "& tools/m4-crt-heap-carry/build.ps1 -Levels O2 -Inline reports/m4-crt-attach/merge-r7-entry -Suffix '-lazy'"` gives `build/m4-crt-heap-carry-O2-lazy`.
- **Play build** (what `Play-MW3.cmd` runs): the same command with `-Suffix '-merge'`.
- **Replay harness** (session scratchpad): `C:\Users\jcbla\AppData\Local\Temp\claude\D--Projects-MW34Recomp\7bd72425-977f-4b4b-ac0e-59916bc040ac\scratchpad\detrun.ps1`.
  - Parameters: `-Build O2-lazy|O2-merge -Visible -NoOverlay [-Dump 0] [-Frames N] [-Times ft-x.txt] [-Script input-ia-13.txt -Ref input-ia-13-v3] [-RegOverlay reg-overlay-mode7.txt]`.
  - It forces the exact CPU path (`MW34_LAZY_RT=0`, `MW34_GPU_HUD=0`, `MW34_WINDOW=integer`) unless those are set, and uses a frozen registry overlay.
  - Exit "Presentation frame budget reached" (exit=1) is the normal end.
- **Exactness checks.**
  - Training CPU path must give `same=116 diff=0` against `input-training-t8000-v3`.
  - GPU path, mode 7: set `MW34_LAZY_RT=1 MW34_GPU_HUD=1 MW34_WINDOW=fit MW34_DRAW_LOG=<file>`, run with `-RegOverlay reg-overlay-mode7.txt -Dump 0`, and compare columns 1-3 with scratchpad `play-text.txt` or `play-fdiv.txt` (1150 identical lines).
  - Instant Action against `input-ia-13-v3` now diverges at frame 80 **on every build**. The pilot file kills went from 9 to 10: replays write `MW3/pilots/JCB.mw3`, so the IA run is not sealed. Compare IA between builds instead. A task chip ("Make replay harness pilot-file hermetic") was offered to the user.
- **Timing:** Training is about 7.2 / 6.9 ms per frame (frames 300-700 / 700-1150) on the CPU path.

## Done this session (all validated)

1. **HUD text at output density** (`gpu_hud.inc`: text_record, text_render, text_blit; hook in `mfc_stage.hpp` DrawTextA).
   - `DrawTextA` calls between `0x577BA0` (clear) and `0x577BD0` (copy) are recorded, then redrawn with GDI at the render scale.
   - `lfWidth` is narrowed when the scaled text would overflow the width the game measured. This fixed the truncation ("TRAINING: Movem").
   - `MW34_HUD_TEXT=0` disables it; `MW34_HUD_TEXT_LOG=<file>` is a diagnostic.
   - Validation: 3D identical on 1150 frames at mode 7; CPU path 116/116. Cost: 7.66 against 7.51 ms per frame.
   - Documented as step 6 in `docs/hud-vulkan-integration-handoff.md`.
2. **FDIV initializer in place** (play path, `MW34_STARTUP=loader`).
   - `_cinit` calls `0x78004254` during the MSVCRT attach resume. The heap Stage yields (`hs::fdiv_inplace_hook`, `heap_stage.hpp`) to a one-call generic stage (`mf::Stage::Kind::call`; `fdiv_in_place` in `main_v2.inc`).
   - That stage runs 8 lifted bodies and 3 real services (GetModuleHandleA, GetProcAddress, IsProcessorFeaturePresent).
   - The pre-attach writer job is gone on the loader path; the accepted path is unchanged.
   - Validation: Training 116/116; GPU mode 7 1150/1150; IA identical to the old build. The play build (`O2-merge`) is relinked with this.
   - Documented in the e0 doc.
   - Backups: scratchpad `*.bak-fdiv`.

## In progress: guest SEH dispatch (test build `O2-lazy` only; play build NOT relinked with it)

The changes are in `tools/m4-crt-heap-carry/mfc_stage.hpp` and `win_bridge.inc`. Backups: scratchpad `mfc_stage.hpp.bak-seh` and `win_bridge.inc.bak-seh`.

- **`struct GuestReturn`** (before `struct Stage`): the lazy nonlocal-return design.
  - `returned()`: a RET to an *outer* bound return word `returns[j]`, with ESP 4-260 bytes above its slot, throws `GuestReturn(j)` and counts `host.nonlocal_returns`.
  - `enter()` (frame push) and `call_guest()` (sentinel frame) catch it for their own frame index, set `depth`, and continue. The abandoned host frames are released by C++ unwinding.
  - This handles both `__except` blocks (they restore ESP themselves) and C++ catch continuations, without knowing ESP at the jump.
- **Services** in `api()`, before the `IsProcessorFeaturePresent` service:
  - `RaiseException`:
    1. Builds the guest `EXCEPTION_RECORD` and x86 `CONTEXT` (offsets 0x9C-0xC8; ContextFlags 0x10007) below ESP, at `(e-0x380)&~15`.
    2. Walks FS:[0] (`runtime.fs_base().value`) and calls handlers via `call_guest(h,{rec,reg,ctx,dc},false,…)`. ContinueSearch moves on; ContinueExecution resumes only to its own return point.
    3. At the end of the chain it runs the top-level filter and stops typed with the exception code.
  - `RtlUnwind`: calls each handler with EXCEPTION_UNWINDING and unlinks it, then returns normally to `TargetIp`, which must equal its return address.
  - `UnhandledExceptionFilter`: calls the stored filter (`heap.unhandled_filter`, `0x7800B322`). For EXCEPTION_CONTINUE_SEARCH it logs the fault and returns EXECUTE_HANDLER.
  - Counters: `host.raises`, `host.unwinds` and `host.nonlocal_returns`, in `mf::Host`.
- **Return-site check:** the service return check in `api()` also accepts returns into MSVCRT code for GetProcAddress tokens. That came from the FDIV work.
- **Diagnostics** (they change behaviour; tests only):
  - `MW34_SEH_TEST=<n>`: the n-th game-code call inside a window procedure does exactly what MFC42 `AfxThrowUserException` (`0x5F463574`) does: lifted MSVCRT `_CxxThrowException` (`0x7800AC1A`) with `&p`, where `p = 0x5F4CE380` (MFC's static CUserException) and ThrowInfo `0x5F4B3310`.
  - `in_wndproc` is counted in `win_bridge.inc` around the window-procedure `call_guest`.
  - `MW34_SEH_TEST_ANY=1` counts every game call, which reaches the unhandled path.
  - `MW34_SEH_LOG=1` logs each raise and nonlocal return.
- **`MW34_TRACE_SERVICES` lines** now also print `a1`, `a2` and `esp`, a small debug addition. Keep it or revert it.

Lifted coverage confirmed in `mfc_entries.inc` (generic set):
- MSVCRT `_CxxThrowException`, `__CxxFrameHandler`, `_except_handler3`, `_global_unwind2`, `_local_unwind2`, `_XcptFilter`, `abort` and `_exit`;
- the filter `0x7800B322`;
- the game's CRT-entry scope handlers `0x5AC502`/`0x5AC517` and the other CRT `__finally` handlers.

The game has 4 `_except_handler3` frames (all CRT code near the entry) and 940 `__CxxFrameHandler` functions. Its import thunks are `0x5AC586` (`_except_handler3`) and `0x5AC100` (`__CxxFrameHandler`).

Validation so far:
- **No regression with the dispatcher idle:** Training CPU path 116/116; timing 7.23 / 6.93 against 7.18 / 6.94 ms (noise).
- **Handled path works** (`MW34_SEH_TEST=1`):
  - Game call `0x484170` inside the window procedure threw.
  - `RaiseException 0xE06D7363` was dispatched; `__CxxFrameHandler` found `AfxCallWndProc`'s CATCH_ALL.
  - `RtlUnwind` ran once, then the catch funclet and the continuation.
  - "nonlocal return to 0x5f401810: frame 8 of 16" followed, and the game kept running to the 400-frame budget.
- **Unhandled path: OPEN DEFECT** (`MW34_SEH_TEST=1 MW34_SEH_TEST_ANY=1`):
  - The first game call is `0x5AC5C0`, in the CRT entry prefix right after the entry's SEH frame is pushed.
  - The dispatch reaches the entry filter, then `_XcptFilter` → our `UnhandledExceptionFilter` → `0x7800B322` (`__CxxUnhandledExceptionFilter`) → `terminate` (TlsGetValue ×2) → `abort` → `_NMSG_WRITE` (`0x7800B901`; `GetModuleFileNameA` buffer `0x20001238`, ESP `0x20001224`, EBP about `0x200013DC`).
  - Then a guest write fault: `site=0x78002fab` (strcpy) `target=0x20002000` ("Guest write outside mapped guest memory").
  - `0x20002000` is the top of the loader-order guest stack: the stack is mapped from `0x1FF01000` (`mf::stack_extension`) to `0x20002000`, and the entry frame is at `0x20001900` (`frame` in `composition.cpp`), giving 0x700 bytes of headroom. The real process has a 1 MB stack.
  - The disassembled `_NMSG_WRITE` strcpy calls target `[ebp-0x1a4]` and `[ebp-0xa0]`, both far below the top. So the faulting strcpy probably comes from another frame, or EBP/ESP were not what the trace suggests. Not yet diagnosed.
  - Ideas: log guest ESP/EBP and the return-stack top when the flat fault handler fires; check whether `_except_handler3` already ran `_global_unwind2` or jumped to `0x5AC517` (`mov esp,[ebp-18h]`) before this; check whether the CONTEXT/record area at `e-0x380` collided with live frames.
  - If the unhandled path then reaches `MessageBoxA` ("Runtime Error! … abnormal program termination"), the existing typed stop "MessageBoxA would block on a modal dialog" is the expected faithful end.

## Next steps

1. Diagnose and fix the unhandled-path fault (above).
2. Rerun both diagnostics plus the regressions:
   - Training CPU path 116/116;
   - GPU mode 7 draw stream 1150/1150;
   - IA identical to the old build.
3. Relink the play build (`-Suffix '-merge'`) and re-check.
4. Update `docs/e0-application-execution-path.md`:
   - the TLS/FS/SEH table: unhandled filter and raise/unwind rows become "Executed (diagnostic trigger)";
   - blocker 3;
   - the design section, noting the lazy GuestReturn variant.
5. Update the memory file `C:\Users\jcbla\.claude\projects\D--Projects-MW34Recomp\memory\resume-2026-10-13-night.md`.
6. Still open:
   - hardware faults → guest SEH (they need a mid-block CONTEXT; separate design);
   - `longjmp`/`__CxxLongjmpUnwind` (not lifted).
7. Later queue:
   - sharper 3D textures from the hi-res texture masters, content-keyed like the HUD pack in `local/hires-pack/hud`;
   - new HUD features;
   - the parked difference of 4-7 extra particle quads in the original on frames 251-699 (tools/mw3-compare).
