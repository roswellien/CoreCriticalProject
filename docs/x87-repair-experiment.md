# Verified x87 control-word repair

Measured 2026-10-07. The bounded FNSTCW/FLDCW repair passes original-x86 versus
generated-native-x64 comparisons at O0/O2. M2 CPU/ABI validation remains active;
actual numerical precision, rounding and exception behavior still require tests.

## Change

The [previous experiment](x87-control-experiment.md) reproduced sixteen native
control-word incompatibilities in the admitted baseline toolchain. The
[new repair contract](x87-repair-contract.md) retains that architectural oracle
and expands it to control-word loads and transitions.

The patch removes the forced single-precision assignment from FNSTCW and
FLDCW. FNSTCW stores the guest State's control word without consulting host
rounding or mutating State. FLDCW retains the loaded word, including its precision
bits, and sends its rounding encoding through the existing setter boundary.
The native worker checks that the load fixture calls that boundary exactly once
with the loaded RC, while the store fixture never calls it. This boundary
records guest RC only; it makes no promise about host numerical arithmetic.

The repair is in [remill-control-word.patch](../tools/x87-repair/remill-control-word.patch).
It also adds an explicit semantics-directory argument to an isolated lifter.
Missing arguments/files are rejected before lifting. This makes the selected
semantics visible and prevents an unnoticed return to the baseline search path.
The adapter preserves State storage and bridges; it applies no semantic repair.

## Measured validation

| Authored fixture | Original cases | Native O0/O2 comparisons | Mismatches | Rejection controls |
| --- | ---: | ---: | ---: | ---: |
| FNSTCW [ECX]; RET | 12 | 24 | 0 | 97 |
| FLDCW [ECX]; FNSTCW [EDX]; RET | 144 | 288 | 0 | 121 |
| Total | 156 | 312 | 0 | 218 |

The load/store fixture covers every Cartesian pair of twelve legal masked
entry/loaded control words: three precision settings and four rounding settings.
It includes 132 actual control-word changes, DF-set cases, unaligned accesses
and page margins. Both fixtures compare all general registers, admitted integer
flags, ESP/EIP and return status, entry/post control words, and every byte of
the 4096-byte memory page. Only the authored destination changes. The original
worker verifies host FXSAVE-state restoration around each execution.

The 218 checks include malformed-result/corruption detection, explicit rejection
of the old precision-clamp result, and intended worker admission failures before
any result output. Separately, two adapter profiles pass 19 actual LLVM mutation
rejections; four native workers each pass 15 bridge checks; two lifter controls
reject missing semantics. Independent review regenerates the complete memory
oracle and reparses saved binary results without importing the comparator's
expected-result functions.

## Isolation and evidence

The baseline Remill source, binaries and semantics remain unchanged. The new
build copies an x86 source overlay into ignored
`local/tools/remill-x87-control-repair/`, changes only X87.cpp and Lift.cpp,
rebuilds the instruction semantics using the recorded compiler recipe, and
links the new lifter against admitted static libraries. Original headers and
the other semantics components retain their hashes. The new records bind
source, patch, compiler/link arguments, libraries, toolchain and worker identities.

Existing G1, G2 and `x87-bootstrap` source/artifact identities remain valid.
The baseline failure remains reproducible through its original recipe. The
repair uses new authored sources under `tools/x87-repair/` and
`tests/x87-repair/`, isolated build directories, and ignored
`reports/x87-repair/` records.

Final authored-source SHA-256:
`92eab0a17d160379a13ec822acf9e9228e94b0eb5fa10610946c648930258984`.
Final comparison report SHA-256:

```text
store:      d3c4441e8d78e19ae67bfd06debfd8128c0ffebad0cc935bdd9736386900e744
load-store: bb5d002f36082ee45b823af5b3b93dcf547172036f1928d3420dbec0af583519
```

Reports are in `reports/x87-repair/{store,load-store}/comparison/report.json`.
Toolchain provenance is `reports/x87-repair/toolchain/repair.json`; the final
independent check is `reports/x87-repair/independent-verification.json`.

During development, one overlay compilation initially resolved semantics
includes against the baseline source directory. The unchanged-semantics guard
rejected that build before any repaired comparison. Its log is preserved at
`reports/x87-repair/toolchain/include-routing-failure-log.txt`. The final recipe
explicitly resolves semantics includes against the overlay; independent review
checks that command and the actual generated code. This development failure is
not counted as a compared case or a rejection control.

## Replay and next step

Use a fresh PowerShell 7 process at the repository root with the recorded local
toolchain and Visual Studio installation:

```powershell
& ./tools/x87-repair/build_repair.ps1 -RunComparison
& 'C:/Python314/python.exe' tests/x87-repair/test_adapter_controls.py `
  --llvm-dll 'local/tools/llvm-21.1.8/clang+llvm-21.1.8-x86_64-pc-windows-msvc/bin/LLVM-C.dll' `
  --store-guest reports/x87-repair/store/guest.ll `
  --load-store-guest reports/x87-repair/load-store/guest.ll `
  --output-dir reports/x87-repair/adapter-controls
```

Each report must say `passed_bounded_control_word_contract`, zero native
mismatches, and `compatibility_gate: false`. The latter records the broader M2
gate, which remains open.

Next, measure actual numerical load/store and arithmetic, using directed
examples that distinguish intermediate precision and rounding settings.
Compare exact defined bit patterns and state, then expand to conversions,
special values, status/tags and exceptions under explicit contracts. A preserved
control word alone does not prove those behaviors. This repair has not been
integrated into a native game executable or used to diagnose the earlier
graphics glitch.
