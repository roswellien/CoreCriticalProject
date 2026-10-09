# Bounded x87 multiplication, division and masked-special contract

Established 2026-10-07. This separate offline experiment uses two authored
fixtures and four admitted input profiles. Earlier integer and x87 sources,
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
exception bits, SF, ES and TOP through SW mask0x38FF, with FTW0 and TOP0 at
both ends. C0/C1/C2/C3/B remain excluded, including C1 from the final FSTP;
the prior conversion C1 result does not prove this different final instruction.
All admitted special results have PE0, and only explicitly predicted IE/ZE
may be set. No unmasked traps, denormal/range exception delivery or live80
register equivalence is claimed.

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
`x87_arithmetic_<kind>`. Final lowering uses strict dynamic constrained
fmul1 or fdiv1, fpext2 and fptrunc1, plus strict quiet constrained comparisons
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
status-bit predicate or external bridge. Layout `status_lowerings` is exactly:

```json
{"memory_operand_promotion":{"moves":1,"source_type":"f64","destination_type":"f80","after_exception_clear":true,"before_arithmetic":true,"captured_by_existing_test":true}}
```

`bridge_lowerings` is empty. Bind the exact admitted IR and generated repaired
IR; require the stated site and operation counts. Metadata corruption controls
reject absent/uncaptured promotion, promotion before clearing and an ordinary
floating comparison. The final corpus must still verify actual IE, payload
and every other observation without altering the expectation or observer.

Actual host PC/RC and normal-return host x87/vector/MXCSR preservation are
checked. Record eight memory and fifteen floating-environment checks per
native, eight profile mutations per kind, three object-symbol rejections per
native and zero rounding-bridge calls. Comparator/admission controls are
separate from corpus records. Include false-negative controls for bypassed PC or store rounding,
ignored RC, reversed division, lost zero sign, absent/spurious IE/ZE/PE,
NaN quiet-bit/payload/sign corruption and dropped precision status.

Save all measurements only under `reports/x87-arithmetic`. A discovered
semantic mismatch must retain its failing records and outcome; it cannot
be counted as a passing case or repaired in the observation harness. Any
bounded implementation repair requires explicitly revised source/layout
provenance and a new complete replay before accepting the contract.

Completion requires 3264 original oracle matches and 6528 native O0/O2
matches across all four profiles, including every stated exception/output
bit. Independently reparse the saved records with a separate oracle. The
general CPU/ABI and native game milestones remain open; arbitrary inputs,
other x87 instructions, excluded condition codes, nonempty stacks, subnormal
or overflow/underflow behavior, two-NaN selection, unmasked traps, exceptional
exit pointer restoration and native game integration remain unproven.
