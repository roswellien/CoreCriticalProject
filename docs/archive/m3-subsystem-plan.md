# M3: first native game subsystem

Status: recovery plan, 2026-10-07. M1 and the bounded M2 gate are complete.
M3 is not complete. The first M3 implementation step is the exact whole game
function at `0x558290`; passing that function alone does not satisfy M3.

The original [milestone definition](../project-milestones.md) requires selecting
and recovering a bounded subsystem from evidence, compiling its reachable code
into the x64 host, implementing its observed dependencies, and comparing outputs
and state against original execution on directed and recorded workloads. This
plan preserves that definition and the [runtime architecture](../architecture.md).
Native startup, menus and a playable Training mission belong to M4 and M5.

## Candidate and evidence

The proposed first subsystem is the shared buffer-state setter and a complete
strided-word copy operation that consumes its state. The boundary is two actual
entries in the admitted game image and their shared data, caller-owned buffers,
and guest stacks. The descriptive names below are provisional; no recovered
pixel format, game screen, gameplay purpose or runtime caller is asserted.

| Entry | Complete extent | Size / instructions | SHA-256 | Role |
| --- | --- | --- | --- | --- |
| `0x558290` | `[0x558290,0x5582BB)` | 43 bytes / 11 | `fd939ea8ce1dc550fd08e7f2c2a2178ff063435cc7a8f5c5aafbf13eff32feaa` | Writes five dwords of shared buffer state. |
| `0x55A560` | `[0x55A560,0x55A5D7)` | 119 bytes / 46 | `072fed4d6b5efe0ff7c3bfa1733c848a11f3ba5402fd05d18c2f1ebf8ff57adf` | Reads four of those dwords and performs a complete register-selected word-copy operation. |

Both identities are bound to the admitted U.S. retail 1.2 image SHA-256
`95bc2c114c9b2e5c5ada8e40ca78cc79470f862e45313ffad0d1e8e6d4d916bf`.
The consumer has ten reviewed basic blocks, two loops, one return, and no
outgoing call, import, indirect transfer, floating-point, MMX or SSE instruction.
All 46 instructions are statically reachable from its entry. Every instruction
and internal branch target was checked against the actual image bytes.

The setter has multiple raw-verified direct-call candidates in the executable.
One reviewed caller at `0x5995B0` calls it at `0x5995DD` after obtaining values
from four global getters. This supports the setter's buffer-state role but does
not establish the meaning of each field. The consumer demonstrably reads the
setter's actual storage; it is not an authored imitation of a game operation.

The current whole-image linear branch scan, an additional executable-section
E8/E9 encoding scan, and a literal pointer scan found no incoming reference to
`0x55A560`. Those scans do not exclude computed or indirect references and do
not prove the function unused. No execution of this consumer during gameplay
has been observed. The selected workload boundary therefore explicitly invokes
the two entries as offline buffer operations; it does not invent a direct call
between them or present the sequence as a recovered gameplay call chain.

This is a meaningful candidate boundary because it includes a configuration
producer, a complete data consumer, persistent shared state and observable
buffer transformations across successive calls. The first setter proof is a
prerequisite. The enclosing gate must then prove actual connected operation
sequences, dependency closure and every reachable consumer path. If recovery
shows a required dependency outside this boundary, the implementation must add
and prove it or keep M3 open. Passing a renamed setter experiment is insufficient.

Private recovery evidence:
[dependency reconnaissance](../../reports/m3-subsystem-review/dependency-reconnaissance.json)
and [complete consumer CFG/data review](../../reports/m3-subsystem-review/candidate-contract-review.json).
Full disassembly and proprietary instruction bytes remain in ignored reports.

## Shared data and ABI

The setter's reviewed M2 planning contract remains the starting point; its
original/native execution proof is new M3 work. See the
[next-slice contract](m2-next-slice-context.md). It receives ECX, EDX and two
stack dwords. It returns with `RET 8`, so its entry ESP advances by twelve bytes.
It writes `0x72C1E4`, `0x72C1E8`, `0x72C1EC`, `0x72C1F0` and `0x72C1F4`.
The last field is the signed fourth input divided by two with truncation toward
zero. The exact EAX/EDX results, other registers, defined final flags, stack
reads and all five writes must pass the first function gate. Its final AF is
architecturally undefined and needs an explicit reviewed policy rather than a
masked accidental mismatch.

| Storage | Setter source | Consumer use |
| --- | --- | --- |
| `0x72C1E4` | Entry ECX | Source address; also default destination when the consumer's ECX is zero. |
| `0x72C1E8` | Entry EDX | Signed value whose arithmetic half supplies the inner loop count. |
| `0x72C1EC` | First stack argument | Signed value whose arithmetic half supplies the outer loop count. |
| `0x72C1F0` | Second stack argument | Retained state; not read by this consumer. Its write is still part of the operation. |
| `0x72C1F4` | Signed truncating half of second stack argument | Source row stride in word units; also default destination row stride. |

The globals occupy the writable `0x72C000` page in the admitted image's
zero-filled `.data` tail. The harness must reproduce this mapping and
initialization explicitly. It must compare the entire mapped global page,
including the retained field and surrounding canaries, rather than fabricate
values directly in the consumer's observer.

The consumer receives a destination address in ECX and a destination stride in
EDX. With ECX zero it takes both destination address and local destination
stride from the shared state. The local substitution does not replace the EDX
register. There are no stack arguments. With entry ESP `s`, it writes a
24-byte frame below the return dword, restores EBX, EBP, ESI and EDI, and returns
with ESP `s+4`. Frame bytes remain written after return; the comparison must
include them. The source and destination buffers must be disjoint from this
frame, its return slot, the global page and executable pages in the initial
admitted domain.

At consumer exit, EAX is zero if the outer loop ran and otherwise retains its
signed half-count. ECX contains the shared source stride if the outer loop ran
and otherwise retains entry ECX. EDX is unchanged when no inner copy occurred;
otherwise its low sixteen bits contain the last word read while its upper
sixteen bits preserve entry EDX. These subregister effects need directed
controls. All six final arithmetic flags come from the frame-cleanup ADD;
DF is preserved. Intermediate undefined AF values are overwritten before
return and have no reviewed consumer. Admitted x87/vector and observable host
environment preservation must be measured even though neither function uses
those units; the experiment contract records metadata observation limitations.
The guest domain requires zero FOP/FIP/FDP and rejects nonzero requests before
entry. A preserved asset-free x86 scheduling probe reproduced loss of nonzero
metadata across an API-free integer interval on this host while numerical state
remained unchanged. Actual zero metadata is still compared exactly; raw records
are not normalized. Host restoration has separate actual nonzero-metadata
normal/error controls, with its observable low-32 scope retained.

## Complete consumer control flow

The only branch destinations are instruction boundaries inside the admitted
119-byte extent. Fallthrough and both directions of every conditional branch
must be compiled and exercised.

| Branch site | Taken destination | Other destination / meaning |
| --- | --- | --- |
| `0x55A573` | `0x55A582` | `0x55A575`; selects explicit versus default destination. |
| `0x55A580` | `0x55A584` | Unconditional join after default selection. |
| `0x55A595` | `0x55A5CF` | `0x55A597`; skips copying for a nonpositive outer count. |
| `0x55A59D` | `0x55A5B4` | `0x55A59F`; skips the inner loop for a nonpositive inner count. |
| `0x55A5B2` | `0x55A5A5` | `0x55A5B4`; inner counter backedge. |
| `0x55A5CD` | `0x55A59B` | `0x55A5CF`; outer counter backedge. |

The return is at `0x55A5D6`; it has no argument cleanup. There is no outgoing
code dependency from the consumer's CFG. The selected operation has no observed
API dependency, allocation request, vtable, callback or external object access
inside either entry. A harness that seeds valid caller-owned mappings is an
explicit test environment, not an implementation of the game's unrecovered
allocator, caller or startup path.

## Memory order and bounded domain

Let `R` be the arithmetic half of signed storage `0x72C1EC`, and `C` the
arithmetic half of signed storage `0x72C1E8`. This differs from the setter's
truncating signed division for its stride field. The consumer takes
`max(R,0)` outer iterations and `max(C,0)` inner iterations per outer iteration.
Zero, one, negative and odd input dimensions are therefore important cases.

For an admitted positive copy, row `r` and column `c` read a two-byte word at
`u32(source + 2*source_stride*r + 4*c)` and then write that word at
`u32(destination + 2*destination_stride*r + 2*c)`. All pointer arithmetic is
32-bit guest arithmetic. The source stride is read again each row, while the
destination stride remains in the local frame. The simple address description
assumes the admitted buffers cannot overwrite the global stride or frame.
Global/stack/code alias is rejected in the initial domain; it cannot silently
be treated as ordinary buffer alias.

Source/destination alias within caller-owned buffer mappings is part of the
candidate's useful contract. Reads and writes occur in increasing row order,
then increasing column order, with each read preceding its matching write.
An overlapping write can change a later source read. Neither an oracle nor the
native implementation may substitute a copy from a snapshot of the initial
source, reorder overlapping writes or use a bulk-copy assumption. Default
in-place copying, identical addresses with differing strides, overlapping
offsets and row-crossing effects need separate cases.

Pre-entry admission must establish the complete writable stack frame and
return slot, required global reads, and every reached two-byte read/write span.
It must reject spans outside mapped permissions or crossing the 32-bit address
limit. The arithmetic may wrap, but an individual access may not straddle an
unmapped or wrapping span. Negative strides, unaligned word accesses and
unaligned stacks can be admitted when every actual access remains valid.

The final experiment must set an explicit deterministic work budget before
running original code. Huge positive dimensions cannot enter a worker and be
reported as successful after a timeout. Nonpositive-count cases still execute
their real register, flag, pointer-update and stack effects. All mapped stack,
global and buffer pages are compared byte for byte, including untouched data.
Specific limits and page layouts remain pending the consumer protocol.

## Operation recordings and comparison

The subsystem gate must include original execution of complete sequences, not
just unrelated function vectors. A minimum meaningful recording covers initial
state setup, configuration through the actual setter, default and explicit
destination operations, repeated copies using persistent data, reconfiguration
to different dimensions/strides, overlapping buffers, and noncopying branches.
Both functions must execute through the same address registry and checked
memory model used for their compiled native entries. The resulting five globals
must feed the consumer without expected-value substitution.

Each recording must preserve complete entry CPU/flags, mapped memory, return
context and live noninteger state, the ordered selected entries, and complete
actual original outputs after each step. These are **offline original-operation
recordings** when produced by the isolated x86 worker. They may satisfy this
bounded comparison contract but must never be described as captured gameplay,
an observed in-game consumer call, native game rendering or mission stability.
Any later live-game recording needs independent identity and full-state
provenance; a partial logger row alone is insufficient.

Replay each directed, seeded and recorded sequence against original x86 and
compiled x64 O0/O2. Compare per-step and final state, pages, ordered memory effects
and the defined observations from the ABI. A separate independent oracle must
model the mutable overlap behavior and subregister/stack effects. Runtime
observers only capture actual execution; they do not compute expected outcomes.
Sequence traces and complete results remain local and hash-bound.

## Deferred clusters

The surrounding buffer-processing region is larger than this candidate.
It includes allocation/cleanup, clipping and other kernels, indirect selection
through `0x72C1F8`, MMX implementations at `0x558380`/`0x558460`, and floating-point
paths including FSIN. Those are separate unresolved code and policy dependencies.
Their proximity does not make them necessary callees of this no-call operation,
and this plan does not claim they are implemented.

The timer/object path at `0x5996D0` → `0x5995B0` remains outside the selected
boundary. The complete latter function has seven direct calls, accesses an
object, writes its fields and invokes unresolved vtable slot `+8`. The wrapper
also needs a real timer import and unadmitted floating-point forms. Four global
getters and the setter do not close that path. No stubbed success, guessed
virtual return or borrowed M2 authored fixture may fill those gaps.

## Full M3 acceptance checklist

Every row remains pending until its actual evidence is reviewed. The first
function report can discharge prerequisites for a row, not the whole row.

| ID | Required proof |
| --- | --- |
| M3-01 | Explicit subsystem operation/entry boundary selected from actual code and shared-data evidence, with caller observations and unknown runtime use distinguished. Confirm that the two-entry operation is the accepted bounded component. |
| M3-02 | Exact image/function identities, complete instruction/CFG recovery, all branch destinations, loop bounds, return contracts and any shared/tail blocks for every admitted entry. |
| M3-03 | Close every reachable code, import, global, buffer, object and routing dependency. Unknown required paths stop with guest address/reason; broader excluded clusters remain explicit. |
| M3-04 | Offline lifting and native x64 compilation of every reachable admitted instruction at O0/O2. No interpreter, JIT fallback, fake dependency result or expected-result execution path. |
| M3-05 | Full guest ABI proof: GPR/subregisters, EIP/ESP, argument cleanup, all defined exit flags, reviewed undefined flags and preservation of admitted live floating-point/vector state and observable host environment, with excluded observations explicit. |
| M3-06 | Checked guest page initialization/permissions, global persistence, caller buffer lifetimes, exact stack writes, 32-bit arithmetic, every access span and actual sequential alias effects; compare all mapped bytes. |
| M3-07 | Implement any observed environment/API dependency required by the accepted operation, or prove its absence from the closed entries. Do not claim the upstream game allocator or timer/object caller is implemented. |
| M3-08 | Directed and deterministic seeded workloads covering every branch, loop termination, signed/odd dimensions, strides, zero-copy cases, alias, unaligned and boundary accesses, varying entry state and explicit work limits. |
| M3-09 | Hash-bound recordings of actual original connected operation sequences with complete input/output state and per-step memory provenance; explicitly identify offline recordings versus any genuinely observed game trace. |
| M3-10 | Original/native O0/O2 per-step and final full-state comparisons for functions and complete sequences, zero unexplained differences, plus a separate exact oracle and observer review. |
| M3-11 | Meaningful code/image/source/metadata/routing/input admission controls and comparator corruptions; invalid or unsupported execution rejects before entry/output. Test overlap order, upper EDX preservation, wrong count rounding and stack/flag corruption. |
| M3-12 | Independent full-scope acceptance, replayable source/tool/artifact pins, preservation of prior M1/M2 successes and failures, appropriate ordinary regression checks and asset-free public tooling with proprietary outputs ignored. |

A passing isolated setter establishes the first whole-function step. A passing
complete consumer establishes another function step. M3 completes only after
the accepted connected boundary satisfies all twelve rows and its original
recorded workloads. Effort and dates remain unset; recovery findings decide
whether this boundary can close without additional required code.
