# Original-world GPU geometry prototype

2026-10-15. The first bounded original-world geometry bridge is implemented and
tested in a private native host. It advances **original mesh arrays → immutable
host geometry → GPU vertex projection**, retaining original per-frame shading
attributes and all original producers. It does not add new lighting or remove
the original CPU transformation work. The playable launcher is unchanged.

## Recovered contract

The original executable SHA256 is
`95bc2c114c9b2e5c5ada8e40ca78cc79470f862e45313ffad0d1e8e6d4d916bf`.
Retained Ghidra12.1.4 evidence is in
`local/terrain-distance-investigation-r1/rea-evidence.json`:

| Evidence | Observation |
| --- | --- |
| `ev_23b65affd885c4b5b55e384266515be1f074686c087a6687a6e1da6a960d14ea` | 0x4F6720 iterates admitted cells and dispatches their nodes through0x4F5910. |
| `ev_fb822adcb4b5c90d759b6539a69cf6c02017a4a5b83b0cd71bff6ebcaaeba595` | Type5 nodes dispatch through0x4F4AB0. |
| `ev_ff20586f48328f0dc9221d8c1fc0be445496bed77c61b9e925a93fdbf909ab01` | Bounding/state handling reaches generic mesh producer0x53F2E0. |
| `ev_8097882cda3c0a9add20233864165df65feb933fd58907526b7e279ec4a8df7a` | Mesh positions, corner indices, normals, UVs and runtime material pointers are available before projection. |

At0x53F2E0, node+0x3C points to the mesh. Mesh+0x10/+0x14/+0x18 hold polygon,
position and normal counts; +0x34/+0x38/+0x3C point to those arrays. Polygon
records are36 bytes: flags/count at+0, position indices+8, normal indices+12,
UVs+16, vertex RGB+20 and runtime material pointer+28. Material pointers here
are not serialized asset material indices.

The normal pointer is additionally confirmed in original disassembly at
0x53F99E–0x53F9B4: mesh+0x3C supplies the input to0x5226E0, which rotates
12-byte XYZ normals without translation. Tiny retained evidence is in
`local/terrain-distance-investigation-r1/raw-normal-*-disassembly.txt`.

Cell context alone does not mean terrain: dynamic scene nodes can be assigned
to cells too. The initial name filters `ter`, `wall` and `healthy` identify the
experiment's bounded subset, not a universal terrain/building classifier.
Live inspection confirmed those nodes carry real original mesh arrays and
produce original D3D calls inside the captured mesh scope.

## Implementation

- `apply_world_geometry.py` applies checked edits to a fresh private host
  snapshot already containing the geometry profiler.
- `world_geometry_stage.inc` snapshots bounded static mesh arrays and captures
  the actual local-to-camera matrix. Morphing/light-bearing/billboard meshes,
  mech ancestry and non-world drawing remain on their established path. Opaque
  triangle fans are admitted only when every original TL corner matches a raw
  source position and UV, with compatible reciprocal depth. Clipped or ambiguous
  polygon matches are counted and retain the established TL draw.
- Content-hashed immutable geometry carries local positions, normals and UVs
  into cached GPU buffers. Equal hashes require equal bytes. The prototype
  stops visibly at4096 cached batches rather than reusing unknown/stale data.
- `world_scene.vert` projects raw positions using the original camera contract.
  A second vertex binding retains the original TL diffuse/specular/fog/UV data.
  The original fragment shader, texture state, fog and alpha behavior continue.
  Raw positions, not inverted screen vertices, drive the new projection.
- Pipeline selection, first-vertex offsets and binding restoration distinguish
  original-world, replacement-model and ordinary TL draws. Original simulation,
  animation, damage, lights and culling continue running.

In particular,0x53F2E0 advances animated-light state and handles morphing;
0x4F6720 changes visibility, light-affect and temporary matrix state. Bypassing
either entire producer would omit required effects and is not authorized by
this prototype.

## Bounded validation

Final development executable:
`local/remaster/gpu-native-world-geometry-r2/build/entry_commandline.exe`, SHA256
`034ad67f5127aa4f680df3ac6e09860cb1f6dabb517c6bb138f01777dfb81ebf`.
Base: the stage1 profiling build. The same37,201 translated object entries and
prior Lab, distance and model fixes remain. Exact source pins are retained in
the candidate's `source-snapshot.json`.

On RX9070 at3440×1440, FXAA/AF16,1600-unit scenery, current textures/model
bindings, a1400-frame original Instant Action walk/turn route produced:

- **147,585 GPU world draws**, with source queue and renderer execution counts
  agreeing. **525** content-addressed batches uploaded once, **90,240 bytes**
  beyond the replacement-model control. Cached batches span336 `healthy`,
  118 `ter` and71 `wall` selections. These are batches, not525 whole objects.
- **1400/1400 original draw count/hash records identical**, with identical
  original scene and virtual-clock sequences.
- **7026 unmatched polygon attempts** retaining TL drawing. This is partial
  coverage; no claim that all world geometry migrated.
- Separate original-compatible Training check: **116/116 CPU PPMs identical**.
- With the world option disabled, all five matched captures below are
  byte-identical to the pre-prototype renderer and all1400 original records match.

| Capture | Changed pixels with prototype enabled | Maximum channel difference |
| --- | ---: | ---: |
| Frame600,3440×1440 | 0 | 0 |
| Frame900,3440×1440 | 3 | 4 |
| Frame1100,3440×1440, after readback | 1 | 4 |
| Frame1300,3440×1440 | 7 | 8 |
| Frame1000 logical CPU readback,640×480 | 1 | 8 |

Visual review confirms matching composition and scenery on the sampled views;
the tiny differences are consistent with float versus original CPU projection.
Enabled output is not bit-identical. The route exercises travel and a changing
camera; it does not establish exhaustive terrain, building, damage or LOD support.

An asset-free authored GPU fixture (`test_world_geometry.cpp`) additionally
passes raw projection with deliberately offscreen TL positions, poisoned prefix
attributes to detect wrong offsets, restoration of ordinary TL drawing between
world draws, and reuse of two GPU buffers across two renders. It ran on RX9070.
The authored shader compiles with the existing glslang15.3.0 compiler.
Independent source review found no blocker in the current projection path.

Each live run terminates at its intentional presentation budget (exit1), not
normal quit. Protected save/registry checks pass; no original assets or user
saves were edited. Play launcher bytes remain unchanged. Strict acceptance stays
131/144. Private results: `local/gpu-world-geometry-r1/validation.json`,
`world-comparison.png`, `runs/world-r2-*` and `runs/world-control-walk`.

## Remaining boundary before lighting and performance claims

This bridge deliberately retains CPU projection and original TL attributes.
It decodes source arrays and searches polygon matches during rendering, adding
bring-up work. No performance improvement is claimed. The next step is a direct
polygon/instance binding and retained mesh lifecycle that removes matching and
redundant render-only CPU work after its side effects are proven.

Before per-pixel lighting or normal mapping, resolve coincident corners with
different normals, verify derived face-normal orientation/smoothing, mirrored
transforms and tangent handedness, and bind normal maps by actual material
identity. Current normals are retained data, not validated lighting results.

The process-wide content cache prevents stale-pointer substitution but lacks
mission eviction and eventually hits its bounded capacity. Add explicit lifecycle
release before sustained play or production use. No camera-independent caster
traversal exists yet; the prototype sees admitted original camera draws only.

Reproduction and fixture instructions: [world geometry development test](../tools/remaster-launcher/WORLD_GEOMETRY_TEST.md).
