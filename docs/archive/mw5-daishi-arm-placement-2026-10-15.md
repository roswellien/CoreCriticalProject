# Daishi: raise and tuck the complete arms

The user accepted the leg/waist fit but rejected the elongated shoulder
connectors in R2. R3 restores the original donor shoulder connector shape and
moves each complete arm upward and inward to its MW5 shoulder attachment.
The arms, forearms and weapons retain their existing mesh shape. The accepted
legs and waist are byte-identical to R2; 38 of 39 close-detail draw groups are
unchanged. Only the torso group's stretched clavicle surfaces are restored.

The current Remaster executable is
`local/remaster/gpu-native-daishi-arms-r1/build/entry_commandline.exe`, SHA256
`11ce36987b79a26a675015689f53561e307953633ae9fdb83773f3dcffaa47df`.
It is based on the then-current scenery-distance build, SHA256
`e95305b22aba43e44e6cb8663405d7580f1be6ec894938f2b54ba1628b1a23cd`.
Only `host-source/mesh_override_stage.inc` differs in the private host source;
the translated object list and all other host sources are retained.
Current 3440x1440, FXAA, AF16, configured 1600-unit scenery range, seven models,
39 texture banks, HUD and music settings are preserved.

## Placement and execution boundary

The donor shoulder centers, transformed by the existing torso fit, supply the
placement. Each arm moves about 1.26 model units upward and 0.37 inward, with
the source-derived fore/aft correction. The entire upper-arm/forearm/weapon
branch receives the same translation. Restoring the original clavicle shape
eliminates the elongated connection used in the rejected R2 preview.

Baking this translation separately into each arm/hand mesh would make it rotate
around different old pivots and could reopen the elbow/shoulder connections.
The renderer instead applies the displacement in that actor's current torso
frame after original limb animation. It recovers the ancestor camera basis
through the exact current source hierarchy. GPU instances, conservative near
clipping and the CPU projection path use the same placed camera transform.
Original animation, aiming, damage, weapon simulation and firing origins are
unchanged. Visible muzzle presentation remains separate unfinished work.

`BWMESH3` adds a placement-frame name and three floats to each batch after its
owner/visibility fields. V1/V2 keep their prior paths. Unknown frames, invalid
names, nonfinite offsets, offsets without a frame, and invalid ancestry fail
visibly. This is compiled host rendering code, not an interpreter or an
original-code fallback. The launcher checks the model's required mesh format
against the published host capabilities before preparation/launch.

## Validation

- Training software frames: **116/116 identical** to the retained baseline.
- Mode7 original GPU draw records: **1150/1150 identical**.
- Instant Action software frames: **116/116 identical**.
- Updated Daishi native case: **2600/2600 original draw records identical** to
  R2; corrected geometry queued without rejection at 3440x1440, FXAA and AF16.
  This case uses default 800-unit scenery for a matched comparison; it does not
  independently repeat the existing 1600/3200-unit scenery validation.
- Actual-adapter fixture: **3880 checks, zero failures**, including legacy
  payloads, close/distance V3 payloads, source visibility/damage alternatives,
  rotated torso/arm/hand ancestry, GPU/CPU emission and malformed placements.
- All 13 recovered Daishi clips pass serialized mesh/normal checks at both
  detail levels. All 57 saved walking samples match actual V3 placement within
  0.00000124 model units; preview/runtime disagreement is bounded numerically.

The initial software Training smoke explicitly disabled frame dumps and supplied
no frame-equality evidence; the retained `TrainingCpu-frames` rerun supplies the
116-frame comparison above. Budget exit 1 is expected for all bounded cases.
Actual registry and pilot hashes remain unchanged. Full campaign/damage,
both live LOD transition directions, native normal maps and muzzle correction
remain open. Acceptance remains **131/144**, strict lane paused. No commit.

## Assets, launcher and previews

The living launcher uses R3 close/distance meshes under
`local/work-ahead/mw3-next-mechs-r1/daishi-arm-placement-r3/`. Other six model
records are unchanged. Host/profile and model registry backups are
`local/remaster/launcher.before-daishi-arms-r3.json` and
`local/remaster/models.before-daishi-arms-r3.json`.
Both actual launcher registration and preparation checks pass.

Private [R3 comparison and walking previews](https://drive.google.com/drive/folders/1EqJGX3IZ6X7oFQMV5v3L2zdlkA1o3hUw)
show the donor, rejected R2 shoulder fit and raised/tucked R3 assembly. Earlier
R2 previews remain as rejected evidence. The [previous fitting record](mw5-fit-corrections-2026-10-15.md)
retains the accepted leg/waist work and its limits.

Local receipts include `geometry-checks.json`, `pose-placement-checks.json`,
`motion-review.json`, `distance-motion-checks.json`, `native-validation.json`,
`publication.json`, `drive-previews.json`, the fixture log and the published
host's `source-snapshot.json`.
