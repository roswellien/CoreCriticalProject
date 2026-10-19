# Roadmap

Updated 2026-10-13. The current strategy is [faithful recompilation with modern
platform services](faithful-modernization-plan.md): preserve original game logic,
connect a complete native execution path, and validate configurable enhancements
against an original-compatible mode. MechWarrior 3 U.S. retail1.2 is the current
target; Windows x64 and Vulkan are selected. The experimental native host now
executes a live menu, partial Training 1 and normal quit; whole-game fidelity,
performance and formal acceptance remain open.

## Model activation: 2026-10-16

[All prepared models](all-models-native-integration-2026-10-16.md) now have native
registrations:14MW5chassis plus the authored original-Strider variant. Original
Avatar/Firefly/Owens remain, parked STL Avatar excluded. Current standard launcher
uses the validated all-models host, unchanged graphics/HUD/music and current colors.
This is optional visual integration; native normal mapping and full combat/LOD/
muzzle/performance validation remain, with strict acceptance still131/144paused.

## Playtesting and frontend priorities: 2026-10-15

The user prioritizes fixing the native Mech Lab layout to unblock playtesting.
The first repair composes its original controls and3D preview in one consistent
canvas, with matching input and correct transitions. A centered original4:3
layout is an interim compatibility step, not the final menu design goal.

Future menus must adapt their layout to the actual resolution and aspect ratio,
including usable widget placement, readable text, scrolling and matching hit
testing. The settings menu must expose the implemented modern graphics options:
resolution/aspect handling, antialiasing, anisotropic filtering, scenery range
and fog behavior, and optional replacement visuals. Persisted settings and the
launcher must agree on the applied capabilities and values.

Dynamic lighting and normal mapping remain planned renderer work and may follow
soon once Lab usability and sustained playtests establish the next priorities.
Current base-color rendering does not implement normal mapping. New lighting and
material behavior require the actual geometry/material contracts, configuration
and comparative validation; settings must not claim those features work before
the renderer supports them. None of these goals changes strict acceptance credit.

For future MW5 replacement-model normal mapping, the user selected the
[12x-equivalent Bushwacker preview](mw5-normal-strength-high-preview-2026-10-15.md#approved-target-for-future-native-normal-mapping)
as the appearance target on 2026-10-15. Calibrate the native material response to
that reference (Blender Strength 10.20 from baseline 0.85), preserving the glass
exception and separate original-MW3 material tuning. This records the planned
enhanced look; it does not enable normal mapping or change a live default.

Reaffirmed on 2026-10-16 after the high-quality Mad Cat 12x/24x comparison: the
user saw little to no visible improvement at 24x and chose to keep 12x as the
target going forward. Retain 24x as experimental comparison evidence only.

Model direction selected on2026-10-16: retain the original MW3 Avatar, Firefly,
Owens and Strider until suitable higher-polygon donors are found. MW4 reviews
and the parked STL experiment do not replace that default. Continue optional
MW5 model candidates with maintained-but-well-used materials and the approved
12x preview target. [Supernova's prepared candidate](supernova-port-progress-2026-10-16.md)
completes initial visual work for all 14 locally matching MW5 chassis: seven
existing runtime registrations and seven offline candidates. The latter still
need native visual retarget, weapon/damage/LOD and live checks; this is not
completion of 14 playable ports. Preserve the frontend/playtesting priorities above.

The original Avatar, Owens, Firefly and Strider now all have upgraded-color
12x normal-map walking/light previews. The latest
[Firefly and Strider tests](mw3-firefly-strider-normal-preview-2026-10-16.md)
retain original geometry and 336 source poses per model, with matched on/off
camera and lighting. These are offline material reviews; native normal-map
integration and calibration remain separate renderer work.

The user subsequently authorized an authored detail pass on the stock Strider
design. The [first geometry prototype](strider-geometry-detail-prototype-2026-10-16.md)
adds bevels, armor layers, cockpit frames, vents and bearing covers while keeping
the original 16 moving controls and walk. It has 17,129 triangles versus 759;
matched offline previews and editable assets are prepared. The installed Strider
and gameplay are unchanged; native visual registration, damage and LOD checks
remain before any runtime adoption.

The [dynamic lighting and shadows investigation](dynamic-lighting-shadows-investigation-2026-10-15.md)
records current renderer limits and a staged implementation path: capture scene
geometry before projection/culling, add per-pixel lights, prove a bounded cast
shadow, then expand outdoor coverage and normal-map materials. No lighting or
shadow option has been enabled by this investigation.

The [GPU geometry development plan](gpu-geometry-development-plan.md) starts with
an isolated live CPU/GPU replacement-model comparison, then advances retained
world geometry, proven CPU-work removal, per-pixel materials/lights and shadows.
The development benchmark does not switch the playable launcher.

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
  [accepted receipt](../reports/m4-joint-startup131-root/acceptance-r1/report.json)
  is not a whole-M4 or whole-game percentage.
- Claude's new registry, lock, import, CRT-page, global-page and ENV probes are
  reusable prerequisites, with explicit policy/completeness limits. See the
  [work review](m4-claude-work-review-2026-10-11.md) and [acceptance history](m4-execution-plan-r14.md).
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
[current graphics work](live-native-rendering-current-work.md). Coordinate with
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
Moon now has an [experimental native startup target](pirates-moon-native-startup.md)
using the shared runtime with separate identities, dependencies and generated code;
its scripted Vulkan menu/Options/normal-quit slice now matches the original's
210 scene fingerprints. Physical input has not been manually checked, and PM
missions/cinematics remain unverified. MW4 remains a later target. Earlier research and evidence remain available;
[architecture](architecture.md) and [development workflow](m4-development-workflow.md)
retain current contracts. The [Claude prompt](claude-m4-continuation-handoff.md)
provides the execution-first continuation instructions.
