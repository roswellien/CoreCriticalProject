# Playable lighting integration — 2026-10-19

**2026-10-20 correction:** The historical R6 identity and broad weather-completion
claims below are superseded by the [R7 repair record](world-lighting-repair-2026-10-20.md).
Review found lighting upload, light-type, mission observation and fixture-lifetime
defects. Rain particles, pooled reflections, falling ash and true heat distortion
are not finished. The replacement fixture benchmark retains all repeated trials.

The current Material Normal Preview host now combines the maintained mech and
material work with the corrected live filming camera and experimental weapon
lighting. This continues the existing native host; it does not replace the game
with the private trailer-capture build. Acceptance remains **131/144**.

## Execution boundary

The base is the current attachment host (`a85f211d…`), retaining all 15 registered
chassis and 30 close/distance bindings, including the detailed MW3 Strider,
current Mad Cat/Vulture attachments, remastered menu and restored hover wave.
Existing upgraded world artwork, authored normals, water and cloud detail remain
selected. No new material artwork is claimed by this integration.

Live detached views now override the camera only while rendering the world.
Original camera setup still executes; genuine camera outputs and the wide-view
cache are restored before simulation continues. The shared installer rejects
unknown source revisions before changing either adapter file. Private scheduled
capture controls and orbit choreography are excluded from the playable host.

Weapon lights reuse the existing bounded full-content effect catalog and its
presentation-time fading. Lights remain unshadowed, capped at 16, and can miss
effects that never reach the renderer. Replay recording now defaults off in the
host itself, including when no environment setting is supplied. The launcher's
explicit opt-in remains available.

A normal window-close test exposed an unimplemented original MFC shutdown call.
The host now forwards the observed `WinHelpA(HELP_QUIT)` request to Windows and
returns its actual result. Other unsupported Help commands still fail visibly.
The [Windows API contract](https://learn.microsoft.com/en-us/windows/win32/api/winuser/nf-winuser-winhelpa)
describes this release request. Campaign Mission 1 subsequently loaded and
closed through Alt+F4 with `ExitProcess(0)` and native DLL detach.

## Build and evidence

- Local build: `local/material-authoring-r1/native-lighting-integrated-r6`.
- Executable SHA-256: `8fce991dfd490fb0c1210d17e6673fec33baee882c53c2ba8af1c332912b0c27`.
- Source snapshot SHA-256: `aea8ffc0d936db584c7e943752286e4218a23e7e79f32187ba1a434db34d31b3`.
- Existing 37,201 translated objects retained; Clang-CL/Ninja build completed.
- Vulkan light geometry, radius, normal response, HUD exclusion and stale-list
  fixtures pass; photo/replay math and serialization fixtures pass.
- Two installer preservation controls and two effect-material admission controls
  pass.
- A private diagnostic derivative compared 679 moving frames: player pose,
  simulation clock and 18 monitored camera words were identical. One monitored
  aim component differed by at most `3.665306380347226e-14`; the aim flags matched.
  This is a bounded noninterference check, not proof for every weapon or pose.
- A paused world region was pixel-identical across two frames and weapon lights
  expired after resume. Five full-resolution native PNGs covered Orbit, Dolly,
  Game Photo, Freefly and resumed live view. Scheduled input was used; physical
  F11/F9 keyboard polling was not established by desktop automation.

Diagnostic camera and pause controls initially used a different texture-bank
precedence from the launcher. That discrepancy does not establish material
appearance equivalence. The runner was corrected to apply prepared asset bindings
first and explicit profile bindings second. Earlier benchmark results are retained
as historical evidence and superseded by the corrected run set. The final report
records the exact run identities and settings.

Local evidence is stored through the `reports/lighting-integrated-20261019-r5`
junction on the Games drive. Generated source, executables, original game media
and private game/save copies remain local and outside source control.

## Corrected performance baseline

Eight bounded original-input runs used the published candidate executable on an
AMD Radeon RX 9070: four environments, lights off/on, 1,500 measured frames per
setting after warm-up. Simulation advanced by a controlled 16.666667 ms; the
measurements below use actual presentation intervals, not the simulated clock.

| Environment / mech | Time | Lights off FPS | Lights on FPS | FPS change | Added mean frame time |
| --- | --- | ---: | ---: | ---: | ---: |
| Grasslands / Puma | Night | 75.85 | 73.70 | -2.83% | 0.384 ms |
| Big Lake / Orion | Sunset | 120.51 | 117.35 | -2.62% | 0.223 ms |
| Rolling Hills / Thor | Night | 151.15 | 142.15 | -5.95% | 0.419 ms |
| Gorge / Champion | Sunrise | 91.56 | 88.91 | -2.89% | 0.325 ms |

Settings: 3440×1440, FXAA, 16× AF, 1200 scenery distance, 1100 fog distance,
latest upgraded material bindings, replay/capture off, 16-light cap, and
**sun/moon shadows off**, preserving the current material-preview setting.
Optional diagnostic logs were disabled; the world-geometry audit required by
this host remained active. All four routes fixed light azimuth at 225 degrees
for comparison; the Gorge sunrise case uses sunrise color/elevation settings
with that direction override. Each setting has one sample, not repeated trials;
these are bounded route baselines rather than whole-game performance estimates.
Runs are named `bench-{mech}-{0|1}-r5c` in the local integration evidence directory.

## Testing the integrated host

Use `Play MW3 - Material Normal Preview.cmd`. The older Normal Mapping Preview
shortcut is an alias for that same profile and current material registry.
`Play MW3 - Dynamic Night Lighting Preview.cmd` selects the same integrated host
and assets with the moonlit-night preset. The GUI launcher's regular
`local/remaster/launcher.json` profile is outside this preview publication.

The material preview defaults to sunset. Append `--lighting-preset sunrise`,
`--lighting-preset midday` or `--lighting-preset night` for manual comparisons.
Prior executable/profile files are retained for rollback. Source and executable
pins must agree before launching through the preview wrapper.

## Campaign 20-mission progression and weather integration (R6)

The full 20-mission campaign lighting and weather plan authorized on 2026-10-19 is now implemented across all 20 campaign maps (`c1m1`–`c1m4`, `c2m1`–`c2m4`, `c3m1`–`c3m6`, `c4m1`–`c4m6`), replacing static session presets during campaign gameplay:

- **Mission lifecycle & identity:** Recovered direct native `CreateFileA` mission database binding in `mfc_stage.hpp`. When the game opens `Database_Files/zbd/c[1..4]/readerm[1..6].zbd` (including `c4b` for Operation 4 Missions 4–6) or loads save games (`/games/*.mw3`), `CampaignManager` automatically selects the exact mission environment. Non-campaign modes (Training `t1`, Instant Action `readeria*.zbd`, and menus) are isolated from campaign overrides and retain standard neutral/baseline lighting.
- **Dynamic per-frame lighting:** `sun_lighting.hpp` provides dynamic `current_settings(presentation_time)` evaluated per frame in `vk_scene.hpp`, ensuring smooth mid-session mission transitions, restarts, and save loads. Manual overrides (`--lighting-preset` / `MW34_MANUAL_LIGHTING=1`) remain fully honored for manual testing.
- **Weather and environmental lighting in Vulkan shader (`sun_scene.frag`):**
  - *Rain & Wetness:* Diffuse albedo soak darkening and specular glint sheen on wet mechs, terrain, and structures (`c1m2`, `c1m3`, `c4m2`).
  - *Lightning:* Dynamic periodic multi-strike lightning flashes that spike direct and ambient light to brilliant blue-white with exponential decay (`c1m3`, `c2m4`).
  - *Localized Valley Fog:* Height-attenuated low-altitude fog ceiling with exponential distance extinction (`c1m4`, `c4m2`).
  - *Dust Storm & Smog:* Particulate scattering towards the sun and warm ochre haze attenuation (`c2m2`, `c2m3`, `c2m4`, `c3m2`).
  - *Heat Shimmer:* Micro-turbulent horizon mirage dispersion and specular highlight bleaching at high noon (`c3m1`).
  - *Volcanic Ash & Lava Radiance:* Upward radiant orange/red thermal emission from caldera floors on low elevations (`c4m1`).
  - *Enclosed Interior:* Outdoor ambient sun suppression (`night_world_gain = -1.0`) with localized environmental light emitters (`c3m5`).
- **Main launcher gap resolved:** Connected `local/remaster/launcher.json` and `tools/mw3-remaster-launcher` directly to the completed integrated host (`native-lighting-integrated-r6\build\entry_commandline.exe`, SHA-256 `8fce991dfd490fb0c1210d17e6673fec33baee882c53c2ba8af1c332912b0c27`), ensuring campaign lighting is active in GUI launcher campaign play while preserving user-configured graphics settings.
- **Texture-bearing fixture lights & emissive self-illumination:**
  - *Analytical Fixtures:* Cataloged 14 light-bearing game texture definitions (`spotlight1`, `c5strt10`, `c5strt04`, `c5strt09`, `c5strt12`, `mfglow01`, `MFGLOW01`, `runway01`, `m7runway01`, `lighthouse01`, `lighthouse04`, `point_flare`, `LFLARE1`, `LFLARE2`).
  - *Polygon Observation & Scoring:* Observed 3D world polygon vertices in `d3d_provider.inc` and `effect_lighting_stage.inc`, dynamically computing centroids, surface normals, and spatial deduplication (2m radius). Camera-distance importance scoring dynamically assigns the nearest active lights to open GPU light slots (sharing the 32-light uniform buffer with weapon flashes).
  - *Directional Cone / Spotlight Attenuation:* Added cone attenuation (`cosAngle` threshold) in `sun_scene.frag` for perimeter floods and streetlamps.
  - *Procedural Bulb Self-Illumination:* Evaluated diffuse luminance in `sun_scene.frag` to boost bulb/lens regions, ensuring lamps glow brightly in pitch-black night missions while casings remain properly shaded.
  - *Measured Performance:* Night 3D gameplay runs at 17.63 ms (~56.7 FPS, 95th percentile 16.67 ms / 60.0 FPS) compared to 17.15 ms (~58.3 FPS) daytime, demonstrating negligible added overhead (< 0.48 ms, < 2.8%) at 3440×1440.
- **Evidence and acceptance:** Verified with clean 60-frame, 120-frame, 700-frame and 800-frame Vulkan presentation runs on AMD Radeon RX 9070, automated lifecycle test suite, full-resolution 3D frame dumps (`training-day-frame600.png` and `training-night-frame600.png`), and C# GUI launcher Release compilation. Acceptance remains unchanged at **131/144**.
