# Original MW3 Avatar geometry upgrade R1

2026-10-19. The user requested geometry upgrades for the remaining three
stock-model chassis, starting with Avatar. Avatar, Owens and Firefly are that
remaining group; Strider already has its authored geometry upgrade. This pass
uses the original MW3 Avatar, not the parked STL adaptation or a MW4/MW5 donor.

## Geometry and materials

The source model has 558 triangles in 19 rigid moving geometry parts. The
authored candidate has 17,318 triangles, merged into those same 19 controller-owned
parts. The original reference geometry and UVs remain unchanged in the editable
scene. No control is added, rotated, translated, stretched or reparented.

Added 95 shallow source-textured armor layers, 15 physical vent regions with
louvers, 22 missile-tube collars following the original eleven-hole layout on
each side, six muzzle collars, two source-aligned cockpit frames/panes and
manufactured edge bevels with weighted normals. Joint locations, limb lengths,
foot/toe hierarchy and gameplay firing points are unchanged. Large plates stay
planar; this work adds mechanical shapes rather than general surface noise.

New parts follow hardware already painted in the MW3 texture layout. Ports and
vents are shallow facade wells over the retained core, not cut-through internal
mechanisms. No cockpit interior or new joint assembly is modeled. Overlapping
armor/core pieces are intentional game geometry, not a watertight printable mesh.

Existing upgraded Avatar base-color and authored normal images are reused
unchanged. The normal response remains Strength10.20, the previous12x0.85
reference. New exposed edges, vent blades and dark wells use recorded constant
materials. Cockpit panes have smooth source-colored glazing without connected
normal relief. The original tiny untextured white head patch receives dark-blue
smooth glazing in the candidate only; its original coordinates/control remain.
Existing baked color shading and interpreted relief retain their prior limits.

## Execution boundary and checks

Boundary advanced: original stock Avatar model/material/walk -> authored geometry
candidate and offline Blender review. This is not installed in either launcher.
No native host, geometry registry, normal registry or prepared pack is changed.
The current15 replacement chassis, including the Mad Cat/Vulture R4 live arm
repair, remain installed. Owens and Firefly geometry work has not started.

All336 existing walking-preview poses retain exactly the same34 controller/frame
world matrices: maximum error0. The original action curves and reference
geometry/UV hashes are unchanged. Each detailed part has the same parent and
local matrix as its source part, with no unapplied modifier. Actual detailed
vertices remain in the camera at every336 poses; minimum margin0.0560757.

The existing MW3 sampled walk remains in place, with only the earlier preview's
horizontal hip travel removed. Preview interpolation, display scale, orbiting
light and material response are not a claim of native animation/lighting parity.
Authored surface additions slightly change local silhouette and triangle cost;
there is no native performance measurement. Native payload/registration, LOD,
weapon alignment, damaged/debris states and live joint checks remain before
installation.

Private authoring workspace:
`C:/Users/jcbla/.codex/workspace-storage/MW34Recomp/avatar-detail-20261019-r1/`.
Source pins, build script, tailored mesh helpers, packed editable scene,
geometry manifest and render checks are retained there. No desktop screenshots,
game launch, original registry/pilot writes or commit. Strict acceptance remains
paused131/144; offline geometry work earns no native-game credit.

## Review delivery

The [organized Avatar review folder](https://drive.google.com/drive/folders/1Oll-tlBkwQyALDvr_ygnauJrjKUP3Hn3)
contains separate Previews and Notes folders. Only rendered review media and
notes are uploaded; original model/texture files and the editable scene stay
local. Drive sharing settings are unchanged.


## Verified delivery and local review

Two matched walking passes each contain336frames /30fps /11.2seconds, six
original walk cycles and one light orbit. Camera/light/object matrix signatures
match at all336frames. Videos use H.264 CRF8/slow/grain from lossless PNGs;
individual view1280x960, comparison2560x1020 with an external60px header and no
model-image downscale. Four paired gray views disable normal/color/alpha maps
and use identical constant surface properties and a view-relative inspection
fill. Complete geometry framing passes in each view.

Reopening the saved candidate verifies19matching original controller parents
and local transforms, no unapplied modifiers, finite vertices, valid material
slots and46packed image byte hashes equal to their copied source files. All
source pins and five initial launcher/registry context files remain unchanged.
Three local video stream/count/duration checks pass. The local HTML's links and
15copied deliverables verify. Only two video originals are uploaded.

[Walking comparison](https://drive.google.com/file/d/1yR2nacQwbkyq5vjiNdVOZ9_M-AhBY41d/view?usp=drivesdk),
[textured still comparison](https://drive.google.com/file/d/18QmsyMWfysjk2a86B-YJZ9sfH3jUz1OW/view?usp=drivesdk),
and [geometry-only comparison](https://drive.google.com/file/d/1hvcIOY13nzHRdWKSX8-OKVgYD7OyMlTt/view?usp=drivesdk).
Nine Drive files in Previews/Notes have verified names, MIME types, parents and
exact byte sizes. Local SHA256values are recorded; no remote checksum equality
claim. For fine detail, download the originals rather than relying on streamed
compression.

Local review: `local/work-ahead/mw3-avatar-detail-r1/comparison.html`.
The packed editable `avatar-detailed-r1.blend` stays in that local folder.
The new geometry is an offline candidate; native registration/LOD and live
weapon/damage/joint/performance validation remain the next integration work.
Strict acceptance remains131/144paused.


Follow-up: user requested stronger forms and use of the STL. See [R2 STL-guided geometry](avatar-stl-guided-geometry-r2-2026-10-19.md); R1 is preserved. Both remain offline candidates.
