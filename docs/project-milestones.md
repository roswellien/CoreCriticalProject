# MW34 RECOMP goals and milestones

Established: 2026-10-07. First implementation target: MechWarrior 3, admitted
U.S. retail 1.2 executable. First native host target: Windows x64.

Current acceptance: **103/144 selected startup initializers**, with **41 remaining**,
as recorded in the [milestone update r6](project-milestones-r6.md) and
[103-root evidence](m4-progress-startup103.md). Inventory coverage is separate
from total M4 or project completion.

The user selected Vulkan as the graphics backend target on 2026-10-08. Bounded
[graphics learning/prototyping](vulkan-learning-prototype.md) has begun separately
from native startup; it does not advance native menu/Training acceptance.

The project goal is a maintainable native recompilation that preserves original
gameplay and uses each user's own game data. Modernization is configurable and
follows measured compatibility. Original assets, binaries, complete traces and
game-derived translations stay local.

## Milestone register

| ID | Milestone | Current state | Definition of done |
| --- | --- | --- | --- |
| M1 | MW3 Bootstrap | Complete within its bounded scope | Buildable repository; admitted image and version provenance; reviewed PE/API inventory and research backlog; pinned authored x86-to-x64 comparisons; one actual MW3 function compared with its compiled native translation; reproducible evidence. |
| M2 | CPU and ABI validation | Complete 2026-10-07 within its defined bounded scope | Reviewed contracts and original/native comparisons for required floating-point behavior, direct calls, global data, an observed import bridge and bounded indirect dispatch. Unsupported behavior is identified and rejected. Define the guest state and routing needed for the next game slice. |
| M3 | First native game subsystem | Complete 2026-10-07 within the accepted two-entry buffer component | Select and recover a bounded subsystem from evidence; compile its reachable code into the x64 host; implement its observed dependencies; compare outputs and state against the original on directed and recorded workloads. |
| M4 | Native startup and menus | Active; 103 selected initializers accepted on 2026-10-09, with 41 of 144 remaining. Actual original/native O0/O2 execution, persistent source/ownership comparisons and independent controls pass. Thread/exception-chain support, remaining initialization, environment/mainargs, startup scheduling and native menus remain open. [Current evidence](m4-progress-startup103.md). | A project-built x64 executable loads admitted user data, initializes required services, presents correct menus and responds to input. File/configuration, graphics, input and audio dependencies have explicit implementations; unresolved required paths fail visibly. |
| M5 | Playable native Training mission | Planned | Load and play Training through the native runtime, including movement, weapons, collision, AI, HUD, input and audio. Complete a recorded test scenario with measured original-behavior comparisons and no unresolved required execution paths. |
| M6 | Gameplay compatibility and reproducible release | Planned | Expand to campaign and Instant Action; compare representative missions, saves and timing behavior; pass defined regression and extended-play scenarios; document supported configurations, remaining defects and an asset-free user build/install recipe. Choose soak durations and performance thresholds from measured baselines before testing this gate. |
| M7 | Configurable modernization | Later | Each improvement has an original-behavior baseline, explicit settings and regression checks. The graphics workstream first establishes correct texture/material sampling, then adds filtered mip chains and capability-limited anisotropic filtering, followed by separately configurable edge anti-aliasing and optional output upscaling. Acceptance includes original/modern comparison scenes, motion and distance shimmer checks, alpha/UV/color fidelity, memory and frame-cost measurements, and a tested fallback profile. Other candidates include smooth independent rendering, resolution/aspect/FOV/UI support, modern devices, audio, authored textures and normal maps after geometry/material behavior is recovered. |
| M8 | Additional platforms and games | Later | Validate Linux and potentially ARM64 with independent ABI/floating-point/backend tests; evaluate macOS separately. Admit and analyze Pirate's Moon and each MW4 title independently before implementation. |

Milestones indicate evidence and dependencies, not completion dates or promises
of whole-game feasibility. A reproduced blocker can complete a research probe;
it cannot satisfy a compatibility or gameplay gate that still fails.

### M7 graphics and texture-rendering workstream

This work is gated behind recovered rendering behavior and the M6 compatibility
baseline. Vulkan is now the selected backend target; implementation and minimum
feature requirements remain subject to recovered graphics behavior and measured
requirements. Implement each stage behind settings so the original-compatible
path remains available for comparison and regression.

1. **Sampling baseline and material contract.** Record source texture dimensions,
   format/color space, alpha or color-key behavior, UV transforms, wrap/clamp
   modes, filtering and current distance behavior. Capture representative
   Training scenes at native render resolution and while moving. Preserve
   markings, seams, material response and legacy transparency before enabling
   enhanced assets.
2. **Mipmaps and texture filtering.** Build or load complete mip chains with a
   quality-tested downfilter; preserve alpha coverage and avoid color fringes
   around transparent/keyed edges. Add selectable point/linear magnification,
   bilinear/trilinear minification, mip LOD bias and anisotropic filtering.
   Query and clamp anisotropy to device support. Verify minification at distance,
   oblique ground/mech surfaces, UV seams, tiled wrapping and memory use. These
   controls directly address high-frequency texture shimmer and sparkle.
3. **Anti-aliasing.** Measure geometry-edge aliasing separately from texture
   shimmer. Add a configurable, low-cost post-process such as FXAA only after the
   resolved image/color path is understood; compare sharpness and text/HUD
   readability. Evaluate MSAA only where the render target and legacy blending
   path support it. Do not count edge AA alone as a fix for missing/poor mipmaps.
4. **Optional resolution upscaling.** Keep internal render resolution and output
   resolution as separate settings. First validate ordinary spatial scaling; an
   optional FSR 1-style spatial upscaler can be evaluated on an already
   anti-aliased frame. Temporal FSR-style upscaling is a later option only if
   motion vectors, depth, jitter, exposure and UI/reactive handling can be
   supplied and validated. Upscaling is a performance/output-resolution feature,
   not a substitute for correct texture sampling; frame generation is outside
   this texture-quality gate.
5. **Asset and runtime validation.** Compare original and approved AI texture
   packs at matching scenes, camera distances, motion, native and higher output
   resolutions. Check that authored high-frequency detail settles through the
   mip chain without sparkle, while markings, alpha, colors and UV alignment
   remain correct. Record frame time, VRAM use, device limits and fallback behavior.

The gate passes when a documented default profile improves the approved target
scenes without regressions in the original-compatible mode, with each filter,
AA and upscaling feature independently switchable and tested. Use representative
captures and motion clips, not only enlarged still previews. FSR API/version and
backend choices remain implementation decisions until this gate is scheduled.

Current M4 additions include a [native three-service CRT entry prefix](m4-crt-entry-three-service-prefix.md),
a [native FDIV writer](m4-crt-fdiv-native.md) with independent source/state/API
and failure review, and an accepted [canonical numeric component](m4-fp-numeric-max-canonical-acceptance.md)
with 57,024 independently checked native phases. The isolated FDIV original
capture has completed 48 runs; the [bounded FDIV replay and entry review](m4-fdiv-replay-and-entry-prerequisites.md) now
passes within the explicit CPU/FP/provider-page transport scope. The
[initialized-data entry composition](m4-crt-entry-data-review.md) now passes
48 positive O0/O2 compositions and 24 causal denials with complete state/page
carry and host preservation. The [selected 27-root gate](m4-joint-startup27-review.md)
also passes actual original/native, provider checkpoint and independent failure
review. Earlier failures remain preserved. Complete CRT, the remaining 117
nonzero initializer roots and native menus remain open.

A [live numeric initializer x64 test](mw3-live-native-numeric.md) passed on
2026-10-08: one actual original-game startup callback consumed verified x64
worker output through an x86 bridge, with full CPU/FP/ENV/global comparison.
The admitted live SSE precision flag and actual CRT call route are retained.
This separate live result did not advance the joint gate; the later 27-root
startup composition above supplies that acceptance. M4 remains active.
The user subsequently confirmed launch, Training gameplay and manual quit through
the native numeric launcher without issues; its fresh trace independently verifies
native publication and a clean monitored exit. See the linked Training receipt
in the live numeric record. Extended stability remains open.
The [live native address-helper test](mw3-live-native-helper.md) now also passes:
one actual game call published the generated x64 result after a complete original
comparison and independent BEFORE-only receipt review. The user confirmed launch,
Training entry and quit, with exit code zero and a clean passive monitor. Both
requested live component tests are accepted; shared native startup integration
and extended gameplay stability remain open.

## What is complete now

- M1 reconnaissance covers the exact executable and 474 ordinary imports, with
  explicit open questions for deeper recovery.
- Four authored integer fixtures pass 40,576 original inputs and 81,152 native
  O0/O2 comparisons, with 135 rejection/bridge checks.
- The isolated MW3 helper `sub_00409ED0` passes 16,609 inputs and 33,218 native
  O0/O2 comparisons, with zero mismatches and 49 rejection controls.
- The separate authored x86 replacement logged one verified call in original
  MW3, and the user confirmed Training loaded.
- Live diagnostics and launch tooling exist. Extended gameplay stability and
  complete detection of graphics/physics defects remain unproven.
- The numeric initializer has two independently verified actual x64-worker
  startup callbacks in separate original-game sessions. The user confirmed
  Training gameplay and quit in the second session; both exited with code zero.
  Whole-game native execution and extended Training stability remain open.
- The selected native startup sequence now connects 27 initializers, including
  numeric-max, with 1,296 original phases compared against 2,592 native O0/O2
  phases. Complete state/page carry and meaningful terminal failure checks pass.
- The native FDIV producer now supplies initialized data to compiled CRT entry,
  which completes actual `__setusermatherr` registration and floating-point
  control setup. The [first-null composition review](m4-crt-entry-initterm-review.md)
  also executes the complete `_initterm` provider over its first null-only
  interval, returning to actual game continuation. Its 48 positive / 96 fault
  cases pass complete persistent state review; 124 independent rich caller
  hardware pairs pass. The [latest mainargs composition](m4-crt-entry-mainargs-review.md)
  extends the real `__getmainargs` and ordinary argument builder to their first
  required `GetModuleFileNameA` import. Its 48 positives and 120 causal cases
  pass review; 118 have source predictions and two retain the earlier mode43
  artifact-specific scope. Root checks cover 330 ordinary host pairs and
  88,806 corruption denials; independent compiled checks include 128 rich
  host pairs. The final [root seal](../reports/m4-crt-mainargs/root-acceptance-r1/report.json)
  passes. Argument/environment outputs, the main initializer table and
  menus remain open.
- The later [actual filename service](m4-crt-filename-review.md) passes 48 normal
  and 24 causal sequences plus eight API units. Independent compiled review
  passes 90 scenarios and 180 rich hardware pairs. It returns through the
  actual compiled builder, then refuses before the command-line pointer load
  at `7800BBD6`. The [new workflow](m4-development-workflow.md) adds reviewed
  bundles, stage timing and conflict-checked manifest merging; the
  [application work map](m4-application-workahead.md) orders 13 dependency batches.
- The address helper has one independently verified actual x64-worker call in
  the original game, including full admitted CPU/flags, preserved FP/ENV and
  unchanged shadow memory. The user confirmed Training entry and quit, and its
  session exited with code zero without passive-monitor alerts or lost segments.

Original-game playability with compatibility software, an authored x86 hook,
and the isolated native x64 function are separate results. M4/M5 require the
project's own native game executable and runtime.

Evidence: [Bootstrap review](initial-phase-plan.md),
[validation record](bootstrap-validation.md),
[integer fixture suite](fixture-suite-experiment.md),
[native MW3 leaf](mw3-leaf-experiment.md).

## Completed milestone: CPU and ABI validation

All twelve M2 requirements are accepted in the
[final acceptance record](m2-acceptance.md) and
[completion audit](m2-completion-audit.md), following a full independent
requirement review and root acceptance. All eight ordinary test groups pass
with the native LLVM adapter tests enabled. Fresh G1/G2 replays preserve all
171,555 earlier records byte for byte; earlier x87/integration failures and
successful measurements remain preserved separately.

The first M2 probe compares authored `FNSTCW [ECX]; RET` control-word storage
and preservation. It is complete as a research experiment: original hardware
preserves all twelve tested PC/RC settings, while native O0/O2 each reproduce
eight precision-control incompatibilities. All other admitted state and memory
match. See the [measured experiment](x87-control-experiment.md).

The separate [control-word repair](x87-repair-experiment.md) now passes twelve
store cases and all 144 entry/loaded-setting transitions: 312 native O0/O2
comparisons with zero mismatches. The original failure and baseline toolchain
remain preserved. The [first numerical gate](x87-numeric-experiment.md) now passes
240 original directed add/subtract cases and 480 native O0/O2 comparisons,
including all twelve precision/rounding modes, signed zero and precision status.
The separate [spill and conversion gate](x87-expand-experiment.md) now passes
624 original cases and 1,248 native O0/O2 comparisons. It verifies explicit
binary64 intermediate stores/reloads and valid rounded signed32 conversions.
An incompatible extended-value CRT call was reproduced, preserved and repaired
with a checked pointer bridge. The separately strengthened
[finite conversion C1 gate](x87-c1-experiment.md) now matches all 384 original
cases and 768 native O0/O2 comparisons, including the 111 C1 settings previously
omitted per build. The new spill regression also passes; 3,096 earlier x87
records replay byte-identically. The separate
[multiplication/division and masked-special gate](x87-arithmetic-experiment.md)
now passes 3,264 original cases and 6,528 native O0/O2 comparisons after preserving
and repairing 96 missing signaling-NaN exception flags. Exact NaN payload/sign,
signed zero, infinity and selected masked invalid/divide-by-zero behavior match.
A fresh replay preserves 4,968 earlier x87 records byte for byte. Its raw results
identify final-store C1 differences excluded from that earlier gate. The separate
[final-store C1 repair](x87-store-c1-experiment.md) now passes all 3,264 original
cases and 6,528 native O0/O2 comparisons under the stronger status mask,
repairing all 160 previously missing flags. Independent exact oracles confirm
the saved records; a fresh replay preserves 14,760 earlier records byte for byte.
The separate [denormal/range gate](x87-range-experiment.md) now passes 3,840
original cases and 7,680 native comparisons under the same stronger status
mask, after preserving and repairing 3,072 lost sticky DE flags. Two independent
reviews pass; host MXCSR isolation and all earlier frozen evidence are verified.
The [authored call/global/import/indirect chain](m2-call-integration-contract.md)
passes 4,580 original cases and 9,160 native comparisons, with an independent
[root review](../reports/m2-integration/root-review/report.json). It establishes
bounded global memory, indirect dispatch and shared replacement routing.
The separate [boundary extension](m2-boundary-extension-contract.md) proves
actual stack-argument consumption independently of poisoned EAX in 4,592
original and 9,184 native observations. Its selected bridge/context also
executes the actual timer provider in 24 live observations. The
[live x87 state gate](x87-state-experiment.md) passes 13,824 original and 27,648
native observations for push, pop, exchange and free, with separate logical
and physical independent oracles, exact worker replays and host isolation
checks. The [floating-point policy addendum](m2-acceptance.md#floating-point-policy-addendum)
consolidates all admitted domains and tested exclusions. General x87, unmasked
guest traps and unvalidated game execution remain denied.

The [next-slice context and dependency contract](m2-next-slice-context.md) is
accepted for M2 planning after an [independent image-byte and map review](../reports/m2-slice-admission/root-review/report.json).
It selects the complete observed function at `0x558290`, with two stack inputs,
five global dword writes and no outgoing calls. Six admission test groups pass;
the larger timer wrapper's unresolved dependencies remain recorded. This M2
planning admission did not authorize execution. M3 subsequently supplied the
exact translation, flag policy and original/native comparison in its separate
[accepted component](m3-acceptance.md).

Each added probe is done when its contract, original instructions, generated
native path or precise failed lowering, expected result and measured outcome
are saved with tool/source identities and a replay recipe. A successful probe
does not complete M2 or validate all floating-point behavior. A reproduced
limitation leads to a smaller discriminating test and a documented repair or
tool-selection decision before broader translation.

The complete floating-point gate must address control/status and tags,
rounding and precision modes, extended intermediates, spills, conversions,
signed zero, infinities, NaNs, denormals and exceptions under an explicit policy
for defined and undefined observations. An epsilon-only comparison or a
fast-math workaround does not satisfy this gate.

The [completion audit](m2-completion-audit.md) records acceptance of every
mandatory M2 item. The [first M3 comparison contract](m3-slice-contract.md)
specified the complete CPU, memory and preserved-state observations for the
whole function at `0x558290`. The complete setter and connected consumer now
pass M3's separate dependency, directed-workload and recording gates below.

## Completed milestone: first native game subsystem

All twelve unchanged M3 requirements are accepted for the complete shared-state
setter at `0x558290` and strided-word consumer at `0x55A560`. Both complete
functions are statically compiled into native x64 O0/O2 entries with checked
guest memory and routing. The component has persistent globals, buffers and
guest context, with no outgoing game/API dependency in its recovered graph.
See the [acceptance record](m3-acceptance.md) and [replay recipe](m3-replay.md).

The prerequisite whole-function gate passes 15,780 original cases and 31,560
native comparisons. The connected gate passes 1,427 sequences, 3,968 original
steps and 7,936 native comparisons, with zero defined differences. Independent
reviews validate actual CPU, full mapped pages, native State, floating-point
observations and ordered native memory events. All eight ordinary regression
groups pass; earlier M1/M2 evidence and M3 failures remain hash-bound.

These are offline original-operation recordings. No in-game consumer use or
upstream allocator/timer/object implementation is asserted. Guest x87 metadata
is restricted to zero after an independent probe reproduced external loss of
nonzero metadata; actual zero metadata is still compared exactly. The accepted
host restoration scope and remaining exclusions are recorded explicitly.

M4 is active. The [native image foundation](m4-image-foundation.md) maps all
five regions and 6,246,400 bytes correctly against an independent file model
and Windows' passive image view, with all 474 imports preserved and unresolved.
The [first real startup initializer](m4-initializer-experiment.md) passes 5,320
original cases and 10,640 native O0/O2 comparisons with zero defined differences,
including independent full-state review and causal admission controls.

The connected first and second initializer graph now passes 10,640 original
records and 21,280 native comparisons. The fourteen remaining import-free
integer roots pass 8,512 original records and 17,024 native comparisons.
Independent raw-record reviews pass for both components. The
[fresh sixteen-root host](m4-integer-integration-r9-contract.md) executes those
selected callbacks in table order on one persistent admitted image and State;
its combined observations have a narrower scope than the component gates.
The [asset parser](m4-assets-contract.md) matches all 178 archive entries and
14,925 tokens in four checked payloads, including `MAINMENU`.

The [first required FP initializer](m4-fp-first-experiment.md) now matches 2,016
original directed records and 4,032 native comparisons after separately
retaining and repairing rounding/accumulated-exception failures. Its final
independent review passes. The [two additional FP roots](../reports/m4-fp-simple-batch/independent-review-r1/report.json)
pass 5,952 original / 11,904 native directed measurements and independent
review. The [four cosine roots](m4-fp-cosine-review.md) pass 6,144 original /
12,288 native directed measurements and independent review after preserving
and repairing their measured status defects. The square-root root passes 5,760
original / 11,520 native directed records and independent review. The two
remaining import-free trig roots pass 9,024 original / 18,048 native directed
records and independent review. All ten import-free FP roots now have bounded
standalone reviews. The [reviewed connected gate](m4-mixed-startup-review.md)
runs all 26 selected integer/FP targets on persistent image/State: 1,248 original
phases match 2,496 native phases, with independent integration review complete.
The [isolated CRT provider gate](m4-crt-provider-experiment.md) passes 1,728
original / 3,456 native comparisons and independent review. Those services
use authored callback fixtures. The complete
[CRT control provider component](m4-crt-control-review.md) also passes independent
source-model review of 3,264 original / 6,528 native records. The complete
[game control wrapper](m4-crt-control-integration-review.md) now also passes
independent connected review of 192 original / 384 native records through
unchanged Runtime r9. The [control-to-initializer carry gate](m4-crt-control-carry-review.md)
now passes independent review of 648 original and 1,296 native phases through
the 26 selected callbacks, plus 2,016 independent compiled checks. Broader
CRT services and application dependency recovery remain open.

The imported [numeric-max initializer](m4-fp-numeric-max-review.md) now passes
independent standalone review of 14,688 original and 29,376 native records,
including actual provider-return checkpoints and complete State/page/event
checks. Its later [selected joint integration](m4-joint-startup27-review.md)
now passes, including actual preceding-root carry and failure review. The
[CRT command-line reference-data gate](m4-crt-data-review.md) also passes
independent original and ownership review. The separate
[native command-line writer](m4-crt-commandline-native-review.md) now passes
independent review of 384 original / 768 native observations, with actual OS
bytes and 638 independent compiled checks. Broader provider initialized data
remain open. The [Windows work-area service](m4-spi-workarea-review.md) passes
independent review of 144 original and 288 native records, with checked RECT
ownership and actual x86 argument-cleanup observations. Its bounded handwritten
caller remains outside the shared startup gate. The isolated
[CRT math-error callback registration](m4-crt-matherr-review.md) now passes
independent review of 1,536 original / 3,072 native observations and 462 compiled
assertions. It stores callback data; callback execution and the complete CRT
caller remain untested.

Its [actual game CRT caller composition](m4-crt-entry-matherr-review.md) passes
independent source and compiled review of callback registration. Those rich
caller tests exposed and repaired metadata loss during C++ failure handling;
earlier entry-data fixtures had zero legacy metadata. The later
[control composition](m4-crt-entry-control-review.md) carries this state through
the complete game wrapper, import thunk and `_controlfp` provider. The
[first actual initializer interval](m4-crt-entry-initterm-review.md) now executes
CALL `0x5AC440` to `_initterm` thunk `0x5AC598`, reads the null-only interval
`[0x5E0248,0x5E024C)` and returns. Its compiled game continuation reaches
`__getmainargs` at source `0x5AC468`, owning IAT `0x5BB514`. The new
[bounded mainargs prefix](m4-crt-entry-mainargs-review.md) enters the complete
compiled 66-byte export and its complete 140-byte ordinary builder,
then refuses the real filename API CALL at `0x7800BBD0` / IAT `0x7802E018`.
The later [filename service](m4-crt-filename-review.md) now executes that API,
publishes its checked buffer and stdcall return, then stops before the required
command-line load `0x7800BBD6 -> 0x78037174`. Next carry the reviewed
command-line producer into the existing mappings without
duplicate mappings or reseeding, and establish locale/parser, allocator and
environment contracts. Then connect the main initializer-table caller.
The selected count remains 27 of 144; 117 roots and full native startup/menu
behavior remain open. Ordinary game play is not needed for this isolated native
gate; a future live recording will have a separate test request.

The [M4 plan](m4-startup-plan.md) keeps all twelve full startup/menu requirements
open beyond these prerequisites. Sixteen of 144 nonzero CRT initializer roots
have reviewed integer execution; ten other roots have reviewed standalone
FP execution. Their connected gate now includes the imported numeric-max root
and passes independent review at 27 selected roots; 117 nonzero initializer
roots remain outside it.
CRT/SEH/MFC context, remaining initializers,
application callbacks, services and native menu/input behavior remain required.
Native menus and Training have not been established.

## Reporting rules

Keep each experiment's status separate from the enclosing milestone. Report
implemented, tested, blocked and unknown states explicitly, using source and
binary hashes while the repository remains uncommitted. Update this register
and the [roadmap](roadmap.md) when evidence changes. Preserve prior failures;
never count an unavailable input or failed execution as a passing comparison.

The M3 subsystem is selected and accepted above. Choose the M5 scenario and M6
soak/performance thresholds when preceding evidence supports those decisions.
Dates and broader effort estimates remain unset until the execution and
dependency gates reveal them.
