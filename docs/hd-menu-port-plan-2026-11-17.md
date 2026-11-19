# Full HD menu port plan

**Owner decision (2026-11-17):** implement the full HD main menu port (Option A)
for round 6. Preserve MW3's original menu logic, timing, animation, and input.
This work changes how the menu frame is presented; it does not replace gameplay
or make a new menu system.

This plan was checked against `HEAD` and `origin/develop` at
`f3166904776b8b64384e5915c6183f7e7118734c`; they matched when this document was
written. Keep the menu's 640x480 (or existing wide-canvas) CPU frame as the
compatibility copy while presentation moves to the GPU in measured steps.
Unknown required drawing operations must fail visibly or use the existing CPU
shadow fallback until their GPU behavior is implemented. Do not add an
interpreter or original-code fallback.

## What the old port did

The previous HD menu work is documented in these repository files:

- [`apply_menu_hd.py`](../tools/remaster-launcher/apply_menu_hd.py) composed a
  high-resolution background on the CPU. It sampled the scrolling background,
  inferred tint and glow from the low-resolution frame, kept opaque menu pixels,
  and fell back to ordinary 16-bit presentation when its assumptions did not
  hold.
- [`apply_menu_dl.py`](../tools/remaster-launcher/apply_menu_dl.py) recorded and
  replayed menu blits in order. It re-rendered recognized text recipes with the
  game's recorded GDI font settings at output scale, used enhanced artwork
  identities where available, and retained the old presentation if replay did
  not sufficiently match the game's frame.
- [`build_ui_packs.py`](../tools/remaster-launcher/build_ui_packs.py) builds the
  menu and HUD packs from local artwork. It validates the `MW3H-v1` sprite and
  `MWHDBG1` background headers and packages them under `ui/sprites/` and
  `ui/background.mwhd`.
- [`UiPack.cs`](../tools/mw3-remaster-launcher/Core/UiPack.cs) validates pack
  manifests, resource hashes, sprite identities, dimensions, formats, and the
  optional menu background before exposing those resources to the launcher.

The owner's plan identifies the menu pack as `com.mw3remaster.menu`, with 26
`MW3H-v1` sprites and `ui/background.mwhd` at 5760x4320. The source confirms the
pack ID construction, resource names, and format readers, but the actual menu
pack and artwork are not in the tracked checkout. Therefore the sprite count
and this asset's dimensions are **unverified here**; the builder accepts up to
256 sprite identities and backgrounds up to 16384 pixels per side. Do not use
those two asset facts as implementation constants until checked against the
local source pack.

## What the runtime does today

The game draws its 2D menu into the native 16-bit CPU buffer. In
[`app_engine.cpp`](../runtime/mw3-re/src/mech3/app_engine.cpp), `video_clear`
clears that buffer and `video_flip` sends a non-3D frame to
`SdlScreen2D::present_16`. The current display path is implemented in
[`sdl_platform.cpp`](../runtime/mw3-re/src/frontend/sdl/sdl_platform.cpp).

The renderer already has a draw observer:
[`zrndr_blit.h`](../runtime/mw3-re/src/gamez/zrender/zrndr_blit.h) defines
`zrndr::DrawObserver` for image blits, pixels, spans, and other framebuffer
writes. [`gpu_hud.cpp`](../runtime/mw3-re/src/frontend/sdl/gpu_hud.cpp) turns
observed images, points, and spans into output-sized GPU geometry. For text it
can call `ztwod::host().hud_text_image`; the SDL host implementation is in
[`sdl_twod_host.cpp`](../runtime/mw3-re/src/frontend/sdl/sdl_twod_host.cpp).
The adapter keeps the CPU buffer as a shadow for native reads.

Today, the observer is started by the 3D overlay lock path
(`lock_back` -> `begin_overlay_16`) and finished by `overlay_16`. Ordinary menu
frames do not use that lock path, so their draws do not reach `GpuHud`. The
observer also deliberately returns to CPU composition when it sees an
unsupported framebuffer write. That protects effects such as ripple, alpha
fills, additive glow, or cursor save-under until they have equivalent GPU
behavior. The current [`prepared_menu_background.cpp`](../runtime/mw3-re/src/platform/prepared_menu_background.cpp)
reconstructs a scrolling background through a cached CPU composition; it is
already covered by a focused headless check.

## Delivery sequence

Each implementation PR should be independently reviewable and keep the current
CPU output available until its new path passes its gate. Avoid
[`camera.cpp`](../runtime/mw3-re/src/gamez/zclass/camera.cpp) and
[`frame_renderer.cpp`](../runtime/mw3-re/src/frontend/core_critical/frame_renderer.cpp)
while other open view-distance, zoom and flare changes touch them (check for merge conflicts before starting a stage). If a stage cannot avoid either file, first
re-scope that stage around the conflicting work.

| PR | Scope and likely files | Headless checks and validation gate | Execution boundary advanced |
| --- | --- | --- | --- |
| 0. This plan | `docs/hd-menu-port-plan-2026-11-17.md` | Review links, claims, and `git diff --check`. No build or game run for documentation. | No runtime boundary; records the round 6 plan. |
| A. Observe menu frames | `runtime/mw3-re/src/mech3/app_engine.cpp`, SDL screen/HUD files, and focused HUD tests. Start `GpuHud` at menu frame start; finish at `video_flip`. If `finish()` returns false, keep `present_16` as the fallback. Add bounded per-screen counts for images, text hits, and shadow reasons. Add a headless test that feeds a recorded menu draw list through the observer. | Extend/run `mw3hud_checks`; retain and run `mw3menu_background_checks` and `mw3prepared_staging_checks`; run the pinned `python tools/check.py` harness (build, CTest, format, style). Require unchanged menu output against the recorded draw-list baseline before accepting this stage. | Menu draw commands reach the same GPU overlay adapter already used for HUD overlays, with no intended visual change. No live menu claim until exercised in the game. |
| B. Cover menu primitives | GPU equivalents for ripple, alpha panel fills, additive glow, and cursor drawing/saving. Keep shadow fallback for anything unsupported. Match the original `blit16` rounding, transparency thresholds, clipping, and color-key behavior; unknown required primitives fail visibly. Likely files are zrender primitive/effect code, `gpu_hud`, and focused renderer/HUD tests. | Add headless comparisons against the CPU `blit16` behavior for edge values, clipping, alpha thresholds, and representative effects; exercise each fallback and unknown-operation failure. Run all three named checks and the pinned harness. | Common menu writes no longer force the entire frame onto CPU presentation; unsupported writes remain safe and visible. |
| C. Present the background as a GPU quad | Replace the CPU compositor only after B covers its writes. Feed the validated background texture as one GPU quad and preserve the scrolling source rectangle and wrap behavior. Keep the CPU background path available until matching checks pass. Wide-canvas behaviour is decided: cover scaling, REPEAT sampling, wrap at the image's own width (1920 source px for the wide master; 1280 original-game px, the full 5760-wide master at 4.5x, for the existing master), and the original scroll speed (see the owner decisions). Likely files include `prepared_menu_background.*`, SDL presentation, and tests. | Headless tests cover scroll offsets, wrap edges, crop rectangles, cover-scaling geometry (cover, no pillarbox), repeat sampling and wrap at the image's own width, background loading failures, and CPU/GPU output correspondence. Run `mw3menu_background_checks`, `mw3prepared_staging_checks`, `mw3hud_checks`, and the pinned harness. | The HD background is sampled by the GPU rather than reconstructed pixel-by-pixel on the CPU. Menu state and input remain owned by the original game logic. |
| D. Route menu text and sprites | Use `hud_text_image` for recognized menu text recipes at output scale. Route registered `MW3H-v1` menu sprites through the menu GPU path. Log missing identities once per identity, with bounded output; retain explicit failures for malformed required resources. Likely files are `gpu_hud`, SDL text host, pack binding/loading, and tests. | Headless tests cover text recipe identity/cache invalidation and scale, sprite identity hits/misses, crops, and pack validation. Run the three named checks and pinned harness. Verify local artwork/pack identity before relying on it; those assets are not checked into this repository. | Registered menu lettering and artwork are presented from their output-resolution sources while original game menu code continues to choose content and positions. |
| E. Layout and documentation | Document and implement the selected ultrawide layout policy, keeping menu hit testing aligned with visible controls. Update relevant user/contributor docs and focused layout/input code only as required. Likely files depend on the policy decision. | Add headless coordinate tests for 4:3 and wide windows, including visible bounds, hit regions, and resize changes. Run the three named checks and pinned harness. Validate text scale and cursor placement against the intended layout. | Menu presentation adapts to the selected wide-canvas policy, with the visible controls and input coordinates agreeing. Live confirmation remains required. |

For every code PR, the maintainer runs the pinned harness using its configured
clang-cl/MSVC toolchain. A code PR is not ready if compilation, CTest, format,
style, or a focused check fails. Do not disable or loosen an existing check to
make a stage pass. `mw3hud_checks` is declared in
[`runtime/mw3-re/CMakeLists.txt`](../runtime/mw3-re/CMakeLists.txt),
`mw3menu_background_checks` is declared there as well, and
`mw3prepared_staging_checks` is declared in
[`runtime/mw3-re/src/frontend/core_critical/CMakeLists.txt`](../runtime/mw3-re/src/frontend/core_critical/CMakeLists.txt).

## Open policy questions

Resolve these before the affected stage depends on an answer. The 4:3 menu
background and menu hit regions must not acquire inconsistent policies.

1. **Wide-canvas controls and hit testing:** keep a centered 4:3 logical menu,
   or reflow controls for wider layouts? In either case, rendered controls and
   pointer/controller hit regions must share the same transform.
2. **Text scale:** should text follow the menu's logical 4:3 layout scale, the
   output's vertical scale, or a separately bounded readable scale? Preserve
   the original GDI font recipe and layout metrics unless a deliberate
   presentation rule is approved.
3. **Cursor behavior:** should the cursor scale with the menu transform or
   retain a physical-pixel size? Keep clipping and hotspot behavior consistent.
4. **Save-under and restoration:** which cursor and menu effects read pixels
   back from the CPU buffer, and what explicit shadow/copy rule preserves them
   when GPU drawing is active? Do not assume the shadow CPU image contains GPU
   output.
5. **Performance budget:** set an acceptable frame-time and memory budget for
   large background textures, text rasters, cached sprites, and compatibility
   copies. Measure on supported hardware before removing the CPU path.

## Owner decisions (2026-11-18)

- **Background scaling:** cover (no pillarbox), GPU sampling repeat/wrap. The previous runtime's
  menu patch fitted the menu to 4:3 and pillarboxed; that is not kept.
- **Wide master strips:** a 640-px AI-generated strip is acceptable for 32:9.
- **Wrap width:** the scroll wraps at the HD image's own width: 1920 source pixels for the wide
  master, and 1280 original-game pixels (the full 5760-wide master at 4.5x) for the existing
  master.
- **Scroll speed (owner decision, 2026-11-19):** a FIXED 60 px/s per axis, in source pixels of the
  original 1280x960 image, from elapsed time and independent of the presented frame rate. This is what
  the original looked like at 60 Hz and what the previous runtime patch did. **Source facts:** the
  original 0x40A210 moves the view 1 px per presented frame with no time basis (about 143 px/s at
  144 fps), the port previously stepped once per 1/30 s (30 px/s), and the "about 60 px/s" figure came
  from `tools/remaster-launcher/apply_menu_scroll_time.py`. `ScrollImage::update` now steps 60 times a
  second (`menu_widgets.cpp`, `main_menu_moves_per_second`). Its steps are texels of the bound
  game texture, which remains 1280 pixels wide. Presentation converts both the horizontal scroll
  origin and the view span by `master.source_width / game_texture.width`: 60 original-game px/s
  becomes 90 master-source px/s on the 1920-wide master. One 1280-pixel game cycle therefore covers
  the entire 1920-pixel master, including the extra 640 columns, and wraps at its own width.
  Scaling the view span by the same ratio preserves on-screen speed; changing only the origin
  would accelerate it. For the existing 1280-source-pixel master (5760 HD texels at 4.5x), the
  ratio is one. Vertical coordinates use the corresponding game texture height. CPU and GPU
  coordinates correspond within 8-bit quantization tolerance, rather than promising exact pixels.
- **Art assets:** the owner's HD art candidates live in a local, untracked folder and are never
  committed.
- **Menu layout (owner decision, 2026-11-19):** the menu keeps its 4:3 layout; the background fills
  the full screen resolution; menu text scales with the 4:3 menu; the cursor scales with the menu.
  These are recorded as named constants in `runtime/mw3-re/src/gamez/zrender/zrndr_blit.h`
  (`kMenuKeepsFourByThreeLayout`, `kMenuBackgroundFillsScreen`, `kMenuTextScalesWithMenu`,
  `kCursorUsesMenuLogicalTransform`).

## Order of work (priorities: no crashes first, then the HD menu at full speed on the GPU)

The stages are A, B, C, D, E as in the delivery sequence above:

1. **This docs PR.**
2. **Stage A: menu frames through the draw observer, no visual change.** It comes first because
   the CPU compositor identifies background pixels per frame by classifying each frame pixel
   against the recorded blits (`prepared_menu_background.cpp`). A GPU quad drawn under the
   original frame needs a keyed layer, that is, knowledge of which frame pixels are background,
   and the observer path gives that per draw (`menu_background_blits()` plus the draw list)
   without per-pixel CPU classification.
3. **Stage B** (menu-only primitives: ripple, alpha fills, additive glow, cursor), then **stage C**
   (the GPU background quad, replacing the CPU compositor once B covers its writes; the CPU path
   stays as the fallback until tests prove the GPU path), **stage D** (text and sprites at output
   scale) and **stage E** (ultrawide layout and documentation).

## Risks and live-only validation

- The observer reports only draws made while it is installed. Starting it at
  menu frame start must cover the actual clear/draw/flip lifecycle without
  capturing unrelated scene or overlay work.
- CPU/GPU differences in RGB565 rounding, alpha thresholds, color keys,
  clipping, blending, and command order can create visible seams or change
  animation. Keep comparison fixtures and the fallback until each class is
  covered.
- Some effects depend on previous framebuffer contents. A CPU shadow buffer is
  not automatically current after GPU composition; save-under and readback
  behavior need explicit treatment.
- A 5760x4320 RGB background is large, but that size is not verified from the
  tracked asset. Texture limits, upload cost, caching, and memory pressure must
  be checked against the actual locally supplied asset and target hardware.
- The texture upload API exposes no mip levels. The GPU menu upload is area-filtered once on
  the CPU to at most twice the initial window height (2160 when no window is supplied), because
  the original 480-high view spans half the 960-high background canvas. This reduces scrolling
  shimmer near the initial display size while retaining the full source for CPU composition.
  Resizing does not regenerate this upload; smaller windows can still minify it and larger ones
  can lose detail. Filtered GPU output and full-source CPU output correspond within 8-bit
  quantization tolerance only where filtering footprints agree; filtering detail can differ.
- Invalid or mismatched background inputs retain native-frame presentation, with one diagnostic.
  Optional GPU image/map allocation failures select CPU composition. Vulkan texture and staging
  allocations are preflighted before draw submission so their failure does not stop the render
  worker. CPU fallback uses the same cleared surround as explicit CPU mode; it does not extrapolate
  a repeating image from only the first recorded blit.
- Classification still compares the full native frame and recorded blits. Scrolling changes both,
  so the whole-frame cache misses on each scrolling frame even when unchanged correction maps
  require no upload. This remains a known CPU cost; UV-only GPU updates do not remove classification.
- Headless tests can check recorded draws, pixel math, asset parsing, geometry,
  and input transforms. Only a live game run can verify the actual animated
  menu, real draw order, transitions, cursor interactions, navigation, quit,
  frame pacing, and visual quality on supported displays.

This is a plan only. **The live game was not run for this plan.** No menu port
behavior or visual improvement is claimed as implemented or validated.
