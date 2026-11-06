# Authored replacement emission

`BWMEM1` is a bounded material descriptor for owned replacement meshes. It is
generic: authors can describe eyes, cockpit glass, engine details or other
luminous regions without a model-name branch or guessed bright-pixel admission.
This initial contract/import change does not yet implement native glow.

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
Native draw-uniform and moving-light integration follows this contract before
any real runtime advertises the capability or native glow is claimed.
