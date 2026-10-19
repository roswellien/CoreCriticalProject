# Original MW3 Avatar: 12x normal-map preview

2026-10-16. At the user's direction, stop the MW4/MekTek donor search and test
the stock MW3 Avatar. No MekTek installation/download or STL geometry is used.

## Model, colors and animation

The decoded original model has 33 hierarchy nodes, 19 geometry nodes,
279 source polygons and 558 triangulated faces. Its source entry SHA-256 is
be2bd3b285b83ba889e57ccfa198dbe70c87750665de9d97a5ad7112e7d3b79c.
Positions, topology, corner UVs and flat polygon shading are preserved. UV V
becomes 1-v for Blender. The original untextured material13 remains white.

Use 25 upgraded primary color bindings from the dedicated published
`D:/Projects/MW34Recomp/local/work-ahead/avatar-textures-v1/modding-v1` bank.
Copies retain their bytes, dimensions and alpha; no new color artwork was made.
The older cumulative Owens bank contains low-resolution stock Avatar images,
so it is not used for this preview. This observation does not establish which
Avatar bank is currently selected by the launcher.

The source MW3 walk has 57 samples /56 intervals /1.8666666746 seconds. It runs
on its own hierarchy six times. Only hip X/Z travel is held at source-stand
values for an in-place review; stored vertical translation and all other motion
are retained. No limb correction, deformation or added joint. Linear preview
curves are not a claim to reproduce native interpolation or ground adjustment.
Every one of the 336 sample poses is checked against the source hierarchy;
maximum world-matrix error is 2.384185791015625e-6 after the same display frame.
Uniform display scaling is 0.9511265215531082. The reference camera's orthographic
scale is widened 15% for the original arm span; all vertices stay at least
0.055188 of the image extent inside the frame across the whole sequence.
The floor is below the swept minimum vertex, without foot-contact corrections.

## Relief and lighting

Twenty-one distinct relief groups serve the 25 material bindings. The built-in
image_gen tool authors three height pages for20 new groups; shared mech01 uses
the prior validated map only after exact RGBA pixel/dimension identity. A fourth
focused edit removes false relief under the red painted triangle. The tiny
unresolved mech02 strip is a flat height field. The source missile tile actually
has11 holes (3+3+3+2), retained in the output; the first prompt's count10 was wrong.

These are authored interpretations of visible mechanical detail. They may add
or simplify fine relief and are not recovered original geometry/height maps.
Paint colors are intended to remain on their underlying plateaus. Residual
alignment error, baked illumination and invented fine relief limit fidelity.
Exact prompts, source reference pages and selected generated outputs are saved
locally. Heights use one-reference-pixel Gaussian filtering; OpenGL tangent
normals use derivative gain16 and Non-Color sampling. Strength10.20 is12x0.85,
a shader response setting rather than physical depth.

The earlier Bushwacker review scene supplies an orbiting soft key, weak fill,
world and floor. Materials use roughness0.57, metallic0.12 and specular0.4.
Normal-on/off differ only in Strength10.20/0. Their camera/light/object matrix
signatures are checked at all336 frames. Neutral-color stills isolate relief
from painted and baked detail. Silhouette and cast-shadow geometry stay stock.

## Outputs and execution boundary

11.2 seconds /336 frames /30fps. Each individual view is1280x960. The comparison
is2560x1020, with a separate60px header and no model-image downscale. Encode
H.264 CRF8 /slow /grain /yuv420p /faststart directly from lossless PNG sequences.
Drive streaming can reduce detail; retain downloadable originals and PNG pairs.

The packed editable scene, three clips, still pairs, maps ZIP, exact prompts,
source pins and delivery checks live in this C: workspace because D: has limited
free space. `preview.html` links them. `preview-checks.json` and
`drive-publication.json` record final validation and verified remote metadata.

Boundary advanced: original MW3 Avatar model/colors/motion to an offline Blender
normal-map/material review. No native renderer, launcher or runtime asset change,
game launch, desktop screenshot, registry/pilot edit or commit. Strict acceptance
is paused at131/144; offline material previews earn zero native credit.
Native normal-map transport, lighting and calibration remain future engine work.

Drive folder:
https://drive.google.com/drive/folders/1iUj76LAOiCeBRfw7fhnkrjl1a-UJFEiz

## Verified delivery

Ten Drive files in three folders: names, MIME types, parents and exact byte sizes
match connector readback. All25 copied colors/source pins remain unchanged.
All21 normal-map dimensions and positive tangent Z check out. Three clips each
contain336 frames /11.2 seconds. Both render passes match at336 camera/light/
object signatures. Local HTML links and the42-map ZIP integrity check pass.

Comparison video:
https://drive.google.com/file/d/1tO8757BfQkgV3u4eFyckJcKQpoZ49UC5/view?usp=drivesdk

12x walking video:
https://drive.google.com/file/d/1BpdtRCsgaiMeL3EIovGloT1knzRtghHS/view?usp=drivesdk
