# Live native address-helper test

Run `Launch MW3 with Native Helper.cmd` from the project root, load Training,
play briefly and quit through the game's menu. The reviewed call to
`0x409ED0` occurs during loading. It computes an address and has no intended
visible gameplay change.

The launcher builds an authored x86 DLL/launcher and two persistent x64 workers.
Each worker links the exact accepted generated helper object from G2 at O0 or
O2; live play uses O2. It does not execute an authored formula for the result.
The authored bridge redirects the five-byte CALL at `0x40516E`, retaining the
entire original function for comparison. Installation happens with the game's
entry thread held after Windows loader initialization.

Before launching, both workers undergo independent directed/random and rejected
input checks. A separate original-x86 thunk test verifies actual stack cleanup,
registers, flags and preserved FP state. Build inputs and immutable executable
copies are recorded in a fresh `reports/mw3-live-native-helper` directory.
Python invokes PowerShell with a process-scoped policy argument.

For an actual call, the bridge captures literal CPU/flags, FX512, separate ENV28,
the stack argument and return address before C++ scratch work. The x64 worker
imports observed CPU fields into a zero-seeded hidden Remill State and projects
the argument and return into an owned 4096-byte virtual stack. The generated
code performs two checked reads and one `RET 4`; the whole page must remain
unchanged. Its generated arithmetic flags merge with the captured remaining
flags. ESP and EIP map back to the actual caller.

The original function also executes on a guarded private hardware stack from
the same captured input. Its CPU, preserved FP/ENV and unchanged page must match
before compiled output is returned to the game. FP remains opaque transport:
the admitted integer-only helper never observes or changes it. Native FX512
and ENV28 echo the original input; separate original hardware observation and
the returning x86 thunk check preservation.

IPC binds the actual pipe client/server PIDs, sequence and worker identity.
An idle worker waits until the next call; partial transfers have deadlines.
Rejected requests are logged without native test credit. Execution failures,
mismatches and lost IPC stop this launcher's own child rather than publish an
unverified result. The on-disk game and earlier numeric test remain unchanged.

Every synthetic and actual call has private BEFORE/native/original snapshots
and original page before/after files. `verify_live.py` derives CPU effects and
memory predictions solely from BEFORE, checks the admitted source/caller route,
and deliberately corrupts observations to test its rejection behavior:

```powershell
C:/Python314/python.exe tools/in-game-native-helper/launch.py --prepare-only
C:/Python314/python.exe tools/in-game-native-helper/verify_live.py <fresh-run>
```

The passive monitor records process/window health and file output. Visual
glitches, frame timing and every possible internal error require more
instrumentation. This test covers one live component in the original x86 game;
the full native startup/menu milestone remains active.
