# Bootstrap validation record

Initial record: 2026-10-06. Current review: 2026-10-07. The bounded G2 gate now
passes for one actual MW3 integer leaf compiled to native x64. The earlier
snapshots below remain historical; they do not replace the current validation.

## Current bounded validation, 2026-10-07

| Check | Observed result |
| --- | --- |
| G1: ADD, branch, memory and shift/SUB authored fixtures | 40,576 valid original x86 cases; 81,152 native O0/O2 comparisons; zero mismatches; 135 rejection/bridge controls |
| G2: admitted `sub_00409ED0`, 22 bytes at VA `0x00409ED0` | 16,609 valid cases; 33,218 native O0/O2 comparisons; zero mismatches; 49 controls |
| G2 independent offline evidence review | Passed: current full-image/slice admission, source/worker/generated-artifact identities, layout policy, deterministic corpus, complete saved state/memory results and controls |
| Host adapter tests | 14 passed with native LLVM controls enabled; checks include escaping or observed undefined flags and wrong explicit profiles |
| MW3 corpus/comparison/evidence tests | 20 passed, including oracle boundaries, all-state corruption, protocol/layout-policy rejection and verified replay selection |
| Current ordinary MSVC Debug build | Passed |
| Current ordinary CTest groups | Six groups passed; game-monitor coverage was checked separately as described below |
| Game monitor tests | 21 of 23 passed in the sandbox; the two path-resolution/process-cleanup cases also passed in focused outside-sandbox runs |
| Original x86 helper replacement in game | One verified real call, zero mismatches; user confirmed full launch and Training loaded |
| Original installed executable | Exact admitted image unchanged |
| Git-visible material/ignore review | Passed: 101 authored/metadata files; no private extension/directory violations; representative original/generated artifacts confirmed ignored |

The monitor's two sandbox-sensitive checks resolve a temporary executable path
and clean up their own native test process; their
focused outside-sandbox success is recorded separately from the sandbox run.
This does not make a failed sandbox run a passing all-in-one suite. Native LLVM
adapter controls are also explicit opt-in tests, separate from their portable
authored proof tests. The current checks do not refresh the older Release,
formatting or clang-tidy observations below.

G2 executes the actual admitted leaf in an isolated x86 reference worker and
the generated translation in two native x64 workers. An independent Python
oracle first checks the original measurements. Both native builds then match
every declared GPR, six final arithmetic flags plus preserved DF, return EIP,
ESP+8 and all 4,096 mapped memory bytes. The corpus contains 6,608 directed
cases, 10,000 random cases with seed `0x3434`, and one verified Training input
pair. It covers all 128 incoming flag/DF combinations, 12,153 unaligned stack
cases, each final flag outcome, 48*n wrapping boundaries and address wrapping.
The real input supplies only `n=0` and ECX base `330401912`; remaining entry
state is authored, so this is not a complete game-state replay.

The reviewed adapter policy is `straight-line-ssa-overwritten-af-of-v1`: exactly
two intermediate undefined values at AF/OF offsets 2069/2077 are overwritten
before any observation. LLVM verifies the module and matching State layouts;
the adapter separately checks SSA uses, storage aliases and the straight-line
overwrite proof. Final flags remain defined by the original SUB semantics.
This bounded policy cannot admit other observable undefined behavior.

Local evidence IDs are `reports/fixture-suite/report.json`,
`reports/mw3-leaf-lift/build.json`, and
`reports/mw3-leaf-differential/{report,verification}.json`. Game-derived slices,
IR, objects, worker results and traces remain private and ignored.
The public-material review is recorded separately as local evidence ID
`reports/mw3-leaf-differential/public-material-review.json`.

The final fixture recipe isolates compiler environments in child processes,
fixing repeated Visual Studio setup that exceeded Windows' command-line limit.
G1 passed again after that change. One subsequent G2 attempt rejected its fixed
original-address reservation/commit before executing the helper; its precise
Windows cause is unknown. The unchanged comparison retry and independent offline
verification passed. That failure is preserved in
`reports/mw3-leaf-differential/address-admission-failure-report.json`; it is not
counted among the 49 intentional rejection controls. The final completion review
is `reports/mw3-leaf-differential/completion-review.json`.

| Current evidence identity | SHA-256 |
| --- | --- |
| Authored lifting source digest | `5458ca4f59f0ffaf7ecadc37234b386a261e7920f79fa714c9f196b514ad7657` |
| G2 comparison report | `ec28ddbd0ceccf2a22c984564e18c18343dd9f838b5afb4c7343d3a687e2a5cd` |
| G2 build metadata | `3a51677200b38b30ec3500323ba4f937fdcfdcfc33f6c07ca7101add7359098e` |
| Deterministic G2 corpus | `93a4371870f199e05029599568f6611ff66f61b5f1cbbe77fe2c2a573e99d6cf` |
| Admitted leaf | `560c17c210dd7fedd7de601f42570c2a0473fa71962c13cfa85a005509a77c65` |

Replay on the matching Windows toolchain and private installed image:

```powershell
& tools/lifting/run_fixture_suite.ps1
& tools/lifting/build_mw3_leaf.ps1 -RunComparison
python tools/lifting/verify_mw3_leaf.py --report-dir reports/mw3-leaf-differential
```

The game-dependent recipe admits the exact full image and reviewed contract
before running any original instruction. It never launches MW3, runs its PE
entry point or injects native x64 code into the original x86 game. The ordinary
public build/test path remains independent of game ownership and the lifter.

## Historical bootstrap snapshot, 2026-10-06

The following environment, Debug/Release, formatting and analysis results were
recorded before the current G1 expansion and G2 work.

## Local environment

- Windows x64, Visual Studio 18 Community.
- MSVC 19.51.36256.0; Windows SDK 10.0.26100.0.
- CMake 4.3.1-msvc1; Visual Studio 18 2026 generator, x64 target.
- Python 3.14.7.
- clang-format and clang-tidy bundled with Visual Studio, LLVM 22.1.3.

## Results

| Check | Observed result |
| --- | --- |
| CMake configure and MSVC Debug build, warnings treated as errors | Passed |
| MSVC Release build, warnings treated as errors | Passed |
| CTest in Debug and Release | 2/2 suites passed in each configuration |
| Python synthetic tests | 27 tests passed |
| Runtime tests | Passed: serialization, unaligned access, mapping, overflow, permissions, failed-write preservation |
| C++ format-check | Passed |
| Direct clang-tidy check of guest_memory.cpp | No project diagnostics; standard-library diagnostics suppressed by tool defaults |
| Direct clang-tidy check of runtime_tests.cpp | One exception-escape diagnostic at main; reviewed as a tool false positive, detailed below |
| Unsupported Visual Studio clang-tidy integration | Configure rejects request explicitly; Ninja/Makefiles required |
| Local documentation links | Passed |
| Git ignore checks | User media, reports, build output and generated translations ignored |
| Supplied patch-package metadata analysis | Succeeded; hash remains unknown to game manifest |
| Patch-package game validation | Rejected as expected |
| Installed MW3 1.2 exact identity validation | Passed as `mw3-us-1-2-retail` |
| Installed MW3 1.2 strict metadata analysis | Passed |

Commands for the normal configured build:

```sh
cmake --build --preset default
ctest --preset default
cmake --build build/default --config Release
ctest --test-dir build/default -C Release --output-on-failure
cmake --build build/default --target format-check
```

Runtime test checks remain active in Release. PE tests use only authored fixtures,
including malformed directories/sections, ordinal and named imports/exports,
HIGHADJ relocation pairs, resource limits, full-hash validation and changed-byte
rejection. Disassembly adapter tests mock the external executable.

The clang-tidy diagnostic follows `std::map` sentinel allocation of one 72-byte
element into the library's allocation-size overflow branch. That branch cannot
overflow for this count, and the call is inside both standard and catch-all
exception handlers. The warning persists with explicit C++ exception flags. The
review therefore treats it as a clang-tidy 22.1.3/MSVC library analysis limitation;
the check remains enabled and its diagnostic has not been suppressed.

## Installed game identity

MW3 was installed through the original wizard to `D:\Projects\MW34Recomp\MW3`,
then updated through the user-completed 1.2 patch wizard. The admitted executable
is 2,384,384 bytes with SHA-256
`95bc2c114c9b2e5c5ada8e40ca78cc79470f862e45313ffad0d1e8e6d4d916bf`,
resource version `1.2.22.0` and registry version `1.2`. See
[media observations](media-inventory.md) for provenance and the preserved base
baseline, and [supported binaries](supported-binaries.md) for identity policy.
T06's install, provenance, exact-identity and negative controls are complete in
the current review. The historical snapshot below predates completion of the
bounded reconnaissance and G2 gate recorded above.

## Authored arithmetic experiment

LLVM 21.1.8 assembled/disassembled the nine-byte ADD fixture. Pinned Remill v6.0.1
built and emitted LLVM IR; LLVM verified the host bridge and identical State
storage layouts. MSVC x86 reference execution passed 10,144 edge/random cases
against an independent register/flag/stack/full-memory specification. Three
comparator corruption controls and 28 worker/adapter rejection controls passed.
O0/O2 native x64 workers each matched all 10,144 original cases with zero
mismatches. Windows Application Control had initially blocked execution; the
user turned Smart App Control off, its state was verified as `0`, and the full
pipeline then passed. The ADD arithmetic proof is complete. See
[the complete experiment record](fixture-add-experiment.md).
After integration, the ordinary Debug build and both CTest suites passed again;
the existing 27 synthetic binary tests remain independent of Remill. Worker C++
format checks, Python compilation and both PowerShell recipe syntax checks passed.

The subsequent three-fixture historical [G1 suite](fixture-suite-experiment.md) also passed signed branches,
partial-register writes, unaligned memory reads/writes, complete permitted-output
and surrounding-byte comparisons, and `ret 8` stack cleanup. Each of its three
fixtures has 10,144 valid cases, matching x86 and native O0/O2, for 30,432 valid
inputs and 60,864 native comparisons. All 105 rejection/bridge check entries pass,
including an unresolved-target rejection and 14 native memory-failure probes.

## MW3 reconnaissance and static function review

The installed 1.2 image still matches its exact supported profile. Known input
passes the independent validator; changed-code input and the unrelated patch
installer are rejected with exit 2. LLVM 21.1.8 game disassembly now runs through
the adapter after removing its unsupported standalone option terminator.
Python and LLVM header/import views agree, including all 474 ordinary entries
across 18 libraries. The bounded research backlog is documented in the
[API inventory](../games/mw3/docs/api-dependencies.md).

The [sub_00409ED0 dossier](../games/mw3/docs/first-function.md) records a complete
22-byte integer-leaf contract, caller/boundary evidence, and independent
LLVM/XED decoding. Exact-image/slice extraction and private guest IR generation
passed; six admission controls rejected altered input/metadata or public output.
The original executable remained unchanged. At this historical stage, guest IR
had not yet been adapted or executed natively: the shift-flag policy and x86 host
placement were pending. Both were subsequently implemented and tested for the
bounded G2 experiment above.

Normal CTest passed 2/2 after these changes, including all 27 synthetic binary
tool tests. New/changed Python files compile; 10 Markdown files' relative links
and the complete import CSV were checked. Local evidence and tool/source hashes
are under `reports/mw3-recon/`; original bytes and generated game IR are ignored.

## Not yet verified

The GitHub CI workflow is configured for Windows/MSVC and Linux/Clang but has not
been run remotely; no Linux native build is verified. Native x64 whole-game
startup, integration into the original x86 process, x87/floating-point fidelity,
calls/imports/indirect dispatch and deeper whole-image function/type recovery
remain queued. The isolated game reference execution and compiled native leaf
are now verified within the current G2 scope. Original-game main-menu startup was observed with
app-local dgVoodoo2, and the user reported playable training. A reported
terrain/view glitch appeared resolved after setting a 30 FPS ceiling, with
reduced smoothness. Broader runtime stability and the cause of the glitch remain
unverified; see the [MW3 findings](../games/mw3/docs/findings.md).
See [roadmap](roadmap.md) and the [initial-phase review](initial-phase-plan.md)
for the bounded completion assessment and next expansion probes.
