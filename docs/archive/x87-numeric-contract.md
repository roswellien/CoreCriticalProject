# Bounded x87 add/sub numerical contract

Established 2026-10-07. This separate experiment tests actual arithmetic after
the isolated control-word repair. Existing integer, bootstrap and control-word
evidence stays frozen. A pass closes this authored fixture and directed corpus;
general x87 and game compatibility remain open.

## Fixture and exact inputs

The complete authored x86 fixture at `0x10000000` is:

```asm
FLD  qword ptr [ECX]
FADD qword ptr [ECX+8]
FSUB qword ptr [ECX]
FSTP qword ptr [EDX]
RET
```

Its ten bytes are `DD 01 DC 41 08 DC 21 DD 1A C3`. Each input is a raw
binary64 encoding: base is +1 or -1, and increment is either sign of 2^-30,
2^-54, 2^-24, 2^-53 or 2^-64. Test every twenty-vector/twelve-control-word
combination exactly once: 240 cases. Control words are
`0x007F | (PC << 8) | (RC << 10)`, PC 0/2/3 and RC 0/1/2/3, with all
exceptions masked. Reject other encodings and all other numerical inputs.

PC selects 24-, 53- or 64-bit significand precision for FADD/FSUB. RC selects
nearest even, down, up or toward zero. See [Intel SDM Volume 1, sections
8.1.5.1-8.1.5.3 and Table 8-2](https://www.intel.com/content/dam/www/public/us/en/documents/manuals/64-ia-32-architectures-software-developer-vol-1-manual.pdf#page=199).

## Independent numerical oracle

Decode operands into exact signed rational numbers, without Python floating
arithmetic. Round the addition to PC precision using RC; subtract the exact
base from that rounded value and round again to PC/RC. Finally round to the
53-bit binary64 destination using RC. Compute spacing from each exact binade,
including the different spacing immediately above and below +/-1. Record each
intermediate rational and whether each rounding stage was inexact.

Exact cancellation produces -0 under round-down and +0 under the other modes.
Compare the stored sign bit exactly. FSTP rounds to its destination width and
pops its source. See [Intel SDM Volume 2A, FSUB pages 3-395-3-396](https://www.intel.com/content/dam/www/public/us/en/documents/manuals/64-ia-32-architectures-software-developer-vol-2a-manual.pdf#page=497)
and [FST/FSTP pages 3-387-3-388](https://www.intel.com/content/dam/www/public/us/en/documents/manuals/64-ia-32-architectures-software-developer-vol-2a-manual.pdf#page=489).

Start with clean status and an empty x87 stack, then load the requested CW.
Expect sticky PE if any rounding stage was inexact; other exception flags,
SF and ES remain zero. These admitted values and results are normal or zero.
See [Intel SDM Volume 1, sections 4.9.1.6 and 8.5.6](https://www.intel.com/content/dam/www/public/us/en/documents/manuals/64-ia-32-architectures-software-developer-vol-1-manual.pdf#page=108).

## Complete measured boundary

The v1 request header is 24 bytes (`MW34REQ1`, version 1, count 240, record
64, pointer width 32). Each request is eight GPRs, integer flags and EIP,
then CW and memory seed as uint32, and base/increment as uint64, all little
endian. Input integer flags require `0x202` and permit only the seven observed
bits in mask `0xCD5` in addition.

The guest page is 4096 bytes at `0x20001000`. Byte i starts as
`(37*i + seed) & 255`. The twelve-byte frame at ESP contains uint32 sentinel
`0x10000100`, CW and seed. The sixteen-byte input at ECX contains base then
increment; the eight-byte output at EDX is separate. All three spans must fit
and cannot overlap. Exercise page edges, aligned and unaligned operands and
stacks, varied full GPRs and integer flags, including DF.

Only the output eight bytes may change. GPRs remain unchanged except ESP+4;
EIP reaches the sentinel; seven integer flags remain unchanged; worker status
is zero. CW before/after equals the requested word. The measured SW mask is
`0x38FF`: six exception flags, SF, ES and TOP. Require TOP zero before/after
and abridged FXSAVE FTW zero before/after, since FLD/FSTP balance an initially
empty stack. Save raw SW but exclude C0-C3 and busy from this contract. C1
rounding direction is outside this first gate. CW, SW and FTW hardware snapshots
come from FXSAVE outside guest memory, without inserting FNSTCW/FNSTSW.

Result header is `MW34RES1`, version 1, count 240, record 4152 and pointer
width 32 original/64 native. Result is ten CPU uint32 fields plus status,
4096 memory bytes, CW-before/after uint16, SW-before/after uint16,
FTW-before/after uint8 and a zero reserved uint16. Parse lengths and every
header field strictly. Compare complete CPU/memory, CW and tags exactly and
SW through the stated mask, with no epsilon or numerical precision mask.

## Native implementation and evidence gates

Reuse the unchanged isolated repaired semantics/lifter and its saved repair
provenance. Admit only the reviewed guest IR identity. The new numerical
adapter uses dynamic-rounding, strict-exception constrained operations:
one fadd, one fsub, three fpext and one fptrunc. Check the 32/64-bit State
layout and exact reviewed bridge calls. Undefined helper values may reach
only excluded C0/C2/C3 storage. Configure the actual host x87 PC/RC and clean
exceptions for each invocation; recording a requested RC alone is inadequate.
Save/restore the host x87/vector environment and MXCSR with aligned
FXSAVE64/FXRSTOR64; include a pending-host-exception/high-pointer round trip.
Record the separate memory bridge,
FP environment and altered-IR admission checks with their limited scopes.

Bind contract and authored source maps, exact tools/repair record, generated
IR/layout/objects and worker hashes to build metadata before running workers.
Preserve rejection evidence for malformed protocol, code identity, unsafe
flags, illegal CW/vector, overlap/extent and duplicates; deliberately corrupt
each observed result field. Include regressions for signed zero, premature
binary64 intermediate rounding and ignored RC. Save reports under
`reports/x87-numeric/` and independently reparse the saved records using a
separate oracle implementation.

Completion requires all 240 original records to satisfy the oracle and all
480 native O0/O2 observations to match both it and the original on the defined
boundary. This establishes this finite cancellation corpus only. It does not
prove arbitrary x87 arithmetic, other instructions, live 80-bit register
contents, nonempty entry stacks, denormals, NaNs/infinities, conversions,
unmasked traps, FIP/FDP restoration across exceptional exits or game behavior.
