# Orion and Annihilator visual forearm alignment

The announcement captures exposed two real imported-model pose defects: Orion
and Annihilator pointed their arm weapons upward during an ordinary standing
pose. This advances the native model-binding boundary only. Original simulation,
joint animation, weapon origins, damage rules and AI are unchanged. Strict
acceptance remains 131/144; this work grants no additional acceptance credit.

## Diagnosis and correction

- Orion uses the older rigid BWMESH2 payload. Its forearm export retained donor
  weapon axes instead of the original hand-local firing axis. A native original-
  geometry comparison confirms that the original standing weapons point forward.
  Twenty individually measured missile cones agree on the bore direction. Pure
  rotations of about 52.70 degrees left and 51.13 degrees right correct forearm
  vertices and normals around the existing hand pivots. Other vertices, batch
  headers, UVs, visibility and texture bindings remain unchanged.
- Annihilator uses BWMESH4. Its donor forearm rest directions differ from the
  original standing reference firing directions by about 55.46 and 57.35 degrees.
  Correcting each forearm's rest matrix, including its dependent hand and damage
  bones, fixes this neutral-reference mismatch. Elbow positions, original
  reference matrices and every vertex-payload byte remain unchanged.
- The other inspected newer donor rigs do not share Annihilator's large mismatch;
  their measured arm-axis differences are approximately zero to two degrees.
  No blanket correction was applied.

Both close and distance payloads are corrected. These are separate local asset
revisions; the previous payloads are retained. Both the material-preview registry
and the main model registry now point to the corrected assets and updated batch
metadata. Unrelated chassis entries and all albedo/normal-map registrations were
preserved, including concurrent joint-fitting work.

## Local evidence

The private capture host is `ac21b64ab89b5aea9a6c525f9347ed6f6dce885777fc8c1dc9ee4cce64fbb789`.
It adds camera/hotkey automation only; no gameplay or renderer change is needed
for these asset corrections.

- Orion correction and asset hashes:
  `C:/Users/jcbla/MW34SunTests/orion-arm-alignment-20261019/correction.json`.
- Annihilator correction and asset hashes:
  `C:/Users/jcbla/MW34SunTests/annihilator-arm-alignment-20261019/correction.json`.
- Registry backups and publication receipt:
  `C:/Users/jcbla/MW34SunTests/arm-alignment-install-20261019/installation.json`.
- Native front/side comparisons:
  `C:/Users/jcbla/MW34SunTests/announcement-captures-20261019/orion-corrected-arm-comparison`
  and `annihilator-corrected-arm-comparison` beneath the same capture root.
- Orion movement check: `orion-corrected-motion-check` beneath that root. The
  original player moves approximately 50 metres and the arms remain forward.
- Annihilator movement check: `fixed-facing-annihilator-3` beneath that root.
  The corrected arms remain forward after walking in Gorge. A separate static
  retake supplies the gallery image because the moving view retained a distracting
  original unit marker above the mech.

Both native comparison runs reached their explicit presentation budgets and
their clean front/side screenshots were visually reviewed. Offline checks verify
pure rotations, preserved pivots, unchanged non-forearm data and both LOD payloads.
The material-preview launcher's prepare-only check succeeds with all 15 chassis
and 39 texture banks. The main launcher's checked plan resolves both corrected
close/distance bindings while preserving its concurrent joint-fitting revisions.
Full combat, damage/detachment sequences and exact rendered-muzzle-to-gameplay-
origin fitting have not been established by these checks. Scripted fire input
alone is not evidence of a verified combat sequence.

## Gallery status

The corrected Orion and Annihilator front, 100-degree side and elevated head-on
views were visually reviewed and uploaded across two environments per chassis.
Orion's three existing Drive files were replaced in place. The hold labels were
removed after replacement; the earlier broken captures remain local evidence.

The full material-preview gallery now contains three PNGs per chassis across
15 folders, verified by Drive readback (45 images total). Local exports, exact
source hashes, lighting/view settings and the Drive readback receipt are under
`reports/mech-gallery-facing-20261019`. Private review:
https://drive.google.com/drive/folders/1jwO2_iNAH4mKdKMZ5_5LU0KVnQuLG2zR

The separate Mad Cat/Bushwacker/Vulture joint-fitting lane is producing newer
geometry and a newer host. This capture pass records the material-preview
bindings used by each run; it must not be described as proof of every subsequent
joint-fitting revision. Refresh those chassis after that lane's integration is
settled.

Nothing was committed or publicly published. Game assets, generated payloads and
capture automation remain local.
