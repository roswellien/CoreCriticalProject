# Direct original-polygon binding

2026-10-15. The development bridge now binds an original polygon directly and
reuses decoded mesh metadata after checking its source bytes. This advances
the original mesh/instance ownership boundary and removes the prototype's
all-polygon screen-coordinate search. Original CPU render producers remain.
No production launcher or gameplay change is published.

## Binding and cache

All original addresses here are VAs for the U.S.retail1.2 image at base0x400000,
SHA256 `95bc2c114c9b2e5c5ada8e40ca78cc79470f862e45313ffad0d1e8e6d4d916bf`.
Original prologue0x53F2E0 pushes EBP and sets it to entryESP−4. Instructions at
0x53F2FD retain the mesh at EBP−0x38. The loop initialization at0x53FBDF–0x53FBF6
stores the current36-byte polygon pointer at EBP−0x34. Relevant source slices
are retained in `local/gpu-world-direct-r1/original-binding-disassembly.txt`.
The existing REA/Ghidra evidence remains the source of the surrounding contract.

`apply_world_direct.py` applies checked source substitutions to a fresh copy of
the world-r2 snapshot. `world_direct_stage.inc` captures that original frame,
checks mesh ownership, reads the polygon pointer, validates its range/alignment,
and indexes the cached polygon table. It reverses source corner order exactly
as the original producer does. Coincident corners retain their actual normal
indices instead of selecting the first projected match.

The linear screen/depth/UV audit remains. Clipped, reordered or otherwise
unsupported draws keep the established TL drawing. Original color, fog and
material callbacks are preserved; the shader and GPU resource format are
unchanged from the previous bridge.

`world_binding.hpp` implements the source-snapshot cache and polygon bounds
helper. The caller freshly reads mesh headers, full positions/normals, polygon
headers, indices, normal indices and UV bytes. Exact byte equality is required
for a cache hit; address identity alone is insufficient. Changes or reused
addresses trigger decoding again. Dynamic colors and material state still
arrive through the original per-draw attributes. Each instance receives a fresh
scope/frame and live camera matrix; cached metadata does not cache its pose.

The metadata cache is bounded to512 meshes/16MiB. The existing GPU geometry
cache remains bounded to4096 batches. Capacity failure is visible. Mission
eviction and a broader geometry lifetime contract are still required before
production or sustained multi-mission use.

## Validation and measurements

Final local executable:
`local/remaster/gpu-native-world-direct-r2/build/entry_commandline.exe`, SHA256
`81d176211470353e9621097f98181ac768e8ce4d45f1d3d1d7a600b550d5308e`.
Base is world-geometry-r2; the37,201 translated object entries and shader bytes
remain unchanged. Candidate `source-snapshot.json` records exact source pins.

On the same1400-frame Instant Action walk/turn route:

- **147,697 GPU world draws**, source queue and renderer execution counts equal,
  using the same525 cached geometry batches.
- **6143 metadata cache hits /34 decodes**. Fresh byte snapshots still run on
  each use; this is not elimination of all CPU geometry traffic.
- **6914 unmatched attempts** retain TL rendering. The direct binding admits112
  draws previously rejected as ambiguous. These counts concern the selected
  `ter`/`wall`/`healthy` subset, not all world geometry.
- All1400 original draw count/hash records match in the enabled capture and
  all four performance runs against their matching controls. Original scene
  counts and virtual-clock sequences match within those comparisons.
- Frames600/900/1100/1300 at3440×1440 and frame1000 logical CPU readback are
  **byte-identical to the previous world-r2 prototype**. Its bounded0–7 pixel
  differences against the original-renderer control therefore remain unchanged.
- Original-compatible Training: **116/116 CPU PPMs identical** to retained r17.
- Asset-free GPU fixture passes projection from raw positions, nonzero attribute
  offsets, restoration of TL binding and cached GPU buffer reuse on RX9070.
- Portable authored cache fixture passes changed-source/reused-address misses,
  replacement budget reclamation, capacity/empty-value rejection, preservation
  after rejection, polygon alignment/bounds and wrapped-address rejection.

Performance uses RX9070/Ryzen7 9700X,3440×1440,FXAA/AF16,1600 scenery and current
local model/texture bindings. Four runs in search/direct/direct/search order
measure all presentation intervals for frames800–1400. No captures occur in
those timing runs; capture comparisons use separate runs.

| Case | Mean presentation ms | Median ms | P95 ms |
| --- | ---: | ---: | ---: |
| Search A | 9.831 | 8.138 | 18.573 |
| Direct A | 9.341 | 7.655 | 18.095 |
| Direct B | 9.388 | 7.675 | 18.167 |
| Search B | 9.825 | 8.110 | 18.748 |

Mean interval is9.828→9.364ms, **4.72% lower** on this route. This compares
prototype implementations with matching visuals, not original engine CPU
projection against a complete GPU replacement. Presentation includes CPU,
driver/GPU, FIFO/desktop pacing and logging; no GPU timestamp claim is made.

### Retained divergent control

The first disabled-feature capture run, `direct-r2-disabled-walk`, diverged from
the original draw stream at frame487 and differs in914 subsequent records.
Build, input/asset/settings hashes and clock sequence match the intended control.
Two unchanged-executable repeats (`...-repeat`, `...-repeat2`) match all1400
original records and all five captures byte-for-byte. The cause remains
unresolved; successful repeats are not a diagnosis or a fix. The divergent run
is retained, is not used in performance statistics, and prevents a blanket
determinism or production-readiness claim.

Every live run reaches its intentional presentation budget (exit1), not normal
quit. Private save/registry checks pass. Play profile bytes remain unchanged;
strict acceptance remains131/144. Evidence and bounded validation are retained
under `local/gpu-world-direct-r1/`, including `validation.json`, `benchmark.ps1`,
fixture logs and the original failed control. Independent source review found no
blocker in frame binding, snapshot coverage, cache accounting or scope restoration.

## Why original projection still runs

Independent source analysis found inline projection loops at0x540975–0x5409C4,
0x541295–0x5412E4,0x541474–0x5414C3 and0x541580–0x5415CF. Their screen/depth
outputs feed later clipping and material/secondary-layer callbacks. Likewise,
the mesh transform fills scratch used by backface culling and original lighting.
Skipping those loops alone would violate observed consumers. Skipping the entire
mesh producer would also lose light/morph/resource effects and cleanup.

The next safe boundary is an enhanced draw producer that explicitly owns those
downstream consumers, with original side effects retained separately. This
direct binding/cache is useful groundwork for per-pixel materials and lights,
but does not authorize a wholesale CPU render-body bypass. Normal/tangent
orientation, material ownership, full coverage and off-camera shadow casters
remain separate requirements.

See [development test instructions](../tools/remaster-launcher/WORLD_GEOMETRY_TEST.md)
and [the development plan](gpu-geometry-development-plan.md).
