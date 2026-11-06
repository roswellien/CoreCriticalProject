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

## Exact local candidate

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
prior donor solver. The static fitting moves elbow/knee seams to the original
pivots and preserves six recovered primary weapon endpoints; it does not move
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
applies it at the exact deferred provider call (`57E2ED`). Descriptor identity,
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
- The asset-free `deferred_source_provenance` fixture exercises the actual
  producer wrapper and late lookup, multiple material descriptors, sorted
  consumption, HUD metadata merging, Original/fallback/no-emission behavior,
  4:3 and widescreen operation, identity failures and exception cleanup.
  Mutations removing source capture or late suppression each fail the fixture;
  receipts are in `mutation-tests/result.json`.
- Fresh independent review ended clean. Its checks passed: build, CTest 37/37,
  formatting, enforced style and launcher dispatch 8/8
  (`independent-final-checks.log`). The WPF active-Steam limitation below remains.

This advances the native replacement boundary through deferred translucent
draws. It is a local development preview, not a merged or published release,
and does not establish broader live damage, LOD or cockpit-glass acceptance.

## Checks and remaining acceptance

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
`local/atlas-preview-r5/Start-AtlasPreview.ps1`. It uses an isolated game/profile,
the pinned host and prepared content, real input/clock, and a zero frame budget
(no automatic frame-limit exit). It is a development preview, not an installable
or published runtime update.
