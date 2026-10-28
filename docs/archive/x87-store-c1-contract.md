# Bounded final x87 store C1 contract

Established 2026-10-07. This separate offline experiment uses two authored
fixtures and four admitted input profiles. This new gate strengthens the final FSTP status observation. Earlier integer and x87 sources,
contracts, workers and reports remain frozen. No game session is required.

## Fixtures and deterministic input profiles

Start at `0x10000000`; return to `0x10000100`.

| Profile | Complete sequence | Exact bytes | Vectors per CW | Cases |
| --- | --- | --- | --- | --- |
| mul64 | `FLD qword [ECX]; FMUL qword [ECX+8]; FSTP qword [EDX]; RET` | `DD01DC4908DD1AC3` | 96 | 1152 |
| div64 | `FLD qword [ECX]; FDIV qword [ECX+8]; FSTP qword [EDX]; RET` | `DD01DC7108DD1AC3` | 96 | 1152 |
| mul-special | same multiplication fixture | same bytes | 40 | 480 |
| div-special | same division fixture | same bytes | 40 | 480 |

CW is `0x007F | (PC << 8) | (RC << 10)`, PC0/2/3 and RC0/1/2/3.
All exceptions are masked. Test the Cartesian product of twelve modes and
each profile's exact ordered raw binary64 pair list once. Reject every other
CW, vector, count and instruction sequence. The first operand is the loaded
destination and the second is the memory arithmetic operand, so division
means first divided by second.

For finite profiles, expand the following twenty-four positive magnitude pairs
with signs ++, +-, -+, --, in that order. The exact bit encodings are public
constants in the new comparator and protocol.

| Index | First magnitude | Second magnitude |
| --- | --- | --- |
| 0-8 | (1,1), (1,2), (2,1), (1,3), (3,1), (2,3), (3,2), (5,7), (7,5) | shown as pairs |
| 9 | 1+2^-23 | 1+2^-24 |
| 10 | 1+2^-24 | 1+2^-24 |
| 11 | 1+2^-52 | 1+2^-52 |
| 12 | 1-2^-53 | 1+2^-52 |
| 13 | 1-2^-53 | 1-2^-53 |
| 14 | 1+2^-27+2^-51 | 1+2^-26 |
| 15 | 1+2^-52 | 3 |
| 16 | 3 | 1+2^-52 |
| 17 | 1.5 | 1.5 |
| 18 | 2^500 | 2^500 |
| 19 | 2^-500 | 2^-500 |
| 20 | 2^500 | 2^-500 |
| 21 | 2^-500 | 2^500 |
| 22 | 2^500 | 3 |
| 23 | 2^-500 | 3 |

All finite operands and results remain nonzero normal binary64 at every mode;
no store overflow/underflow or denormal operand is admitted in this profile.
The finite matrix distinguishes PC24, PC53 and PC64, including legitimate
double rounding. Under nearest, multiplication pair14 stores
`0x3ff0000006000003` at PC53 and `0x3ff0000006000002` at PC64.
Division pair16 stores `0x4007ffffffffffff` and `0x4007fffffffffffe` respectively.

For special profiles, expand (0,1), (1,0), (0,0), (0,infinity),
(infinity,0), (infinity,1), (1,infinity), (infinity,infinity) with the same
four signs. Append each of the following NaNs paired with +1 in both operand
positions, in order: `0x7ff8000000001234`, `0xfff8000000004321`,
`0x7ff0000000001234`, `0xfff0000000004321`. This gives forty distinct pairs.
There is never more than one NaN input. Two-NaN selection/ties, unlisted
payloads, range boundaries and subnormals are deferred to a separate contract.

## Exact finite and explicit special expectations

Use exact integer/rational arithmetic without host floating arithmetic or
epsilon. Decode both inputs exactly. Multiply or divide the rationals, round
the arithmetic result at PC/RC, then round the store at 53 bits using RC.
Nearest halfway values choose even significands; directed rounding uses the
sign of the exact value. Track precision loss at both stages; sticky PE is one
if either is inexact. Do not force PC53 and PC64 to agree. Each normal output
is checked bit-for-bit, and its intermediate rational is recorded.

Special outputs have explicit bit and exception expectations. For signed
zero/infinity results, use the XOR of input signs. Multiplication of zero by
infinity is invalid. Division of zero by zero or infinity by infinity is
invalid; finite nonzero divided by zero sets ZE. Infinity divided by zero
returns infinity without ZE. Other admitted zero/infinity pairs do not raise
exceptions. Invalid results are the binary64 floating indefinite
`0xfff8000000000000` with IE set. See [Intel SDM Volume 2A, FDIV table3-24](https://www.intel.com/content/dam/www/public/us/en/documents/manuals/64-ia-32-architectures-software-developer-vol-2a-manual.pdf#page=437)
and [FMUL table3-29](https://www.intel.com/content/dam/www/public/us/en/documents/manuals/64-ia-32-architectures-software-developer-vol-2a-manual.pdf#page=464).

A single QNaN propagates without IE; a single SNaN raises IE and becomes quiet
by setting bit51. For these selected inputs, compare the full propagated
binary64 encoding, including source payload and sign. Preserve measured raw
bits and classify the result too; classification does not replace exact
comparison. There are no ambiguous two-NaN selection cases in this contract.
See [Intel SDM Volume 1, section4.8.3.5/Table4-7](https://cdrdv2-public.intel.com/843827/253665-sdm-vol-1-dec-24.pdf#page=102)
and [floating indefinite section4.8.3.7](https://cdrdv2-public.intel.com/843827/253665-sdm-vol-1-dec-24.pdf#page=103).
These expectations include the preceding FLD: loading an SNaN in the first
position must retain its masked invalid status through the subsequent operation.

Start with clean status and empty x87 stack. CW stays requested. Observe
exception bits, SF, ES, TOP and final FSTP C1 through SW mask0x3AFF, with
FTW0 and TOP0 at both ends. C0/C2/C3/B remain excluded. The final store
overwrites C1; sticky arithmetic PE does not determine final-store C1.
All admitted special results have PE0, and only explicitly predicted IE/ZE
may be set. No unmasked traps, denormal/range exception delivery or live80
register equivalence is claimed.

## Final-store C1 expectation

For finite inputs, let A be the exact rational after PC/RC arithmetic rounding
and S be the binary64 value after the final RC store. Define C1 as
`abs(S) > abs(A)`. This tests significand magnitude increment, including
negative results, rather than signed greater-than. Compare A at its full
admitted 64-bit significand precision; prematurely truncating A to binary64
would erase the evidence. An exact store clears C1 in this bounded clean-entry
matrix even if an earlier arithmetic operation left sticky PE set. Admitted
masked zero, infinity, quieted single-NaN and indefinite stores have C1 zero.
The twelve-mode hardware matrix must independently verify every such case.

[Intel SDM Volume 2A, FST/FSTP](https://cdrdv2-public.intel.com/812383/253666-sdm-vol-2a.pdf#page=547)
defines destination-width rounding and C1 rounding indication; C0/C2/C3 are
undefined. [Volume 1, section8.5.6](https://cdrdv2-public.intel.com/843827/253665-sdm-vol-1-dec-24.pdf#page=232)
explains the masked precision exception's significand increment indication.
The rational rule above is the bounded oracle for these normal finite and
listed masked-special inputs. It is not a claim about arbitrary x87 stores,
nonempty entry stacks, unmasked exceptions or range faults.

Preserve and independently reparse the previous arithmetic measurements under
a strengthened mask. They must reproduce exactly 160 missing final-store C1
observations: 32 multiplication and 48 division cases per optimization level,
with zero special-profile differences and all other observations correct.
The new archive belongs under `reports/x87-store-c1/baseline-failure`; every
new build must bind its report and archived workers/results. Separately keep
the earlier right-SNaN IE failure proof under its original mask0x38FF;
strengthening this new gate does not revise that historical classification.

## CPU, memory and protocol

Retain v1 Header24, Request64 and Result4152. Input header `MW34REQ1` specifies
version1, exact profile count, record64 and pointer width32. Each request is
eight uint32 GPRs, flags, EIP, CW and memory seed, then two uint64 input bits.
Require flags0x202; permit observed flags0xCD5 in addition. Vary GPRs, flags,
DF, operand alignment, stack alignment and page margins.

Initialize page4096 at `0x20001000`, byte i=`(37*i+seed)&255`. Frame12 at ESP
contains uint32 sentinel, CW and seed. Input16 at ECX contains both operands;
output8 at EDX is the only writable guest span. All spans fit the page and
are disjoint. Observe the entire page and every CPU field. GPRs stay unchanged
except ESP+4; EIP reaches the sentinel; flags0xCD5 stay unchanged; status0.

Result is CPU/status44, memory4096, uint16 CW-before/after and SW-before/after,
uint8 abridged FTW-before/after and zero uint16 reserved. Output `MW34RES1`
identifies version1, count, record4152, pointer width32 original or64 native.
Validate every header field and exact length. Original CW/SW/FTW snapshots
use FXSAVE outside guest memory. Store both raw and observed status values.

## Native evidence and completion

Admit exact guest IR hashes and State3504 ABI, pinned source/contract/tool maps,
the unchanged isolated repair provenance, generated IR/layout/objects, workers,
disassembly and object-symbol controls before executing workers. Profiles are
`x87_store_c1_<kind>`. Final lowering uses strict dynamic constrained
fmul1 or fdiv1, fpext3 and fptrunc1, plus strict quiet constrained comparisons
fcmp_f64=3 and fcmp_f80=6. All floating operations use the reviewed strict
policy; ordinary classification comparisons are not mixed with constrained
arithmetic. The six external bridge names have readf64=2, writef64=1,
read32=1, return=1, exception-clear=2 and exception-test=2. No new bridge or
undefined helper is permitted. The observer must not infer expected output
or exception bits from input operands.
See [LLVM constrained intrinsics](https://llvm.org/docs/LangRef.html#constrained-floating-point-intrinsics).

Initial measurements found 96 missing right-hand SNaN IE results: twenty-four
per special profile at each optimization level. All finite cases, stored
payloads and other observed fields matched. Preserve the failing report and
151-file initial source/artifact/worker/result snapshot under
`reports/x87-arithmetic/baseline-failure`. Every final build binds the pinned
failure report and its manifest, and the comparator independently reparses
all 3264 original and 6528 initial native records. The pre-repair snapshot is
historical evidence, not a passing implementation.

The bounded repair relocates exactly the existing right-operand f64-to-f80
promotion after the first exception-clear/barrier and before arithmetic.
The existing exception test then captures the promotion's invalid exception
instead of clearing it first. It adds no operand classifier, result oracle,
status-bit predicate or external bridge. The retained exception repair and the new final-store status lowering are
bound together. Layout `status_lowerings` is exactly:

```json
{"memory_operand_promotion":{"moves":1,"source_type":"f64","destination_type":"f80","after_exception_clear":true,"before_arithmetic":true,"captured_by_existing_test":true},"final_store_c1":{"stores":1,"state_byte_offset":2739,"rule":"stored_magnitude_greater_than_input","input_type":"f80","stored_type":"f64","assignment":"unconditional","nonfinite_cleared":true,"comparison":"unsigned_abs_f80_encoding"}}
```

`bridge_lowerings` is empty. Immediately before the reviewed final write,
strictly extend the actual stored binary64 value back to f80. Bitcast that
value and the actual full f80 store input to i80, clear each sign bit, and
compare the unsigned magnitude encodings. Guard the input nonfinite exponent
so the admitted zero/infinity/NaN paths clear C1. Store the resulting byte
unconditionally at State offset2739; this replaces stale C1 rather than ORing
it into the state. For the admitted canonical finite f80 values, unsigned
absolute encodings preserve magnitude order. No new external bridge, host-C1
capture or observer computation is used. The three fpext operations include
this lossless store-result promotion; all floating comparisons remain strict.
Bind the exact admitted IR and generated repaired
IR; require the stated site and operation counts. Metadata corruption controls
reject absent/uncaptured promotion, promotion before clearing and an ordinary
floating comparison. The final corpus must still verify actual IE, payload
and every other observation without altering the expectation or observer.

Actual host PC/RC and normal-return host x87/vector/MXCSR preservation are
checked. Record eight memory and fifteen floating-environment checks per
native, eight profile mutations per kind, three object-symbol rejections per
native and zero rounding-bridge calls. Comparator/admission controls are
separate from corpus records. Include false-negative controls for lost or
spurious C1 in every mode, negative directed rounding, nearest halfway stores,
using the pre-PC exact result as the store input, sticky arithmetic PE with an
exact store, and nonfinite C1 leakage. Include controls for bypassed PC or store rounding,
ignored RC, reversed division, lost zero sign, absent/spurious IE/ZE/PE,
NaN quiet-bit/payload/sign corruption and dropped precision status.

Save new measurements only under `reports/x87-store-c1`. Earlier arithmetic
measurements and the historical signaling-NaN failure archive remain frozen. A discovered
semantic mismatch must retain its failing records and outcome; it cannot
be counted as a passing case or repaired in the observation harness. Any
bounded implementation repair requires explicitly revised source/layout
provenance and a new complete replay before accepting the contract.

Completion requires 3264 original oracle matches and 6528 native O0/O2
matches across all four profiles, including every stated exception/output
bit. Independently reparse the saved records with a separate oracle. The
general CPU/ABI and native game milestones remain open; arbitrary inputs,
other x87 instructions, C0/C2/C3/B, nonempty stacks, subnormal
or overflow/underflow behavior, two-NaN selection, unmasked traps, exceptional
exit pointer restoration and native game integration remain unproven.

## Required preserved evidence and replay

This local research recipe requires the immutable C1 baseline report
SHA256 `03eba1e074e3770bb42c2c411e876335f0cef556c9e4dd80d027cc960cd2f586`
and manifest SHA256
`ce06d189c3d2547b7f050623db2281d139c1e9d896d35059c3fa797bcb5b77cb`.
The 123-file archive binds previous source, tools, artifacts, reference/native
workers, all four input corpora, saved results and prior final build/report
pins. Each final build records `c1_baseline_path` and `c1_baseline_sha256`.
The gate independently reparses 3264 previous original and 6528 previous native
records, requiring exactly the stated 160 C1-only failures. It does not execute
or silently regenerate archived failing workers. The earlier 151-file SNaN
archive stays separately pinned and independently reparsed under mask0x38FF.
A workspace without these records must first reproduce the preceding arithmetic
experiment and preserve its failure measurement; this recipe is not a claim
of whole-project reproducibility from an empty checkout.

Run the new isolated recipe `tools/x87-store-c1/build_store_c1.ps1 -RunComparison`
after the new source set is frozen. Reject changed archive, source, contract,
tool, artifact, worker and layout identities before execution. A passing
bounded result requires all four complete strong-mask matrices, O0 and O2,
plus comparator/admission controls and a separate saved-record oracle review.
Keep failing and passing artifacts distinct; only new experiment paths may
receive writes.
