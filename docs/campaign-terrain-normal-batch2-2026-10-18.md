# Campaign terrain normal refinement — batch2, 2026-10-18

The next pass follows the first100 campaign encounter queue: `txwall06`,
`txgter_1`, `beach01`, `sandtrans1` and `ltsand`. It updates23 exact C1 texture
identities across these five families. The existing road artwork revision stays
installed. No color texture, executable, simulation or rendering code changes.

## Content and limits

`txgter_1` receives a separate AI-assisted grayscale height candidate derived
from the upgraded artwork. Coarse alignment screening prefers zero displacement
for all five variants, with correlations .8996–.9289. Its512×512 normals have
p95 slope .154 and no clipped samples. This does not establish measured physical
height or exact fine-grain correspondence; the candidate remains reviewable.

A third `txwall06` AI attempt is rejected: correlations improve to .809–.861,
but all variants prefer a horizontal shift. That image remains excluded. The
selected cliff refinement instead derives height directly from each variant's
upgraded pixels, removing the persistent left/right illumination bias and
retaining horizontal strata at their source coordinates. New cliff normals are
512×1024, with p95 slopes .202–.401 and at most .568% clipped samples.

The three sand families receive separate analytic recipes that reduce broad
painted shading in the height estimate and retain shallow grain. The transition
recipe suppresses the large sand-color change rather than treating it as a deep
step. Output resolution stays within the source dimensions:256–512 pixels for
beach/transition and512 for light sand. These four families remain color-derived
technical refinements, not four newly completed hand-authored height maps.
The combined treatment is deliberately less lumpy than the previous draft.

Global terrain/object strength remains **1.5**. Separately tuned mechs, water,
clouds and other world materials are unchanged. The package preserves all4,000
keys and3,977 other normal bindings byte for byte. It totals494,608,788 bytes
(471.70MiB), within the existing512MiB limit. This increases content memory and
is not a performance optimization or a new timing benchmark.

## Native review

The resolved-midday candidate matches all2,000 original frame/draw-count/hash
triples from the previous road-revised baseline. A fresh low-angle pair also
matches all2,000 triples, using azimuth45° and elevation9° to illuminate the
cliff. Both members of each pair use world strength1.5, identical color banks,
the same camera/input route and replay video off. The illuminating direction
is diagnostic; it does not change the launcher's default lighting preset.
All stops are intentional presentation-budget exits, not crashes or normal
mission completion. Three uniform-surface checks produce exactly flat normals;
full output catalog reads and per-binding preservation checks pass.

- [Terrain before](https://drive.google.com/file/d/1rmFZmWDnahgOIMQzE0qSpTsRQ6q3_M8P/view)
- [Terrain after](https://drive.google.com/file/d/1VhKiSzNUXJV4sgkEq62f7CDYCVLkAo7G/view)
- [Sunlit cliff before](https://drive.google.com/file/d/1wgPmtem8RmQ0c9w3WvqeiZahXZ4ip2HH/view)
- [Sunlit cliff after](https://drive.google.com/file/d/1F-5PmMWOxijaEgESPQilB0OFptVZWHoM/view)

All screenshots are3440×1440 native captures. Uploads retain the existing private
Drive folder organization and sharing. They support appearance review, not a
claim that all100 materials have been authored or approved.

Only **Play MW3 - Material Normal Preview.cmd** selects this batch. The other
two previews retain the previous normals, updated roads and1.5 strength.
Local receipts, original/candidate captures, source pins and the rejected gain
trial are under `C:/Users/jcbla/MW34SunTests/campaign-terrain-batch2-20261018/`.
Generated height images and exact prompts are in ignored
`local/material-authoring-r1/authored-batch2/`. The preparer is
[prepare_campaign_terrain_relief.py](../tools/remaster-launcher/prepare_campaign_terrain_relief.py).

Execution boundary advanced: the first five encountered C1 terrain families now
use individually selected relief treatments in the live native preview. Final
art approval and further height authoring remain open. Continue with the queued
rock blocks, wall and village-object materials; road03 at rank6 was addressed
in the preceding correction. Acceptance remains131/144. No commit is made.

## Later coverage correction

The [batch4 binding audit](campaign-boat-normal-batch4-2026-10-18.md#ground-entry-correction)
found that the live `txgter_1` key still selected its older dedicated surface
normal over this world-catalog candidate. Earlier captures therefore cannot
establish that this particular AI-height map was active. Material Normal
Preview now selects the matching new data in the authoritative dedicated entry;
the other55 dedicated bindings and other preview profiles stay unchanged.
