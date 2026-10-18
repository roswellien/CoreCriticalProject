# Bushwacker: Mission 3 skin D and shared shoulder correction

2026-10-17. Optional visual integration; strict acceptance remains **131/144,
paused**. Original media, generated host source and test inputs remain local.

Campaign 1 Mission 3's `bushwacker_01` is Commander Freya
(`MSG_AIV_COMMANDER_FREYA`), with original skin index 3 / variant D. The original
`readerm3.zbd` and `dfn_bushwacker.zrd` establish this mapping. Skin D has charcoal
armor, yellow/gold trim and the shark mouth. The old runtime had only the close
Bushwacker roster; the user's play log rejected the exact 13-mesh distant roster.

The native adapter now recognizes that original distance roster and binds the
approved MW5 geometry to its controllers, combining the original close model's
toe batches into the corresponding distance foot. Reference-world placement
error is below 0.0000005 model units. This distance payload currently retains the
full donor geometry; a decimated distance mesh and its performance remain future
work.

Original renderer 53F2E0 reads polygon+28 as its material pointer, material+16 as
a texture reference, and that reference+8 as a 32-byte texture name. Observed
primary and `_d` names corroborate this contract. The optional adapter selects
skin D from the validated instance's original material references, independently
per root and scene. It never substitutes a mission-wide color or modifies AI,
damage, simulation or saved skin state. Missing optional D pixels retain the
original geometry/skin. Other alternate skins have not been recreated here.

`tools/remaster-launcher/native_assets.py` packs named alternate skin sets for
both original LOD batch orders. Primary sidecar bytes remain identical for all
30 existing sidecars. `play_remaster.py` checks explicit native skin capability
and matching snapshot metadata. `apply_bushwacker_skins.py` reproduces the tested
adapter patch exactly from the validated 29-binding adapter and recovered local
distance roster; it declines an incompatible source version.

The user's subsequent shoulder observation affects the player and Freya because
they share geometry. The older fitting pass moved shoulder pivots down/outward
relative to the donor torso. Both complete arm/hand/weapon assemblies now move
about 0.630 units up, 0.329 inward and 0.094 forward, using the current original
torso frame. Existing BWMESH3 placement handles this without adding parts or
changing vertex, normal, UV, waist or leg bytes. Both close and distant payloads
receive the correction. Across 59 stored stand/walk samples, shoulder-anchor
error is at most 0.00000144 and arm/hand relative-position error 0.00000054.

Authored Freya albedos are under
`local/work-ahead/mw5-bushwacker-extract/freya-skin-d-r1/`; corrected payloads,
matched before/after renders and numeric checks are under the sibling
`shoulder-fit-r1/`. Image-generation edits preserve the established UV layout and
adapt the original skin's palette/markings with maintained-but-used wear. They
are an authored adaptation across different geometry/UVs, not a pixel-exact
original texture transfer. Normal maps remain offline/reference work; the
approved future enhanced target stays 12x equivalent.

Validation of the exact published host:

- Original-compatible Training: 116/116 framebuffer captures identical to the
  previous heap-isolated build; mode 7 GPU original draw stream: 1150/1150
  identical; Instant Action: 116/116 captures identical, with gameplay reached.
- Actual adapter fixture: 10,370,925 checks, zero failures, including existing
  chassis, cockpit, arm-damage and malformed-payload cases, and new independent
  primary/D actors at close and distant LODs. The final shoulder payloads pass.
- Copied current campaign save, selected Mission 3 through ordinary original
  menus: exact final host/payloads reach 1800 Vulkan presentations at 3440x1440,
  FXAA/16xAF, scenery1200/fog1100. Player primary close model and enemy D distant
  model both queue positive GPU geometry. A preceding skin test reaches 3000.
  Termination is the explicit frame budget, not normal quit or mission completion.
- Five positive/adverse launcher capability checks pass. Both real launch
  commands pass `--check`; full `--prepare-only` verifies the installed assets.
- Original pilot/save/registry hashes are protected by each run. No desktop
  screenshot, original-state mutation, commit or acceptance credit.

The base is photo/replay host 9b76a02c, retaining its newer controls and the heap
isolation repair. Its source had reverted to 13 bindings despite advertising
15 chassis; the previously validated full adapter is restored before this patch.
The final host has **30 bindings / 15 chassis**, plus skin D at both distances.
HUD, graphics defaults, music and all 39 texture banks remain as configured.

Published executable:
`local/remaster/gpu-native-bushwacker-skins-r1/build/entry_commandline.exe`

SHA256: `f21c0c7ef160fd41b44a0de51e2728feda8d446bc1e344b4917254f5e101f783`.

Private evidence namespace:
`C:/Users/jcbla/.codex/workspace-storage/MW34Recomp/bushwacker-c1m3-variant-r1/`.

Execution boundary advanced: live optional replacement of an original enemy's
distant chassis with its source-selected alternate skin, plus shared rigid
shoulder placement. Native game-function acceptance is unchanged. Next fidelity
checks are extended combat/effect alignment after the visual arm move, live
close-range Freya/LOD transitions and distance performance. Original simulation
firepoints remain untouched; no claim that weapon-effect alignment is completed.

Private preview folders: [Freya skin](https://drive.google.com/drive/folders/1Y8-9ybmf-8asiF63-R_wAmx3pO5Bo_5V)
and [player/Freya shoulder comparisons](https://drive.google.com/drive/folders/1U6XW9vY3z_rDk5MgArOHCCW6RTrZqmjf).

## R2: existing connectors and weapon mounts

The user's next visual review found defects missed by R1's pivot checks: the
existing shoulder connector stayed below the moved arm, and a weapon floated.
R1 is retained as historical evidence, not the current attachment fit. The
exporter had grouped `Clavicle_Left_DM0` / `Clavicle_Right_DM0` with the torso
controller, while the old geometric fitter stretched them with the upper arms.
R1 moved arm-owned batches only. Separately, the old fitter had translated five
weapon assemblies away from their MW5 mounting seats to align muzzle centroids
with original MW3 firepoints; the left forearm launcher had already been restored.

R2 separates those two existing connector groups into their own batches, undoes
their old upper-arm stretch and places their original donor shapes at the torso
mounts. Both arms move 0.22 units outward from R1, retaining its raised placement.
The five displaced weapons return to their donor seats; all six weapons retain
their assigned torso/hand owner. No joint or connector geometry is added, and
total triangle/vertex counts and all UVs are conserved. Only the connector
position/normal data and rigid placement offsets change. The approved waist,
legs and primary/Freya texture source files are unchanged. Both original LOD
bindings now use 34 batches and matching primary/D material index packs.

Current assets: `local/work-ahead/mw5-bushwacker-extract/shoulder-fit-r2-attachments/`.
The main living launcher registry selects these payloads; its native executable
remains the exact f21c0c7e host above. No host relink or game-logic changes.

New validation, distinct from the preceding host/R1 live evidence:

- Exact installed adapter with the new payloads: **10,371,197 checks, zero
  failures**. Primary and D remain isolated at both original LODs. Added checks
  exercise every arm/hand batch's individual placement through rotated parent
  transforms, including the weapon whose offset differs from its hand armor.
- Physical mesh checks across all **59 stand/walk samples**: maximum nearest
  connector-to-arm surface distance is 0.002437 left / 0.007149 right model units.
  Every weapon reaches its assigned armor within 0.002972 units at reference;
  its common rigid owner preserves that relative mount during source motion.
  These are mesh-contact diagnostics, not exact collision-volume proof.
- Restored connector bounds match the donor's torso-mounted shape within
  0.0000017 units. Both distance bindings retain close reference-world placement
  within 0.00000048 units. Matched exact-payload Blender renders inspect both
  skins from both sides, plus three walking poses; no native normal-map claim.
- A fresh live check was attempted, but the singleton refused an independently
  running native Sun-test process. It was not interrupted. Therefore the earlier
  R1 Mission 3 run does **not** establish R2 live visual/effect alignment. Fresh
  Mission 3 review, weapon effects and close-D/LOD transitions remain next.
- Both real launcher commands pass `--check`, and the main command completes
  `--prepare-only`. All 39 banks / 32 sidecars are prepared; the four installed
  Bushwacker packs match the tested 34-batch private packs byte for byte. Final
  checks conserve total vertices and every triangle's UV corner bytes, preserve
  other chassis registry entries and all ten texture source hashes, and confirm
  the protected original registry/current-pilot hashes still match the prior run.

Private tools, fixture and receipts:
`C:/Users/jcbla/.codex/workspace-storage/MW34Recomp/bushwacker-attachments-r2/`.
The acceptance count stays **131/144, paused**; no game-function boundary advanced
by this asset-only correction. Original pilots/registry and other work remain
untouched. No commit or desktop screenshot.

[R2 previews: both skins and walking](https://drive.google.com/drive/folders/1j3xrgW6env0kGbiiZZk387ZQDxTAJ8hX).
