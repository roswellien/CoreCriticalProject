# Matherr native callback-registration variant

This is a finite native compiler/runtime test for the complete four-instruction
staged MSVCRT `__setusermatherr` leaf at `0x7800B38F`. It stores a guest integer
callback value and clears `0x780392B8`; it never invokes a callback. The real
game `PUSH 0x51E7B0` and `CALL [0x5BB50C]` are static linkage evidence. The full
CRT caller and ordinary game startup are not executed by this gate.

The root preflight sources, shared Runtime r9, guest IR and earlier reports stay
unchanged. New native sources are under `tools/m4-crt-matherr/paired`. The first
six native attempts and all source versions remain in separate private report
directories. The final build is `paired-native-build-r7`.

The final variant uses a tiny C++ exception through non-noexcept external
bridges. Its enclosing catch runs after unwinding the compiled LLVM frame.
CMake's inherited `/EHsc` is removed, and `/EHs` is explicit: appending `/EHs`
alone left the external-C no-throw assumption active and removed the local
catch. Failed r1/r2/r3 logs preserve this observation; the shared runtime still
poisoned those failed calls. Actual final O0/O2 controls establish local cleanup,
first-error retention, blocked poisoned retry and full host FX512/ENV28 restore.

Each level passes 1,536 coherent positive unit cases, 21 denial scenarios and
1,692 assertions, including 17 corrected retries against poisoned Runtime.
There are 20 separate native CLI/output denials and three recipe no-mutation
controls. The 12 masked control words, all eight TOP values, live depths 0/1/7/8,
sticky status 0 or `0x25`, eight callback integers, two repeats and DF 0/1 are
explicit input fixtures. No numeric operation or FWAIT is executed by the leaf;
no unmasked numerical domain is admitted.

The original reference records were completed and frozen before the task was
narrowed to native testing. This variant only reads that file offline. The
replay accessor selects tags, original BEFORE CPU, FX, legacy ENV and owned
pages. Original AFTER fields are never execution inputs. Each record has a fresh
Runtime. r9 explicitly pushes the same existing return word `0x5AC42E` at
`0x200017FC`; this is same-word native orchestration, not an original CALL claim.

Original CPU AFTER records contain the authored final capture PC `0x10000100`;
the relational comparison projects only that PC to the real return `0x5AC42E`.
AND's original AF is undefined and excluded only from paired CPU comparison.
Native AF's selected zero remains checked in the full State and CPU model.
Every other CPU field, all three whole pages, all 3,504 State bytes and the five
actual ordered checked accesses are checked. Original State/events are
unobserved. Hardware original FX/legacy ENV remain separate. Native Runtime FX
is owned software storage; native ENV-after is preserved input serialization,
with actual whole State independently proving the legacy fields remain intact.
Native host FX512/ENV28 are actual host captures around explicit restoration.

Native raw framing is 24 bytes: `MW4MPN01`, then four little-endian u32 values
`{1,1536,33964,3504}`. Each record begins with the original-compatible Common
26,836-byte layout: tags20, CPU before40/after40, four FX512, four ENV28, and
before/after three-page memory12288. StateBefore begins at26836, StateAfter at
30340, five16-byte events at33844, route six u32 at33924, counters four u32 at
33948. Route is `{site,target,return,import,completed,index}`; counters are
`{step,used,complete,failed}`. Each event is `{address,value,width,write}`.

Return-word, nonvolatile and EAX corruption controls are explicit authored unit
observers; the observer is null in every positive and replay row. Protected or
unmapped argument/global/RET controls cause real compiled access failures.
Pre-entry routing denials need not fabricate a Context first error. Active-call
failure poisons Runtime, whereas existing pre-call IAT/return/registry/stack
denials can remain unpoisoned under r9's existing contract.

The gate assumes serial trusted Runtime ownership and ordinary private paths.
Deliberate host changes to immutable game metadata/mapping ownership, concurrent
writers and reparse-point publication are outside this test. Two earlier test
assertions incorrectly expected denial after changing unexecuted CALL bytes or
host permissions without changing immutable admission metadata; those failed
versions remain preserved. They do not grant source/permission revalidation
credit. The final variant adds no production startup registration or full M4
completion claim. A different reviewer must independently accept the candidate.

Fresh native reproduction (it only reads the frozen original stream):

```powershell
& 'C:/Users/jcbla/.cache/codex-runtimes/codex-primary-runtime/dependencies/native/powershell/pwsh.exe' -NoProfile -ExecutionPolicy Bypass -File tools/m4-crt-matherr/paired/build_native.ps1 -OutputDirectory D:/Projects/MW34Recomp/reports/m4-crt-matherr/paired-native-fresh-r1
```

The report directory and both derived build directories must all be absent.
The final compilation consumes the frozen ABI-r1 host IR directly at O0/O2,
using LLVM21 and Runtime r9. Build reports contain literal source snapshots,
tool identities, commands, compiler include logs and output identities.
