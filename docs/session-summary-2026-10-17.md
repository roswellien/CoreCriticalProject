
# Development session summary — 2026-10-17

The public website entry is [the October 17 MechLab update](mechlab/2026-10-17.md).
The website publishes dated files from `docs/mechlab/`, not this technical record.
Earlier sections below preserve their session-specific evidence and limits.
Acceptance remains **131/144**; no native milestone credit was added.

## Big Lake model expansion and performance repair

The isolated Big Lake host has 15 chassis / 30 original LOD bindings, directional
sunlight, normal mapping and a single camera-centered shadow map. The incoming
handoff's cascaded-shadow description was incorrect; its specific sky-shader
root-cause account was not corroborated by the inspected source. Full live
chassis/damage/LOD coverage remains open, as does an unmatched original signature
with torso 76, right hand 34 and left hand 30 vertices. Do not assign that
signature to a chassis without identity evidence.

Model expansion had removed existing model-path and candidate-name caches.
Restoring them removes repeated environment searches and roster scans from live
native scene traversal while preserving models, lighting and original producers.
The isolated Play build was rebuilt and its local profile identity updated to
SHA256 `709fcac6625d6646356b32566259fdc69679b36ad348f894eb780e27619fcb08`.

The controlled 3440×1440 route improved from **23.18 ms / 43.1 FPS** to
**12.18 ms / 82.1 FPS**, approximately 47% less frame time. All 1,000 original
frame/draw/hash triples and non-timing world counters matched; captures matched
outside changing FPS text. A separate profiled comparison reduced UCRT sample
share from 48.91% to 3.83%. These are fixed-clock route-throughput results, not
universal live-combat predictions. Frame-budget termination adds no normal-quit
or mission-completion credit.

`apply_perf_env_cache.py --models-only` validates all anchors before writing,
reproduces the verified repair, is idempotent and rejects changed anchors. The
repair changes host bookkeeping at the existing live render boundary; it removes
no original game work. See the [full performance investigation](big-lake-model-performance-investigation-2026-10-17.md).

## Bounded terrain CPU-removal experiment

GPU terrain retention was partially implemented, but original CPU producers
still run. Native inspection corrected earlier labels: original VA `0x545720`
is general material lighting, `0x51FB30` composes matrices, and relevant vertex
and perspective loops are inside `0x53F2E0`. Tile/cell dispatch and required
LOD/light/callback effects cannot be replaced by an unconditional draw.

The new development installer and optional terrain CPU scopes reuse the existing
observed projection contract and restrict admission to resident `ter`/`bwg`
meshes. The prototype removes perspective prefixes while preserving the final
original iteration and supported State/FP/scratch contracts. It preserves other
transform, lighting, fog, clipping and submission work. No interpreter,
original-binary execution or AFTER-state seeding was introduced.

- The original-loop fixture passed 1,152 cases and exercised 119,808 watched writes.
- Fully observed 1,200-frame comparisons admitted 51,868 polygons, omitted 128,116
  iterations and observed 128,116 permitted depth-copy reads without unknown-read
  or pending-token failures. Rendering-semantic records and three capture files
  matched. These records deliberately exclude omitted CPU scratch bytes; raw-TL
  equality for bypasses is not claimed.
- Timing pairs averaged 19.040 ms with the experimental bypass disabled and
  19.187 ms enabled. Restoring the production geometry object in the same host
  averaged 12.258 ms. Experimental producer/hook integration adds about 6.78 ms;
  the prototype has no measured speedup and was not promoted.
- Diagnostic observation defaults on. Explicitly unobserved timing runs provide
  no safety credit; a failed partial-observer timing attempt remains recorded.
  Earlier October 15 divergences are also retained.

This advances a bounded development CPU-removal boundary, not the playable
terrain migration. Big Lake Play retains the cache-fixed production build.
The next step is source-bound ownership of remaining terrain TL producers and
material queues, admission before costly work, and a production-equivalent
disabled control. See [the terrain investigation](terrain-cpu-removal-2026-10-17.md)
for identities, comparisons, failure details and limitations. Assets, generated
code, binaries and raw evidence remain local.

## Bushwacker alternate skin and shoulders

[Detailed record](bushwacker-freya-and-shoulders-2026-10-17.md): recovered Campaign1 Mission3 Commander Freya skin D, added missing original Bushwacker distance binding and per-instance alternate albedo selection; current player primary retained. Corrected shared arms up/in relative to donor torso, both skins/both distances, no new parts or vertex/normal/UV edits. Main launcher now selects f21c0c7e host with all15 chassis/30bindings, photo controls/heap fix retained,39banks unchanged. Native copied-Mission3 1800presentations verifies player primary and enemy D GPU draws. Training116/116, originalGPU1150/1150 and IA116/116 identical; adapter10,370,925checks pass;59stand/walksamples checked. Original saves/registry protected. Extended combat/effect alignment, live close-D/LOD transition and distance performance remain.131/144strictpaused; no commit.

Subsequent R2 review corrected R1's dangling existing shoulder connectors and
floating weapon mounts. Split the two donor clavicle groups out of the torso
batch, restored their original shape/torso seats, moved arms 0.22 units outward
from R1 and undid the old five whole-weapon muzzle-fitting translations. Both
player and Freya / both original LOD bindings use current 34-batch payloads.
No added geometry, texture edits, gameplay firepoint edits or host relink.
Adapter10,371,197checks/zero failures;59stand/walk mesh-contact samples and
both-side exact-payload Blender previews pass. Main living launcher updated;
fresh live R2 test deferred because another native game was running and the
singleton correctly refused launch. R1 live results remain historical, not R2
visual proof. [R2 previews](https://drive.google.com/drive/folders/1j3xrgW6env0kGbiiZZk387ZQDxTAJ8hX).
