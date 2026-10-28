# Actual CRT caller connected through math-error registration

Accepted 2026-10-08 within the bounded composition and caller domains below.

The compiled FDIV writer and game CRT entry now call the actual translated
`__setusermatherr` leaf on the same Runtime, State and guest memory. The game
stores callback address `0x51E7B0`, returns from the provider, cleans up its
cdecl argument and reaches its next required direct helper: source `0x5AC431`
calls the CRT floating-point control wrapper at `0x5AC5A0`.

The [root acceptance receipt](../../reports/m4-crt-entry-matherr/root-acceptance-r1/report.json)
binds the [final build](../../reports/m4-crt-entry-matherr/build-r3/build.json),
[fresh root execution](../../reports/m4-crt-entry-matherr/root-execution-r2/execution.json),
[independent source observer](../../reports/m4-crt-entry-matherr/root-model-r4/report.json)
and [independent compiled/foundation review](../../reports/m4-crt-entry-matherr/independent-foundation-r2/report.json).
The enclosing M4 milestone remains active; the selected initializer gate remains
27 of 144 nonzero roots, with 117 outside that gate. This service composition
has not yet been joined to the selected initializer table's actual CRT caller.

## Persistent execution and source identity

Fresh O0/O2 executions cover 48 positive compositions from the 24 preserved
original FDIV BEFORE inputs and 48 causal failure cases. Expectations come from
those BEFORE inputs, exact PE source and actual OS feature-query observations.
Native AFTER bytes are comparison evidence. No author fixture model supplies
the independent expectations.

Each checkpoint retains the entire 3,504-byte State, separate 512-byte FX
image, fourteen pages, three CRT DWORDs, admitted NT_TIB fields and 447 bytes
of entry/provider identity. The added provider pages are exact raw section
pages, disjoint from the FDIV pages. Their final page includes raw alignment
padding. Complete DLL initialization remains open.
Only declared CPU/frame transitions project State; FP and opaque fields carry
through the compiled producer, caller and provider without reseeding.

The unchanged compiled provider objects execute four source instructions at
`0x7800B38F`: read the actual callback argument, clear `0x780392B8` from its
source value `0x2694`, store callback data at `0x7803B0C4` and perform RET.
The owning game IAT slot is `0x5BB50C`, with unchanged raw value `0x1DED1E`.
The callback remains guest data and is not invoked.

The observer predicts all 4,656 positive FDIV events, 1,680 game events and
240 math-error provider events, complete call ledgers and every checkpoint.
It rejects 11,248 corrupted checkpoint, event, status and route observations
through the same comparisons used for acceptance. These are evidence-validator
controls, separate from actual compiled failure injections.

## Failures and caller preservation

Actual failures cover the preceding producer/entry checks, changed provider
pages or IAT, protected zero/callback globals, changed callback/return frame,
corrupted return registers, invalid access order and an observer exception.
The source model predicts their complete stopped State/page prefixes, exact
first attribution and terminal retry. The zero-store failure occurs before
AND flag updates. A rejected RET read leaves the original ESP; a post-RET
closure failure retains the already changed State while Runtime CPU remains
at the incomplete service boundary. No required failure receives continuation
or successful retry credit.

Independent compiled fixtures add 494 assertions across 34 cases, including
30 null, arbitrary and cross-owner token denials before mutation. Typed bridges
require the currently active owner before accessing either Context. Fresh COFF
and unwind inspection verifies the frozen provider objects and actual O0/O2
exception-handling paths.

The ordinary root captures check 186 direct caller boundary pairs. An additional
68 independent hardware pairs deliberately populate FIP/FDP/CS/DS/FOP, live
x87 depths 0/1/3/7, TOP 3/7, sticky status `0x20`, CW `0x0A7F`, MXCSR `0x1FA0`,
raw80 registers and ABI-preserved XMM6–15. They exposed metadata loss when a
required entry failure unwound through C++ catch handlers. The
[failed rich-metadata capture](../../reports/m4-crt-entry-matherr/independent-compiled-r5)
is preserved.

The repaired invocation boundary owns a full FX and legacy ENV guard spanning
the actual call and its catch handlers, restoring the caller immediately before
the bool return. The internal invoke guard adds protection; the encompassing
boundary is required for the reviewed preservation guarantee. All 68 deliberately
populated hardware pairs now preserve the declared caller state. Volatile
XMM0–5 equality is not claimed.

Correction to the earlier [FDIV-to-entry review](m4-crt-entry-data-review.md):
its statement claiming nonzero legacy metadata coverage overstated the fixtures.
Their 138 caller pairs had zero FIP/FDP/CS/DS/FOP. The earlier equality results
remain bounded, while this new gate supplies deliberately populated metadata
tests and the resulting repair. Frozen prior evidence is retained.

## Remaining boundary

The guest FDIV corpus remains twelve masked control words with an empty TOP0
register stack and two repetitions. Broader guest/host domains, original full
CRT entry, DLL attach, guest exception dispatch, remaining CRT setup, callback
execution, the full initializer ledger and native menus remain open. Undefined
AF receives only the retained explicit representative.

Next, connect and compare the actual control wrapper and its provider, then
argument initialization and the CRT initializer-table caller. The bounded
research executable does not establish a native game menu or Training session.
