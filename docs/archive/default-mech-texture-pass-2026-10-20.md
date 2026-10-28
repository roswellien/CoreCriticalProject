# Default mech texture pass — 2026-10-20

Audited the default material sets for all 18 represented MW3 chassis. Six sets
needed further work; twelve already had detailed worn art and were retained.
The revised defaults are installed in both local model registries and the two
original-model texture banks. Alternate-skin registrations and their separate
replacement textures are unchanged. This advances asset selection and packing;
it adds no native gameplay or acceptance credit. **131/144; strict acceptance
remains paused.** No commit was made.

## Art and resolution

The maintained-but-used treatment keeps most paint intact. It adds directional
cuts through paint into dark metal with narrow brighter cores, contact rubs,
irregular edge chips, seam dirt and localized heat/scorch marks. Large armor
faces stay relatively calm. Existing default palettes and markings, including
the Bushwacker mouth, are retained. Normal-map images, strengths, geometry,
UVs, animation, attachment repairs and LOD registrations are unchanged.

| Chassis | Result |
|---|---|
| Bushwacker | Existing worn set retained |
| Mad Cat | Existing worn set retained |
| Vulture | Existing revised worn set retained |
| Thor | Existing revised worn set retained |
| Orion | Existing worn set retained |
| Daishi | Body/variant reauthored; formerly uniform weapon material replaced |
| Shadow Cat | Body/variant reauthored; formerly uniform weapon material replaced |
| Puma / Adder | Existing worn set retained |
| Annihilator | Existing worn set retained |
| Cauldron-Born / Ebon Jaguar | Existing worn set retained |
| Sunder | Existing worn set retained |
| Supernova | Existing worn set retained |
| Black Hawk / Nova | Existing worn set retained |
| Champion | Existing worn set retained |
| Strider | Default armor and mechanical tiles reauthored; smooth-plate normal cleanup retained |
| Avatar | Default tiles and formerly plain new geometry covers reauthored |
| Owens | Blurry enlarged original tiles and smaller mechanical surfaces reauthored |
| Firefly | Blurry enlarged original tiles and smaller mechanical surfaces reauthored |

The two MW5 weapon atlases reuse the reviewed Mad Cat worn weapon layout only
after the donor and recipient weapon normal maps matched exactly. Their normal
SHA-256 is `1a85f78797f2bd4d646093d471c7160c5b1c12b3afe0792794d685332e95f611`.
An initial Shadow Cat variant that copied the wrong reference layout was
rejected. Selected stock revisions reduce broad distressing and preserve
Avatar blue, Owens pale paint and Firefly markings.

127 material bindings across the six complete authored sets have changed;
71 of these belong to the four revised runtime replacement models. Other
bindings are the Owens/Firefly sets used by original geometry and the offline
prototypes. Export dimensions retain larger existing tiles up to 2048 long
edge and raise smaller authored nonconstant tiles to 1024 long edge. Constant
glazing and the intentional small `mech02` gradient are retained. Already
detailed larger sets were not enlarged merely to change their size label.

These are reconstructed textures, not recovered high-resolution originals.
Selected generated atlases are natively 1254 square or 1774×887; small tile-page
crops have lower effective authored resolution than their 1024/2048 exports.
Resampling is not additional authored detail. Exact source identities, crop
boxes, native dimensions and export dimensions are recorded locally.

## Installation

Local candidate and review directory:
`local/work-ahead/default-mech-textures-20261020-r1/`.
It contains the selected 18 sets, packed offline scenes, comparison HTML,
before/after renders, configuration backups and validation receipts.

Changed default paths in:

- `local/remaster/models.json`;
- `local/material-authoring-r1/normal-registry.json`.

Both launcher profiles now reference the versioned texture-bank map and stock
surface-catalog list in that directory. The native executable and all graphics
settings remain unchanged. In particular, the user explicitly chose to retain
the main profile's `fullscreen_windowed` setting.

The two versioned banks derive from the banks actually selected by the old
profile, not a stale manifest. `rmechtex16` changes 58 selected default entries
and preserves 2228 other entries byte-for-byte. `rmechtex` changes 91 selected
entries and preserves 3269 other entries byte-for-byte. Table order and opaque
RGB565 format contracts are preserved. The three globally shared helper tiles
`mech01`, `footpad`, and `weap_hole` remain unchanged in these banks: their
existing normal interpretations differ between banks. Chassis-local replacement
textures may still use their new authored versions. Unselected bank surfaces
and the separate Bushwacker alternate-skin replacement set are preserved.

46 new full-color surface identities carry forward the exact normal-image
tuples already bound to the previous bank pixels. Both existing world/vehicle
surface catalogs remain byte-identical and are retained in the new catalog
list. No normal-strength recalibration or color-derived replacement normals
were introduced. Six stale Campaign 1 manifest paths were synchronized to the
object banks already active in the profile; this preserves actual world
textures while making preparation agree with the launcher's override map.
The other 37 active bank rows are unchanged.

The runtime roster remains 16 chassis: 14 MW5 ports plus detailed Strider and
Avatar. Owens and Firefly still use their original runtime geometry through
the color-bank path. Their newer geometry prototypes are **not installed** by
this texture pass. Original-model launch mode also sees the selected updated
original texture tiles.

## Verification and limits

- Offline front, rear, torso and color-only before/after renders for the six
  revisions; geometry/UV/pose hashes unchanged within each comparison.
- Additional Owens/Firefly reviews use their actual original runtime geometry,
  rather than showing only the uninstalled detailed prototypes.
- Both 16-model registries resolve. Independently decoded all 34 color sidecars
  per profile, including distance bindings and the separate Bushwacker skin.
  Every material name, batch index, dimension, RGB565 pixel and stored signature
  agrees with its selected PNG and batch metadata.
- Main's two normal sidecars and the normal profile's 32 normal sidecars are
  byte-identical to the previous reviewed prepared maps. All non-color model
  fields and skin registrations compare equal to their configuration backups.
- Both prepared bank maps agree with the profiles' 39-bank override maps.
  Existing surface catalogs and the original `MW3/mw34-registry.txt` retain
  their hashes. No pilot files were read or written for this pass.
- The normal-preview root launcher completes `--prepare-only`. Main and
  original-model `--check` resolve the assets but still report the pre-existing
  unsupported graphics-profile combination: the main profile requests
  `fullscreen_windowed`, which its published capability list does not support.
  Its display settings were explicitly left untouched. Main assets were
  prepared directly with the same native asset preparer, not by bypassing a
  live launch guard or claiming that the main launcher can start.
- No game was launched and no desktop screenshot was taken. Blender illumination
  is a review setup, not a promise of native lighting equivalence. No FPS,
  full combat, damage progression, all-view UV seam, extended campaign or new
  normal-strength acceptance claim is made. Native visual review remains next.

## Review links

[Drive review folder](https://drive.google.com/drive/folders/1XwQpG5ZroBa4G1yFVqVcHL0vBkymE6yk)
contains the roster overview, six per-chassis before/after comparisons, and
notes. Only rendered previews and notes were uploaded; editable/raw assets,
original media and generated game code stay local. Preview IDs, parent folders
and byte counts were read back through the Google Drive connector.

[Roster overview](https://drive.google.com/file/d/1W3No-o6QxVflnOOnGhVcjYe-6wdsDOeW/view)
and local `comparison.html` show the six revisions and list all eighteen sets.


Runtime follow-up, 2026-10-20: the detailed Owens and Firefly are now included in
the [18-model main Remaster integration](all18-mechs-main-integration-2026-10-20.md).
This supersedes the offline-only status above for those installed candidates;
the listed native combat/performance limits remain.
