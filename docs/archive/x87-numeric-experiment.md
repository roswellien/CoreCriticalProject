# First numerical x87 experiment

The authored cancellation fixture passes 240 original x86 cases and 480 native
Windows x64 comparisons at O0/O2 with zero mismatches in the admitted observations.
This advances M2's arithmetic validation; the complete CPU/ABI milestone remains
active.

The ten authored bytes `DD 01 DC 41 08 DC 21 DD 1A C3` execute:

```asm
fld  qword ptr [ecx]
fadd qword ptr [ecx + 8]
fsub qword ptr [ecx]
fstp qword ptr [edx]
ret
```

The expression `(base + increment) - base` separates extended intermediates from
premature binary64 rounding. The corpus combines base +/-1 with positive/negative
powers 2^-30, 2^-54, 2^-24, 2^-53 and 2^-64, under every admitted masked precision
and rounding setting. The 24-, 53- and 64-bit precision modes and four rounding
modes are checked by exact output bits, including positive/negative zero.

The comparator uses an exact rational oracle, rounding each arithmetic stage
independently and checking the sticky precision exception. Original x86 executes
the authored instructions; the native path executes generated LLVM/Remill code.
Neither worker contains the expected-result oracle. All registers, admitted
integer flags, return address/stack effect, the full 4096-byte memory page,
control words, defined status bits and final empty-stack observations are checked.
Raw status words are retained; the contract's explicit observation mask excludes
the condition bits not admitted by this experiment.

All 160 rejection controls pass: 55 deliberately corrupted comparator records,
15 metadata/layout changes and 30 admission failures per worker. Ten additional
checks confirm the exact excluded-status-bit mask. Eight modified IR profiles
are rejected before emitting a host artifact. The independent saved-record
review uses a separately written integer/dyadic oracle and confirms all 720
original/native records, with 120 precision exceptions, 120 exact results,
63 positive zeros and 15 negative zeros per worker.

The new adapter admits only the exact reviewed IR for this fixture. It converts
the add/subtract and floating conversions to LLVM constrained operations with
dynamic rounding and strict exception behavior. The Windows x64 worker loads
the guest precision/rounding into hardware x87 control, reads it back, bridges
guest memory through checked 32-bit addresses and accumulates Remill's exception
flags. Optimized output retains the constrained operations. LLVM describes why
dynamic rounding must constrain optimizer transformations in its
[language reference](https://llvm.org/docs/LangRef.html#constrained-floating-point-intrinsics).

The numeric harness uses the previously repaired, explicitly selected semantics.
No further Remill semantic patch was needed. Baseline, control-probe and repair
sources/evidence remain preserved.

The host isolation review exposed a separate harness defect: legacy FNSAVE/FRSTOR
can truncate x87 instruction/data pointers to 32 bits in a 64-bit process. The new
scope uses aligned FXSAVE64/FXRSTOR64 and declares restored x87/XMM registers as
compiler clobbers. A pending host exception with synthetic high pointer bits
provides a discriminating round-trip check on this CPU, which otherwise saves
zero pointer metadata for masked operations. The observed legacy truncation and
repaired result are retained in `reports/x87-numeric-review/`.

Both native workers pass eight memory-bridge checks and fifteen environment
checks: twelve actual fixture runs preserving host x87 numerical state, opcode,
full pointer fields and MXCSR; active-state restoration during C++ unwinding; an
unwrapped exception control; and a pending-exception/full-pointer round trip.
The initial unwind discrepancy is retained in
`reports/x87-numeric/fp-unwind-failure-log.txt`. C++ exception dispatch changed
pointer metadata in the unwrapped control as well; the numerical state was
preserved. This does not establish pointer preservation across arbitrary OS
exception delivery.

Replay from a fresh PowerShell 7 process with the local pinned toolchain:

```powershell
& ./tools/x87-numeric/build_numeric.ps1 -RunComparison
```

The [contract](x87-numeric-contract.md),
[build recipe](../../tools/x87-numeric/build_numeric.ps1),
[comparison tool](../../tools/x87-numeric/compare_numeric.py) and local
`reports/x87-numeric/build.json` bind source, contract, compiler/tool, reused
repair, fixture, IR, native object and worker identities. The measured result,
corpus, raw worker outputs and rejection evidence are in
`reports/x87-numeric/comparison/`. Independent review is saved separately.

Frozen run identities:

| Record | SHA-256 |
| --- | --- |
| Authored source digest | `8de76793d9e4f31129f975c7de4fb1f26bf9e8d23fbc8d8d21888ab863b08216` |
| Build metadata | `3d2ee50b285db5a19fd185176d89c03b7e2bfd24a7037edda8bcc4f34ef90483` |
| Directed corpus | `75c1c0932f6a448018a1926c1a4bb58c4e8f062f987ecfa362acafe0627d18fd` |
| Comparison report | `b8bd970b509e583665915f8c47d7e2007d36ed0bf066d93c41caf5c21048d9c3` |

The independent oracle review is
`reports/x87-numeric/comparison/read-only-review.json`. The separate worker and
source/tool/artifact review is `reports/x87-numeric/independent-verification.json`.
Prior integer/helper/control sources retain their recorded identities; checks
are saved in `reports/x87-numeric/prior-source-preservation.json` and the replayed
offline helper verifier's `prior-mw3-helper-verification.json`. These checks did
not start a game process.

This gate covers finite directed add/subtract inputs with masked exceptions,
a clean initial stack and exact binary64 stores. It does not admit NaNs,
infinities, denormals, exponent-range boundaries, unmasked guest exceptions,
general tag bookkeeping, other x87 instructions or other host architectures.
The next authored gates should cover explicit spills and integer conversions,
then multiplication/division and exceptional values before another game slice.
