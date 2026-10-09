# Authored height and normal-map pilot

Started 2026-10-07 after the user visually approved the twelve-texture full-AI
batch. Four opaque materials are selected from that batch: `annihilator-panel`,
`bushwacker-panel`, `stone-blocks` and `weathered-concrete`. Effects remain outside
this surface-normal pilot because their sprite transparency and animation need a
separate treatment. The opening movie remains queued with processing held.

The approved color PNGs are copied unchanged and bound by SHA-256. AI-authored
grayscale height drafts interpret restrained surface depth at the same normalized
feature positions. These are speculative material relief, not recovered geometry
or depth measurements. Flat faces, recessed seams and shallow grain are intended
depth; paint, labels, highlights and shadows should not become extruded geometry.
Initial drafts and targeted correction prompts are retained for review.

## Export convention

The project-authored `export_material_maps.ps1` deterministically sizes a height
input to its approved color image and computes paired tangent-space RGB8 normal
maps. Heights use the explicitly chosen red channel as scalar R8/255, without
color transfer or luminance inference. Strength is measured in target texel units,
so export resolution and strength must be recorded together.

Central differences sample clamped neighboring height texels. Image rows run down
the canvas; the positive-Y convention is
`normalize(-strength*dHdx, +strength*dHdy, 1)`, with X right, Y up and Z toward
the viewer. The paired negative-Y map flips only the encoded green channel.
Normals are data, decoded with `2*RGB-1` and renormalized before lighting. This
data/normalization treatment follows the [Khronos normal-texture specification](https://registry.khronos.org/glTF/specs/2.0/glTF-2.0.html#material-normaltexture);
it does not establish MW3's eventual shader or tangent convention.

Both maps match the color PNG canvas: 1024 x 512 for the annihilator and
1024 x 1024 for the other three. The initial export setting is strength 8 with
a four-pixel flat-normal collar. The collar changes only outer normal texels,
not the height draft; it does not prove seamless repeating height or real UV
boundaries. RGB8 cannot encode exact zero tangent components, so the flat
positive-Y texel is (128,128,255) and its exact green inverse is (128,127,255).

## Local review and handoff

Working files stay under ignored `local/work-ahead/material-pilot-v1/`. Each
material retains approved color identity, generated height/provenance, sized
height, paired normals and export settings/hashes. The local manifest links each
material back to its original container and texture entry.
Editable OpenRaster documents retain scalar height as the visible layer, with
normal maps and approved color hidden as reference layers. The local ZIP and
hash sidecar are stored alongside the batch directory.
The package contains four editable height documents and eight normal maps, with
all 72 file checksums and 73 ZIP entries verified against the working files.

The review gallery provides a planar moving directional light, flat versus
normal shading, both Y conventions, adjustable preview relief, color versus
neutral material, and repeat inspection. Height/normal previews can be examined
separately. Color PNGs already contain painted lighting; adding a preview light
cannot establish a physically accurate material or remove that baked shading.
The light preview does not displace geometry or validate original mesh UVs.

Actual integration still needs recovered geometry/material bindings, tangent
generation, normal handedness, orientation, seam checks and shader support.
Normal/height appearance, alignment and relief strength require review before
expanding this pilot to the remaining mech and terrain textures.
The user's subsequent request to proceed led to an
[eight-material batch](work-ahead-material-batch.md) that retains these four sets
and adds the other four. The original pilot archive remains unchanged.

All four exports pass saved-PNG checks. All 31 authored asset tests pass,
including four material fixtures. Independent Pillow/NumPy recomputation checks
every normal component in both directions with zero mismatches and confirms
unchanged approved color hashes. It uses raw byte gradients before normalization
and reciprocal scaling to avoid different rounding at half-byte boundaries.
Dimensions, collar, opacity, paired green, data chunks and report hashes also
pass. JavaScript and gallery resources receive static checks; actual browser/GPU
rendering remains unverified. Corrected height drafts retain some speculative
features and bevel shading, so numerical correctness does not establish depth
or mapped appearance.
