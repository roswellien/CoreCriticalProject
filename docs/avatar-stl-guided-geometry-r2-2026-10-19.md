# Avatar STL-guided geometry revision R2

2026-10-19. After reviewing R1, the user asked for a stronger geometry upgrade
and specifically authorized working from their Avatar STL. This revision uses
that file as both a geometric donor and a form reference. R1 is preserved.
The older, mis-fitted STL animation experiments are not reused.

## Geometry boundary

R1 has17,318triangles; R2 has36,038 in the same19 MW3 controller-owned parts.
The original558-triangle reference and its UVs remain unchanged in the scene.
R2 adds more substantial forms rather than increasing fine normal-map noise:

- 81 deep, stepped/chamfered armor shells replacing R1's shallow layers, larger
  manufactured bevels and shaped roof/arm/thigh/shin/foot armor.
- Stepped shoulder bearings, hip and knee covers, ankle covers, original-toe
  hinge covers/pins and recessed hip-cover fasteners. These cover existing
  pivots; no new joint/control is added and no limb is moved or rotated.
- A central cockpit/nose extracted anew from the untouched52,262-triangle STL.
  It contributes6,580triangles. Only its largest connected clipped surface is
  retained, with cut faces closed/triangulated. It is fitted to the original
  central torso profile and owned by that existing torso control. This is a
  local adapted shape, not the whole STL or an imported skeleton.

The STL source SHA256 is
`79edde800dd44f7dec4fc6554b99e614375dfb44d646a8f175375c5ebbc46de5`.
Raw source coordinates also remain in a hidden reference collection. Canonical
inspection uses30degrees yaw correction. The fitted front uses original hull
faces0/69 as backing:0.18unit rear inset and up to0.32unit forward relief.
Early standalone-mask and nearest-face fits were rejected during authoring;
the latter crossed adjacent pod faces. The final shared centerline profile
keeps the adapted cockpit against its intended hull section.

Original MW3 proportions, controller hierarchy, sampled walk and gameplay firing
points remain. Existing22 missile and six muzzle collars and15vent regions are
retained, aligned to the revised armor surface. Solid added cover geometry
overlaps the retained hull intentionally; it is not a watertight printing mesh
or a new internal mechanical simulation. Full native collision, damaged/debris
shapes, LOD and effects alignment are not provided by this prototype.

## Materials and review limits

All46 packed color/normal source images are reused unchanged. Existing body
normal response stays at10.20, the12x0.85 reference. New bearing/edge/well
materials use constants. The adapted nose uses a small existing armor-paint
patch without connected normal relief, plus smooth geometric glazing. This new
nose mapping and the clean added mechanical covers are provisional material
fits, not a completed new weathering/UV pass. The R2 shape changes should be
judged in the gray views as well as the color comparison.

This is an offline Blender candidate, NOT INSTALLED in either launcher. This
task changes no native renderer, executable, registry or prepared pack. The15
registered chassis and Mad Cat/Vulture R4 assets are untouched by this task. Native payload,
LOD and weapon/damage/live-joint/performance validation remain before adoption.
There is no new FPS or native-game claim. Strict acceptance stays paused131/144.

Workspace:
`C:/Users/jcbla/.codex/workspace-storage/MW34Recomp/avatar-detail-stl-20261019-r2/`.
The candidate, source identity, method, build/render scripts and lossless frames
stay local. No game launch, desktop screenshots, original pilot/registry edits,
commit or sharing change. Only rendered reviews and notes are uploaded.

[Organized R2 review folder](https://drive.google.com/drive/folders/1Zi5FrbFoHRveJg2f6hKmK1B4RbpGaA6i).


## Verified review delivery

All336checked world transforms of the34original controller/frame objects match
R1 exactly (maximum error0); reference geometry/UV and action hashes remain.
Each of the19new parts has its original parent/local matrix. Actual vertices
stay framed through all336poses, with minimum margin0.0572993. Reopened-scene
checks pass finite positions/UVs, material slots, no unapplied modifiers and46
packed source-image hashes. The hidden STL reference retains52,262faces.

R1/R2 rendered camera/light/object matrix signatures match at all336frames.
Individual videos1280x960; comparison2560x1020 with an external60px header,
no model-image downscale. Each has336frames /30fps /11.2seconds, six original
in-place cycles and one light orbit, encoded CRF8/slow/grain from lossless PNGs.
Four paired gray views use matching material/light/camera and pass full framing.
Three local video stream/count/duration checks and local HTML references pass.

Ten Drive files in Previews/Notes have verified names, MIME types, parents and
exact byte sizes. Local hashes are recorded without claiming remote checksum
equality. Only two videos, rendered stills and notes are uploaded. Download
original videos when inspecting detail; streaming can add compression.

[Geometry comparison](https://drive.google.com/file/d/1nVdXRoSTwiNgH3va625KmKEAd0o8q9-l/view?usp=drivesdk)
and [matched walking comparison](https://drive.google.com/file/d/1PXzGMP_9umlcnH2_cjQO0Z8HL_QCi1dK/view?usp=drivesdk).

Local review: `local/work-ahead/mw3-avatar-detail-r2/comparison.html` and packed
`avatar-detailed-r2.blend`. Source/build/render/delivery receipts are retained
in the private authoring workspace. R1 remains intact.

The initial whole-live-context equality check correctly detected independent
changes to both launcher profiles during this work. Those files now point at
the separate integrated-lighting r6 host,efff7b59. They were read and preserved,
not restored or modified by this task; that host is not validated by this
offline asset check. Both model registries and original game registry still
matched their initial hashes at the recorded check. Actual changed-file hashes
are in `live-context-observation.json`. Geometry/source checks remain separate
from this mutable live context. No native success or unchanged-launcher claim
is inferred from the offline checks. Strict acceptance stays131/144paused.


## 2026-10-19 - R3 hip-cover seating correction (offline)

The user correctly identified detached outer hip covers in R2. Their placement
used the maximum thigh width instead of the narrower upper-thigh surface,
leaving the backing about 0.526374 model units outside the stock core. R3 moves
only the existing covers and bolts inward by 0.556374 units per side, seating
their backs 0.03 units into the thigh. No extra connector or geometry is added.
This is overlapping rigid game geometry, not a welded manufacturing mesh.

Exactly 504 vertices per side (1,008 total) move on X only. All other vertices,
UVs, materials, topology, limb transforms, joint pivots and animation remain.
The candidate retains 36,038 triangles, 19 source-owned parts and 46 byte-identical
packed source images. Mounting samples at 17 positions per side pass; the covers
share the thigh controller. All 34 source controller/frame world matrices match
over 336 poses with maximum error zero. Unlike the earlier transform-only checks,
the new checks explicitly inspect the cover backing against the core surface.

Three before/after boards and a matched 112-frame walking close-up expose the
seat. The geometry walk disables normal/color maps and uses identical camera,
light and object transforms. The 2560x1020 H.264 comparison is 30 fps / 3.733333 s,
CRF 8 from lossless frames. These are offline rendering and mounting checks;
native LOD, weapon, damage, live-joint and performance checks remain open.

Five Drive previews/notes have read-back name, MIME, parent and exact byte-size
verification. Local SHA values are recorded separately, without claiming remote
checksum equality. Only rendered media and notes are uploaded; raw assets stay
local. No sharing changes.

[R3 review folder](https://drive.google.com/drive/folders/1NnBiXaOoXofzZw7h3KeH6YOXJntU5a2k),
[geometry before/after](https://drive.google.com/file/d/1G_AsZKKqIKy0h3qzCSysFIPdTOwAsaas/view?usp=drivesdk),
[walking comparison](https://drive.google.com/file/d/1hYbMJIakME34ChGYEkctcx8o71hg5vAa/view?usp=drivesdk).

Local review: `local/work-ahead/mw3-avatar-hip-fit-r3/comparison.html`;
packed scene: `avatar-hip-fit-r3.blend` in that folder. Scripts and receipts:
`C:/Users/jcbla/.codex/workspace-storage/MW34Recomp/avatar-hip-fit-20261019-r3/`.
R2 is retained. This advances the offline Avatar attachment-fit boundary only;
NOT INSTALLED. Live profiles/registries remain at their observed initial hashes.
No game run, desktop screenshot, original registry/pilot write or commit.
Protected Python jobs remain running. Strict acceptance stays 131/144 paused.


## R4 runtime adoption

The user subsequently approved texturing and installation. The corrected R3
geometry is now the [R4 textured native Avatar](avatar-native-integration-2026-10-19.md),
installed in both launcher profiles. R1-R3 historical scenes remain preserved.
