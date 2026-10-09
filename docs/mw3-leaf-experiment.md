# G2: first MW3 native function comparison

Date: 2026-10-07. **G2 passed for `sub_00409ED0`.** The admitted original
x86 instructions and their Remill-generated native x64 versions agree on
16,609 inputs at O0 and O2: 33,218 native comparisons, zero mismatches and
49 rejection controls. Independent offline verification reproduced the corpus,
checked provenance and revalidated every saved result.

This establishes sampled equivalence for one isolated integer leaf. Full-game
x64 startup, floating-point behavior, graphics and extended gameplay stability
remain later milestones. The separate authored x86 hook has one verified call
in the original game; it is a different experiment.

## Identity and mechanism

| Field | Admitted value |
| --- | --- |
| Profile | `mw3-us-1-2-retail` |
| Game SHA-256 | `95bc2c114c9b2e5c5ada8e40ca78cc79470f862e45313ffad0d1e8e6d4d916bf` |
| Function / original VA | `sub_00409ED0` / `0x00409ED0` |
| Original slice | 22 bytes; SHA-256 `560c17c210dd7fedd7de601f42570c2a0473fa71962c13cfa85a005509a77c65` |
| Remill | v6.0.1, commit `0e324aee8c67a63ec759ef379dcfafa0b3cb1448` |
| LLVM | 21.1.8 |
| Targets | `i686-pc-windows-msvc`, `x86_64-pc-windows-msvc` |
| Native compilation | `llc -O0`; separately `opt default<O2>` then `llc -O2` |

The [function dossier](../games/mw3/docs/first-function.md) specifies the ABI,
arithmetic and final flags. Full-image identity, reviewed metadata, executable
section mapping and slice identity are checked before translation or execution.
The original worker executes the actual admitted instructions at their original
VA in a separate Win32 process. Its host image is located away from the game
code reservation; exact guest allocations must succeed. Code becomes read/execute,
and the initialized data page has inaccessible guard pages.

The native workers statically link LLVM's x64 COFF objects. Reviewed disassembly
shows compiled integer operations and direct calls to checked memory/return
bridges. There is no interpreter or JIT path. The handwritten Python formula is
an independent measurement oracle, not the translated implementation.

## Undefined intermediate flags and ABI

Remill emits two undefined intermediate shift values for AF/OF. The explicit
`mw3-helper` adapter profile accepts them only after a complete bounded SSA
proof: one unconditional block chain, exact AF/OF byte stores at State offsets
2069/2077, and defined overwrites before any read, State escape or return.
Aliases, overlapping loads, extra uses, conditional paths, unknown calls,
missing overwrites and tainted overwrites fail admission. The arbitrary zero
value supplied to these dead intermediates never supplies a final output flag.
The default fixture profile continues to reject the undefined helper.

LLVM's layout API verifies all guest State storage sizes, alignments and offsets
remain equal across the 32-to-64-bit target change. State is 3,504 bytes; guest
addresses remain 32-bit, with no host pointer/integer conversions or indirect
calls. Both comparison and offline verification check the recorded profile,
proof, layouts, IR identities and LLVM DLL identity.

An independently authored shift-then-subtract fixture first exercises this policy.
The expanded [G1 suite](fixture-suite-experiment.md) passes all four integer leaves
on the same source digest: 40,576 inputs, 81,152 O0/O2 comparisons and
135 rejection/bridge checks.

## Corpus, measurements and controls

The corpus contains 6,608 directed inputs, 10,000 deterministic random inputs
with seed `0x3434`, and one input pair from the verified Training trace. Its
826 directed index values cover every `48*n` wrap and sign-crossing boundary
with neighbors, low-byte parity, powers of two and integer limits. Base addresses
straddle final address wrap, including 826 exact-zero and 826 exact-maximum
directed outputs. All 128 safe arithmetic-flag/DF input combinations occur;
every final flag has both set and clear outcomes. Stack offsets span 16 through
4,080, including 12,153 unaligned cases.

For each input, both native results and the original measurement are checked
against the independent contract. Comparison includes all eight GPRs, the six
final arithmetic flags, preserved DF, ESP +8, EIP at the fixed `0x10000100`
capture sentinel, successful termination, and every byte of the initialized
4,096-byte payload. No memory write is permitted by this leaf.

The Training replay uses only the recorded index and ECX base. Other registers,
flags, stack location and payload are authored test inputs; it is not a replay
of the complete live process state.

The 49 controls comprise five changed-image/metadata admission rejections,
20 output corruptions spanning every state field and mapped-memory edges, and
24 malformed-input/unsafe-state/changed-slice worker rejections across the
original and both native workers. Thirteen portable adapter test groups and
an opt-in LLVM test also pass; the latter rejects 11 mutated authored modules
and two incompatible profiles. Twenty public corpus/provenance test groups pass,
including verified replay selection and changed-evidence rejections.

## Reproduction and saved evidence

With the matching installed game and the [pinned dependencies](dependencies.md),
run from the repository root:

```powershell
./tools/lifting/run_fixture_suite.ps1
./tools/lifting/build_mw3_leaf.ps1 -RunComparison
C:/Python314/python.exe tools/lifting/verify_mw3_leaf.py --report-dir reports/mw3-leaf-differential --game MW3/Mech3.exe
```

The game recipe accepts `Game`, `LiveSnapshot`, `LLVMRoot`, `RemillRoot`, `VSRoot` and `Python`
overrides. It executes only the admitted isolated leaf; it does not launch the
game. Ordinary CMake tests need no game installation or lifting dependencies.
The frozen Training trace is a local replay input recorded in the comparison
report. Missing or changed replay evidence fails this recorded-input gate.

For a fresh matching-game installation, create a real helper trace with the
[authored hook recipe](../tools/in-game-hook/README.md), then close that test
session so its log is stable. Save the strict verifier's successful JSON beside
the log and pass that session explicitly:

```powershell
$mwRun = 'reports/mw3-in-game/<closed-session>'
C:/Python314/python.exe tools/in-game-hook/verify_trace.py $mwRun | Set-Content -Encoding utf8 "$mwRun/verification.json"
if ($LASTEXITCODE -ne 0) { throw 'Real helper trace did not pass verification' }
./tools/lifting/build_mw3_leaf.ps1 -LiveSnapshot $mwRun -RunComparison
```

This accepts the first strictly verified call from that session. The input pair
and trace/verification hashes are bound to the new report; no fixed allocation
address is required. This project's default frozen trace continues to replay
the saved Training pair. The saved hash table below identifies that specific run.

Private ignored evidence:

- `reports/mw3-leaf-lift/`: admitted slice, guest/host IR, O0/O2 objects,
  native disassembly, checked layout and build provenance.
- `reports/mw3-leaf-differential/`: corpus, actual original/O0/O2 result streams,
  comparison report and offline `verification.json`.
- `reports/mw3-leaf-build-20261007.log`: final native build and initial comparison attempt.
- `reports/mw3-leaf-comparison-retry-20261007.log` and
  `reports/mw3-leaf-final-verification-20261007.log`: successful unchanged
  comparison retry and final offline verification.
- `reports/mw3-in-game/20261007-060648-615224-95ac7622/verified-snapshot/`:
  separate frozen x86 hook evidence supplying the single recorded input pair.

| Record | SHA-256 |
| --- | --- |
| Authored lifting source digest | `5458ca4f59f0ffaf7ecadc37234b386a261e7920f79fa714c9f196b514ad7657` |
| Corpus | `93a4371870f199e05029599568f6611ff66f61b5f1cbbe77fe2c2a573e99d6cf` |
| Comparison report | `ec28ddbd0ceccf2a22c984564e18c18343dd9f838b5afb4c7343d3a687e2a5cd` |
| Build metadata | `3a51677200b38b30ec3500323ba4f937fdcfdcfc33f6c07ca7101add7359098e` |
| Offline verification | `9c8e55f60462f7a7d7f89241cde5774fafe6e99b222eb7ba13974388c06dbfa6` |

The installed executable still has its admitted SHA-256. Public files contain
authored tools, fixture sources and reviewed metadata; original instructions,
game-derived IR, binaries and complete traces remain ignored.

One final-run attempt failed before helper execution because the required
original-address reservation or commit was unavailable. The worker failed
closed without relocating the function. An unchanged comparison retry passed;
the failed attempt remains in `address-admission-failure-report.json` and
`reports/mw3-leaf-address-admission-failure-20261007.log`. The occupying map or
Windows error was not captured, so the precise cause is unknown. This recipe
requires those fixed guest addresses to be available on its test host.

The four-fixture recipe now isolates each Visual Studio environment in its own
PowerShell child. This fixes an observed accumulated-PATH command-length failure
when the fixture suite and game build ran in one session. The corrected G1
regression and the final G2 evidence share the source digest listed above.

The next engineering gate is authored x87 fidelity under an explicit
rounding/status/NaN policy, followed by direct calls and observed import bridges.
Integer equivalence alone cannot establish MW3 physics or whole-game feasibility.
