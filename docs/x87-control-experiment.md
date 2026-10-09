# First x87 control-word experiment

Measured 2026-10-07 with pinned Remill v6.0.1 and LLVM 21.1.8 on Windows.
The bounded research probe is complete: it reproduces a control-word
incompatibility. M2 CPU/ABI compatibility remains open.

## Result

The project-authored fixture is three bytes: `FNSTCW word ptr [ECX]; RET`.
The [reviewed contract](x87-control-contract.md) requires storage and preservation
of twelve admitted masked control words, combining three legal precision modes
with four rounding modes. The original hardware execution is the reference.

| Execution | Requests compared | Architectural matches | Architectural mismatches |
| --- | ---: | ---: | ---: |
| Original x86 hardware | 12 | 12 | 0 |
| Generated native x64, O0 | 12 | 4 | 8 |
| Generated native x64, O2 | 12 | 4 | 8 |

Both generated builds clear the precision bits `0x0300` in the stored word
and the translated State's post-execution control word. Single-precision
requests match; double- and extended-precision requests disagree with the
original. These sixteen native incompatibilities are failures of compatibility,
not passing cases. They exactly reproduce the pinned semantics' explicit
assignment to single precision. The generated IR and native disassembly retain
the corresponding bit clearing; no repair was applied to this experiment.

All other admitted observations match: all eight general registers, seven
observed integer flags including DF, ESP advancing four bytes, return EIP,
status, and every other byte of the 4096-byte memory page. Entry control-word
readbacks match all requests. The original worker verifies restoration of its
host FP/vector state around every case. The native control probe exposes
admitted guest RC through a scalar bridge and performs no host FP arithmetic.

Validation includes 27 comparator corruption/parser controls and 23 admission
rejections in each of three workers: 96 checks. Separately, the adapter passed
one valid input and eight mutation rejections; each native worker passed six
memory-bridge checks. Original and native execution files, corpus, generated
IR/objects, source hashes and build commands are saved locally. Independent
verification reparses the saved measurements rather than requiring another
game session.

The first corpus construction attempt placed one destination inside a return
frame. Admission rejected it before execution. The corrected corpus separates
those addresses and retains unaligned coverage. The failed attempt's report
and log remain in `reports/x87-bootstrap/corpus-admission-failure-*`; it is not
counted as a compared case or a rejection control.

## Evidence and replay

Authored sources are in `tools/x87-probe/` and `tests/x87/`. Generated artifacts
and build metadata are in ignored `reports/x87-bootstrap/`; measurements are
in its `comparison/` directory. Prior integer G1/G2 sources were untouched and
their offline verifiers still pass.

Final recorded SHA-256 identities:

```text
authored sources: 0d7a2d1e2252f457b6ed260543e51d21a464ec1cd112493c3f9bc55d74548749
build metadata:   3faef59ecea120a6308c78c100646f72052b2749359d932f83e9cf5447d36aff
comparison report:b8aa7eb2dd3824636ce5509459aee817b77771fb28cf3690c5f4f1a0d1b6ee2f
corpus:           9482a57409b2e780e94a7d063b7557b3bfb55506035eafc37b59b0a016b264ff
```

Replay from a fresh PowerShell 7 process at the repository root, with the
recorded local toolchain and Visual Studio installation:

```powershell
& ./tools/x87-probe/build_control.ps1 -RunComparison
& 'C:/Python314/python.exe' tests/x87/test_adapt_control.py `
  --llvm-dll 'local/tools/llvm-21.1.8/clang+llvm-21.1.8-x86_64-pc-windows-msvc/bin/LLVM-C.dll' `
  --guest reports/x87-bootstrap/control-guest.ll `
  --output-dir reports/x87-bootstrap/adapter-checks
& ./build/x87-control-native-O0/mw34_x87_native.exe --check-memory-bridges
& ./build/x87-control-native-O2/mw34_x87_native.exe --check-memory-bridges
```

The comparison exits successfully only when it reproduces the defined defect
with no unexpected differences. Its report explicitly records
`reproduced_x87_control_incompatibility` and `compatibility_gate: false`.
Changing the translator requires revising the experiment's outcome contract
before interpreting a different result as a compatibility pass.

## Next gate

Review and test a precision-control preservation repair, including FLDCW and
FNSTCW, before broader translation. Then establish actual numerical precision
and rounding behavior with authored load/store and arithmetic tests, extended
intermediates, conversions, special values and exception policies. Preserving
CW bits alone does not establish numerical fidelity.

This experiment does not establish SW/TOP/tags, live ST-register equivalence,
MXCSR behavior, unmasked traps, game floating-point behavior, or a cause for
the previously reported graphics glitch. The native game subsystem and
playable-native milestones remain future work; see the
[milestone register](project-milestones.md).
