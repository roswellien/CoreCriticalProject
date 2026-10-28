# Isolated x87 control-word repair contract

Established 2026-10-07. This follow-up measures a repaired control-word load
and store implementation against original x86 hardware. The original
`x87-bootstrap` experiment and its precision-bit incompatibility remain frozen.
This contract closes only the two bounded control-word fixtures if they pass;
M2 floating-point compatibility remains open.

## Authored instructions and expected behavior

| Kind | Complete authored fixture | Bytes | Cases |
| --- | --- | --- | --- |
| store | `FNSTCW word ptr [ECX]; RET` | `D9 39 C3` | Twelve entry control words |
| load-store | `FLDCW word ptr [ECX]; FNSTCW word ptr [EDX]; RET` | `D9 29 D9 3A C3` | Every entry/loaded pair: 144 transitions |

FLDCW loads its two-byte source into the control register. FNSTCW stores that
register without replacing its precision or rounding fields. C0–C3 are
architecturally undefined for these instructions and are excluded. This
experiment uses FNSTCW without FWAIT and starts with clean, masked hardware
exceptions. See [Intel SDM Volume 2A, FLDCW, pages 3-357–3-358](https://www.intel.com/content/dam/www/public/us/en/documents/manuals/64-ia-32-architectures-software-developer-vol-2a-manual.pdf#page=459)
and [FSTCW/FNSTCW, pages 3-389–3-390](https://www.intel.com/content/dam/www/public/us/en/documents/manuals/64-ia-32-architectures-software-developer-vol-2a-manual.pdf#page=491).

The admitted set is `0x007F | (PC << 8) | (RC << 10)`, with PC 0, 2, 3 and
RC 0, 1, 2, 3. These select 24-, 53- and 64-bit precision and all four rounding
encodings while masking every exception. PC 1 and other bit patterns are
rejected. See [Intel SDM Volume 1, sections 8.1.5.1–8.1.5.3 and Table 8-2](https://www.intel.com/content/dam/www/public/us/en/documents/manuals/64-ia-32-architectures-software-developer-vol-1-manual.pdf#page=199).

| Precision | Nearest even | Down | Up | Toward zero |
| --- | --- | --- | --- | --- |
| 24 bits | 0x007F | 0x047F | 0x087F | 0x0C7F |
| 53 bits | 0x027F | 0x067F | 0x0A7F | 0x0E7F |
| 64 bits | 0x037F | 0x077F | 0x0B7F | 0x0F7F |

## State, memory and observations

Each request contains eight GPRs, integer flags, entry EIP, entry CW `a`,
loaded CW `b`, and a memory seed. For store, `b` is an unused frame word.
Original hardware CW and generated native State CW start at `a`. The hardware
harness records entry CW before fixture execution; evidence fails if that
value differs from `a`. It saves and restores the host FP/vector environment.

The guest page is 4096 bytes at `0x20001000`. Initial byte `i` is
`(37*i + seed) & 255`; the frame at ESP contains little-endian return sentinel
`0x10000100`, `a` and `b`. For load-store, `[ECX]` additionally contains
little-endian `b` before execution. Every two-byte operand must fit within the
page and avoid the twelve-byte frame; input and output cannot overlap.
Aligned and unaligned addresses, varied registers/flags including DF, and
page-edge operands are included.

Store must write `a` at `[ECX]` and preserve CW `a`. Load-store must write `b`
at `[EDX]`, preserve its input word, and finish with CW `b`. No other guest
memory byte changes. EAX, ECX, EDX, EBX, EBP, ESI and EDI and the seven observed
integer flags (mask `0xCD5`) remain unchanged. ESP advances by four; EIP reaches
the sentinel; worker status is zero. Observe post CW outside guest memory.
Compare exact complete records against an independent architectural oracle
and compare generated O0/O2 records to the original; no epsilon tolerance or
precision-bit mask is permitted.

The native load-store worker records exactly one rounding-setter call with
encoding `(b >> 10) & 3`; store permits none. This bounded bridge records the
requested encoding and does not implement or validate floating-point math.
No rounding getter, arithmetic bridge, fallback result, or adapter semantic
rewrite is admitted. Unsupported imports, requests and fixture bytes fail
before execution.

## Repair provenance and completion

Repair only an isolated source overlay of pinned Remill commit
`0e324aee8c67a63ec759ef379dcfafa0b3cb1448`. Remove the FNSTCW precision clamp
and rounding getter, and the FLDCW precision clamp; retain the FLDCW setter.
Save the authored patch, baseline and changed source hashes, baseline and
repaired semantics hashes, isolated lifter identity, and compiler/link commands.
The baseline semantics SHA-256 is
`138d370500c1f337e6e8fe8ddab09d91d85ea27456036c5bea0a18031b893d71`.
Existing tools, sources, reports and integer proofs remain unchanged.

Bind each kind's fixture, generated IR, ABI layout, objects, workers and source
identity to its build metadata before workers execute. Preserve malformed
input, illegal CW/overlap/extent, changed-code and comparator corruption
rejection evidence. Save new reports under `reports/x87-repair/`.

Completion requires 12 store and 144 load-store original records satisfying
the oracle, and all 312 native O0/O2 comparisons with zero mismatches. Any
precision-clamp result remains a failure here. Independent verification must
reparse saved records and repeat state/memory checks without importing the
comparator's oracle. A passing result establishes bounded control-word
storage/transitions, not numerical precision, rounding arithmetic, SW/TOP/tags,
live 80-bit registers, NaNs, conversions, unmasked traps or game compatibility.
