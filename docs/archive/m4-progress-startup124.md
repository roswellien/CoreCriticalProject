# Accepted native startup sequence: 124 selected roots

Updated 2026-10-09. **124/144 selected startup initializers are accepted**, up from
[120](m4-progress-startup120.md), with **20 inventory roots remaining**. This is
86.1% of the initializer inventory. Full M4, project-built native menus and native
Training remain open.

The [final acceptance](../../reports/m4-joint-startup124-root/acceptance-r1/report.json),
SHA `6bd35e55bca15e1a0537044bf59a1c3ced5e9ef8b30a8a169b71c78824811462`,
binds **39 passed gates and 324 explicit measured predicates**. Its complete
conflict-normalized union physically rehashed **11,809 dependencies** in 103.82
seconds, including every historical capture whose identity was reused during
local iterations. No metadata cache or historical archive exemption was used.
The accepted 120-root evidence remains unchanged.

## Added behavior

Roots `411010`, `4DC140`, `500660` and `5968F0` execute in the original relative
table order. Recovery covers ten new game bodies, fourteen entries, 303 physical
instruction rows and 1,048 bytes. Two admitted MSVCP50 fast-path bodies add
seventeen rows and 51 bytes. Warm Ghidra analysis corroborates the game bodies;
the literal physical bytes define the recovered closure.

The genuine x86 loader establishes initialized MSVCP state2 and its critical
section. The native runtime associates a distinct real 40-byte Windows critical
section with the 24-byte guest object. Observed serial lock fields have exact
typed relations; opaque loaded fields retain their own complete input bytes.
This accepts the reached initialized constructor/destructor path. Native MSVCP
DllMain, lazy initialization, contention and Sleep paths remain outside this gate.

The four roots add four stored callback registrations and eight MFC allocations:
six requests of 24 bytes and two of 20 bytes, each genuinely acquiring a 32-byte
original backing. Thirty-two exact owned stores and eight publications have
independently corroborated original/native contracts. The full schedule has
**96 ordered callbacks, 58 MFC allocations, 19 duplicated strings and one callback
vector: 78 live ordinary owners before cleanup**, plus five real critical sections.
Stored callbacks are not executed by this initializer gate.

## Passed evidence

| Gate | Measured extent |
| --- | --- |
| [Genuine original execution](../../reports/m4-lockit-original/original-validation-r2/report.json) | Six persistent sequences, 744 phases, 43 pages, 144 Lockit snapshots, 48 API frames and 48 new owners |
| [Original source](../../reports/m4-lockit-paired-provider/original-r2/report.json) | 24 new prefixes, 144 actual source boundary joins, 72 normal FS joins and 1,860 complete owner carries |
| [Persistent native source](../../reports/m4-lockit-source/connected-native-source-r3/report.json) | Twelve O0/O2 sequences, 1,488 phases, 63,984 whole pages before and after; no per-phase or AFTER machine seeding |
| [Provider lifecycle](../../reports/m4-lockit-source/native-provider-r1/report.json) | 24,636 full State/CPU/FX checkpoints, 2,307,540 whole checkpoint pages, 696 MFC allocations, 228 string duplications and 936 source frees |
| [Paired data](../../reports/m4-lockit-paired-provider/paired-r2/report.json) | 122,016 ordinary page relations plus 2,976 separate whole loader-page relations: 124,992 nonstack endpoints |
| [Independent paired review](../../reports/m4-lockit-review/paired-review-r1/report.json) | 96 whole private-owner byteflows, 384 typed DWORD stores, 216 branch derivations and 8,928 whole provider-page reconstructions |
| [Causal controls](../../reports/m4-lockit-review/controls-validation-r4/report.json) | 64 attempts: 30 targeted refusals, 32 unchanged whole-state retries and two positive four-root runs; 160 real resource deletions |
| [Independent configuration review](../../reports/m4-lockit-build-review/acceptance-r1/report.json) | Exact 39-gate configuration, typed predicates, implementation/build edges and mandatory final full physical verification |

Across both native levels, the twelve sequences complete a total of 96 Lockit
CALL/RET pairs, 96 complete paired normal FS relations, 96 publication activations
and 288 whole new-owner carries. Source
comparison retains complete installed/restored twelve-byte normal game records,
all persistent state and the observed host boundaries. All twelve provider
sequences release their owners and observe the real post-HeapDestroy identity.
Used callback-vector size and measured capacity are 384 bytes; genuine same-owner
size queries independently predict the observed first additional growth.

Original Lockit observation stops at the constructor's API return before its
epilogue, and at the destructor's pre-RET. Their post-RET CPU is independently
source-derived. Actual original API volatile registers and provider scratch
stack bytes are retained without a blanket cross-branch equality claim. Complete
native CPU/State/stack proofs remain separate. Branch-local saved bytes, including
the auxiliary store at `60BF90`, have exact source provenance and subsequent
carry checks. No page mask or modification of actual captured bytes is granted.

## Build, efficiency and next closure

The [link review](../../reports/m4-lockit-build-review/link-r2/report.json) verifies
**363 literal COFFs, 27 compiled objects and two capture objects per level: 392
actual linked inputs**. The fixed native record remains 159,716 bytes; page
coverage expands to seventeen fixed and 26 external pages. The
[native worker](../../reports/m4-joint-startup124-root/execution-r2/report.json)
finishes in 175.31 seconds at O0 and 120.90 seconds at O2. Each level emits
3,399,774 canonical logical records and 13,209,324,735 payload bytes. These
worker timings do not measure whole-workflow speedup.

Failed workers and comparisons remain preserved. Corrections are additive;
the final paired rerun fixes one missing auxiliary provenance check and keeps
ordinary and loader page counters distinct. An additive
[lineage receipt](../../reports/m4-joint-startup124-root/lineage-r2/report.json)
records a stale previous-preparation path label while verifying the authoritative
physical maps through the actual native preparation and final build.

Local compile/run iterations reuse roughly 117 GB of inherited capture identities
that the worker does not consume. Changed code and fresh outputs remain physically
validated; the final acceptance above rehashes all inherited payloads. A separate
[reader efficiency proposal](../../reports/m4-lockit-source/reader-efficiency-plan-r1/proposal.md)
and [corrected accounting](../../reports/m4-lockit-source/reader-efficiency-plan-r2/report.json)
identify duplicate capture scans. Adoption requires a new compatible reader,
mutation controls and measured timings; current accepted consumers are unchanged.

The [physical next frontier](../../reports/m4-joint-startup124-root/next-frontier-r1/report.json)
checks all twenty remaining original-table roots: 4,336 unique instruction rows,
13,068 bytes, thirteen roots with FS sites, thirteen with unresolved controls
and one with floating-point sites. [Plan r10](m4-execution-plan-r10.md) targets
the separately recovered `4B7F70` tree next. Remaining providers, required
thread/exception behavior, environment/mainargs, startup scheduling and menus
must still pass before M4 closes. Earlier live helper/numeric Training tests
retain their separate scope.
