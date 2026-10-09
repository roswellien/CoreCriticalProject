# Independent CRT control provider review

The complete statically compiled `_controlfp`/`_control87` provider component
passes independent review for its measured empty-stack domain. An independent
x86 instruction model predicts all registers, defined flags, normalized CW,
all 4,096 stack bytes and nested CALL/RET events from original before-state.
All 3,264 original records and 6,528 native O0/O2 records match that model.
The [author experiment](m4-crt-control-experiment.md) remains frozen; this
record closes its pending independent review.

The [independent report](../reports/m4-crt-control/independent-review-r4/report.json)
has SHA-256 `b75abde48029efcdb8cb123c163c6bfb27a9b76dc62da014e620fca7c95bac56`.
Its [physical map](../reports/m4-crt-control/independent-review-r4/pins.json)
has SHA-256 `fbba28c07c1f1ccc2308d41f6c9264a38a1a8dba6fdd9b8bb0689c6b86aed6c4`
and 1,093 bindings. It verifies the frozen 1,039-binding author aggregate,
55 explicit historical source substitutions and 19 pre-repair literal sources.

Fresh provider decoding verifies every instruction byte against the admitted
file. Independent static analysis matches all 148 original instruction PCs
to the complete four lifted bodies, reverses the three typed FP transfers,
and verifies all 34 named guest/host layouts. Every host State store has a
resolved destination and width, including the AH alias. Required fault
boundaries promise neither `nounwind` nor `willreturn`. Sixteen actual bound
objects were independently decoded.

The raw comparison protects every native State byte, separate FX512 and
legacy ENV28 metadata, guest stack and full captured host restoration. It
checks 45,696 real native entry/return events. The independent observer
rejects 226 corruptions and accepts two explicit undefined-original-AF
controls. The 24 actual worker controls and 27 compiled context controls per
optimization level remain bound to their actual execution logs.

The review preserves the causal Windows `longjmp` defect and its narrow
repair: removing `noexcept` from `Context::deny` leaves every other Context
byte unchanged. Earlier guest-positive streams remain preserved. Two reviewer
failures concerned LLVM's unnamed SSA renumbering and a scalar helper's formal
argument; their literal sources and diagnostics remain in the independent
evidence alongside the passing review.

Acceptance covers twelve measured masked incoming CWs, empty physical tags,
SW0/TOP0 and MXCSR `0x1F80`. The corpus executes 146 of the 148 static PCs;
the two incoming-IC-set decoder PCs remain statically retained but unmeasured.
Guest exception masks may become unmasked, but no numerical instruction
follows within this component. Occupied stacks, pending exceptions and host
numerical-CW synchronization remain open. The Context is a serial trusted
worker object, not a general thread-owned or single-use callback interface.

The shared Runtime r9 and its provider registry remain unchanged. Actual game
service routing, initialized data imports, complete CRT/SEH startup and the
native menu path require fresh integration. This component does not complete
M4.
