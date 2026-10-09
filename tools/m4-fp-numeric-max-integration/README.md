# Shared Runtime numeric-max prerequisite

This new namespace connects the exact compiled table root `0x4C19F0`, complete
body `0x4C1A00`, and actual staged MSVCP50 leaf `0x780C10F0` through the frozen
Runtime r9 checked memory, persistent State, registry and real guest return
frames. It registers the real named MSVCP50 owner at game IAT `0x5BB4FC`.
The frozen MSVCRT-only provider-continuation parser is unused: the leaf returns
directly to admitted game address `0x4C1A09`. Provider code/data are owned guest
byte containers, never executable host mappings.

The three accepted strict-FP IR bodies retain their numeric/type semantics.
New names isolate the bridges; only the wrapper's direct body call is routed
through the shared dispatcher. The compiled original CALL writes its return
word first. Orchestration raises the caller-view ESP by four, then r9 stores
the same word. Actual compiled RETs update State and are validated by r9.
Typed C++ bridge exceptions unwind actual LLVM COFF frames to the outer
Session boundary; first-error and poisoned-context checks prevent continuation.
No production runtime or accepted standalone source changed.

`native-build-r5` passes 106 assertions per optimization level, 22 denials,
21 corrected poisoned retries and five constructor/ownership scenarios.
It records 216 persistent pairs (432 phases) and replays 432 default plus
6,912 directed wrapper inputs per level from frozen original BEFORE fields.
Raw magic is `MW4NMI01`, header24, stride46,680. The compiled `schema.json`
describes every offset. Actual C++ State is 3,504 bytes/alignment16; the
unchanged LLVM types have alignment8 and Runtime storage alignment64.

The admitted profile has twelve masked control words, TOP0/7, contiguous
depth0/1/7 with the measured live raw80 values, incoming sticky0/2/34 and
C1/C0/C2/C3 zero, flat DS/SS, owned FS and coherent separate software FX.
Depth8 is rejected before a guest body runs. Dead storage is carried; it is
never reseeded between positive phases. Explicit directed data fixtures
substitute only one source DWORD in the exact provider RO page.

Offline replay reads original BEFORE CPU/FX/legacy ENV/four pages and a
declared hidden-State seed. Original AFTER/checkpoint records are observer
inputs only. BEFORE projections replace the instrumented outer capture word
and return PC with admitted RX `0x410A80`, retain the actual raw owning game
IAT rather than the original sparse-worker's resolved provider address, and
use the owned r9 FS base. No output value is normalized. Native FX and ENV
are explicit software projections of actual State; original FNSTENV and
debugger CONTEXT have distinct hardware provenance. Full actual host
FX512/ENV28 restoration is tested around positive and failed calls.

Lifetime requires a stable Runtime and one lexical serial borrower on the
constructing thread. Session must outlive registered calls. Discard Runtime
after a failed constructor or partial registry registration; registration
rollback is unavailable in r9. Current owned mappings/metadata are trusted;
host mapping replacement, deliberate permission changes between admission
and use, concurrent publication and reparse points are excluded. Borrowers
are used lexically and are not copied or moved. No callback/data pointer is
invoked as host code.

Fresh private output and both derived build directories are admitted before
recipe mutation. Final worker publisher uses CREATE_NEW staging and
no-replace commit. Existing ordinary output/stage sentinels and partial
recipe markers survive actual denial controls. Historical failed attempts
and their literal sources are retained.

This is one bounded shared callback, pending independent integration review.
It is not yet a 27-root connected gate. At the actual table position after
`0x4B7020`, the accepted26-root stream carries PE and sometimes C1, outside
this standalone profile. Broadening admission alone would be incorrect:
the old FLD IR does not clear incoming shadow C1. A new measured derivative
must close that carry domain without reseeding before joint integration.
Full startup, DLL initialization, SEH, MFC/menu and full M4 remain open.

Reproduce with bundled PowerShell7 and an entirely new immediate private
report name:

```powershell
pwsh -NoProfile -ExecutionPolicy Bypass -File tools/m4-fp-numeric-max-integration/build.ps1 -OutputDirectory D:/Projects/MW34Recomp/reports/m4-fp-numeric-max-integration/native-build-fresh
```

Run the author observer with fresh output, and the worker checker with a
fresh report/fixture namespace (the checker currently owns fixed historical
recipe-marker names; an exact rerun must use a newly authored variant).
Neither command executes an original x86 process or an ordinary game.
