# First actual CRT initializer interval

The native composition connects the real game CALL at `0x5AC440`,
frozen compiled thunk `0x5AC598`, and complete 28-byte staged MSVCRT `_initterm`
provider at `0x780014F8`. Its actual first interval
`[0x5E0248,0x5E024C)` contains one null DWORD. The native provider executes its
original loop and RET; the compiled game continuation then prepares argument
pointers and stops at the required `__getmainargs` import, source `0x5AC468`
and IAT `0x5BB514`.

The five stack arguments are four pointers (argc, argv, environment and startup
information) plus the wildcard flag read from guest BSS. The frozen author
README's phrase "five argument pointers" is corrected here; that README remains
unchanged under its author submission hash.

The fresh [root execution](../reports/m4-crt-entry-initterm/root-execution-r1/execution.json)
passes 48 positive compositions and 96 fault cases across O0/O2. These
144 rows include 282 direct caller host boundary pairs. The independent
[BEFORE-only instruction model](../reports/m4-crt-entry-initterm/root-model-r2/report.json)
compares all captured state, pages, ordered accesses and terminal retries;
68,840 meaningful corruption probes fail the same comparison validators.
The
[independent source closure](../reports/m4-crt-entry-initterm/independent-source-r3/report.json)
accepts the exact provider lowering, Session seam, typed ownership and compiled
associations. The [independent compiled review](../reports/m4-crt-entry-initterm/independent-compiled-review-r1/report.json)
passes 1,540 assertions across 62 actual scenarios, 192 malformed-token
refusals and 124 rich hardware caller pairs. The separate
[hardware-observer controls](../reports/m4-crt-entry-initterm/independent-compiled-observer-controls-r1/report.json)
reject 548 meaningful corruptions. The [read-only model audit](../reports/m4-crt-entry-initterm/independent-root-model-audit-r1/report.json)
accepts the full prediction and records the mode43 limit below. The final
[root acceptance](../reports/m4-crt-entry-initterm/root-acceptance-r2/report.json)
passes with 191,708 physically rehashed dependency bindings and report SHA
`0685db17817db850ae18d146de4c70844c4d94a0a5d41703bff57702b46c46fc`.
The independent read-only sealer review also passes. This is acceptance of the
bounded first-null composition; M4 remains active.

The [preparation](../reports/m4-crt-entry-initterm/preparation-r3/report.json)
and [build](../reports/m4-crt-entry-initterm/build-r3/build.json) retain the same
Runtime, State3504 and distinct FX512 through the accepted startup prefix.
The fourteen captured pages become sixteen by borrowing the already admitted
game table page `0x5E0000` and mapping the full literal provider RX page
`0x78001000`. Every checkpoint captures all pages and 934 source identity
bytes. Positive paths retain 48 game accesses, eight initterm accesses,
six initterm routes and nine completed Runtime call records; the root remains
incomplete at the next required service.

The private Session derivative makes exactly three edits: declaring the new
adapter, replacing only `_initterm`'s registered callback pointer, and
withholding the old callback continuation publication. The unused continuation
would own an overlapping 28-byte mapping. The complete source page belongs to
the new compiled provider instead; preceding service bodies, globals and
frozen Session files remain unchanged. No callback continuation or successful
nonnull callback execution is admitted by this gate.

New causal controls exercise provider/thunk/IAT corruption, early table
integrity, an actual later nonnull CALL denial, failed first PUSH, later stack
read bounds, modified RET word, ESI closure, observer exception, changed first
argument and an end pointer changed after the first CMP. The latter reaches
the real attempted next table read and is denied outside the owned interval.
Failed PUSH retains the prior ESP; POP publishes its increment before the
checked read; RET reads its word before publishing PC/ESP. Required faults
clear nesting and current ownership, and retries retain the full failed
checkpoint. Broader fault and incoming FP domains require their own evidence.

The injected ESP mutation after MOV has a bounded per-build observation:
O0 computes the next operand `0x20002008`; O2 retains `0x20001874` while
StateESP is changed. Both fail the current operand guard at `0x78001502`.
This tester mutation does not grant original architectural partial-fault
equivalence.

The ordinary source-derived causal corpus therefore contains 94 records;
the other two are artifact-specific observer-injection fixtures. Both
expectations are independently derived from preserved noalias IR and the
actual unchanged O0/O2 provider objects. Failed author/root expectations
remain preserved. No new complete original CRT execution was captured.

The main interval `[0x5E0000,0x5E0244)` follows argument setup and still contains
144 nonzero roots. This first null-only interval does not increase the accepted
selected count: **27 connected roots, 117 remaining**. M4 remains active; full
CRT, callback dispatch, application startup and native menus remain open.

Replay and sealing details are in the [root proof recipe](../tools/m4-crt-entry-initterm-root/README.md).
The author recipe is frozen in its separate submission; its original pending
acceptance wording records the state at submission time.
