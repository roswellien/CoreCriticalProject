# Annihilator missing neck covers

The user identified an open neck and an apparently disconnected block after the
2026-10-20 cockpit/height repair. That repair did not restore the missing neck
armor. A raw body-only MW5 decode also has this gap: the necessary covers are
separate hardpoint visuals, not part of `Annihilator_SKM`.

## Source and cause

The `MWMechDataAsset` export of `ANH-1A_MDA` explicitly lists
`Torso_Left_GB1_blank` and `Torso_Right_GB1_blank` under
`Properties.MechData.BlankWeaponHardPoints`. `Annihilator_HPS` maps their
`None` visuals to the corresponding `Weapon_Mech_ANH_Torso_*_GB1_Blank`
blueprints on `Torso_Weapon`. Those blueprints reference skeletal cover meshes.
The original local assembler enumerated installed weapons only, omitting these
variant-defined blank parts. Its body bounds checks could not detect the loss.
The exposed central block includes the existing center laser mount; it did not
require an invented connector or relocation.

## Repair and execution boundary

Restored both source cover meshes using the original socket/bone frame and Body
material/UVs. Appended two batches, 224 triangles total, to each existing native
payload. Existing batches, rig/reference bytes, cockpit geometry, height fit and
forearm alignment remain byte-identical; only the batch count and appended data
change. Maximum reconstructed attachment error is below 0.000001 world units.
The local source preparation now includes explicit `BlankWeaponHardPoints` for
future assemblies. This advances optional replacement-asset completeness only;
gameplay/controllers and native acceptance remain unchanged at 131/144.

Assets, attachment source, export script and installation preimages are local:
`local/work-ahead/annihilator-neck-review-20261021/`. The normal and material
registries now select its corrected `assets/` files. Renderer/profile graphics
settings were not changed. Original media remains local; no commit was made.

## Validation and limits

- Separate full asset preparation succeeds (18 models, 39 banks), including the
  corrected base-color and normal-map bindings. Main and original-model launcher
  checks pass.
- Native sunset front, left, rear and right views were captured and inspected in
  `C:/Users/jcbla/MW34SunTests/mech-evolution-series-2-20261020-r2/annihilator/neck-framing-r3/`.
  The run reaches its expected 1636-frame stop. Both LOD normal resources load;
  close-view torso submission includes the two new cover batches. The distant
  LOD has the same added source geometry but no new distant visual capture.
- The separate material-preview profile check reports a stale executable
  validation pin. It was not silently updated; this does not prevent the main
  launcher check or the completed native candidate capture.
- Existing video exports and Drive files have not been rerendered for this neck
  correction. Full combat/damage and every donor-model assembly remain outside
  this narrow check.
