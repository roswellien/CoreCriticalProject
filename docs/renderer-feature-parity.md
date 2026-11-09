# Renderer and feature parity

Status as of 2026-11-09 for CoreCriticalProject integration commit `ace166e24b8304ce241e6a84bfd8ed15fe3edb1e`. The target is the native MW3-RE runtime in `runtime/mw3-re/`. Keep original gameplay and stock presentation available while adding opt-in Core Critical enhancements. The legacy runtime is a behavioral comparison point. See the [project roadmap](roadmap.md), [contribution guide](../CONTRIBUTING.md), and [distribution policy](legal.md).

This page tracks package status and milestone gates. Use GitHub issues to claim, scope and track individual work slices.

## Current status

| Package | Integration status and evidence |
| --- | --- |
| WP00A, WP00B, WP18 | Merged baseline reconciliation, typed renderer configuration, and Vulkan platform boundaries. Platform qualification remains a separate milestone. [Baseline](https://github.com/roswellien/CoreCritical-MW3-RE/pull/24), [typed bridge](https://github.com/roswellien/CoreCritical-MW3-RE/pull/25), [platform boundary](https://github.com/roswellien/CoreCritical-MW3-RE/pull/26) |
| WP01, WP02A, WP02B | Merged normal and material sidecar readers, first authenticated world-surface binding, and multi-category binding. Preserve exact-key rejection, mission reload invalidation, and the 512 MiB decoded world-normal cache budget. [Contracts](https://github.com/roswellien/CoreCritical-MW3-RE/pull/29), [first surface](https://github.com/roswellien/CoreCritical-MW3-RE/pull/32), [category scaling](https://github.com/roswellien/CoreCritical-MW3-RE/pull/34) |
| WP03A, WP03B | Merged mission lighting, verified environment pack integration, sealed-map sky suppression, and directional BWSFM material response. [Mission lighting](https://github.com/roswellien/CoreCritical-MW3-RE/pull/38), [packs](https://github.com/roswellien/CoreCritical-MW3-RE/pull/37), [sealed maps](https://github.com/roswellien/CoreCritical-MW3-RE/pull/39), [material response](https://github.com/roswellien/CoreCritical-MW3-RE/pull/40) |
| WP04A, WP04B | Merged native local-light producers and per-view tiled GPU light lists. Keep camera/view ownership, bounds, and fallback checks when adding consumers. [Local lights](https://github.com/roswellien/CoreCritical-MW3-RE/pull/41), [tiled lists](https://github.com/roswellien/CoreCritical-MW3-RE/pull/43) |
| Per-map environment follow-ups | Merged pack ambient override, sky tint and brightness, glow, horizon blend, and SDR visibility tuning. The C1M2 SDR comparison reported mean capture brightness of 8.49 before tuning and 12.24 after tuning on a 0–255 scale. Preserve HDR behavior and mission-specific reset. Sky grading is a separate open fork draft. [Ambient](https://github.com/roswellien/CoreCritical-MW3-RE/pull/46), [tint](https://github.com/roswellien/CoreCritical-MW3-RE/pull/53), [glow](https://github.com/roswellien/CoreCritical-MW3-RE/pull/54), [horizon](https://github.com/roswellien/CoreCritical-MW3-RE/pull/55), [SDR](https://github.com/roswellien/CoreCritical-MW3-RE/pull/57), [grading draft](https://github.com/roswellien/CoreCritical-MW3-RE/pull/56) |
| WP05 headlights | In progress. The fork prototype proved the C1M1 `L` toggle with one synthetic Mad Cat hip attachment. The deliberately mismatched digest submitted zero spotlights and matched Off pixel for pixel. A local port is in progress on the WP05 topic branch. Integrated live proof and real stock and Atlas coverage are outstanding. |
| WP06 onward | Remaining qualification and implementation are listed below. A merged package is evidence for the scope of its checks. |

[Import PR #277](https://github.com/roswellien/CoreCriticalProject/pull/277) preserved the project and fork histories on `develop`. Runtime promotion to `main`, signed delivery, and validation on a clean non-development PC have separate release gates.

## Next contributor slice

**WP05 — native mech headlights.** Start with the owner of the existing WP05 branch before making a second port. Trace input from the native mission and mech code into the local-light submission path under `runtime/mw3-re/src/frontend/core_critical/`. Keep `L` as the player toggle. Keep mount lookup tied to authoritative mech identity, attachment and pose. Verify slot capacity and retirement on mission transition and shutdown.

1. Run the renderer-specific state and staging checks and build the native executable. Compare repeatable C1M1 Off, On, and wrong-key runs with the same build, content, camera and seed. Confirm spotlight submission in traces and a visible effect in the capture.
2. Add real stock and Atlas mount evidence in small slices. Exercise donor and LOD changes, damaged or removed mounts, player switch and AI behavior. Check pose tracking across motion, then reset and shutdown. Treat the synthetic fixture as a diagnostic control.
3. Keep the sun and fixture shadow work in WP06A. Start it from the reviewed light producer and lifecycle baseline. Validate worker synchronization and run with Vulkan validation enabled.

## Remaining milestones

| Gate | Work packages and exit evidence |
| --- | --- |
| G2 — lighting | WP05 real headlights and WP06A sun and fixture shadows. Compare stock Off against modern On, verify per-view 16×16 tile lists, sealed-map sky and fog, mount tracking, and zero Vulkan validation errors during shadow stress. |
| G3 — geometry, content and settings | WP07A light bakes, WP07B skinning and morphs, WP07C material ordering and cutouts, WP06B dynamic/cutout shadows, WP07D effects and weather, WP07E fine visibility and indirect draws. WP08A stock roster, WP08B additional chassis including Atlas, and WP08C runtime and launcher settings. Verify supported families against CPU reference across main view, HUD zoom, MFD and MechLab, including ultrawide. Require the 18-stock and Atlas roster matrix and settings precedence. |
| G4 — material and AA extensions | WP10 parallax occlusion, WP11 tessellation and displacement, WP12 subsurface scattering, WP13 SMAA. Require CPU/GPU reference comparisons, shared-edge continuity, correct material ordering, and effect-Off equivalence. |
| G5 — temporal rendering | WP14 world scale with output-resolution HUD, WP15A depth/motion/reactivity/exposure, WP15B history lifecycle, WP16 FidelityFX upscaling, WP17 optional frame generation. Verify temporal reset and disocclusion, moving and deforming geometry, HUD clarity, and simulation invariance. |
| G6 — performance, platforms and delivery | WP09 dual-GPU performance qualification after geometry and temporal inputs, WP19 Linux x64, WP20 macOS arm64, WP21 Android arm64, WP22A packaging and rollback, WP22B final qualification. Record repeatable performance comparisons, native platform results, signed update/install/rollback receipts and clean-PC validation. |

## Evidence and pickup rules

- Start from current `develop` in an isolated worktree and follow the [GitHub workflow](github-workflow.md). Claim one issue and one bounded package slice. Coordinate with the current writer on shared renderer, mission and pack code.
- For native renderer checks, use `runtime/mw3-re` as the CMake source directory with an out-of-tree build. Run scoped CTests with `--no-tests=error`. Use locally supplied game media for live checks and run one game capture at a time on a shared GPU.
- Record exact source SHA, mode, mission, seed, camera/frame, pack and GPU configuration, test counts, trace results and capture comparison. Report CPU fixtures, synthetic probes and live behavior separately. For mission settings compare both maps and verify transition reset. For release validation check menu/HUD fonts, borderless mode, pack selection, lighting, admission and rollback.
- Update this page when a package merges or its verified scope changes. Link the PR and public-safe evidence. Keep game files, generated code, private packs and raw private artifacts local.
