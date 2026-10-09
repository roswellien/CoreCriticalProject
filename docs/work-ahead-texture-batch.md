# First prepared MW3 texture batch

Recorded 2026-10-07. Twelve textures are exported and packaged locally: four
mech panels, four terrain surfaces and four effect sprites. All use exact 4x
dimensions. They follow the approved weathered material direction, with original
color, layout and explicitly protected markings retained by the export recipe.
Status is **packaged prototype**, pending visual and mapped in-game review.
After comparison, the user chose the [full AI version at 100% as the starting
point](work-ahead-texture-ai-batch.md). This preserved batch remains a reference;
the new AI batch is the active art direction.

## Selection and source mapping

Mech entries come from `MW3/zbd/rmechtex.zbd`, SHA-256
`8f679537d33fb6da204d8dcb83d5b4d0e4d5dbcee1a16d0c63caeed9649fdbfe`.
Terrain and effect entries come from `MW3/zbd/c1/rtexture.zbd`, SHA-256
`56afd5738562ffd51596ce4b3557b734cacedfd187b09307e9b94281dd39269f`.
Entry indexes are zero-based. Categories are inferred from names and appearance;
their exact game bindings have not been recovered.

| Category | Batch ID | Source entry / name | Source size | Export size |
| --- | --- | --- | --- | --- |
| Mech | `annihilator-panel` | 0 / `annihi_d01` | 128 x 64 | 512 x 256 |
| Mech | `avatar-panel` | 200 / `avatar01` | 128 x 128 | 512 x 512 |
| Mech | `bushwacker-panel` | 552 / `bushwacker01` | 128 x 128 | 512 x 512 |
| Mech | `shadowcat-panel` | 2358 / `shadowcat01` | 128 x 128 | 512 x 512 |
| Terrain | `beach-sand` | 11 / `beach01` | 128 x 128 | 512 x 512 |
| Terrain | `weathered-concrete` | 31 / `c1conc01` | 128 x 128 | 512 x 512 |
| Terrain | `stone-blocks` | 231 / `rockblok` | 64 x 64 | 256 x 256 |
| Terrain | `sand-transition` | 234 / `sandtrans1` | 128 x 128 | 512 x 512 |
| Effects | `dust-puff` | 340 / `dust01` | 32 x 32 | 128 x 128 |
| Effects | `fire-frame` | 342 / `fire_f01` | 32 x 32 | 128 x 128 |
| Effects | `blue-impact` | 370 / `laser_impact_blue` | 32 x 32 | 128 x 128 |
| Effects | `white-smoke` | 440 / `wtsmoke1` | 32 x 32 | 128 x 128 |

The strict decoder accepts these opaque RGB565 and RGB565-plus-byte-alpha
entries. Reserved, palette and stretch forms in the terrain package remain
unsupported. Preparation verifies package hashes, entry spans and decoded RGBA
and PNG identities before producing any exports.

## Art treatment and preservation

Eleven textures use generated material drafts; the annihilator draft reuses the
earlier approved pilot. Smoke retains its original uniform RGB and alpha shape.
Raw drafts contain sharper detail but also change panel forms, markings or effect
rays. They are included as editable art references, separately from the exports.

The final recipe starts with bicubic original RGB and adds only bounded draft
variation within each enlarged source-pixel cell. Draft cell means are removed;
residuals are capped at +/-20 per channel before strength. Strength is 0.5 for
mech panels, 1.0 for terrain, 0.25 for effects and zero for smoke. This reduces
coarse layout and color changes; it does not prove that all generated variation
represents original detail.

Every original alpha byte is replicated exactly on the 4x grid. RGB is black at
zero alpha. Two source-pixel borders, named marking/boundary rectangles and both
endpoints of adjacent RGB contrasts of at least 48 levels retain exact original
RGB. These protections intentionally leave some regions soft or blocky. The
[export lock specification](../tools/asset-inventory/texture-lock-format.md)
documents the formula, coordinates, reconstruction and checks.

These are authored image-coordinate protections. They preserve selected artwork
boundaries but do not establish unknown mesh UV islands or seam positions.

## Local handoff

The ignored directory `local/work-ahead/texture-batch-v1/` contains:

- `review.html`: source pairs with full-resolution AI artwork, resized drafts,
  preserved exports or protection masks; actual image dimensions, fit/1:1/2:1
  display controls, backgrounds and terrain repeat previews. The default right
  image is now the full-resolution artwork shown inline in chat.
- `manifest.json`: package and entry mapping, byte spans, decoded identities,
  artifact hashes, provenance, prompts, tool identities and export settings.
- One six-layer editable OpenRaster document per texture, plus the decoded
  original, final RGBA8 PNG, raw draft and preservation components.
- Per-texture `generation.json`, `locks.json` and `export-report.json`, the exact
  command vectors in `selection-and-recipe.json`, and local preparation scripts.
- `independent-validation.json` and `SHA256SUMS.txt`.

`local/work-ahead/texture-batch-v1.zip` packages the directory, with an adjacent
SHA-256 sidecar. Source containers are not included. The final exports contain
1,835,008 pixels total, or 7,340,032 bytes as uncompressed RGBA8 before mipmaps.
No engine texture format, mip policy or replacement loader is assumed.

Each editable document opens with the checked final layer visible and five
component layers hidden. Partial-alpha components cannot reconstruct the export
through ordinary source-over blending: select protected RGB using the lock mask,
then restore original alpha using the recorded exporter. Any edited export must
pass the same checks.

## Evidence and remaining gates

All 12 exports pass exact dimensions, source alpha, protected RGB and transparent
RGB checks with zero mismatches. An independent read-only Pillow check confirms
those invariants, source grids, masks, file hashes and contrast-guard coverage.
All 27 authored asset tests pass through CTest `asset_tools`. All editable archive
references and merged-final identities pass; the outer ZIP's entries match
the packaged files. Gallery JavaScript syntax and local resources pass static
checks. Browser automation refused local file navigation, so automated rendered
gallery review was unavailable.

Review must still establish actual asset bindings, UV seams, orientation,
sampling/gamma, terrain repetition and effect blending in the original or native
renderer. The four effects are individual sprites, not complete animation packs.
The gallery's repeat preview helps inspect boundaries but does not establish
seamless in-game tiling. Visual approval, mapped review and a replacement contract
remain necessary before integration-ready status.

Derived media and the local handoff ZIP stay Git-ignored under the project's
[content policy](legal.md). The opening movie remains the first planned full
video upscale, on hold as recorded in the [video queue](work-ahead-video-pilot.md).
