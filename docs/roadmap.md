# Roadmap

Updated 2026-10-13. The current strategy is faithful recompilation with modern
platform services (local reference: `docs/faithful-modernization-plan.md`): preserve original game logic,
connect a complete native execution path, and validate configurable enhancements
against an original-compatible mode. MechWarrior 3 U.S. retail1.2 is the current
target; Windows x64 and Vulkan are selected. The experimental native host now
executes a live menu, partial Training 1 and normal quit; whole-game fidelity,
performance and formal acceptance remain open.

## Native execution update: 2026-10-13

The [session summary](session-summary-2026-10-13-native-host.md) and
[execution map](e0-application-execution-path.md) record startup through the live
animated menu, Vulkan Training 1 scenes with the game HUD, and Quit -> confirm
through native shutdown to exit code 0. The user confirmed startup and walking
in interactive Training. Intro decoding by the recompiled Indeo IV50 codec was
tested with the window hidden. Heavy Training scenes reached about 13 fps on
the development system, up from about 2.6 fps earlier in the session.

Execution priorities are now: retest the built FPATAN correction for camera/leg
behavior; exercise the rest of Training and weapons; compare physics, AI and
timing against the original; improve performance; and review visible intro
playback. The [native-host build](../tools/m4-crt-heap-carry/README.md) requires
local staged images and generated lift output; it is not a portable release.
These observations add no accepted-function or whole-milestone credit.

Alongside recompilation, the project develops a D7VK-based Vulkan wrapper and
launcher for the original MW3 U.S. retail 1.2 executable, replacing dgVoodoo in
an isolated local profile. This original-executable compatibility track keeps
the original engine running while native recompilation progresses.

## Original-executable wrapper track

The [wrapper and launcher summary](d7vk-wrapper-launcher-summary.md) records
the working local setup and fixes as of 2026-10-13: DirectDraw4/Direct3D3 through
D7VK's matching D3D9/DXVK backend into Vulkan, GUI/CLI launch, high-resolution
4:3 and FOV-corrected widescreen profiles, MSAA/AF controls, and NTFS hard-link
switching of local AI texture banks. It documents video initialization and
Instant Action backbuffer fixes, binary identities, and launch instructions.

Next, validate sustained original-game scenes and transitions, configuration
regressions, and launch/restore behavior under the
[wrapper plan](mw3-d7vk-wrapper-plan.md). A portable setup/build procedure and
third-party license/notice inventory are needed before a wrapper release.
The current launcher requires prepared local files and a fixed checkout path.
Original media and generated game code remain local.

Wrapper operation advances the original EXE -> D7VK -> Vulkan boundary. It
does not complete the native E1-E4 checkpoints, authorize an original-code
fallback in the native host, or change the accepted **131/144** startup roots.

## High-resolution texture pack track

An optional [Hi-Res texture upgrade pack](hi-res-texture-pack.md) is the third
active project track. It develops AI-assisted mech, terrain/water, building and
selected effects artwork alongside recompilation and the original-EXE wrapper.
The current local audit records 39 cumulative archives and 19 complete primary
mech sets. The terrain inventory records 243 of 298 priority families upgraded
across all corresponding banks; 55 still need at least one replacement.
These are archive coverage counts, not full in-game visual acceptance.

Continue remaining bank coverage and mapped scene review, checking seams,
palette/alpha, effects timing, memory cost and original-mode restoration.
Normal/roughness maps and HUD vector artwork require future renderer support.
Keep assets local; public pack distribution remains subject to the existing
content/provenance policy. This work does not change native acceptance criteria.

## Current evidence

- M1-M3 retain their accepted bounded scopes. See the
  [milestone register](project-milestones.md), [M2 audit](m2-completion-audit.md)
  and [M3 acceptance](m3-acceptance.md).
- The selected startup gate remains **131/144**, with13 remaining. The
  accepted receipt (local reference: `reports/m4-joint-startup131-root/acceptance-r1/report.json`)
  is not a whole-M4 or whole-game percentage.
- Claude's new registry, lock, import, CRT-page, global-page and ENV probes are
  reusable prerequisites, with explicit policy/completeness limits. See the
  work review (local reference: `docs/m4-claude-work-review-2026-10-11.md`) and [acceptance history](m4-execution-plan-r14.md).
- Vulkan viewer and captured-scene replay tests are separate from a live renderer.
  Original-game play with isolated native replacements is separate from a complete
  recompiled game. The integrated native host now executes its own live menu
  and partial Training; fully validated faithful Training remains open.

## Primary execution queue

| Order | Checkpoint | Next deliverable |
| --- | --- | --- |
| E0 | Complete application path | Retail translated entry connected through provider attach, initialization and application callbacks; retain source map and remaining initialization/fidelity limits. |
| E1 | Integrated native host | One x64 development host executes startup and application services; close build reproducibility and service-contract limits. |
| E2 | Live native menu | Animated menu and input executed; normal Quit -> confirm reaches exit code 0. Continue lifecycle and error-path validation. |
| E3 | Live native Training frame | Training 1 scene and game HUD rendered through Vulkan; controlled original/native scene comparison remains open. |
| E4 | Faithful playable Training | Startup/walking observed; retest camera/legs and validate remaining steps, weapons, collision, AI, timing and audio. |
| E5 | Compatibility and release | Expand campaign/Instant Action, saves, error paths and extended play; document a reproducible user-data build. |
| E6 | Configurable modern features | Validate resolution/aspect/FOV, controls, filtering, interpolation and other selected enhancements against their affected original-compatible baseline. |

E0-E6 organize work alongside M1-M8; they do not alter accepted milestone criteria.
Modern platform services are built from the start. Gameplay/visual changes remain
explicit options and must not hide defects in original-compatible mode.

The table records executed boundaries and remaining work, not formal checkpoint
closure. Accepted selected roots remain **131/144**. Strict acceptance v6 still
fails on the pinned `docs/m4-startup-plan.md` hash; the decision to rerun reviews
or change the criterion remains with the user. This publication changes neither.

## Existing strict acceptance lane

Preserve the running controls composer and watcher; never inspect its active
SQLite contents or launch a duplicate. After actual successful closed output,
use admissionv2, independent composite reviewv3, actual45-field review, candidate
finalization, configuration, exact allowance review and strict acceptance. Keep
all39 gates/841 typed predicates and existing whole-input conservation rules.
Planning/doc changes do not authorize running the long chain in this session.

Current141 still needs collection-completeness confirmation, CRT/ENV policy
review/admission, the53 inherited-check rebind, the full paired141 comparer and
acceptance. Connected HYPOT, version and loader remain open. Reuse existing probe
results; do not repeat captures or create more evidence adapters by default.
This lane can progress alongside independent execution work, with heavy readers
serialized. Completing144 does not by itself complete startup, menus or Training.

## Reuse before rebuilding

Start from [application workahead](m4-application-workahead.md), the
[MFC receiver](m4-mfc-app-receiver-adapter.md), [reader research](m4-reader-bridge-research-r1.md),
[video contract](m4-video-backend-contract-r1.md), [native Vulkan build path](m4-native-vulkan-build-path-r1.md),
[presenter extraction review](m4-vulkan-presenter-extraction-review-r1.md) and
current graphics work (local reference: `docs/live-native-rendering-current-work.md`). Coordinate with
existing writers. Capture-to-Vulkan transport may prove a renderer boundary but
must remain labelled original-process diagnostic execution until translated game
producers drive it. Cinematic/HUD/asset work remains separately scoped.

Audit reusable tools only for a specific translation or runtime gap. Retain the
existing lifter and CPU/ABI evidence unless a measured blocker requires a change.
No instruction interpreter or original-binary fallback is authorized for the
production native host. A justified host bootstrap must reproduce required
initialization, callback and cleanup behavior; it cannot bypass them.

## Validation and later scope

Use narrow contract/resource and original/native checks for the changed boundary;
reserve full closure for the applicable milestone criteria. Record actual executed
PCs, unresolved services, ABI/FP state, input provenance and ownership. A passing
fixture or static call graph is not live gameplay. Do not add another verifier
layer without explaining its uncovered criterion or concrete execution defect.

Modern texture filtering and antialiasing follow recovered sampling/material
behavior. Higher rendering rates must not alter the original simulation cadence.
Temporal upscaling needs validated depth/motion inputs and is optional, not the
next startup requirement. Vulkan remains selected. See the
[M7 workstream](project-milestones.md#m7-graphics-and-texture-rendering-workstream).

Linux, ARM64 and macOS require separate platform/ABI/backend validation. Pirate's
Moon and MW4 remain later targets. Earlier research and evidence remain available;
[architecture](architecture.md) and [development workflow](m4-development-workflow.md)
retain current contracts. The Claude prompt (local reference: `docs/claude-m4-continuation-handoff.md`)
provides the execution-first continuation instructions.
