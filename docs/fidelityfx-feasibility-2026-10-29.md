# FidelityFX stage 1 feasibility results

Recorded October 29, 2026 for [issue #97](https://github.com/roswellien/MW3Recomp-Private/issues/97).
This completes the bounded P0 feasibility investigation in the
[implementation plan PR](https://github.com/roswellien/MW3Recomp-Private/pull/96).
It establishes SDK context compatibility and a native offscreen baseline; FSR
image dispatch and live presentation integration remain future work.

## SDK and device results

The [standalone probe](../tools/fidelityfx-probe/README.md) compiles with the host's
LLVM 21.1.8 and Vulkan-Headers 1.4.321, with warnings treated as errors. The
[dependency manifest](../tools/fidelityfx-probe/dependencies.json) records the full
SDK source commit `7539ae8b6568ad29ed78a753404351daf3b5cca7`, distribution URL,
archive SHA-256, four consumed SDK headers, two DLLs, license and Vulkan headers.
No third-party SDK payload is committed or added to runtime packaging.

Both Vulkan loader/upscaler DLL signatures validated as Advanced Micro Devices.
Imports were inspected with LLVM: loader/upscaler use the Windows/UCRT/MSVC runtime;
the upscaler also imports `vulkan-1.dll` and `VERSION.dll`. No SDK import library
is used. Shader decompression and effect internals remain inside the signed DLLs.
The tagged [SDK API documentation](https://github.com/GPUOpen-LibrariesAndSDKs/FidelityFX-SDK/blob/v2.4.0/Kits/FidelityFX/docs/getting-started/ffx-api.md)
defines the loader/effect split and provider queries.

| Device | Windows driver | Providers successfully created/destroyed | Context memory at 720p to 1080p |
| --- | --- | --- | --- |
| Radeon RX 9070, vendor/device 1002:7550 | 32.0.31035.1003 | 4.1.2, 3.1.6, 2.3.4 | 80,150,144 / 77,989,120 / 117,638,912 bytes respectively |
| Radeon integrated graphics, 1002:13c0 | 32.0.21045.1000 | 3.1.6, 2.3.4 | 74,068,736 / 111,460,864 bytes respectively |

These are context memory queries, not total host VRAM, frame-generation costs or
performance measurements. FSR 4 was not offered on the integrated device. Each
context was explicitly pinned to an ID returned by enumeration; the created
provider name was queried back. FSR 4 returned required-resource bits 15 and
optional bits 0; FSR 3/2 returned 15 and 48. In the pinned header, 15 denotes
color/depth/motion/exposure and 48 denotes reactive/composition masks. Contexts use
auto exposure; exposure requirements must be interpreted with the context flags.

Both devices accepted a Vulkan 1.3 instance/device, compute queue family 0 and the
probe's broad supported-core-feature profile without device extensions. Float16,
int8, subgroup control and synchronization2 were supported. Sampled RGBA16F,
RG16F, R32F and D32F were available. This proves an initial compatible profile;
it does not prove the minimum required features or future dispatch validity.
Keep this profile out of production until narrowed and exercised with real work.

Negative controls: a nonexistent SDK directory and GPU index 999 each returned
exit 1 with explicit errors. The build checks pinned input hashes and signatures;
a deliberately modified SDK header was rejected before compilation, then restored.
No silent provider success or simulated context is used.

## Native baseline

A fresh isolated Training run reused the existing native input runner, copied
pilot/configuration and registry, and read-only original asset junctions. The
runner and raw logs remain in the task's ignored `local/fsr-p0/` directory.
The existing clean-build host was used without changes:

- Source receipt commit: `f1181f94e3b933e2ba15ff8b587e55ee5cbfe094`.
- Host SHA-256: `01b17fa52ba1f939d271a412c50c5353b2e1fcd885367549e25897dff67cb714`.
- Translated DLL SHA-256: `6d6e3c25fef68727113a6d52859253883dbb554958ddaa5a091187667aa8bfa5`.
- Original executable SHA-256: `95bc2c114c9b2e5c5ada8e40ca78cc79470f862e45313ffad0d1e8e6d4d916bf`.
- Investigation source baseline: `647f018a72792c06b2da8c74da04aeb550144c21`.
  Relative to the measured host, canonical graphics files are unchanged; the host
  difference is in `mfc_stage.hpp`. This is a named older host baseline, not a
  claim that current develop was rebuilt or released.

Configuration: 1920x1080 world/output, FXAA, AF16, draw/fog distances 1200/1100,
dynamic sun lighting and normal maps enabled, shadows/replay disabled, existing
replacement models and environment/texture packs. The isolated run receipt holds
the complete environment and asset paths. This is an enhanced-content baseline,
not a stock-content comparison or a statement of all-pack compatibility.

The diagnostic simulation step was 16.666667 ms; timings use the host wall clock.
The hidden-window run reached 2,200 frames and 7,717 3D scenes, then stopped with
the expected frame-budget diagnostic (exit 1). It made **zero swapchain presents**.
Wall duration was 38.15 seconds. For frames 1200 through 2200, excluding startup
and loading, 1,001 consecutive frame intervals measured:

| Metric | Milliseconds |
| --- | --- |
| Mean | 6.879 |
| Median | 6.609 |
| p95 | 7.521 |
| p99 | 9.835 |

Percentiles select the sorted element at floor(p * (n - 1)). This single run
measures instrumented offscreen native throughput, not displayed FPS, pure GPU
time, real-time input latency or an FSR improvement. Existing frame/world/model
logging remained enabled. No screenshot or whole-game acceptance is implied.
The earlier visible clean-host receipt stopped at surface capabilities -13;
this offscreen result does not resolve that presentation defect.

## Source-backed temporal coverage

All paths below are beneath `tools/m4-crt-heap-carry/host/` in the investigation
baseline. This table records inspected producers and missing inputs, not completed
temporal integration.

| Producer or boundary | Existing evidence | Missing criterion and next change |
| --- | --- | --- |
| Real-frame completion | `vdd.inc` Flip validates the chain, swaps guest memories and calls `present`; host frame count advances there | Use a completed real-frame ID, not EndScene count. Audit non-Flip presentation and auxiliary views before enabling temporal history |
| Guest surface accesses | `gpu_sync`, `gpu_protect`, Lock/Unlock, Blt and texture Load synchronize resident targets | Separate presentation output from authoritative guest images; maintain exact read/write and depth conversion behavior |
| World-to-HUD ordering | `vk_scene.hpp` applies FXAA on HUD entry; `finish_world` runs at direct presentation; `gpu_hud.inc` may flush or fall back | FSR must run once per completed view. Record composition segments when world/HUD/guest writes interleave; first HUD alone is insufficient |
| View identity | `effect_scene` supplies frame, campaign generation, context and eye position | Early return when effects are disabled makes this unsuitable as the universal temporal source. Extract minimal view metadata independently of lighting |
| Retained static scenery | `world_geometry_stage.inc`, `world_direct_stage.inc`, ModelInstance transforms | Add prior camera history and lifetime/view generation; recover unsupported scenery classes separately |
| Original opaque TL geometry | `sun_capture_tl` carries camera/world projection and reciprocal-depth data for eligible draws | Capture is sun-gated and skips blended/point draws. No previous object pose; camera reprojection cannot cover moving stock mechs |
| Replacement rigid parts | `mesh_override_stage.inc` creates ModelInstance from batch-to-camera transform | Retain stable per-instance/per-part identity and previous pose across frames; do not key history on draw order or geometry alone |
| Deformed and near-clipped meshes | Donor bone poses and CPU clipping in `mesh_override_stage.inc` | Preserve previous deformation and interpolate previous positions for newly clipped vertices; handle LOD/damage topology changes |
| Sky and zoom | `sun_capture_sky`, sky_view and widescreen role/camera handling | Independent view history, sky motion convention and zoom reset rules; current sky capture is also lighting-gated |
| Transparent effects | Blend state, effect draws and material roles are retained | Define particle/water/animated-texture motion and mask treatment; existing light emission is not a temporal mask |
| HUD/deferred panels | `gpu_hud.inc`, `hud_deferred_stage.inc` retain role and guest order | Composite at output resolution without rerunning guest callbacks or changing rand/FP/guest writes |

## Decision and next implementation boundary

Proceed to independent world/output targets (P1), keeping FSR disabled. The SDK
and toolchain are viable on both tested devices. Full temporal integration remains
gated on lighting-independent view metadata, moving-object history and interleaved
composition. Preserve guest resolution, D32-to-guest depth conversion and current
presentation behavior while adding separate host-owned output images.

Before an FSR dispatch can ship, validate a narrower feature set, storage usages,
barriers, history resets, actual color/exposure conventions and moving geometry
on the canonical host. The known visible presentation limitation needs a bounded
retest/fix before any displayed-FPS claim. These are explicit next-stage criteria,
not reasons to invent temporal data or claim a live FSR result.
