# Actual CRT caller connected through floating-point control

Accepted within its bounded scope, 2026-10-08. The root acceptance seal binds
the passing source/object review, compiled fixtures, fresh root execution,
whole-state source comparison and independent read-only model audit.

The compiled FDIV writer, game CRT entry, math-error registration leaf and real
floating-point control wrapper now execute on the same Runtime, State, FX image
and guest memory. Source CALL `0x5AC431` enters wrapper `0x5AC5A0`, whose actual
PUSH instructions supply `_controlfp` arguments `0x10000` and `0x30000`. The
compiled staged provider selects 53-bit x87 precision while carrying the other
incoming control-word bits. It returns through the real import and wrapper
frames, and game entry continues to the next required initializer-table call.

That next boundary is source CALL `0x5AC440` → thunk `0x5AC598`, with return PC
`0x5AC445`. Immediately preceding source PUSH instructions supply table bounds
`0x5E024C` and `0x5E0248`. The thunk is the actual `JMP [0x5BB510]` import route
to `_initterm`. This first interval, `[0x5E0248, 0x5E024C)`, contains one null
entry; connecting this call will not run the selected callbacks. A later main
interval, `[0x5E0000, 0x5E0244)`, contains the 144 nonzero initializer callbacks.
The next thunk's translated body and both actual caller/table connections remain
outside this composition. The selected initializer gate remains **27 of 144
nonzero roots, with 117 outside that gate**. This change does not increase that
count or join the separate selected-root gate to the real CRT caller.

The final evidence uses [preparation-r5](../reports/m4-crt-entry-control/preparation-r5/pins.json)
and [build-r6](../reports/m4-crt-entry-control/build-r6/build.json), with
[fresh root execution](../reports/m4-crt-entry-control/root-execution-r1/execution.json),
[independent root source observer](../reports/m4-crt-entry-control/root-model-r3/report.json),
[independent source/object closure](../reports/m4-crt-entry-control/independent-source-r2/report.json),
[independent compiled closure](../reports/m4-crt-entry-control/independent-compiled-review-r1/report.json)
and [hardware-observer controls](../reports/m4-crt-entry-control/independent-compiled-observer-controls-r1/report.json).
The [read-only root model audit](../reports/m4-crt-entry-control/independent-root-model-audit-r1/report.json)
confirms the final observer and corrected partial PUSH ordering. The
[root acceptance receipt](../reports/m4-crt-entry-control/root-acceptance-r1/report.json)
seals 86,884 physical dependency bindings; its SHA-256 is
`984e18e7165532a0d219082122245d527716042d7dd97ff1fb6f378df134b460`.

## Persistent state and compiled source

Fresh O0/O2 root runs cover 48 successful compositions from the 24 preserved
original FDIV BEFORE inputs and 72 causal failures. Expectations derive from
those BEFORE inputs, exact game/provider PE source and actual OS feature-query
observations. Native AFTER records are comparison evidence; the independent
observer does not import an author fixture model.

Every checkpoint retains the entire 3,504-byte State, the separate 512-byte FX
image, the same fourteen pages, three CRT DWORDs, admitted NT_TIB fields and
900 bytes of source identity. The identity comprises 430 entry bytes, 17
math-error leaf bytes, 19 wrapper bytes, six thunk bytes, 303 hot provider bytes
and 125 cold provider bytes. The control provider reuses the already mapped
FDIV pages. Its Context borrows the persistent State and FX without reseeding,
remapping pages or resetting software FP state. The typed control-word transfer
updates State CW and the first two Runtime FX bytes, preserving their distinct
legacy pointer/opcode metadata.

The earlier entry and math-error COFF objects remain unchanged. Control COFF
objects are newly compiled from the accepted complete control IR after exactly
nine LLVM names are moved into a composition namespace: two game bodies and
seven flag/undefined helpers. Reversing the complete declared mapping recovers
the original IR exactly; provider bodies and external bridge ABIs retain their
source semantics. This is a reviewed symbol derivative, rather than reuse of
the older control COFF files. Independent inspection binds the actual O0/O2
control objects, production typed boundaries, exception unwind data and
compiler-read header associations.

The root source observer verifies 4,656 FDIV events, 1,824 game events, 240
math-error accesses, 624 control route events and 2,496 control source accesses
in successful records. It checks every complete and stopped checkpoint, call
ledger, source identity and terminal retry, and rejects 51,574 corruptions using
the same evidence comparisons.

## Required failures and caller preservation

The additive control Context replaces the earlier nested `setjmp`/`longjmp`
escape with `BridgeAbort` and C++ unwinding. Every entered execute boundary
decrements its depth and clears outer activity on success and exceptions.
Bridges verify the exact current typed owner before interpreting an opaque
token; simultaneous math-error/control ownership is refused. Required failures
retain partial semantic frames and the first diagnostic. A poisoned Runtime
cannot be revived by correcting the trigger.

The wrapper adapter clears its owner before taking a catch-path checkpoint, so
an observation failure cannot leak the owner. Independent fixtures exercise
both a post-completion observer exception and a second catch-checkpoint
exception, alongside exceptions before wrapper/provider execution. They also
cover actual generated writes, argument and return corruption, nonvolatile
register closure, event/access bounds, changed provider source and failures
after real FNSTCW and FLDCW transfers. All preserve the terminal prefix and
clear the entered C++ boundaries.

Root causal modes 28 and 29 mutate control hot/cold source before game entry.
The already admitted FDIV producer guards detect those changes before control
provider execution. They receive early producer-identity failure credit. The
independent compiled fixture mutates those bytes later, inside the actual
provider-before hook, and proves the provider's own source-identity rejection
before its first translated access. These are distinct causal checks.

The root observer retains partial translated instruction ordering. In
particular, a failing PUSH write at `0x780042EA` leaves the old State ESP because
the accepted IR commits ESP only after the bridge returns. The preserved
[earlier root-model failure](../reports/m4-crt-entry-control/root-model-r2)
led to correction of the scalar model's write/ESP order; the candidate IR and
compiled objects were unchanged.
Failed provider POP-read ordering is outside this root fault corpus and receives
no partial-prefix equivalence credit.

Independent compiled fixtures pass **1,676 assertions across 72 compositions**,
including **144 null, arbitrary, stale, cross-owner and conflicting-owner token
denials**. Their corrected triggers cannot change the complete State, FX,
fourteen pages, Runtime CPU, partial frames, access records or first diagnostic
on retry. The sealed [failed first fixture iteration](../reports/m4-crt-entry-control/independent-compiled-build-r1)
retains an incorrect observer-exception expectation; only that fixture
expectation was corrected for the passing build.

The ordinary root runs check 234 direct caller boundary pairs. An additional
144 independent hardware pairs deliberately populate complete FIP/FDP/CS/DS/FOP
metadata, live x87 depths 0/1/3/7, TOP 3/7, sticky status `0x20`, masked CW
`0x0A7F`, MXCSR `0x1FA0`, all eight distinct raw80 values and nonvolatile
XMM6–15. The accepted encompassing invocation guard spans the actual call and
its outer C++ catch handlers. Every declared caller field is preserved. An
additive observer check verifies every actual BEFORE raw80/legacy-tag fixture
and rejects 548 corruptions, including coherent but incorrect BEFORE/AFTER
fixtures. Volatile XMM0–5 equality is not claimed.

## Remaining boundary

The guest differential corpus remains twelve masked control words, an empty
TOP0 stack, zero pending guest status, MXCSR `0x1F80` and two repetitions.
Independent native-only CW variants provide causal fixture coverage without
enlarging original-process equivalence. The occupied x87 hardware fixtures
describe caller preservation, not a broader guest control-transfer domain.
Undefined AF retains only the existing explicit representative.

Next, connect the actual `_initterm` thunk and verify the first null-only
interval, then reach the later main-table caller and connect its dispatch to
the existing selected-root gate. Complete CRT startup, the
remaining tables and services, DLL initialization, guest exception dispatch,
callback execution, native menus and playable native gameplay remain open. No
ordinary game was launched for this gate, and no full CRT or whole-M4
completion credit is granted.
