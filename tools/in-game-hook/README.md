# One-function in-game experiment

This opt-in Win32 research tool replaces MW3's reviewed `sub_00409ED0` address
helper with authored C++ and a MASM ABI bridge. The original x86 game calls the
replacement. This is separate from the native x64 lifting milestone G2; it does
not use the generated Remill game IR or change gameplay intentionally.

Only the admitted U.S. 1.2 image is supported: SHA-256
`95bc2c114c9b2e5c5ada8e40ca78cc79470f862e45313ffad0d1e8e6d4d916bf`.
See the [reviewed helper contract](../../games/mw3/docs/first-function.md).

## Run locally

For a single launcher that enables both the replacement and live diagnostics,
double-click `Launch MW3 with Hook.cmd` in the project root, or run
`./tools/in-game-hook/build.ps1 -MonitoredLaunch`. Close any ordinary MW3 session
first. The raw `mw34_hook_launcher.exe` requires arguments; use these wrappers
for a fresh, hash-bound run with the correct files and log paths.

Close any existing MW3 session before launching this experiment. From the project
root, with Visual Studio's x86 C++ and MASM tools installed:

```powershell
./tools/in-game-hook/build.ps1 -Launch
```

This builds separate Win32 Release targets and creates a fresh ignored run
directory under `reports/mw3-in-game/`. A build record binds source, launcher,
hook DLL and game identities. Enter Training and play briefly. To check that
the game actually called the replacement, use the directory printed by the build:

```powershell
C:/Python314/python.exe tools/in-game-hook/verify_trace.py reports/mw3-in-game/<run>
```

The verifier independently checks the recorded arithmetic and refuses an
installation-only or self-test-only run. Its successful output still needs a
separate observation that Training loaded and remained playable.

## Installation and rollback

The launcher admits the complete game image before creating its own process.
It places a temporary breakpoint at the admitted executable's entry point,
restores that byte, and detaches its debugger while holding the main thread.
The normal loader has completed before an initialization thread loads our DLL.
The DLL checks the loaded helper digest and runs its tests before writing a
seven-byte jump over two complete instructions. Only then does the launcher
resume the original game's main thread. DLL initialization performs no work in
`DllMain`, and no hook is installed while the Windows loader lock is held.

The installed `Mech3.exe` is never patched on disk. Exiting this process removes
the hook. Launching the ordinary executable next time uses the original helper.
Use a new log path for each run; existing evidence is never overwritten.

## What the evidence proves

Before installation, 10,400 directed/random cases compare authored arithmetic
with the original 22-byte leaf executed in an isolated x86 reference reservation.
The reference checks every GPR, defined arithmetic flags, DF, return address,
stack delta and all 4,096 bytes of its guarded payload. Seven corruption controls
check that register, flag, return and memory differences are detected.

Another 64 cases execute the actual entry/return assembly thunk. They check
`ret 4`, preserved registers, flags, 1,024 caller-owned stack bytes and the
FXSAVE state covering x87/MMX/XMM/MXCSR. The thunk reserves aligned stack scratch
space for C++ and logging and restores floating-point/vector state afterward.

Each real `game_call` records the actual process, thread, caller, ECX base and
stack argument. Before returning authored outputs, it runs the original leaf
on those inputs in the isolated reference reservation and rejects discrepancies.
The expected original return site is `0x00405173`. Self-test calls have a
different event name and are never counted as in-game evidence.

`memory_unchanged` in this trace refers to the isolated reference payload, not
every byte of the live game process. `stack_delta` describes the reviewed return
contract, checked by the thunk tests. The experiment uses additional scratch
stack memory and synchronous flushed logging. It is a verification probe, not
a performance improvement or a general renderer/physics compatibility fix.
Any detected mismatch ends this research game process with exit code 91.
Initialization failure cancels only the launcher's own child process.

Private reference bytes, installed game assets, builds and run logs remain
ignored. The public tool contains only authored source, identities and contracts.
