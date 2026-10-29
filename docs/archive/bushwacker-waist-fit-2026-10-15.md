# Bushwacker waist fit correction

The user reported a waist gap both at rest and in motion. Inspection of the
registered native mesh confirmed a physical separation, independent of the
recent R7 worn textures. The standing pelvis top was 0.139269 model units below
the lowest main-torso surface; the two surfaces had no triangle intersections.

## Cause and correction

The original donor-to-MW3 fitting translated the pelvis and torso separately.
The donor pivot interval was 0.398524 units; the original MW3 interval is
0.695234 units, including 0.294531 extra vertical separation. The existing
pelvis connector had retained its donor height.

Fit the existing upper pelvis over this interval. A clamped displacement ramp
leaves everything below the hip plane fixed, extends the region between the
donor hip and torso planes, and translates the upper contact region by the same
offset as the torso. This preserves the donor's upper contact shape and overlap
instead of stretching it beyond the joint interval. Normals use the inverse
transpose of the local deformation. Original MW3 controller pivots and motion
remain authoritative.

Only batch 0, the existing Body material on the hip controller, changes:
4,025 of its 6,804 triangle corners move, by at most 0.299622 units. All other
31 batches are byte-identical. There are still 34,438 triangles, the same batch
headers, and identical UVs. No joint or filler geometry is added. Lower pelvis,
legs, upper torso, cockpit and weapon placements remain as before. All R7
texture sources and the prepared material sidecars are retained.

The isolated local revision is
`local/work-ahead/mw5-bushwacker-extract/waist-fit-r1/`. The original serialized
mesh remains at `live-pose-r1/bushwacker-native-test.bin` for rollback. The new
mesh is `waist-fit-r1/bushwacker-native-waist.bin`, SHA-256
`f60554e5853874b140c7cb915fc7a1f17e1e6ba90b0c916b05a544a28a05e982`.

## Validation and execution boundary

- Check all 607 samples of the 14 recovered original clips for finite native
  coordinates and valid normals. Coordinate round-trip error is below
  0.0000015 model units. No nondegenerate triangle collapses or inverts.
- The pelvis and main torso retain physical surface contact in all 294 standing
  and locomotion samples (stand, walk, run, trot, step, limp and backward limp).
  The standing surfaces now overlap vertically by 0.155262 model units.
- Thirteen synthetic torso-yaw poses, every 15 degrees from -90 to +90, retain
  contact. These are offline stress poses, not recorded gameplay.
- The existing actual-adapter fixture, compiled against the currently registered
  fog-fixed native host and supplied the new mesh and current worn sidecar,
  passes **3,880 checks with zero failures**. It exercises legacy V1 emission,
  controller identity, repeated draws, other model formats and rejected payloads.
- Matched front, rear, side, full, walk and synthetic turn renders use the exact
  serialized native batches. The walking comparison uses the original MW3 walk
  matrices. R7 worn albedo is retained; these are offline renders, not game captures.

`local/remaster/models.json` now selects the new Bushwacker mesh and matching
batch metadata. The other six model records, all texture registrations and the
native executable/profile are retained. Rollback registry and publication
receipts are in the revision's `before/` and JSON files. The actual root
`Play MW3Remaster.cmd --prepare-only` path verifies preparation without starting
the game; the publication check compares all prepared material sidecars to
their previous bytes.

This advances optional visual-asset delivery only. No new guest/game execution
boundary or acceptance credit is claimed. The game was not launched, and this
change does not establish live visual or performance results. Existing V1
Bushwacker component-damage and fitting limits remain. Strict acceptance stays
paused at **131/144**. No protected registry/pilot files or original media are
modified; no commit is made.

[Before/after stills and walking preview on private Drive](https://drive.google.com/drive/folders/1_CBZecIqQsQJXzAQVkge_OskM1cPhaZ-).
