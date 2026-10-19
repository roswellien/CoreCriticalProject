# Supernova MW5 visual port candidate

2026-10-16. The user authorized the next untouched MW5 match after the
Cauldron-Born/Sunder batch. Supernova completes initial visual preparation for
all14 locally matching MW5 BattleMechs: seven existing runtime registrations
and seven offline candidates. This is not completion of14 playable ports.
Avatar, Firefly, Owens and Strider retain original MW3 models until suitable
higher-polygon donors are found; the STL experiment stays parked.

## Assets, assembly and animation

The installed DLC9 Supernova_SKM and SNV-1 primary donor were decoded using
the existing selective repak/CUE4Parse UE4.26 workflow. The local manifest pins
1497 files /1,421,745,100 bytes. Zero unresolved visual
string candidates remain in that selective scan; it is not whole-game dependency
closure, and damage/effect/gameplay packages are outside this visual preparation.
Original MW3 hierarchy has35nodes,19geometry meshes,285polygons and11firepoint
markers;13original motion clips were recovered. The walk has57samples over
56intervals /1.8666666746s. None of these original controls was edited.

Main donor body:30368triangles /107bones. Complete body, exterior cockpit and
six separate ER large laser visuals: 34040 triangles /8mesh instances.
Donor SNV-1 classes/counts match the original six ER large lasers, three per arm.
Original loadout and gameplay firepoints are unchanged. Weapon placement uses
source sockets and source rest frames; visual agreement does not establish
alignment of each barrel with original gameplay firing origins.

The full standing assembly was height-normalized before retargeting with uniform
scale1.0000000239946127. The final saved worn scene's new/original height ratio
is0.999999685195; local mesh coordinates, UVs, weights and rest skeleton
are preserved. No per-limb stretch, added joint, connector or filler geometry.

The offline visual walk keeps donor segment lengths and thigh planes, driven by
original MW3 phase/stride/lift. Horizontal travel is projected out. A constant
walking pelvis drop of0.423771557859scene units is the minimum fixed-length reach
correction under the established10%-of-hip-height cap. The original ankle minimum
sets the foot-ground reference. Original source animation remains authoritative;
this is a visual candidate, not a gameplay/skeleton replacement.

Actual toe controls are preserved: Left Middle/Pinky/Index map to ltoe02/01/03;
Right Middle/Pinky/Index map to rtoe02/03/01. Original hand controls are present.
All225retarget samples pass; reopened saved curves pass449joint/length/plane
checks, including interpolation midpoints. Maximum contact error is
0.000004822109scene units. Standing rest matches donor; only stand/walk
are covered. Falls, damage, aim blending and native animation decisions remain.

## Materials and previews

Primary colors use the original MW3 Supernova armor palette (supernova04/07/13)
on donor UVs. Two built-in image_gen Body/Variant edits add visible steel-core
paint cuts, edge chips/rub, localized scorch and seam grime, retaining serviced
armor. Donor normals guide hardware/UV layout; approved Thor R2 guides wear
intensity. Exact prompts and selected1254-square PNGs are retained under
maintained-worn-r1. Shared worn Weapons color is reused only after exact donor
normal/UV atlas identity. Three color files change;17other maps are byte-identical
in the20-map pack. New painted scars have no newly authored normal relief.
The original palette is inspiration, not exact transfer of original decals.

The normal/light walk uses the approved12x response: Blender Normal Map
Strength10.20 for Body/Variant/Weapons, glass0.30; flat MissileHead0.85 if used.
Existing donor normals retain the DirectX-to-OpenGL green-channel conversion.
Bushwacker reference material/light constants are retained; roughness/metalness
maps remain provisional authoring inputs, not native shader parity.

The material/presentation pass preserves geometry, weights, UVs, rest joints and
source action curves. All336rendered poses match the adapted source scene with
maximum stored-matrix error0. The camera and light follow horizontal pelvis
movement; all evaluated model vertices fit across the full walk. Floor is below
the measured swept minimum, which does not prove native ground collision.

HQ video:1280x960 /336frames /30fps /11.2s, six walks and one moving-light orbit,
H.264CRF8/slow/grain/yuv420p/faststart encoded directly from lossless PNGs.
Lossless wear/normal/unlit, original comparison and walking contact sheet are
included. Static skinned glTF is retained without animation; the packed animated
Blender scene is separate. Maximum attachment export transform error is
0.000000953674. Read local delivery-r1/comparison.html for all links.

## Delivery and execution boundary

[High-quality walk](https://drive.google.com/file/d/1t5ikMEXe_njl4qR6BSK73ECrPBfIY__P/view?usp=drivesdk).
[Organized Drive folder](https://drive.google.com/drive/folders/14zgDxIUzrmncjFzypAqYH3MOgyC21CS9). All15files /3folders have verified identity,
name, MIME, parent and exact remote/local byte lengths. Source pins,20-map ZIP,
static glTF, video streams and local HTML references pass. Download originals
for fine detail; Drive streaming can reduce quality. No sharing settings changed.

Local outputs: C:/Users/jcbla/.codex/workspace-storage/MW34Recomp/mw3-supernova-r1.
Packed scene: normal-walk-r1/supernova/supernova-normal-walk-12x.blend.
Exact built-in image-generation prompt set: maintained-worn-r1/generation-prompts.json.
candidate-assets.json records status and integration inputs. D: low space is
the reason for C: placement; earlier work was preserved.

Boundary advanced: installed cooked media -> decoded complete assembly ->
original-driven offline walking and maintained-worn/12x material candidate.
NOT INSTALLED. Next blocker is the optional native visual retarget adapter;
then muzzle alignment, damage/detachment, LOD, cockpit/zoom and live performance.
No engine/launcher/runtime assets were written by this batch. Before/observed
live-context hashes are recorded; unchanged=True. Other writers were preserved.
No game run, desktop screenshot, registry/pilot edit or commit. Strict acceptance
remains paused131/144; offline visual work earns zero native acceptance credit.
