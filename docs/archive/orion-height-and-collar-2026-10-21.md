# Orion height, blue paint and front collar

The user reported an overly tall replacement Orion, pale blue paint, and then
identified a blurry middle front torso in the first correction preview. Work
was stopped when requested. The user subsequently authorized fixing it and
installing it in-game.

## Changes

- Original standing top: 12.42886448; prior replacement top: 14.10426426 in the
  same coordinate frame. The replacement upper body now fits that original top
  using a vertical factor of 0.72186497 about the original torso pivot. Legs,
  arms, source joint/controller locations and prior arm/missile alignment are
  preserved. This is a visual silhouette fit, not a claim of identical donor
  anatomy or altered original gameplay.
- The Body atlas's existing blue paint is stronger. Source-selected blue pixels
  change from median RGB (123,140,147) to (55,115,161); other material atlases and
  existing normal sources are retained. Image generation edited the color atlas;
  exact pixel preservation of every unpainted area is not claimed.
- The old upper pelvis/collar fit stretches donor geometry by about 2.546, while
  some front faces sample only roughly 35–40 atlas pixels. Merely recoloring or
  enlarging the old image did not resolve that low texture density. A dedicated
  sharp `Collar` material now serves the main front shell, inset and raised
  center plate. Its color detail was authored against the source normal guide.
  The main normal region is sampled in numeric Raw mode; small central plates
  reuse a sharp blue region in the same matched color/normal atlas.
- Material splitting/rebinding affects 242 close and 110 distant triangles.
  Position/normal records, owners, visibility and triangle counts are preserved
  across this UV/material change. Close/distant batch counts are 33/23.

## Installation and evidence

Ignored workspace: `local/work-ahead/orion-fit-color-20261021/`.
Selected geometry is in `final-assets-r7/`, material sidecars in `prepared-r7/`.
The normal and base model registries reference the new geometry/materials.
Explicit Orion runtime paths in the normal launcher and material profile also
reference these prepared resources: profile runtime bindings otherwise overwrite
the staging environment. The previous Annihilator neck repair's explicit paths
were corrected at the same boundary so its registered covers actually persist
through normal launch. Other model records and graphics choices are preserved;
installation preimages and hashes are retained locally.

Private native checks under
`C:/Users/jcbla/MW34SunTests/mech-evolution-series-20261020/orion/`:

- `fit-original-reference-r4`: matching original standing reference, expected
  1160-frame stop.
- `collar-final-r6`: four-angle silhouette/material inspection. Its close view
  exposed another small low-density center plate, addressed in R7.
- `collar-final-r7`: final full and close front views, expected 1260-frame stop.
  Close inspection confirms the former blurry center surfaces now resolve paint,
  seams and scratches. Both LOD meshes and material-name normal bindings load.
- `fit-color-motion-r7`: original scripted movement/turn route followed by front
  and side inspection, expected 1810-frame stop. No gross attachment separation
  was observed in these sampled poses. This is not exhaustive animation QA.

Registered Orion asset preparation and normal/original-model launcher checks
pass. Distant material resources load but a new distant visual capture, full
combat/damage checks and exhaustive silhouette matching remain open. The separate
material-preview profile retains its previously identified executable validation
pin issue; its asset bindings were updated without bypassing that validation.

Execution boundary advanced: corrected optional Orion assets now resolve for the
existing native renderer and normal launcher. Strict acceptance remains 131/144.
No renderer binary, simulation, pilot/save or gameplay-controller change, no
commit, no video rerender and no Drive/YouTube update was performed.

## Authorized video follow-up

Later on 2026-10-21, after approving the in-game repair, the user requested a new
Orion video. A fresh corrected 720-degree pass was captured at the same Grasslands
spawn and sunset settings. The original 360-degree comparison passes, approved
10-second opening and MW3 audio were retained. Both 1440p60 local master and
1080p60 Drive copy decode fully at 6361 frames / 106.016667 seconds. Transition
and endpoint contact views were inspected. The thumbnail now shows the corrected
model and blue paint, with ground markers removed; the description records the
revision. Title and keywords are retained.

Outputs: `reports/orion-evolution-corrected-20261021/orion/`. The existing Drive
video, two thumbnails and description were replaced in place; readback verifies
all six package filenames, unique IDs and exact local/remote sizes in
`reports/orion-evolution-corrected-20261021/Drive-delivery.json`. No ZIP, YouTube
publication, proprietary source upload or commit was performed.
