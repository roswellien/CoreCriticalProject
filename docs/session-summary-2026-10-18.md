# Development session summary — 2026-10-18

The website entry is [the October 18 MechLab update](mechlab/2026-10-18.md).
Dated entries belong in `docs/mechlab/`; this file is the technical session index.

The [stock material lighting integration record](stock-material-lighting-integration-2026-10-18.md)
continues the [main-host normal-mapping candidate](normal-mapping-integration-2026-10-17.md)
using the Big Lake lighting work. It connects original Avatar, Owens and Firefly
materials, separates geometric sunlight from normal-map enablement, and preserves
the [remastered menu and restored rollover wave](menu-rollover-restoration-2026-10-17.md).
The preview also carries the shared Big Lake sunset/sunrise/midday sun, sky and
ambient presets; sunset is the preview default. Preset resolution is shared by
launch checks and actual native launches, with the effective choice recorded.
It records pinned inputs, exclusions, native controls and the remaining scope.

The regular main Play and Big Lake profiles are not promoted by this stock-material
continuation. Concurrent main-host edits remain untouched. Source changes and
documentation remain uncommitted; original media, generated source, prepared
assets and executables remain local. No additional acceptance credit is claimed:
the verified count remains **131/144**.

The [automatic world-normal continuation](world-normal-mapping-preview-2026-10-18.md)
prepares terrain and objects from 36 pinned upgraded banks. It adds lazy normal
pages, preserves authored exclusions, and authenticates original camera
activation to exclude temporary effect views from world lighting. The regular
main Play and Big Lake profiles remain separate from this preview candidate.

The [C1M1 shoreline colour continuation](campaign1-shoreline-colour-2026-10-18.md)
compensates the brighter surf-water modulation with a water-only grade across all
13 frames, leaving foam, sand, original animation and black-key masks intact.
Sunset/midday 1,200-frame pairs and the final 1,800-frame control preserve original
draw triples. Only the Normal Mapping Preview bank map was updated. Its dated
record also documents the obsolete Escape input behind the test-window problem.

The [campaign lighting progression plan](campaign-lighting-progression-plan.md)
records the user's four-operation, twelve-beat storm-to-sunrise art direction for
later mission mapping. Its eight-day/27-hour-day schedule is explicitly a working
creative assumption pending retail roster and briefing verification; no mission
clock or gameplay timing is changed by the plan.

The [C1 sky/water continuation](sky-water-normal-preview-2026-10-18.md) adds a
separate preview with presentation-driven water ripples, matching surf-water
normals and cloud-specific sky relief. It uses the upgraded, color-corrected C1
banks and preserves the existing Normal Mapping Preview and regular launcher.
Cloud registration is excluded from ordinary opaque world lighting, preventing
the polygon-shaped sky edge exposed by the first candidate. The surf mask clamps
independently of the repeating ripple field. No campaign clock is activated.

The [lighting performance review](lighting-performance-2026-10-18.md) doubles
terrain/original-object normal strength from 1 to 2 in both preview profiles,
preserving replacement-model and dedicated sky/water strengths. Repeated
comparisons show no consistent strength-related slowdown. Visible presentation
checks, startup spikes and unresolved diagnostic stalls are recorded separately.
Profiling identifies significant automatic video-replay capture work; controlled
capture-disabled runs quantify it without changing interactive replay defaults.
No renderer rebuild or additional acceptance credit is included.

Following the performance review, the automatic replay video buffer is now off
by default in the native launch scripts and both installed MW3 Launcher entry
points. Photo & Replay retains an explicit opt-in checkbox, now describing a
30–35% performance impact instead of claiming zero impact or hardware encoding.
The previous default-on setting migrates off while preserving unrelated saved
preferences; later explicit opt-in/out choices persist. WPF build, settings
migration/persistence and synthetic launch-environment checks pass. Native host
binaries and other photo/game-state replay controls are unchanged.

The [material authoring continuation](material-normal-authoring-plan-2026-10-18.md)
identifies the top 73/289 terrain names (92.60% of static references) and 271/1081
object names (82.88%), plus large/landmark candidates and all identified vehicle
materials. Editable material-specific colour-derived drafts cover 515 world
names/1,738 refined bindings; four mech-bank vehicle names gain eight additional
bindings, preserving the existing 48 authored stock bindings. Seven Strider
normal gaps gain 1K candidates; detailed authored mech normals remain intact.
The separate Material Normal Preview selects this 444.26 MiB world package and
candidate sidecars without changing normal launchers. Native Big Lake draw
triples match in 1,300-frame controls; changing the sun to illuminate the selected
cliff exposes the new relief, while its sunset-shaded view remains nearly flat.
The queue and drafts begin the requested authoring pass; individual masks/art
approval and vehicle damage/animation coverage remain open. No commit or added
acceptance credit is claimed.

The first [focused cliff-height authoring batch](material-normal-authoring-plan-2026-10-18.md#authoring-batch-1--cliff-height-candidate)
adds an AI-assisted height candidate for five `txwall01` identities with 1K
normals, preserving the other 3,993 world bindings. Two `txwall06` image attempts
fail alignment and are excluded; an overstrong slope calibration is also retained
as rejected. The selected repeat matches 1,300 original draw triples against a
fresh control, and matched screenshots use the same illuminating sun position.
Material Normal Preview alone selects this revision. Individual art approval,
the remaining families and vehicle-state checks are still open.

The user then changed the active priority to the
[first100 campaign-encounter materials](campaign-first-100-materials-2026-10-18.md).
A separate diagnostic capture host records first world-texture submissions on
the original Operation1 Mission1 coastal/village route. All128 traced identities
resolve by full pixel keys; 14 dedicated water/surf identities are excluded,
leaving114 eligible groups. The first100 form the new work queue:22 terrain/
structure,71 world-object and7 shared/original-mech groups, with upgraded-source
audits flagged for the latter. Main executables and profiles remain unchanged;
the trace/control runs preserve all2600 original draw triples. The wider global
frequency queue is retained as backlog. No inventory entry is counted as newly
authored or approved artwork.

## C1 roads and softer terrain relief

The [C1 road artwork audit and correction](c1-road-artwork-2026-10-18.md) found
that several enlarged road replacements retained a soft original appearance.
The two C1 road families now use the existing detailed artwork across all six
bank variants, with new exact-pixel normal registrations where needed. Terrain/
world-object strength is reduced from2 to1.5 in the three preview launchers,
following the requested4→3 example. Two native comparison runs preserve all2,000
original draw triples; screenshots include a matching approach pair and a new
village view. Other campaign road artwork still needs review in mission order.

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


## Material priority adjustment — large scenery and vehicles

The user deferred tiny soldier textures and requested larger terrain, larger
structures and vehicles, including mechs. The [active authoring plan](material-normal-authoring-plan-2026-10-18.md)
now applies that priority while preserving historical campaign encounter ranks.
Next source-review targets are dark sand and sand transitions, then the tracked
vehicle family; prominent wall, bridge, dock, industrial and bunker surfaces
remain in scope. Small props and power-line hardware are deferred. Existing
batches, strength 1.5 and screenshot review remain unchanged. This adjustment
changes the work queue only; it makes no new rendering or acceptance claim.


## User playtest follow-up

The user reports that a retry completed Campaign Operation 1, Mission 1.
The earlier out-of-bounds surface rectangle failure remains unexplained; this
successful retry does not establish a crash fix or change acceptance 131/144.
Queue reconciliation records the previously completed `road01` restoration:
23 of the first 100 material families have received targeted work, including
partial drafts; 77 await that pass. Eight of those are explicitly deferred
soldier/power-line materials, leaving 69 candidates before further filtering
for large scenery and vehicles. These counts do not imply final art approval
or a complete census of the newly prioritized whole-game scope.


## User playtest and queue follow-up

The user reports completing Campaign Operation 1, Mission 1 on retry. The earlier
surface-rectangle failure remains unexplained; this is not a verified crash fix
or a change to acceptance 131/144. The first-100 queue has 23 families with
targeted work (including partial drafts), 77 pending, of which eight soldier/
power-line families are deferred. The other 69 still need filtering for larger
scenery and vehicles. D: reached zero free space during queue maintenance;
the CSV was checked complete and backed up to C:. Only 2.50 MiB of identical,
redundant batch 5 editable-map copies were removed from D:, with authoritative
maps preserved under the C: batch 5 candidate. More free space is required for
further workspace builds or asset generation.

## Storage recovered for continued material work

The [storage relocation](storage-relocation-2026-10-18.md) is complete. Older asset
revisions and all reports now live in the existing Games-drive archive, with
verified junctions preserving their original paths. Thirty-five current source
directories remain on D:. D: now has 1,314.39 GiB free. All 130 directory moves
and 31 loose package/checksum moves passed their checks; the acceptance-131
receipt remains byte-identical and Material Normal Preview passes its launch
check. Future report output also goes to Games. No renderer or profile changed
for this storage action. Campaign 1 material work resumes with the larger terrain,
structures and vehicles prioritized by the user. Acceptance remains 131/144.

## Campaign 1 larger-surface normal pass

The [Campaign 1 refinement pass](campaign1-normal-material-pass-2026-10-18.md) is
installed in Material Normal Preview after storage relocation. It covers 287
selected terrain/structure/vehicle families: 265 refined and 22 previous families
retained. The world package keeps 4,001 keys, changes 907 bindings and preserves
3,094 other normal images. Lossless deduplication and bounded resolution choices
leave it at 493.63 MiB under the existing 512 MiB limit. Upgraded colors and
strength 1.5 remain unchanged.

Original-mech variants gain 91 exact-content bindings; shared pads add two more,
with the tiny stock pad explicitly flat. Two earlier Mad Cat atlas drafts receive
panel/glass masks. The final dedicated catalog has 149 keys and 81 images across
two bounded pages, preserving the authored 256 MiB aggregate limit. Existing
replacement models, sun/sky/ambient work, water/cloud detail, remastered menu and
rollovers remain. Replay video stays off.

Three bounded 2,600-frame original-UI/save comparisons preserve all draw triples;
a final shared-catalog repeat does too. Eighteen Python checks and the native
material/cache contract checks pass. The final preview launcher check passes;
[before](https://drive.google.com/file/d/1fhzf9XC_CCSyyh0u0kmcFI17GiXtWhL3/view?usp=drivesdk)
and [after](https://drive.google.com/file/d/19ng5Dsz3xvcmatgItMb6EWd5D8_Kycvh/view?usp=drivesdk)
cliff screenshots are posted to the existing private Drive folder. Appearance
changes are restrained; distant village/C1M3 views are limited art evidence.
C1M4 has static coverage rather than a live playthrough; close-up art/combat/LOD
review remains. This closes the selected first refinement pass, not final art
approval. Acceptance remains 131/144 and no commit is made.

The separate standard launcher has a pre-existing controls-build/source-snapshot
mismatch and was left unchanged. Use Material Normal Preview for this pass; its
new host and snapshot match. The full scope ledger and limitations are in the
linked report.
