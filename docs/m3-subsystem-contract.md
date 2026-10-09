# M3 shared buffer-state and strided-word-copy contract

Status: authored experiment contract, 2026-10-07. The two-entry component is a
selected bounded candidate from the admitted MW3 image. M3 remains open until
the complete [subsystem plan](m3-subsystem-plan.md) is satisfied and independently
accepted. Inputs defined here are authored workloads, not gameplay recordings.
Actual original per-call outputs become offline operation recordings only after
the original instruction bodies have executed and their results are saved.

## Exact entries and closure

The admitted U.S. retail 1.2 image SHA-256 is
`95bc2c114c9b2e5c5ada8e40ca78cc79470f862e45313ffad0d1e8e6d4d916bf`.
Every original and native run requires this full identity, the complete private
code identities and exact reviewed metadata before execution.

| Entry | Extent / size | Code SHA-256 |
| --- | --- | --- |
| Setter `0x558290` | `[0x558290,0x5582BB)` / 43 bytes | `fd939ea8ce1dc550fd08e7f2c2a2178ff063435cc7a8f5c5aafbf13eff32feaa` |
| Consumer `0x55A560` | `[0x55A560,0x55A5D7)` / 119 bytes | `072fed4d6b5efe0ff7c3bfa1733c848a11f3ba5402fd05d18c2f1ebf8ff57adf` |

The setter's five shared dword writes are actual dependencies of the consumer,
which reads four of them at five static sites. Both complete functions have no
outgoing calls or imports; all consumer branches are internal. Code, global
storage, the caller's stack and buffers, checked return routing, and persistent
guest state are the entire selected dependency boundary. Broader allocation,
timer/object, MMX, sine and rendering paths remain outside this experiment.
No incoming runtime consumer call is asserted. The subsystem plan records the
actual static incoming-reference limitation and the recovered ABI/CFG.

## Persisted mappings and caller setup

Four writable guest pages are serialized in this order:

| Region | Guest address / size | Initial bytes |
| --- | --- | --- |
| Stack | `0x20001000`, 4,096 | Byte `i`: `(i*37 + seed) mod 256`. |
| Shared globals | `0x72C000`, 4,096 | The admitted PE's complete virtual zero-filled page. |
| Buffer block | `0x20003000`, 8,192 | Byte `i`: `(i*73 + (seed>>8) + (i>>8)*19 + 0x5B) mod 256`. |

These are 16,384 bytes total. The two buffer pages form one contiguous checked
region, so an unaligned word crossing their internal boundary is valid. Pages
outside the explicit mappings are not made valid by guest pointer arithmetic.
The mappings, contents, shared globals and non-CPU guest state persist through
all steps of one sequence. Each new sequence gets its own defined initial state.

Before each call the authored caller sets all eight GPRs, flags and entry PC
from that step. It writes the return sentinel `0x10000100` at entry ESP. A setter
step also writes its two dword stack arguments at ESP+4 and ESP+8. A consumer
step writes only the return dword; its unused request argument fields must be
zero. This caller setup is reported separately from function execution and is
excluded from the native instruction-memory event stream. Other native State
bytes, floating-point state and vectors must persist without reseeding per step.

Setter frames require `[ESP,ESP+12)` within the stack page. Consumer frames
require `[ESP-24,ESP+4)` within that page, including unaligned ESP. The frame,
globals, code and return trampoline cannot alias the admitted buffer accesses.
Both entries retain the actual 32-bit guest return convention. A setter returns
at ESP+12; a consumer at ESP+4. Unknown entry/return targets fail visibly.

## Arithmetic and memory observations

The [whole-function plan](m3-subsystem-plan.md#shared-data-and-abi) defines the
setter and consumer register/argument contracts. The independent measurement
oracle uses integer arithmetic and mutable byte memory. In particular, the
setter's signed half-stride truncates toward zero; the consumer's signed
dimension halves are arithmetic shifts, rounding negative odd values downward.

A consumer may run at most sixteen positive outer iterations and thirty-two
positive inner iterations per outer iteration: at most 512 read/write pairs.
If the outer count is nonpositive, no inner work occurs and the unused inner
count is not restricted to thirty-two. Nonpositive inner counts still allow
the bounded outer loop's real pointer, counter and stack effects. Pointers that
are never dereferenced need not denote a mapped buffer. Admission rejects any
reached word read/write outside the isolated buffer block, any invalid frame,
wrapping access span or work-budget excess before original/native entry.

All pointer additions retain 32-bit guest wrapping behavior. The two-byte
access itself must fit the mapped region and must not straddle the 32-bit limit.
Negative, zero and positive strides are valid when every reached access fits.
Source and destination buffers may overlap. Copy events occur in increasing
row/column order, with each actual source read preceding its destination write.
Later reads observe earlier writes. A bulk copy from the initial source or an
oracle built from immutable initial values is outside the contract.

Every result compares all eight entry/exit registers, return EIP/ESP and the
complete four-page memory image before and after each call. This includes every
stack push/pop/local access, the retained fifth global, untouched buffer bytes
and surrounding canaries. Partial DX writes preserve EDX's upper sixteen bits.
Default-destination selection substitutes the stride only in its local slot;
it does not overwrite entry EDX.

Both entries admit entry arithmetic flags and DF with fixed bit1/IF set:
`0x202 | selected bits of 0xCD5`. TF, privileged, reserved and other unreviewed
flag configurations are rejected. Setter exit defined mask `0xCC5` covers
CF/PF/ZF/SF/DF/OF; its final SAR AF is undefined. Native AF may be the reviewed
arbitrary zero without a compatibility claim. Consumer exit mask `0xCD5` also
includes defined AF. Its final six arithmetic flags come from adding eight to
the frame-cleanup ESP value, before RET. AF must not be removed from that check.

## Live floating-point, vectors and complete State

Each sequence admits the twelve masked x87 control words
`0x007F | PC<<8 | RC<<10`, with PC encodings 0, 2 and 3 and RC encodings 0..3.
The initial FXSAVE-format payload carries arbitrary admitted TOP/physical FTW,
coherent full physical tags, masked sticky/condition flags, zero FOP/FIP/FDP metadata,
logical raw80 storage and eight XMM vectors. Occupied extended values are
canonical finite normals, signed zero, infinity or quiet NaN; occupied signaling
NaNs, denormals and noncanonical encodings remain rejected. Empty-slot payloads
remain preserved storage, not numerical operands. Guest MXCSR is `0x1F80`;
selectors, reserved bytes and unsupported host-width fields are zero.

Nonzero guest FOP, FIP or FDP requests are rejected before any operation runs.
This is a measured host observation boundary, not an architectural claim that
integer instructions clear these fields. The preserved first-function
`reports/m3-slice/canonical-broker/comparison/report.json` has two original
records in which nonzero legacy metadata became zero with all other observed
state intact. The asset-free Win32 experiment under
`reports/m3-subsystem-review/metadata-scheduling-probe/` reproduced the loss
across API-free integer-only intervals with a competing thread pinned to the
same processor, as well as scheduling API calls. Its immediate captures retain
the seed. This demonstrates an external observation loss; the exact Windows or
processor mechanism is not established by this experiment. Independent decoding
of its 69,216 records found 60,000 immediate captures retaining the seed, all
8,704 scheduling-API captures losing it, and 401 of 512 API-free contended
integer intervals losing it. Entry metadata, numerical/storage/vector state and
observable host restoration were correct in all 69,216 records. Both FXRSTOR
and explicit FLDENV seed paths reproduced the interval loss.

The canonical sequence corpus retains all counts, numerical/raw80 storage,
control/status/TOP/occupancy and vector patterns while admitting only zero
metadata. Actual FXSAVE and FNSTENV metadata must equal zero at both boundaries.
No raw observation is normalized, substituted or exempted from this equality.
The earlier nonzero-input measurements remain diagnostic failure evidence.

The original worker captures actual hardware state before/after each call and
restores its host floating-point environment. CW/status/occupancy, logical raw
storage, MXCSR and XMM use FXSAVE observations. Guest FOP/FIP/FDP equality uses
actual FNSTENV observations. FXSAVE and FXSAVE64 returned zero metadata in the
preserved nonzero diagnostic measurements, while FNSTENV usually retained the
seed but sporadically lost it. Saved FX/ENV bytes are never rewritten to
fabricate metadata, and zero metadata equality is mandatory in both views.
The native worker captures actual
guest State and serialized architectural fields, with its observation mode
explicitly identifying that origin. It must not compute expected floating-point
outcomes in the observer. Neither integer body may alter the admitted x87
control/status/TOP/tags/logical payloads, FOP/FIP/FDP, XMM bytes or guest MXCSR.
Native serialized State has 3,504 bytes; every byte outside the exact reviewed
CPU/flag/PC write set must remain unchanged across each body and caller overlay.
Full hardware/native byte-structure equality is not implied for padding or
backend-specific representation.

The first measurement also exposed a host-isolation defect: FX-only restoration
after FNINIT loses observable metadata on this host. The repaired scope therefore
saves and restores both FX state and the actual legacy environment, including
low-32 FIP/FDP and FOP, and checks both observable views after normal and contained
error-status exits. High-64 host pointer metadata is not independently observable
through this legacy view and is explicitly excluded from the restoration claim.
Earlier frozen M2 FX-only controls retain their historical observed scope; they
do not prove this newly discovered metadata guarantee. The original failed
measurement and its workers must remain preserved.

Observable host state restoration, checked-memory accesses and full native State
preservation need compiled controls and actual measurements. The first setter
gate's tests are prerequisites, not automatic credit for the consumer or
connected sequence. The contract makes no claim that general x87, MMX/SSE game
instructions, exceptions, threads, callbacks or graphics are implemented.

## Wire protocol

Headers are 24 bytes, `<8s4I>`, with magic `MW34S3RQ` for requests or `MW34S3RS`
for results, version 1, count, record size and pointer bits. Input pointer bits
are 32; output bits identify actual worker architecture, 32 or 64. Request count
is the number of sequences. Result count is the sum of all admitted step counts,
with actual records in sequence order then step order. Exact header/length and
trailing-byte validation precede execution/output.

Each request is exactly 1,296 bytes: a sixteen-byte `<4I>` prefix containing
step count, memory seed, full physical tag word and reserved zero; the 512-byte
initial FX payload; and sixteen fixed 48-byte step slots. A step is `<12I>`:
eight GPRs in EAX,ECX,EDX,EBX,ESP,EBP,ESI,EDI order, flags, EIP, and two argument
dwords. Step count is 1..16. Every unused slot is all zero. Every sequence and
all reached step spans are preflighted before any code in the batch executes.

Each actual step result is 73,728 bytes:

| Offset | Size | Observation |
| --- | --- | --- |
| 0 / 40 | 40 each | Actual CPU before / after. |
| 80 | 24 | Six dwords: sequence index, step index, status, observation mode, host-restored indicator, trace count. |
| 104 / 16,488 | 16,384 each | Full mapped memory before / after. |
| 32,872 / 33,384 | 512 each | FX before / after. |
| 33,896 / 33,924 | 28 each | Environment before / after. |
| 33,952 / 37,456 | 3,504 each | Native State before / after; original mode does not claim this host representation. |
| 40,960 | 32,768 | 2,048 fixed sixteen-byte memory-event slots. |

An event is four little-endian dwords: address, value, width, operation.
Operation 0 is read and 1 is write; width is the actual two or four bytes.
Native checked bridges record actual accesses in execution order, including
frame pushes/pops, local/global accesses and the RET read. Count overflow fails;
events cannot be truncated. Every unused event slot is zero.

Original mode has trace count zero and all event slots zero. Original
instruction-level memory accesses are **not observed by this protocol**. Native
events are checked against the independent sequential oracle; full original
overlap outcomes independently corroborate ordering. Expected oracle events
are never labeled hardware traces. Recordings include actual per-entry inputs
and outputs, not a claim about unobserved original per-instruction memory events.

## Corpus and controls

The authored corpus uses deterministic seed `0x340055A560`. Its exact counts,
categories, request SHA-256 and maximum trace/step counts must be computed from
the frozen file and saved in each report. Directed workloads cover an initially
unconfigured no-copy call followed by real configuration; negative, zero, one,
odd and bounded maximum dimensions; default and explicit destination selection;
negative/zero/positive strides; in-place and partial overlap; repeated copies;
reconfiguration; unaligned and page-boundary accesses; EDX upper-half poison;
all twelve control words, all TOP values, both extended-value patterns and
occupied/empty/noncontiguous tags. Seeded connected sequences preserve actual
modified buffers and globals, and a sixteen-step workload exercises suffix
validation and the complete work budget.

Meaningful controls must reject changed image/function bytes, unknown entry or
return routing, wrong/truncated/trailing headers, bad counts, nonzero unused
steps, unsafe flags, bad stack/word spans, global/stack/code alias, excess work,
incoherent tags and unsupported FP encodings before output. Comparator
corruptions must detect CPU/global/stack/buffer changes, lost EDX upper bits,
wrong signed-half behavior, wrong final consumer AF, reset persistent data,
reordered/omitted/changed native events, spurious original trace claims, changed
occupied or empty payloads, vectors, tags and control/status metadata. Excluded
setter AF and backend padding must have explicit false-positive controls.

The recipe binds exact source/tool/artifact/worker/code/input/output identities,
historical M1/M2 acceptance and the independent recovery review. Passing requires
actual original and native O0/O2 records with zero defined differences, complete
recorded operation sequences and separate independent review. Unsupported cases,
unavailable input and failed execution remain failures. This gate establishes
the accepted bounded component only; it does not establish native game startup,
game rendering, observed consumer use during play or whole-game compatibility.
