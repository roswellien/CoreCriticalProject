# Rendering development pause and handoff — 2026-10-16

Development is paused at the user's request because weekly usage is nearly
exhausted. This handoff records current state; it does not authorize background
development, builds or recurring work. No commit was requested or made.

## Where we are

MW3 remains a faithful native recompilation with Vulkan platform services, not
a remake. The original simulation and geometry producers still execute. Modern
rendering can now proceed without waiting for the experimental CPU projection
removal to pass. Formal acceptance remains **131/144**.

Three separate playable profiles exist:

| Launcher | Current purpose |
| --- | --- |
| Play MW3 Remaster | Current playtesting build, optional turret timing repair and platform investigation traces |
| Play MW3 - Alpha GPU Tests | Stable retained GPU world/model geometry experiment; original CPU projection retained |
| Play MW3 - Big Lake Sun Tests | New isolated Big Lake instance with directional sunlight and constant ambient fill |

The sun experiment has not changed either existing launcher, the user's original
pilot/registry, or the campaign Mission 2 save. All three use 1200 drawing distance
and 1100 fog distance in their current profiles. The sun test is 3440×1440, FXAA,
AF16, with the frozen development textures/models.

### Big Lake sun prototype

The new world-fixed per-pixel directional sun illuminates terrain/hills, admitted
world meshes and GPU replacement mechs. Sun azimuth, elevation, intensity and
constant ambient fill are configurable. Default is azimuth 225°, elevation 35°,
strength 0.85 and ambient 0.30. Sky and HUD retain their existing rendering.

This is direct sunlight plus ambient fill. **It does not sample normal-map
textures, cast shadows, calculate bounced GI, or add local dynamic lights.**
Existing painted shading remains in base-color textures.

GPU model/world paths provide transformed geometry normals. Other opaque
textured world draws use their original transformed/lit (TL) vertices: shaders
reconstruct visible world positions from reciprocal depth and the authenticated
camera/projection, then derive face normals. This is a limited receiver bridge;
it is not retained geometry for off-camera shadow casting. Blended/alpha-tested
draws are excluded. Opaque water can receive diffuse light, without a water BRDF.
Near-clipped replacement batches retain their original CPU branch. The inherited
replacement-model fog gap remains open.

The original camera Y/Z conversion is accounted for. Capture arithmetic uses
full FXSAVE/FXRSTOR preservation with declared XMM clobbers and restored LastError.
Model push constants remain 128 bytes; lighting uses a separate aligned dynamic
uniform binding. Do not bypass these contracts while adding materials.

### Validation and its limits

- Authored CPU/GPU fixtures pass on RX 9070, including transformed normals,
  camera invariance, capture admission, FP state, ambient/backfaces, TL terrain,
  fog ordering, HUD exclusion and geometry reuse.
- Final sun run preserves all 1000 original frame/draw/hash records and exactly
  reproduces the prior corrected sun captures. Sun-off repeat preserves all 1000
  control records and both control captures byte-for-byte.
- The first final sun-off attempt diverged at original hash frame 487. It remains
  retained as `final-off`; cause is unestablished. Its passing repeat does not
  erase this evidence or prove universal replay determinism.
- At frame 1000, cumulative sun calls: 109,850 retained-world, 326,095 TL
  receiver and 21,877 replacement-model draws. These are not distinct objects.
- Dedicated launcher smoke reached 1000 Big Lake frames. Bounded runs stop at an
  intentional frame-budget failure; this is not normal-quit/mission-completion
  credit. Broader live zoom, damage/LOD, reload and sustained play remain open.
- Vulkan validation layers are unavailable (instance creation -6). No layer
  coverage or performance improvement is claimed for the lighting prototype.

## Performance and unresolved gameplay issues

Post-handoff sun on/off benchmark: **124.85 FPS off /121.50 FPS on (−2.7%)**,
8.010/8.231ms,1% lows37.47/36.75FPS. Four same-executable runs in reversed order
pass scene/geometry-count and within-mode repeat-capture checks. See
[Big Lake sun benchmark](big-lake-sun-benchmark-2026-10-16.md) for method and limits.
This measures current direct sun plus ambient only, not normal maps or shadows.

See [benchmark report](gpu-geometry-benchmark-2026-10-16.md). At 3440×1440 FXAA
AF16 and 1200/1100, Remaster averaged **87.2 FPS**, alpha **88.0 FPS (+0.9%)**,
within run variation. At stock 800, alpha was **−0.9%**. Alpha's 1% lows were worse.
These are matched virtual-clock route throughput measurements, not live-clock
whole-game benchmarks. No reliable net speedup has been established.

Partial CPU projection removal is **not promoted**. A stale timing build had zero
actual bypass admissions, invalidating its apparent performance result. The
rebuilt experiment skips work but fails the matching-scene gate around frame
489. Disabled controls also showed recurring divergence. Keep bypass **0** in
playable/sun profiles; diagnose independently without claiming a bypass speedup.

Campaign 1 Mission 2 Bravo remains a game-breaking user-reported issue: its
launcher appeared and then vanished while approaching, before firing. It remained
selectable with an empty targeting view and could not be hit. Root cause and
resolution are unconfirmed. Alpha long-distance firing was also reported. An
original turret short-frame defect above roughly 153 FPS was isolated and an
optional repair tested, but that does not prove Bravo is fixed. User is remote;
campaign save is still at Mission 2 and authorized for testing with private copies.

Mech Lab layout work still needs user playtesting. Future menus must adapt to
resolution/aspect ratio, and graphics settings must expose implemented options.
Do not claim high-FPS Mech Lab compatibility or layout completion from this
rendering work.

## Recommended next advanced-rendering work

1. **Connect normal maps to the existing sun on one GPU replacement mech.**
   Inspect actual UV/material/normal texture bindings and texture conventions.
   Supply or derive a correct tangent basis, including mirrored UVs, instance
   scale and animation. Decode tangent-space normals in the fragment shader,
   transform to world space, and use them for the existing sun calculation.
   Keep this optional in the isolated Big Lake launcher; begin with a flat-normal
   equivalence check, directional detail checks, camera turns and sun-angle
   comparisons. Preserve glass exceptions and separate original-MW3 tuning.
   The selected MW5 appearance reference is the approved 12x-equivalent preview;
   do not blindly copy a Blender numeric strength into the native shader.
2. **Add a small bounded local-light experiment**, such as one point light with
   known position/radius. Establish attenuation, coordinate consistency and a
   measured light budget before wiring weapon flashes or explosions to gameplay
   events. Compare on/off at identical geometry and capture actual GPU/CPU costs.
3. **Prove one shadow caster/receiver pair**, then grow coverage. Use a retained
   GPU mech and reliable ground receiver; build a real depth shadow pass and
   validate light-space transforms, bias and camera movement. General sunlight
   shadows need actual caster geometry collected before camera clipping/culling;
   visible TL reconstruction alone cannot supply occluded/off-camera casters.
   Only after that proof consider terrain coverage and cascaded sun shadows.
4. **Evaluate bounced GI later.** Constant ambient is not GI. Choose an approach
   after material, geometry and frame-time budgets are known; do not label the
   present sun test global illumination.

Before broad feature expansion, preserve the current sun baseline and do narrow
live checks for zoom, damage/LOD, fog and transitions. Lighting and CPU-removal
investigations should remain independently switchable. Fixes to gameplay blockers
remain a separate priority when user playtesting resumes.

## Files, identities and evidence

- Implementation detail: [Big Lake sun report](big-lake-sun-test-2026-10-16.md).
- Root launcher: `Play MW3 - Big Lake Sun Tests.cmd`.
- Launcher script: `tools/remaster-launcher/play_big_lake_sun.ps1`.
- Installer: `tools/remaster-launcher/apply_sun_lighting.py`.
- Authored helpers/shaders: `tools/remaster-launcher/native-overrides/sun*`.
- Fixtures: `tools/remaster-launcher/test_sun_lighting.cpp` and `.py`.
- Local profile: `local/remaster/big-lake-sun-tests.json`.
- Private host, instance, build and evidence:
  `C:/Users/jcbla/MW34SunTests/big-lake-r1/`.
- Final sun executable: `host/build/entry_commandline.exe` under that C directory;
  SHA256 `e34358483eefe78add184c5765a236d48eda7b449a03ac9bca912539c08895bc`.
- Remaster SHA256:
  `a7454e3e8ff168f037bd6d49001f47bada8bd425202c738710fc462616bf7f5f`.
- Alpha SHA256:
  `067087909f4224a196c6d16602eb3dbacc295edadc7d574ff051c90b7c177824`.
- Sun evidence: `validation.json`, `validation-r5.json`, `published-profile.json`,
  `installer-final.json`, `final-fixture.log`, `runs/`, and build logs.
  Fresh installer matched all 14 changed compiled-host source files.
- Benchmark evidence:
  `C:/Users/jcbla/MW34Benchmarks/geometry-20261016-r1/`.
- Protected original hash baseline:
  `local/campaign2-platform-investigation-r1/protected-bravo-pilot-hashes.json`.

**Remote reviews go on Google Drive.** Upload screenshots and comparisons, then
verify metadata and return Drive links; local-only links are insufficient.
Do not upload original media, executables, translated game source or asset packs.

- [Big Lake screenshots folder](https://drive.google.com/drive/folders/1tN9VCLV95oWMAaaQS3BV5H6_cx8jpoxN)
- [Original / sun225 / sun45 comparison](https://drive.google.com/file/d/1Wi5jU6C827MBxHNd6Kru6NkdCe2X5dDL/view)

## Operational constraints

Read the repository AGENTS instructions and current strategy before choosing
implementation. Preserve the dirty working tree and other graphics/asset writers.
Do not commit without user instruction. Original media/generated translations stay
local. No production interpreter/original-code fallback or fake API success.

At pause, no game/build is running. Python PIDs **6536 and 5196** have blank
command lines; protect them and re-inspect process identities before expensive
work. Never open active SQLite or duplicate long jobs. D has only about 3.7 GB
free; use C for substantial copied game instances/builds. Benchmark data was
preserved on C, not deleted. Do not launch full rebuilds just to read this handoff.

## Copy/paste prompt for the next agent

```text
Continue MW34Recomp in D:\Projects\MW34Recomp from the rendering handoff.
First read AGENTS.md instructions, CONTRIBUTING.md, docs/legal.md,
docs/faithful-modernization-plan.md, docs/roadmap.md,
docs/rendering-handoff-2026-10-16.md and
docs/big-lake-sun-test-2026-10-16.md. Read the required work-review/continuation
documents named by AGENTS if present; report missing files rather than inventing
their contents. Preserve all existing uncommitted work and other asset writers.

Current milestone: isolated Big Lake directional sun plus constant ambient works
on native Vulkan world/model geometry and a limited visible-TL terrain bridge.
It does not use normal-map textures or implement shadows/bounced GI/local lights.
The main Remaster and alpha launchers are unchanged; CPU projection bypass stays0.
Acceptance is131/144. Final test executable SHA and all paths are in the handoff.

On explicit resumption, the recommended next feature is optional normal mapping
on one GPU replacement mech using the existing sun. Inspect actual material/UV/
normal bindings and tangent conventions first. Prove flat-normal equivalence,
then directional detail, correct camera/instance transforms and sun-angle changes.
Keep glass handling and original-MW3 material tuning separate. Preserve the sun
baseline and all failed comparisons; a passing repeat does not erase divergence.
Do not pursue CPU-removal promotion or claim a performance gain from earlier runs.

Use private Big Lake instances under C:\Users\jcbla\MW34SunTests, not the original
campaign files. Inspect running processes and disk space first; protect the
composer/watcher, blank-command Python processes, active SQLite and long jobs.
Run only narrow meaningful checks and measure costs before expanding lights or
shadow coverage. Full terrain shadows require real caster collection before
camera culling; visible TL derivatives cannot provide it.

Upload review screenshots/comparisons to the existing Google Drive project
previews folder and provide verified Drive links. Do not upload original game
files or generated translations. Do not commit or switch public launcher defaults
without instruction. Bravo disappearance and Mech Lab playtesting remain open.

Development was paused for usage limits. Do not start implementation merely
because this handoff was loaded; follow the user's resumption instruction.
```
