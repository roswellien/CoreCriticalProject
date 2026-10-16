# Cached world triangles and bounded projection-audit removal

Development work, 2026-10-15. This advances the retained original-mesh -> Vulkan
handoff. It removes CPU work introduced by the experimental bridge; it does
not yet bypass the original game's projection producer. Play remains unchanged.

`apply_world_fast.py` applies to a fresh copy of the direct-r2 host snapshot.
It creates resident reversed-fan triangle lists once per exact source revision,
instead of allocating, triangulating, hashing and comparing them every draw.
The existing full source-byte snapshots continue to detect mutation and address
reuse. Current instance transforms, material state, color and fog remain live.

With the development-only `MW34_WORLD_FAST_BINDING=1`, an ordinary textured
polygon can also omit the bridge's repeated CPU position transformation and
perspective projection audit. Admission requires:

- Original frame, mesh, polygon and material ownership, equal corner count and
  the original reversed UV order.
- Original node clip mask low six bits clear; polygon decomposition flag0x400
  clear; zero depth bias; no secondary layer global0x7489A8.
- Zero original frame local EBP−0x54, excluding special material/lighting paths.

Other draws retain the linear audit and established TL drawing on mismatch.
This option does not remove original CPU clipping, lighting or material callbacks.
Counters record attempted fast/audited corners, including partial rejected draws.
Eager triangle preparation retains some never-drawn polygons; the visible4096
batch capacity can therefore be reached sooner. Mission eviction is still open.

## Timing test

Final development executable:
`local/remaster/gpu-native-world-fast-r2/build/entry_commandline.exe`, SHA256
`a7695089f62cca2150996a902ff9b6408fa1b2285dcd5b66f4000324381c8972`.
Its37,201 translated object entries and shader bytes are unchanged. The earlier
r1 experiment is retained but not used for these final measurements: source
review added the special-path guard before rebuilding and repeating the test.

Four runs in direct/fast/fast/direct order use the same1400-frame Instant Action
walk/turn route, RX9070/Ryzen7 9700X,3440×1440,FXAA/AF16,1600 scenery and current
local model/texture bindings. Measure all presentation intervals800–1400 with
no screenshots/readback in those timing runs. All1400 original draw records and
scene/virtual-clock sequences match across all four runs; protected file, input,
asset and graphics-setting identities match. Performance is not a GPU timestamp
measurement or a comparison against a complete GPU replacement of the engine.

Mean presentation interval is **9.588→9.469ms (1.24% lower)**. Integer QPC scopes
measure bridge binding work at **0.0924→0.0342ms/frame (63.0% lower)**. The latter
is a small part of total frame time; original CPU producers still run. Do not
extrapolate this bounded improvement to the whole game or other scenes.

| Timing case | Mean presentation ms | Binding CPU ms/frame |
| --- | ---: | ---: |
| Direct A | 9.513 | 0.0913 |
| Fast A | 9.436 | 0.0342 |
| Fast B | 9.501 | 0.0341 |
| Direct B | 9.662 | 0.0936 |

The separate final fast capture run executes147,697 GPU world draws, with6914
unmatched attempts retaining TL. It records400,180 attempted fast corners and
118,023 audited corners. Triangle preparation runs822 times for717 distinct
host geometry entries across34 decoded source meshes, instead of rebuilding
for every draw. Host-prepared entries include never-drawn polygons; these counts
are not717 GPU uploads. GPU upload counts match the previous bridge.

All five fast captures (four3440×1440 targets and one logical CPU readback) are
byte-identical to direct-r2. A repeated audited control also matches all five;
the disabled control matches the original renderer's five captures. Original-mode
Training remains116/116 CPU PPMs identical. Asset-free GPU projection, attribute
offset, TL binding restoration, cache reuse and adverse admission fixtures pass.
Timing and capture scene/clock sequences match within their corresponding cases;
capture readback changes scene accounting, so the two classes are not treated
as identical scene sequences. All live runs end at their intentional presentation
budget (exit1), not normal shutdown. Private save/registry protections pass.

### Recurring divergent control

The first audited capture run, `final-audited-walk`, diverges at frame487 in914
records. Its entire1400-record original draw stream equals the earlier retained
disabled failure from direct-r2. The unchanged-executable audited repeat matches
the common reference. This is not a diagnosis or a fix; the failure remains
part of `validation.json`, rather than being replaced by the successful repeat.

An inventory of27 retained runs finds that both divergent routes use camera
data address0x50BD8460 at frame280, while matching routes use0x50BD84A0. Camera
coordinates first differ at frame492. Startup copies host command line and
environment strings into guest allocations, so test paths/environment can affect
layout; no simple path-length threshold or causal link to the gameplay difference
has been proved. Do not attribute this to GPU math, physical input or PRNG state
without further evidence. The inventory and its source hashes are retained in
`local/gpu-world-fast-r1/allocation-variant-inventory.json`.

Follow-up [divergence investigation](gpu-divergence-investigation-2026-10-15.md)
adds thirteen controlled runs and detailed opt-in vertex/allocation capture.
The alternate route was not reproduced; cause and fix remain open.

Private timing records, source pins, fixture logs and validation are retained
under `local/gpu-world-fast-r1/`. The Play profile remains unchanged and strict
acceptance remains131/144. The earlier divergent disabled control described in
the direct-binding report remains unresolved and retained; these tests do not
diagnose it or establish general determinism/production readiness.

## Next original-producer boundary

The original image is U.S.retail1.2 at base0x400000, SHA256
`95bc2c114c9b2e5c5ada8e40ca78cc79470f862e45313ffad0d1e8e6d4d916bf`.
All addresses here are VAs. Retained LLVM disassembly and provenance are in
`local/gpu-world-fast-r1/callback-projection-evidence.txt`.

The simple textured/unlit projection begins at0x541295. Callback cell0x72F3C0
is initialized to0x57CE20, called at0x54139D. That callback packs vertex colors
and specular/fog, copies projected depth into RHW, and either submits a draw
immediately or copies full TL vertices into deferred/batched queues. Those
copies remain consumers even though the callback does not numerically calculate
with screen X/Y. Skipping perspective projection without owning those paths
would leave stale vertex data in draws and CPU readback.

A future bypass must guarantee raw-GPU submission before skipping projection,
preserve callback state effects/order, account for deferred geometry and readback,
and explicitly change affected draw-trace comparisons. The whole mesh producer
still has required lighting, morph and cleanup effects. No wholesale bypass is
authorized by this bounded test.

The next bounded original-loop experiment is described, with exact retained
IR/object provenance and unresolved machine-state/readback/trace contracts, in
`local/gpu-world-fast-r1/projection-bypass-next.txt`. The current dispatch hook
does not intercept an inline loop inside the monolithic translated function;
a source-bound change to that one lifted module is required. No such original
projection bypass has been implemented here.

See [development plan](gpu-geometry-development-plan.md),
[previous direct-binding results](gpu-world-direct-binding-2026-10-15.md) and
[test instructions](../tools/remaster-launcher/WORLD_GEOMETRY_TEST.md).
