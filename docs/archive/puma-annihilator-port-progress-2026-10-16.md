# Puma / Adder and Annihilator visual port candidates

2026-10-16. The user approved this pair after reaffirming the 12x normal-map goal.
Both are offline visual candidates, not installed in Play MW3Remaster. Existing
seven registrations and Black Hawk/Champion candidate work are preserved.

## Source and assembly

Reuse the installed MW5 archive, pinned package listing, repak 0.2.3 and existing
CUE4Parse UE 4.26 decoder. Selective body/skin/dependency extraction and decoded
metadata retain source identities in ignored `local/work-ahead/mw3-puma-annihilator-r1/`.
Main donors: DLC7 Adder/Adder_SKM and base-game Annihilator/Annihilator_SKM.
Original MW3 mechlib/motion entries and primary-loadout definitions are recovered
from existing admitted local sources; no game files are changed.

Exterior cockpits and all 11 weapon assemblies use source-defined donor sockets
and glTF rest transforms. Puma ADR-PRIME supplies 2 Clan ER PPCs and 1 flamer.
Annihilator ANH-1A hardpoints select 4 LB-X10s and 4 medium pulse lasers to match MW3,
rather than silently carrying the donor's AC10/medium-laser loadout. Static
assembly placement checks preserve existing geometry/transforms. Source weapon
class agreement is not yet muzzle-origin or live weapon-system validation.

## Geometry and walking

Uniformly match original MW3 standing height; retain donor body proportions,
mesh coordinates, UVs, weights and rest joints. Evaluated new/original height
ratios are 1.000000068 (Puma) and
0.999999951 (Annihilator). Widths/silhouettes
retain the modern donor's shape; limbs are not independently stretched.

The first unadapted Puma gait correctly failed fixed-length reach validation;
that failure remains in retarget.log. The canonical retarget script maps source
MW3 foot motion to fixed donor leg lengths, preserves the donor knee bend branch,
keeps thigh motion in its original sagittal plane, removes horizontal travel for
an in-place review, and maps 3 original toe controls per foot by rest direction.
Walking foot-ground baselines use each source cycle's minimum ankle height.
A minimal constant walking pelvis drop makes the complete stride reachable:
Puma 0.09432265 and Annihilator 0.15810596 scene units. Stride amplitude, foot lift
and cadence remain source-driven. The stand pose matches donor rest. This is
an adapted visual gait, not identity with the original MW3 joint matrices.

225 baked walk samples per model retain fixed segment lengths. Reopened saved
actions pass 449-time joint/contact/plane checks, including interpolation midpoints:
Puma maximum contact error 2.92260361e-06,
Annihilator 4.9189408e-06, tolerance 0.0001.
No extra joint mesh or armor pieces are added. The initial template generator is
guarded after validation; reproduce with canonical retarget-r1/build_preview.py
using `-- puma` or `-- annihilator`, preserving the reach/ground adaptation.

## Materials and previews

Primary colors derive from original MW3 texture references on unchanged donor UVs.
Four Body/Variant wear edits use built-in image_gen with the existing normal maps
as hardware/UV guides and Thor R2 as service-wear intensity reference. Exact
prompts, generated images, paths and hashes are retained in maintained-worn-r1/.
Paint cuts, exposed metal, chips, localized soot and seam grime remain readable
in diffuse/unlit views. Shared worn Weapons color is reused only after exact
common normal/UV-atlas identity.17other maps per chassis retain their initial
bytes. Each material pack has 20 maps; Body/Variant colors are 1254 square. Existing
donor normal detail is retained with OpenGL green-channel conversion. Painted
new scars have no newly authored normal relief. Exact original decal transfer
and dynamic damage are not complete; this is an MW3-palette-inspired worn draft.

Walking/light previews use approved 12x response 10.20 for armor/variant/weapons,
glass 0.30, flat missile normal 0.85 where used, and the established illustrative
Bushwacker PBR constants. The ZIP roughness/metallic maps are provisional inputs;
the controlled light test uses those common constants instead of recovered
native shader parity. All 336 output poses exactly match the adapted retarget
scene at the corresponding phase; source curves, geometry and material-only
walk conservation checks pass. Presentation camera/light follow pelvis XY and
all actual model vertices fit over all 336 frames. Ground plane is below the
swept vertex minimum; this is authored review lighting/floor, not game evidence.

Individual MP4s are 1280x960, 336 frames, 30 fps, 11.2 s: six walks/one light orbit.
H.264 CRF 8/slow/grain encodes preserve fine detail. The 2560x1020 side-by-side is
encoded directly from PNG sequences with a separate 60 px header, no downscaling
or label occlusion. Metadata verified; varied gait/light contact sheets reviewed.
Lossless PNG wear/normal comparisons and original-model comparisons are included.
Packed animated Blender scenes and static skinned glTF candidates remain local.
Static glTF export preserves attachment world transforms within 0.00001.

## Delivery and boundary

[Both walks](https://drive.google.com/file/d/1SsOfF9z2tFEgpOEZXHuZDa96ohjyyWjG/view?usp=drivesdk).
[Puma walk](https://drive.google.com/file/d/1Rw_Lzz34RiWm0fFZAvzjTyACRHqov9F3/view?usp=drivesdk).
[Annihilator walk](https://drive.google.com/file/d/1Y-F9f4XFJjHmK46ce4L6Uzn-Imr2Rhrk/view?usp=drivesdk).
[Organized Drive batch](https://drive.google.com/drive/folders/1zvFcOnsjMnPQku-ziRbAVfkpbaNTd9Pd). 32 files and 7 folders have verified
identity/title/parent/MIME metadata; remote byte lengths match local files.
Each chassis has separate Previews/Textures folders with individual colors and
a 20-map ZIP. Download originals for detail checks. No sharing changes.
Local comparison: delivery-r1/comparison.html. Candidate assets and next blockers
are indexed in candidate-assets.json. All rendering-source pins match; shared
launcher/model context before/observed hashes are recorded without reverting
another writer's setup. No launcher registration, game code or runtime asset edit.

Execution boundary advances installed packages -> decoded/assembled donor visuals
-> source-driven offline animation and worn material candidates. Next blocker is
the native visual retarget adapter: the existing source-control rigid fitting
does not preserve these donor leg lengths and walking stance. Muzzle alignment,
damage/detachment, LOD, cockpit/zoom behavior and live performance must then be
validated. Neither a Blender video nor static export grants native gameplay
credit or proves a finished port. No production fallback or fake API success.
Protected processes were left intact. BelowNormal/two-thread jobs; no game
launch, desktop screenshot, registry/pilot edits or commit. Strict acceptance remains paused at 131/144.
