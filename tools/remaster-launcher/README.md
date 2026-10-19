# Local Remaster launcher

October 19 surface-lifetime repair: after composing a compatible private host,
`apply_surface_page_pool.py HOST_SOURCE` installs checked reuse of retired
virtual surface pages. It preserves live/locked/queued/resident surfaces and
the original address limits. Build, validate and publish matching source pins
before changing a launcher profile. See the Big Lake surface-lifetime repair
record in `docs/big-lake-surface-lifetime-fix-2026-10-19.md`.

October 18 replay video buffer update: **off by default**. In MW3 Launcher,
open **Photo & Replay** and enable the 60-second Instant Replay Background
Buffer to opt in. Its description states a **30–35% performance impact**, with
cost varying by system and scene. F10 saves a clip when the buffer is enabled.
Old launcher settings migrate to off once; subsequent explicit choices persist.
Regular native and lighting-preview shortcuts also default off. Direct script
users may opt in with `-InstantReplay 1` on `play_native.ps1` or
`play_big_lake_sun.ps1`. Photo mode, screenshots, manual recording and game-state
rewind remain separate controls. [Measurements and limits](../../docs/lighting-performance-2026-10-18.md).

October 15 maintained/well-used batch: Orion, Thor and Vulture now use the new
worn base-color sets, alongside the previously installed Bushwacker and Mad Cat.
The regular root launcher prepares them on each launch, including Orion LOD1.
All four new prepared files match their source material pixels; other model
registrations, geometry, build/profile and six unrelated sidecars are retained.
Normal maps remain separate work. [Art, comparisons and installation checks](../../docs/orion-thor-vulture-worn-textures-2026-10-15.md).

October 15 worn-texture publication: the normal `Play MW3Remaster.cmd` launcher
now registers Bushwacker R7 worn colors and Mad Cat maintained/well-used R1 colors.
All five base-color material paths for each model point to the completed local
sets. The launcher repacks them on every launch; both prepared RGB565 files were
checked against every source pixel after the existing 2048-pixel cap/vertical
conversion. Other registrations, geometry, graphics and the selected build are
unchanged. This enables the painted wear; normal mapping remains planned.
See [installation and checks](../../docs/worn-mech-textures-launcher-install-2026-10-15.md).

Current October15 arm-placement update selects
`local/remaster/gpu-native-daishi-arms-r1/build/entry_commandline.exe`, SHA256
`11ce36987b79a26a675015689f53561e307953633ae9fdb83773f3dcffaa47df`.
It retains the scenery-distance host and current graphics settings. Daishi R3
raises/tucks complete arms with original shoulder shapes; accepted legs/waist
and all other model registrations remain. BWMESH3 adds rigid current-ancestor
frame translation, supported by both GPU/CPU projection. Models declaring
`required_native_mesh_format: 3` require a profile whose `mesh_payload_versions`
includes 3; V1/V2 profiles default to versions 1/2. Incompatible hosts fail
before launch. [Implementation, checks and previews](../../docs/mw5-daishi-arm-placement-2026-10-15.md).

Current profile, validated 2026-10-15: **native 3440x1440 ultrawide, FXAA, 16x AF**.
Launch `D:/Projects/MW34Recomp/Play MW3Remaster.cmd`. It selects the completed
`local/remaster/gpu-native-daishi-arms-r1/build/entry_commandline.exe` (SHA256 `11ce36987b79a26a675015689f53561e307953633ae9fdb83773f3dcffaa47df`),
not the newest file by timestamp. `--check` verifies the published build and
registrations without launching. No build or package installation occurs at launch.

The current model registry includes the October 15 Daishi waist and Shadow Cat
vertical-thigh corrections for both distance levels. Both draw in the unchanged
r17 native build; all 4,700 original draw records match the prior cases. The other
five models and texture PNG registrations are unchanged. See
[the asset correction](../../docs/mw5-fit-corrections-2026-10-15.md).
Daishi's current second revision also corrects pelvis/torso connector ownership
at the hips and shoulders; a further 2,600-frame native check matches all original
draw records. The other six model records are retained in that second update.

r17 retains ported body parts after original arm loss instead of reverting the
whole mech. Exact source stump/remaining-roster checks preserve original damage,
weapon logic and debris. Orionrightarm loss is verified in a6500frame native
battle with all6500original draw records matchingr15. Training116/116,
GPU1150/1150 and IA116/116 pass. Other live damage states, converteddebris and
muzzle correction remain pending. [Details](../../docs/mw5-arm-damage-fix-2026-10-15.md).

r15 adds Orion, Daishi and Shadow Cat runtime candidates to the existing four.
All three render in bounded native IA tests; Training116/116, original
GPUdraw1150/1150 and IA116/116 match r14. Both distance texture bindings refresh
from current registered PNGs at launch. Visible muzzle alignment, controlled
damage/debris, actual new LOD1 selection and material review remain pending.
Normal maps are prepared offline; the native adapter samples base color only.
See [the batch record](../../docs/mw5-next-mechs-2026-10-15.md).

r14 retains r12 zoom alignment, r9 HUD repairs, r8 campaign movie timing and r7
performance changes. It corrects the zoom window's marker-occlusion footprint
and aligns its three target-triangle lines using the original camera choice.
Intended hiding and per-edge clipping remain, as do original zoom FOV/input.
Training116/116, GPU1150/1150 and IA116/116 match r12. A matched1000-frame
3440x1440 cockpit case covers false hiding and zoom-marker alignment;14 sampled
1920x1440 control captures are identical. The Vulkan validation layer was
unavailable; normal-renderer checks pass. Radar semantics and controlled damage
progression remain open; Mech Lab is investigation-only. See
[the October15 findings](../../docs/hud-mechlab-investigation-2026-10-15.md).


Local MW3 music is now enabled on both Remaster variants. The supplied Track 01
and Track 02 FLACs map to original CD slots 2/3; the game chooses tracks, repeats
mission music and controls its volume. Configured sources are verified/prepared
on launch. The current `Play-MW3.cmd` native build supports the same soundtrack.
Intro/Ending FLACs are not playlist tracks; movie audio keeps its AVI path.
See `tools/music/README.md` and `local/music-integration-r1/validation.json`.

The exact r5 build retains Training116/116, GPU1150/1150 and IA116/116, and passes
bounded actual-music checks with all Remaster assets. Detailed HUD coverage below
was performed on the retained r4 renderer; r5 adds its reviewed music host bridge.

The wider camera adds horizontal world visibility while retaining the vertical
view. Original HUD elements keep their proportions and appropriate edge/center
anchors; menus and radar maps remain proportional. The tested features include
radar modes, zoom, targeting, damage, weapon groups, objectives and HUD toggling.
The diagnostic performance overlay defaults off to leave the radar unobscured.
FXAA runs before the HUD; world/model textures use real anisotropic sampling/mips.

Both root launchers reread `local/remaster/launcher.json`, `models.json` and the
cumulative texture registrations each launch. They currently supply 39 texture
banks and Bushwacker/Mad Cat/Vulture/Thor/Orion/Daishi/Shadow Cat; Avatar is excluded. Registered texture
source updates are prepared atomically on launch. New model entries require a
compatible, tested native adapter/build before publication. Mad Cat/Vulture/Thor/Orion/Daishi/Shadow Cat
remain runtime candidates with weapon/damage/LOD validation pending.

`Play MW3Remaster without new models.cmd` uses original geometry with the same
textures, HUD, display and quality settings. To return to 4:3, set the profile's
`graphics.width` to 1920; height stays 1440. Supported values are width 1920/3440,
AA `1` (off) / `"fxaa"`, AF 1/2/4/8/16. Other output sizes are rejected visibly.
Normal/PBR materials remain separate work.

Evidence and fidelity limits: `local/remaster/gpu-native-r4/validation.json`,
`source-snapshot.json` and the current r4 section in `docs/e0-application-execution-path.md`.
Original-compatible Training 116/116, mode 7 GPU 1150/1150 and IA 116/116 pass.
The 2400-frame HUD test has zero GPU fallback and zero Vulkan warnings/errors.
This is bounded Training/IA coverage, not exhaustive whole-game equivalence.
Strict acceptance remains 131/144 and paused. Existing game sessions are preserved.

## Historical launcher and integration notes

The following text records earlier builds and requested profiles. The current
profile above supersedes their resolution, AA and renderer descriptions.

`Play MW3Remaster.cmd` in the project root calls `play_remaster.py` using the
project root as its working directory. `--check` reads the current configuration
and reports readiness without launching, staging media or changing settings.

`Play MW3Remaster without new models.cmd` calls the same living launcher with
`--original-models`. This disables every replacement, including Bushwacker,
Mad Cat, Vulture and Thor, and does not stage their model texture sidecars.
The native host uses original MW3 geometry with the 39 registered texture
banks and the current 1920x1440, AA-off, AF-off profile. It rereads the shared
build/graphics/texture registrations each launch and leaves the normal launcher's
model selection unchanged. Inherited model bindings are cleared by the launcher.

The root launcher checks Python 3.11+ and Pillow imports before choosing an
interpreter. It prefers the existing Codex bundled Python under
`%USERPROFILE%/.cache/codex-runtimes/codex-primary-runtime/dependencies/python`,
then checks `C:/Python314/python.exe`, `python`, and `py`. No package installation
or administrator access is needed when one of these runtimes has Pillow.
Pillow 12.3.0 (HPND license) is the existing image dependency used to decode,
resize and stage the registered PNG textures; the standard library cannot
perform this image preparation. This dependency belongs to the launcher,
not the native game executable.

The current profile is 1920x1440 (4:3 at the height of a 3440x1440 display),
AA off and AF off, requested on 2026-10-14 for performance testing. Internally
`aa=1` means one raster sample per output pixel and `af=1` disables anisotropy.
The same host also supports 8-sample SSAA and 16x AF; the supported-value lists
allow either setting without falsely rejecting the disabled profile.
Local settings are in ignored `local/remaster/launcher.json`.
The original installation is not changed by this launcher.

The launcher rereads the cumulative texture pack's configured-banks manifest
and `local/remaster/models.json` every time. Publish completed runtime models
into this registry with their backend, status and required local files. Keep
Blender/GLB candidates at `offline-preview` until their actual runtime adapters
and validation are complete. Do not select arbitrary newest files by timestamp
or use partially generated assets. Registered models must also be supported by
the configured backend's launcher; registration alone does not integrate a mesh.

Current backend boundary:

- Native (selected): the private host implements a 1920x1440 presentation image,
  eight raster samples per output pixel (4x2 supersampling), hardware 16x AF,
  cumulative bank redirection, and Bushwacker, Mad Cat, Vulture and Thor replacements. Guest-sized
  color/depth are rendered separately and retained for original game execution.
  Original CPU HUD writes are composed onto the enhanced presentation. This is
  SSAA rather than MSAA; it has a larger performance cost. Normal/PBR lighting
  and a high-resolution HUD geometry pass are not included.
- D7VK: the existing isolated original-executable launcher implements this
  resolution, 8x MSAA, 16x AF and the current cumulative texture pack. Native model
  adapters are incompatible with it. Selecting it requires an explicit backend
  choice; it is not an original-code fallback in the native executable.

`--backend native` or `--backend d7vk` overrides the configured backend for one
launch. Game singleton checks preserve existing sessions. No game is killed or
project build started by this script. Normal maps/PBR remain separate native
renderer work. No formal native-game acceptance credit is claimed.

The native profile reloads both manifests and verifies bank hashes (cached only
when size/mtime match). It prepares a checked bank map and model texture sidecars
under `local/remaster/prepared` using atomic file replacement. It never replaces
the original installation's media or edits the D7VK profile. Renderer settings
and model file bindings are passed directly to the registered native executable.
`--prepare-only` verifies/prepares assets; `--frames`/`--dump` permit bounded local
checks. Frame-time logs are recorded in `local/remaster/runs`.

To publish another completed native model: add its entry to the local registry,
including its `id`, required files, environment bindings and optional texture
sources/batch metadata. Update the native profile's executable and `model_ids`
only after its adapter is actually implemented and tested. Unrecognized IDs
are refused rather than silently skipped. Changes to an existing registered
texture source take effect the next time this launcher prepares the sidecar.
On 2026-10-14 the user explicitly requested enabling the latest non-Avatar
assets. The profile selects the compatible multi-model build
`local/work-ahead/mw3-cinematic-mechs-r1/runtime-integration-r1/build-identity-r1/entry_commandline.exe`,
with a pinned executable hash and all four model IDs. Mad Cat, Vulture and Thor
retain `runtime-candidate` status: their matching-chassis native draw and short
walk checks passed, while muzzle effects, damage and lower LOD checks remain
pending. The profile's `include_runtime_candidates` option enables these
candidates without mislabeling them runtime-ready; the launch summary identifies
them. Avatar is absent from the registry and staging. Twenty model base-color
maps and the 39 configured texture banks are prepared from their registered
sources each launch. Alternative skins and normal/PBR maps are not combined
into the primary base-color skin.

Execution boundary advanced: the root launcher now prepares and supplies all
four native model bindings to the tested multi-model host, with the requested
1920x1440, 8-sample SSAA and 16x AF profile. Check mode was exercised from
`C:/Windows/System32` through the root CMD launcher with user-site Python packages
disabled; asset preparation verified all four IDs, twenty maps and 39 banks.
No additional game run or formal acceptance credit is claimed for this
configuration update. The previous local Bushwacker-only manifests are retained
under `local/remaster/previous-bushwacker-profile-20261014`.

## Current optimized native connection (2026-10-14)

This supersedes the asset-test executable described above. The shared profile
selects `local/remaster/optimized-native-r1/build/entry_commandline.exe`, SHA256
`3835852f66e1ee4152d9bd3bf4d316c30b5dfb294adf89f37cade2be77e3b8e4`.
Both root launchers use it. It builds the current optimized host and translated
object list used by `build/m4-crt-heap-carry-O2-lazy`, with the Remaster
presentation, texture-bank and model adapters added. Launch summaries now print
the selected executable. Shared runtime sources and other writers are untouched.

`connect_optimized.py` snapshots the current host into ignored local storage;
`build_optimized.ps1` builds it against the optimized object list. The profile
uses host-built initial state and true native loader-order startup
(`MW34_SEED=host`, `MW34_STARTUP=loader`), without reading original-process BEFORE
state. Lazy target residency is retained for original-resolution execution;
enhanced presentation currently uses exact guest-sized readback for its separate
high-resolution pass, which remains a performance cost.

Two concrete integration defects were fixed: the HAL's hardcoded 256x256
texture maximum now reports the Vulkan device's actual `maxImageDimension2D`,
allowing the updated textures to render correctly; and the complete observed
original cockpit signature is excluded from chassis body identity while its
original draws remain intact. Required chassis names/counts/vertices still match
exactly. Unknown attachments are not silently admitted.

`local/remaster/optimized-native-r1/test-r4-native-texture-limits` produced correct
updated textures and a real 1920x1440 frame with original models.
`test-r6-camera-attachment` completed 900 presented frames, loaded four payloads
and twenty base-color maps, and validated Bushwacker's 21 source meshes and 20
replacement controllers through camera switches. The other chassis retain
experimental status and their earlier matching-chassis checks; weapon/damage/LOD
checks remain pending. Frame-budget stops are intentional, not normal quits.
An additional one-frame run through the actual no-model launch path recorded
the selected executable hash and optimized startup flags. Source/object pins
and validation scope are in `source-snapshot.json`. Formal acceptance remains
131/144. The previous shared manifests are retained under
`local/remaster/before-optimized-native-20261014`.

### Performance correction: optimized-native-r2

The shared launcher now selects `local/remaster/optimized-native-r2/build/entry_commandline.exe`.
The current optimized core object list still matches the native O2-lazy build.
The Remaster adapter's non-integer scaling formerly computed two divisions and
conditional copies for every sample pixel (22,118,400 pixels at 8x SSAA).
It now caches exact inverse coordinate boundaries and fills only changed source
pixel rectangles. Both the original source and enhanced frame captures at
frames 300/400 are byte-identical before/after for AA off and 8x SSAA.

With four replacement payloads and the updated banks enabled, the matching
early Training sample at frames 301-450 improved from 4.38 to 8.58 FPS at
1920x1440 / 8x SSAA / 16x AF, and from 18.96 to 21.83 FPS with AA/AF off.
These are short deterministic wall-time samples, not whole-mission rates.
The source-size native baseline is not the same graphics workload: Remaster
still renders a second target, performs readback/CPU resolve and does not use
lazy residency in enhanced mode. FXAA is not implemented; default AA/AF remain
off. r2's `source-snapshot.json` retains identities and performance scope.

### Alpha GPU playtest launcher (2026-10-15)

Double-click `play mw3 - alpha gpu tests.cmd` at the repository root. It uses
the separate local `launcher-alpha-gpu-tests.json` profile. The optimized alpha
retains fast GPU scenery, the original optimized CPU producer and the Mech Lab
repair. The unfinished CPU projection removal experiment stays in a private
safety-test host; it is not linked into this interactive package.
GPU-world geometry and fast binding are enabled with the current seven models,
39 texture banks, HUD/music,3440×1440 FXAA/AF16 and stock800-unit scenery with
original scene-defined fog. Both normal and alpha profiles use this distance.
Both normal and alpha profiles enable the original-device fog-cache repair
(`MW34_DEVICE_FOG_REBIND=1`), restoring fog after the gameplay display-mode switch.
See [fog investigation](../../docs/fog-rendering-investigation-2026-10-15.md).

`--check` validates the build/assets without launching. Interactive launch has
no frame budget or scripted clock. World counters and geometry CPU timings go
to each session's `local/remaster/runs/` directory; heavy diagnostic payloads
are disabled. The recurring divergence remains under investigation; see
[results](../../docs/gpu-divergence-investigation-2026-10-15.md).

### Bounded campaign-normal authoring continuation

`repack_world_normals.py` losslessly groups identical complete normal-image tuples
across existing world pages; all source keys, image bytes and resolutions remain.
`prepare_campaign_materials.py` refines pinned upgraded campaign sources with
explicit UV features, flat-glass/coverage masks and material-specific shallow grain.
`campaign_material_source.py` validates RGB565 entries and separate alpha planes,
including their ARGB1555/ARGB4444 runtime identities. Outputs require fresh folders;
other bindings and previously retained work are checked byte-for-byte.

A compatible native host accepts either a single `BWSNR2` authored sidecar or an
`MW34SNA1` manifest at `MW34_SURFACE_NORMALS`. The manifest contains plain sibling
page filenames, at most 16 pages and 256 MiB in aggregate. Each page retains the
64-image/256-binding format limits. Duplicate identities fail; authored bindings
retain precedence over lazy world pages. Launcher profiles and matching snapshots
must advertise `authored_normal_catalog_versions: [1]`. World page/resident limits
remain unchanged. See the Campaign 1 report for the selected preview and evidence.
