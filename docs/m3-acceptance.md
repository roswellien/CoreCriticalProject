# M3 acceptance: first native game subsystem

Accepted 2026-10-07 for the closed offline buffer-state setter and complete
strided-word-copy consumer. All twelve requirements from the frozen
[M3 subsystem plan](m3-subsystem-plan.md) are satisfied. The milestone retains
its original definition: select and recover a bounded subsystem from evidence,
compile its reachable code into the x64 host, implement its observed
dependencies, and compare outputs and state against the original on directed
and recorded workloads.

The independent [full requirement review](../reports/m3-subsystem/full-independent-review/report.json)
accepts all twelve rows. Its SHA-256 is
`7370b1f4ef80a62f32345bfd599207d9ce9ae9474c67a7c38e67c5802a34cb51`;
the accompanying [final pins](../reports/m3-subsystem/full-independent-review/final-pins.json)
have SHA-256
`90a03afeb271c85dd21fccab1b3b9d87069f77d6d8a4bec7a4db0f2cff76aef5`.
The root closure record is
[reports/m3-acceptance/root-review/report.json](../reports/m3-acceptance/root-review/report.json),
with its [pins](../reports/m3-acceptance/root-review/pins.json).
Reproduction instructions are in [M3 replay](m3-replay.md).

## Accepted component

The admitted U.S. retail MW3 1.2 image has SHA-256
`95bc2c114c9b2e5c5ada8e40ca78cc79470f862e45313ffad0d1e8e6d4d916bf`.
Both complete functions belong to that exact image:

| Entry | Complete extent | Recovered code | Role |
| --- | --- | --- | --- |
| `0x558290` | `[0x558290,0x5582BB)` | 43 bytes, 11 instructions | Sets the buffer pointer, dimensions and derived stride in five shared dwords. |
| `0x55A560` | `[0x55A560,0x55A5D7)` | 119 bytes, 46 instructions | Reads four of those dwords and performs the complete strided word-copy operation. |

All consumer branches are internal; both loops and every reachable instruction
are recovered. Neither entry has an outgoing call, import, indirect transfer,
object or callback dependency. The operation closes over its exact code, shared
globals, caller stack and buffers, persistent guest state, and checked entry and
return routes. Both bodies are statically compiled into native x64 objects at
O0 and O2. There is no interpreter, JIT fallback, fake dependency return or
expected-result implementation in the execution path.

The connection is actual shared data. No incoming game call to the consumer was
observed, and this acceptance does not invent a direct setter-to-consumer call
in MW3. The accepted surface is the complete offline component operation,
including reconfiguration and persistent buffer use. Nearby allocator, clipping,
MMX, FSIN and timer/object/vtable clusters remain outside this recovered
dependency graph and are not credited as implemented.

## Measured results

| Gate | Actual original records | Actual native O0/O2 comparisons | Defined differences |
| --- | --- | --- | --- |
| First complete setter | 15,780 | 31,560 | 0 |
| Connected component | 3,968 steps in 1,427 sequences | 7,936 steps | 0 |

The first-function result is supported by the
[canonical comparison](../reports/m3-slice/canonical-zero-metadata/comparison/report.json)
and [combined independent acceptance](../reports/m3-subsystem-review/first-function-combined-acceptance-review.json).
That independent review preserves the original separate saved-byte arithmetic
and State review. The connected result is supported by the
[normal-Windows comparison](../reports/m3-subsystem/normal-windows-comparison/report.json),
the [separate all-record/source audit](../reports/m3-subsystem/full-independent-review/record-source-audit.json)
and the root's [independent coordinate-address oracle](../reports/m3-validation/independent-connected-actual-records.json).
The separate connected reviewer imports neither the implementation corpus nor
the primary comparator.

Each original record comes from actual isolated x86 execution of the admitted
game instructions. Inputs are deterministic authored workloads; they become
offline operation recordings only when actual original outputs are saved.
These recordings are not live gameplay, renderer or menu traces. Original
per-instruction memory events and the native backend's opaque State are
unobserved in the original worker and have zero wire fields. Native events are
actual checked bridge accesses; expected oracle events are never described as
hardware traces.

The connected corpus contains 1,555 setter and 2,413 consumer steps. It covers
every conditional direction and both loop backedges/exits, signed and odd
counts, explicit/default destinations, nonpositive copy counts, positive,
negative, zero and wrapping strides, repeated and overlapping buffers,
reconfiguration, unaligned/page-boundary accesses and poisoned upper EDX.
Sequences contain up to sixteen steps. Reached positive loops admit at most
sixteen rows and thirty-two columns, with every accessed word checked before
execution. Unused pointers are not required to be mapped. All twelve masked
x87 PC/RC modes, all eight TOP values, physical/full tags, admitted logical
raw80 storage, status, MXCSR and eight XMM vectors are covered.

All 16,384 mapped bytes compare before and after every connected step. This
includes stack saves, locals and cleanup, all five persistent globals, buffer
canaries and unchanged bytes. Native full 3,504-byte State also preserves every
byte outside the reviewed CPU/flag/PC effects and persists through caller CPU
overlays. The overlap oracle uses mutable memory: later reads see earlier
writes. Independent sensitivity checks detect an immutable-source copy model,
wrong negative-odd stride rounding and loss of EDX's upper half.

## Full requirement acceptance

The required proof text below is unchanged from the frozen plan. Every row is
accepted by the linked independent twelve-row review; the isolated first setter
is a prerequisite, not the definition of M3 completion.

| ID | Required proof | Disposition |
| --- | --- | --- |
| M3-01 | Explicit subsystem operation/entry boundary selected from actual code and shared-data evidence, with caller observations and unknown runtime use distinguished. Confirm that the two-entry operation is the accepted bounded component. | Accepted: complete data-connected operation boundary; unknown game use remains explicit. |
| M3-02 | Exact image/function identities, complete instruction/CFG recovery, all branch destinations, loop bounds, return contracts and any shared/tail blocks for every admitted entry. | Accepted: both complete extents, all instructions and internal branches reviewed. |
| M3-03 | Close every reachable code, import, global, buffer, object and routing dependency. Unknown required paths stop with guest address/reason; broader excluded clusters remain explicit. | Accepted: reachable closure has no external call/API/object dependency; checked routes and mappings fail visibly. |
| M3-04 | Offline lifting and native x64 compilation of every reachable admitted instruction at O0/O2. No interpreter, JIT fallback, fake dependency result or expected-result execution path. | Accepted: exact static native objects and source/tool/IR identities. |
| M3-05 | Full guest ABI proof: GPR/subregisters, EIP/ESP, argument cleanup, all defined exit flags, reviewed undefined flags and preservation of admitted live floating-point/vector state and observable host environment, with excluded observations explicit. | Accepted: complete ABI, defined flags and admitted live state; immediate observable host restoration measured separately. |
| M3-06 | Checked guest page initialization/permissions, global persistence, caller buffer lifetimes, exact stack writes, 32-bit arithmetic, every access span and actual sequential alias effects; compare all mapped bytes. | Accepted: full pages and actual ordered native access events match the separate sequential oracle. |
| M3-07 | Implement any observed environment/API dependency required by the accepted operation, or prove its absence from the closed entries. Do not claim the upstream game allocator or timer/object caller is implemented. | Accepted: exact complete code proves API absence within this boundary. |
| M3-08 | Directed and deterministic seeded workloads covering every branch, loop termination, signed/odd dimensions, strides, zero-copy cases, alias, unaligned and boundary accesses, varying entry state and explicit work limits. | Accepted: frozen directed/seeded sequences and observed branch coverage. |
| M3-09 | Hash-bound recordings of actual original connected operation sequences with complete input/output state and per-step memory provenance; explicitly identify offline recordings versus any genuinely observed game trace. | Accepted: actual offline original step records with persistent pages/state; no gameplay claim. |
| M3-10 | Original/native O0/O2 per-step and final full-state comparisons for functions and complete sequences, zero unexplained differences, plus a separate exact oracle and observer review. | Accepted: zero defined differences and independent complete saved-record reviews. |
| M3-11 | Meaningful code/image/source/metadata/routing/input admission controls and comparator corruptions; invalid or unsupported execution rejects before entry/output. Test overlap order, upper EDX preservation, wrong count rounding and stack/flag corruption. | Accepted: causally verified input diagnostics and effective comparator/adapter controls. |
| M3-12 | Independent full-scope acceptance, replayable source/tool/artifact pins, preservation of prior M1/M2 successes and failures, appropriate ordinary regression checks and asset-free public tooling with proprietary outputs ignored. | Accepted: all twelve rows, frozen replay pins, preserved history and eight passing ordinary groups. |

## Control evidence and preservation

The first gate has 145 observer controls: 142 corruptions reject and three
explicitly unobserved/undefined changes are accepted. It has 117 meaningful
named input rejections. Thirteen original negative runs initially stopped at
address reservation rather than the named input check; those logs remain
preserved. Fresh runs of the same pinned worker/code/image/invalid requests
reached the intended diagnostics with exit 1 and no output, completing the
117 proofs as 104 prior causal checks plus thirteen supplemental checks.
The [causal supplement](../reports/m3-subsystem-review/first-causal-controls/report.json)
does not add thirteen distinct inputs to the 117, and no positive workload was
rerun to repair this evidence gap.

The connected gate has 206 observer controls: 201 corruptions reject and five
explicit exclusions are accepted. All 216 actual input controls, seventy-two
per worker, reach their intended diagnostics with exit 1 and no output.
Mapping collisions or unrelated failures are not credited as those input
proofs. Code/image, input extent, unsafe state, routes, access/alias and work
limits, zero-metadata policy and late-record validation are checked.

All eight [ordinary regression groups](../reports/m3-validation/authorized-ctest/report.json)
pass with native LLVM adapter tests enabled. The independent final review
rehashes the prior M1/M2 evidence: 3,349 unique bound files and both manifest
files remain unchanged. This is preservation verification, not a claim of new
historical worker executions. Public tooling is asset-free; original media,
game-derived extraction/IR/disassembly/objects and complete results remain in
ignored local directories. Fresh runs refuse to overwrite frozen evidence.

## Floating-point observation boundary

Guest FOP, FIP and FDP must be zero. Every nonzero requested field rejects
before any body runs. Actual FX and legacy ENV metadata must equal zero at
entry and exit; raw records are not normalized and defined differences are
not masked away. All admitted numerical, raw storage, status/tag/TOP, control,
MXCSR and vector preservation checks remain in place.

This boundary follows preserved measurements, not a claim that integer
instructions clear x87 metadata. Two original first-function records lost
nonzero legacy metadata while other state matched. The separate
[asset-free scheduling probe](../reports/m3-subsystem-review/metadata-scheduling-probe/final-review.json)
decoded 69,216 actual intervals: all 60,000 immediate captures retained the
seed, all 8,704 scheduling-API intervals lost it, and 401 of 512 API-free
contended integer intervals lost it. Both FXRSTOR and explicit FLDENV seed
paths reproduced the loss. Numerical/storage/vector fields remained intact.
The exact kernel or processor mechanism is not established.

The host scope saves both FX state and the actual legacy environment. It
checks restoration immediately after normal and contained status-error exits,
including observable low-32 host FIP/FDP/FOP. First-function compiled controls
provide 48 such measurements across both native builds; connected controls
provide 96 and vary actual host CW across all twelve settings. This does not
guarantee nonzero metadata survives unrelated Windows descheduling. High-64
host pointer metadata, arbitrary escaping Windows exception unwinding,
unmasked guest traps and unsupported FP encodings remain outside the claim.
The earlier FX-only observation/restoration defect, representation failures,
nonzero-metadata records, mapping failures and pre-zero connected diagnostic
recordings remain preserved, with their historical scopes distinguished.

## Next milestone

M4 is native startup and menus: a project-built x64 executable must load admitted
user data, initialize its required services, show correct menus and respond to
input. File/configuration, graphics, input and audio dependencies need explicit
implementations; required unresolved paths must fail visibly. This M3 offline
component result supplies a validated native runtime operation and recovery
process. It does not establish native startup, a playable mission, renderer
behavior or game-wide compatibility.
