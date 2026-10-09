# M4 initialized FDIV data connected to native CRT entry

Accepted 2026-10-08 within the bounded producer/consumer scope below. The actual
translated FDIV writer and game CRT entry now execute on the same persistent
Runtime, State and guest pages. Entry consumes the source-written `_adjust_fdiv`
value and stops at its next missing measured service, `__setusermatherr` at
source `0x5AC428`, owning game IAT slot `0x5BB50C`.

The [root execution receipt](../reports/m4-crt-entry-data/root-execution-r1/execution.json)
records fresh O0/O2 worker execution: 48 positive compositions and 24 causal
failure cases. The [independent source observer](../reports/m4-crt-entry-data/root-model-r1/report.json)
predicts the complete results from the preserved original FDIV BEFORE inputs,
exact PE source and actual Windows query observations. Native AFTER bytes are
comparison evidence only. The [build receipt](../reports/m4-crt-entry-data/build-r6/build.json)
pins the literal compiled objects, source, toolchain, headers and libraries.
The [second foundation/source audit](../reports/m4-crt-entry-data/independent-source-r1/report.json)
finds no additional blocker within this scope and independently checks all
direct caller boundary observations, including nonzero legacy metadata.

Each positive composition carries the entire 3,504-byte State, separate
512-byte FX image, eleven owned pages, three CRT DWORDs and implemented NT_TIB
fields across the producer and consumer. The entry adapter changes only the
declared outer ESP/EIP transition before executing the game instructions. A
separate checkpoint captures that transition and actual outer return frame.
The 430 original entry bytes are retained at every checkpoint.

The source read at `0x5AC408` records the unchanged raw IAT value `0x1DED32` and
resolves the initialized provider address `0x78037C2C`. Source `0x5AC40D` reads
the actual query BOOL and `0x5AC40F` stores it at game global `0x9A17E4`. The
three measured CRT services return correctly, and the real translated one-byte
RET at `0x5AC5C0` executes. The source TEST at `0x5AC41F` records one explicit
AF=0 representative; AF is undefined there and receives no preservation or
original-equivalence credit. The root call remains incomplete at the required
missing math-error service.

The independent observer checks all 4,656 writer events and 1,632 consumer
events, data ownership and complete call ledgers. It rejects 56 deliberately
corrupted state, memory, event and route observations. The 24 actual negative
cases cover premature data resolution, incoherent State/FX control words,
read-only provider data, changed provider instructions/IAT/data, changed game
entry/IAT bytes and read-only stack/game/CRT destinations. Their exact stopped
source prefixes, first faults and terminal retries are independently predicted;
no continuation or successful retry is credited after a required failure.

All 138 direct caller boundary observations preserve numerical FP state,
physical raw80 registers, MXCSR, complete legacy ENV28 and ABI-preserved
XMM6–15. Volatile XMM0–5 bytes remain observations without equality credit.
Earlier build failures, the undefined-AF stop and control-fixture failures are
preserved separately.

The admitted FDIV corpus remains twelve masked control words, TOP0 and an
empty register stack, with two repetitions. The entry frame and first three
CRT globals are explicit research inputs. This accepts initialized data
consumption within that corpus; it does not establish original full CRT entry,
DLL attach, guest SEH dispatch, remaining initializer coverage or native menus.

The next service integration is the separately reviewed
[math-error callback registration](m4-crt-matherr-review.md), followed by the
control wrapper, argument initialization and actual CRT initializer-table path.
Each needs persistent-state composition review before advancing entry.
