# All prepared mech models connected to Remaster

2026-10-16. The user's request to connect all new models is installed in the
living Play MW3Remaster launcher. The native executable is
`local/remaster/gpu-native-all-models-r1/build/entry_commandline.exe`, SHA256
`8bf6e08e33c1c6e2b86ef9c2c17ca973872634db09b64ded47055e2814dac06b`. It extends the previously selected
turret-aim host, preserving its37,201translated objects and all host files
except the documented optional model adapter/registration changes.

## Installed selection

Fifteen chassis: all14locally matching MW5 replacements plus the detailed MW3
Strider. The eight additions are Black Hawk/Nova, Champion, Puma/Adder,
Annihilator, Cauldron-Born/Ebon Jaguar, Sunder, Supernova and Strider.
The parked STL Avatar remains excluded; Avatar, Firefly and Owens retain
their original MW3 geometry. Existing Bushwacker/Orion/Daishi/Shadow Cat visual
fits remain. Mad Cat/Vulture/Thor now use their final prepared BWMESH2 close
streams and distance variants, retaining their verified identical LOD0 vertex
bytes and latest maintained-worn color sources. Current model records/PNGs
are read at launch; --prepare-only completes all15model sidecars successfully.
Retired obsolete r5-executable/unused-texture requirements from Bushwacker.

Both actual .cmd launchers pass --check. The standard launcher reports15models;
the without-new-models launcher reports original geometry on the same latest
native host. Graphics remain3440x1440,FXAA,AF16,1200-unit scenery and1100-unit
fog;39cumulative banks, current HUD, music and original-model option remain.
No game install or real save/registry data were rewritten.

## Runtime and asset changes

Authored donor_retarget.hpp and donor_runtime.inc implement compiled optional
visual retargeting. The new MW5 rigid parts preserve donor lengths and original
source control deltas. The legs solve in their donor sagittal planes; no new
guest joint, independent gait timer or guest transform writes. Unreachable
goals are constrained for visual reach rather than stretching limbs. A reach
limit diagnostic occurred in each donor player run; its frequency is not
measured by the once-per-root log. Original weapon origins/simulation remain.
Helpers with identical motion share rigid groups. The few true cross-joint
seam triangles retain per-vertex bindings and use the existing CPU clipper;
remaining geometry uses resident GPU batches. Caches belong to the actor and
scene; different cameras recover the current root-to-camera basis.

BWMESH4 adds bounded donor bone/reference matrices and gait metadata before
the existing batch streams. Each batch specifies a rigid bone or a per-vertex
seam index list. Invalid counts, names, parents, frames, affine matrices,
binding indices and nonfinite data fail explicitly. V1/V2/V3 retain prior
behavior. BWTEX1 accepts1..64materials, allowing Strider's source tile set and
constant edge/glass/joint colors. Current native sidecars contain base color;
Blender12xnormal maps are not enabled by this standard renderer profile.

All15have close bindings; all except Bushwacker also have distance bindings,
29total. Original LOD choice remains in control. New distance bodies weld
coincident positions while retaining per-corner UVs/normals, then simplify
body geometry. Weapons, exterior cockpits and cross-joint seams are retained.
Strider's thin authored trim keeps the full17kgeometry at both distances,
with omitted controls folded into original distance ancestors and its
different original LOD1head offset compensated in payload coordinates.

| New chassis | Close triangles | Distance triangles |
| --- | ---: | ---: |
| puma | 56,501 | 30,009 |
| annihilator | 28,618 | 17,402 |
| cauldron | 41,456 | 24,320 |
| sunder | 46,099 | 25,100 |
| supernova | 34,040 | 18,848 |
| blackhawk | 41,657 | 24,443 |
| champion | 37,305 | 21,210 |
| strider | 17,129 | 17,129 |

The first live Black Hawk case exposed a cockpit-binding defect. Recovered
all18original cockpit mesh signatures from the existing decoded mechlib;
only complete exact signatures are excluded from body identity. Source cockpit
draws remain original. All29rosters pass complete/changed-cockpit controls.
Added exact source arm-loss alternatives at both distances:58plans total,
with original stump signatures/ancestry and surviving-node checks retained.
Missing visual helpers at distance inherit source parent deltas; this changes
no game-required service or simulation control.

Final image review caught Strider's saved walking pose being baked against
stand and then applied again in-game. Corrected the export to cancel the current
owner matrix and preserve controller-local mesh coordinates. All51,387serialized
corners match the original detailed scene within0.000002873
world units; all16moving mesh bindings match across336frames within
0.000000954. Geometry, UVs, colors and
actions are unchanged. Corrected both close/distance streams and repeated the
actual adapter and native Strider case. Failed payloads/images/runs remain.

## Validation and execution reached

Final executable, with actual gameplay reached in focused isolated runs:

- Training software frames116/116identical to previous native host.
- Mode7original GPU draw records1150/1150identical.
- Instant Action software frames116/116identical.
- Each of eight additions completed an1800frame native IA player check at
  3440x1440,FXAA,AF16, with positive visible GPU geometry. These are rendering
  checks, not per-chassis original-draw equality claims. Test enemy selection
  does not establish that the enemy was within the camera frustum.
- Actual compiled adapter fixture:10,370,795checks,0failures. Includes all29
  identities, close/distance parsing, original visibility/reactivation,
  cockpit attachments, exact arm-loss alternatives, CPU/GPU emission and
  malformed payloads.406approved stand/walk samples agree within0.000012617;
  recovered extra motion clips and distance samples retain finite poses and
  fixed joint lengths. Separate asset-free math fixture:42checks,0failures.
- Actual .cmd --check, --prepare-only and original-model .cmd --check pass.
  Prepared texture sidecars follow current registrations, including updated
  Mad Cat/Vulture/Thor distance batch indices and all Strider source materials.

Initial nonfocused runs stayed in menus and are retained as incomplete
coverage. They are not the final gameplay regressions. The expected exit1
is the explicit presentation frame budget, not normal mission completion.
No new campaign completion, full damage/LOD transition closure or FPS claim.
Live NPC distance transitions, every damage/debris state, muzzle presentation,
extended play and native normal mapping remain. Models retain candidate labels.

## Delivery and continuation

[Native overview](https://drive.google.com/file/d/1DjKbiJcN0UCBZnmGKPg-EneYr5sLevxV/view?usp=drivesdk).
[Corrected Strider](https://drive.google.com/file/d/1wOPeUTgbC5U5gcnMH5ckbOWg7kVo_AhR/view?usp=drivesdk).
[Organized Drive previews](https://drive.google.com/drive/folders/1_rfk3ocVrRCplcaw_Z7ZQiT47IKrauzt). Ten files in two folders have verified
names, MIME types, parents and exact remote/local sizes; local SHA256 recorded.
Full PNGs are3440x1440native render-target dumps, not desktop screenshots.
The overview is reduced for identification. Camera uses original external
follow framing, which can crop the lower player model. Sharing unchanged.

Private source/build/scripts/proofs and failed attempts remain at
C:/Users/jcbla/.codex/workspace-storage/MW34Recomp/mw3-all-models-native-r1.
Runtime registrations currently reference that C:asset workspace as well as
D:project assets; retain it until a later packaging/migration task. The published
executable and source-snapshot metadata are under local/remaster/gpu-native-all-models-r1.
Backups: local/remaster/launcher.before-all-models-2026-10-16.json and
models.before-all-models-2026-10-16.json. Preserve both for rollback.

Boundary advanced: prepared offline models -> registered native visual payloads,
original-control GPU rendering in actual IA, and the standard Remaster launch.
Original recompiled gameplay remains in control. Installed registry/pilot files
are unchanged; tests used private copies and overlays. Protected jobs and other
writers were preserved. No desktop capture or commit. Strict acceptance remains
paused131/144; no additional native-function acceptance credit.


## Later startup repair and current build

The [post-video heap isolation repair](post-intro-heap-isolation-2026-10-16.md)
now supplies the standard launcher. It preserves all 15 models/29 bindings while
retaining the newer photo/replay source. The original all-model host above is
retained as evidence and is superseded for play by the repaired build.
