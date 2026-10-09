# Eight-material height and normal-map batch

Recorded 2026-10-07. The user requested the next step after the
[four-material pilot](work-ahead-material-pilot.md), authorizing expansion to all
eight mech and terrain textures in the approved full-AI batch. Four existing
material sets retain their exact bytes and creation history; four newly authored
height drafts complete the remaining materials. Approved color artwork and both
earlier sealed packages remain unchanged.

| Material | Category | Color/height/normal canvas | Preparation |
| --- | --- | --- | --- |
| Annihilator panel | Mech | 1024 x 512 | Inherited pilot maps |
| Avatar panel | Mech | 1024 x 1024 | New authored height and normals |
| Bushwacker panel | Mech | 1024 x 1024 | Inherited pilot maps |
| Shadowcat panel | Mech | 1024 x 1024 | New authored height and normals |
| Beach sand | Terrain | 1024 x 1024 | New authored height and normals |
| Weathered concrete | Terrain | 1024 x 1024 | Inherited pilot maps |
| Stone blocks | Terrain | 1024 x 1024 | Inherited pilot maps |
| Sand transition | Terrain | 1024 x 1024 | New authored height and normals |

The local directory is `local/work-ahead/material-batch-v1/`, with the handoff
ZIP and SHA-256 sidecar alongside it. It contains eight scalar height maps,
sixteen normal maps across both Y orientations, approved color and decoded
original references, native height artwork, generation prompts, editable
documents and the moving-light review gallery.

Source/container/entry mapping and hashes follow the
[texture batch record](work-ahead-texture-batch.md). Numeric settings and importer
requirements follow the [material-map specification](../tools/asset-inventory/material-map-format.md):
explicit red-channel height, strength8 per target texel, four-pixel flat normal
collar, paired green encoding, linear normal data and shader renormalization.
The exporter and its 31 passing authored asset tests are unchanged.
Fresh independent Pillow/NumPy checks reproduce every normal component across
all sixteen maps with zero mismatches and confirm unchanged approved color
hashes. Paired green, flat collar, dimensions, opacity and linear data chunks
also pass. Imported pilot material files retain their exact hashes and lineage.

Sand and transition height drafts target shallow grain on a broadly level plane.
Color transitions, markings, lighting and stains should not become geometric
steps. Mech drafts interpret panel relief while leaving painted marks flat.
These are speculative authored surfaces, not recovered game geometry. Existing
pilot drafts retain their documented residual shading and inferred details.

The gallery provides planar moving-light comparison, material selection,
height/normal/color inspection, strength and Y-convention controls, and terrain
repeat inspection. Its PNGs are embedded for offline use. Static checks do not
establish browser/GPU rendering. Mapped mesh, UV/tangent conventions, material
response and tiling remain open before integration.
All 24 embedded gallery PNGs match the packaged files; local links, filtering,
controls, shader uniforms and JavaScript syntax pass static checks. Editable
height stacks and archive member identities are verified during package closure.

Status: **eight prepared material prototypes; review and mapped integration
pending**. The following [six-frame dust animation pilot](work-ahead-effects-animation-pilot.md)
adds configured sequence evidence and full-AI frames; motion and native blending
remain open. INTRO remains the first planned full video upscale, with processing
held. All working media stays ignored under the local content policy.
