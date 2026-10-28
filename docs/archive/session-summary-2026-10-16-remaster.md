# Remaster session summary - 2026-10-16

The public website entry for this day is `docs/mechlab/2026-10-16.md`.
The sections below retain technical/session evidence and distinguish offline
visual experiments from native runtime work. The public feed does not scan this
file. Individual earlier sections record their state at the time of that task.

## Native rendering, campaign and distance work

The main and alpha profiles use draw1200/fog1100 with authenticated main/zoom
camera extension. Mission2 platform investigation finds both actors in private
loads, but the user's Bravo disappearance while approaching without firing is
still unresolved. A distinct original short-frame turret-aiming defect was
reproduced and its optional correction published in the regular playtesting
profile. It is not proof of a Bravo fix or mission completion. Details:
`docs/campaign2-platforms-and-distance-2026-10-16.md`.

Matched earlier Remaster/alpha throughput tests at3440x1440 FXAA/AF16 and1200/1100
measured87.2/88.0FPS (+0.9%, within run variation); alpha1% lows were worse.
No reliable GPU-geometry speedup is established. The stale CPU-removal timing
package had zero bypass admissions; rebuilt experiments fail scene matching.
Keep CPU projection bypass0. See `docs/gpu-geometry-benchmark-2026-10-16.md`.

## Big Lake directional sun and measured cost

Created a separate native Big Lake launcher/private instance and configurable
world-fixed directional sunlight plus constant ambient. GPU world/model normals
and a limited opaque original-TL terrain receiver bridge feed per-pixel lighting.
No normal-map sampling, cast shadows, local lights or bouncedGI. Sky/HUD retain
their old path; inherited replacement fog and near-clipped batch limits remain.
Both existing launchers and protected original pilot/registry/Mission2 save
remain unchanged by this experiment. Details: `docs/big-lake-sun-test-2026-10-16.md`.

Final sun1000-frame original draw records match, and final captures reproduce
the corrected earlier sun views. Sun-off repeat matches1000 control records and
both control captures; initial final-off divergence at487 remains unexplained
and retained. Authored CPU/GPU fixtures pass; Vulkan validation layers unavailable.

Four same-executable1800-frame Big Lake benchmark runs, off/on/on/off, measured
124.85FPS off versus121.50FPS on (−2.7%),8.010/8.231ms (+0.221ms),1% lows
37.47/36.75FPS. All per-frame scene counts/final geometry counters match and
within-mode repeated captures are exact. Actual host throughput uses fixed50ms
simulation input; not live-clock whole-game performance. Diagnostic draw/projection
logging off, required world log retained. Do not cross-compare these numbers to
the earlier separate-session alpha benchmark. See
`docs/big-lake-sun-benchmark-2026-10-16.md`.

Screenshots and benchmark report uploaded and metadata verified on Google Drive:
https://drive.google.com/drive/folders/1tN9VCLV95oWMAaaQS3BV5H6_cx8jpoxN
Remote reviews must use Drive links. Renderer handoff and next-agent prompt:
`docs/rendering-handoff-2026-10-16.md`. Next recommended feature is normal-map
materials on one replacement mech, then bounded local lights and shadow proof.
General shadows need real off-camera caster collection; TL receiver normals
cannot supply that. User paused development for usage limits; the subsequently
requested benchmark is complete and development returns to that pause.
Mech Lab/user campaign playtests remain open. Acceptance stays131/144.


## Black Hawk and Champion worn colors

User approved Black Hawk's corrected walking animation; both initial color
drafts were still too clean. Added four generated Body/Variant color edits
with paint-cut scars, steel exposure, chips, localized scorching and service
grime; reused worn Weapons atlas after exact UV/detail normal hash match.
Seventeen other material maps per chassis retain their original bytes.
Geometry/UV/rig/placement/action hashes unchanged; approved walk preserved.
Matched diffuse/unlit comparisons and updated11.2s walking clip reviewed.
Saved-action449-time knee/ankle contact check still passes. Two20-map ZIPs,
PNG sets, packed Blender scenes, exact prompts and local comparison HTML.
26 Drive uploads and7folders verified by metadata readback:
https://drive.google.com/drive/folders/11aIvVfTZvc31I1EdX44pZ1NTHdqasHUr
Latest candidate material pointers updated for future native ports.
Details docs/blackhawk-champion-worn-textures-2026-10-16.md.

Neither new chassis installed. Black Hawk native visual retarget and existing
Champion fit/muzzle/damage/LOD limits remain; no runtime execution advance.
Current seven live models/profile retained. No game launch, desktop screenshot,
protected registry/pilot edit or commit. Strict acceptance paused at131/144.


## Thor retained R2 and Vulture stronger R2 installed

User reminder: both skins should follow maintained-but-well-used directive.
Thor stronger R2 already installed; reviewed/retained unchanged. Vulture broad
armor still too plain: new Body/Variant steel-cut scars, chips, seam grime,
localized scorch/launcher fouling, same MW3 taupe/gray/blue-gray color zones.
Other3colors and normal/roughness/metallic files unchanged; no new normal relief.
32part geometry/UV/pose digest preserved. Built-in image_gen prompts retained.

Installed Vulture texture paths only. Actual root launcher --prepare-only0;
all Vulture RGB565 pixels/hashes/bindings verified (32b/9451864bytes), other9
sidecars unchanged. Thor5paths/PNG hashes match R2 and staged digest matches
prior complete pixel check. Other6records/meshes/current native/profile retained.
25Drive files/7folders readback verified, combined currentR2/R1 comparisons:
https://drive.google.com/drive/folders/1_OrNxlxZ7SFANNRF3mbkU1dIyy6YR0BJ
Details docs/thor-vulture-service-wear-2026-10-16.md.
No game launch/screenshots/protected registry-pilot edits/commit.131/144paused.
Offline color preparation advances, no new native execution/performance claim.


## Five-mech normal-map walking tests completed

Mad Cat, Thor, Vulture, Black Hawk and Champion use latest worn colors and
unchanged donor tangent normals, approved12x response10.20/glass0.30. Controlled
same illustrative PBR and height-normalized moving key/fill. Preserved geometry,
UV/weights/rest/action curves; all336output poses match source exactly. Black
Hawk approved donor-length walk retained. Six walks/one orbit11.2s30fps; individual
1280x960videos and combined1920x960. Matched color/neutral off-on stills, editable
packed Blender scenes and localHTML.27Drive files/6folders metadata verified:
https://drive.google.com/drive/folders/1KcleCRlp7SFz7KBZ8rn9ICGzWuVa3OzR
Details docs/five-mech-normal-walk-preview-2026-10-16.md.

Offline visualization only: native lighting/normal/shadow support, game FPS and
Black Hawk/Champion runtime integration unchanged. Painted new scars have no
new normal relief. All render-source/model registry/root-launcher pins match;
shared launcher profile changed externally and is preserved, identities recorded.
One BelowNormal2thread renderer; existing game session left untouched. No task
game launch/screenshots/registry-pilot edits/commit.131/144strictpaused.


## Following-camera correction and Mad Cat 24x preview

Fixed R1 static-camera presentation: camera, orbit center/aim and fill now follow
world hip/pelvis XY for all5mechs; vertical bounce and all336model/rig poses
unchanged. Geometry/UV/weights/rest/actions preserved, actual-vertex camera bounds
checked with evaluated camera per frame. Six verified11.2s336-frame videos:
5corrected12x walks plus Mad Cat24x, synchronized12x/24x side-by-side and overview.
24x changes only armor/variant/weapons normal Strength10.20->20.40; all other
material inputs/images and336camera/light/model poses identical. Planned native
12x target unchanged; exploratory Blender-only comparison.
33Drive files/6folders metadata verified:
https://drive.google.com/drive/folders/1X3TNDdQiV1Xh5qZ0HC0dRTDxhv5BYxM2
Details docs/five-mech-camera-follow-24x-2026-10-16.md.
Render source pins preserved; no native execution/FPS/settings/registration change,
game launch/screenshots/registry-pilot edits/commit. Strict131/144paused.


## Mad Cat high-quality video replacement

User reported compression obscuring details. Re-encoded12x/24x directly from
original336PNG frames at H.264CRF8/slow/grain; native1280x960 each, comparison
2560x1020 with no model-image downscale. Same animation/camera/lights/materials.
Both full-frame YUV420 SSIM checks improve over oldCRF20;336frames30fps11.2s
metadata verified. Updated3existing Drive IDs, added2lossless PNGs and notes;
6writes verified including sizes. Local prior encodes and PNG sources retained.
Details docs/five-mech-camera-follow-24x-2026-10-16.md. No native/game/settings
change, launch/screenshots/registry-pilot edits/commit.131/144paused.


## Normal-map target reaffirmed at 12x - 2026-10-16

After reviewing the high-quality Mad Cat12x/24x comparison, the user saw very
little to no difference and explicitly retained12x as the goal going forward.
Use the approved12x-equivalent MW5 appearance: Blender armor/variant/weapons
Strength10.20 from baseline0.85, glass0.30. Calibrate future native materials
visually to that reference; preserve separate original-MW3/per-material tuning.
Keep24x as experimental comparison evidence only. No renderer/launcher/live
asset change, game run or acceptance advance; strict131/144 remains paused.


## Puma and Annihilator visual port candidates

User approved the pair. Both donors/cockpits and 11 MW3-primary weapon visuals
were decoded and assembled; Annihilator selects 4 LB-X10s and 4 medium pulse
lasers. Uniform height matches the original; donor geometry, UVs, weights, rest
joints and leg lengths are retained. Source-driven visual IK uses small walking
pelvis drops, a ground baseline and toe mapping. Each model passes 449 saved
animation contact/interpolation checks without thigh clocking.
Four built-in image_gen Body/Variant wear edits and a verified shared Weapons
atlas provide the worn colors; 17 other maps per chassis are unchanged. Two
20-map packs are included. All 336 preview poses match the adapted retarget.
Delivery includes two CRF 8 individual walks, a comparison at original pixel
dimensions, lossless original/wear/normal/unlit views, packed Blender scenes
and static glTF candidates. Metadata and byte lengths verified for 32 Drive
files in 7 folders:
https://drive.google.com/drive/folders/1zvFcOnsjMnPQku-ziRbAVfkpbaNTd9Pd
Details docs/puma-annihilator-port-progress-2026-10-16.md; local candidate-assets.json.
NOT INSTALLED: native visual retarget adapter, muzzle/damage/LOD/live checks
remain. Existing 7 registrations preserved; no engine/launcher change, game run,
screenshot, protected registry/pilot edit or commit. Strict acceptance remains
paused at 131/144.

## MW4 Owens donor review

Recovered Owens from the installed MW4 Mercenaries core/props/textures archives
with a pinned source-only #VBD/LZW/ERF Blender importer. Twenty exterior meshes,
935 triangles and 36 recovered rig joints; six textures resolved and 146 source
animation Actions imported. Four first-person cage meshes are retained separately
and excluded from exterior output; no invented canopy or mesh repositioning.
Original MW3 geometry triangulates to 774 faces. The donor is wider; complete-
height comparison includes MW3 antennas and is not the final port scale.

Original-texture front/rear/side comparisons and a high-quality recovered MW4
walk review are published with texture sources in separate Drive folders:
https://drive.google.com/drive/folders/1W9xIqZEEiBaZ09VuHWjOmkUZYCcUnJdL
Ten files / three folders verified, including exact remote/local byte sizes.
Source archive hashes and render geometry/UV conservation checks pass; static
exterior glTF contains exactly 20 meshes / 935 triangles and no animations.

NOT INSTALLED. Native camouflage composition, MW3 scale/control/gait fitting,
upgraded worn materials/normal maps and weapon/damage/LOD/live checks remain.
Details: docs/mw4-owens-donor-review-2026-10-16.md. Tool source has no declared
license and stays local. No game run, desktop screenshots, protected registry/
pilot edits, launcher changes or commit. Strict acceptance remains 131/144 paused.


## Original MW3 Avatar - 12x normal-map review

User stopped the MW4/MekTek search and requested the original MW3 Avatar.
Prepared its original19-mesh /279-polygon /558-triangle model, upgraded primary
colors from avatar-textures-v1/modding-v1 and original57-sample walk. No STL data,
limb correction or geometry change. All336 source poses match within2.39e-6.
Twenty-one prototype height/normal groups serve25 unchanged color bindings;
20 newly authored,1 inherited after exact color/dimension identity. Strength10.20
=12x0.85. Normal-on/off camera/light/object signatures match at all336 frames.
Three CRF8 high-quality videos plus lossless pairs and a42-map ZIP are delivered;
10 Drive files /3 folders read back, including exact remote/local byte lengths.
https://drive.google.com/drive/folders/1iUj76LAOiCeBRfw7fhnkrjl1a-UJFEiz
Details docs/mw3-avatar-normal-preview-2026-10-16.md. Outputs/packed scene on C:
C:/Users/jcbla/.codex/workspace-storage/MW34Recomp/mw3-avatar-normal-light-r1.
Offline Blender material review only; no native/launcher change, game run,
desktop screenshots, registry/pilot edits or commit. Strict131/144 remains paused.


## Cauldron-Born and Sunder visual port candidates

Complete MW5 DLC8 body/cockpit/primary-weapon candidates, original MW3 palette
references, maintained-worn colors and12x normal/light walks are prepared.
Donor lengths, source-present controls,449 saved animation checks per model,
336 retained poses and complete-assembly MW3 height checks pass. Corrected
Cauldron's shoulder-pod height with uniform full-rig scale; initial partial
render retained. Body triangles34397/41976;5/8weapon assemblies. Two20-map packs,
lossless comparisons, static glTF and three CRF8videos delivered to Drive:
https://drive.google.com/drive/folders/1t1XJCQEYEu3rtQ2GpXSCv3MC3F_luuzF
32files /7folders verified, including remote/local sizes. See
docs/cauldron-sunder-port-progress-2026-10-16.md. NOT INSTALLED: native optional
visual retarget, muzzle/damage/LOD/live checks remain. Supernova is the remaining
untouched MW5 match. Keep original MW3 Avatar/Firefly/Owens/Strider until suitable
higher-polygon donors are found. No game, desktop screenshots, protected files,
runtime/launcher change or commit. Strict131/144 remains paused.


## Supernova visual port candidate

Prepared complete MW5 DLC9 Supernova body/exterior cockpit and six ER large
laser visuals. Donor-length walking, source three-toe-per-foot controls,449saved
contact checks and original MW3 full standing height pass. Maintained-worn colors,
20-map pack and12x normal/light HQ walk delivered: https://drive.google.com/drive/folders/14zgDxIUzrmncjFzypAqYH3MOgyC21CS9
15files /3folders verified including remote/local sizes. See
docs/supernova-port-progress-2026-10-16.md. All14local MW5 matches now have initial
visual work:7existing runtime registrations plus7offline candidates. Supernova
is NOT INSTALLED; native retarget/combat/LOD/live checks remain. Preserve original
MW3 Avatar/Firefly/Owens/Strider pending suitable higher-polygon donors. No game,
desktop screenshots, protected file edits, launcher/runtime writes or commit.
Strict acceptance131/144 remains paused.


## Original Firefly and Strider normal-map tests

Completed matched original MW3 Firefly/Strider upgraded-color12x normal-map
walk/light previews. Original geometry/UVs and336source poses retained per
model; on/off camera/light/object signatures match336frames. Firefly622triangles,
32color bindings/16normal maps; Strider759triangles,22bindings/15maps. Colors
unchanged;13/12new relief tiles plus3exact-matched inherited maps each. Fixed
false relief under painted symbols. Six CRF8HQ clips, still/neutral pairs,
contact sheets and color/normal/height packs delivered: https://drive.google.com/drive/folders/1hTVAlWNBh5sVunDE9pnKqNzMXcgNzeME
20files/7folders verified including byte sizes. See
docs/mw3-firefly-strider-normal-preview-2026-10-16.md. Offline only; no native
normal-map integration, launcher/runtime writes, game, desktop capture, pilot/
registry changes or commit. Strict acceptance131/144 remains paused.


## Strider original-model geometry detail prototype

Authored a17,129-triangle Strider prototype from the original759-triangle MW3
design, preserving16moving parts and336original control poses/action curves.
Added60armor layers,5cockpit frames/smooth panes,12vents,2port collars and
joint covers on existing controls. Retained original source and first draft;
52texture PNGs unchanged. Matched walking/12x-light videos and normal-off
geometry stills, packed Blender/static GLB and material pack delivered:
https://drive.google.com/drive/folders/1m0CEmWk1wXHIKlkQGkWvIUvx0IYbAwEv
13files/4folders verified including exact byte sizes. Static16part roundtrip
error below0.00001; full336frame vertex framing passes. See
docs/strider-geometry-detail-prototype-2026-10-16.md. OFFLINE PROTOTYPE, NOT
INSTALLED; native payload/material/weapon/damage/LOD/performance work remains.
No game, screenshots, protected file edits, runtime/launcher writes or commit.
Strict acceptance131/144 remains paused.


## Strider smooth armor normal-map revision

Addressed user-reported wrinkles on broad plates/head roof. Edited12relief
tiles and added a derivative noise floor, retaining12x strength,22unchanged
colors,3shared relief groups,17,129-triangle geometry and336original poses.
Matched HQ walk, roof and neutral-gray comparisons, editable scene/material
pack delivered: https://drive.google.com/drive/folders/1hRkIHkTC-sJ0W41adAwYlzkSe52fkz6f
11files/4folders verified including byte sizes. Source/map/pose/packed-image/
video/ZIP/HTML checks pass. See docs/strider-normal-surface-cleanup-2026-10-16.md.
Offline only; no native/launcher change, game, desktop capture, protected-file
edits or commit. Strict131/144 remains paused.


## All prepared models installed in the native Remaster launcher

Connected all14MW5chassis plus detailed Strider (15total), latest base colors,
29close/distance bindings and original-model launcher on native8bf6e08e.
Eight actual1800frame player runs, final gameplay regressions116/116,1150/1150,
116/116 and10,370,795adapter checks pass. Fixed source cockpit recognition and
Strider double-pose export; corrected Strider51387corners/336bindings checked.
Graphics/HUD/music/39banks retained; STL Avatar excluded. Previews: https://drive.google.com/drive/folders/1_rfk3ocVrRCplcaw_Z7ZQiT47IKrauzt
Native normal mapping, fullcombat/debris/LODtransition/muzzle/performance QA
remain. Source/proofs/assets partly on C:; preserve that workspace. See
docs/all-models-native-integration-2026-10-16.md. No desktop capture, actual
pilot/registry writes or commit. Strict acceptance131/144stays paused.


## Opening-video startup crash repaired

Installed native `110c0ae83f79` with isolated CRT/codec/service heap regions.
Reproduced the invalid campaign-list read after the movie; codec freed blocks had
been reused by the separate game heap. No pilot reset, seeded fields, index
clamp or movie bypass. Also restored all 15 chassis/29 bindings in the newer
photo/replay host after the live check caught its older seven-chassis adapter.
Final complete opening/menu, enlarged-environment skip, full-profile Black Hawk
IA, Training116/116, GPU1150/1150 and IA116/116 pass. Source snapshot identity/model
checks now protect the installed launcher. See [repair evidence](post-intro-heap-isolation-2026-10-16.md).
Original files untouched; no commit; strict acceptance 131/144 remains paused.
