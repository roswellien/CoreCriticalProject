# Campaign-first normal-map authoring: first 100 materials

Date: 2026-10-18. Current user direction: work in campaign encounter order,
starting with the first 100 textures, instead of global frequency or Big Lake
showcase order. This supersedes the active ordering in the
[wider authoring plan](material-normal-authoring-plan-2026-10-18.md), while
preserving its existing artwork, selection data and verification evidence.
Acceptance remains **131/144**. No normal-map authoring completion is inferred
from an inventory or trace.

## Active batch

The [full Campaign 1 refinement pass](campaign1-normal-material-pass-2026-10-18.md)
now supersedes this list as the completion scope. Historical ranks remain intact:
88 entries are included/reconciled in that pass and 12 remain deliberately
deferred small characters/props or separate surf work. The CSV retains previous
states and appends the current treatment; prepared coverage is not final art approval.

The [first-100 queue](campaign-first-100-materials-2026-10-18.csv) contains exactly
100 distinct eligible material groups, all first encountered on the recorded
**Operation 1, Mission 1** walkthrough. This route found 114 eligible groups,
so later missions are not artificially inserted to fill the batch.

| Priority | Texture | Starting task |
| ---: | --- | --- |
| 1 | `txwall06` | Rework the cliff-height candidate; previous AI layouts failed alignment |
| 2 | `txgter_1` | Review and refine ground relief without amplifying grain |
| 3 | `beach01` | Author restrained sand relief; preserve shore transitions |
| 4 | `sandtrans1` | Match neighbouring sand height and repeat boundaries |
| 5 | `ltsand` | Refine broad/fine sand balance |
| 6 | `road03` | Separate road relief from painted colour and shading |
| 7 | `rockblok` | Review the rock prop/atlas layout |
| 8 | `txwall09d` | Inspect wall material and damage detail |
| 9 | `fishvill01` | Begin village-building panel/material masks |
| 10 | `fishvill02` | Continue village-building material work |

The list then follows boats, village structures, other world objects, terrain
and encountered vehicle/original-mech surfaces. It contains 22 terrain-marked
or structural groups, 71 other world-object groups and seven shared/original-mech
groups. The prior `txwall01` height candidate appears at priority69 and remains
preserved. Work proceeds from priority1; previous work is not discarded or
renumbered as newly completed.

The final selected group is `owens01_h`, first submitted at frame1620. The exact
trace keys, encountered bank variants, aliases and excluded surfaces stay local.
The CSV includes the first frame, trace sequence, material lane, source-review
status and existing authoring state for every target.

## What encounter order means here

The [optional capture hook](../../tools/remaster-launcher/campaign_texture_trace.inc)
records the first full-content material identity submitted by the world renderer.
It excludes frontend/HUD, sky-only draws and replacement-mech mesh draws, whose
already-authored normal maps remain separate. Water/surf/effects are classified
and excluded from this opaque-material batch. Original vehicle/mech surfaces
using the world texture path remain eligible.

This is **recorded draw-submission order**, not pixel-depth visibility: an object
submitted behind another object can enter the trace. Multiple textures in the
same first frame are tied by renderer submission sequence; it does not imply
one was visibly on screen before another. Different player routes or camera
directions can change the order. This is a reproducible practical campaign
authoring route, not a universal first-100 list for every playthrough.

The [queue builder](../../tools/remaster-launcher/campaign_material_queue.py)
sorts captures by explicit campaign mission order, then preserves the encounter
sequence. It requires complete dimension/format/pixel-hash matches, coalesces
identical aliases, retains different-pixel variants for later review, rejects
unresolved identities, and fails a short capture rather than padding from bank
or scene-file order. All 128 material identities in this capture are resolved:
97 through the existing world catalog and 31 through complete pixel matches in
the selected installed banks. Fourteen dedicated water/surf identities are
excluded, leaving 114 eligible groups.

The route enters the campaign through the original UI, switches to exterior view,
walks through the starting coastal/village area and turns the mech. It stops at
2,600 presented frames; this is not a mission-completion claim. The captures use
the same raw lighting environment on both hosts, not a claimed campaign lighting
schedule. The future campaign time/weather plan is still separate.

## Source audit before authoring

The upgraded-world catalog supplies pinned source identities for 93 selected
groups. Seven additional groups are matched in the currently selected mech banks:
`mcat20`, `owens16_h`, `footpad`, `owens04_h`, `owens14_h`, `owens15_h`, and
`owens01_h`. Several are small tiles. An installed upgraded bank does not prove
every individual entry has approved high-resolution artwork.

The existing stock Owens catalog registers the non-`_h` names. Matching its
reviewed primary material artwork by name alone to these other live variants
is not authorized evidence of correct UVs or matching pixels. Audit the approved
upgraded source and exact layout before adding or replacing these bindings.
Do not silently derive supposed new detail from an unchanged small original tile.
The queue explicitly carries this source-review requirement.

## Campaign progression

Recovered `maps.zrd` entries and mission-reader files identify this working order:
`c1m1`–`c1m4`, `c2m1`–`c2m4`, `c3m1`–`c3m6`, `c4m1`–`c4m6`.
The final three Operation4 mission-reader files reside in the `c4b` region; that
region is not a fifth operation. These 20 mission map identifiers replace the
unverified twelve-beat count only for this material scheduling task. The saved
lighting proposal remains art direction pending a separately reconciled schedule.
No mission data, campaign state, save or briefing is rewritten.

After the first100, extend the same encounter record through later missions in
that order, adding newly encountered materials once and retaining their variants.
Do not jump ahead to globally frequent textures or another test map merely to
fill a batch.

## Verification and execution boundary

The trace is compiled into a **separate local diagnostic host**, cloned from the
current preview. It uses the identical 37,201-object list (SHA256
`a0a4d56ff36b26d036ac8d646fe6357224732243e17a83919de6e2c9317e13cd`).
Only the optional render-submission trace is added; no guest/gameplay hook,
simulation change, native interpreter or executable fallback is introduced.
The main/preview executables and launcher selection remain unchanged.

The trace host builds and completes the route; its SHA256 is
`c49ab2c98fc9c34d943748355339b108246979b171c3c64f9b2b6d525e392a3b`.
Existing compiler warnings remain; a warning-free build is not claimed.
A matching run on the original preview host preserves **all 2,600 original
frame/draw-count/hash triples**. This establishes that the optional trace did
not alter that observed submission stream, not full mission fidelity or depth
visibility. Four synthetic queue tests check ordered ties/exclusions, no padding,
unknown-key failure and backwards mission ordering.

Local capture, route, source-index, roster and queue receipts:
`C:/Users/jcbla/MW34SunTests/campaign-material-order-20261018/`.
Three screenshots retain the route context. Original media, generated game
sources and binaries remain local. No new texture artwork is approved by this
reordering step, and no acceptance count or main-profile promotion changes.

## Road source correction after this capture

The [C1 road revision](c1-road-artwork-2026-10-18.md) replaces soft variants of
`road01`/`road03` with the detailed existing exports and registers their new
full-pixel identities. This queue remains a record of the original capture; its
order is retained and its old source pins are not silently changed. Artwork
quality must be checked separately from bank registration and file dimensions.
The three preview profiles now use world strength1.5, superseding the capture's2.
