# Authored arithmetic lifting experiment

Date: 2026-10-06. **Original x86 and compiled native x64 execution matched on
all 10,144 cases at both O0 and O2.** This is the first authored arithmetic fixture,
not an MW3 function. The subsequently completed G1 gate is recorded in the
[branch/memory suite](fixture-suite-experiment.md); G2 remains pending.

## Observed results

| Check | Result |
| --- | --- |
| Real LLVM assembly/disassembly | Passed: i386 `mov eax,[esp+4]; add eax,[esp+8]; ret` |
| Actual original x86 execution | 10,144 cases passed an independent specification |
| Register, flag, stack and memory capture | All eight GPRs, EIP, CF/PF/AF/ZF/SF/OF, preserved DF and the entire 4 KiB mapped page matched |
| Corpus | 144 edge pairs plus 10,000 pseudorandom pairs; seed `0x3434`; varied preserved registers, initial flags, memory and stack alignment |
| Comparator negative controls | Corrupt register, carry flag and mapped memory changes were detected |
| Rejection controls | Current extended harness: 30 passed, including wrong compiled identities; initial arithmetic-only run had 28 |
| Remill lifting | Reviewed nine bytes emitted LLVM IR using the pinned x86 semantics |
| Host ABI adaptation | LLVM verified the module; every identified State storage type kept its size, alignment and field offsets |
| Native compilation | Windows x64 COFF objects and worker executables built at O0 and O2 |
| Differential execution | O0 and O2 each matched the original x86 output and independent specification on all 10,144 cases; zero mismatches |

The original reference is a Win32 MSVC process. It executes the authored bytes
at guest VA `0x10000000`, on a fixed stack inside `0x20001000..0x20002000` with
uncommitted guard pages on both sides. A fixed return sentinel jumps to an
assembly capture trampoline without changing registers or flags. Capture writes
to host storage after the guest returns; it does not overwrite the compared
stack. The parent validates every output against a separate arithmetic
specification before attempting any translated comparison.

Fixture SHA-256:
`6d1e1d30f2068501de61e0022c4352fda2a7650f29eb96f01ad04fa160305e21`.
Corpus SHA-256:
`98e6d88f30d01d53f77f95aa9e9a1f9ea9e4ce5a53f2184e698f5f3b1adaaca3`.
Requests contain only explicit-width integers and carry no native pointers.
The workers reject changed fixture bytes, invalid entry/stack addresses,
unsafe flags, malformed headers, truncation and trailing bytes. A nonzero worker
exit discards its output; a partially written file cannot count as a pass.

## Generated code and bridge

The lifted implementation comes from Remill's instruction semantics. The host
worker contains no C++ implementation of ADD. Its bridges provide checked guest
memory reads and validate the return sentinel. Bridge errors fail the whole case
after returning through Remill's nonthrowing intrinsic boundary.

Guest arithmetic and addresses remain `i32`; native pointers become 64-bit.
The host adapter uses the official LLVM 21.1.8 C API through Python. It permits
only the reviewed entry and memory/return bridges, rejects indirect calls and
pointer/integer casts, and defines four flag annotation identities in agreement
with upstream `tests/X86/Run.cpp`. Their first argument is the flag value already
computed by Remill; the adapter does not recompute flags.

State contains unused vector storage whose guest LLVM alignment differs from
the default host alignment. Explicit `i128:64` storage alignment preserves the
guest layout; LLVM checks all struct sizes, alignments and offsets before output.
The native bridge also asserts State size 3,504 and the register/flag offsets.
The native objects were disassembled to confirm actual x64 machine code and the
expected State accesses. There is no decoder, interpreter or JIT in the workers.
O0/O2 refer to this host optimization/code-generation step; Remill's generated
guest module already undergoes its own semantics optimization.

## Reproduction

Ordinary project builds do not download or require these tools. The experiment
uses the separately built dependencies recorded in [dependencies](dependencies.md).
Starting from the pinned Remill checkout, apply
`tools/lifting/remill-v6.0.1-x86.patch` and build the x86 tool/semantics:

```powershell
git -C local/tools/remill-v6.0.1/remill-6.0.1 apply D:/Projects/MW34Recomp/tools/lifting/remill-v6.0.1-x86.patch
./tools/lifting/build_remill.ps1
./tools/lifting/build_fixture.ps1
```

The patch path for this checkout is
`D:/Projects/MW34Recomp/tools/lifting/remill-v6.0.1-x86.patch`.
The current local checkout already has the patch; do not apply it twice.
The scripts accept `LLVMRoot`, `RemillRoot`, `VSRoot` and `Python` overrides.
The fixture build assembles, disassembles, lifts, validates layout, compiles both
host levels and records generated-file and executable hashes. `llvm-as` creates
guest bitcode from validated textual IR; Remill's direct bitcode writer left an
empty destination on this Windows build. Empty generated artifacts are rejected.

Reference-only verification is also available:

```powershell
C:/Python314/python.exe tools/lifting/compare_fixture.py `
  --reference build/fixture-reference/Release/mw34_reference.exe `
  --fixture build/fixture-reference/fixture_add.bin `
  --metadata reports/fixture-add-lift/build.json `
  --output-dir reports/fixture-add-reference-final
C:/Python314/python.exe tools/lifting/check_controls.py `
  --reference build/fixture-reference/Release/mw34_reference.exe `
  --fixture build/fixture-reference/fixture_add.bin `
  --llvm-dll local/tools/llvm-21.1.8/clang+llvm-21.1.8-x86_64-pc-windows-msvc/bin/LLVM-C.dll `
  --guest reports/fixture-add-lift/fixture-guest.ll `
  --report reports/fixture-add-lift/controls.json
```

For the complete verified build and test sequence, use
`./tools/lifting/build_fixture.ps1 -RunComparison`. It compares both x64 builds
against the original x86 and independent specification, then runs all 30
rejection checks. The extended worker also checks wrong compiled identities.
This arithmetic proof is complete;
the [full reviewed G1 suite](fixture-suite-experiment.md) adds branch/memory fixtures.

## Resolved execution blocker and evidence

The attempted O0 launch produced WinError 4551. Windows Code Integrity events
3033 and 3077 identify
`build/fixture-native-O0/mw34_lifted.exe` as failing the signing/policy requirement;
Smart App Control event 3118 occurred at the same time. That attempt could not
start and did not establish a translation mismatch.
The recorded Remill build recipe also compiled successfully during its final
verification. A subsequent attempt to refresh the generated artifacts was
blocked on the newly rebuilt `remill-lift-21.exe`; Code Integrity 3033/3077
confirmed the same signing-policy cause. The earlier block evidence was preserved.
The standalone C++ adapter was also blocked; its replacement performs IR
processing through the official LLVM library. Blocked executable payloads were
not loaded elsewhere. The user then turned Smart App Control off. Its local state
was verified as `0`, the full pipeline ran, and both native comparisons and all
28 rejection checks passed. The assistant did not change Windows security settings.

Local ignored evidence:

- `reports/fixture-add-reference-final/report.json`: earlier reference-only run.
- `reports/fixture-add-lift/build.json`: successful generated/compiled artifact
  snapshot, including the producing lifter's hash.
- `reports/fixture-add-lift/layout.json`: all compared State storage layouts.
- `reports/fixture-add-lift/controls.json`: 30 current explicit rejection results.
- `reports/fixture-add-lift/fixture-guest.ll`, `fixture-host.ll`,
  `fixture-host-O2.ll`: generated modules.
- `reports/fixture-add-lift/native-O0-disassembly.txt`,
  `native-O2-disassembly.txt`, `native-O0-headers.txt`: static native evidence.
- `reports/fixture-add-differential/report.json`: passing O0/O2 comparisons, exact
  corpus and source digests, commands, worker/output hashes and build provenance.
- `reports/fixture-add-lift/blocked-comparison-previous.json`: preserved earlier
  blocked comparison attempt.
- `reports/fixture-add-lift/execution-block.json` and `execution-block.xml`:
  Windows Code Integrity evidence for that attempt.
- `local/tools/fixture-native-build.log`: successful native compilation log.
- `local/tools/remill-recipe-verification.log`: successful Remill recipe build.
- `local/tools/fixture-pipeline-build.log`: successful full pipeline and tests.
- `reports/fixture-add-lift/lifter-execution-block.json`: later rebuilt-lifter
  block evidence and binary hash.

Historical blocked-attempt records describe the binaries at those times. Current
tested artifact hashes are in `build.json` and the differential report. No game
launch was needed. Branch/memory-write coverage now passes in the G1 suite. Next
is review of an actual hash-bound MW3 leaf; this fixture establishes no whole-game
compatibility claim.
