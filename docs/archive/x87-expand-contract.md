# Bounded x87 spill and signed conversion contract

Established 2026-10-07. These two authored offline fixtures extend the earlier
numerical gate. Previous integer and x87 sources/evidence remain frozen.
Passing these directed corpora does not close general x87 or game compatibility.

## Authored fixtures and admission

Both fixtures start at `0x10000000` and return to `0x10000100`.

| Kind | Complete instruction sequence | Exact bytes | Cases |
| --- | --- | --- | --- |
| spill64 | `FLD qword [ECX]; FADD qword [ECX+8]; FSTP qword [EDX+8]; FLD qword [EDX+8]; FSUB qword [ECX]; FSTP qword [EDX]; RET` | `DD01DC4108DD5A08DD4208DC21DD1AC3` | 240 |
| fistp32 | `FLD qword [ECX]; FISTP dword [EDX]; RET` | `DD01DB1AC3` | 384 |

Control words are `0x007F | (PC << 8) | (RC << 10)`, with PC 0/2/3 and
RC 0/1/2/3. All exceptions are masked; other control words are rejected.
The twelve modes select 24/53/64 significand bits and nearest even/down/up/zero.
PC affects FADD/FSUB but does not reduce the precision of a loaded operand or
set the width of a memory store or integer conversion. See [Intel SDM Volume
1, sections 8.1.5.1-8.1.5.3](https://www.intel.com/content/dam/www/public/us/en/documents/manuals/64-ia-32-architectures-software-developer-vol-1-manual.pdf#page=199).

For spill64, the twenty raw binary64 vectors are base +/-1 and increment
either sign of 2^-30, 2^-54, 2^-24, 2^-53 or 2^-64. Test every vector in every
mode exactly once. Output is sixteen bytes: final binary64 at EDX and the
actual intermediate binary64 spill at EDX+8.

For fistp32, increment bits must be zero and input is one binary64 word.
The thirty-two exact inputs, in order, are each +/- pair of 0, 0.25, 0.5,
0.75, 1, 1.25, 1.5, 1.75, 2, 2.5, 3.5 and 12345.5, followed by
-2147483648, +2147483647, -2147483647.75, +2147483646.75,
-2147483647.5, +2147483646.5, -2147483647.25 and +2147483646.25.
The two zero signs have distinct input encodings. Every rounded result is
valid signed32 under all four RC modes. Reject all other inputs, including
overflows, denormals, NaNs and infinities. Test all 384 mode/input pairs.

## Exact architectural oracles

Use signed rational arithmetic, with no host floating arithmetic or epsilon.
Spill64 rounds addition at PC/RC, then rounds the intermediate store to
binary64 width using RC. Reload that stored value exactly, subtract the
original base and round at PC/RC, then round the final store to binary64.
Calculate each binade's spacing, including the spacing change at +/-1.
Exact cancellation yields -0 only under round-down. Check both stored words
and each intermediate rational. A binary64 spill cannot retain the discarded
extended precision. See [Intel SDM Volume 2A, FST/FSTP pages 3-387-3-388](https://www.intel.com/content/dam/www/public/us/en/documents/manuals/64-ia-32-architectures-software-developer-vol-2a-manual.pdf#page=489)
and [FSUB pages 3-395-3-396](https://www.intel.com/content/dam/www/public/us/en/documents/manuals/64-ia-32-architectures-software-developer-vol-2a-manual.pdf#page=497).

Fistp32 rounds the exact input to an integer using RC, independently of PC.
Nearest ties choose the even integer. Store its signed32 two's-complement
encoding and pop the source. The oracle explicitly checks representability;
masked invalid/indefinite results are outside this contract. See [Intel SDM
Volume 2A, FIST/FISTP pages 3-348-3-349](https://www.intel.com/content/dam/www/public/us/en/documents/manuals/64-ia-32-architectures-software-developer-vol-2a-manual.pdf#page=450).

Start with clean status and an empty stack. For both kinds, sticky PE is set
if any applicable rounding/conversion stage is inexact; other exceptions,
SF and ES remain zero. TOP and abridged FTW finish zero. CW is preserved.

## CPU, memory and protocol boundary

Use the existing authored v1 layout: 24-byte `MW34REQ1` header, record64,
input pointer width32, fixture-specific count240/384. Each little-endian
request has eight GPR uint32 values, flags, EIP, CW and seed, then base and
increment uint64 bits. Require flags0x202 and permit only the seven observed
flags in mask0xCD5 in addition.

The mapped page is 4096 bytes at `0x20001000`, initialized byte i as
`(37*i+seed)&255`. Frame twelve bytes at ESP holds uint32 return sentinel,
CW and seed. Spill64 input spans16 at ECX and output spans16 at EDX;
fistp32 input spans8 and output spans4. Every span fits the page and input,
output and frame are disjoint. Include aligned/unaligned operands and stacks,
page edges, varied full GPRs, flags and DF. Only the output span may change.

Observe all GPRs unchanged except ESP+4; EIP reaches the sentinel; observed
integer flags remain unchanged; worker status is zero. Result4152 contains
CPU/status44 bytes, memory4096, CW-before/after uint16, SW-before/after uint16,
FTW-before/after uint8 and zero reserved uint16. Header `MW34RES1` identifies
version1, correct count, record4152 and pointer width32 original/64 native.
Strictly parse every header field and full extent.

Record raw FXSAVE CW/SW/FTW outside guest memory. Compare SW through0x38FF
(exception flags, SF, ES and TOP); exclude C0-C3 and busy from this first
extension. Compare all CPU/memory, both CW values and tags exactly. Preserve
both zero signs for spilled floating output; integer output has no zero sign.

## Native implementation and evidence

Bind each exact guest IR/profile, generated IR/layout/objects, worker/tool
hashes, source map and this contract to per-kind build metadata before
executing workers. Reuse the unchanged isolated repair provenance and frozen
LLVM adapter API, identified by their hashes. Bind the new FXSAVE64
host-environment implementation in its source map.
Set actual host PC/RC, clean exceptions and save/restore x87/vector state and
MXCSR. Admit only reviewed State3504 layout and bridge counts.

Spill64 uses strict, dynamic constrained add1/sub1/trunc2/ext4. Fistp32 lowers
exactly one nearbyint to `__mw34_x87_nearbyint80(in10,out10)`, using pointers
to separate ten-byte temporary storage. It performs hardware FRNDINT with
the actual requested RC and preserves the host floating-point environment
and exception status around that operation. No scalar80 value crosses the
Windows C ABI; [Microsoft documents long double as the same width as
double](https://learn.microsoft.com/en-us/cpp/cpp/data-type-ranges?view=msvc-170),
which differs from LLVM x86_fp80.
After rounding, constrained fptosi converts the integral valid result and
constrained sitofp supplies the existing inexact test; each appears once,
along with one fpext. PE is explicitly determined from the original nonintegral
input. Constrained fptosi alone truncates; it cannot provide FISTP RC behavior.
See [LLVM constrained intrinsic semantics](https://llvm.org/docs/LangRef.html#constrained-floating-point-intrinsics).
Spill undefined helper values may reach only excluded C0/C2/C3 slots;
conversion permits none. Arbitrary IR transformations are rejected.

Save malformed protocol, code/cross-fixture identity, illegal vectors/CW,
unsafe flags, overlap/extent and duplicate rejection evidence. Corrupt every
observed field and output byte. Include regression controls for bypassed
spill rounding, lost signed zero, ignored RC, ties away from even, forced
integer truncation and PC-clamped conversion input. Record twelve memory
bridge and fifteen FP environment checks per native and eight adapter
mutation rejections per kind separately from corpus comparisons.
For conversion, record twenty-four direct rounding-bridge cases per native
covering signed inputs across PC/RC, unaligned ten-byte storage, canaries and
host numerical FP environment preservation. Spill permits no rounding bridge.
Inspect each generated object's unresolved symbols before linking: permit
only the reviewed bridges and compiler stack/float support markers, and
preserve three symbol rejection controls per native. External nearbyint or
nearbyintl library calls are rejected. Hash both symbol reports and LLVM nm.

Save new reports under `reports/x87-expand/`. Completion requires all 624
original records to match the independent oracle and all 1248 native O0/O2
observations to match it and the original on the stated boundary. Independently
reparse saved records using a separate oracle. A pass covers these two finite
corpora only; arbitrary inputs/instructions, live80 register values, nonempty
entry stacks, exceptional values, invalid integer results, unmasked traps,
exceptional-exit FIP/FDP restoration and game integration remain open.
