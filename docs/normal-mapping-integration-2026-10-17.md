# Normal mapping: main-host integration candidate

2026-10-17. The current main native host now has a separately built lighting and
normal-mapping candidate. It retains the main host's photo/replay, heap isolation,
turret correction and distance services, and the same 37,201 native object list.
The regular Play profile remains unchanged. The later menu continuation also
updates the isolated Big Lake launcher, as recorded below. This is
readiness for wider integration testing, not a claim that every game material
has a normal map. Acceptance remains **131/144**.

## Changes and execution boundary

The new shared runtime header, `runtime/graphics/material_normals.hpp`, reads
validated material-normal packs. The native renderer consumes them at its live
material/submission boundary. Original simulation, pose, terrain transformation,
material producers, clipping, culling and callbacks still execute. No terrain
projection bypass, interpreter, original-binary execution or AFTER-state seeding
was added.

- **All 30 model bindings:** prepared named normal materials for 15 chassis at
  both original distances. Each pack checks its exact batch count and material
  names against the selected albedo layout. Loading all bindings is distinct
  from live visual verification of every chassis, damage state and distance.
- **Material exclusions:** BWNRM2 explicitly marks unperturbed batches with
  `UINT32_MAX`. Glass is no longer assumed to occupy slot 3. This matters for
  Strider's different material layout and for layouts that omit glass images.
  Legacy BWNRM1 remains readable and identifies its glass exception by name.
- **Strict loading:** reject malformed dimensions/counts, bad indices, wrong
  material order, truncated/trailing data, duplicate names and changed BWNRM2
  pixel hashes. A configured missing pack fails visibly when enabled. Fully
  validate a pack before publishing its batch bindings.
- **Shared images:** reuse identical normal pixels across distances and chassis,
  checking dimensions, full-pixel hash and pixel equality. The current 30 packs
  contain 1,754.8 MiB of logical normal pixels; deduplication retains 47 unique
  replacement images / 701.3 MiB. GPU bindings share those indices as well.
  This is not a measurement of total process memory or total VRAM.
- **Independent option:** `MW34_NORMAL_MAPS=0` keeps geometric lighting without
  normal perturbation and avoids loading replacement normal packs. Missing or
  explicitly unperturbed materials receive zero normal strength. The normal-map
  flag accepts only 0/1; it is separate from the existing normals debug view.
- **Materials across maps:** the optional BWSNR2 surface catalog binds original
  textured geometry through dimensions, 16-bit format and a hash of every colour
  pixel. It does not rely on a map name, handle or the first eight texture bytes.
  Cached matches follow the original surface version, backing address, pitch,
  dimensions and format. Pixel spans that wrap guest addresses are refused.
- **Stock geometry:** registered opaque original geometry can use the validated
  camera/TL lighting bridge outside the terrain-cell path. Frontend/HUD, blended
  and alpha-tested effects remain excluded. The bridge supplies reconstructed
  face normals; it does not recover smooth source normals or hidden casters.

Normal images remain linear OpenGL tangent-space RGBA data. Packing preserves
channel values and resolution, applies the same vertical orientation as albedo,
and performs no colour-space conversion, normal-Y inversion or strength baking.
Normal strength remains independently tunable for replacement and world materials.

## Main-host composition and launcher

`tools/remaster-launcher/integrate_normal_mapping.py` reconciles the reviewed
main, alpha baseline and lighting host trees into a **new** private candidate.
`normal_mapping_source_pins.json` pins the six reviewed adapter inputs in each
tree. Changed input versions or unexpected merge conflicts fail before replacing
any playable tree. The recipe retains main capture methods and photo/turret
wrappers rather than copying an old test host over newer main services.

The final recipe reproduces the compiled candidate's source content with line
endings normalized. The extra unused terrain diagnostic file in the manual
development tree is not a recipe dependency. Main heap, photo/replay, turret and
guest-memory service files retain their source bytes. No experimental geometry
object was rebuilt or substituted.

`native_assets.py` now optionally packs registered `normal_textures`, with
explicit null entries for unperturbed materials. It writes the correct material
order for each distance binding; alternate colour skins share that geometry's
normal detail. A cache keys source-content hashes, batch order and pack format,
and checks the cached sidecar's SHA256 before reuse. Changing a source, batch
layout or cached pack invalidates it. The temporary image-hash cache is cleared
before gameplay so the waiting launcher retains no full source-image cache.

The ordinary launcher supports selecting a completed profile/registry and a
separate prepared-asset folder. Registered normals require a BWNRM2-capable host;
the profile and executable source snapshot must agree on that capability.
Normal source existence is checked alongside required model files. Existing
default profile and asset-output behavior are retained.

Local review entry point:
[Play MW3 - Normal Mapping Preview.cmd](<../Play MW3 - Normal Mapping Preview.cmd>).
It selects the private integration profile/registry and an asset directory on
the test drive. It uses the existing Big Lake private game/pilot and its own
registry-overlay copy. It does not switch regular Play or advance the user's
original campaign save during these automated tests. Interactive preview uses
the ordinary live clock; bounded proofs used scripted input and a 50 ms clock.

Initial normal-map candidate executable SHA256 (retained comparison baseline):
`a20501cd2e9ad21fe8d6e5ae55fb1173767de17c78c19e82ca37d6d3564afcfb`.

The subsequent [original menu rollover repair](menu-rollover-restoration-2026-10-17.md)
is included by the integration recipe. The preview launcher now selects its
current-main candidate under
`C:/Users/jcbla/MW34SunTests/menu-rollover-r1/normal-host/`, SHA256
`e3ebbfa0f72934b80165016ee0c6f3b62eb8ac5ed5708ae12ec9925ee9c71e7e`.
The profile and source snapshot were updated together. Enhanced menu backgrounds,
sprites and their original hover wave are enabled in that preview. Another
1,200-frame Training run and 1,200-frame Instant Action run preserved both complete
extended draw logs and full-resolution captures 600/900 exactly against the initial
candidate; each loaded all 30 normal bindings. The older build and evidence remain
available.

Local profile and source snapshot:
`local/normal-mapping-integration-r1/launcher-normal-mapping.json` and
`local/normal-mapping-integration-r1/source-snapshot.json`.

The current regular profile's older source snapshot has an existing executable
identity mismatch, independently of this candidate. Its AA/window capability
metadata also does not describe every selected graphics value. Those existing
files were preserved. The new preview profile has matching source/executable
identities and uses its separately checked graphics configuration; this is not
a repair or validation of those older launcher metadata entries.

## Verification

Evidence stays local under `local/normal-mapping-integration-r1/` and
`C:/Users/jcbla/MW34SunTests/normal-mapping-integration-r1-assets/`.
Original media, pixels, generated game source and executables remain local.

- The material CTest target passes with warnings treated as errors. It covers
  malformed/truncated packs, explicit exclusions, material-order rejection,
  hashes and legacy glass. It exercises the actual surface-binding stage with
  authored memory: cache hits, same-prefix changed textures, surface-version
  changes, dimensions, pixel format, backing address, pitch and address wrapping.
- Four Python tests pass: named packing/exclusions, full-content surface
  identities/duplicate rejection, preparation cache corruption/source changes,
  and launcher capability/snapshot/missing-source controls.
- The authored Vulkan fixture passes on AMD Radeon RX 9070. Corrected its old
  constant-UV normal test to use a real UV gradient and surface-consistent normal.
  A tilted normal must visibly change lighting; disabled mapping must retain
  geometric lighting. Invalid option values fail. Existing camera, fog, HUD,
  normal-transform and geometry-cache checks also pass.
- **Instant Action, feature off:** current main versus candidate, 1,200 frames
  each. Entire extended draw logs match, and full 3440×1440 capture pixels at
  frames 600 and 900 are identical.
- **Instant Action, lighting on:** normal-off and normal-on runs each retain all
  1,200 original frame/draw/hash triples from the main control. Normal-on loads
  30 model bindings and positively binds the full-content surface catalog with
  the old ground-normal setting absent. Captures change when normal mapping is
  enabled; these are intentional rendering changes, not baseline equality.
- **Training, feature off:** another current-main/candidate pair of 1,200 frames
  matches the entire extended draw logs and both captured frames exactly.
- **Training, enabled:** all 30 model bindings load and all 1,200 original
  frame/draw/hash triples match the Training control. Lighting intentionally
  changes the captured image. No every-chassis live coverage claim follows.
- **Final executable repeat:** another 1,200-frame enabled Big Lake run matches
  all original draw triples and both earlier enabled captures pixel for pixel.
  Final host source files still match their recorded snapshot hashes.
- The preview shortcut's `--check` and the normal launcher's full
  `--prepare-only` succeed. Warm preparation, including existing albedo/music
  work, took 21.88 seconds; the initial normal asset preparation took 69.64
  seconds. These are preparation observations, not rendering benchmarks.

Every bounded game test ends at its intentional 1,200-presentation budget fault,
exit 1. These are not normal-quit, mission-completion or formal acceptance tests.
Protected original pilot/save/registry/source identities remain unchanged.

The exploratory route timings must not be presented as an isolated normal-map
speedup: the old main renderer does not honor the test's vsync-off request while
the candidate does, and the candidate includes restored host configuration
caches. The single on/off lighting pair also has ordinary run variation. A
controlled performance comparison with identical presentation settings remains.

## October 18 continuation

The [stock material integration](stock-material-lighting-integration-2026-10-18.md)
connects approved original Avatar, Owens and Firefly normals, separates geometric
sunlight from normal-map enablement, and retains the remastered menu and original
rollover wave. That record identifies the newer preview candidate and its controls;
the October 17 build identities above remain historical comparison evidence.

## Remaining work before changing main Play

The engine can consume registered normal materials across maps, but the content
catalog is incomplete. The October 17 surface proof contained one recovered ground
texture identity; October 18 extends it with registered stock mech materials and
live checks. Other world textures still need registration and validation. Seven
Strider texture slots lack reviewed normal images and remain unperturbed, as do
its four constant materials. No synthetic replacement maps were invented for them.

The October 17 controls used neutral daylight, original sky treatment and shadows
disabled. The October 18 preview now exposes the shared Big Lake sunrise/sunset/
midday atmosphere presets, with sunset as its preview default. Automatic
map-appropriate light selection,
the approved enhanced-strength target's native calibration, weather/sky behavior,
zoom/near-plane, damage/LOD, reload, weapon effects and sustained campaign play
still need broader validation. Normal mapping has a deliberate option but is not
yet exposed as a completed in-game settings-menu feature.

Terrain CPU-work removal is a separate unfinished optimization. Its earlier
prototype had no net speedup and remains disabled. Normal mapping works through
the existing retained-world and TL bridges without that bypass. Neither this
integration nor its tests add native game-function credit.
