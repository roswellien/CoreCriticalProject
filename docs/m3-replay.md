**Replay the bounded M3 function and connected-component validation**

This guide runs the complete original x86 setter at `0x558290` and consumer at
`0x55A560` against their statically lifted Windows x64 O0/O2 implementations.
Use the exact accepted checkout and its local evidence dossier. A fresh source
checkout without the ignored toolchain, previous acceptance artifacts and
private inputs cannot satisfy this replay's admission gates.

The accepted connected source snapshot is 64 files with source digest
`e1df715cd82b36d5df975768e7e161bec81ca8a5298a1e79d79d21db2f452f3c`.
The first-function snapshot has digest
`a729001cd76d5d7f0ef03a84a5f1023d5badb5ecabcce8b2b596053d6d309c64`.
Keep their technical sources, contracts, runtime dependencies and toolchain
unchanged. The recipes rehash those inputs and reject a source change during
compilation. A modified implementation needs a new review and acceptance record.

Supply your own admitted `MW3/Mech3.exe`, SHA-256
`95bc2c114c9b2e5c5ada8e40ca78cc79470f862e45313ffad0d1e8e6d4d916bf`.
The image and all extracted bytes, disassembly, IR, objects, workers and result
streams stay in ignored `MW3/`, `local/`, `build/` and `reports/` directories.
Keep these private artifacts out of source control. Missing inputs and changed
image or complete-function bytes fail admission.

The local accepted replay input is
`reports/m3-acceptance/first-gate-pins.json`. Its `previous_gate_pins` object
contains these seven bindings:

| Label | Required local evidence |
| --- | --- |
| `first_build` | Frozen first-function build record. |
| `first_comparison_report` | Passing 15,780-original/31,560-native comparison. |
| `first_initial_failure_report` | Preserved initial failure report. |
| `first_initial_failure_manifest` | Exact initial failure archive manifest. |
| `m2_final_pins` | Frozen M2 acceptance pins. |
| `m2_independent_pins` | Frozen independent M2 audit pins. |
| `first_independent_review` | Combined first-function acceptance review, including the causal rejection supplement. |

Every binding has exactly `path` and `sha256`: an absolute path to the existing
artifact and its literal 64-character lowercase SHA-256. Preserve the map and
all referenced files. Admission checks the accepted first build, current
sources, tools, layouts, workers, requests and actual saved results; it does not
create a missing dossier or silently skip a previous gate. Absolute path
bindings also mean relocating the checkout requires a separately reviewed local
evidence binding.

Run from a normal Windows PowerShell session with the accepted LLVM 21.1.8,
repaired Remill toolchain, Python and Visual Studio installation available.
The recorded defaults are Python `C:/Python314/python.exe`, Visual Studio
`C:/Program Files/Microsoft Visual Studio/18/Community`, LLVM under
`local/tools/llvm-21.1.8/` and Remill under `local/tools/remill-v6.0.1/`.
The repair provenance record at `reports/x87-repair/toolchain/repair.json` and
its pinned tool files must exist. Optional recipe parameters can locate those
tools; their admission checks still apply.

The following complete build runs the admission controls, both static lifts,
original/native worker builds, compiled protocol/context/State/host-environment
checks and the full comparison. Choose a new output directory and a new final
path component for every experiment; the directory must not already exist.

```powershell
Set-Location D:/Projects/MW34Recomp
powershell.exe -NoProfile -ExecutionPolicy Bypass -File tools/m3-subsystem/build_subsystem.ps1 `
  -FirstGatePins D:/Projects/MW34Recomp/reports/m3-acceptance/first-gate-pins.json `
  -Image D:/Projects/MW34Recomp/MW3/Mech3.exe `
  -OutputDirectory D:/Projects/MW34Recomp/reports/m3-subsystem/replay-20261007 `
  -RunComparison
```

`-ExecutionPolicy Bypass` applies to that PowerShell process. The command does
not change the machine's execution-policy setting. If preparing a build and
running the comparison separately, omit `-RunComparison` above, then execute
the following in the same normal Windows environment with another new output
directory:

```powershell
C:/Python314/python.exe tools/m3-subsystem/compare.py `
  --build D:/Projects/MW34Recomp/reports/m3-subsystem/replay-20261007/build.json `
  --out D:/Projects/MW34Recomp/reports/m3-subsystem/replay-20261007-comparison
```

The normal Windows environment is part of this reference-run requirement.
The preserved sandbox run failed before entry because a suspended child already
had a private reservation overlapping `0x720000`; it produced no result bytes.
The unchanged compiled workers passed the complete measurement outside that
sandbox. A reservation failure remains a failed experiment. Preserve its
report, use a fresh output directory for a separately justified environment
change, and require the intended diagnostics for each negative control.
A nonzero exit alone does not prove a particular malformed input was rejected
when startup failed earlier.

For the frozen corpus, expect 1,427 sequences, 3,968 original steps and 7,936
native comparisons. Acceptance requires all workers to complete, zero defined
differences, the observer and rejection controls, and independent review.
`compare.py --replay <saved-comparison-directory>` only rechecks existing result
streams; it does not execute workers or rerun rejection controls and is not a
replacement for the complete command above.

Guest x87 FOP/FIP/FDP metadata is restricted to zero. Nonzero requests fail
before entry/output, and actual metadata must be zero at both boundaries.
The independent scheduling probe showed that this Windows host can lose
nonzero hardware metadata even across an integer-only interval. No metadata
normalization or test skip converts that unsupported domain into a pass.
Numerical x87 state, tags, TOP, masked status/control state, vector storage and
actual host restoration remain checked; separate short host-isolation controls
retain nonzero metadata seeds.

This replay validates the bounded offline component described in
`docs/m3-subsystem-contract.md`: complete functions, shared guest globals,
isolated stack/buffer pages, persistent guest context and ordered native bridge
events. Original per-access events are unobserved. Unsupported encodings,
unmasked FP exceptions, callbacks, SEH, concurrent guest execution and other
dependencies remain outside this gate. Passing establishes neither game startup
nor rendering, observed consumer use during play, whole-game compatibility or
Milestone 4 integration.
