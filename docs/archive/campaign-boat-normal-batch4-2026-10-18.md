# Campaign fishing-boat normal authoring — batch4, 2026-10-18

Campaign encounter ranks 11–17 now have individually authored structural relief:
`fish_boat05`, `04`, `08`, `07`, `06`, `01` and `02`. The seven families cover 23
reviewed C1 full-pixel identities. Only Material Normal Preview selects this
batch, at unchanged terrain/object strength 1.5. Existing colors, rock artwork,
roads, water/cloud tuning and model geometry are retained.

## Authored treatment

| Material | Relief and exclusions |
| --- | --- |
| fish_boat05 | Hull ribs, rails and small hinge plates; hazard-color band excluded from grain; unused black lower region flat |
| fish_boat04 | Hatch frame, cover plates, handles and vent slots; dark port interior flat |
| fish_boat08 | Panel rims, shallow recess and horizontal hardware |
| fish_boat07 | Wheelhouse frames and vents; three glass panes flat; paint band excluded from grain |
| fish_boat06 | Window outlines, diagonal cabin frame, hatch hardware and pipes; polygonal glass masks flat |
| fish_boat01/02 | Restrained plate-joint relief and shallow surface grain; paint-stripe boundaries suppressed; dark lower hull region flat |

The source audit compares all seven live inputs with the corresponding original
bank entries: each uses different, larger upgraded color data. Those colors are
unchanged in this batch. Structural forms come from explicit normalized UV
feature recipes rather than interpreting all bright/dark paint as height.
The upgraded color contributes only restrained fine grain outside exclusion
masks. Clamped float height differentiation avoids wraparound across unrelated
edges and 8-bit quantization of shallow features; editable 16-bit heights and
RGBA8 normals are retained locally. These are interpreted surface features,
not measured displacement or changes to the geometry.

All 23 selected bank identities pass layout screening against their respective
upgraded references, with minimum zero-offset correlation .9792 and no preferred
tested displacement. Fine-feature placement still needs visual review. Normals
are 512 pixels on the longest side for most materials and 1024 for the two tall
hatch/hull layouts, bounded by each source image. No samples hit the .4 slope
cap; maximum observed slope is .255. The global1.5 multiplier is not baked in.

The final world catalog retains all 4,001 keys:23 normal values change and 3,978
others stay byte-identical. One page required splitting to respect the existing
16 MiB page ceiling. The first preparation correctly fails on its oversized page
and is retained as excluded evidence; the second publishes 77 valid pages totaling
519,152,180 bytes (495.10 MiB). The 512 MiB total ceiling remains unchanged, leaving
about 16.90 MiB. Later batches need explicit memory planning before adding more
large maps; no performance improvement or increased budget is claimed.

## Ground entry correction

The coverage audit found that the dedicated surface catalog's older `txgter_1`
entry remained authoritative over the batch 2 AI-height candidate in the world
catalog. That precedence is intentional in the renderer; the Material Preview
asset selection had not replaced the older dedicated entry. Consequently,
earlier screenshots must not be cited as proof that this particular new ground
height was active. Other batch 2 terrain changes are unaffected by this finding.

The candidate now replaces exactly that one explicit full-pixel entry with the
already prepared batch 2 height-derived normal, preserving the other 55 dedicated
bindings byte for byte. A fresh native run uses the corrected surface catalog
and preserves 2,600 original draw triples against the boat candidate. The
village-frame difference is only 17 pixels, so that view is not meaningful
visual proof of ground quality. Separate prepared field imagery and the full
registration/configuration receipts remain local. Final ground art review is
still open. Other preview profiles retain their existing dedicated ground maps.

## Native verification and screenshots

Fresh normal-view baseline/candidate runs preserve all 3,000 original frame/
draw-count/hash triples. A second matched pair holds the original reticule-zoom
key and also preserves all 3,000 triples. Both pairs use the same original C1M1
route, resolved midday light, world strength 1.5 and replay video off. Logs confirm
that all seven live boat keys bind to normal textures. Four new feature-mask
checks plus the ten existing atlas/relief checks pass: painted color stripes
cannot make structural ridges, glass stays flat, structural relief survives
uniform albedo, invalid UVs fail, and earlier atlas/relief contracts remain intact.
All exits are intentional presentation-budget stops, not crashes or normal quits.
No executable or game/rendering source change is part of this batch.

- [Coast before](https://drive.google.com/file/d/1eWNqE_uI0biy9ycte99OiId5NEJY8WrW/view)
- [Coast after](https://drive.google.com/file/d/1UfXPFuLKyBI8Bo727KujcWxIDXzbNESg/view)
- [Original zoom before](https://drive.google.com/file/d/1TgS1upzfIRPRB5r83CnEgjRnRmMyHPmI/view)
- [Original zoom after](https://drive.google.com/file/d/1FH3TmC3BRU-LJvxeUyvcKHRGIVQvkLgf/view)

These 3440×1440 native screenshots show the boat treatment, which is unchanged
by the subsequent dedicated-ground correction. The normal changes are subtle at
this distance and light angle; the views do not prove close-range appearance
of every hatch/vent. A short-pulse zoom probe did not retain zoom in its saved
frames and is excluded from the zoom comparison. Private Drive sharing is
unchanged; original textures/height assets are not uploaded.

Execution boundary advanced: seven additional C1 boat families now have
source-matched structural normals reaching both ordinary and original zoom
views, and the newer ground height is selected in its authoritative slot.
Native acceptance stays 131/144. No full mission, timing benchmark, final art
approval, completion of the 100-material pass or commit is claimed.

Local evidence: `C:/Users/jcbla/MW34SunTests/campaign-boat-batch4-20261018/`.
Recipes/layout review/editable maps: ignored
`local/material-authoring-r1/authored-batch4/`. The generic
[feature-height authoring helper](../../tools/remaster-launcher/feature_relief.py)
is covered by [feature-mask checks](../../tools/remaster-launcher/test_feature_relief.py).
The next queued materials are the ruins and further village surfaces at ranks 18+.
