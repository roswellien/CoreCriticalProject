# Orion, Daishi and Shadow Cat ports — October 15

**Fit correction:** Daishi's waist connector and Shadow Cat's outward thigh fit
are corrected in new close/distance asset revisions on the unchanged r17 host.
Both models draw natively, with 4,700/4,700 original draw records matching the
earlier cases. [Correction details and previews](mw5-fit-corrections-2026-10-15.md).

**Later follow-up:** the launcher now selects r17, which fixes whole-model
fallback after original arm loss. All three new LOD1 variants have also drawn
in native tests. See [the damage and distance record](mw5-arm-damage-fix-2026-10-15.md).
The r15 first-integration evidence below is retained with its original scope.

The next three MW5 model ports now render in native MW3. The initial Remaster
profile selected **r15** and included Orion, Daishi (Dire Wolf) and Shadow Cat
alongside Bushwacker, Mad Cat, Vulture and Thor. The three new entries remain
**runtime candidates**. Avatar/STL work remains parked and excluded.

Launch `Play MW3Remaster.cmd` in the project root. The profile remains
3440×1440, FXAA and 16× AF, with all 39 registered texture banks, the existing
HUD pack and local music. The original-models launcher uses the same r15 host
without replacement geometry. Both launchers use the published executable hash,
not file modification times.

[Model comparisons, standing/walking renders and native captures on Drive](https://drive.google.com/drive/folders/1sZydS_wzVdXtAs3dSPD6ae4hxQt7_DDv).
[Texture drafts on Drive](https://drive.google.com/drive/folders/1Y4eDZtk5fTA_M8XSNy10C6ZHJeaM4RwK).
These remain in the project's existing private folder organization. Blender
renders and native target dumps supply previews; no desktop screenshots were taken.

## Assets and fit

All source bodies, separate exterior cockpits, original donor hardpoint sockets
and necessary weapon assemblies were decoded locally with the existing tools.
The primary visual layouts follow the original MW3 chassis definitions:

- **Orion:** ON1-M parts supply two medium lasers, LB-X 10, SRM4, LRM20 and NARC.
  The initial ON1-K selection was replaced because its visible loadout differed.
- **Daishi:** Dire Wolf Prime supplies four ER large lasers, four medium pulse
  lasers, two Ultra AC5s and LRM10. Multiple weapon classes share original MW3
  firepoints; their bindings are checked by class and controller together.
- **Shadow Cat:** the donor's existing alternate hardpoints put the Gauss rifle
  on the left arm, matching MW3, with ER medium lasers on the right arm/torso.
  The donor's default opposite-arm Gauss arrangement was not used.

Rigid parts follow the original MW3 joint hierarchies. Existing toe pivots are
matched geometrically; Shadow Cat's right forearm follows its original arm
controller because that MW3 hierarchy has no separate right-hand joint. No
original joints, firing origins, weapon logic or animation clips were changed.
Orion's first fitted preview exposed a waist gap: its original torso/pelvis
pivots are farther apart than the donor's. Stretching only the donor's existing
upper pelvis collar closes that gap while retaining the lower pelvis and mounts.
The rejected first export is retained locally.

MW3 palette-inspired primary material drafts retain donor UVs, surface masks,
wear and normal detail. Base color, roughness, metallic and OpenGL normal maps
are prepared for all five material categories. **The native adapter currently
samples base color only.** This is not native normal-map/PBR support.

| Model | Close triangles | Distance triangles | Reduction |
| --- | ---: | ---: | ---: |
| Orion | 32,163 | 17,890 | 44.4% |
| Daishi | 36,051 | 20,613 | 42.8% |
| Shadow Cat | 18,476 | 8,924 | 51.7% |

Distance exports simplify body geometry while retaining weapon/cockpit
assemblies. Surviving original LOD controller transforms match the close model;
omitted toe controls fold into the original feet. Shadow Cat's distance hand
draw is actually named `g77`; visibility binds that observed mesh beneath
`lhand`, rather than assuming controller and mesh names are identical. These
triangle reductions are not measured frame-rate gains.

## Native execution and checks

Published executable:
`local/remaster/gpu-native-r15-next-mechs/build/entry_commandline.exe`.
SHA256: `5821edb3a58229242de320de89125afeed89519e50933e430ba1fee343ae9972`.

The host change appends six exact original mesh rosters: the new three chassis
at LOD0 and LOD1. All seven existing roster slots and the adapter logic are
retained. The 37,201 translated objects are unchanged. r14 target-marker, r12
zoom, r9 HUD, r8 codec timing and r7 performance changes remain present.

- Original-compatible Training captures match r14 **116/116**.
- Original mode-7 GPU draw frame/count/hash records match r14 **1150/1150**.
- Original-compatible Instant Action captures match r14 **116/116**.
- Every serialized close-model vertex/UV is checked against the saved fitted
  walking scene: Orion 56 samples, Daishi and Shadow Cat 57 each. All 41
  recovered source clips also pass offline transform/normal checks, including
  each chassis's actual locomotion bindings. This does not establish every live
  animation-state transition.
- A fixture includes the actual r15 adapter and all 13 replacement
  model/LOD payloads. **3,159 checks pass**, including inherited visibility,
  reactivation, exact identity/ownership,
  coexistence and 15 malformed-payload rejections. Its instance trees and
  active flags are synthetic; this is not battle-damage validation.
- Native Instant Action reaches **2,000 frames with Orion**, **2,100 with
  Shadow Cat**, and **2,600 with Daishi**, including 1,237/1,169/1,309 frames
  containing 3D respectively. Each player's exact LOD0 identity validates and
  queues replacement geometry on the GPU. The cases use all banks, FXAA,
  AF16 and 3440×1440. Exit 1 is the explicit frame-budget stop. Selected enemies
  remain outside the main view; no live enemy/LOD1 coverage is inferred.
- The living launcher freshly packs close and distance texture indices from
  the same current registered PNGs. All six resulting sidecars are byte-identical
  to the independently prepared candidate sidecars. Future texture changes
  therefore reach both distance levels on the next launch.

Evidence stays ignored under `local/work-ahead/mw3-next-mechs-r1/`, principally
`runtime-integration-r1/integration-validation.json`,
`original-regression-checks.json`, `launcher-texture-checks.json`, the retained
native runs, `weapon-fit-review-r1/motion-review.json`, and
`damage-lod-review-r1/fixture-run-r3.log`. Build/source pins are under
`local/remaster/gpu-native-r15-next-mechs/source-snapshot.json`.
The r14 launcher and model registry backups end in
`.r14-backup-20261015-next-mechs.json`.

## Remaining fidelity work

Visible muzzle alignment needs review against original firing effects. The
original weapon-origin producer also feeds collision/damage/random decisions;
it remains unchanged. Translating entire weapons to a centroid was previously
rejected because it detached them from their mounts.

The next model blocker is controlled combat inspection: visible firing origins,
per-part damage/debris breakup and actual distance switching on each new
chassis. Distance payloads have passed adapter/pose checks, but none selected
LOD1 in these bounded native cases. Initial material colors also need user
review. No completed campaign run, normal-map renderer support, or new FPS
claim follows from this batch.

Test runs use copied installations/pilots and private registry overlays. Actual
`MW3/mw34-registry.txt` and `MW3/pilots/JCB.mw3` are unchanged. Existing game
sessions and composer/watcher processes are protected. No commit was made;
proprietary assets and generated game code remain local. Acceptance is still
**131/144**, with the strict lane **paused**. No probe/fixture/preview grants
additional native acceptance credit.
