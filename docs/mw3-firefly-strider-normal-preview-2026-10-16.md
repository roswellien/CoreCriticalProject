# Original MW3 Firefly and Strider: 12x normal-map tests

2026-10-16. The user requested the same upgraded-color normal/light walking
tests already performed for the original Avatar and Owens. Original MW3 models
remain the selected path for these four chassis pending suitable higher-polygon
donors. This batch uses no MW4, STL or MW5 replacement geometry.

## Model, colors and source motion

| Model | Nodes | Geometry nodes | Polygons | Triangles | Motion clips | Color bindings | Unique normals |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Firefly | 34 | 21 | 297 | 622 | 14 | 32 | 16 |
| Strider | 32 | 16 | 356 | 759 | 14 | 22 | 15 |

Model entry SHA-256: Firefly 3b3e8e1229ffcfa37aacfe84981c936e0c40e03fed0860683c00a359de188bc2;
Strider 5d4567cac5f6a2377c2ee3e5667a2ed2331f53d03e525c7560d7b0a229f0f96a. Existing bounds-checked model/motion parsers
recover the original hierarchy, raw local transforms, geometry, corner UVs,
materials and clips from local user media. Blender changes UV V to1-v and
retains flat original polygon shading and untextured material13.

Use dedicated published Firefly/Strider exports/source-anchored primary colors;
shared mech01, weap_hole and footpad colors come from the existing cumulative
puma-strider-launcher-v1/main-bank-modding bank. Every copied color retains its
bytes, dimensions and alpha. No new color artwork was made, and this source
selection is not a claim about which bank the current launcher installs.

Each original walk has 57 samples / 56 intervals / 1.8666666746 seconds. Six repeats
give 336 frames / 11.2 seconds at 30 fps. Only hip horizontal X/Z travel is held at
source-stand values for an in-place presentation. Vertical translation and all
other original stored motion are retained. There is no limb fitting, added
joint, mesh deformation or topology/UV change. All 336 sample poses per model
match the original hierarchy under one uniform display transform. Maximum
world-matrix errors: Firefly 1.9073486328125e-06; Strider 1.9073486328125e-06.
Minimum screen margins: 0.091563/0.116439.
The floor is below the swept minimum vertex. Piecewise-linear preview curves
and floor placement do not reproduce native interpolation, ground adjustment,
game animation decisions or damage state transitions.

## Relief and lighting

Firefly has 13 new height tiles, Strider 12; each reuses three shared maps only
after exact RGBA pixel/dimension identity. Four built-in image_gen atlas edits
author the new interpreted mechanical relief. Two focused corrections remove
the false Firefly yellow-triangle/hazard-stripe relief and Strider painted
three-triangle insignia relief. Selected1254-square pages, initial attempts,
exact prompts and crop mappings are preserved. Smooth cockpit panes avoid
treating reflections as surface relief; mechanical frames/vents remain.

These are authored interpretations of source texture hardware, not recovered
original height data. Approximate alignment, residual baked shading, simplified
or invented small detail and retained diffuse illumination limit fidelity.
Paint is intended to remain at its underlying plate's height. Height crops use
one-reference-pixel Gaussian filtering; OpenGL tangent normals use derivative
gain 16, Non-Color sampling and Strength 10.20 = 12x0.85. Original geometric
silhouettes, flat polygon boundaries and cast-shadow geometry remain unchanged.

The approved Bushwacker reference scene supplies the orbiting key, weak fill,
world, floor and camera. Materials use roughness 0.57, metallic 0.12, specular 0.4.
Matched normal-on/off differ only in Strength 10.20/0; camera/light/object matrix
signatures agree across all 336 frames in each pair. Neutral-color stills isolate
the normal response from existing painted and baked details.

## Delivery and boundary

[Firefly comparison](https://drive.google.com/file/d/1Ibwjr-9j-vw3LB8lgcQPfJyCDbQYxAZZ/view?usp=drivesdk).
[Strider comparison](https://drive.google.com/file/d/1mGq2290jMMJrfY5Qny6tE0fA8JD_z_bE/view?usp=drivesdk).
[Organized Drive batch](https://drive.google.com/drive/folders/1hTVAlWNBh5sVunDE9pnKqNzMXcgNzeME). Each model has separate Previews and
Textures folders. Twenty files in seven folders have verified identity, names,
MIME types, parents and exact remote/local byte sizes. No sharing change.

Each individual clip is 1280x960; comparisons are 2560x1020 with a separate 60px
header and no model-image downscale. H.264 CRF8/slow/grain/yuv420p/faststart is
encoded directly from lossless PNGs. Six clips, matched PNG pairs, neutral
comparisons and walking/light contact sheets are retained. Download originals
for detail; Drive streaming may lower quality. Each material ZIP includes copied
base colors, normal/height maps, exact prompts and binding metadata. Archive
integrity, source pins, normal dimensions/positive tangent Z, 336-frame stream
counts and local HTML references pass. Color/normal/height PNG totals: 64/52.

Local workspace: C:/Users/jcbla/.codex/workspace-storage/MW34Recomp/
mw3-firefly-strider-normal-light-r1. comparison.html links both full reviews.
Each model folder contains its packed editable mw3-<model>-normal-12x-walk.blend,
textures, prompts, lossless frames and checks. C: is used because D: is low on
space; prior work remains intact.

Boundary advanced: original MW3 model/upgraded colors/source walk -> interpreted
normal material and matched offline moving-light review. No native renderer,
launcher or runtime asset writes, game launch, FPS measurement, desktop capture,
registry/pilot edit or commit. Initial/observed live-context hashes unchanged:
True. Other writers and protected jobs preserved. Native normal transport,
lighting and calibration remain engine work. Strict acceptance stays paused
131/144; this batch earns zero native gameplay credit.
