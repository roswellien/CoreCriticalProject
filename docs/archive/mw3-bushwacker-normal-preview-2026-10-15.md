# Original MW3 Bushwacker normal-map preview - 2026-10-15

The user requested the same normal-map/walking/orbiting-light test using the
original MW3 Bushwacker with its upgraded textures. This is an offline Blender
experiment, separate from the MW5 replacement and all live game assets.

The original decoded model retains21mesh nodes,314source polygons and635Blender
triangles. Vertex coordinates and polygon corner order are verified against the
decoded source. Corner UVs come directly from original material bindings with
V converted to1-V for Blender and REPEAT sampling;138corners use wrapped UVs.
No smoothing, subdivision or mesh displacement is added. A uniform display-root
transform matches the previous preview's frame1height and center; source local
coordinates and relative animation stay unchanged. Model entry SHA256:
`439dcd024df0f945fab04eb4accf243f8ac90de53b8948e7354aa468961b8f21`.

The24textured material bindings use unchanged upgraded PNGs from the currently
configured cumulative rmechtex bank's source folder,
`local/work-ahead/vulture-textures-v1/main-bank-modding/`. Exact duplicate aliases
share one normal map, yielding17distinct relief tiles. Original untextured
material13 has source RGB255,255,255 and remains a constant white surface in
this simplified shader; full original material-flag behavior is not recovered.

Two built-in image_gen edits interpret the packed color-tile references as
mechanical height, asking for flat paint/markings and relief at actual panels,
vents and fasteners. Gaussian filtering and height derivatives produce OpenGL
tangent normal data (gain16, shader strength.85, Non-Color). These are authored
prototype maps, not recovered original surface detail or a simple color-luminance
conversion. Generative layout/relief decisions and wrapping seams need review.
The upgraded colors are untouched. A neutral-gray toggle pair isolates normal
shading from the color textures' baked highlights and shadows.

The previously saved original MW3 walk runs directly on its source hierarchy,
with horizontal hip root motion projected out as in that earlier diagnostic.
No MW5 retarget or thigh correction is applied.37source-node actions repeat
six times; five samples across three repeats have maximum matrix difference0.
The camera, light orbit, world, ground, fill and material constants come from
the previous1280x960,30fps,11.2-second Eevee test. The primary off/on clips differ
only in normal strength (0 versus.85); a labeled side-by-side video is included.

Ignored workspace: `local/work-ahead/mw3-bushwacker-normal-light-r1/`.
The packed scene, unchanged color copies,17normal/height pairs, prompts, geometry/
UV/source checks and media remain there. Sources, live launcher and model registry
are hash-pinned unchanged. No native renderer integration, game launch, runtime
performance claim, desktop screenshot, pilot/registry edit or commit. Native
execution boundary unchanged; accepted131/144, strict lane paused.

[Organized private Drive folder](https://drive.google.com/drive/folders/1QE_Ge8MC432TnpiP-YH8yOZkdqTv03Zj)
contains separate preview and normal/height-map folders. Earlier MW5 tests remain
available for comparison; new maps fit the original MW3 texture layout only.

Final validation:672frames rendered across two passes; both individual videos
and the labeled1920x780comparison each contain336frames at30fps,11.200seconds.
The same-pose color toggle changes119175pixels by more than4/255 in at least
one RGB channel (whole-image mean difference2.175); the neutral-color toggle
changes110496pixels (mean2.373). These are image differences, not a percentage
of perceived3D. All source pins remain unchanged. Four orbit states and both
textured/neutral toggles were visually reviewed. All11Drive uploads were read
back to verify IDs, filenames and destination folders; receipts remain local.

[Matched off/on video](https://drive.google.com/file/d/1wwXGe-1vU92oukBBBKOvNTg1TrM_4DML/view),
[normal-on video](https://drive.google.com/file/d/1V6GepczaOmG76F67f5ap3gf4tGrckx6Y/view),
[neutral-color comparison](https://drive.google.com/file/d/1uM29oDdIAPbHUoJDiHNYyY8sJ41z1zQu/view),
[normal/height map package](https://drive.google.com/file/d/1KSGzHFH4tk9XYYgMymB-rhMhJibwlczM/view).
