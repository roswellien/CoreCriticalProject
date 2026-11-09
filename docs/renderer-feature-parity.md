# Renderer and feature parity

Status as of 2026-11-09 for CoreCriticalProject integration commit `ace166e24b8304ce241e6a84bfd8ed15fe3edb1e`. The target is the native MW3-RE runtime in `runtime/mw3-re/`. Keep original gameplay and stock presentation available while adding opt-in Core Critical enhancements. The legacy runtime is a behavioral comparison point. See the [project roadmap](roadmap.md), [contribution guide](../CONTRIBUTING.md), and [distribution policy](legal.md).

This page tracks package status and milestone gates. Use GitHub issues to claim, scope and track individual work slices.

## Current status

| Package | Integration status and evidence |
| --- | --- |
| WP00A — baseline reconciliation | Merged the fork preview stack and upstream baseline while retaining both histories. [Fork PR #24](https://github.com/roswellien/CoreCritical-MW3-RE/pull/24) |
| WP00B — typed renderer bridge | Merged typed `RendererBridgeConfig` and stage/test hook registration. [Fork PR #25](https://github.com/roswellien/CoreCritical-MW3-RE/pull/25) |
| WP18 — platform abstraction | Merged portable platform and Vulkan WSI boundary. Linux, macOS, and Android qualification remains open in WP19–WP21. [Fork PR #26](https://github.com/roswellien/CoreCritical-MW3-RE/pull/26) |
| WP01 — material contracts | Merged BWNRM, BWSNR, and BWSFM readers and contract tests. [Fork PR #29](https://github.com/roswellien/CoreCritical-MW3-RE/pull/29) |
| WP02A — first authenticated world normal | Merged lazy paging and first bounded terrain `SurfaceKey` proof. Continue preserving rejection of wrong keys and the 512 MiB decoded cache budget. [Fork PR #32](https://github.com/roswellien/CoreCritical-MW3-RE/pull/32) |
| WP02B — world normal scaling | Merged multi-category surface binding and wrong-binding controls. [Fork PR #34](https://github.com/roswellien/CoreCritical-MW3-RE/pull/34) |
| WP03A — mission sun and campaign lighting | Merged native sun/moon mission policy, sealed-map sky behavior, and directional BWSFM response. [Fork PR #38](https://github.com/roswellien/CoreCritical-MW3-RE/pull/38), [sealed-map follow-up](https://github.com/roswellien/CoreCritical-MW3-RE/pull/39), [material response](https://github.com/roswellien/CoreCritical-MW3-RE/pull/40) |
| WP03B — environment packs | Merged verified environment-pack integration and cache/mission lifecycle wiring. [Fork PR #37](https://github.com/roswellien/CoreCritical-MW3-RE/pull/37) |
| WP04A — local-light producers | Merged native and effect local-light producers. [Fork PR #41](https://github.com/roswellien/CoreCritical-MW3-RE/pull/41) |
| WP04B — tiled light lists | Merged per-view GPU compute light lists. [Fork PR #43](https://github.com/roswellien/CoreCritical-MW3-RE/pull/43) |
| Per-map environment follow-ups | Merged pack ambient override, sky tint and brightness, glow, horizon blend, and SDR visibility tuning. The C1M2 SDR comparison reported mean capture brightness of 8.49 before tuning and 12.24 after tuning on a 0–255 scale. Preserve HDR behavior and mission-specific reset. Sky grading is a separate open fork draft. [Ambient](https://github.com/roswellien/CoreCritical-MW3-RE/pull/46), [tint](https://github.com/roswellien/CoreCritical-MW3-RE/pull/53), [glow](https://github.com/roswellien/CoreCritical-MW3-RE/pull/54), [horizon](https://github.com/roswellien/CoreCritical-MW3-RE/pull/55), [SDR](https://github.com/roswellien/CoreCritical-MW3-RE/pull/57), [grading draft](https://github.com/roswellien/CoreCritical-MW3-RE/pull/56) |
| WP05 headlights | In progress. The consolidated port on `develop` includes verified stock catalog integration ([PR #282](https://github.com/roswellien/CoreCriticalProject/pull/282)) covering 18 stock chassis and 93 lamps with SHA-256 member verification. Graceful mount loss, node deletion hook (`node_delete`), and ancestry tracking are implemented on branch `roswellien/feature/280-headlight-limb-retirement`. Atlas and donor bone socket support are next. |
| WP06A — sun and fixture shadows | Planned. No merged implementation recorded in the integration snapshot. Scope includes worker-safe directional sun shadow maps, 9-tap PCF, a six-face cubemap fixture shadow atlas, allocation/retirement, and Vulkan synchronization validation. |
| WP06B — dynamic and cutout shadows | Planned after WP07B deformation and WP07C material/cutout data. Extend shadow casters and receivers for moving/deformed and alpha-cutout geometry. |

[Import PR #277](https://github.com/roswellien/CoreCriticalProject/pull/277) preserved the project and fork histories on `develop`. Runtime promotion to `main`, signed delivery, and validation on a clean non-development PC have separate release gates.

## Next contributor slice

**WP05 — native mech headlights.** Start with the owner of the existing WP05 branch before making a second port. Trace input from the native mission and mech code into the local-light submission path under `runtime/mw3-re/src/frontend/core_critical/`. Keep `L` as the player toggle. Keep mount lookup tied to authoritative mech identity, attachment and pose. Verify slot capacity and retirement on mission transition and shutdown.

1. Run the renderer-specific state and staging checks and build the native executable. Compare repeatable C1M1 Off, On, and wrong-key runs with the same build, content, camera and seed. Confirm spotlight submission in traces and a visible effect in the capture.
2. Add real stock and Atlas mount evidence in small slices. Exercise donor and LOD changes, damaged or removed mounts, player switch and AI behavior. Check pose tracking across motion, then reset and shutdown. Treat the synthetic fixture as a diagnostic control.
3. Keep the sun and fixture shadow work in WP06A. Start it from the reviewed light producer and lifecycle baseline. Validate worker synchronization and run with Vulkan validation enabled.

## Full remaining work package plan

Each row is a distinct package from the master plan. Packages are planned unless their current status is explicitly shown above. Gate completion depends on the full evidence in the source work package and its acceptance criteria.

| Phase and package | Scope and completion evidence |
| --- | --- |
| Phase 2 · WP05 — mech headlights | Complete the active port, real stock and Atlas mount coverage, donor/LOD and damaged-mount behavior, player/AI and switch behavior, pose tracking, retirement, and Off/On/wrong-binding comparisons. |
| Phase 2 · WP06A — sun and fixture shadows | Directional sun shadow maps with 9-tap PCF and six-face cubemap fixture shadow atlas. Verify worker-safe ownership, allocation/retirement, shadow captures, stress behavior, and zero Vulkan validation errors. |
| Phase 2 · WP09 — geometry performance and shared handoff | After WP07A–WP07E and WP15A–WP15B, run ABBA Training benchmarks on RX 9070 and RTX 5070. The planned target is at least 5% mean FPS gain, p95 within 5% of the slower control, and a verified shared `cc::geometry` handoff. |
| Phase 3 · WP07A — geometry light bakes | Move projected-light refinement and static light bakes to GPU. Compare supported families with the CPU reference. |
| Phase 3 · WP07B — deformation and morphs | GPU vertex morphs and mixed-bone prepared skinning from authoritative CPU poses. Verify poses and geometry across supported views. |
| Phase 3 · WP07C — geometry material order | Alpha/cutout, texture cycling, UV scrolling, priority bias, overlays, and second pass. Verify material and draw ordering against CPU reference. |
| Phase 3 · WP06B — dynamic and cutout shadows | Extend shadow casters/receivers for WP07B moving/deformed geometry and WP07C alpha-cutout data. Verify caster/receiver agreement and CPU-reference comparisons. |
| Phase 3 · WP07D — geometry effects and weather | GPU facades, billboards, points, puffers/particles, weather, and flares. Verify each supported family against CPU reference. |
| Phase 3 · WP07E — fine visibility and indirect draws | GPU frustum, near-plane, and backface culling with `vkCmdDrawIndexedIndirect`. Verify all views against the CPU reference. |
| Phase 3 · WP08A — 18-stock roster parity | Full stock roster, skins, damage, detached limbs, and stock mech coexistence. Verify the roster matrix and representative states. |
| Phase 3 · WP08B — additional chassis packs | `additional-chassis-v1`, including Atlas lamps, interior and detached parts, plus prepared UI. Verify pack and asset binding. |
| Phase 3 · WP08C — settings and launcher UI | Native options/CLI and launcher setting precedence with effective-state UI. Verify precedence and displayed effective configuration. |
| Phase 4 · WP10 — parallax occlusion mapping | Authenticated BWSFM1 POM with signed height amplitude and decal ordering. Verify negative, zero and positive amplitudes against an analytic oracle with UV error at or below 1.5e-3. |
| Phase 4 · WP11 — tessellation | Selective tessellation and displacement for terrain/rock patches. Verify bit-identical shared-edge factors and matching shadows. |
| Phase 4 · WP12 — subsurface scattering | Thin transmission and separable bilateral diffusion on RGBA16F. Verify energy conservation and zero armor bleed. |
| Phase 4 · WP13 — SMAA | SMAA 1x before output-resolution HUD. Verify effect-Off is bit-exact with the Phase 3 baseline. |
| Phase 5 · WP14 — world scale | Independent 50–100% world render scale with output-resolution HUD. Verify scaling and exact guest depth readback. |
| Phase 5 · WP15A — temporal producers | Reversed-Z depth, motion vectors for static and moving/deformed/displaced/scrolling geometry, reactive masks, and exposure queries. Verify motion and masks against known scene changes. |
| Phase 5 · WP15B — temporal lifecycle | Flip-only history commits and resets for all 10 lifecycle triggers. Verify no ghosting or disocclusion trails. |
| Phase 5 · WP16 — FSR upscaler | Pinned FidelityFX Vulkan upscaler. Verify supported SDK paths, chained descriptors, and provider queries. |
| Phase 5 · WP17 — frame generation | Optional frame generation with real/presented pacing separation. Verify simulation and RNG advance only on real frames. |
| Phase 6 · WP19 — Linux x64 | Native Vulkan WSI, asset lookup, and lavapipe/GPU qualification. Record native build and execution evidence. |
| Phase 6 · WP20 — macOS arm64 | MoltenVK portability and floating-point behavior. Record native build and execution evidence. |
| Phase 6 · WP21 — Android arm64 | NDK build, `ANativeWindow` lifecycle, tile budgets, and opt-in defaults. Record device/runtime evidence. |
| Phase 6 · WP22A — packaging and delivery | Versioned installer/update producers and transactional rollback. Verify signatures, filenames, install/update, and rollback. |
| Phase 6 · WP22B — final qualification | Cross-feature, dual-GPU, pack rollback, and four-OS release qualification. Collect receipts for all leaf packages and release checks. |

The phase gates are G0 for base/bridge/platform foundations, G1 for material contracts and authenticated world normals, G2 for lighting/headlights/shadows, G3 for GPU geometry/roster/settings, G4 for surface-relief/SSS/AA, G5 for temporal rendering/upscaling/frame generation, and G6 for performance/platforms/release. Preserve the full acceptance thresholds in each work package when planning implementation; this overview is for contributor navigation.

## Evidence and pickup rules

- Start from current `develop` in an isolated worktree and follow the [GitHub workflow](github-workflow.md). Claim one issue and one bounded package slice. Coordinate with the current writer on shared renderer, mission and pack code.
- For native renderer checks, use `runtime/mw3-re` as the CMake source directory with an out-of-tree build. Run scoped CTests with `--no-tests=error`. Use locally supplied game media for live checks and run one game capture at a time on a shared GPU.
- Record exact source SHA, mode, mission, seed, camera/frame, pack and GPU configuration, test counts, trace results and capture comparison. Report CPU fixtures, synthetic probes and live behavior separately. For mission settings compare both maps and verify transition reset. For release validation check menu/HUD fonts, borderless mode, pack selection, lighting, admission and rollback.
- Update this page when a package merges or its verified scope changes. Link the PR and public-safe evidence. Keep game files, generated code, private packs and raw private artifacts local.
