# First required FP initializer

This separate M4 experiment compiles the complete initializer at `0x4133C0`.
Its reviewed wrapper reaches the original FLD/FMUL/FSTP body, which squares
the float at `0x5E1F58`, stores to `0x604E40`, and returns. Exact original bytes
and generated translations remain in private reports. Execution uses the
static LLVM translation and checked guest-memory bridges.

The installed input 20.0 first matched in 48 original and 96 O0/O2 native
observations, with independent raw-record review. The expanded authored
corpus contains 42 float words: signed zeros, normals, denormals, rounding
and range boundaries, infinities and quiet/signaling NaN payloads. Twelve
masked precision/rounding controls, empty x87 TOP 0/7 and two repeats produce
2,016 original records and 4,032 native comparisons.

The baseline preserved all numerical outputs but differed in status in 384
records per native level: 108 DE-only, 240 C1-only and 36 both. A typed store
test captures actual hardware C1 after the strict dynamic conversion. Both
the multiplication and store also need to retain the accumulated DE flag;
repairing the store alone leaves 144 failures per level. Each intermediate
failure is retained. The final candidate changes status handling only and
matches all 4,032 comparisons with zero observed differences.

Exception flags accumulate until explicitly cleared, and the FSTP rounding
status has a defined C1 meaning. C0/C2/C3 after this instruction are undefined.
These policies come from Intel's [basic architecture manual](https://www.intel.com/content/dam/www/public/us/en/documents/manuals/64-ia-32-architectures-software-developer-vol-1-manual.pdf)
and [FST/FSTP instruction reference](https://www.intel.com/content/dam/www/public/us/en/documents/manuals/64-ia-32-architectures-software-developer-vol-2a-manual.pdf).
Dead empty-stack raw80 contents and undefined conditions remain labelled as
observed storage rather than architectural defined data.

The original hardware FXSAVE metadata is zero on this measured machine, while
its legacy FNSTENV contains the actual instruction/opcode/data addresses.
Native State retains the legacy view. The comparison records and checks both
representations separately, with CPU, nine complete pages, ordered accesses,
protected 3,504-byte State and actual host FP restoration.

Thirty corruptions, fifteen actual worker identity/publication denials and
eight compiled context/permission/return controls at each level pass. The
[author closure](../reports/m4-fp-directed/author-review-r1/report.json) retains
1,242 physical bindings, 27 literal sources and five historical source-path
replacements. Sandbox fixed-address collision, build-script, compile and
semantic failures remain preserved. The successful original capture ran in
an isolated normal Windows worker; the ordinary game was not launched.

The [final independent directed review](../reports/m4-fp-directed/independent-review-r1/closure-r1/report.json)
passes all 2,016 original records, 4,032 native comparisons and 34 independent
corruption controls. Its [author archive association](../reports/m4-fp-directed/independent-review-r1/author-association-r1/report.json)
rehashes all 1,242 author bindings while preserving earlier seals. The review
reconstructs the complete native State and checks every whole page and 16,128
actual native events. Original State and event traces remain unobserved.
C1 has conservatively established store-rounding meaning in 672 original
records; the other 1,344 matching C1 values, undefined C0/C2/C3 and empty-tag
raw80 payloads carry observation credit only.
This domain excludes occupied x87 stacks, unmasked traps, other hardware,
broader initial state, other FP roots and connected startup ordering. It
does not register this translation in the shared Runtime or complete M4.

Replay the native candidate with the bundled PowerShell runtime:

```powershell
pwsh -NoProfile -ExecutionPolicy Bypass -File tools/m4-fp-store-repair/build_accumulated.ps1 -OutputDirectory D:/Projects/MW34Recomp/reports/m4-fp-store-repair/FRESHLEAF
```

The recipe requires fresh report/build directories and the pinned private
input evidence. The original observation and native comparison remain
separate commands in `tools/m4-fp-directed/capture.py` and `analyze.py`.
