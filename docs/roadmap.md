# Roadmap

The [project milestone register](project-milestones.md) defines the current
goals, status and completion criteria from Bootstrap through playable native
MW3 and later modernization. M1, M2 and M3 are complete within their defined
scopes; M4, native startup and menus, is active. Its
[native image foundation](m4-image-foundation.md) and
[connected 27 selected initializers](m4-joint-startup27-review.md) pass their
bounded gates. The [full M4 plan](m4-startup-plan.md) still requires CRT/MFC services,
application callbacks and measured native menu/input behavior. The
latest prerequisites include an executing [three-service CRT entry prefix](m4-crt-entry-three-service-prefix.md)
and an independently reviewed [native FDIV writer](m4-crt-fdiv-native.md).
Its [bounded FDIV replay and entry review](m4-fdiv-replay-and-entry-prerequisites.md) now passes the measured
before-only corpus. The [initialized FDIV-to-entry composition](m4-crt-entry-data-review.md)
now passes, carrying actual producer state/data into compiled game entry.
The [actual CRT/math-error registration composition](m4-crt-entry-matherr-review.md)
now also passes 48 positive and 48 causal cases, with independent rich caller
FP metadata tests and a preservation repair across C++ failure handling.
The later [CRT/control composition](m4-crt-entry-control-review.md) passes
48 positive and 72 causal cases. The [first actual initializer interval](m4-crt-entry-initterm-review.md)
now continues through the complete `_initterm` provider over one null table
entry and returns to compiled game startup. Its 48 positive and 96 fault cases
pass independent review. The later [bounded mainargs prefix](m4-crt-entry-mainargs-review.md)
now compiles and executes the real 66-byte `__getmainargs` export and 140-byte
ordinary builder up to the required `GetModuleFileNameA` import at `0x7800BBD0`.
Its 48 positives and 120 causal cases pass review and the final
[root seal](../reports/m4-crt-mainargs/root-acceptance-r1/report.json) passes.
The causal scope is 118 source-predicted cases plus two retained mode43
artifact fixtures. That earlier gate supplies no API result. The later
[filename service](m4-crt-filename-review.md) now obtains the actual native
worker filename, copies its checked buffer, returns through the compiled
builder and refuses before the command-line pointer load at `0x7800BBD6`.
Its 48 normal / 24 causal cases and eight API units pass; independent compiled
review adds 90 scenarios and 180 rich host pairs. Argv/environment and complete
CRT startup remain open. The [new workflow](m4-development-workflow.md) and
[13 application batches](m4-application-workahead.md) pass bounded verification.
The selected initializer gate remains 27 of 144; joining its main-table CRT
caller remains open.
The [canonical numeric component](m4-fp-numeric-max-canonical-acceptance.md) is
accepted after raw and compiled review, with preceding failures preserved.
Its real preceding-root carry and imported provider now pass the selected
27-root joint gate. The
separate [live numeric test](mw3-live-native-numeric.md) has also passed a
user-confirmed Training session with verified native output and a clean monitored
exit. The [translated x64 address-helper test](mw3-live-native-helper.md) now also
passes one actual native publication with independent original/state/memory review,
user-confirmed Training entry/quit and a clean monitored exit. Both requested live
component tests pass. Next carry the reviewed command-line producer without
duplicate mappings or reseeding, and close locale/parser, allocator and
environment contracts before connecting the main initializer-table caller.
The remaining 117 nonzero roots and M4 menus remain required. The
[M2 acceptance record](m2-acceptance.md) binds all twelve requirements,
independent reviews, preserved failures and passing ordinary checks.
The [first x87 experiment](x87-control-experiment.md) reproduced a precision-control
defect in native O0/O2. The separate [control-word repair](x87-repair-experiment.md)
now passes 312 native comparisons. The [first numerical x87 gate](x87-numeric-experiment.md)
passes 480 native comparisons across twelve precision/rounding modes. The
[explicit spill and valid integer conversion gate](x87-expand-experiment.md)
passes another 1,248 native comparisons after repairing a reproduced extended
value ABI mismatch. The separate [finite conversion C1 repair](x87-c1-experiment.md)
now passes 768 native comparisons with the strengthened status mask, alongside
a passing spill regression and byte-identical replay of 3,096 earlier x87
records. The [multiplication/division and masked-special gate](x87-arithmetic-experiment.md)
now passes 6,528 native comparisons after repairing 96 lost signaling-NaN flags,
with exact NaN payload/sign and selected signed-zero/infinity/exception behavior.
A new replay preserves 4,968 earlier x87 records. The separate
[final-store C1 repair](x87-store-c1-experiment.md) now passes all 6,528 native
comparisons with C1 included, repairing 160 missing flags while preserving
14,760 earlier records byte for byte. The separate
[denormal/range gate](x87-range-experiment.md) now passes 7,680 native comparisons
after preserving and repairing 3,072 lost sticky DE flags, with independent
review and host MXCSR isolation. The
[authored call/global/import/indirect chain](m2-call-integration-contract.md)
passes 9,160 native comparisons; global memory, bounded indirect dispatch and
shared routing are verified. The separate
[boundary extension](m2-boundary-extension-contract.md) passes 9,184 native
comparisons with actual stack-argument consumption and 24 live timer-provider
observations through the selected bridge/context. The
[live x87 state gate](x87-state-experiment.md) passes 27,648 native observations
with separate logical/physical oracles. The final floating-point policy and
all twelve requirements are accepted in the [M2 audit](m2-completion-audit.md).
The [next-slice context](m2-next-slice-context.md) was accepted for planning.
M3 subsequently passed exact translation, flags and complete state/memory
validation for its separately admitted two-entry buffer component.

The [initial-phase execution plan](initial-phase-plan.md) contains the detailed
work queue, dependency graph, deliverables, acceptance gates and risk responses.
Its preferred endpoint is a real MW3 integer function passing original-x86 versus
native-x64 differential tests. This roadmap summarizes the milestones.

## MW3 Bootstrap

The first session establishes a buildable research foundation. It does not
establish that the complete game can be recompiled.

| Deliverable | State |
| --- | --- |
| Git repository, CMake/C++20 foundation and documentation | Implemented |
| Distribution policy and ignored user-media locations | Implemented |
| Binary validator and supported-binary manifest format | Implemented |
| PE sections/imports and metadata dependency reporting | Implemented; synthetic tests and strict installed-image analysis passed |
| Exact supported installed MW3 executable SHA-256 | Admitted as `mw3-us-1-2-retail`; exact validator passed |
| Game-specific dependency report and function recovery | Bounded reconnaissance R complete; 474 imports reviewed and sub_00409ED0 contract recovered |
| Native guest-memory library with automated tests | Implemented; restricted bootstrap semantics |
| Recompilation architecture and framework evaluation | G1 passed: ADD, branch, memory and shift leaves; 40,576 inputs, matching O0/O2, 135 rejection/bridge checks |
| First translated MW3 function | G2 passed 2026-10-07: original sub_00409ED0 versus generated native x64; 16,609 inputs, zero O0/O2 mismatches, 49 controls |
| First authored helper replacement in the original game | Passed 2026-10-07: one real call from the reviewed caller, zero mismatches; user confirmed Training loaded |
| Live game diagnostics | Implemented and exercised in real MW3; passive default reaches menu and Training; debugger capture remains opt-in after a menu crash |

The bounded **MW3 Bootstrap initial phase is complete**: reconnaissance R, G1
and G2 have passed with replayable evidence. This establishes the first isolated
native function, while whole-game recompilation remains open. See the
[G2 experiment record](mw3-leaf-experiment.md).

## Completed first MW3 comparison and M2 validation

The user also requested one function change tested in-game. The
[opt-in authored x86 hook](../tools/in-game-hook/README.md) replaces the reviewed
helper in the original process while preserving behavior and logging reference
comparisons. Offline and thunk tests pass. On 2026-10-07, the strict verifier
accepted one actual call to `0x00409ED0` from reviewed caller `0x00405173`,
with zero mismatches, and the user confirmed full launch into Training. This
completes the narrow first replacement test; extended gameplay stability remains
open. The separate native x64 G2 comparison now passes. The [first-function dossier](../games/mw3/docs/first-function.md)
records the evidence and its scope.

The [authored fixture suite](fixture-suite-experiment.md) records the pinned
toolchain, actual x86 reference worker and compiled x64 workers. ADD, signed
branches, partial-register writes, unaligned memory writes and callee stack
cleanup pass their bounded contracts at O0/O2. An authored shift fixture now
also verifies the overwritten intermediate-flag policy. G1 is complete; the user resolved
the earlier Application Control block. These tests do not depend on game files.

The original wizard installed MW3 to `D:\Projects\MW34Recomp\MW3`; the user
completed the 1.2 patch wizard. Exact validation and strict metadata analysis
passed for `mw3-us-1-2-retail`. See [media observations](media-inventory.md) and
[supported binaries](supported-binaries.md). This completes the install and
exact-identity portion of T06. Changed-code rejection now also passes. The
[memory map](../games/mw3/docs/memory-map.md),
[API inventory](../games/mw3/docs/api-dependencies.md) and
[first-function dossier](../games/mw3/docs/first-function.md) complete the bounded
reconnaissance and static contract review. Deeper whole-image recovery remains queued.

The reviewed dead-flag policy, original-address x86 reference host and generated
native x64 workers are implemented and tested. Both native builds matched all
16,609 original cases, with independent contract checks and 49 rejection controls.

The M2 expansion probes and bounded M3 component are complete. The complete
setter at `0x558290` passes 15,780 original cases and 31,560 native comparisons.
The connected consumer at `0x55A560` and persistent shared state pass 1,427
offline sequences, 3,968 original steps and 7,936 native O0/O2 comparisons with
zero defined differences. Every reachable instruction and dependency within
the two-entry boundary is recovered and reviewed. All twelve M3 requirements
and eight ordinary regression groups pass. See the
[M3 acceptance record](m3-acceptance.md) and [replay recipe](m3-replay.md).

Bootstrap admission is already accepted: the exact supplied executable
validates, a one-byte mutation fails, and the candidate functions have reviewed
boundaries and reproducible contracts. M3 preserves the complete bounded
subsystem definition in the [milestone register](project-milestones.md).
The accepted recordings are offline operations; in-game consumer use and
upstream allocator/timer/object paths remain unknown. M4's native image host
matches all 6,246,400 mapped bytes and preserves all 474 unresolved imports.
Its connected two-root graph passes 10,640 original records and 21,280 native
comparisons; the remaining fourteen import-free integer roots pass 8,512
original records and 17,024 native comparisons. Both have independent reviews,
and the fresh r9 host dispatches all sixteen selected roots in table order.
The asset parser's four payloads match 14,925 tokens. The first FP initializer
passes its directed comparison and independent review. Two more FP roots and
four cosine roots also pass independent directed reviews, bringing the
standalone FP total to seven. Square-root and both remaining import-free trig
roots now also pass independent review, bringing that total to ten. The
[reviewed connected 26-root gate](m4-mixed-startup-review.md) matches 1,248 original
and 2,496 native phases with full persistent State/page/call observations;
independent integration review is complete. Another 118 roots remain outside
this connected gate.
The isolated CRT
provider gate also passes 1,728 original / 3,456 native comparisons and review.
The [CRT control provider component](m4-crt-control-review.md) passes 3,264 original /
6,528 native observations and independent source-model review. The
[game control wrapper](m4-crt-control-integration-review.md) now passes connected
review of 192 original / 384 native records through unchanged Runtime r9.
The [control-result carry gate](m4-crt-control-carry-review.md) now passes
independent review of 648 original / 1,296 native phases through all 26 selected
initializers, with complete persistent State and memory observations. Broader
startup integration remains required.
The [numeric-max initializer](m4-fp-numeric-max-review.md) now passes independent
standalone review of 14,688 original / 29,376 native records; its shared
Runtime/MSVCP50 integration is open. The
[CRT command-line reference ownership gate](m4-crt-data-review.md) is also
reviewed. The separate [native command-line writer](m4-crt-commandline-native-review.md)
now passes independent review of 384 original / 768 native records using actual
OS bytes, plus 638 independent compiled checks. Complete provider initialization
remains open. The [Windows work-area service](m4-spi-workarea-review.md) passes
independent bounded caller/service review of 144 original and 288 native
records. It remains outside the connected startup gate. The isolated
[CRT math-error registration](m4-crt-matherr-review.md) passes independent
review of 1,536 original / 3,072 native records and 462 compiled assertions.
Callback execution and the complete CRT caller remain open.
The [bounded actual caller integration](m4-crt-entry-control-review.md) completes
this registration and floating-point control. The [first actual null interval](m4-crt-entry-initterm-review.md)
now executes CALL `0x5AC440` -> thunk `0x5AC598` -> compiled `_initterm` and
returns. The [mainargs composition](m4-crt-entry-mainargs-review.md) now continues
from source `0x5AC468` through the real ordinary builder and deterministically
refuses its first filename API import. It retains State3504, FX512 and all
sixteen pages, with 1,140 source identity bytes. The independently modeled
prefix covers 19 source PCs, sixteen accesses and four typed routes; 330 root
ordinary host pairs and 88,806 corruption denials pass. Successful argument
setup, the main table and selected 27-root caller remain later dependencies.
The later [filename service](m4-crt-filename-review.md) now resolves that import
and stops before the unconnected command-line producer read. The
[measured workflow](m4-development-workflow-results.md) uses direct bundle
comparison and keeps heavy file-processing phases staggered.
Imported FP routines, actual game service integration and application recovery
continue. Full startup, required services, menus and
input must pass before native gameplay work. The ordinary installed game need
not be launched for this isolated native gate.

## Minimal recompilation experiment

First prove the lifting integration on project-authored x86 fixtures. Pin the
lifter and LLVM toolchain before adoption. Then lift the identified MW3 leaf
function into LLVM IR, compile natively, and compare registers, flags, touched
memory and return behavior against the original in a local 32-bit test harness.
Use random, edge and recorded inputs. Keep proprietary inputs and derived
outputs local. Reject unsupported instructions and unresolved control flow.

Expand only after integer/ABI equivalence: memory accesses, indirect dispatch,
x87 rounding/exceptions, callbacks, then a narrow game subsystem. A synthetic
fixture passing is not evidence that MW3 runs. Evaluate M-HT/SR as the alternative
if the preferred lifter fails the gate in the research document.

## Runtime bring-up

Implement only observed APIs. Add PE image mapping/relocations, exact guest
stack and heap policies, import thunks, guest handles, callbacks and explicit
function dispatch. Keep Win32, graphics, input and audio interfaces separate.
The first rendering milestone is correct output. Establish the original timing
and simulation behavior before changing clocks or introducing a fixed step.

## Later milestones

The [work-ahead asset track](work-ahead-assets.md) can begin discovery, format
research and visual specifications alongside recompilation. Texture, video,
normal-map and effects preparation has separate readiness criteria; integration
depends on recovered loaders and rendering/playback behavior, with configurable
modernization accepted under M7.

Whole-game reachability and regression coverage come before configurable
widescreen, resolution/FOV, UI, controller/HOTAS, force feedback, audio and
renderer improvements. Linux and ARM64 need independent ABI, floating-point and
backend validation. macOS is exploratory. MW3 Pirate's Moon and the MW4 titles
remain future targets with no implementation commitments.

For texture rendering, the M7 graphics workstream orders the work by cause:
recover legacy sampling and material behavior; add filtered mip chains and
trilinear/anisotropic sampling to address texture sparkle and minification;
evaluate edge anti-aliasing (such as FXAA) separately; then consider optional
output upscaling. Temporal upscaling remains gated on renderer data such as
motion vectors and depth. These are configurable candidates on the eventual
selected backend; Vulkan is still an evaluation option, not a project decision.
See the [M7 texture-rendering gate](project-milestones.md#m7-graphics-and-texture-rendering-workstream).
