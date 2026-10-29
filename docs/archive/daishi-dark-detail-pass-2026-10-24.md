# Daishi dark mechanical detail pass — 2026-10-24

The first Daishi default-skin revision restored pale armor and the red launcher
marker but left broad black replacement-model surfaces nearly featureless.
Reviewing the original local MW3 tiles and original-model front view showed
the remaining identity cues: ribbed vents, circular access covers, dense
mechanical panel seams, soot around vents and the blue canopy. The extracted
tiles did not show a large faction decal or caution-stripe pattern to copy.

This follow-up fills formerly near-uniform dark regions of the Body atlas with
readable charcoal gunmetal panels, grills, ribs, circular machinery and worn
edges. The existing pale armor islands and their UV positions are retained.
The Weapons atlas is lifted to gunmetal while preserving its original island
placement and fine engraved parts. Window, Variant (including its red marker),
and MissileHead are unchanged from the previous Daishi revision.

Authoring textures, stock-tile references and matched front/rear/close Blender
renders are local under `local/work-ahead/daishi-details-20261024-r2/`.
The edited sheets are `textures/Body_basecolor.png` and
`textures/Weapons_basecolor.png`. Blender reported unchanged geometry/UV/pose
and animation hashes. The LOD0 and LOD1 BWTEX1 batch tables and all three
untouched material records remained byte-identical to the prior installation.

The optional local model pack, `local/remaster/models.json`, and
`local/material-authoring-r1/normal-registry.json` now point Daishi's default
color binding at this pass. Other model entries, alternate skins, normals and
meshes were not changed. This asset presentation pass does not change the
131/144 native acceptance count. An in-game visual check is still open.
