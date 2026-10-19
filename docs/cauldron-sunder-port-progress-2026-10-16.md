# Cauldron-Born and Sunder MW5 visual port candidates

2026-10-16. The user requested more MW5 candidates after choosing to retain the
MW3 Avatar, Firefly, Owens and Strider until suitable higher-polygon donors exist.
Cauldron-Born/Ebon Jaguar and Sunder are the next pair; Supernova is the remaining
untouched local matching chassis. Existing seven live registrations and four
earlier offline candidates are preserved. These two are NOT INSTALLED.

## Assets and fitting

Both donor bodies are from the installed MW5 DLC8 packages. Reused repak0.2.3 and
the existing UE4.26 CUE4Parse decoder.3382 selectively extracted files total
2,007,610,614 bytes; five string-based visual dependency rounds leave zero
unresolved visual string candidates. This is not proof of whole-game dependency
closure. Package/entry identities, exact paths and hashes stay in the local
selection/extraction manifests. Original MW3 hierarchy, materials, primary
loadouts and28 motion clips were recovered from existing local archive inputs.

Body triangle counts: Cauldron-Born34397; Sunder41976. Both include their
source-defined exterior cockpit and complete primary weapon visuals: five on
Cauldron-Born (Clan Gauss,LBX5,ER medium laser,SRM2,LRM10), eight on Sunder
(AC20,2large lasers,2medium lasers,3SRM4). Donor primary classes/counts already
match MW3; no original loadout or gameplay firepoint was changed. Assemblies
use source sockets and original glTF rest frames; existing geometry/placements
pass conservation checks. Visual weapon class agreement does not prove muzzle
alignment with original gameplay origins.

Cauldron-Born's assembled shoulder pods made it8.6% taller than the initial
body-only normalization. A uniform full-rig scale of0.9208388409903242 corrects
this before retargeting; no per-limb stretch, added joint or filler geometry.
The original primary scene and the stopped146-frame first render are retained;
the final files use normal-walk-r2-heightfit. Both complete standing heights
match their original MW3 references within0.000001 relative error.

The source MW3 stand/walk supplies phase, stride, foot lift and root motion.
Original source joints/gameplay remain authoritative; offline visual IK retains
the donor segment lengths and knee bend branch, with thighs in their original
planes. Horizontal travel is projected out for an in-place presentation.
Cauldron-Born needs no walking pelvis drop; Sunder uses0.19379601115768308 scene
units and a measured foot-ground reference to retain fixed-length reach.
Cauldron has no separate source hand controls: forearms inherit arm motion.
Its two toe controls per side map by rest direction to the three donor toe
roots; Sunder has no source toes and donor toe helpers inherit foot motion.

Each225-sample retarget preserves mesh/UV/weights/rest joints. Reopened actions
pass449 joint/length/plane checks including interpolation midpoints; maximum
joint error remains below0.000005 scene units. Standing rest matches donor.
Only stand/walk are covered; falls, damage and live animation decisions remain.

## Materials and presentation

Primary colors use original MW3 texture palettes on unchanged donor UVs. Four
built-in image_gen Body/Variant edits add readable paint cuts, metal cores,
edge chips, localized scorch and seam grime, using matching donor normal maps
as hardware/layout guides and Thor R2 as the approved wear-intensity reference.
Exact prompts and selected1254-square outputs are saved in maintained-worn-r1.
Shared worn Weapons color is reused only after exact common normal/UV-atlas
identity. Each20-map pack changes three color files;17other maps are byte
identical. No newly authored normal relief is claimed for painted new scars.
Palette inspiration does not constitute exact original decal transfer.

The moving-light test uses approved12x response10.20 for armor/variant/weapons,
glass0.30 and missile head0.85 where used. Existing donor normal detail retains
the OpenGL green-channel conversion. Lighting/material constants match the
earlier Bushwacker test; roughness/metallic maps are provisional authoring inputs,
not native shader parity. Geometry, weights, rest joints and source action curves
are unchanged by the material/render pass. All336 rendered phases match the
adapted source scene exactly (maximum stored-matrix error0). Camera/light follow
horizontal pelvis movement; all actual vertices fit over the full336 frames.
Floor placement is below the swept minimum, not native collision/ground proof.

Each video is1280x960 /336frames /30fps /11.2seconds, with six walks and one
light orbit. Composite2560x1020 is encoded from lossless PNG sequences with an
external60px header and no model-image downscale. H.264CRF8/slow/grain/yuv420p/
faststart. Lossless wear/normal/unlit and original-model comparisons accompany
packed animated scenes and static skinned glTF candidates. Static attachment
world transforms differ by less than0.00001 after export. glTF is not animated;
the editable animated Blender sources are retained separately.

## Delivery and execution boundary

[Walking comparison](https://drive.google.com/file/d/1YuWx7CuZ8sV_tcWjpUTpntekDPpHWyrB/view?usp=drivesdk).
[Organized Drive batch](https://drive.google.com/drive/folders/1t1XJCQEYEu3rtQ2GpXSCv3MC3F_luuzF). All32files /7folders have verified identity,
name,MIME,parent and exact remote/local byte lengths. Material packs, static
glTF, source pins, all local HTML links and three video stream metadata checks
pass. Download originals for detail; Drive streaming may reduce quality.

Local outputs live at C:/Users/jcbla/.codex/workspace-storage/MW34Recomp/
mw3-cauldron-sunder-r1 because D: has limited space. delivery-r1/comparison.html
links the current assets; candidate-assets.json records the next boundaries.

Boundary advanced: installed packages -> decoded complete assemblies -> original-
driven offline animation and maintained/worn material candidates. Next blocker
is an optional native visual retarget adapter preserving these donor proportions;
then muzzle alignment, damage/detachment, LOD, cockpit/zoom and performance tests.
No engine/launcher/runtime assets were written by this batch. Before/observed
live-context hashes are recorded without reverting other writers. No game run,
desktop screenshot, registry/pilot edit or commit. Protected jobs remain intact.
Offline previews earn zero native credit; strict acceptance remains paused131/144.
