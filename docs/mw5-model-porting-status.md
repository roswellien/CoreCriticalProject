# MW5 model porting status

## October 16: all prepared models connected to native Remaster

All14MW5matches and the detailed original Strider are now registered in the
standard launcher (15chassis,29close/distance bindings). Eight additions draw
in actual native IA with current maintained-worn colors. Parked STL Avatar
remains excluded; Avatar/Firefly/Owens keep original geometry. The current host
retains graphics/HUD/music and passes the three original-compatible regressions.
Cockpit identity, donor-length retarget and Strider controller-local binding
are corrected. [Installed paths, tests and remaining fidelity limits](all-models-native-integration-2026-10-16.md).
Native normal maps and full combat/LOD transition/muzzle/performance QA remain.
Older offline statuses below are retained history; strict131/144stays paused.


## October 16: authored stock-Strider geometry prototype

At the user's request, the original Strider design now has a higher-detail
prototype: 17,129 triangles, original 16 moving controls/walk, beveled armor,
layered plates, cockpit frames and physical vents/joint covers. It uses the
existing upgraded colors and 12x body-normal reference. This is authored MW3
geometry work, not another MW5 donor. The installed stock model is unchanged.
[Preview, editable assets and checks](strider-geometry-detail-prototype-2026-10-16.md).
Native visual integration/damage/LOD/performance remain open; 131/144 stays paused.

Follow-up material review: the user found broad flat plates/head roof too
wrinkled. The [smooth-plate revision](strider-normal-surface-cleanup-2026-10-16.md)
cleans twelve relief tiles while retaining 12x strength, colors, geometry and
the original walk. R1 is preserved; R2 is the current offline material preview.

## October 16: original Firefly and Strider material tests

The four chassis retaining MW3 geometry now all have original-model 12x
normal-map previews: Avatar, Owens, Firefly and Strider. The latest pair uses
unchanged upgraded colors, 16/15 normal maps and matched original walks.
Both pass 336 source-pose and normal-toggle camera/light checks. Videos, stills
and material packs are on Drive. This adds no replacement model or native
material support. [Firefly/Strider results](mw3-firefly-strider-normal-preview-2026-10-16.md).
Strict acceptance remains paused at 131/144.

## October16: Supernova completes initial local MW5 visual coverage

Supernova now has its complete cockpit/six ER large lasers, donor-length walking
fit with original three-toe controls, maintained-worn20-map set and12xHQ previews.
449saved contact checks and original MW3 complete standing height pass. This is
an OFFLINE CANDIDATE, NOT INSTALLED. Native retarget/combat/LOD/live checks remain.
[Supernova record](supernova-port-progress-2026-10-16.md). All14locally matching
MW5 chassis have initial visual work:7runtime registrations plus7offline
candidates (Black Hawk, Champion, Puma, Annihilator, Cauldron-Born, Sunder,
Supernova). This does not mean14completed playable ports. Original MW3 Avatar,
Firefly, Owens and Strider remain until suitable higher-polygon donors exist.
Strict acceptance remains paused131/144. Older sections retain historical status.

## October16: Cauldron-Born and Sunder offline candidates

Complete body/cockpit/primary-weapon assemblies, donor-proportion walking fits,
maintained-worn colors and12x material previews are prepared and delivered.
Both complete heights match MW3;449 saved joint/contact checks each pass.
These are NOT INSTALLED. Native visual retarget and weapon/damage/LOD/live checks
remain. Existing seven runtime registrations and four prior candidates retained.
[Current batch](cauldron-sunder-port-progress-2026-10-16.md). Supernova remains
the next untouched local MW5 match. Per user direction, Avatar/Firefly/Owens/
Strider keep their original MW3 models until suitable higher-polygon donors exist.
Strict acceptance remains paused131/144.

## October 15: complete Daishi arms moved up/in

The current host supports torso-frame rigid placement. Daishi R3 restores the
donor shoulder connector shapes and moves the complete arms up/in, retaining
the user-approved legs/waist and the other six model records. This supersedes
the elongated R2 shoulder fit. Training116/116, GPU1150/1150 and IA116/116 match
the retained baseline; the new Daishi2600frame case matches all original draws.
[Current placement and previews](mw5-daishi-arm-placement-2026-10-15.md).

## October 15: Daishi waist and Shadow Cat thigh corrections

Daishi now uses the second connection revision: pelvis-owned hip connectors
and torso-owned clavicles fit to original limb joints. This supersedes the
central-only Daishi correction after the user identified remaining side/shoulder
gaps. Another 2,600-frame native check matches every original draw record.
The Shadow Cat thigh correction is retained. Current paths and R2 previews are
in [the correction record](mw5-fit-corrections-2026-10-15.md).

The optional geometry now fits Daishi's existing waist connector across the
original torso/pelvis interval and keeps Shadow Cat's upper legs vertical in
the front view. Original pivots, knee endpoints, UVs and weapon placements are
retained. Both corrected player models draw natively; all 4,700 original draw
records match the prior cases. Close/distance assets are registered in the living
launcher. See [the fit correction and previews](mw5-fit-corrections-2026-10-15.md).
The r17 executable is unchanged; acceptance stays 131/144, strict lane paused.

## October 15 follow-up: damage recognition and native distance models

Current Remaster r17 fixes the full-model fallback observed when Orion loses
its right arm. Surviving MW5 parts remain, with original stump/debris rendering.
All6500original combat draw records and the standard3regressions matchr15.
All3newLOD1 variants now draw natively. Other live destruction states, converted
debris, both distance transition directions and muzzle correction remain open.
See [the follow-up](mw5-arm-damage-fix-2026-10-15.md). Acceptance131/144strictpaused.

## October 15: three additional native candidates

Orion, Daishi and Shadow Cat now render in the native r15 Remaster build and
were registered with the existing four models in r15. All original regressions match
r14; 41 offline animation clips and the actual-adapter fixture pass. Primary
materials and distance payloads are prepared. Visible muzzle alignment,
controlled damage/debris and live distance switching remain pending.
See [the new batch and validation](mw5-next-mechs-2026-10-15.md). Avatar remains
excluded; 131/144 strict acceptance stays paused. No commit.

## October 14 finishing pass (historical)

The user chose to finish Mad Cat, Vulture and Thor before starting another
chassis. Avatar/STL work remains parked. The normal Remaster launcher still
uses its validated r5 executable and existing registered models; this pass
does not publish the new candidate into that profile. No commit was requested
for this continuation.

## Candidate changes

The private `local/remaster/gpu-native-r6-lod1` host recognizes exact original
LOD1 mesh rosters as well as LOD0. It leaves original distance selection and
hysteresis in control; it does not force high detail or change gameplay.
The source LOD1 controller pivots and ancestry match the surviving LOD0
controllers. Mad Cat and Vulture omit toe controllers at LOD1, so their toe
geometry is folded into the corresponding original foot controller.

| Model | Close triangles | Distance triangles | Reduction |
| --- | ---: | ---: | ---: |
| Mad Cat | 23,084 | 14,000 | 39.4% |
| Vulture | 29,822 | 15,101 | 49.4% |
| Thor | 30,408 | 14,776 | 51.4% |

Only main body geometry is simplified. Weapon assemblies, exterior cockpit,
UVs and normals in unsimplified groups retain their original payload values.
All LOD0 vertex records are byte-identical to the approved previous payloads.
An initial seam-split decimation was rejected after previewing cracks. The
current exporter welds geometric positions while retaining corner UVs/normals,
and refuses incomplete generations before preparing runtime bindings.
These triangle reductions are not measured FPS gains.

The optional BWMESH2 stream adds a checked original visibility-node name to
each batch. Source node active flag `+0x24 & 0x4`, propagated through ancestors,
filters individual components without writing guest memory. The external
cockpit is associated with the original head marker's activity while still
being emitted under the torso controller. This avoids depending on the
transparent head marker's own tiny culling bounds. BWMESH1, including the
existing Bushwacker path, retains its prior behavior.

## Evidence and execution reached

All working assets, original analysis and rendered previews remain ignored
under `local/work-ahead/mw3-cinematic-mechs-r1/weapon-fit-review-r2` and sibling
`damage-lod-review-r2`.

- Forty-four distinct recovered clips were evaluated offline against serialized
  geometry in 49 model/clip evaluations, with
  standing/walking/running/limping/falling/getting-up previews.
  This is clip/coordinate evidence, not proof of live animation-state choices.
  The original Vulture locomotion definition selects `madcat_*` clips; archive
  clips named `vulture_*` alone do not establish its runtime selection. The
  actual five `madcat_*` locomotion bindings were also evaluated on Vulture,
  and its motion preview now uses those bindings.
- A standalone fixture includes the actual candidate adapter and roster
  headers. Its final artifact rerun passes 1,725 checks, including all six
  BWMESH2 payloads, Bushwacker BWMESH1, controller ancestry, inherited activity,
  reactivation, cache reset and fifteen malformed payload cases. It captures
  draw commands without a game or Vulkan device.
- `preserved-geometry-checks.json` verifies unchanged LOD0 vertex records and
  zero numeric differences in all unsimplified distance assemblies.
- Final-payload native Instant Action runs reached 1,900 frames with Mad Cat
  against Mad Cat, and 2,000 frames each with Vulture against Thor and Thor
  against Vulture. Logs validate and queue all three LOD0 identities. Mad Cat's
  same enemy instance additionally validates and queues LOD1, beginning at
  frame 754. Neither Vulture nor Thor selected LOD1 in these bounded runs.
  Exit 1 is the explicit frame-budget stop, not normal mission completion.
- Combat exposed a missing original MSVCRT `memmove` continuation. An original
  model baseline reproduced the same frame-1,301 fault, independently of the
  replacements. Four original short-copy continuations were translated and
  added to the private host. The same frozen input then reaches 1,750 frames;
  all 1,301 original draw records before the previous stop remain identical.
  The subsequent three model runs above use this corrected host. The bounded
  closure scanner fix and four asset-free table tests are authored source;
  generated bodies, DLL evidence and executable remain local.
- The test harness refuses to launch while a normal game is running. It uses
  a copied install/pilot and private registry; actual registry and pilot files
  are only hashed and are never written. Native target dumps and Blender
  renders provide previews; no desktop screenshots are taken.
- Fresh standard regression attempts stayed in the menu with foreground
  acquisition failure; a Windows system dialog held focus. An unchanged r5
  control did the same. Matching menu captures are excluded from gameplay
  validation. Training 116/116, GPU draw 1150/1150 and IA 116/116 remain pending
  on this candidate; the earlier r5 evidence is retained separately.

## Open boundaries

The original weapon-origin producer `0x4b36e0` feeds collision, continuous-beam
damage and random-number decisions. It must not be changed to fix presentation.
Several source firing points differ materially from MW5 barrel openings.
The recovered route for a future correction tracks exact beam/FIRE effect
instances and adjusts only host drawing geometry before projection/clipping,
keeping the original hit endpoint. That route is documented locally in
`weapon-presentation-contract.md`; no completed muzzle fix is claimed.

Actual combat limb loss, debris, head damage, both distance-transition
directions, Vulture/Thor LOD1 selection, clipping and final per-chassis performance remain unobserved for
this revision. Same-name/same-count geometry swaps are not recognized;
subtree removal conservatively restores original rendering. Static base-color
sidecars do not select original damage skins. The semantic cockpit/head-marker
association and same-scene visibility snapshot need live validation. Normal
maps remain available offline but are not consumed by this native base-color
path.

Next: verify the remaining distance paths and actual damage events for every
chassis after normal play has closed, then
implement and validate the scoped visual-effect origin correction. Promote
the candidate into the living launcher only after those checks. Strict
acceptance remains paused at **131/144**; this work adds no accepted credit.

## 2026-10-19 — Model joints and reference-corrected Mad Cat

[Joint-fit record](mech-joint-fit-2026-10-19.md): reproduced Mad Cat/Vulture
elbow fitting and detached inner Bushwacker toes. Vulture retains donor upper/
lower arm spacing; inner toes now use the existing fitted foot hinges. The
user's subsequent Mad Cat art reference exposed low/inward original shoulder
anchors: final Mad Cat restores donor-relative shoulders beneath missile pods
and keeps separate torso/upper-arm corrections through optional BWMESH5.
Both source distances and Bushwacker primary/Freya geometry are registered.
No added pieces, artwork changes or gameplay firing-point edits.

Fresh current-source host be9bc313… is published at
local/remaster/gpu-native-joint-attachments-r1 with an actual matching snapshot;
the prior42672b40/2926029b source-record mismatch is preserved as history, not
relabeled. Main launcher supports the existing AA-off/fullscreen settings,
passes normal/original-model checks and asset preparation. Current settings,
39banks/32sidecars, other chassis and original pilot/registry hashes preserved.
1496changed-adapter checks and10,370,925legacy checks pass. Mad Cat1542offline
pose/LOD cases checked; retained original collapser/getup hand translations
are distinct from fitting residual. Vulture349poses, Bushwacker59samples.
Fresh be9bc313 stock comparisons pass: Training 116/116, GPU draw stream
1150/1150, IA 116/116. Separate native IA runs reach 1400 Vulkan presentations
with each corrected chassis: Mad Cat/Vulture LOD0, Bushwacker LOD0 and LOD1.
Positive instance-validation and queued GPU records establish actual use;
original F2 exterior views were inspected. Small joint contacts remain partly
outside the rear-view framing, so offline front/side poses provide detailed
fit evidence. One menu-only attempt is excluded; budget exit 1 is intentional.
No game ran concurrently with another native session; singleton refusals were
respected. Extended combat/damage/effect alignment, full LOD transitions,
Freya replay on this host and performance remain open. Protected originals
and artwork hashes remain unchanged. Strict 131/144 paused; no commit.
[Final Mad Cat previews](https://drive.google.com/drive/folders/1XHakISSeDm96ejNObO9AI4YihuqtxVGc).


## 2026-10-19 — Mad Cat torso-follow correction R3

User review supersedes the preceding Mad Cat R2 shoulder claim: walking lowers
the torso but the source arm joints compensate upward by about2.0888 units.
The previous fitting test retained that travel and missed the visual detachment.
Optional BWMESH6 now fixes the replacement shoulder in torso space and gives
the same live translation correction to each complete upper/lower arm and its
weapons. Original rotations, aiming, hand motion and guest simulation remain;
no geometry or artwork added/changed. Both distances updated; other chassis,
settings,39banks/32sidecars and original registry/pilot/artwork hashes preserved.

Main launcher selects source-matched native host546c5616 at
local/remaster/gpu-native-madcat-torso-follow-r1. All15recovered MadCat clips at
both distances pass1542attachment cases (max residual0.00000107, formerly2.088815).
Actual adapter15183/0 and legacy10370925/0 checks pass. Fresh exact-host stock
Training116/116 GPU1150/1150 IA116/116 match. Native IA1400 Vulkan presentations
validates/queues MadCat LOD0 complete arms; F2 exterior target inspected.
Small joint contacts partly leave the rear-view frame; detailed fit evidence
uses matched Blender standing/walking poses. Intentional budget exit1, not
mission completion or measured FPS. Live LOD1, extended combat/damage, effect
origins, clipping extremes and performance remain open. Strict131/144paused.
No commit, desktop screenshots or writes to original registry/pilot files.

[Detailed R3 record](mech-joint-fit-2026-10-19.md#r3-arms-follow-the-lowered-torso).
[R3 before/after walking previews](https://drive.google.com/drive/folders/1lx6N77iOrW6J8jxDH0jVNeKH9J1Z5rSM).
Private receipts: C:/Users/jcbla/.codex/workspace-storage/MW34Recomp/joints-20261019-r1/torso-follow-r3/.


## 2026-10-19 — Mad Cat / Vulture live arm attachment R4

[R4 live-joint repair](mech-live-attachments-2026-10-19.md) supersedes the previous
Mad Cat R3/Vulture R1 attachment claims. Actual gameplay forearm translations
differ from the saved stand reference, causing measured1.147158/1.797140-unit
elbow gaps. Existing BWMESH6 data now anchors both shoulder and elbow, preserving
source rotations; existing clavicle triangles follow torso. No added geometry,
artwork edits or guest pose/simulation writes. Both distances and both main/
material-preview registries updated; all other chassis/settings preserved.

Native base-color walk/aim/stop2500presentations per chassis and separate lit/
normal front/side2500per chassis verify live corrected geometry; max elbow
residual below0.00006476.3084clip/LOD checks,318captured-pose/LOD replays and
actual adapter154247/0 checks pass. Main host546c5616 unchanged. Material Preview
gets source-matched V5/V6 hosta85f211d; fresh stockTraining116/116 GPU1150/1150
IA116/116 match. Versioned matching albedo/normal packs,39banks and15models in
each profile. Original-model/main/material launcher checks pass. Future model
promotions must keep both geometry registries compatible with their hosts.
Live LOD transitions, damaged/stump states, effect origins, clipping extremes
and final performance remain open. Strict131/144paused; no commit or desktop
screenshots, original registry/pilot writes, or release of the trailer hold.
[Native game previews](https://drive.google.com/drive/folders/1Qx34jJGwLTQiAHC92EjCaLdEmQQ8CQEm).
Private receipts: C:/Users/jcbla/.codex/workspace-storage/MW34Recomp/joints-runtime-20261019-r4/.


## 2026-10-19 - Original Avatar geometry upgrade R1

[Avatar geometry candidate](avatar-geometry-detail-2026-10-19.md): upgraded the
original558-triangle model to17318triangles across the same19moving parts.
Added source-aligned armor layers/bevels,15vent regions,22missile collars,
six muzzle collars and cockpit framing. Existing color/normal images retained;
12x reference preserved. No parked STL, new joint or changed limb transform.
All336controller poses match exactly;336matched walking render pairs, four
gray comparison views and46packed image hashes pass. Nine Drive review files
are verified; local packed scene/HTML and source receipts retained.
Offline geometry boundary only, not installed in either launcher. Native LOD,
weapon/damage/joint/performance validation remains. The15installed replacements
and MadCat/Vulture R4 are unchanged. Owens/Firefly geometry remains next.
No game, desktop screenshot, original pilot/registry write or commit.
Strict131/144paused; no new native credit.


## 2026-10-19 - Avatar STL-guided geometry R2 (offline)

After R1 review, the user requested a stronger upgrade using the supplied STL.
[R2 geometry revision](avatar-stl-guided-geometry-r2-2026-10-19.md) has36,038triangles
vs R1's17,318, retaining19original MW3 controller parts. It adds81deeper chamfered
shells, stepped shoulder/hip/knee/ankle and toe covers, plus a newly extracted
6,580-triangle STL cockpit/nose. The old mis-fitted STL rig is not reused.
Original control transforms/action curves and all336checked poses remain exact;
46packed source color/normal files retain bytes and12xbody response. Nose mapping
and clean new covers have provisional materials. Gray and color R1/R2 reviews,
336matched walking render pairs and video checks pass;10Drive files verified.
Native payload/LOD and weapon/damage/live-joint/performance work remain; NOT
INSTALLED. Two separate launcher changes observed during authoring are preserved
without restoration; source model registries and original registry remained
unchanged at inspection. No game, desktop screenshots, original pilot/registry
write or commit. Strict131/144paused; zero new native credit.


## 2026-10-19 - Avatar R3 hip covers seated (offline)

Corrected the detached R2 outer hip covers: moved only the existing covers/bolts
inward onto the actual narrow upper-thigh surface, with 0.03-unit backing overlap.
No new connector, joint or leg movement. Exactly 1,008 cover vertices change on
X only; 36,038 triangles, 19 parts and 46 packed source images remain. Seventeen
mounting samples per side and 336 unchanged controller poses pass. Three boards
and 112 matched walking frames reviewed; five Drive preview/notes files verified.
[R3 detail and review links](avatar-stl-guided-geometry-r2-2026-10-19.md#2026-10-19---r3-hip-cover-seating-correction-offline).
Local: `local/work-ahead/mw3-avatar-hip-fit-r3/comparison.html`. NOT INSTALLED;
native LOD/combat/live-joint/performance checks remain. R2 and live assets retained.
No game, desktop screenshots, original registry/pilot write or commit.
Strict 131/144 paused; no new native credit.


## 2026-10-19 - Avatar R4 textured and installed

[Textured Avatar integration](avatar-native-integration-2026-10-19.md) is now in
both living launcher profiles:16replacement chassis total. Preserved R3 hips,
19original moving parts and36,038triangles. Retained25body color tiles pixel
for pixel; new surfaces have separate worn paint/metal/soot textures.45material
slots,43normal bindings, smooth glazing exceptions and the selected12x reference.
Both source distances and four arm-loss alternatives registered; far geometry
currently retains full detail. Merged the independently updated lighting host
8fce991d before publishing the Avatar hosta0cefef7, preserving prior15registrations.
Latest-host Training116/116, GPUdraw1150/1150 and IA116/116 match; adapter3850/0;
native player2500frames with movement/firing and normals; both launchers prepare
all16 and original-model option passes. Six Drive previews/notes verified.
NPC LOD transitions/full destruction/muzzle/extended play/FPS remain open.
No desktop screenshots, original registry/pilot writes or commit. Strict131/144
paused; no accepted-function credit. Remaining original geometry work:Firefly/Owens.


## 2026-10-19 - Owens ZIP-inspired geometry prototype R1

The supplied Downloads Owens Omnimech5955019 ZIP contains editable Blender,
STL and render references credited to UnrestedGuy. Used as visual inspiration
for [new authored geometry on the MW3 Owens](owens-zip-geometry-prototype-2026-10-19.md),
without importing its rig, meshes or print base.774to21,170triangles,16same moving
parts;82faceted shells,10source missile openings,4vents, cockpit/bearing/optics,
8toe hinges and2solid antenna whips on the source centerlines. Existing colors
and12x normal reference retained; new mechanical materials remain provisional.
All336source controller poses match exactly;88mounting samples inside original
part armor,42packed source-image hashes,168matched walking render pairs and
4uniform-gray views pass. Seven Drive previews/notes names/MIME/parents/bytes
verified. Local packed scene/HTML:local/work-ahead/mw3-owens-detail-r1/.
Offline/not installed. Native mesh/LOD/material export and weapon/damage/live
checks remain. Current16model launchers and original registry retain their
initial hashes. No game, desktop screenshots, original pilot/registry write
or commit. Strict131/144paused; no new native acceptance credit.


## 2026-10-19 - Firefly Firebug-inspired geometry prototype R1

Inspected both supplied Firebug ZIPs: two PunyKaiju-named posed STLs and separate
bases, no license/README in the supplied archives. Used as visual inspiration for
[authored MW3 Firefly geometry](firefly-firebug-geometry-prototype-2026-10-19.md),
without importing reference triangles, bases or STL poses. 622 to23,688triangles,
21same moving parts/35same controller-frame objects. Added103armor panels,
cockpit contour frame, circular housings, four grilles/30louvers, four leg rails,
seated bearings,14source-layout missile wells and10toe hinges on8toe controls.
An initial hinge crossing the paired front toe gap failed the mounting check;
separate embedded hinges now follow each prong under the original control.
Original source geometry/UV/actions retained;336control poses exact,82mounting
samples and48packed image identities pass. Existing worn colors/12xreference
retained; new hardware finishes remain provisional.168matched walking render
pairs plus4normal-off gray views;7Drive previews/notes metadata/bytes verified.
Local packed scene/HTML:local/work-ahead/mw3-firefly-detail-r1/.
Offline/not installed; native mesh/LOD/material export, weapon/damage and live
performance remain. Current16model launcher/registry hashes unchanged. No game,
desktop screenshots, original pilot/registry write or commit. Strict131/144paused.


## 2026-10-20 — Default mech texture pass

Audited all18default sets; revised Daishi, ShadowCat, Avatar, Strider, Owens
and Firefly, retaining twelve already detailed/worn sets. Reconstructed crisp
panel/metal wear with calmer broad armor, original palettes/markings. Both
model registries and original banks installed;34color sidecars/profile checked
against every source pixel and batch index. Existing2main/32normal sidecars
unchanged;149selected bank entries changed,5497others exact.46newcolor keys
preserve existing native normal tuples; six stale Campaign1 manifest paths
aligned with already active object banks. Host/graphics/mesh/skinfields retained.
User explicitly kept main fullscreen_windowed despite its existing capability
mismatch; normalpreview preparation passes, main preparation verified directly.
No game/desktopcapture/pilotregistrywrite/commit;131/144strictpaused.
Owens/Firefly detailedgeometry remains offline. Beforeafterreviews/notes on
Drive; see [texture pass](default-mech-texture-pass-2026-10-20.md) for sources,
resolution limits, validation and remaining native visual checks.


## 2026-10-20 — All 18 models in the main Remaster

Integrated detailed Owens and Firefly into the current main HUD damage-colour/
lighting/window host. Main and GUI now resolve18chassis with the current default
textures and normal registry. Host ba86eac90b based on85a9a59eef; only exact new
rosters/table entries/arm-loss metadata differ, translated objects unchanged.
Owens21,170tri/16parts/42materials; Firefly23,688tri/21parts/53materials,
336bindings below0.000002matrixerror, source body UVs retained and56latestcolor
files byte-identical. Both distances currently retain full geometry. Adapter
7782checks/0failures; original Training116/116, GPU1150/1150, IA116/116 match.
NativeIA2000frames each with geometry/normals loaded. Main/GUI/normal preparation
passes18models,38color/36normal sidecars; original-model option retained. All
previous16records, graphics and runtimeenv preserved. GUI pack description now18.
No original registry/pilot writes or commit; strict131/144paused. NPCdistance,
damage/debris, precise muzzles, extended campaign/FPS remain. See
[all18 integration](all18-mechs-main-integration-2026-10-20.md).
