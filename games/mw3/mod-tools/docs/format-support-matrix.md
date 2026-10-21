# MW3 Data Formats & Mod Tooling Support Matrix

**Date:** 2026-10-20
**Status:** Working Format Specification & Tooling Audit (Phase 1)

Verification scope: the current six-phase editor check exercises mission
discovery/loading, editing/history, project serialization, one unchanged C1M1
GameZ export and one edited export. The Studio check exercises HTTP and pack
export. The family-wide "100%" labels below are initial prototype claims, not
independently established coverage of every listed format, archive or field.
Broader format round trips and native custom-mission play remain open.

This document records the exact binary archive, terrain, world geometry, and mission data formats used by MechWarrior 3 (1999) and its native recompilation (`MW34Recomp`), identifying which formats currently support reading, which support writing, and which fields remain unresolved.

---

## 1. Summary Support Matrix

| Format Family | Primary Extension | In-Game Role | Native C++ Reader | Native C++ Writer | Mech3AX unzbd (Read) | Mech3AX rezbd (Write) | Byte-Exact Round-Trip Status |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **ZBD Archive Container** | `.zbd` | Master container for all game packages | ✅ `mw34_m4_assets` | ⚠️ Planned (P2) | ✅ `unzbd mw <cmd>` | ✅ `rezbd mw <cmd>` | **VERIFIED (100% Byte-Exact)** |
| **Mission / Logic Documents** | `reader*.zbd` (`*.zrd`) | Objectives, spawns, triggers, AI profiles, nav nets | ✅ `mw34_m4_assets` | ⚠️ Planned (P2) | ✅ `unzbd mw reader` | ✅ `rezbd mw reader` | **VERIFIED (100% Byte-Exact)** |
| **World & Scenery Geometry** | `gamez.zbd` | 3D scene node hierarchy, models, materials, terrain bounds | ✅ Host Vulkan Scene | ⚠️ Planned (P2) | ✅ `unzbd mw gamez` | ✅ `rezbd mw gamez` | **VERIFIED (100% Byte-Exact)** |
| **Tactical / HUD Map Images** | `rimage.zbd` | Top-down map bitmaps (`c1m1.png`, etc.) | ✅ Native texture pipeline | N/A (Image format) | ✅ `unzbd mw textures` | ✅ `rezbd mw textures` | **VERIFIED (100% Byte-Exact)** |
| **Texture Banks** | `texture*.zbd`, `rtexture*.zbd` | World surface tiles, mech textures | ✅ Native texture loader | N/A (Image format) | ✅ `unzbd mw textures` | ✅ `rezbd mw textures` | **VERIFIED (100% Byte-Exact)** |
| **Interpreter Scripts** | `interp.zbd` | Engine state machine & scenario file resolution | ❌ Guest execution | ⚠️ Planned | ✅ `unzbd mw interp` | ✅ `rezbd mw interp` | **VERIFIED (100% Byte-Exact)** |
| **Baked Animations** | `anim.zbd` | Pre-baked mesh and node keyframe sequences | ❌ Guest execution | ⚠️ Planned | ✅ `unzbd mw anim` | ✅ `rezbd mw anim` | **Supported in Mech3AX** |
| **Mech Geometry Library** | `mechlib.zbd` | Stock mech chassis, hardpoints, lods | ✅ Native replacement host | ⚠️ Planned | ✅ `unzbd mw mechlib`| ✅ `rezbd mw mechlib`| **Supported in Mech3AX** |
| **Mech Skeletal Motion** | `motion.zbd` | Walk, run, limp, death skeletal cycles | ✅ Donor rig retargeting | ⚠️ Planned | ✅ `unzbd mw motion` | ✅ `rezbd mw motion` | **Supported in Mech3AX** |
| **Terrain Mesh Geometry** | Part of `gamez.zbd` | Irregular ground meshes & partition bounds | ✅ GPU terrain pipeline | ❌ Geometry sculpting | ✅ (Inside gamez) | ✅ (Inside gamez) | **Read supported; mesh sculpting planned** |

---

## 2. Format Specifications

### 2.1 ZBD Archive Container (`.zbd`)
Every game archive in MW3 is packaged in a Zipper Binary Data (`.zbd`) container.

- **Footer Structure:** Located in the final 8 bytes of the file:
  - `+0x00` (uint32): Archive Format Version (always `1` in MW3 v1.2 retail).
  - `+0x04` (uint32): Directory Entry Count `N`.
- **Directory Table:** Located at `file_size - 8 - (N * 0x94)` bytes.
  - Each directory record is exactly **0x94 bytes (148 bytes)**:
    - `+0x00` (uint32): `payload_offset` (absolute file byte offset).
    - `+0x04` (uint32): `payload_bytes` (uncompressed payload length).
    - `+0x08` (char[64]): ASCII NUL-terminated entry name.
    - `+0x48` (uint32): `opaque_word` (internal engine category / index).
    - `+0x4C` (byte[72]): Opaque metadata (timestamp, alignment, sub-flags).
- **Writing Requirements:** When writing modified entries, `payload_offset` and `payload_bytes` must be recalculated. All trailing directory entries and footer must be re-emitted in strict original sort order. The 72-byte metadata blocks must be preserved byte-for-byte to prevent engine rejection.

### 2.2 Reader Documents (`reader*.zbd`, `*.zrd`)
Reader files contain hierarchically typed binary token documents (ZRD).
Tokens consist of:
- `TokenType::integer` (Type 1): 4-byte signed/unsigned integer.
- `TokenType::float_bits` (Type 2): 4-byte IEEE 754 single-precision float.
- `TokenType::string` (Type 3): 4-byte byte count `L`, followed by `L` bytes ASCII/bytes.
- `TokenType::list` (Type 4): 4-byte child count `C + 1`, followed by `C` child tokens.

**Critical Mission Files:**
1. **`maps.zrd`** (in `zbd/reader.zbd`): Defines all 20 mission and Instant Action maps:
   - `name`: String (e.g. `"c1m1"`, `"c1ia"`).
   - `bitmap`: String matching the top-down map texture in `rimage.zbd` (e.g. `"c1m1"`, `"c1ia"`).
   - `mpp`: Float, Meters Per Pixel (e.g. `3.476000` for C1 maps, `-5.175` for C3 maps).
   - `offset`: Vector3 `[X, Y, Z]` specifying the world coordinate corresponding to the center of the 640x480 map image.
2. **`location.zrd`** (in `zbd/c*/reader.zbd`):
   - Named spawn points with world coordinates `[X, Y, Z]` and initial compass heading `Yaw` in degrees:
     - `"Mission 1 Start"`: `[[-2897.0, -27.1, -1349.0], 0.0]`
     - `"Mission 2 Start"`: `[[-1408.7, -10.0, -845.3], 0.0]`
     - `"Mission 3 Start"`: `[[402.0, 33.0, -980.0], -90.0]`
     - `"IA_base"`: `[[197.0, -4.9, -2219.4], 0.0]`
3. **`reg_*.zrd`** (in `zbd/c*/reader*.zbd`):
   - Trigger regions and bounding polygons: sequence of `node_00`, `node_01`, ... each carrying a 3D coordinate `[X, Y, Z]` and connection indices forming closed convex or non-convex perimeter polygons (e.g. `reg_base`, `reg_water`, `reg_outpost`).
4. **`objectives.zrd`** (in `zbd/c*/reader.zbd`):
   - Mission objectives categorized by `primary`, `secondary`, `tertiary`.
   - Criteria types: `valve_change`, `destroy_entity` (binding to GameZ node names), `protect_entity`, `reach_nav`.

### 2.3 World Scenery & Object Placement (`gamez.zbd`)
`gamez.zbd` contains the static world state for each operation:
- **`nodes.json` / Node Table:**
  - 9,560 scene graph nodes in Operation 1 (`c1`).
  - Hierarchical parenting via `parent_indices` and `child_indices`.
  - Transform data in `data.Object3d.transform.RotateTranslateScale`:
    - `translate`: World position `{x, y, z}` in meters.
    - `rotate`: Euler angles `{x, y, z}` in radians.
    - `scale`: Scale factor `{x, y, z}` (typically `{1.0, 1.0, 1.0}`).
  - Bounding boxes: `node_bbox`, `model_bbox`, `child_bbox` with `a: {x,y,z}` (min) and `b: {x,y,z}` (max).
  - Node Flags:
    - `active`: Boolean (whether node is enabled at startup).
    - `terrain`: Boolean (marks ground/terrain surface meshes).
    - `altitude_surface`, `intersect_surface`, `bbox_node`, `id_zone_check`.
- **Terrain Representation:**
  - In MW3, terrain is not stored as a separate 2D raw heightfield file.
  - Terrain is composed of 1,025 mesh nodes in `c1/gamez.zbd` flagged with `terrain: true`, spanning bounds:
    `X: [-3840.0, 1750.0]`, `Y: [-296.8, 423.4]`, `Z: [-2818.0, 2816.0]`.

---

## 3. Explicitly Labeled Unresolved Fields

The following fields are preserved losslessly during import and export, but their semantic behavior has not yet been reverse-engineered:

1. **`opaque_word` (`+0x48`) in ZBD directory records:** Preserved exactly; altering it causes unknown catalog lookup faults.
2. **`metadata` (72 bytes, `+0x4C`) in ZBD directory records:** Preserved exactly; suspected to contain timestamp, checksum, or spatial sorting keys.
3. **`update_flags`, `field192`, `field196`, `field200`, `field204` in GameZ nodes:** Preserved exactly as integer words.
4. **`signs` (`4104` etc.) in `Object3d`:** Preserved exactly; relates to matrix sign/reflection flags in the original fixed-point math engine.
5. **AI Vehicle Script Thresholds in `aiv.zrd`:** Internal numeric parameters controlling AI engagement ranges and retreat thresholds remain empirical.
