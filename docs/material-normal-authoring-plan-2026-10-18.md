# Material normal-map authoring priorities

Date: 2026-10-18. User-directed terrain, world-object and all-vehicle refinement,
including mechs. Continues the [automatic first pass](world-normal-mapping-preview-2026-10-18.md)
and [current lighting measurements](lighting-performance-2026-10-18.md).
Original media, generated height/normal images and sidecars remain local.
Acceptance remains **131/144**.

## Completion scope — Campaign 1

The [Campaign 1 first refinement pass](campaign1-normal-material-pass-2026-10-18.md)
is now selected in Material Normal Preview. Its ledger covers 287 selected large
terrain/structure/vehicle families, preserves earlier work, and records the
deferred/separate-path materials. Shared original-mech variants and pads are
reconciled separately. Native route checks pass; individual close-up art review,
live C1M4 review and full playthroughs remain distinct from prepared coverage.

User direction on 2026-10-18: finish storage relocation, then complete the normal-map
upgrade pass for all missions in Campaign 1 (the first operation). The first-100
encounter list is a historical ordering aid, not the completion boundary. Enumerate
all Campaign 1 scene/material references and upgraded bank variants to establish
the eligible coverage list before claiming completion.

Continue prioritizing larger terrain, prominent structures and vehicles, including
mechs. Tiny human textures and small incidental props remain deferred. Preserve
strength 1.5 and existing upgraded albedo. Track prepared coverage, actual runtime
selection and visual review separately; do not equate static coverage with a full
mission playthrough. Save native screenshots for review as each batch is verified.
Resolve the existing catalog capacity limit before adding maps beyond its remaining
space; do not silently drop prior authored materials or raise the budget.

## Current work order — large surfaces and vehicles

Updated by user direction on 2026-10-18: prioritize larger terrain pieces,
larger structure pieces and vehicles, including mechs. Defer the tiny human
character materials (`thedude06/05/03/04/07`) and small incidental props for now.
This supersedes strict first-100 execution order; retain the original encounter
ranks and evidence in the [campaign queue](campaign-first-100-materials-2026-10-18.md).
Use campaign encounter order within the eligible large-surface/vehicle work,
with visually prominent surfaces receiving attention before small details.

Before the full Campaign 1 pass, the next eligible terrain candidates were dark sand (`dksand`) and its transition
(`sandtrans2`), followed by remaining wall/cliff families. Structure candidates
include bridge, dock, plant, bunker and communications-building surfaces.
Vehicle work includes tracked/support vehicles, APCs, tanks and mechs; review
whole vehicle material sets together where that prevents inconsistent finishes.
The `tredtruck` family was the next vehicle source-review target; these families
are now included in the Campaign 1 pass linked above.
Candidate filenames alone do not establish object size, screen coverage or
material meaning: confirm artwork and placement before authoring. Power-line
hardware and other small props are deferred alongside the character materials.

Preserve all completed batches and upgraded colors. Work from the upgraded
sources, retain world strength 1.5, and post native before/after screenshots.
The pre-pass world catalog was 500.60 MiB; the current Campaign 1 candidate is
493.63 MiB against the unchanged 512 MiB ceiling;
plan each batch's normal resolution and memory use before generation. Do not
raise the ceiling or remove prior reviewed maps merely to fit the next batch.
A selected queue entry is not a completed or approved normal map. The wider
519-target analysis remains a backlog rather than an obligation to author tiny
objects ahead of important scenery.

## Selection and frequency

The [priority scanner](../tools/remaster-launcher/rank_normal_priorities.py)
follows all six previously decoded Training/campaign world archives through node,
model, polygon, material and texture references. It counts polygon-material uses
per placed node, rather than counting duplicate texture-bank entries. Terrain
and non-terrain world nodes are ranked separately; a texture can appear in both.

| Lane | Eligible names | Top 25%, rounded up | Static reference coverage |
| --- | ---: | ---: | ---: |
| Terrain-marked geometry | 289 | 73 | 92.60% |
| Other world/object geometry | 1,081 | 271 | 82.88% |

Dedicated water surfaces, animated surf/foam, sky and classified effects are
excluded from opaque-material authoring. Wet ground and underwater floor remain
eligible where they are solid terrain. The original terrain flag also covers
some walls, bridges and structures; it is not a pure dirt/grass label.

These are static scene-reference rankings, **not measured screen time or mission
visibility**. Stored LODs, library objects and repeated placements affect counts.
Mission traversal must subsequently validate visibility and distance importance.

The [complete authoring queue](material-normal-authoring-priorities-2026-10-18.csv)
retains rank, count, selection reasons and vehicle roots. The combined queue has
515 world texture names, plus four vehicle materials in the separate mech banks
(519 combined queue entries). Individual upgraded bank/pixel variants stay distinct; a
shared name does not justify sharing different artwork's normal image.

## Visual-impact additions

Add the top decile of static local polygon area in each lane, plus explicitly
flagged cliff/mesa/rock, building, bridge, bunker, industrial and port material
candidates. Polygon area is a review proxy, not projected screen coverage;
name matches require artwork review and do not prove landmark status. There
are 158 name-screened candidates before overlap with the frequency/area lists.

First terrain families include `gter_1`, `gter01`, `txgter_1`, `ggter_1`, `mount01`,
`wallface01`, `clifwall01`, `clifwall02` and `gwall01`. Big Lake's `txwall01` and
`txwall06` receive explicit rock treatment because their first-pass 128×64 and
64×128 maps lose the erosion-scale features of their upgraded colour textures.

Frequently referenced objects include `m_hq08`, `engineparts`, `trunk01`,
`clstruin`, `tanktrak`, `m3ruin`, `m_hq03`, `missle_turret01`, `tredtruck04`,
`drytree02`, `chalet01` and `m4ruin01`. Alpha foliage/decals and reflective or
painted details need individual masking decisions before final approval.

## Material authoring recipe and review

The [candidate preparer](../tools/remaster-launcher/prepare_priority_relief.py)
reads the pinned upgraded colour banks from the first-pass receipt. It checks
complete source hashes before and after generation. It exports editable 16-bit
height PNGs, linear normal PNGs and per-identity recipes, with separate broad,
medium and fine relief bands. No colours, UVs, geometry or gameplay are changed.

| Material | Candidate longest side | Art direction |
| --- | ---: | --- |
| Cliff/mesa/rock | 512 | Preserve erosion channels and large rock ridges |
| Ground | 256 | Moderate broad form plus small surface detail |
| World structures | 256 | Shallow relief; flatten atlas borders |
| Non-mech vehicles | 512 | Shallow panels/mechanical detail; suppress chroma-only marks |
| Missing Strider materials | 1,024 | Fill reviewed coverage gaps while retaining existing maps |

These are **material-specific, colour-derived authoring drafts**, not hand-painted
or physically recovered height. They start the authoring queue; generating them
does not mean all 515 materials are visually approved. Painted shadows, stains,
logos and highlights can still produce false height. Each important material
needs an editable mask/height review, a grazing-light render, seam/atlas inspection
and a distance check. Preserve detail without making ground noisy or armor lumpy.

Keep world strength at the requested 2, replacement-model strength at 1, and
replay video off. Do not hide insufficient relief by increasing global strength.
Runtime registration retains complete colour keys and authored/exclusion
precedence. Candidate pages must stay within existing 16 MiB/page and 512 MiB
world-package/resident budgets; raising renderer limits is not part of this work.

## Vehicles and mechs

Vehicle descendants are collected from explicit vehicle/support/aircraft roots,
including Bulldog, Harasser, Striker, APC/hulk, missile carrier, tracked/mining
trucks, mover, mobile HQ, MFB body, wheeled trucks and helicopter geometry. The
result contains 73 texture names across 20 root labels (several labels alias the
same family). Shared engine, wheel, tread and turret materials are included.
This follows scene geometry; mission-specific spawning and every damaged state
still need live validation. Root-name matching requires a roster completeness
review before calling this exhaustive vehicle-family coverage.

The world package covers 69 of those vehicle names. `blkhwk13`, `mcat16`,
`mcat20` and `mcat21` come from the installed upgraded primary/hardware mech
banks instead: eight exact bank/pixel bindings extend the stock catalog from
48 to 56 keys. All previous authored bindings remain byte-identical. Both
`mcat16` source entries are still small (64×64 / 64×128); these candidates cannot
recover absent panel detail. That tile remains a specific manual-artwork task,
not a claimed high-resolution upgrade. All 73 identified vehicle names now have
candidate coverage across the two catalogs.

All 15 replacement-mech registrations and both LOD variants are audited. Their
existing detailed authored maps, mostly 2K–4K, are preserved instead of being
replaced by colour-derived estimates or enlarged without adding detail. Original
Avatar/Owens/Firefly authored maps are retained with their stock catalog. Firefly
colour-artwork work remains separate. Seven previously unreviewed Strider slots
receive new 1K relief candidates, including damage materials; glass and constant
materials retain their explicit flat exclusions. More mapped batches do not by
themselves prove correct damage or animation appearance.

## Evidence and remaining validation

Local receipts, editable artwork, exact source pins, per-material recipes,
rankings and mech audit live under
`C:/Users/jcbla/MW34SunTests/material-authoring-20261018/`.
Synthetic checks cover retained broad rock relief, flat atlas behaviour and
polygon-area calculation. Native appearance/identity comparisons and the final
candidate installation status are recorded below as those checks complete.

## Prepared candidate and native checks

`Play MW3 - Material Normal Preview.cmd` selects a separate local candidate
profile/registry and prepared-asset directory. It retains the current sky/water
host, upgraded colour banks, mechs, menu and lighting presets. Other launchers
are unchanged. New Strider and shared-vehicle sidecars are selected only here.
The profile check passes; assets prepare through the existing launcher path on
launch. There is no native host rebuild or main-profile promotion.

The world draft replaces 1,738 bindings across 515 selected names while retaining
all 3,998 world identities. Its 74 pages total 465,838,248 bytes (444.26 MiB),
within the existing 512 MiB limit; the previous package was about 148 MiB. This
is a memory/content tradeoff, not a performance optimization. Complete page/hash
reads pass, no keys duplicate, and the preserved stock catalog is checked byte
for byte per binding. Original Avatar/Owens/Firefly maps stay intact. Both
Strider variants move from 53 to 63 mapped batches out of 92; the seven newly
mapped slots are drafts requiring damage/animation appearance review.

Big Lake baseline/candidate controls retain all 1,300 original frame/draw-count/
hash triples. Under the existing sunset azimuth 225°, the chosen cliff face is
in shade: it receives mostly uniform ambient and changes almost imperceptibly.
This is an additional limitation beyond the old normal maps' resolution; merely
authoring more detail does not create directional ambient lighting.

A second matched pair uses azimuth 45° on both baseline and candidate, retaining
the 9° elevation, strength 2 and other settings. At frame 1200, the lit cliff
comparison changes 3,521,368 image pixels, with mean absolute channel difference
5.14/255 across the image and 4.22/255 in a fixed cliff crop. This establishes a
native response to the content change, not art approval. Normal package load
reports all 3,998 keys and a peak observed lazy-world allocation of 87,023,616
bytes in the first candidate route. These screenshots are diagnostic captures,
not timing benchmarks or exhaustive vehicle/mission tests. A hidden candidate
attempt stalled at menu frame 4 before mission/material binding; only its owned
process was stopped, its record retained, and visible retries completed. No
cause for that intermittent menu stall is claimed.

Remaining work is individual height/mask authoring and approval, mission-level
visibility review of the static ranking, the source-limited shared tile, and live
damage/LOD/animation checks for the new vehicle/Strider content. The broad draft
generation must not be described as 519 final hand-authored materials.

## Authoring batch 1 — cliff height candidate

The first focused pass uses the imagegen skill's built-in tool to derive a
separate grayscale height candidate from the upgraded `txwall01` artwork.
The saved workspace inputs and exact prompts are under ignored
`local/material-authoring-r1/authored-batch1/`; no colour pixels are replaced.
These AI-assisted inputs are not measured height or guaranteed de-lighted data.

The [explicit height preparer](../tools/remaster-launcher/prepare_authored_relief.py)
pins the height, baseline catalog and upgraded bank identities. It screens each
bank variant for coarse UV drift before deriving stored-V tangent normals.
The selected `txwall01` input has zero-offset correlations .908–.938, with the
best tested displacement at zero for all five identities. This catches gross
misregistration but does not prove fine crack alignment or physical height.

Normals are now 1024×512 for those five identities. Periodic-plus-smooth height
decomposition reduces wrap-boundary discontinuities without replacing the
interior form. Calibration uses a .008 normalized height/tile ratio and .7
slope cap; median slope is .160, p95 .498, and .846% of samples hit the cap.
An earlier .055 ratio saturated most slopes and was rejected. Global world
strength remains 2; no 2x multiplier is baked into the image.

Both attempted `txwall06` AI inputs failed coarse layout review and are retained
as rejected artwork. The first had correlations about .54–.60 and a preferred
horizontal shift. The second retained incompatible ridge details. Its previous
aligned colour-derived draft remains active. Name-only sharing is not accepted.

Content checks show exactly five changed normal bindings and 3,993 byte-identical
world bindings, with all 3,998 keys preserved. The package is 473,702,568 bytes
(451.76 MiB), within the existing limit. Six synthetic checks cover broad relief,
flat inputs, boundary correction, displaced-feature detection and area calculation.

The selected native repeat matches all 1,300 original draw triples against its
fresh control. Both captures use azimuth45°, elevation9°, world strength2 and
replay video off. At frame1200, 3,284,205 pixels change, with full-image mean
absolute channel difference3.74/255. This is a content response and a coarse
appearance check, not final user art approval. One preceding candidate run had
a small camera/player-position difference from frame446 onward; it is retained
and excluded from the matched screenshots. The repeat, not that earlier run,
supplies the before/after evidence; no cause for the variation is assigned.

Only Material Normal Preview selects this first authored-height candidate.
Other launchers and native executables remain unchanged. Local evidence is in
`C:/Users/jcbla/MW34SunTests/material-authoring-20261018/authored-batch1/`.
The next content priorities remain the rejected cliff family, frequent ground
materials, prominent structures, and vehicle damage/LOD review. The full pass
is unfinished. Allow roughly 12–24 active work hours across sessions as a
provisional planning range, subject to revision as difficult layouts and vehicle
states are tested; this is not a promised completion deadline.

## Campaign terrain batch2

The [next campaign-ordered terrain batch](campaign-terrain-normal-batch2-2026-10-18.md) refines the first five
encountered families across23 C1 identities. One aligned AI-assisted ground
height candidate is selected; the cliff retry is rejected and four families
receive material-specific analytic refinements. All4,000 keys remain, with
3,977 other normals unchanged. Daylight and illuminating low-sun comparisons
each preserve2,000 original draw triples. Material Normal Preview selects the
batch at the unchanged1.5 strength; road artwork is retained. Screenshots are
posted to Drive. This is a review candidate, not completion of the full100.

## Campaign object batch3

The [next four campaign materials](campaign-object-normal-batch3-2026-10-18.md) now include a512px rock
color/normal candidate, aligned wall/plank height candidates and isolated atlas
panels. One misaligned wall identity retains its previous normal map. Material
Normal Preview selects the batch at1.5 strength, preserving earlier terrain and
roads. All2,600 original draw triples match the fresh control; ten narrow relief/
atlas checks pass. Screenshots are posted to Drive. Final art review and the
remaining campaign queue stay open.

## Campaign boat batch4 and ground selection correction

The [seven fishing-boat material families](campaign-boat-normal-batch4-2026-10-18.md) now use UV-authored
frames, ribs and vents with flat-glass/paint exclusions across23 reviewed keys.
All3,000 original draw triples match in ordinary and held-zoom comparisons;
fourteen targeted checks pass. Material Normal Preview retains1.5 strength,
existing colors, roads and previous materials. The older dedicated ground entry
was shadowing the batch2 height candidate; one entry is now corrected while55
others remain intact. Earlier images do not establish that that ground height
was active. The world package is495.10MiB under the unchanged512MiB ceiling.
Native screenshots are posted to Drive; close-up art review and the rest of the
campaign queue remain open.


## Campaign village and ruin normals — batch 5

The [next four campaign materials](campaign-village-normal-batch5-2026-10-18.md) now have three UV-authored village
relief candidates and one restrained ruin-grain refinement across 11 identities.
Only Material Normal Preview selects them, at unchanged strength 1.5. All 24 C1
color aliases match the upgraded sources; 3,990 other world normals and the
corrected dedicated ground catalog remain unchanged. Ordinary and original-zoom
pairs each match 2,600 draw triples. Village before/after screenshots are posted
to private Drive; the distant views and roof-focused zoom leave close-range art
review open. The 500.60 MiB pack leaves 11.40 MiB under the existing limit, so
future batches need explicit memory planning. Next are the queued `thedude`
materials and power lines. Acceptance remains 131/144; no commit or full-pass
completion is claimed.
