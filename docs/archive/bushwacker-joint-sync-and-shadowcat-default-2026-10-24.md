# Bushwhacker mesh sync and Shadow Cat default color revision

2026-10-24. Optional model-pack work only; strict acceptance remains **131/144**.
No commit. Original media and generated game code remain local.

## Bushwhacker

The prior default-color preview opened `bushwacker-worn-prototype.blend`, an
older scene that does not represent the installed repaired shoulder placement.
The optional pack also pointed to the earlier R2 attachment payload while
`local/remaster/models.json` pointed to the later October 19 joint-fit payload.
Both installed mesh LODs now match the project registry: SHA-256 `3103701d...`
and `84cd33cc...`. Existing default/alternate color and normal payloads were
left intact. Exact serialized LOD0 geometry was rendered with the current
default texture in standing left, right, front and walking left views. These
offline reviews show the current torso-to-upper-arm joints; they do not claim
live-game animation coverage.

## Shadow Cat

The original MW3 local texture tiles were inspected. The stock `shadowcat04`
tile includes yellow caution stripes, and `shadowcat17` has service color
details. The prior offline marking candidate supplied suitably placed pigment,
but replaced too much fine atlas detail. This revision retains the mapped
October 20 default Body atlas and copies only the saturated caution/service
pigments from that candidate. A paint-side edge pass lifts armor edges toward
warm metal without whitening dark gaps; dark mechanical pixels get low-amplitude
graphite variation. Variant, Weapons, Window and MissileHead color images,
normal maps, geometry, UVs and all alternate skins remain unchanged.

The new default Body color was packed into both Shadow Cat LOD BWTEX1 payloads
and selected in both local model registries. The optional pack's model registry
and file manifest were updated. The pack's original-model/no-pack path was not
changed. A matched saved-scene front, rear and torso review confirmed the
stripe maps to the upper torso and the small red mark maps to leg armor. The
geometry/UV/pose digest held constant during renders. The installed pack's
selected payload hashes, sizes, header formats and manifest were checked.

The wear is deliberately restrained. The result has not yet received an
in-game lighting review; offline renders show the color mapping, while native
material and scene lighting may change the perceived contrast.

## Remote review

[Google Drive folder](https://drive.google.com/drive/folders/1w6Ss03HwCEzSgVvJXdqw57qLX9eWgpBF)
contains nine rendered PNGs, including Bushwhacker shoulder views, Shadow Cat
before/after and the retained Somerset Strikers inspired Bushwhacker draft.
The latter remains a separate local Blender/GLB/color-atlas draft, not an
installed native skin.

## Shadow Cat follow-up: joint tone and surface response

The first review was too dark and matte, and its edge lift did not read on the
model. A second local revision uses the fitted model's Body UV coverage to
target the atlas pixels the mesh actually samples. Broad near-black mechanical
regions now have visibly varied graphite color, while narrow dark panel seams
remain dark. A narrower bright-region boundary pass puts cool metallic wear on
the paint side of selected armor edges. MW3-style markings remain visible.

The Blender material now includes revised Body roughness and metallic maps:
dark joint surfaces have a satin response, painted armor is less uniformly
matte, and exposed wear has stronger highlights. The editable packed scene is
`local/work-ahead/shadowcat-default-revision-20261024-r2/shadowcat-default-material-r2.blend`.
The optional native model pack currently consumes the revised **Body color**
plus its existing normal map; it does not consume the new Blender roughness or
metallic maps. Therefore the live game gets the lighter graphite/edge color,
but the Blender specular response is not yet a claim about native rendering.

Both installed Shadow Cat default color payloads were replaced again after
review, with final hashes `8311c175...` and `dc336c15...`; the other maps,
model meshes, normal payloads and alternate skins were preserved. The pack
registry/manifest and both project registry paths were checked. Exact before
and after Blender renders held the same geometry/UV/pose digest, and the Drive
files were updated in place. [Close-up comparison](https://drive.google.com/file/d/1R8A6WaiPaAnoRraB1EY9LdfG0aApqqvy/view)
and [revised rear view](https://drive.google.com/file/d/1pP_jMAClRhArNb6Z26o8MEnJhzwgr-uG/view)
show the previously black joint surfaces clearly. No native gameplay run was
performed for this color-only review.

A separate [revised color with previous PBR maps torso proxy](https://drive.google.com/file/d/11ge7YMp4pO40VyfxqVxdod_AyZaV1z58/view)
and [rear proxy](https://drive.google.com/file/d/12WpxoGmDzemtn9Ai-TJgw2IgCcrtegka/view)
is included for review. These are Blender renders with the revised base color
and previous PBR maps, not native game screenshots.
