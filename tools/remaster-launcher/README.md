# Local Remaster launcher

Current profile, validated 2026-10-14: **native 3440x1440 ultrawide, FXAA, 16x AF**.
Launch `D:/Projects/MW34Recomp/Play MW3Remaster.cmd`. It selects the completed
`local/remaster/gpu-native-r5/build/entry_commandline.exe` (SHA256 `a45e07298fa753c2c9f1f11a3df573f9ac65fba5fa6e1b54e1969635de498557`),
not the newest file by timestamp. `--check` verifies the published build and
registrations without launching. No build or package installation occurs at launch.


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
banks and Bushwacker/Mad Cat/Vulture/Thor; Avatar is excluded. Registered texture
source updates are prepared atomically on launch. New model entries require a
compatible, tested native adapter/build before publication. Mad Cat/Vulture/Thor
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
