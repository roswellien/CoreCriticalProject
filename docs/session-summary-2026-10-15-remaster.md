# October 15 development summary — rolling notes

These notes are retained for tonight's development summary. User play reports
and automated checks are labeled separately; this is not a final daily release
or a change to strict acceptance.

## User-confirmed campaign milestone

The user reports successfully **completing the first campaign mission** after
the r8 decoder fix. This extends the earlier automated evidence, which covered
only mission entry and 1,800 presented frames. The current Remaster profile is
3440x1440, FXAA and 16x AF, with current registered models/textures and music.
No independent replay, full-campaign, or save/load equivalence is inferred from
the completion report. See [the decoder fix](campaign-video-startup-fix.md).

## Issues reported during play

At 3440x1440 ultrawide, the user reports:

1. Player status panel, bottom right: translucent green background extends
   past its rectangular frame.
2. Target status panel, bottom left: the same background/frame mismatch.
3. Small radar: red/yellow lines appear misaligned. The user has not compared
   these with the original; baseline behavior needs checking.
4. Zoom reticle: does not correctly follow the aiming cross away from center.
5. Enemy status: expected increasing red damage tint, separately by mech part,
   does not update as in the original.
6. Weapon list, top right: its containing box is much wider than its text.
7. Intermission Mech Lab: layout is substantially broken in widescreen.

Other resolutions have not been user-tested for these reports. The requested
Mech Lab scope is **investigate the root cause and discuss the fix before
implementation**. HUD and Mech Lab investigation is in progress; no fix is
claimed by this initial issue record. Installed pilots/registry are protected;
no desktop screenshots or commit. Strict acceptance remains **131/144, paused**.

## HUD follow-up

The [HUD and Mech Lab investigation](hud-mechlab-investigation-2026-10-15.md)
records the root causes and validation. The published r9 HUD build fixes the shared
deferred-anchor defect behind the two overflowing status backgrounds and the
oversized weapons box. It restores original MW3 condition schematics in the
HUD while keeping replacement models in the world. Controlled per-part damage
progression remains to be checked. Training 116/116, mode-7 draw stream
1150/1150 and IA 116/116 match r8; enhanced captures cover 1920x1440 and
3440x1440. Radar and zoom observations remain open, with no speculative changes.

Mech Lab investigation identifies mismatched 2D/3D frontend composition paths.
The proposed first step is one centered original-aspect canvas. Implementation
is intentionally pending discussion, as requested; a genuine accessible Lab
state is still needed for runtime reproduction. This is a rolling record, not a
claim that every reported HUD/Lab issue is resolved.

The user clarified that the Lab issue occurs directly after Mission1 completion,
and that the zoom's small inner cross is the drifting element. A follow-up
traced the real Win/Continue/loader/Lab route; the initial reloaded1/1 map
intentionally disables Lab and was not the same case. Three fresh private zoom
diagnostic runs cover both screen edges, cockpit and native4:3. The fully open
cross stays centered with a constant raster offset; original opening/closing
transients are observed, while persistent drift is still unreproduced. Timing
clarification remains pending. No further production changes or Lab repair were
made; the normal Remaster launcher stays on r9.

The later locked-window/cockpit clarification exposed a different issue: the
magnified scene was scaled about the full screen center while its frame followed
the movable zoom camera. r12 now captures the original zoom camera's center
before deferred submission and uses it consistently for scene geometry and
clipping. Original input, zoom FOV and gameplay remain unchanged. Matched locked
sweeps cover both views and off-center movement;1920x1440 captures remain
unchanged. A1500-frame real-clock cockpit run also passes. All three original
regressions remain identical: Training116/116, GPU1150/1150 and IA116/116.
The normal Remaster launcher now selects the validated r12 build; r9 is preserved.
The detailed investigation includes source pins and Drive comparisons. Mech Lab,
controlled damage progression and original-radar comparison remain open. Strict
acceptance stays131/144 and paused; no commit was made.

The later intermittent target-triangle report exposed a second zoom display
mismatch. The original marker-hiding logic used a wider footprint than the
displayed zoom window, and zoom-projected triangles retained the normal-camera
display policy. r14 corrects the occlusion comparison and captures the original
camera choice for the three triangle lines. The reproduced false hide beside
the window is fixed; intended overlap hiding and per-edge clipping remain.
Training116/116, GPU1150/1150 and IA116/116 still match r12;14 sampled4:3
captures are identical. The normal launcher now selects r14. The Vulkan
validation layer was unavailable, so only the normal-renderer checks are claimed.
The detailed HUD investigation retains the source pins, failed attempts, limits
and Drive comparison. No new campaign/acceptance credit or Mech Lab change.

## MW5 porting: Orion, Daishi and Shadow Cat

The next batch now renders as three additional native runtime candidates in
published r15. Existing four models, r14 target/zoom/HUD changes, r8 codec and
r7 speed improvements remain intact; Avatar remains parked. Source donor
loadouts were corrected to match MW3, and the fitted Orion waist gap was
repaired using existing pelvis geometry. MW3-inspired material drafts include
normal maps for later renderer use; the current adapter remains base-color only.

Training116/116, original GPUdraw1150/1150 and IA116/116 match r14. All41 recovered
clips pass offline; actual adapter fixture3159checks pass. Native player-model
cases reach Orion2000, ShadowCat2100 and Daishi2600frames at3440x1440 FXAA/AF16,
with exact LOD0 identities and GPU replacement draws. Distance models save
43–52% of triangles; actual native distance switching, muzzle alignment and
controlled damage/debris checks remain next. No FPS gain or campaign completion
claim. Both distance texture sets now refresh from current PNGs at launch.

[Full batch record, tests and Drive previews](mw5-next-mechs-2026-10-15.md).
Protected originals unchanged; no screenshots/commit;131/144strictpaused.

## Ported-model combat and distance follow-up

Current Remaster now selects r17. A real6500frame Orion-versus-Daishi battle
exposed whole-model fallback after the original right-arm loss atframe4414.
Source-recovered stump replacement variants now retain surviving ported body
parts while leaving original stump/debris draws intact. The same6500original
combat draw records match; Training116/116, GPU1150/1150 and IA116/116 matchr15.
Fixture3454checks covers13model/LODpayloads and39synthetic armstates, including
exact stump geometry/ancestry and malformed data rejection. Other live limb
losses remain untested. Daishi/Orion/ShadowCatLOD1 all drew in separate native
sweeps; both distance transition directions remain unproved.

The private r16observer links8actual Orionbeam draws to its right-hand weapon
and original firepoint02. It revealed a material distinction between ordinary
beam endpoint fields and the alternate segment layout. No muzzle warp is
published. Native normals, converted debris and leg/torso damage remain open.
[Full record and before/after Drive previews](mw5-arm-damage-fix-2026-10-15.md).
No user-save/registry edit, screenshots, commit or new acceptance;131/144paused.


## Daishi waist/shoulder and Shadow Cat thigh corrections

Shadow Cat upper thighs now stand vertically in front view; the fit retains
original animation pivots and knee endpoints. Daishi first received a central
waist-collar correction, then a second revision after the user found side-hip
and shoulder gaps. Current R2 correctly assigns the existing hip connectors to
the pelvis and clavicles to the torso and fits them to original limb joints.
No new joint/filler mesh, weapon/cockpit change, or gameplay change.

Both close/distance levels are registered in the living launcher. All 27 clips
pass at both detail levels; R2 Daishi also passes all 13 clips and 3454 adapter
checks. Initial native Daishi2600/ShadowCat2100 cases match all4700original draw
records; R2 Daishi adds a further2600 matching frames. These are bounded cases,
not complete damage or LOD-transition acceptance. User registry/pilot unchanged.
Current native r17 executable retained. Original hip local translations leave
a measured <=0.0023812 model-unit connector-center deviation across563samples.

Private Drive has source/before/after comparisons and original-MW3 walk GIFs.
Current Daishi: https://drive.google.com/drive/folders/1R9Nk5qFlvxZ3ncd9QVnrNilQDvzzf4sx
Shadow Cat: https://drive.google.com/drive/folders/1AC-hNsJlTxrB4vfbb2CgJDKMmgU73ptr
Details: [fit correction](mw5-fit-corrections-2026-10-15.md). No screenshots or
commit. Accepted131/144, strict lane remains paused.


## Daishi R3: complete arms raised and tucked inward

The user accepted the legs/waist and rejected R2 stretched shoulder connectors.
R3 restores donor shoulder shapes and moves entire arms up/in, retaining the
accepted legs/waist and arm/weapon mesh shapes (38/39groups exact). Rigid
placement follows each actor current torso frame; compiled GPU/CPU paths agree.

The new host is based on the latest scenery-distance build, preserving current
3440x1440 FXAA AF16,1600configured drawdistance,39banks,7models,HUD/music. Only
mesh adapter source changes; original translated object list unchanged. Actual
Training116/116,GPU1150/1150,IA116/116 and Daishi2600originaldraws match baseline.
Fixture3880checks passes,13clips bothLODs pass,57savedwalk samples match runtime
placement. Earlier CPU smoke disabled dumps; separate frame rerun supplies116.

Living launcher and both Daishi detail levels updated; old formats supported
and incompatible old hosts rejected. Other6models and userfiles unchanged.
[Detailed record and Drive previews](mw5-daishi-arm-placement-2026-10-15.md).
R2shoulderpreview rejected; preserve its evidence. Strict131/144paused; no
screenshots or commit. Muzzle presentation/full damage/LOD transitions open.


## Bushwacker worn-color prototype R7

Created a separate five-map prototype with chipped paint, metal gouges, scorch,
dirty seams and readable gunmetal machinery. Retains MW3-inspired camouflage,
approved shark-mouth shapes and exact geometry/UV0/pose. Built-in image_gen art
and Blender bake; matched diffuse and unlit comparisons demonstrate color-only
detail without normals or specular. Live textures, model registry and launcher
hashes unchanged. No game launched or performance claim; seam/mip and game review
remain before publication. Organized Drive comparisons/maps/ZIP uploaded and all
13files read back verified. [Detailed record](bushwacker-worn-texture-prototype-2026-10-15.md).
No desktop screenshots, pilot/registry edits or commit. Strict131/144paused.


## Bushwacker walking normal-map and moving-light preview

Created an offline Blender Eevee demonstration using the R7 worn colors and
retained donor normal detail. Existing repaired walk repeated6times, one light
orbit,11.2seconds at1280x96030fps.336frames and duration verified; same geometry,
UVs, basecolors and live registration. Original/repeated sampled pose matrix
error0. Same-light normal toggle and four-light-state sheet included. Seven
Drive uploads read back verified; packed Blender scene stays local. No game
renderer integration, FPS claim, new scar relief or physics. No game launch,
desktop screenshots, pilot/registry edits or commit.131/144strictpaused.
[Detailed record](bushwacker-normal-light-walk-preview-2026-10-15.md).


## Bushwacker preview R2: straight upper legs during the walk

Corrected the preview thigh side tilt/twist with sagittal rotation and a rigid
knee solve preserving hip/ankle positions, leg lengths and foot/toe world poses.
Only6bone curve sets changed. Non-leg bones and weapon/glass objects exact;
mesh/UVs, R7 textures, normals and light setup unchanged. Initial once-per-frame
bake failed subframe foot drift; eighth-frame bake449samples passes,897denser
checks show max foot/toe matrix difference.00314 and upper side angle.00652deg.
Rerendered11.2s1280x96030fps336frame video and mobile GIF, plus frontal comparison.
Five Drive files read back verified. Original motion and live assets unchanged.
[Detailed record](bushwacker-thigh-preview-correction-2026-10-15.md).
No game launch, desktop screenshots, pilot/registry edits or commit;131/144paused.


## Original MW3 Bushwacker normal-map walking/light experiment

Ran the same offline test on the original21mesh/314polygon/635triangle model
with current upgraded MW3 texture tiles. Source geometry and UV bindings verified;
24material bindings share17new authored height/normal pairs. Built-in image_gen
height artwork, technical OpenGL normal conversion, shader strength.85. Unchanged
color maps, original sampled MW3 walk directly, same camera/light/fill/world.
672frames rendered in normal-on/off passes;11.2s30fps videos and labeled A/B,
mobile GIF, textured and neutral-color comparisons, and map ZIP completed.
All geometry/source/media checks pass;11Drive uploads read back verified in
organized preview/map folders. No game assets/settings installed or game launched,
no desktop screenshot, pilot/registry edits or commit; strict131/144paused.
[Detailed record](mw3-bushwacker-normal-preview-2026-10-15.md).


## MW5 Bushwacker normal-map strength R3

Compared current.85,2x1.70 and4x3.40 on armor/weapon materials, glass unchanged.
Same corrected R2 walk and R7 colors/maps/geometry/materials/lights. Scene
signature excluding only target strength stays identical; baseline frame15
pixel-identical to reused R2 render. Two336frame passes completed; three videos
verified11.2s30fps, full views1280x960, three-way1920x540. Includes4xmobileGIF,
colored/neutral/close still comparisons and packed local2x/4x scenes.10Drive
uploads read back verified. This is offline material response only, no new
scar relief/displacement, game integration or bulk changes to other models.
[Detailed record](mw5-normal-strength-preview-2026-10-15.md).
No game run, desktop screenshot, pilot/registry edit or commit;131/144paused.


## MW5 Bushwacker 8x / 12x normal strength R4

User requested 8x and 12x normal strength. Body/Variant/Weapons use 6.80/10.20
relative to original 0.85; previous 4x = 3.40. Window remains 0.30. Same corrected
R2 walk, R7 worn colors, existing donor normals, geometry, UVs, camera and lights.
Source pins and scene signature excluding target Strength sockets unchanged.
Fresh 4x frame 15 is pixel-identical to R3. No new painted-scar relief authored.

Workspace: D:/Projects/MW34Recomp/local/work-ahead/mw5-bushwacker-extract/normal-light-walk-r4-strength-high
Packed 8x/12x scenes retained. Two new 336-frame, 11.2s, 30fps, 1280x960 walks;
1920x540 three-way comparison, 12x GIF, colored/neutral stills, closeup, HTML.
Media/source checks pass. Ten uploads verified by metadata readback.
At 12x broad armor panels begin looking rippled and seams exaggerated. This is
shading amplitude, not physical displacement or new geometry.

The user game was running. Only the Blender worker used BelowNormal priority
(verified 0x4000), two CPU threads and 0.08s yields. User game/composer untouched.
Offline Blender only; live game still lacks normal support. No game launched,
desktop screenshot, pilot/registry edit or commit. Accepted 131/144; strict paused.

Folder: https://drive.google.com/drive/folders/1cH42ScTE9Xx6S4NR7z54eZkdkLMgBm84
Compare: https://drive.google.com/file/d/1WdkKJEkCeU-GkUtgaYEm-MN11zveF7-J/view?usp=drivesdk
8x: https://drive.google.com/file/d/1Kvu1MovvVPB94D87MioULZB6i_9yE5gv/view?usp=drivesdk
12x: https://drive.google.com/file/d/1eoSfJUR1e8pCPDHdkwMQTOqp-CmXc3k3/view?usp=drivesdk
Details: docs/mw5-normal-strength-high-preview-2026-10-15.md


## Future in-game MW5 normals: user selected 12x equivalent

On 2026-10-15 the user selected the R4 12x appearance for future in-game MW5 replacement-model normal mapping. Reference Body/Variant/Weapons Strength 10.20 = 12 x original 0.85; Window 0.30. Match the visual response in the native shader rather than copying an unexplained numeric 12. Keep per-material/chassis calibration, separate original-MW3 tuning, and an independent off setting. Lighting/material foundation, verified tangents/UV handedness, normal textures, visual regression and measured performance remain required. No runtime/profile/assets changed and no execution/acceptance advance. See docs/mw5-normal-strength-high-preview-2026-10-15.md, approved-target section.


## Mad Cat maintained and well-used texture prototype

User requested the Bushwacker wear ideas on Mad Cat: maintained but well used.
Created isolated Body/Variant/Weapons base-color atlases with built-in image_gen,
retaining muted MW3 sage/gray/olive paint, adding edge chips, thin steel-exposing
scrapes, dirty seams, modest soot and serviced mechanical color detail. Existing
normal atlas was used only as layout guide; no normal/roughness/metallic changes.
Three generated main maps are 1254 square; source was 2048. Window/MissileHead
remain byte-identical 64-square PNGs. New scars have no authored normal relief.

Workspace: D:/Projects/MW34Recomp/local/work-ahead/mw3-cinematic-mechs-r1/madcat-worn-textures-r1
Contains five-map ZIP, packed .blend, matched front/opposite/rear/unlit pairs,
five comparison JPGs, self-contained HTML, exact prompts and source manifest.
Uses runtime-integration-r1/madcat/madcat-fitted-walk.blend (38 fitted parts).
Geometry/UV/pose unchanged: aa46bd18a1700f351adb3c0d8872e533f3c4b2450ad1cdddda1ea1e9dca558ec.
Pinned source images, scene, native source payloads, registry/profile hashes
unchanged after render/packaging. Both sides/rear/unlit inspected. Sixteen Drive
uploads verified by metadata readback; folders under Textures / Mad Cat.

Folder: https://drive.google.com/drive/folders/1qmixvZwjNdplg7P6QX807oN6gbmvwdFY
Compare: https://drive.google.com/file/d/1--QRJGSEw0EoJ-I8NppUxQf2MiWDjeQe/view
ZIP: https://drive.google.com/file/d/1jxtyS1TC0VmSVYXAyVcJC3Hfs2GJiCSY/view

Offline color prototype only; live assets/registration unchanged. Review seams,
mips and game appearance before publication. No game launched, screenshot,
pilot/registry edit or commit. No execution/performance/acceptance advance;
131/144 strict paused. Details docs/madcat-worn-texture-prototype-2026-10-15.md.
Future MW5 native normal target remains the approved 12x-equivalent reference.


## Worn Bushwacker and Mad Cat sets installed for Play MW3Remaster

User explicitly requested installing the new Bushwacker and Mad Cat color sets.
Changed only the five texture paths per model in local/remaster/models.json:
Bushwacker -> mw5-bushwacker-extract/mw3-material-r7-worn-prototype/textures;
Mad Cat -> mw3-cinematic-mechs-r1/madcat-worn-textures-r1/textures.
Both under local/work-ahead. Regular Play MW3Remaster.cmd rereads/repackages
these on every launch. Other model fields, registrations and mesh files unchanged.
Avatar remains excluded. No engine rebuild or launcher code change needed.

Ran actual root launcher --prepare-only to exit 0, without starting the game.
Independently parsed actual staged RGB565 BWTEX1 files and verified every pixel,
material, dimension, hash and batch mapping: Bushwacker 32 batches / 14,695,440
bytes; Mad Cat 38 batches / 9,451,888 bytes. Existing 2048 cap applies to Bushwacker
4096 Body source; other main maps 1254. Eight unrelated sidecars unchanged.
39 banks / seven models; native build/profile/old and new color source hashes
unchanged. Current build gpu-native-fog-stock-r1, sha866d6c7ce7e4aa566f9c06fa2b44afaaeb421591f58a44946830476121aba908.
3440x1440 FXAA AF16 / 800 scenery unchanged. No normal mapping enabled.

Rollback registry and prior target sidecars: local/work-ahead/worn-texture-launcher-install-r1/before/
Publication/verification JSON in that workspace. Earlier offline prototype
manifests remain historical; their registry hash predates this publication.
Details docs/worn-mech-textures-launcher-install-2026-10-15.md.
No in-game visual/performance claim or game launch, desktop screenshot,
MW3/mw34-registry.txt/pilot edit or commit. Accepted 131/144; strict paused.


## Orion, Thor and Vulture maintained/well-used colors installed

User requested updating these skins to the new maintained-but-well-used standard.
Six Body/Variant color atlases edited with built-in image_gen; muted MW3 palettes
retained. Chips, thin steel-exposing scrapes, dirty seams, restrained soot/service
wear. Shared Mad Cat gunmetal Weapons atlas reused only after all donor Weapons
normal hashes matched exactly (1a85f78797f2bd4d646093d471c7160c5b1c12b3afe0792794d685332e95f611).
Body/Variant/Weapons1254 square; exact Window/MissileHead64-square PNGs retained.
No normal/roughness/metallic edits; new scars have no authored normal relief.

Workspace D:/Projects/MW34Recomp/local/work-ahead/orion-thor-vulture-worn-r1
has per-chassis generated art, five-map ZIPs, packed .blend scenes, matched
front/opposite/rear/unlit views, global self-contained HTML, overview, exact
prompts and pinned source identities. Geometry/UV/pose preserved for Orion32,
Thor21 and Vulture32 fitted parts. No source scene/payload modifications.

Installed all three by changing only their texture paths in local/remaster/models.json.
Actual root Play MW3Remaster.cmd --prepare-only exited0. Every material pixel,
header hash, dimension, batch index/count and file boundary verified in four
actual staged BWTEX1 files, including Orion LOD1. Vulture32b9451864bytes,
Thor21b9451820, OrionLOD0 32b9451864, OrionLOD1 22b9451824. Six unrelated staged
files (including installed BushwackerR7/MadCatR1), other model records, geometry,
current build/profile and source PNG identities unchanged. Seven models/39banks,
Avatar excluded. Rollback registry and prior targets in publication/before/.

Drive root: https://drive.google.com/drive/folders/1JHLP161TwOdbraA9DIs1wM_CyPalZk0B
Orion compare: https://drive.google.com/file/d/1IZZpXUsO-HdrE8fF2U92N_fWx0iwE6HM/view
Thor compare: https://drive.google.com/file/d/1Fgt5ga5ks84dt5xZPr6hDbC7c7nTxelL/view
Vulture compare: https://drive.google.com/file/d/1CKG6ybQDb-e_wQt6FfC-4nrRs6FXJO53/view
25uploads and9childfolders metadata verified. Organized by chassis with Previews
and Texture set folders. No sharing changes or email.

No game launched, screenshots, MW3/mw34-registry.txt/pilot edits or commit.
Asset preparation/offline art only; native execution/performance/seam-mip-game
acceptance not claimed.131/144strictpaused. Other builders/composer untouched.
Details docs/orion-thor-vulture-worn-textures-2026-10-15.md. Normal mapping and
future approved12x-equivalent response remain separate renderer work.


## Bushwacker waist gap corrected and installed

User confirmed gap both standing and moving. Native baseline had0.139269unit
separation: independent rigid pivot fitting left donor pelvis connector short
across MW3's larger hip-to-torso interval. Refit existing upper pelvis with a
clamped displacement ramp; no filler, source pivots or extra geometry. Only
batch0 changes4025corners; other31groups, UVs, lower pelvis, weapons unchanged.
14clips/607samples checked,294stand/locomotion samples and13synthetic turns retain
surface contact. Actual current-host adapter fixture3880checks/0failures.
Matched offline before/after views and original MW3 walk MP4/GIF reviewed.
Installed BW mesh+metadata paths only; all6othermodel records and10prepared
texture files unchanged. Root Play MW3Remaster.cmd --prepare-only exits0.
Current native build/profile, seven models/39banks, Avatar exclusion retained.
Private Drive organized before/after and walk previews:
https://drive.google.com/drive/folders/1_CBZecIqQsQJXzAQVkge_OskM1cPhaZ-
Details docs/bushwacker-waist-fit-2026-10-15.md. Backup in revision before/.
No game launch/screenshots, protected registry/pilot edits, commit or native
execution credit.131/144strictpaused. Live visual review remains pending.
