# Authored x87 spill and integer conversion experiment

Measured 2026-10-07 on Windows x64 with LLVM 21.1.8 and the previously isolated
Remill control-word repair. Both new finite directed contracts pass: 624 original
x86 cases and 1,248 generated native O0/O2 comparisons, with zero architectural
mismatches. M2 remains active. No game process was started by this experiment.

| Fixture | Original x86 | Native O0 | Native O2 | Mismatches |
| --- | ---: | ---: | ---: | ---: |
| Explicit binary64 intermediate spill/reload | 240 | 240 | 240 | 0 |
| Valid rounded signed32 conversion | 384 | 384 | 384 | 0 |

The [contract](x87-expand-contract.md) admits all twelve combinations of
24/53/64-bit precision and nearest-even/down/up/toward-zero rounding, with
exceptions masked and an initially empty stack. Inputs are exact finite vectors;
the workers reject everything outside the respective corpus before execution.

The spill fixture executes:

```asm
fld  qword ptr [ecx]
fadd qword ptr [ecx + 8]
fstp qword ptr [edx + 8]
fld  qword ptr [edx + 8]
fsub qword ptr [ecx]
fstp qword ptr [edx]
ret
```

The intermediate store must discard precision beyond binary64. For example,
base 1 plus increment 2^-54 in 64-bit precision and nearest-even mode spills
as 1, so subtraction after reload yields +0. The earlier fixture without that
store retained 2^-54. The new test checks both the actual spilled word and the
final result, including both zero signs and sticky precision status.

The conversion fixture executes `FLD qword [ECX]; FISTP dword [EDX]; RET`.
Its 32 inputs include signed zero, positive and negative fractions, ties,
integers and signed32 endpoints. All rounded results are representable under
every admitted rounding mode. Tests at low precision ensure the conversion
does not first clamp its loaded operand to the arithmetic precision setting.

The comparator rounds spill stages with exact rational arithmetic and rounds
conversion inputs to integers with an explicit representability check. Neither
execution worker contains that expected-result oracle. Each worker produces
152 precision exceptions for spill and 288 for conversion, matching the oracle.
Comparison covers all GPRs, admitted integer flags, return address and stack
effect, the complete 4096-byte guest page, control words, defined status bits
and final empty-stack observations. Raw status remains saved; C0-C3 and busy
are excluded by the reviewed mask 0x38FF.

The independent review found a concrete excluded observation: original FISTP
sets C1 in 111 of the 384 cases, giving raw SW 0x0220 where native SW is 0x0020.
Defined status through 0x38FF still matches. Full C1 fidelity remains an open
status gate; these results must not be described as matching every raw status bit.

The first conversion build exposed a real ABI failure. All 384 records in each
native build disagreed with original hardware on defined status. Disassembly
and undefined-symbol inspection showed LLVM calling `nearbyintl` with extended
80-bit argument/result storage. Microsoft's C++ implementation gives `long
double` the same width as `double`, so the local CRT boundary could not implement
that call correctly. See [Microsoft's type ranges](https://learn.microsoft.com/en-us/cpp/cpp/data-type-ranges?view=msvc-170).
The 768 failed comparisons, original results, IR, objects, binaries, disassembly
and source snapshots remain under `reports/x87-expand/conversion-abi-failure/`,
bound by its `record.json`. They remain failed evidence.

The repair lowers that exact nearbyint operation to the reviewed pointer bridge
`__mw34_x87_nearbyint80(in10, out10)`. Hardware FRNDINT uses the actual guest
rounding control and transports ten-byte payloads through pointers. An inner
FXSAVE64/FXRSTOR64 scope restores the host exception status and numerical state
around the rounding operation. The existing translated conversion then sets
the guest precision flag from the original input. No scalar extended value
crosses the Windows C ABI. Constrained fptosi handles the already integral,
valid signed32 value; fptosi alone truncates and cannot implement FISTP rounding.
See [LLVM's constrained conversion semantics](https://llvm.org/docs/LangRef.html#constrained-floating-point-intrinsics).

The spill operations retain strict dynamic constrained add/subtract and
binary64 conversions. Exact source/IR admission rejects arbitrary rewrites.
The new [object symbol gate](../../tools/x87-expand/check_object.py) runs before
linking, requiring the reviewed bridge dependencies and rejecting unexpected
floating library calls. This prevents the linker from silently satisfying a
future incompatible `nearbyintl` call.

| Additional checks | Spill | Conversion |
| --- | ---: | ---: |
| Comparator corruption rejections | 74 | 62 |
| Metadata/layout rejections | 16 | 16 |
| Admission rejections across original/O0/O2 workers | 96 | 108 |
| Excluded-status-mask controls | 10 | 10 |
| Altered IR profiles rejected before emission | 8 | 8 |
| Object symbol rejections per native object | 3 | 3 |
| Memory boundary checks per native worker | 12 | 12 |
| Host FP environment checks per native worker | 15 | 15 |
| Signed raw80 rounding bridge checks per native worker | 0 | 24 |

Thus each comparison report records 186 passing rejection controls plus ten
status-mask checks. The build separately records adapter, symbol, memory and
environment checks. The rounding bridge checks include all PC/RC settings,
both signs, unaligned ten-byte buffers, canaries, and host state restoration.

Replay with the local pinned tools from a fresh PowerShell 7 process:

```powershell
& 'D:/Projects/MW34Recomp/tools/x87-expand/build_expand.ps1' -RunComparison
```

Per-fixture `reports/x87-expand/<kind>/build.json` and `comparison/report.json`
bind the authored sources, contract, repair provenance, tools, exact instructions,
IR, layouts, native objects, executable workers, corpora and complete results.
The build recipe is [build_expand.ps1](../../tools/x87-expand/build_expand.ps1).

Independent integer/dyadic and integer-rounding oracles reparsed all 1,872 saved
original/native records without importing the comparator's oracle. They also
verified source, tool, artifact, repair, symbol and rejection-evidence bindings.
Reviews are saved separately in each fixture's `comparison/read-only-review.json`.
The separate worker/environment/provenance review and its replay script are
under `reports/x87-expand-reference-check/`. Its `independent-verification.json`
confirms all records, fresh boundary checks and unchanged earlier G1/G2,
control, repair and numerical evidence, including the preserved ABI failure.

| Frozen identity | SHA-256 |
| --- | --- |
| Shared authored source digest | `89bb2cb9ef2d0bf604c18a8239df7f1d33a6bbd357520b765478cea99807a7c5` |
| Spill build metadata | `70d9b9f1eff0514c8668fa0d2a3b87f4333a2439b7d22d7a3ce0ed2816da81e1` |
| Conversion build metadata | `a74e6b6589f3fe24c7d29a9a8fd3f08e8351f8f4e00296f6094aa82fc325bab9` |
| Spill directed corpus | `72772981a40fb7806c95e67d4d5cfbab443ef31fe550eefc3ea8661f2d29eda2` |
| Conversion directed corpus | `6f0a2f18b23a88c4593be9bc35fee0a6f55c21a02923816486a6a64ba6ede922` |
| Spill comparison report | `4e90efc5070b877815710d8c245b3a36b0a33e6fe0702ebf344d8192f64f217e` |
| Conversion comparison report | `3a07d33e00baff243dacb348d135ddd1ff412c2917c076a0afa2f883457a2703` |
| Preserved conversion ABI failure record | `a3c13e1c3a794b3ab2908a6c5393b9dc23736bdafbfe16769e523bb23b845a25` |
| Independent worker/provenance verification | `0747802ba8e4c604014e43599283ccaecc5af2580a098bbdf86e3e783508724b` |

These passes cover only the exact authored finite corpora and final observations.
Arbitrary instructions/inputs, invalid integer conversions, NaNs, infinities,
denormals, exponent-range boundaries, unmasked traps, live extended register
contents, nonempty entry stacks and general tag behavior remain open. The next
authored probes should define conversion C1 behavior, then cover
multiplication/division and explicit exceptional value policies before another
game slice. The [milestone register](../project-milestones.md)
retains M2's broader CPU/ABI requirements.
