# Finite FISTP32 C1 repair contract

Established 2026-10-07. This separate offline experiment observes the conversion
rounding flag omitted by the frozen spill/conversion gate. It also repeats the
unchanged explicit-spill corpus as a regression. Earlier sources and evidence
remain frozen. Completion applies only to the following finite corpora.

## Fixtures and admitted inputs

Both authored fixtures start at `0x10000000` and return to `0x10000100`.

| Kind | Complete instruction sequence | Exact bytes | Cases | Observed SW mask |
| --- | --- | --- | --- | --- |
| spill64 | `FLD qword [ECX]; FADD qword [ECX+8]; FSTP qword [EDX+8]; FLD qword [EDX+8]; FSUB qword [ECX]; FSTP qword [EDX]; RET` | `DD01DC4108DD5A08DD4208DC21DD1AC3` | 240 | `0x38FF` |
| fistp32 | `FLD qword [ECX]; FISTP dword [EDX]; RET` | `DD01DB1AC3` | 384 | `0x3AFF` |

Control words are `0x007F | (PC << 8) | (RC << 10)`, where PC is 0/2/3
and RC is 0/1/2/3. All exceptions are masked and every other control word is
rejected. The modes select 24/53/64 significand bits and nearest even/down/up/zero.
PC controls arithmetic precision; FISTP conversion uses RC without rounding
the loaded input down to PC first. See [Intel SDM Volume 1, section 8.1.5](https://cdrdv2-public.intel.com/843827/253665-sdm-vol-1-dec-24.pdf#page=209).

Spill64 covers all twelve modes and twenty binary64 vectors: base +/-1 and
increment either sign of 2^-30, 2^-54, 2^-24, 2^-53 or 2^-64. It stores final
binary64 at EDX and the intermediate spill at EDX+8.

Fistp32 covers all twelve modes and thirty-two exact finite inputs. In order,
these are each +/- pair of 0, 0.25, 0.5, 0.75, 1, 1.25, 1.5, 1.75, 2, 2.5,
3.5 and 12345.5, followed by -2147483648, +2147483647, -2147483647.75,
+2147483646.75, -2147483647.5, +2147483646.5, -2147483647.25 and
+2147483646.25. Positive and negative zero remain distinct input bit patterns.
Increment bits are zero. Every result is representable as signed32 under every
RC; reject all other vectors, including out-of-range values, subnormals, NaNs
and infinities. The input Cartesian product has exactly 384 unique cases.

## Integer, precision and C1 oracles

All expectations use exact signed rational/integer arithmetic. They do not use
host floating arithmetic, epsilon comparisons or the measured original as an
expected-value substitute. Fistp32 rounds input x to integer r using RC;
nearest ties select the even integer. Store r in signed32 two's-complement
form and pop the source. PE is one exactly when r differs from x.

For these valid finite conversions, the C1 oracle is:

`C1 = 1 if abs(r) > abs(x), otherwise 0`.

This describes an increment of the rounded significand's magnitude, including
negative operands. A signed comparison `r > x` does not implement this rule.
For example nearest conversion of -0.75 to -1 sets C1; conversion of -0.25
to 0 clears it. Nearest -1.5 to -2 sets it and -2.5 to -2 clears it.
Exact inputs and nonincremented results clear C1; it is the last operation's
condition code, whereas PE accumulates exception status. With clean entry and
one conversion the expected SW is `(PE << 5) | (C1 << 9)`.

The magnitude formulation is an interpretation of Intel's significand-increment
definition for this representable finite subset, checked independently against
raw original measurements. [Intel SDM Volume 1, section 8.5.6](https://cdrdv2-public.intel.com/843827/253665-sdm-vol-1-dec-24.pdf#page=232)
describes C1 on inexact results; [Volume 1, Table 8-1](https://cdrdv2-public.intel.com/843827/253665-sdm-vol-1-dec-24.pdf#page=207)
identifies affected condition codes. [Intel SDM Volume 2A, FIST/FISTP](https://www.intel.com/content/dam/www/public/us/en/documents/manuals/64-ia-32-architectures-software-developer-vol-2a-manual.pdf#page=450)
specifies RC conversion, pop, PE and C1, including clearing otherwise and
undefined C0/C2/C3. Faulting and masked-invalid conversions are outside this
contract; their C1 behavior cannot be inferred from this oracle.

Spill64's oracle is unchanged: round addition at PC/RC, round the intermediate
store to binary64 at RC, reload exactly, subtract the original base at PC/RC,
then round the final binary64 store. Track binade spacing and sticky PE at each
stage. Exact cancellation produces negative zero only with round-down. Observe
both stored words; exclude all four spill condition codes from this regression.

For conversion the exact oracle predicts 111 C1 sets, 37 at each PC. By RC,
nearest/down/up/zero contribute 39/36/36/0. Signed-direction comparison predicts
the wrong bit in 144 cases. These counts are derived from the finite corpus,
not assumed to apply to arbitrary x87 values.

## Observed CPU, memory and wire contract

The little-endian v1 header is 24 bytes: `MW34REQ1`, version1, kind-specific
count240/384, record64, pointer width32. Request64 has eight uint32 GPRs,
flags, EIP, CW and memory seed, then uint64 base and increment bits. Require
flags0x202 and permit only observed mask0xCD5 in addition. Vary full GPRs,
flags, DF, aligned/unaligned operands and stack, and page margins.

The mapped 4096-byte page starts at `0x20001000`; byte i is `(37*i+seed)&255`.
The twelve-byte frame at ESP contains uint32 sentinel, CW and seed. Input is
16 bytes for spill64 or 8 for fistp32 at ECX. Output is 16 or 4 bytes at EDX.
All spans fit the page and input, output and frame are disjoint. Only the output
span changes. GPRs remain unchanged except ESP+4; EIP reaches the sentinel;
integer flags through0xCD5 stay unchanged; worker status is zero.

Result4152 contains CPU/status44 bytes, the full 4096-byte memory image,
CW-before/after uint16, SW-before/after uint16, abridged FTW-before/after uint8,
and zero reserved uint16. Header `MW34RES1` specifies v1, count, record4152,
pointer width32 original/64 native. Validate every field and exact extent.

Start with clean status and empty x87 stack. Original CW/SW/FTW are captured
by FXSAVE outside guest memory. CW remains requested; TOP and FTW are zero at
both ends. Compare both CW values and tags exactly. SW mask0x3AFF for fistp32
observes all exception flags, SF, ES, TOP and C1; C0/C2/C3/B remain excluded.
Spill64 observes0x38FF. Preserve raw SW even when bits are excluded. No initial
nonzero C1 or nonempty-stack behavior is claimed by this clean-entry protocol.

## Native repair and provenance

Reuse the unchanged isolated Remill repair toolchain and pinned LLVM adapter
API. Hash source map, this contract, all compile tools, exact guest IR, generated
host IR/objects, layout, worker binaries, disassembly and symbol controls before
execution. The new experiment lives only under `tools/x87-c1`, `tests/x87-c1`
and `reports/x87-c1`; previous experiment artifacts retain their identities.

Fistp32 retains the reviewed ten-byte pointer rounding bridge
`__mw34_x87_nearbyint80(in10,out10)` and constrained ext1/fptosi1/sitofp1.
The bridge uses actual guest RC, handles raw80 in pointer storage and preserves
host exceptions/environment; no scalar80 value crosses the Windows C ABI.
See [LLVM constrained intrinsics](https://llvm.org/docs/LangRef.html#constrained-floating-point-intrinsics).
Valid integral r keeps fptosi representable. The existing inexact test determines
PE from r versus x. Host FXSAVE64/FXRSTOR64 preserves x87/vector state and MXCSR
on the tested normal returns; broader exceptional-exit pointer restoration is
excluded.

The new repair modifies only the admitted conversion IR. Immediately before
its reviewed integer write, take fabs80 of the already rounded value and of
the original loaded value, compare them with ordered greater-than, convert the
boolean to uint8 and assign State C1 byte2739. Assign both zero and one each
call; do not retain an earlier C1. This creates no external bridge. The harness
already reconstructs SW from that State condition slot; it does not compute
expected C1 from measured values. Layout must report exactly:

```json
{"C1":{"state_byte_offset":2739,"operation":"rounded_magnitude_greater_than_input","writes":1,"valid_signed32_only":true}}
```

Spill64 has empty `status_lowerings` and otherwise unchanged arithmetic.
Exact guest IR hashes pin operands and insertion location; the eight reviewed
input/profile mutations reject changed guest input, leaked undefined values
and extra operations. Comparator/layout corruption controls reject
missing/different status metadata, signed-direction policy, wrong storage and
retained C1. Original-versus-native measurements check the actual assigned bit.

Save fresh executions of the frozen earlier conversion workers in
`reports/x87-c1/baseline-failure`. Under the stronger mask each has 111 C1-only
failures and 273 matches; original hardware matches all 384 oracle records.
Bind baseline source/build/report/input/output/worker hashes. Preserve all
other observation equality; an unrelated difference is not a reproduced C1 gap.
This research gate requires the preserved baseline proof and checks its pinned
hash before compilation and measurement. It assumes that proof exists in the
local workspace; it does not claim a recipe for a fresh game installation.
To establish a new baseline, first replay the frozen expansion gate, then run
the independent reference-check script against its unchanged workers and
archive the stronger-mask failure separately. Keep the original reference
worker copy with the archive. The prior failure and new pass have separate
results; each new kind binds the reviewed archived failure.

Corrupt every observed field, both C1 observations, all output bytes and selected
memory bytes. Include C1-only controls for absent/retained C1, wrong signed
direction, odd/even ties, endpoint rounding and each PC mode. These detect
comparator false negatives; they do not extend the admitted entry state.
Record header/extent, flags, code identity, vector/CW, overlap and duplicate
admission rejections. Retain per-native memory12, FP environment15, conversion
pointer-rounding24 and object-symbol3 checks, with spill rounding-bridge count0.
Keep adapter profile controls separate from corpus measurements.

Completion requires all 624 original records and 1248 native O0/O2 observations
to match the exact oracle and original on each kind's boundary, with conversion
raw C1 matching too. Independently reparse saved records with a separate oracle.
This does not prove arbitrary x87 inputs/instructions, live80 register values,
nonempty entry stacks, subnormals/NaNs/infinities, invalid conversions, unmasked
trap delivery, excluded condition codes, exceptional-exit FIP/FDP restoration
or native game integration. The general CPU/ABI milestone remains open.
