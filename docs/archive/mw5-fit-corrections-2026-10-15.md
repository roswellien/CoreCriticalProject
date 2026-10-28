# Daishi waist and Shadow Cat thigh fitting

**Current Daishi arms:** the user accepted R2's legs/waist and rejected its
elongated shoulder fit. R3 restores the donor shoulder shapes and moves complete
arms up/in, with placement following the current torso frame. This needs the
new compatible host based on the existing scenery-distance build. The accepted
legs/waist and other six model records are retained. See
[R3 placement, tests and previews](mw5-daishi-arm-placement-2026-10-15.md).

The user identified a separated Daishi waist and excessive outward Shadow Cat
upper-leg angle in the first port previews. Comparing both original MW3 and
decoded MW5 models confirmed these were fitting defects. This correction changes
the optional visual assets; the native host and original animation/gameplay code
are unchanged.

## R2 Daishi revision: accepted legs/waist, rejected shoulder fit

The user found that the first central-collar correction still left separated
side hip and shoulder connections. That earlier Daishi fit is superseded by
`local/work-ahead/mw3-next-mechs-r1/daishi-joint-fix-r2/`; Shadow Cat retains the
vertical-thigh correction below. The current model registry points to both
corrected Daishi detail levels.

The decoded donor hierarchy assigns `Hip_Left/Right` to the pelvis and
`Clavicle_Left/Right` to the torso branch. The previous helper aliases instead
assigned them to the moving thighs/upper arms. Correct those four connector
owners and fit their existing geometry from the parent contact into the original
child joint center. The upper pelvis collar correction remains. No joint or
filler mesh is added. Original limb pivots, weapon/cockpit geometry, UVs and
animation are retained; all 22 weapon/cockpit draw groups are byte-identical.
Close geometry remains 36,051 triangles; the regenerated distance mesh has
20,612 triangles.

All 13 recovered Daishi clips pass serialization/normal checks at both detail
levels. Attachment centers were measured over 563 samples: shoulder deviation
is below 0.0000011 model units; hip deviation reaches 0.0023812 because original
thigh translations vary slightly between samples. This residual is recorded,
not described as exact animated coincidence. Stand endpoints coincide, and
the front/side/three-quarter and walking renders were reviewed separately.
The actual unchanged r17 adapter fixture passes 3,454 checks with the new
payloads. A further native 2,600-frame copied-install run queues corrected
Daishi geometry without rejection; all 2,600 original draw records match the
earlier case. Protected originals remain unchanged; budget exit 1 is expected.

Only the Daishi registration changes in this second revision. The other six
model records and the then-current launcher profile/executable are retained;
the previous registry is backed up as
`local/remaster/models.r17-backup-20261015-daishi-joints-r2.json`.
Both actual launcher preparation and registration checks pass.
[Current R2 source comparison and walking previews](https://drive.google.com/drive/folders/1R9Nk5qFlvxZ3ncd9QVnrNilQDvzzf4sx)
supersede the earlier central-only Daishi previews. Full damage and both live
distance-transition directions remain unvalidated for these changed connectors.

## Geometry correction

Daishi's donor pelvis-to-torso pivot interval is 0.9203 model units; MW3's is
1.4995. Independent translation of the two parts left the original donor collar
too short. Fit its existing upper pelvis vertices across that interval, using
the inverse-transpose transform for normals. The lower pelvis stays in place;
no replacement joint or new geometry was added. Only one of 39 close-detail
draw groups changes.

Shadow Cat's MW3 thigh pivot sits inboard of the visible hip/upper-leg axis.
The earlier fitter aligned the donor thigh to the pivot-to-knee vector, adding
about 41 degrees of outward angle in the front view. Both original source
meshes have nearly vertical upper legs in that view. The corrected visual fit
places each upper-leg axis over its knee, while retaining the exact original
animation pivot and knee endpoint. Both emitted knee endpoint errors are below
0.0000003 model units. Only the two thigh groups change; the other 21 close
draw groups remain byte-identical.

All close-detail UVs, original mesh rosters, joint/toe bindings and weapon/muzzle
placements remain unchanged. Updated distance geometry is generated from the
corrected close geometry using the existing body-only simplifier. Triangle
counts remain Daishi 36,051/20,613 and Shadow Cat 18,476/8,924 for close/distance.

## Validation and delivery

All 27 recovered Daishi/Shadow Cat clips pass serialized vertex, normal and
controller-transform checks at both close and distance detail. The actual r17
adapter fixture passes 3,454 checks
with the corrected close/distance payloads, including intact trees, visibility,
synthetic arm-loss alternatives and malformed-payload rejection. Offline and
fixture checks are not full live animation or damage acceptance.

Private correction sources, payloads, source comparisons and walking previews
are under `local/work-ahead/mw3-next-mechs-r1/fit-corrections-r1/`. The prior
revision is retained. Private Drive review folders contain the MW3/MW5 source
comparison, previous/corrected front views, three-quarter view and an animated
original-MW3 walking cycle:

- [Shadow Cat thigh correction](https://drive.google.com/drive/folders/1AC-hNsJlTxrB4vfbb2CgJDKMmgU73ptr)
- [Daishi waist correction](https://drive.google.com/drive/folders/14dTaCSMEAncg8gwJPU0NmFCO4zmz7361)

The unchanged published r17 executable was exercised in two native copied-install
Instant Action cases at 3440x1440, FXAA and 16x AF. Daishi ran for 2,600 frames
(1,309 with 3D); Shadow Cat for 2,100 (1,169 with 3D). Both corrected player
models queued GPU replacement geometry with no identity rejection. All 4,700
original frame/count/hash draw records match their corresponding retained r15
runs. Both tests ended at the intentional frame budget, exit 1. Actual user
registry/pilot hashes were unchanged. These runs do not establish complete
mission, damage or distance-transition coverage.

The living launcher now registers the corrected close/distance meshes and
metadata. Its profile/executable and the other five model registrations are
unchanged. The previous model registry is retained as
`local/remaster/models.r17-backup-20261015-fit-corrections.json`.
The actual launcher `--check` and `--prepare-only` pass with seven models and
39 texture banks. Local evidence includes `geometry-checks.json`,
`motion-review.json`, `distance-motion-checks.json`, `native-validation.json`,
the adapter fixture log, `published-assets.json` and verified
`drive-previews.json` in the correction folder. Original Training/GPU/IA
regression results remain those of the unchanged r17 executable; this asset
correction did not rerun those unrelated suites.

Normal-map rendering, remaining damage/debris,
muzzle presentation and complete live distance transitions remain separate
work. Acceptance stays **131/144**, strict lane paused. No commit.
