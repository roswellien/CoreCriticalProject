# MW3 Hi-Res texture upgrade pack

Status reviewed 2026-10-13: active local development, cumulative archive
integration prepared, broader in-game visual validation pending.

The project develops an optional high-resolution texture upgrade pack alongside
[native recompilation](../faithful-modernization-plan.md) and the
[original-EXE Vulkan wrapper](../d7vk-wrapper-launcher-summary.md). The pack uses
AI-assisted artwork and source-aware exports for mech panels, terrain, water,
buildings, structures and selected effects. It preserves an original-textures
mode through the launcher. It is not a whole-game remaster completion claim.

## Current local coverage

The figures below summarize the existing local audit and inventory read for
this documentation update. Those jobs were not rerun; their stored outcomes
remain distinct from fresh game or visual tests.

| Scope | Recorded outcome | Limit |
| --- | --- | --- |
| Launcher archives | 39 configured cumulative `.zbd` banks; audit status `passed`, all installed AI identities and original restore sources verified | Archive integrity and configuration, not appearance in every mission |
| Primary mech sets | 19 complete primary sets; no partial mech assets listed in that audit | Does not establish every skin variant or damage state in-game |
| Terrain/world priority | 298 texture-name families; 243 fully upgraded, 55 needing at least one bank; 348 archive entries remaining | Includes terrain-marked bridges, walls and structures; not solely ground textures |
| Training priority | 42 of 42 terrain/water names upgraded in the regional inventory | Archive coverage, not complete Training asset or gameplay acceptance |
| Campaign 1 priority | 51 of 51 terrain/water names upgraded in the regional inventory | Props and effects are separate coverage categories |
| Buildings and structures batch | 14 Training and 84 Campaign 1 scene-referenced candidates; 588 replacements across 12 banks | Mapped visual review remains pending |
| Terrain target audit | 4,818 prepared target entries checked | Counts repeated bank entries, not unique textures |
| Selected effects | 28 prepared dust/smoke/fire/impact frames in Training banks; blue laser impact in Training and Campaign 1; 13 animated surf frames in those regions | Not all campaign effects remastered |

The broader environment inventory covers 36 original texture-family archives
and six world-scene archives across Training and the base campaign regions:
1,413 names and 18,645 archive entries. These are inventory totals, not upgrade
totals. Regional counts overlap because textures are shared.

Local evidence is retained in `local/work-ahead/texture-launcher-audit-v2/`
(`configured-banks.json` and `verification.json`),
`local/work-ahead/terrain-inventory-v1/summary.json`, and
`local/work-ahead/training-campaign1-objects-v1/README.md`. These ignored paths
are evidence locations for the local workspace, not public download links.

## Artwork and preservation

Early [AI texture pilots](work-ahead-texture-ai-batch.md) established the art
direction; subsequent [Training work](work-ahead-training-textures.md) recovered
material and UV associations and prepared mech/terrain exports. Later batches
include 16x source-dimension masters. Scales and treatment vary by batch.
AI-generated detail is an intentional visual enhancement, not recovered original
detail, and early full-AI alpha choices differ from later source-alpha exports.

Recent building and terrain batches preserve original alpha and use candidate
RGB in primary banks, with bounded detail anchored to original colors and
structures in other bank variants. Their recorded archive round-trip checks
cover dimensions, alpha and RGB565 quantization; cumulative builds preserve
previous replacements and check untouched entries. Sources, prompts/provenance,
export recipes, hashes, review galleries and editable OpenRaster layers remain
in the local batch packages.

The [launcher](../../mw3_launcher.py) selects original or AI banks using NTFS hard
links in the prepared private profile, avoiding full archive copies where
hard linking is available. Per-file replacement is atomic; switching the entire
set is not one atomic transaction. The launcher currently requires a prepared
manifest and local profile; it is not a portable pack installer.

## Remaining work and release scope

Finish remaining bank coverage and confirm texture/material selection in actual
scenes. Review tiling, seams, UV wrapping, palette differences, alpha edges,
damage variants and effects in motion. Measure memory/load/render cost and
verify switching back to original textures. Archive verification and visual
approval of individual previews do not establish whole-game compatibility.

Normal/roughness maps and HUD SVG artwork remain offline preparations requiring
future renderer support. Video restoration follows a separate integration path.
See [the asset workstreams](work-ahead-assets.md) for their respective gates.

Original textures, decoded references, AI-derived artwork and replacement
archives stay local. The [distribution policy](../legal.md) permits documentation
and authored tooling in the repository, but does not authorize public derived
texture packs. A public release needs resolved provenance/distribution policy
and validation; no downloadable texture pack is claimed here.

This documentation advances no execution boundary. Texture integration in an
original-EXE profile is separate from native menu, Training and gameplay
acceptance. The last verified selected native startup count remains **131/144**.
