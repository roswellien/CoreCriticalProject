# Bounded initialized FDIV data and actual game CRT entry

This additive research worker executes the frozen translated FDIV writer, then
borrows its same accepted r9 Runtime, complete 3,504-byte State and checked pages
for the actual translated ordinary game entry. The constructor does not reseed
State, FP, memory or provider data. The declared outer transition changes only
ESP/EIP; literal source CALL/RET and measured CRT services carry the other fields.

The actual Windows query initializes provider data, the owning game IAT projects
only at source `0x5AC408`, and source `0x5AC40D`/`0x5AC40F` reads and copies the
actual BOOL. The frozen translated `0x5AC5C0` RET runs next. The bounded probe
then fails explicitly at the next missing service, `MSVCRT!__setusermatherr`,
source `0x5AC428`, owning IAT `0x5BB50C`.

`prepare_v4.py` preserves the preceding preparations and adds literal 430-byte
entry-source captures. `build_v6.ps1` links immutable O0/O2 entry objects and FDIV
Registry libraries; it rejects existing private output/build directories. Run
the resulting `entry_data.exe` with these six arguments:

1. Exact `MW3/Mech3.exe`.
2. Matching frozen `reports/m4-crt-fdiv-entry-prefix/preparation-r2/candidate-O0.obj`
   or `candidate-O2.obj`.
3. Exact `local/mw3-staged/Shared_DLLs/MSVCRT.DLL`.
4. `reports/m4-crt-fdiv/native-derived-r1/pack.bin`.
5. `reports/m4-crt-fdiv-replay/preparation-r1/before-inputs.bin`.
6. A fresh private experiment directory.

Each build executes 24 original-BEFORE projections (12 supported CWs, twice)
and 12 causal fault scenarios. Fresh phase captures retain whole State/FX,
11 pages, mapped NT_TIB fields, CRT globals, literal entry source, every access,
typed data route, actual Windows API ownership, and terminal retries. Direct
assembly caller captures check legacy ENV28, physical x87 raw80, MXCSR, and
seeded nonvolatile XMM6–15. Volatile XMM0–5 have no equality requirement.

The exact source TEST at `0x5AC41F` requires an undefined AF representative.
This probe supplies zero only there and records its actual site separately.
That representative grants no defined original AF equality or preservation.

The author source observer imports only the author's frozen FDIV interpreter
and separately decodes actual game/provider MOV/CALL/RET/TEST instructions.
Independent root review is a separate gate. This worker does not launch the
original game, execute complete DLL attachment, implement exception dispatch,
complete CRT startup, or increase the connected initializer acceptance count.
