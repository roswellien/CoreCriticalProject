# Optional Surface-Material Contract

This document defines the versioned `BWSFM1` surface-material sidecar contract,
its runtime content capability (`surface-materials` version `1`), and how
authored height, displacement, UV, and subsurface-scattering (SSS) parameters
bind to replacement mech geometry and material batches before entering the
native Vulkan host.

This contract covers reader validation, compatibility verification, preparation
caching, and immutable host record propagation (`OverrideBatch` ->
`ModelInstance` / `Draw`). It does **not** render parallax occlusion mapping
(POM), tessellation/displacement, or SSS on its own, and does not advertise GPU
rendering capabilities for those effects before their respective shader stages
land.

## Design rules and non-goals

- **No normal-alpha overloading:** Existing normal-map sidecars (`BWNRM1`,
  `BWNRM2`, `BWNRM3`, `BWSNR2`, `BWSNR3`) retain their exact semantics. Current
  shaders already use the normal-map alpha channel for detail masks (including
  water/surf/foam). Empty or absent surface-material metadata never rewrites or
  repurposes normal-map alpha.
- **Explicit declarations only:** Missing declarations produce neutral behaviour
  (zero height amplitude, zero displacement, `tessellation_cap = 1`, zero SSS
  participation, and no extra image allocations). Conversely, a material record
  that references a missing or out-of-range image index, or declares non-zero
  height/displacement without a height image, is rejected as a malformed sidecar.
- **Opaque metals and armor default to zero SSS:** `sss_participation` defaults
  to `0.0` for metal, armor, and concrete.
- **No global names or filesystem paths inside binary sidecars:** Distributable
  `BWSFM1` payloads contain only bounded logical identifiers (`asset_id`,
  `material_name`, `image_name`) and raw linear RGBA8 pixel bytes. Any
  identifier containing NUL bytes, path separators (`/` or `\`), `..`, drive
  colons, or control characters is rejected.

## Host world units

All spatial distances in `BWSFM1` (`height_amplitude`, `max_displacement`,
`sss_radius`, `thickness_scale`) are expressed in **native host world units**—the
same coordinate system used by `mw34::vkscene::ModelVertex` positions `(x, y, z)`,
the 3x4 `batch_to_camera` and `sun_world` transforms, headlight `range`
(`1..256`), `shadow_range`, and scenery `draw_distance`. Values are documented
and validated in native host world units and are not labeled meters without a
proven original producer scale factor.

## Compatibility identity (`asset_id`, `material_name`, `mesh_uv_hash`)

A surface-material sidecar is bound to a specific replacement asset and LOD
geometry/UV layout so that switching appearances, skins, or meshes cannot
silently inherit incompatible surface relief or thickness maps:

1. **`asset_id`** (`1..4096` UTF-8 bytes): Logical model and LOD identifier,
   such as `orion:close`, `orion:distance`, or `community.pack:mech:close`.
2. **`mesh_uv_hash`** (`uint64`): 64-bit FNV-1a digest (`0xcbf29ce484222325`
   offset basis, `0x100000001b3` prime) computed over the bound mesh payload's
   batch count and each batch's vertex count and `(x, y, z, nx, ny, nz, u, v)`
   IEEE-754 binary32 vertex stream (or the exact `BWMESH*` payload bytes when
   constructed from a raw mesh sidecar). If the active mesh or UV layout
   changes, `mesh_uv_hash` changes and the reader rejects the mismatched
   sidecar.
3. **`material_name`** (`1..31` printable ASCII bytes, matching `BWTEX1` and
   `BWNRM2` material naming): Identifies the exact material within `asset_id`.
   In a sidecar, `(asset_id, material_name)` pairs must be unique and sorted in
   strictly ascending UTF-8 byte order (`(asset_id, material_name)`) for
   deterministic output.
4. **Batch binding table:** Like `BWTEX1` and `BWNRM2`, each `BWSFM1` sidecar
   carries one `uint32` record index per draw batch (`0..record_count - 1`, or
   `NO_SURFACE_MATERIAL = 0xFFFFFFFF` for batches with neutral/absent surface
   metadata). Every bound record's `material_name` must match the batch's
   albedo material name in `BWTEX1`.

## Binary layout (`BWSFM1`)

All multi-byte integers and IEEE-754 `binary32` floats are little-endian.

### 1. Header (32 bytes)

| Offset | Type | Field | Constraints |
| --- | --- | --- | --- |
| `0` | `char[8]` | `magic` | Exact bytes `"BWSFM1\0\0"` |
| `8` | `uint32` | `version` | Must be `1` |
| `12` | `uint32` | `batch_count` | `1..4096`; must match mesh/albedo batch count |
| `16` | `uint32` | `record_count` | `0..4096` |
| `20` | `uint32` | `image_count` | `0..64` |
| `24` | `uint64` | `mesh_uv_hash` | 64-bit FNV-1a compatibility digest of the bound mesh/UV payload |

### 2. Batch binding table (`batch_count * 4` bytes)

- `uint32 bindings[batch_count]`: Each entry is either `0 <= index < record_count`
  or `NO_SURFACE_MATERIAL` (`0xFFFFFFFF`).

### 3. Material records (`record_count` entries)

Records must appear in strictly ascending `(asset_id, material_name)` order.
Each record consists of two length-prefixed identifiers followed by an 88-byte
fixed numeric payload:

| Field | Type | Constraints & Semantics |
| --- | --- | --- |
| `asset_id_len` | `uint32` | `1..4096` |
| `asset_id` | `uint8[asset_id_len]` | Safe UTF-8 identifier (`[A-Za-z0-9_.:-]`, no path separators or `..`) |
| `material_name_len` | `uint32` | `1..31` |
| `material_name` | `uint8[material_name_len]` | Safe ASCII material name matching the bound batch's albedo material |
| `height_image` | `uint32` | `0..image_count - 1` or `NO_SURFACE_IMAGE` (`0xFFFFFFFF`) |
| `thickness_image` | `uint32` | `0..image_count - 1` or `NO_SURFACE_IMAGE` (`0xFFFFFFFF`) |
| `height_reference` | `float32` | Finite in `[0.0, 1.0]` (neutral default `0.0`) |
| `height_amplitude` | `float32` | Finite in `[-16.0, 16.0]` host world units (`0.0` when `height_image == NO_SURFACE_IMAGE`) |
| `max_displacement` | `float32` | Finite in `[0.0, 16.0]` host world units; must satisfy `max_displacement >= abs(height_amplitude)` (`0.0` when `height_image == NO_SURFACE_IMAGE`) |
| `tessellation_cap` | `uint32` | Integer in `1..8` (neutral default `1`) |
| `uv_scale` | `float32[2]` | Finite non-zero `(scale_u, scale_v)` in `[-1024.0, 1024.0]` (default `(1.0, 1.0)`) |
| `uv_offset` | `float32[2]` | Finite `(offset_u, offset_v)` in `[-1024.0, 1024.0]` (default `(0.0, 0.0)`) |
| `address_mode_u` | `uint32` | `1` (wrap), `2` (mirror), or `3` (clamp), matching D3D texture address modes (default `1`) |
| `address_mode_v` | `uint32` | `1` (wrap), `2` (mirror), or `3` (clamp) (default `1`) |
| `atlas_rect` | `float32[4]` | `(min_u, min_v, max_u, max_v)` finite in `[0.0, 1.0]` with `min_u < max_u` and `min_v < max_v` (default `(0.0, 0.0, 1.0, 1.0)`) |
| `sss_participation` | `float32` | Finite in `[0.0, 1.0]` (default `0.0` for metal, armor, and concrete) |
| `sss_tint` | `float32[3]` | `(r, g, b)` finite in `[0.0, 1.0]` (default `(0.0, 0.0, 0.0)`) |
| `sss_radius` | `float32` | Finite in `[0.0, 16.0]` host world units (`0.0` when `sss_participation == 0.0`) |
| `thickness_scale` | `float32` | Finite in `[0.0, 16.0]` host world units (`0.0` when `sss_participation == 0.0`) |

### 4. Image table (`image_count` entries)

Images carry linear RGBA8 pixels where the **red channel (`R`)** stores the
declared scalar quantity (`height` or `thickness` in `[0, 255]` mapped linearly
to `[0.0, 1.0]`). Green, blue, and alpha channels are preserved verbatim without
colour conversion. Image entries must appear in strictly ascending UTF-8 `name`
byte order with no duplicate names.

| Field | Type | Constraints & Semantics |
| --- | --- | --- |
| `name_len` | `uint32` | `1..4096` |
| `name` | `uint8[name_len]` | Unique safe identifier (`[A-Za-z0-9_.:-]`) |
| `role` | `uint32` | `1` = linear red-channel height, `2` = linear red-channel thickness |
| `width` | `uint32` | `1..4096` |
| `height` | `uint32` | `1..4096` |
| `hash` | `uint64` | 64-bit FNV-1a digest over all `width * height * 4` pixel bytes |
| `pixels` | `uint8[width * height * 4]` | Raw linear RGBA8 bytes |

Every `height_image` index referenced by a record must point to an image with
`role == 1` (`HEIGHT`), and every `thickness_image` index must point to an image
with `role == 2` (`THICKNESS`).

## Budgets and validation limits

- Maximum material records per sidecar: `4096`
- Maximum batch bindings per sidecar: `4096`
- Maximum images per sidecar: `64`
- Maximum UTF-8 bytes per identifier: `4096`
- Maximum total sidecar size and decoded image byte budget per sidecar:
  `64 MiB` (`67,108,864` bytes). Both the Python and C++ readers check all
  length products (`width * height * 4` and cumulative bytes) before allocating
  buffers.
- Truncated streams, trailing bytes after the last image, duplicate `(asset_id,
  material_name)` records, unsorted records, duplicate image names, hash
  mismatches, or out-of-range parameters fail immediately with a visible error.
