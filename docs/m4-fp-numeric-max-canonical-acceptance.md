# Numeric-max component: canonical admission and caller-state repair

The bounded shared numeric-max component is accepted with its explicit owned
invocation boundary, strict Boolean shadow flags and separately measured
incoming PE/C1 behavior. This component acceptance does not add an initializer
to the connected startup gate or complete M4.

The earlier caller-state defect, noncanonical flag alias and C1 carry failures
remain preserved. The new candidate restores caller numerical state and full
legacy environment before returning through `Session.invoke`, rejects all
eleven shadow flags unless each is 0 or 1 before status projection, and clears
C1 at the source-defined FLD commit when stack overflow is absent. It preserves
incoming sticky PE. These are separately enumerated changes; the translated
guest instruction bodies and shared r9 runtime remain unchanged.

Independent raw prediction covers 57,024 native phases: 41,472 directed/carry
phases, 864 narrow persistent phases and 14,688 replays seeded only from frozen
original BEFORE captures. It checks complete 3,504-byte State, four pages,
1,254,528 source events, 171,072 call routes and direct caller numerical/legacy
environment preservation. The carry observer also compares 110,592 checkpoints
against separately captured authored FLD/FSTP hardware observations. Those
additional hardware probes are not original game or full initializer runs.

The independent compiled controls pass 136,208 assertions across 1,420 scenarios
at O0/O2, including 176 malformed flag variants, entered failure and poisoned
retry, valid owner reuse, wrong-thread/nested refusals, and 2,832 direct
before-cleanup hardware snapshots. Fresh source/COFF/EH checks bind the exact
canonical candidate and retain preceding failed drafts. Raw observer corruption
controls reject altered State, memory, events, routes and numerical host fields;
excluded volatile SIMD/padding cases remain explicit observations.

Admission remains bounded to sixteen binary32 inputs, twelve masked IC0 control
words, TOP 0/7, contiguous stack depths 0/1/7, incoming DE/PE combinations and
C1 0/1. It does not establish arbitrary x87 states, full volatile SIMD equality,
concurrent publication, or preservation through raw `Runtime.call_direct` outside
the owned boundary. Final FSTP C1 without a newly generated precision exception
remains an observation; incoming sticky PE does not establish a new rounding
event. Actual carry from the preceding 26 initializers still needs its own
connected execution and review.

Evidence is retained in the private `reports/m4-fp-numeric-max-carry` directory:
`native-canonical-r1`, `author-canonical-review-r1`,
`independent-canonical-closure-r1`, `independent-carry-model-r3`,
`independent-narrow-persistent-r1`, `independent-narrow-replay-r1` and the
root component acceptance receipt. Current disk/source/header associations are
distinct from complete execution-time dependency attestation.
