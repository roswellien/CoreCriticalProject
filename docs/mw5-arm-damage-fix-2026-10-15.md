# MW5 port damage and distance follow-up — October 15

The Remaster launcher now selects **r17**. Orion keeps its surviving MW5 body
parts after the original game removes its right arm. Previously the replacement
adapter rejected the changed hierarchy and restored the entire original
low-detail mech. The seven registered models, texture registrations, HUD,
music, 3440×1440, FXAA and 16× AF remain configured; Avatar remains excluded.

[Before/after native captures on Drive](https://drive.google.com/drive/folders/1kFyI-2o9xhTNzXER01hkRHoYIQb1hIVP).
The comparison uses the same battle and frame 4800. These are native target
dumps, not desktop screenshots. The local gallery is
`local/work-ahead/mw3-next-mechs-r1/combat-review-r1/comparison.html`.

## Actual defect and correction

A 6,500-frame Instant Action case uses ordinary original menu/input commands
to select Orion against Daishi, approach, turn and fire. At frame **4414**, the
original game destroys Orion's right arm. Its `rarm` and `rhand` mesh entries
are replaced by `rarm_stub01`. r15's intact-only identity check rejects this
otherwise valid surviving chassis; the frame-4800 capture shows the original
MW3 geometry instead of the port.

Original producer **461D80** supplies the contract. It clones the source stump
prototype, renames the meshless root to the lost arm's name, removes the old
limb subtree, and attaches the new root to the same original parent. The
result is `torso → meshless rarm/larm → stump mesh`. The detached original
subtree continues into the game's original debris handling.

The r17 matcher admits only complete source-defined alternatives: intact,
left arm lost, right arm lost, or both arms lost. It verifies every surviving
mesh name/count, the exact removed subtree, the renamed meshless root with
one stump child beneath `torso`, and the stump's 23 vertices, 19 polygons,
zero normals and original XYZ byte fingerprint. The same source stump vertex
bytes occur in all six scenario archives. A missing piece alone, an unknown
addition, a wrong stump count/polygon count, or changed stump vertex bits
does not qualify.

The adapter marks absent arm meshes inactive in host-owned display state and
continues replacing the surviving body parts. Original stump and debris
geometry keeps its original drawing path. There are no guest writes, damage
overrides, new original-function calls, changed firing origins or invented
destruction events. The matching plans cover all 13 registered model/LOD
rosters; runtime observation in this pass covers Orion's right arm at LOD0.

Authored helper: `tools/remaster-launcher/model_arm_damage.inc`. The private
host adds its include and checked damage plans in `mesh_override_stage.inc`.
Original source recovery, archive hashes, exact arm rosters and retained
failed/earlier attempts remain ignored under
`local/work-ahead/mw3-next-mechs-r1/combat-review-r1/damage-source`.

## Validation and execution reached

Published executable:
`local/remaster/gpu-native-r17-arm-damage/build/entry_commandline.exe`.
SHA256: `fff729b286da537828908eff4e28a3852f46f61a7a87861d1146ae99017cb044`.
It retains all **37,201** translated objects and the r15/r14/r12/r9 HUD,
r8 codec and r7 performance work. Source pins are in the build's
`source-snapshot.json`; the r15 profile backup is
`local/remaster/launcher.r15-backup-20261015-arm-damage.json`.

- The same **6,500-frame native battle**, including 5,737 frames containing
  3D, reproduces the original right-arm loss at **4414**. r17 has no whole-model
  rejection, emits no missing right-arm/hand batches after the loss, and keeps
  surviving replacement draws through sampled frame 6400. Original frame,
  draw-count and draw-hash records match r15 **6500/6500**.
- Original-compatible Training captures match r15 **116/116**; mode-7 original
  GPU draw records match **1150/1150**; Instant Action captures match **116/116**.
  Exit 1 in these runs is the explicit frame-budget stop.
- The actual adapter fixture passes **3,454 checks** across 13 model/LOD
  payloads, 39 synthetic arm-loss states and 15 malformed payload streams,
  including wrong source-stump geometry rejection. Synthetic cases are not
  additional live limb-loss evidence.
- Separate native camera sweeps draw the new **Daishi, Orion and Shadow Cat
  LOD1** variants. This establishes actual lower-detail drawing, beyond the
  prior offline checks. Both transition directions on the same actor remain
  unproved; they are not inferred from separate runs.

The evidence receipt is
`local/work-ahead/mw3-next-mechs-r1/combat-review-r1/validation.json`.
No test was launched over an existing game: one guard refusal was retained
when another transient native process was present, and testing resumed after
it ended. Tests use copied installations/pilots and private registry overlays;
the installed pilot and registry hashes are unchanged.

## Muzzle investigation and remaining work

An isolated **r16 observation build**, not selected by the launcher, links
eight actual Orion LOD0 beam draws to the live right-hand weapon/controller
and exact original `firepoint02` position bits. All 6,500 original draw records
and three matched native captures remain identical with observation enabled.
This establishes a concrete live association; **no visual muzzle correction
is implemented** and no flash draw was established.

The original beam layouts require care: for ordinary lasers, descriptor `+48`
is an endpoint; `+54/+60` can be zero. The previously documented full segment
origin/direction/length tuple belongs to another source branch. The dated
correction and retained evidence are under `weapon-effects-r1`. A future
adapter must move only the displayed near endpoint while preserving the
original hit endpoint, materials, clipping and lifetime. Simulation origins
remain protected.

Next boundaries are the scoped beam/flash drawing correction, other live arm
loss cases, leg/torso destruction, converted debris and both distance-transition
directions. Original stump/debris remain visually original, normal maps remain
offline, and no new frame-rate or campaign-completion claim is made.

Acceptance remains **131/144**, strict lane **paused**. No commit, desktop
screenshot, original save/registry edit, acceptance run or composer intervention
was performed. Proprietary models and generated game code stay local; Drive
contains requested private previews only.
