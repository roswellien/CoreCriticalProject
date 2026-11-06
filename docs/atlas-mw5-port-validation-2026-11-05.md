# MW5 Atlas primary exterior: native development validation

The fitted MW5 AS7-K exterior now follows the original Pirate's Moon Atlas
controller matrices in the native MW3 host. This advances the owned chassis
from a donor foot-target fit to original-joint presentation in Mech Lab and a
live mission. Original gameplay, collision, motion clips, first-person cockpit,
eight original skin resources and four lamp definitions remain unchanged.
This is the primary Gunmetal exterior, not eight new MW5 paint schemes.

Implementation is tracked in [#255](https://github.com/roswellien/MW3Recomp-Private/issues/255).
The broader acceptance matrix in [#135](https://github.com/roswellien/MW3Recomp-Private/issues/135)
and appearance work in [#126](https://github.com/roswellien/MW3Recomp-Private/issues/126)
remain open. The topic branch includes the unmerged #131/#141 dependencies;
no merge or release is implied.

## November 5 local candidate

| Item | Receipt |
| --- | --- |
| Native source commit | `11b8e604c8fca19feba0702c30c70bc9a8d3daca` |
| Native build | `local/host-build-r5/source-snapshot.json`, clean source, 174 host files / 192 repository dependencies |
| Host executable SHA-256 | `c60dbafed9996c43eb5aea1a840a1803ac1013d0d0654c402c72465e5db8afa4` |
| Unchanged translated DLL SHA-256 | `6d6e3c25fef68727113a6d52859253883dbb554958ddaa5a091187667aa8bfa5` |
| Private pack | `com.corecritical.pm-atlas-0.4.3-mw5-fit-preview.mw3pack` |
| Pack SHA-256 | `7be803754e1fc764d3dd36a5deffe1a772c658dcd53f2f3f3a63ef3587ade79b` |
| Geometry | 28 batches each LOD; close 50,039 triangles, distance 20,800 |
| Conserved authoring inputs | 223 files byte-identical; only project metadata and the two MW5 mesh payloads changed |

These paths are private receipts under `D:/Projects/MW34-135-atlas-port-finish`.
Original media, donor/derived art, generated game code and native build outputs
remain local. The preview pack version is not a game release version.

## Implemented behavior and compatibility

BWMESH4 rig flag 2 applies `current * inverse(reference) * authored_rest` for
bound parts and the parent delta for unbound attachments. There is no inferred
knee pole, foot goal or gait offset in this mode. Existing flags 0/1 retain the
prior donor solver. The initial static fitting moves elbow/knee seams to the original
pivots and preserves six recovered primary weapon endpoints; the later rack
correction below supersedes the missile visual alignment. The fit does not move
the game's firing origins. The original four lamp records and L binding remain.

Selected flag-2 visuals require `owned-chassis-visuals: 2`. Original preparation
still works without that capability; inactive payloads remain fully validated.
The private MWCHAS7 catalog carries arm-subtree removal lists and parent names
derived from the original source hierarchy. Both source arms must exist without
overlap or stump aliases, and all supported damage-state LOD identities must
remain distinct. The native matcher authenticates the original shared GameZ
stump bytes, live parent topology and every surviving mesh. A previously resolved
lamp retires when its mount disappears before the destruction callback; a missing
initial required binding still fails visibly.

Historical runtime profiles are not modified or advertised as supporting this
contract. Future integration must ship the matching coordinator and native host.

## Demonstrated native behavior

All runs below use the actual native translated game and Vulkan/DXGI presentation
on the RX 9070. Scripted trials supply input at the existing DirectInput test
boundary; they do not replay frames or seed guest game state. Each retains
`run.json`, model/world logs, stderr and render-target captures.

| Run under `local/native-trials/` | Observation |
| --- | --- |
| `atlas-skin-cycle-r6` | Reviewed host, 1024x768, 2,050 presented frames. All skin indices 0..7 selected. Gunmetal queues the MW5 geometry; indices 1..7 preserve their original PM geometry. Returning to Gunmetal restores the MW5 model. |
| `atlas-wide-save-mission-r5` | Reviewed host, 3440x1440, 3,200 presented frames. Mech Lab, all eight skin selections, original configuration save named `qatest`, then the Desert mission with walking, ER laser fire, original cockpit and four mounted lamps. L toggles on/off/on and final fade-out. |
| `atlas-reload-mission-r6` | Fresh process and copied saved profile, reviewed host, 1024x768, 2,600 presented frames. The saved `qatest` variant is discovered in the Atlas list; Primary is selected in this capture. The primary MW5 model walks and fires in the mission. This establishes discovery, not selection of the saved custom variant. |
| `atlas-reload-mission-r8` | Saved custom variant `qatest` selected on a fresh process (`target-1150.ppm`), then the MW5 Atlas entered the Desert mission at 1024x768. 2,600 presented frames, original loadout and four lamps, no reach clamps. |
| `atlas-reload-mission-r5` | A navigation mismatch selected a stock Vulture. It reached the mission and fired with original geometry while the Atlas content was enabled; this is a coexistence smoke check, not stock-only acceptance. |

The saved configuration filename is the stable resource key
`configs/ccfff3f976155.mw3`; the original configuration bytes contain `qatest`.
The caller's original installation/profile is not used as a write target.
Native model logs contain no `visual_reach_clamped` event in the successful Atlas
runs. The wide run records `emitters=4`, plus two matching authored-normal images.
Bounded trials end with exit 1 at the requested presentation budget; they are
not normal-quit receipts. The tested manual preview launcher also completed a normal menu close with
`ExitProcess(0)` and DLL detach on the reviewed R5 host. Its receipt is
`local/atlas-preview-r5/runs/20261105-173201-542531/launch.json`. This close is separate from the
bounded save/reload mission trials; it is not a damaged-save acceptance run. Full intro/codec acceptance is outside these runs.

Original-mode A/B at `atlas-original-lab-r2/target-1000.ppm` also shows the small
oval above the head. The November 6 investigation below establishes its source
and removes its unintended draw from the MW5 replacement. Original appearance
retains its original polygon. This does not close the separate cockpit-glass
report in #135.

## November 6: deferred original polygon in the MW5 exterior

The floating piece was the original `atlas15` translucent quad in
`torso_polys`, polygon 41 of the close model (polygon 22 in the distance model).
Its geometry, UVs and texture match the original PM source. It is not a donor
part, and the cockpit model contains no `atlas15`. Its semantic purpose is not
established; this fix does not alter source assets or infer a new attachment.

The original mesh producer at `53F2E0` appends translucent descriptors which
`57E110` sorts and draws after the producer's replacement scope has returned.
Immediate source suppression therefore missed this later draw. Tracking just
one material enqueue backend was insufficient: several sibling backends write
the shared queue. The maintained host now retains replacement display policy
for every descriptor appended by the authenticated source mesh producer, then
applies it at the deferred provider call identified by return address `57E2ED`.
Descriptor identity,
frame, material reference and vertex range are checked. Original/fallback
appearances and previews without an emitted replacement remain eligible.
Original calls, queue contents, sort order, vertices and guest return values
are preserved; HUD provenance is retained independently of source suppression.

Local evidence is under `local/atlas-evolution-20261106/`:

- `atlas-source-queue-trace/stderr.txt` traces the original torso append and
  the later four-vertex `atlas15` draw after its source scope has returned.
- `atlas-alpha-fixed-r7` is the failed single-backend negative control.
  `atlas-alpha-fixed-r8` uses the final mesh-boundary implementation and visibly
  removes the floating quad in the same front framing. Four cardinal views
  were captured with enhanced world textures, authored normal maps, shadows
  and the complete sky. The bounded native run reaches 2,205 frames.
  `atlas-alpha-4x3-r8` repeats the four-angle check at 1024x768 and also reaches
  2,205 frames without the escaped quad. Photo-mode HUD remnants at the right
  edge remain visible in that 4:3 control; it is not used as video footage.
- All 2,205 original `(frame, draw count, draw hash)` records match between R7
  and R8. Whole log bytes differ in renderer cache counters; those counters are
  not part of this equality claim.
- R8 maintained host: `local/host-build-r8/source-snapshot.json`, based on
  `5dda1f863eaf4367e5b3e78afb854051cf19990f` plus the then-uncommitted fix.
  Executable SHA-256:
  `bff870091971b3e4ab47e202f3b91591ab25c80d111ddff8da32226b5efc563e`.
  The translated DLL remains the exact hash recorded above. The private
  `capture-host-r5/capture-build.json` pins this source and adds only camera,
  hotkey and recording automation; it is not a distributed runtime.
  The same fix was then rebuilt from clean commit
  `7bee5cb559b17c946245c5b4f39ddfc607a8cb94` in `local/host-build-r9`;
  executable SHA-256:
  `0351f3a6dd22c05687df012d7807a8cb577dd47058b9fcadcdb5c45a7ae5e4a3`.
- The asset-free `deferred_source_provenance` fixture exercises the actual
  producer wrapper and late lookup, multiple material descriptors, sorted
  consumption, HUD metadata merging, Original/fallback/no-emission behavior,
  widescreen on/off behavior, identity failures and exception cleanup.
  Mutations removing source capture or late suppression each fail the fixture;
  receipts are in `mutation-tests/result.json`.
- Fresh independent review ended clean. Its checks passed: build, CTest 37/37,
  formatting, enforced style and launcher dispatch 8/8
  (`independent-final-checks.log`). The WPF active-Steam limitation below remains.

This advances the native replacement boundary through deferred translucent
draws. It is a local development preview, not a merged or published release,
and does not establish broader live damage, LOD or cockpit-glass acceptance.

## November 6: primary paint and attachment revision

The next private candidate, `0.4.4-mw5-wear-preview`, addresses the owner's
visual review: darker slate-blue paint, stronger contrast between painted
armor and exposed panel edges, and source-mask scuffs/recess wear. These are
edits to the native Blender material graph baked to the existing armor UV layout,
without directional lighting baked into the paint. The existing two runtime
normal images retain their exact pixels and are rebound to the new diffuse
identities. No roughness, emissive or height-map support is claimed here.

The ten warhead meshes use revised axial/circumferential UVs for steel noses
with narrow, subdued identification bands instead of a solid red fill. The separate donor
`Clavicle_Left_AH1_antimissilesystem` visual is removed from both exported LODs.
This removes 942 close-model triangles; close/distance totals are now
49,097/20,424, with 27 material batches each. The original PM loadout, firing
origins, rig matrices, cockpit, eight skin resources and four lamps remain.

Evidence under `local/atlas-look-r1/` includes the editable
`Atlas-look-r1.blend`, `appearance-receipt.json`, `native-export.json`,
`pack-receipt.json`, `Native-before-after.jpg` and `Cardinal-review.jpg`.
The pack SHA-256 is
`d4554c50f70e9d2b29c8e39a489669f823a95c368e244fe9a243903d43e4a79a`.
Only project metadata and the five MW5 mesh/texture/normal-binding files differ
from the November 5 project; the other 220 project files are byte-identical.
The actual C# PackManager imported it into the isolated `atlas-library-r4`.

`local/atlas-evolution-20261106/atlas-wear-proof-r1` reached its 2,205-frame
budget in the native game at 3440x1440. Four cardinal Photo-mode captures show
the material revision, removed shoulder AMS and no escaped original quad with
the complete enhanced environment. `full-profile-wear-r1.json` reuses the
verified environment and composes the revised Atlas through the normal chassis
preparer. The maintained R9 host and camera-only capture host are unchanged.
This demonstrates the optional visual revision in the native mission; it does
not extend the broader live damage/LOD/alternate-skin acceptance above.
The subsequent `final-stage-3-wear-r1` media capture reaches 5,005 presented
frames and records 3,120 frames for the two-turn orbit. Independent evidence
review confirms preserved rig bytes, four lamps and normal-image pixels,
correct new diffuse bindings, the expected removed AMS batch and all 164
archive members matching the isolated installed pack.

### Albedo detail correction after owner clarification

The owner clarified that the flatness report concerns painted texture detail,
not new material-response rendering. Candidate `0.4.5-mw5-albedo-preview`
adds broad tonal gradients, medium-scale pigment mottling and fine coating
grain inside the existing armor panels, brighter silver-toned scuffs, and
predominantly red missile noses with varied coating. The renderer is unchanged.

Private receipts are under `local/atlas-look-r2/`, including decoded original
texture references, an unlit albedo detail comparison and four native views.
Pack SHA-256:
`49245d5e2a7fa2e0d37dad045f16096098b9d173040497de6068f1fa77bb6879`.
The normal C# importer installs it into isolated `atlas-library-r5`.
Compared with the preceding 0.4.4 project, 222 files and both complete mesh
binaries remain byte-identical; only metadata, the two color sidecars and
normal binding identities differ. Normal-image pixels, four lamps and all
original PM resources are preserved. All 164 installed members match the pack.

`atlas-albedo-proof-r2` reaches its 2,205-frame budget at 3440x1440 with the
full enhanced environment and a closer 20-unit Photo camera. This validates
native presentation of the albedo revision, not owner aesthetic acceptance.
The prior channel-video export still depicts 0.4.4 and is not evidence for
this newer candidate.

### Missile rack correction from the supplied reference

Owner Photo 1 identifies the tall ten-nose rack beside the skull. The earlier
weapon-fit translation moved its frame and noses down/forward while leaving
the surrounding cutout at the original donor location. Candidate
`0.4.6-mw5-rack-preview` reverses only that assembly translation
`(-0.642418, +0.422625, +0.958778)` in authoring coordinates. The nose mesh
receives nondegenerate UV islands and a full-tile red coating bake with tonal
variation and small exposed-metal scuffs. Existing detailed armor paint,
normal-image pixels, rig and removed shoulder AMS are retained.

Private evidence is under `local/atlas-look-r3/`: `rack-receipt.json`,
`nose-visibility.json`, `pack-receipt.json`, native closeup and cardinal views.
All ten front-facing nose visibility rays hit the nose mesh. Pack SHA-256:
`466aff22e2cec64855c9d180a1c351574b9fe2f2ab832f92840280425e311933`.
The actual importer installs it into isolated `atlas-library-r6`.
`atlas-rack-proof-r3` reaches 2,205 frames at 3440x1440 and shows the rack in
the reference location, with red noses, in four Photo-mode views.

The original PM missile firing coordinate remains unchanged. Restoring the
donor rack leaves a 1.229052-metre visual-mouth offset from that coordinate;
the six-endpoint alignment criterion is therefore not complete for this
candidate. No gameplay origin is silently moved to disguise that limit.
The owner subsequently approved native red eye/cockpit emission and faint spill,
with a reusable authoring contract for other mechs. The next section records that
implementation; red eye albedo alone was not counted as glow evidence.

## Reusable native eye glow, November 6

Private candidate `0.4.7-mw5-eye-glow-preview` has pack SHA256
`c8dee2b4792237d3290d37aefc606297d2834c8995f890cf0db7dab7404e7131`
and installs through the actual C# importer into
`local/atlas-library-r7`. Meshes, UVs, color/normal images and existing resources
are byte-identical to 0.4.6. Only the project metadata and two authored `BWMEM1`
sidecars are added. Two anchors use the current rigid glass batch's exact pose;
the central non-eye glass strip is excluded from the emissive UV rectangle.
The four headlight definitions and original gameplay remain unchanged.

The maintained host is built from clean source
`18e40c11ef86f4c70a729e3c8ee8da7faa010db7` in
`local/host-build-emission-native-r5`. Its translated module remains
`6d6e3c25fef68727113a6d52859253883dbb554958ddaa5a091187667aa8bfa5`.
The generic runtime integration is documented in
[owned emission materials](owned-emission-materials.md). No Atlas name, image
hash or eye coordinates are hardcoded in the renderer. The capability is
advertised only in this source-pinned development profile, not historical
release profiles.

Native `atlas-glow-positive-r1` and `atlas-glow-zero-r1` each present 2,205 frames
at 3440x1440 using `capture-host-emission-r1`, based on clean `e73dcd9`
(`host-build-emission-native-r2`). They follow the existing live-menu -> Atlas
-> mission path, then use
controlled Photo views. Both use identical geometry/albedo/world settings;
the negative control is a valid descriptor with zero surface/spill intensity.
Front differences are confined to 1,901 pixels around the eyes/nearby face
(x1644..1799,y162..232); sides change 399/454 pixels and the rear is pixel-identical.
A separate spill-only versus zero comparison with normal mapping disabled
uses `capture-host-emission-r2`, based on clean `bdf2f114`
(`host-build-emission-native-r3`). It changes 1,904 front pixels near the face;
rear remains identical. The glass has
no authored normal sidecar. These are native visual checks, not live gameplay,
performance or full-model acceptance.

Independent source review found and fixed missing CPU receiver metadata and a
missing installed-coordinator module. Build, 39/39 CTest, formatting, style,
launcher dispatch 8/8 and focused C# content/import checks passed. Isolated
installed and refreshed coordinator tests read emission without checkout
imports. Deliberate identity/gate, shader-uniform and pose-transform mutations
fail the authored tests. Full WPF checks, retried with no native game running,
still stop at the pre-existing active-Steam guard; Steam remains untouched.
The first attempt during a capture stopped at its expected games-closed guard.

Native global GPU-off diagnostics stop before gameplay with the existing
“Sun prototype requires GPU geometry” restriction. This is not CPU parity proof.
The dedicated `capture-host-emission-near-r1` derivative of the same clean r5
source lowers only Photo mode's camera-radius floor from 2.5 to 0.05. Its receipt
also pins that camera-math change; no emission or renderer code is altered.
`atlas-glow-near-final-on-r1`, `-zero-r1` and `-fixturesoff-r1` each present
2,205 frames with normal mapping off. At frame 1800 the actual nonempty clipped
glass command reports `cpu_emission_batches:1`. Positive/zero controls differ
in 151,038 pixels in the head-intersecting front view; the other views are
pixel-identical. Fixture-off positive descriptors match the valid zero control
pixel-for-pixel in all four views, with the same CPU receiver admitted. This
checks actual shader admission and stable base lighting under the preference.
The extreme diagnostic camera is not an aesthetic/model-quality capture.
Scene-local retirement, distinct-root isolation and 4096 nearest-candidate
selection also have authored production-helper coverage; broad mission/skin
transition and multiple-live-Atlas acceptance is not claimed.

`atlas-glow-lamps-walk-r2` uses the clean r5 camera derivative with full normal
mapping, original W movement, and the original L input before Photo mode.
The log confirms L at frame 1600, four emitters reaching intensity 1 by frame 1680,
and 11 selected fixture/moving lights at frame 1780 (five cached scenery sources,
four headlights and two eye anchors). Native views retain the red eyes. The
first lamp-input attempt inherited a historical unbound session preference;
the retry and manual preview use their own isolated L binding without changing
global user settings. This is a short movement/control check, not broad combat
or headlight acceptance across every model.

The updated local comparison package is
`D:/Projects/MW34Recomp/reports/atlas-evolution-20261106-r4`: 1440p60 and 1080p60
exports, 6,061 frames / 101.016667 seconds, the approved 5-second opening with startup
SFX, revised thumbnail and description. The final MW5 orbit presents 5,005 frames
and records 3,120 frames from clean r5 (`final-stage-3-glow-r1`); earlier Original
and upgraded source passes retain their own build identities in the export
receipt. Both outputs decode fully; opening audio correlation is 0.999618.
Normal binding verification confirms two unchanged Atlas normal images across
five material records. The thumbnail is a built-in imagegen edit of the prior
master using the actual native screenshot; its prompt and receipt are saved.
The video and screenshot A/B are native evidence, not generated visuals. No
media upload or release publication has occurred.

## Earlier fitting checks and remaining acceptance

- `python tools/check.py --area launcher`: build passed; CTest 36/36 passed;
  C++ format, enforced style and launcher dispatch passed. The full launcher WPF
  suite stops at its pre-existing active-Steam guard; Steam was left running.
- Focused launcher `--content-only`: passed, including real pack import and
  appearance, eight-slot legacy skin, identity, integrity and capability checks.
- Native catalog and headlight C++ checks: passed; production owned-arm matcher
  fixture covers left/both loss, wrong surviving parts, altered stump bytes,
  foreign parents and foreign chassis identity.
- Production FK: 666 samples x 12 declared controllers across reference, stand,
  walk and 15 compiled motion clips; maximum matrix error `7.1054e-15`, zero
  clamps. The collapse/limp clips have ankle/toe tracks absent from this reference
  model; those tracks are not included in the controller comparison. This is
  offline pose coverage, not live acceptance of every animation/damage state.
- Regression mutations were observed failing for disabled source FK, unsupported
  flag 2, omitted selected-version gating, removed owned damage admission,
  disabled missing-mount retirement, missing MWCHAS7 support, ambiguous damaged
  LODs, stump aliases and overlapping arm subtrees.
- Independent sessions reviewed the FK path and the damage/catalog/lamp delta.
  The fixture capability leak and damaged-LOD ambiguity found in review are fixed.
  Frozen-language style suggestions remain report-only in
  `local/atlas-fit/style-verbose-r5.log`; enforced style passes.

Source-pose reproduction with the private inputs present:

```powershell
& local/atlas-fit/build_pose.ps1 -Source pose_source.cpp -Name pose-source
python local/atlas-fit/check_source_poses.py --rig local/atlas-fit/candidate-r3/rig.json --all-motion --source-joints
```

Full live limb loss, distant LOD transitions, all eight skins in missions,
player/ally isolation, damaged-save reload, stock-only regression and the seven
upgraded alternate skins remain in #135/#126. Arm-loss and lamp-retirement
fixtures do not establish those live results. The normal-map/POM comparison
video and Mod Studio validation are separate work.

A local manual preview entry point is
`local/atlas-preview-r13/Start-AtlasPreview.ps1`. It uses an isolated game/profile,
the pinned host and prepared content, real input/clock, and a zero frame budget
(no automatic frame-limit exit). It is a development preview, not an installable
or published runtime update.
