# Textured Avatar connected to Remaster

2026-10-19. The user approved texturing and installing the corrected R3 Avatar.
The standard Play MW3Remaster launcher now registers 16 replacement chassis,
including this detailed original-Avatar / STL-guided candidate. The material
preview profile uses the same geometry. This supersedes R1-R3's offline-only
status for the R4 candidate; those earlier scenes remain preserved.

## Artwork and geometry

Retained the MW3 white/blue primary design. All 25 source body color tiles remain
pixel-identical, with 27,236 original body UV corners unchanged. New cockpit,
armor trim, bearings and mechanical covers have separate fitted textures with
paint scarring, exposed metal, localized impact soot and shallow surface wear.
The first whole-body atlas softened existing detail and was rejected; the final
version preserves source body mapping and bakes only the authored additions.

The original 10.20-strength Blender normal shader, representing the selected
12x target, is baked into material tangent maps for native strength 1. The 45
material slots have 43 normal bindings and two explicit smooth glazing
exceptions. Corrected a shared image-name collision between glazing and armor
before installation. Native and Blender lighting are distinct; this is not a
pixel-equivalence claim or a change to other models' normal calibration.

R3 positions, topology, parents, limb matrices and hip-cover seating are retained:
36,038 triangles and 19 source-owned moving parts. All 336 checked controller
poses retain the exported bindings, maximum matrix error 0.000001430512. No new
game joint, changed gameplay skeleton or revival of the old STL leg rig.

## Native registration and current build

`local/remaster/gpu-native-avatar-r1/build/entry_commandline.exe`, SHA256
`a0cefef77b355cff2c160694738f0f1e7249217fc3d26a275d6cd0f32c07140b`.

Preserves the latest integrated lighting host observed during this work, SHA256
`8fce991dfd490fb0c1210d17e6673fec33baee882c53c2ba8af1c332912b0c27`.
Four independently updated lighting files were merged before final validation;
the older initially copied host was not published over that update.

Local host changes add two optional Avatar entries to `mesh_override_stage.inc`
(32 bindings), exact close/distance signatures in `override_avatar_rosters.inc`
(19/13 source meshes), and four original arm-stump alternatives in
`override_arm_damage_plans.inc` (62 plans). BWMESH2 retains original control
ownership, visibility and source LOD choice. Both distances currently retain
the full 36,038 triangles; distance geometry optimization remains open.

Both live model registries append Avatar while retaining the other 15 records.
Both launcher profiles point at the new host and matching source snapshot.
Existing resolution, AA/AF, lighting, banks, music and original-model option
remain. The root launcher reads the current registrations on each launch.
Assets and packed scene: `local/work-ahead/mw3-avatar-native-r4/`.

## Validation and limits

- Latest-host original-compatible comparisons: Training CPU 116/116 frames,
  mode 7 GPU draw stream 1,150/1,150 records, IA 116/116 frames identical.
- Actual compiled adapter: 3,850 checks, zero failures. Both payloads, exact
  roster rejection, material-name normals, glazing exceptions, resident GPU
  emission, CPU/near clipping, inactive arms and all six arm-loss cases pass.
  Adapter emission leaves fixture guest bytes unchanged.
- Actual native IA player run: 2,500 frames through Vulkan at 3440x1440, AA/AF
  off, live movement/firing and positive Avatar GPU geometry; both normal
  sidecars loaded. A presentation-budget exit is not mission completion.
- Saved-scene checks retain geometry and body UVs; 25 tile pixel comparisons
  and the 112-frame, 30 fps HQ walking review pass. Native stills are full
  render-target captures, not desktop screenshots. The external follow camera
  crops lower geometry in these native frames.
- Actual root launcher preparation/check passes with all 16 registrations;
  the without-new-models launcher selects original geometry. Material-preview
  preparation also passes with all 16, including current Avatar normal sidecars.

Live NPC distance transitions, full destruction/debris, precise muzzle
presentation, extended play and performance remain open. No FPS claim is made
from scripted virtual-clock checks. The model retains its runtime-candidate
label. Only source color/normal channels are installed; Blender material
roughness is not a new per-material native shading feature.

[Organized R4 previews and notes](https://drive.google.com/drive/folders/1ehw7gEs1UB3KMW3zFCjHaN59CDevShW_),
[textured walking review](https://drive.google.com/file/d/1J4qprje8cEPBlcTWi6wMQgy_xFTQtHvr/view?usp=drivesdk),
[native frame](https://drive.google.com/file/d/1Lla6oziO0XHvudiP-yjblmWPnR_U8PNH/view?usp=drivesdk).
Only rendered media and notes are uploaded. Raw source assets remain local;
sharing is unchanged. Private scripts, rejected attempts and receipts:
`C:/Users/jcbla/.codex/workspace-storage/MW34Recomp/avatar-native-20261019-r4/`.

Boundary advanced: offline Avatar candidate -> registered native visual
replacement in live IA -> living launcher asset preparation. Original gameplay
remains in control. Test games used private copies/overlays; existing games and
protected jobs were preserved. No desktop screenshots, original registry/pilot
writes or commit. Strict acceptance remains paused at 131/144; no new accepted
function credit. Next asset blocker is the remaining original Firefly/Owens
geometry work, alongside the listed Avatar gameplay validation limits.
