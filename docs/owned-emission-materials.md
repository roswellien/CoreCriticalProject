# Authored replacement emission

`BWMEM1` is a bounded material descriptor for owned replacement meshes. It is
generic: authors can describe eyes, cockpit glass, engine details or other
luminous regions without a model-name branch or guessed bright-pixel admission.
The maintained native renderer consumes these descriptors through its existing
emissive-region shader and shared point-light budget. This is development
support; released runtime profiles are not retroactively granted the capability.

An optional `emission` object in a New owned appearance supplies `close` and
`distance` sidecar paths. Both are validated even when Original is selected.
Only selected New emission requires `owned-chassis-emission: 1` in the trusted
runtime profile. The generated pack declares `BWMEM1` in `required_formats`;
it does not put the selected-only capability in whole-pack requirements.
Old non-emissive packs retain their existing behavior. New emission packs need
an updated coordinator; historical runtime profiles are not modified.

The little-endian file starts with eight bytes `BWMEM1\0\0`, a uint32 record
count and uint64 mesh/UV identity computed by the existing surface-material
mesh identity algorithm. Each record contains a 32-byte ID, uint32 batch index,
32-byte owner and material names, uint32 color width/height, uint64 full-pixel
RGB565 FNV-1a identity, float32 emission strength, and uint32 rectangle/anchor
counts. A rectangle is four float32 values `(u0,v0,u1,v1)`. Each anchor contains
a 32-byte ID and eight float32 values: local position XYZ, RGB, radius and
intensity. Names are nonempty ASCII identifiers of at most31 bytes followed by
zero padding. Duplicate record IDs, batch bindings and per-record anchor IDs
are rejected. The source mesh, owner, material and color identity must match.

Limits are1MiB per sidecar,64 records,32 UV rectangles and8 anchors per record.
UV rectangles are nonempty and within0..1. Strength/intensity are0..2, RGB0..1,
radius0..4world units. Anchor coordinates are finite, within±1,000,000 and within
four units of their bound batch's local bounds. Zero emission/intensity is a
valid negative control. Unknown versions, trailing bytes and nonfinite values
fail visibly. Version1 requires rigid batches: per-vertex bone-weighted geometry
needs an explicit future anchor-deformation contract and is rejected here.

The descriptor carries no image bytes and never repurposes normal-map alpha.
Light anchors are explicit because mirrored/shared eye UVs cannot reliably
identify two separate world-space light positions. A batch may declare several
regions and anchors, while its textured surface emission uses one strength.
Different per-region surface strengths require split batches or a future format.

Authoring helpers are in `tools/remaster-launcher/owned_emission.py`; the C#
importer and maintained C++ reader enforce the same binding/limit contract.
Tests use authored fixtures, including a Python-written descriptor read by the
actual C# importer. Selected capability gating, byte corruption, wrong mesh or
color identity, malformed regions, anchors and zero controls are covered.
The coordinator stages this reader for both initial installs and refreshed
updates. Composition publishes validated selected files through
`MW34_CHASSIS_<RESOURCE>_EMISSION` and `_LOD1_EMISSION`.

## Reusing it on another mech

Add `emission: {close: "visuals/close.emission", distance:
"visuals/distance.emission"}` beside the New appearance's meshes and textures.
Use `owned_emission.mesh_bindings(mesh_bytes, texture_bytes)` and
`surface_materials.mesh_uv_identity(mesh_bytes)` to obtain each LOD's identities,
then pass records to `owned_emission.pack(mesh_hash, bindings, records)`.
For example, a record can describe two mirrored eye regions with two distinct
local anchors:

```python
record = {
    "id": "cockpit-eyes", "batch": glass_batch, "strength": 0.35,
    "regions": [(0.1, 0.2, 0.4, 0.5)],
    "anchors": [
        {"id": name, "position": position, "color": (1, 0.015, 0.01),
         "radius": 1.2, "intensity": 0.10}
        for name, position in eye_positions
    ],
}
```

The positions and UV bounds must come from that mech's mesh; the example is
not a set of shared coordinates. Use stable IDs in both LODs and regenerate
descriptors after changing geometry, UVs or color pixels. Author gradients and
surface detail in the color texture; emission multiplies the textured color.
No new normal image or texture sampler is required.

Each submitted world draw owns its rigid local-to-world snapshot. Its anchors
join the existing light selection without entering the scenery retention cache.
Duplicate passes within one scene are suppressed by root, owner, material ID
and anchor ID; another actor remains distinct. At most4096 nearest candidates
are retained deterministically before the existing overall light budget applies.
A scene with no emitting draw has no retained owned light. CPU-clipped and GPU
model draws carry the same descriptor and camera receiver metadata.

The existing enhanced sun/effect renderer must be enabled. Normal mapping can
be disabled independently, and glass without a normal sidecar uses the existing
flat-normal fallback. Both self-emission and spill follow the effect/fixture
preferences. They do not use the L key or change authored headlights. The CPU
lighting receiver stays the same when fixtures toggle, so turning glow off does
not replace the material's base lighting path. Frontend/schematic draws do not
create world anchors.

Native evidence and current Atlas limits are recorded in
[Atlas port validation](atlas-mw5-port-validation-2026-11-05.md). Other mechs
require their own authored descriptors and visual validation; the runtime has
no Atlas-specific material or coordinate branch.
