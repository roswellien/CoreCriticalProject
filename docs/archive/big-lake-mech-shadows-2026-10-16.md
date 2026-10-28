# Big Lake mech sun shadows — 2026-10-16

Requested by the user on 2026-10-16: the directional sun on the isolated Big Lake test map now
casts shadows from the GPU replacement mechs. This is a renderer extension; the original simulation,
geometry producers, clipping and draw records are unchanged. Formal acceptance remains **131/144**.

## What it does

- One orthographic sun depth map (4096², D32) covers ±200 world units around the active camera,
  pushed half a range ahead horizontally. Its centre snaps to whole shadow texels so shadows do not
  shimmer as the camera moves. Texel size is about 0.1 world units; the Mad Cat is about 14 units tall.
- **Casters:** every visible GPU replacement-model draw (mech parts), drawn once with its exact
  local-to-world transform. Two-sided, with slope-scaled depth bias.
- **Receivers:** everything the sun already lights: the terrain/hills (reconstructed TL world
  positions), admitted world meshes and the mechs themselves (self-shadowing). Receivers offset along
  the geometric normal, subtract a small depth bias and take nine bilinear depth comparisons (a 4×4
  texel PCF footprint). Shadows attenuate only direct sunlight; ambient fill is retained. The region
  edge fades back to full light.
- MW3 submits terrain and mechs in separate BeginScene/EndScene batches (about four receiver-only
  batches per frame). A batch without casters samples the latest map with that map's exact sun
  transform; the map is at most one frame old. The world log reports `sun_shadow_scenes`,
  `sun_shadow_casters` and `sun_shadow_reused`.

Not included: buildings/terrain as casters, near-clipped replacement batches that still take the
original CPU branch, the player's own mech in cockpit view (it is not drawn), cascades beyond
±200 units, local or weapon lights, normal-mapped shadow detail and bounced light.

## Use

Ambient fill default lowered from 0.30 to **0.20** on 2026-10-16 at the user's request
(`-Ambient 0.30` restores the previous look). Comparisons at 0.30/0.20/0.12 are in
`local/remaster/mech-shadow-previews/ambient-comparison-{400,900}.png`.

`Play MW3 - Big Lake Sun Tests.cmd` now enables shadows by default (profile `"shadows": true`).

```powershell
& '.\Play MW3 - Big Lake Sun Tests.cmd' -NoShadows
& '.\Play MW3 - Big Lake Sun Tests.cmd' -ShadowRange 300 -ShadowDarkness 0.8
& '.\Play MW3 - Big Lake Sun Tests.cmd' -Azimuth 140 -Elevation 12   # long low-sun shadows
```

Runtime variables: `MW34_SUN_SHADOWS`, `MW34_SUN_SHADOW_RANGE` (16–2000), `MW34_SUN_SHADOW_SIZE`
(power of two, 512–8192), `MW34_SUN_SHADOW_BIAS`, `MW34_SUN_SHADOW_DARKNESS` (0–1), and the developer
aids `MW34_SUN_SHADOW_DEBUG` (R occlusion, G inside region, B sun-space depth bands) and
`MW34_SUN_SHADOW_AUDIT=<scene>` (logs every caster's world bounds). Shadows require `MW34_SUN=1`.

## Sources

- `tools/remaster-launcher/apply_sun_shadows.py`: anchored host edits (applied after
  `apply_sun_lighting.py` and the Mad Cat normal-map host edits).
- `native-overrides/sun_lighting.hpp`: settings, 240-byte per-draw uniform (adds true local-to-world
  rows, sun-clip rows and shadow parameters), sun view and caster maths.
- `native-overrides/sun_shadow.vert` (new) and the extended `sun_{model,world,tl}.vert` /
  `sun_scene.frag`; compiled headers via `compile_sun_shaders.py` (glslangValidator reproduces the
  previous SPIR-V exactly).
- `play_big_lake_sun.ps1`: `-NoShadows`, `-ShadowRange`, `-ShadowDarkness`.

Build: `C:/Users/jcbla/MW34SunTests/big-lake-r1/shadow-r1/host/build/entry_commandline.exe`, SHA256
`933f87e3eb918d45821ef90c36e7c9430452cfb5b89a61738938677c79d43511`. The previous sun/normal-map build
and profile are preserved (`shadow-r1/big-lake-sun-tests.pre-shadow.json`).

## Validation

Scripted private Big Lake route, 1000 frames, 3440×1440, FXAA, AF16, draw 1200/fog 1100, sun 225°/35°
unless stated. Evidence is under `C:/Users/jcbla/MW34SunTests/big-lake-r1/runs/shadow-r*` and
`shadow-r1/`.

- **Shadows off is unchanged.** With shadows off, the new build's frame-600/900 captures and the full
  1000-frame draw log are byte-identical to the pre-shadow build (`shadow-r1-off`,
  `shadow-r3-off-repeat`). One off run (`shadow-r3-off`) diverged at original frame 487, the same
  frame as the unexplained sun-off divergence already recorded in the rendering handoff; it is retained
  and its repeat passed. Shadows-on runs match the base draw records for all 1000 frames.
- **Geometry contract.** Replacement-model and TL receiver projections agree (scale 340.564/665.107,
  centre 512/384); the caster audit puts all 32 Mad Cat parts at the expected place ahead of the
  chase camera (feet y≈2.2, top y≈13.2).
- **Ground shadows.** The chase camera keeps the ground within about 20 units of the feet below the
  frame, so at the default 35° sun the ground shadow is mostly off-screen. With a low sun behind-right
  (140°/12°) a clean, soft Mad Cat silhouette (both missile pods visible) falls on the terrain
  ahead-left, with no terrain acne. The debug view confirms terrain inside the region and occluded
  where expected.
- **Cost.** Two alternating off/on pairs, frames 400–985: 9.739 ms off vs 9.786 ms on
  (+0.05 ms, about −0.5% FPS), smaller than the spread between the two off runs. Virtual-clock route
  throughput only; not a live whole-game benchmark.
- **Launcher.** A bounded launcher run (700 frames) starts the shadow build, prints the
  `Sun shadows:` line and records 378 shadow scenes.
- Vulkan validation layers remain unavailable; no layer coverage is claimed.

## Open

Live, sustained play; enemy mechs at mid-distance (the scripted route only shows the player's mech
close up); zoom view; damage/LOD changes; mission reload. Building casters need retained world
geometry before culling. Review screenshots are local in `local/remaster/mech-shadow-previews/` and
have not been uploaded to Google Drive.

## Sun/ambient colour and per-map presets (2026-10-16)

User request: adjustable sun and ambient colour, per-map lighting, and a sunrise/sunset motif on Big Lake.

- New runtime settings `MW34_SUN_COLOR` and `MW34_SUN_AMBIENT_COLOR` ("r,g,b", 0–4 each). Defaults
  are the previous warm-white sun (1, 0.96, 0.86) and neutral ambient; with them unset, frames
  400/600/900 are byte-identical to the previous shadow build (`runs/color-default` vs `shadow-r2-on`).
- `tools/remaster-launcher/sun-presets.json` holds named presets per map (keyed by the launcher
  profile's `map`). The Big Lake launcher applies the map's default preset; `-Preset midday|sunset|sunrise`
  picks another; `-Azimuth/-Elevation/-Strength/-Ambient/-SunColor/-AmbientColor` override single values.
- Big Lake now defaults to **sunset**: sun 225°, 9° high, strength 1.6, colour (1, 0.56, 0.28);
  ambient 0.32 tinted (0.78, 0.74, 1.0). **Sunrise**: 45°, 11°, 1.4, (1, 0.73, 0.50); ambient 0.32 ×
  (0.80, 0.86, 1.08). **Midday** keeps the earlier look with ambient 0.20.
- Rebuilt test build SHA256 `3adf24d0e43e29ee13b6008d2cc97f9e5c943cfa1fbe88cac6619cfb5415e6f8`;
  launcher run confirmed the sunset preset values reach the game. Comparisons:
  `local/remaster/mech-shadow-previews/big-lake-presets-{400,900}.png`.

Map presets are chosen per launcher profile; switching automatically from the map loaded in-game is
not implemented yet.

## Sky and haze: manual and automatic (2026-10-16)

User request: the sky and haze get two modes, manual tint/colour, and automatic from the sun and
ambient lighting when no manual values are set.

- MW3 draws the sky as an opaque, textured original TL dome at the far depth limit (z ≤ 0.00025,
  2048×4096 cloud texture, about 28 draws per frame) with vertex fog. Below it are untextured far
  backdrop polygons (the horizon band). Distance haze is the Direct3D fog colour (0.82 grey on Big
  Lake). `tools/remaster-launcher/apply_sun_atmosphere.py` (after `apply_sun_shadows.py`) recolours
  these on the host before upload: fog colour for every non-HUD fogged draw, the dome's diffuse colour
  (or a texture-factor modulate), and the band's colour. No extra GPU pass.
- **Manual:** `MW34_SKY_TINT` (multiplier on the dome) and `MW34_HAZE_COLOR` (absolute fog/band
  colour), from preset keys `sky_tint`/`haze_color` or `-SkyTint`/`-HazeColor`. Each one is
  independent; whichever is not given stays automatic.
- **Auto:** low-sun weight w = clamp((30° − elevation)/25°, 0, 1). Haze = original fog × a
  luminance-normalised mix of ambient tint and sun colour (sun share 0.30 + 0.55w), dimmed by 0.1w.
  Dome = mix of the same colours (sun share 0.15 + 0.30w), dimmed by 0.3w. The dome stays cooler and
  darker while the fogged horizon glows. With neutral colours it is an exact identity, so midday frames
  400/600/900 are byte-identical to the previous build (`runs/sky-default` vs `color-default`).
  `-OriginalSky` (`MW34_SKY_AUTO=0`) keeps the original sky/haze with coloured sunlight.
- Sunset auto: dome tint (0.65, 0.51, 0.55), haze scale (1.28, 0.84, 0.65), giving a mauve sky and an
  orange horizon. Sunrise auto: dome (0.68, 0.64, 0.69), haze (1.07, 0.89, 0.82). All 19,247 dome draws
  were tinted (0 unsupported); 3,319 horizon-band draws recoloured.
- Build SHA256 `53e8b6791d2020f6042f4c896d3375b012b811504f854efbe6414bd00df3d1ed`; launcher run
  verified the default sunset preset with auto sky. Comparison:
  `local/remaster/mech-shadow-previews/sky-haze-{400,900}.png`.


## Sky gradient, glow and smooth horizon (2026-10-17)

User request: smooth the dome-to-horizon edge, make brightness and glow adjustable, and at
sunrise/sunset make the sky brightest and most saturated on the sun side, fading to darker and less
saturated on the far side.

- Sky dome (mode 2), horizon band (mode 3) and unlit fogged world draws (mode 4, original colours with
  directional haze) now go through the sun fragment shader. Each such draw captures its own camera at
  command time, so the widescreen stage adapts it with that draw's own vertices. The view ray is
  computed per pixel from the exact screen position, because the dome's far-plane z and rhw disagree.
- Per pixel: side = azimuth match to the sun (1 sun side, 0 opposite). Dome = original texture × sky
  tint × brightness × mix(far-side brightness, 1, side^1.5), desaturated toward the far side, plus glow
  = glow colour × strength × (exp(−angle to sun × focus) + 0.35·side³·exp(−4·height)). Haze = fog ×
  mix(far-side haze, 1, side) + 0.6 × glow; it is also used for every lit surface's distance fog, so
  terrain fades into the same coloured horizon. Dome fades into the haze between view heights 0.03 and
  0.28; the band is pure haze. Sky/haze output is dithered because the scene target is RGB565; without
  dithering, the smooth azimuth gradient banded into visible curved contours.
- Auto (w = low-sun weight): brightness 1 − 0.2w, glow 0.55w in the normalised sun colour, focus 2.5,
  far-side brightness 1 − 0.5w, saturation 1 − 0.6w, haze 1 − 0.35w. Manual: `MW34_SKY_BRIGHTNESS`,
  `MW34_SKY_GLOW`, `MW34_SKY_GLOW_COLOR`, `MW34_SKY_GLOW_FOCUS`, `MW34_SKY_GRADIENT` (far-side
  brightness), `MW34_SKY_ANTI_SATURATION`, `MW34_SKY_ANTI_HAZE`, `MW34_SKY_HORIZON`(`_LOW`).
  Launcher: `-SkyBrightness -SkyGlow -SkyGlowColor -SkyGlowFocus -SkyGradient -SkyAntiSaturation
  -HazeGradient -HorizonBlend`; preset keys `sky_brightness`, `sky_glow`, `sky_glow_color`,
  `sky_glow_focus`, `sky_gradient`, `sky_anti_saturation`, `haze_gradient`, `horizon_blend`.
- Debug: `MW34_SKY_DEBUG=1` colours draw kinds (dome/band/haze-only/lit); `=2` shows view height, sun
  side and dome blend.
- Validation: neutral settings remain byte-identical at frames 400/600/900 (`runs/grad-default` vs
  `color-default`). All 19,247 dome and 3,319 band draws carried their own camera (22,566); 35,775
  unlit fogged draws took directional haze. A launcher run with `-SkyGlow 0.9 -SkyBrightness 1.05`
  passed the values through. Build SHA256
  `e4a8f831100947c1c6875857579bb23235f041a039626a7116d18367a23e2355`. Comparison:
  `local/remaster/mech-shadow-previews/sky-gradient-final-{600,900}.png`.

Known limits: a faint line can remain where the dome begins; the glow is a sky effect, not a visible
sun disc; transparent effects keep their own colours apart from fog; no live-play review yet.

## Screen-edge world polygons and vsync (2026-10-17)

- Polygons crossing the screen sides were clipped by the original CPU code, failed GPU-world
  admission and were drawn on the TL fallback, lit with reconstructed face normals instead of mesh
  normals, so building shading changed at the screen edges while turning (visible in Path Debug as
  blue→green). `tools/remaster-launcher/apply_world_edge_admit.py` (`MW34_WORLD_EDGE_ADMIT=1`, sun
  builds only) admits a clipped polygon when all submitted vertices lie on the original polygon's
  plane and all original corners are between the near and far limits. Its submission is rebuilt from
  the original corners (UVs from geometry, vertex fog fitted linearly in depth) and the viewport
  clips it. Near-plane cuts keep the fallback. Route result: 1,551 → 0 unmatched polygons, 0 rejects;
  the edge-cut buildings now shade like the rest of the building.
- Ground normal maps now also bind to GPU-kept world terrain (`apply_ground_normals_multi.py`); this
  changed only distant horizon pixels on the route.
- `MW34_VSYNC=0` presents with IMMEDIATE (else MAILBOX); the Big Lake launcher now defaults to vsync
  off and edge admission on (`-Vsync`, `-OriginalEdges` restore the previous behaviour).
- Diagnostics: `-PathDebug` (`MW34_SKY_DEBUG=3`), `-TextureMarkers`, `-DrawDistance 800`, and their
  double-click launchers in the repository root.
- Caution: an original turret short-frame defect was recorded above roughly 153 FPS; this build does
  not include the optional turret repair, so uncapped frame rates may affect turret aiming.

## Menu scroll timing and normal-map tangent cut-off (2026-10-17)

- Front-end scrolling background: original 0x40A210 (scrolling image widget update, thiscall) adds the
  widget's integer velocity (+0xBC/+0xC0) to its source rectangle (+0xE8..+0xF4) once per presented
  frame when +0x138 is set, then wraps and splits the rectangle. Found by heap snapshots at two clock
  rates (rectangle +1/frame regardless of clock), the owning object's vtable 0x5BC1B0 and decompilation.
  `tools/remaster-launcher/apply_menu_scroll_time.py` (`MW34_MENU_SCROLL_HZ=60`) multiplies the velocity
  by the whole 60 Hz steps of real time since that widget's previous update (remainder carried) for one
  original call, then restores it. Measured: original ~143 px/s at ~144 FPS; timed ~57-60 px/s. Menus
  are not frame-capped (`-MenuFps` remains optional, default off).
- Normal maps: the fragment shader skipped normal mapping when the screen-space tangent magnitude was
  below an absolute 1e-10. Close to the camera that magnitude is tiny but valid, so near surfaces fell
  back to the flat normal (seen on close-up Mad Cat panels; most likely the near-ground "stark line").
  The cut-off is now 1e-30 (the tangents are normalised afterwards). Route captures: ground unchanged,
  close-up mech panels gain their normal detail; live confirmation of the ground band is pending.
- Front-end text ticker: original 0x42FB30 (vtable 0x5BD988, slot 9) moves the text left by
  ftol(float speed at +0xBC) pixels per frame and wraps it. The same `MW34_MENU_SCROLL_HZ` hook now
  replaces the speed for one call with the pixels due for elapsed real time (sub-pixel remainder
  carried) and restores it. Measured: original ~290 px/s at ~144 FPS; timed ~120 px/s (2 px × 60/s).

## High-resolution menu background (2026-10-17)

- Asset: original 1280×960 `common_background` (rimage.zbd) upscaled with Real-ESRGAN x4plus (Video2X),
  Lanczos to 5760×4320 (4.5×, full detail at a 2880×2160 4K menu fit), 45% of the original fine grain
  re-added, and the panel lettering, which the model garbled, redrawn as "H154" (the original reads
  H154; earlier upscale showed "HDR") at the measured glyph positions and colour. Local only:
  `C:/Users/jcbla/MW34SunTests/big-lake-r1/menu-hd-r1/` (`build_hd.py`, `common_background-hd.mwhd`).
- The game keeps its original 1280×960 image (bank `rimage-menu-hd-base.zbd` = AI bank with the original
  background restored) so scrolling and framing are unchanged.
- Renderer: `tools/remaster-launcher/apply_menu_hd.py` (`MW34_MENU_HD_BG`). For frames without a 3D
  scene, the 640×480 game frame is composited at the window's 4:3 fit (max 2880×2160): pixels that are
  the background (exact or uniformly tinted by translucent panels) use the HD image at the scrolling
  widget's offset (verified against the frame, 0-4 steps back) times a smoothed per-pixel tint; additive
  green glows are kept as added light; all other UI pixels use the game's pixel. Presented as 32-bit
  colour. Falls back to the original presentation if anything does not match.
- Cost: menu frames ~6.9 → ~21 ms (CPU compositor, 8 threads); mission frames unaffected.

## High-resolution menu UI from the game's draw list (2026-10-17)

- Every element of a menu frame is drawn by the original image blit 0x55B3C0 (background 1280×960 with
  scroll rectangle, 82×82 glow orbs, masked 1-px bars, text images, 1436×228 logo, cursor save-under);
  text images are DrawTextA recipes captured by the GPU HUD hooks 0x577BA0/0x577BD0.
- `tools/remaster-launcher/apply_menu_dl.py`: each blit is recorded with a snapshot of its pixels while
  the game draws as before. At presentation the list is replayed at 640×480 and compared with the game's
  frame (route: 1.0000 match; < 0.97 falls back), then replayed at the window's 4:3 fit (max 2880×2160):
  background from the HD image, text re-rendered with the recorded fonts at output scale, sprites from
  hi-res packs by identity key (`MW34_HIRES_MENU`), other images bilinear with premultiplied alpha.
- Sprites: 26 static menu sprites (orbs, logo, panels, icons, briefing/loading art) exported by
  `MW34_MENU_SPRITE_DUMP`, atlas-upscaled 4× with Real-ESRGAN x4plus, alpha Lanczos (nearest for
  colour-key images). Pack: `C:/Users/jcbla/MW34SunTests/big-lake-r1/menu-sprites-hd/pack` (local only).
  Cursor save-under patches (21×21) change every frame and are not packed.

## Normal maps on all replacement mechs at 12x (2026-10-17)

- `tools/remaster-launcher/apply_mech_normals.py`: the Mad Cat-only normals loader is now generic. Each
  replacement model reads the BWNRM1 sidecar named by its texture variable with `_TEXTURES` replaced by
  `_NORMALS` (`MW34_BUSHWACKER_NORMALS`, `MW34_ORION_LOD1_NORMALS`, ...). The variable missing means no normal map
  for that model, as before.
- Mech and ground strength are separate: `MW34_SUN_NORMAL_STRENGTH` (replacement mechs) and
  `MW34_SUN_GROUND_NORMAL_STRENGTH` (terrain/world meshes, default 1.0 = previous ground look).
  `play_big_lake_sun.ps1` now defaults to `-NormalStrength 10.2` (project 12x = 12 × MW5 default 0.85)
  and `-GroundNormalStrength 1.0`.
- `tools/asset-inventory/build_mech_normals.py` builds a sidecar from a texture sidecar plus donor
  `Body/Variant/Weapons` OpenGL normal PNGs used unchanged (Window and MissileHead flat). Rebuilding the Mad
  Cat sidecar this way matches the existing one exactly.
- Sidecars built (local, `C:/Users/jcbla/MW34SunTests/big-lake-r1/assets/*-normals.bin`): bushwacker,
  daishi(+lod1), orion(+lod1), shadowcat(+lod1), thor, vulture; madcat existing. Listed in the Big Lake
  profile.
- Checks: the enemy Bushwacker shows panel relief in captures with normals on vs off; the player Mad Cat at
  10.2 vs 1.0 shows clearly stronger plate/vent relief with no shading breakup; the launcher smoke test
  (650 frames) logs `normals_loaded` for madcat and bushwacker and stops at the frame budget.
- Not yet checked live; the higher strength adds visible grain on some flat plates (missile-pod tops),
  which is the donor map's detail and can be reduced with `-NormalStrength`.

## Big Lake switched to the current mech models (2026-10-17)

- The Big Lake profile had been using the frozen `gpu-projection-watch-r1` model set, which includes the
  pre-waist-fix Bushwacker (`live-pose-r1`, BWMESH1, 32 batches): the torso was visibly separated from the
  hips in game. Mad Cat, Vulture, Thor and Daishi were also older than the main registry.
- Every model slot the Big Lake host supports now uses the current registry payload (`local/remaster/models.json`)
  and the main launcher's prepared texture sidecars, copied to
  `C:/Users/jcbla/MW34SunTests/big-lake-r1/assets/models-r2/` (local only). This covers the close
  Bushwacker (R2 attachments, 34 batches, which includes the waist and shoulder/weapon fixes) and the close
  and LOD1 Mad Cat, Vulture, Thor, Orion, Daishi and Shadow Cat. The previous profile is saved as
  `models-r2/profile-before.json`. All 13 normal sidecars were rebuilt from the new texture sidecars.
- Checks: test case `models-r2` (same route as `mechnrm-12x`): the enemy Bushwacker's torso now sits on
  the pelvis and the arms are in the R2 positions. The launcher smoke test (650 frames) logs
  textures, normals and `enabled` for all 13 slots (Bushwacker 34 batches).
- Not covered by this older host: Bushwacker LOD1 / distance mesh, Freya skin D, and the newer
  BWMESH4 chassis. At distance the Bushwacker still shows the original MW3 model.

## Performance with many mechs, and normal strength 4x (2026-10-17)

- User stress test (about 10 mechs, live): frames rose from ~12 ms to 23–26 ms in heavy combat. The per-frame
  logs showed cost scaling with transformed-lit draws and model draws, i.e. with mech count.
- New launcher options `-ProfileOut <file> [-ProfileFrom N]` run the existing host sampling profiler
  (`MW34_PROFILE`). Replaying the standard route keeps the user's saved Instant Action setup, so it spawns
  the same opponents: a reproducible stress run.
- Profile: ~30% of main-thread samples were in `getenv` (ucrtbase), a linear scan of ~150 variables:
  `override_begin` (every mesh-node draw) looked up 13 model paths and string-compared every roster;
  `Renderer::render` read `MW34_SKY_DEBUG` per draw.
- `tools/remaster-launcher/apply_perf_env_cache.py` reads these once and uses a precomputed roster-name
  set. The performance overlay also reuses its strip buffer instead of allocating one each frame.
  Rendering is unchanged.
- Same 3000-frame stress replay, mission frames: 10.85 ms mean / 12.7 p95 (92 fps) →
  6.91 ms / 8.4 p95 (145 fps). getenv dropped from 5135 to 167 samples.
- Remaining cost: ~22% of samples wait in the driver. The renderer has one command pool and one fence,
  so every 3D scene waits for the GPU to finish the previous one (7–9 scenes per frame). The next
  performance step is to double-buffer the scene resources so CPU and GPU overlap. The third-person
  slowdown the user reported uses the same mesh-node path; this fix applies to it too.
- Mech normal-map strength: launcher default lowered from 10.2 (12x) to 3.4 (4x = 4 × 0.85) at the
  user's request; ground stays at 1.0.

## Renderer CPU/GPU overlap tested; overlay buffer fix kept (2026-10-17)

- Tried double-buffering the 3D scene resources (two command pools/buffers, fences, upload/vertex/
  texture-upload/sun buffers and descriptor pools; `render()` waits only for the scene two submissions
  back, with one global barrier per scene). Stress replay: 7.04 ms vs the 6.91 ms baseline, no gain.
  Reverted; not in the apply chain.
- Why: a temporary timing build measured the whole renderer at ~0.6 ms of a ~7 ms mission frame
  (8 `render()` calls ≈ 0.37 ms, `present_resident` ≈ 0.24 ms, all fence waits ≈ 0.01 ms per frame).
  The `win32u` "driver wait" samples in the earlier profile were GPU memory frees from process-exit
  teardown (`~Renderer → shutdown`, sampled because the profile ran up to the frame-budget exit), not
  per-frame waits. A deeper-stack profile (first host frame for every sample in a system DLL) confirmed
  this.
- The real per-frame host waste on that path was the performance overlay (on by default in the
  launcher): `overlay_gpu` sized its HUD scene's colour and depth vectors to the full 3440×1440 target
  every frame, ~20 MB allocated, zero-filled and freed per frame (~7% of samples), although that scene is
  resident (no upload or readback). `tools/remaster-launcher/apply_overlay_no_host_target.py`
  (after `apply_perf_env_cache.py`) leaves them empty.
- Stress replay (3000 frames, mission frames 1750+): 6.91 ms baseline → 6.57 and 5.87 ms in two runs
  (mean 6.22 ms, about −10%; runs vary by about ±0.5 ms). Captures: test case `models-r2-ovl` (the
  `models-r2` route with the overlay on) matches `runs/models-r2` pixel for pixel at all five dump
  frames except the overlay box (x 0–753, y 0–38), where the overlay text draws correctly.
- The remaining main-thread time is spread over recompiled guest code and its dispatch
  (`enter`/`called`/`returned`/`remaster_body`, guest-memory reads, `ftol`), with no single host hotspot.

## Host call-dispatch fast path (2026-10-17)

- User round analysed (`play-runs/20261017-140944-061`): mission averaged 13.4 ms (75 fps), median 13.1,
  p95 18.4, p99 22.2; 7 frames over 33 ms (one-off world-geometry builds when new objects first appear,
  one 193 ms hitch). The heaviest stretch (~60 fps) had ~2,000–2,400 game-transformed (TL) draws and ~80
  mech parts per frame. Only Mad Cat, Thor, Vulture and Bushwacker were upgraded. Six mech instances kept
  the original models (distance meshes and chassis the Big Lake host does not support).
- Function profile of the stress replay: ~48% in recompiled game code with no single routine above ~4%, and
  ~22% in host dispatch glue (`Stage::enter/called/returned`, `remaster_body*`, `GuestMemory::read`).
  A frame runs ~80,000 guest calls, and each one went through ~50 hook comparisons and lazy-setting calls.
- `tools/remaster-launcher/apply_dispatch_fast.py` (must be the last host edit) collects the hooked
  addresses from the hook code (`remaster_body` through `remaster_body_inner`, `hud_intercept`, `hud_capture`)
  into a bitmap over the game image. Calls to other addresses go straight to their lifted body; addresses
  outside the image always take the chain. It refuses to apply if any hook is selected by anything other than
  an address equality. `Stage::load` takes the inline cached-region pointer first, the same path `Stage::read`
  already uses. The call/return bookkeeping is unchanged.
- Checks: test case `models-r2-disp` is pixel-identical to `runs/models-r2` at all five frames (600–1525) of
  the deterministic replay. Stress replay mission frames: 5.87–6.57 ms → 5.10 / 5.14 ms (≈195 fps).
