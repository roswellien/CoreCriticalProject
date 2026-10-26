# Full-detail normal authoring continuation

The requested full pass remains open. Assets, editable height images and
receipts are local under `local/material-authoring-r1/full-detail-20261025-r1/`.
No pack has been published or promoted by this work. Acceptance remains 131/144.

## Authored candidates

Owens has seven corrected default material bindings; Firefly has four, including
two exact-color shared mechanical materials. Avatar has eleven, including three
shared materials, two new body tiles and six toe atlases. The original toe maps
and source-shader rebakes were flat; the selected candidates add restrained
procedural metal grain. All six toe UV comparisons have zero error. Both LODs
have prepared sidecars and exact installed-pack color-pixel checks. These are
prepared candidates, not final art or damage/animation acceptance. Legacy skins
share the chassis normal set and still require individual artwork checks.

The Campaign 1 structural pass re-evaluates existing UV recipes at full source
dimensions: 325 variants across 106 families, with 15 variants deferred for
layout or alpha review. Editable heights and normals are exported. Readback
checks cover dimensions, hashes, opaque alpha, vector lengths and slope caps.
Of these variants, 280 keys occur in the inspected installed world catalogs.
The exports contain about 1.06 GB of raw RGBA pixels; they are not installed.
This does not cover every mission, material, or deferred variant.

The subsequent deferred pass adds all 15 skipped variants. Three rock variants
use the existing explicit manual layout review, confirmed against its source
board. Six boat-window and six broken-window bindings use new frame recipes
from inspected RGB/coverage artwork. Glass interiors remain flat; coverage
below 250/255 and a two-pixel guard also force flat normals. RGB565, ARGB1555
and ARGB4444 identities are checked against the stored source and converted
pixel hashes. Thus these two batches contain 340 full-size candidates across
108 families; native art/alpha acceptance remains open.

The bounded native review presented 1,800 menu frames and zero gameplay draws.
It provides no mech-material appearance evidence. Correct the UI input route
before claiming a native comparison.

## Transport defect and change

Seven exported maps cannot fit a 16 MiB uncompressed world page. The new optional
BWNRM3/BWSNR3 transport uses channel deltas and bounded literal, repeated-byte
and signed-nibble tokens. Native decoding writes directly to the final RGBA
allocation and verifies the existing full-pixel hash. It preserves dimensions,
all channel values, material bindings and explicit exclusions. Version 1/2
readers remain supported; existing Python writers still default to version 2.
Snapshot-copy helpers include the new codec header.

One 2048×4096 candidate requires 33,554,432 raw bytes. Its complete compressed
page is 12,122,186 bytes. Python readback and a newly compiled native C++ reader
recover its exact pixels/hash. Asset-free checks cover token bounds, signed
deltas, truncation, padding, hash corruption, exclusions and lazy-page behavior.

This advances authored asset transport and its parser contract only. The running
host has not been rebuilt or advertised as supporting these new formats. No
installed pack manifest or capability declaration has been changed. The 16 MiB
world page, 512 MiB package and 512 MiB resident-world limits remain unchanged.
Compression does not solve resident growth: the current world loader retains
every page it has loaded. Bounded residency, complete package planning and native
visual review remain necessary before full-resolution deployment.

## Operation 1 compressed candidate

`operation1-fullsize-compressed-r1/` now contains a complete candidate catalog:
all 1,250 existing world keys, 295 full-size replacements, and 955 byte-identical
retained normal bindings. It has 23 pages totaling 294,690,403 bytes (about
281 MiB). Every page passes exact Python pixel/key readback and the compiled
native parser's decode/content-hash checks. Source pages are rehashed before
the final manifest is written; interrupted generation does not publish a
loadable manifest. Page, aggregate package and per-pack decoded limits remain
enforced. The candidate is not selected by an installed profile. These checks
decode pages individually and do not establish bounded live residency or native
appearance; remaining Operation 1 materials and all other operations stay open.

## Retained CPU page cache

World pages now evict least-recently-used retained CPU pixels before crossing
the existing 512 MiB limit. Their normal slots, dimensions and content hashes
remain stable. Identity lookup does not reload evicted pixels. The actual
upload-copy branch and texture warmup restore them only when needed. Reload
rejects changed image identities or local bindings, preserving
authored exclusions and existing draw/renderer keys. Scene upload references
own copies; this change does not destroy or recycle Vulkan resources.

The native fixture traverses the actual 23-page candidate twice: 950 stable
normal slots, 36 evictions, and a peak 533,741,568 retained pixel bytes, below
536,870,912. Checks cover LRU ordering, exact reload, unchanged surface versions,
no appended slots on the second traversal, altered-payload rejection and the
existing compressed/uncompressed/disabled paths. This establishes retained CPU
cache behavior, not a whole-process memory ceiling. Decode buffers, scene upload
copies and GPU residency are separate. The installed host remains unchanged;
private candidate build/live checks are described below.

## Additional authoring and live candidate

Seven more families (`apc01`, `bulldog02`, `bunkr01/02/04`, `build08/10`) now
have 15 full-size candidates with inspected, explicit UV features. They retain
camouflage as paint and add shallow vents, access plates, firing slits, masonry
joints and damage recesses. All layout screens, source identities, normal-file
readback and vector/slope checks pass. Their additive private authored catalog
preserves the original authored pages without duplicate keys. The accumulated
world exports now cover 355 distinct pixel keys across 115 families; this is
not the full requested material scope or final art approval.

A private host was rebuilt from pinned current host sources while preserving
the existing detail-role, warmup and initialization paths. Training reached
500 presented frames, with 295 gameplay frame records. The first C1 attempt
resumed a copied C3 pilot and hit stale replacement sidecars; its failure is
retained. A pinned C1 pilot and current composed resources corrected that route.

The first bounded CPU-cache implementation unnecessarily restored pixels during
identity lookup. A live C1M1 attempt reproduced repeated page thrashing and was
intentionally stopped. The corrected upload-only path completes 2,200 C1M1
frames with 1,942,851 logical draws. Its logs contain 54 page loads and 42
evictions, versus 881 loads/870 evictions in the shorter failed attempt; these
are defect-reproduction counts, not a controlled FPS benchmark. Peak retained
CPU pixels in the completed run are 534,487,040 bytes, below the existing ceiling.

Capture inspection also exposed a presentation-policy defect: `MW34_SUN_NORMALS`
sets the shader's diagnostic RGB-normal output, while `MW34_NORMAL_MAPS` enables
perturbation. Enabling authored maps now leaves diagnostic display off, with a
regression check. The ordinary lit C1M1 repeat completes the same 2,200-frame
route and stores full-resolution captures at frames 1600 and 2100. These are
coarse scene checks; close-up seams, damage/LOD/animation, alternate mech skins,
GPU residency across missions and the remaining authored scope remain open.

The subsequent lit baseline uses the same private binary, pinned pilot, input
route and lighting with installed low-resolution world maps. All 2,200 present
records match in logical draw and lighting-role counts. However, the distant
captures change zero pixels at frame 1600 and only three at frame 2100. They do
**not** demonstrate visible new relief. Registration/prewarm hits likewise do
not prove on-screen use. Targeted close-up material views and directional-light
comparisons are still required before promoting this content.

## Large concrete surfaces: source reconciliation

Six further families (`bwall04/05`, `c1conc02/03b/04/05`) have explicit joints,
vent louvers, cracks and shallow pits, with hazard paint, lettering and landing
pad markings suppressed as height. The historical source inventory produced
31 full-size variants (11 numerical layout screens and 20 explicit manual
broad-layout decisions). Their heights/normals and failed screens are preserved.

The installed-key check then showed that none of those 31 historical identities
matched the selected C1 replacement-bank pixels. They must not be counted as
current runtime coverage. The actual `MW34_REMASTER_BANKS` index from the native
run was followed to its six C1 banks; 32 corresponding entries reduce to 15
distinct current pixel identities. All 15 were regenerated at their actual
source dimensions after inspecting the current variant boards. Current layouts
pass the unchanged numerical screen, and full source/converted-pixel hashes,
vector lengths, slope caps and output readback are checked.

The current authored overlay is 15,213,226 bytes. It retains the original
authored pages and the earlier vehicle/building overlay, adds these 15 exact
keys without duplicates, and contains 94,339,072 combined unique decoded bytes,
under the unchanged authored budget. It remains a private candidate. The 31
historical exports and 15 selected-bank exports are separate versions, not 46
current completed materials. Targeted native use, close-up appearance and seam
review are still required.

## Current selected-bank recipe regeneration

The actual native-selected bank index has now been inventoried across all 38
banks, with source-plane SHA-256 and converted runtime identities recorded.
The inventory contains 36,739 supported runtime-variant records and explicitly
records 168 unsupported entries. These are source records, not unique visible
materials or authored coverage counts.

Existing explicit UV recipes were re-evaluated against those current pixels,
using their historical reviewed layout as the reference and retaining the
unchanged coarse alignment threshold. The completed local batch contains 317
full-resolution candidate variants across 113 families; 25 variants were
deferred for layout review or separate alpha masking. Every generated candidate
checks full source identity, exact dimensions, normal vector length/slope and
PNG pixel readback. Heights, recipes, source references and deferrals are in
`local/material-authoring-r1/full-detail-20261025-r1/selected-current-recipes-r1/`.

This advances the current selected-bank asset-authoring boundary, correcting
the historical-source mismatch. It does not advance native-game acceptance,
establish visible material use, or provide final close-up/seam approval. This
batch is not packaged or promoted; the full remaining world and mech scope,
including skin/damage/LOD validation, remains open. Counts overlap earlier
exports and must not be added to them as distinct completed materials.

The 25 deferred current identities now also have local full-size candidates:
12 alpha-format variants, ten building variants and three rock variants. Source
boards revealed that current `build01/02/03` are different window-panel artwork,
so new UV frame recipes replace the historical plaster-wall recipes for these
keys. Boat glass and broken-window relief stays on the frames, with all coverage
below 250 and a two-pixel neighboring guard forced to flat normals. Original
coverage is never differentiated into height. Exact source identity, dimensions,
normal vectors/slope, alpha guard and PNG pixel readback are checked.

`selected-deferred-authored-r2/` holds the 22 frame/building candidates. Its
three rock exports are superseded by `selected-current-rock-r4/`: preview review
rejected inherited horizontal cuts, sharp polygon boundaries and a too-shallow
rounded version. The current rock candidate uses authored stone contours with
UV-scaled rounding and stronger relief; earlier attempts remain intact. Lit
tangent-space previews were inspected, but fine contour alignment and tile
seams still need review. The original numerical layout failures remain recorded;
manual authoring does not turn them into passing numerical screens.

These 25 identities complement the earlier 317, with three rock replacements
selected separately rather than added again. They remain private unpromoted
assets, pending current-key packaging, native directional-light use and final
art review. Full remaining world/mech scope is still open; acceptance remains
131/144.

## Current C1 packaging and native integration

The current-source set contains 357 unique candidates, including the separately
selected rounded rock replacement and 15 current concrete keys. Of these, 347
match selected C1 source identities. `operation1-current-fullsize-r2/` preserves
the installed catalog, replaces 310 maps, adds 37 exact current keys and retains
940 bindings byte-identically on decode: 1,287 bindings in 28 compressed pages,
361,190,352 bytes total. Python readback verifies exact pixels and all original
keys. Every page passes the compiled native parser. Two full native CPU-cache
traversals preserve 987 slots, with 45 evictions and peak retained pixels of
536,608,768 bytes, below the unchanged 536,870,912-byte ceiling.

Authored precedence would otherwise conceal some new maps. The paired private
`current-authored-precedence-r2/` catalog removes 30 superseded non-null bindings,
retains 92 unrelated bindings exactly and preserves explicit flat exclusions
(none overlaps this replacement set). Both resulting pages pass native decode.
This filtered catalog is paired only with the matching C1 world candidate;
installed profiles and assets remain unchanged.

The private native host completes `c1m1-current-fullsize-r3`: 2,200 Vulkan
presents, 1,942,851 logical draws and 912,205 GPU draws, matching the prior route's
totals. Termination is the expected frame-budget exception. The earlier `r2`
run directory records an unsuccessful prelaunch setup with a wrong executable
path; no game was launched there. The completed run uses the existing private
host with SHA-256 `6cea4c878d739afe1f36267ad4c0f3cc3de42fa6635ed07235c1d1f0afa010c1`.
Live normal paging records 58 loads, 45 evictions and peak retained CPU pixels
of 536,281,088 bytes. This is not a total-process or GPU memory bound.

Compared with the same-route lit baseline, frames 1600 and 2100 change 55,279
and 55,252 pixels respectively. The frame-1600 differences occupy the cliff and
shore/building region (bounds x0..2400, y311..694 in the 3440x1440 capture), with
no differences below y719. The shore comparison was inspected. This advances
native candidate integration and demonstrates coarse world shading changes,
but remains too distant for fine normal/contour/seam approval. Captures and the
comparison are retained in the run directory. Other regions, remaining authored
world content and mech skin/damage/LOD review remain open; no promotion or
acceptance-count change is claimed.

## Current prepared mech source reconciliation and Strider candidates

The selected prepared model pack was checked by actual texture/normal batch
bindings, rather than assuming that the older editable registry describes its
content. `current-prepared-mech-dimensions.json` records 2,176 exact-size,
512 undersized-normal, 624 oversized-normal and 400 explicit-flat material
bindings. These counts repeat across bundled skins and both LODs; they are not
unique authored maps. Separate skin packs such as Sommerset are explicitly
outside these counts. Header sizes do not prove art/UV alignment or full detail.
The installed pack still contains earlier small Avatar/Owens/Firefly normals;
their previously created private replacements have not been promoted.

The current pack also exposes nine undersized Strider materials and Orion's
Collar. Strider `mech01` is 512x1024 with an installed 32x64 normal; five armor
atlases are 2048x1024 with installed 1024x512 normals. `weap_hole`, `footpad`
and `strider10` likewise have smaller installed normals. The selected albedo
words were compared exactly with the vertically flipped RGB565 conversion of
the editable source artwork before new authoring.

`strider-fullsize-authored-r1/` contains nine new explicit UV-recipe candidates
at the actual selected texture sizes: pipe collars and vents, foot ribs,
weapon-port rings, armor/access frames, mounts and grille slots. Painted blue
markings are suppressed from grain/height structure. Original normal pixels
were not enlarged to produce these maps. Source identities, dimensions, vector
lengths, slope clipping and PNG readback pass; the source/lit/height board was
inspected. These are preliminary structural candidates: fine hardware/contour
matching still needs refinement, alongside skin alignment and native motion,
LOD and damage review. They are not staged over the installed normals. Orion's
Collar remains open, and the broader goal is still incomplete.

## Orion collar full-size candidate

`orion-collar-fullsize-r1/` now contains a new 1254x1254 collar height/normal
candidate, replacing the earlier 1024x1024 resolution in private staged copies.
The editable source was verified against the exact selected packed RGB565
pixels with the required vertical orientation. Thirty-nine explicit features
follow the inspected panel seams, keyhole contour, channels, fasteners and
access details. Blue paint and a dilated boundary contribute no color-derived
grain. Vector length, slope bounds and PNG pixel readback pass; clipping is
0.03294 percent. Source/lit/height previews were inspected.

The two staged BWNRM2 sidecars retain all unrelated image records and the batch
headers byte-for-byte. The actual native `read_normals` parser validates them
against their corresponding selected albedo material orders: 33 close batches
and 23 distance batches, five images each, one changed collar image. The native
check also compares every unrelated decoded pixel, image identity and binding
with the selected original sidecar. They remain local and uninstalled.

All eight bundled collar skins were decoded from their current packed pixels
and inspected together. Their broad seam/keyhole layout agrees, including the
camouflage skins; this does not approve fine contours or native seam behavior.
The default height source avoids importing camouflage as relief. Native Orion
directional-light views, fine UV alignment, damage and LOD checks remain open.
The earlier statement that Collar was open describes the prior state; it now
has a staged candidate, not final art approval. Full world/mech completion and
131/144 acceptance are unchanged.

## Strider hardware corrections after source review

The preliminary full-size candidates were not treated as approved art. Direct
source review found concrete defects: `mech01` represented curved pipes as flat
bars, `footpad` invented five ribs where the selected artwork has three, and
`weap_hole` treated a camouflage boundary as a panel and used a square flat mask
inside a circular hole. Those earlier exports remain preserved and superseded.

`strider-hardware-refined-r3/` replaces the first two candidates with four
analytic rounded pipe profiles, retained collars/vents and the measured three
beveled foot ribs with shallow scuffs. An earlier r2 pipe preview was too weak;
the r3 pipe strength is increased, with 2.8265 percent slope clipping beneath
the unchanged five-percent limit. The footpad has zero clipped samples.
`strider-port-refined-r2/` supplies a rounded annular weapon-port rim, a circular
flat interior and metal-only fine grain. The painted substrate remains flat;
no camouflage edge is authored as structural height. Port clipping is zero.

All three candidates match exact selected source dimensions and verified
RGB565 words, pass vector length and PNG readback checks, and have inspected
source/tangent-light/height previews. These are corrections to three of the
existing nine identities, not three additional maps. Fine contours, remaining
six preliminary Strider atlases, skin alignment and native LOD/damage/seam/light
review are still open. No candidate was installed or promoted.

## Remaining Strider atlas refinement and staging

`strider-six-atlases-refined-r2/` revises the remaining six undersized identities:
`stride_d05/04`, `strider06/stride_d02`, `stride_d01` and `strider10`. Recipes use
current source-pixel measurements for panel contours, access hardware,
fasteners, mount rings, vent slots and cockpit bezel/grille details. Cockpit
glass has inset polygon flats; blue paint boundaries are suppressed from grain.
The six current source identities and dimensions were checked against packed
RGB565 words. Vector/slope and PNG readback checks pass; clipping ranges from
0.0149 to 1.5518 percent. Source/light/height previews were inspected. Fine art
and motion validation remain open; full-size output alone is not approval.

`strider-refined-staged-r2/` combines these six with the two corrected hardware
maps and circular weapon port, replacing nine images in each selected Strider
normal sidecar. The current native parser checks both against the actual packed
albedo material order: 92 batches and 22 images in each sidecar. All nine new
dimensions match their selected textures; every unrelated image's decoded pixels,
dimensions, hash and binding remain exact. Original batch headers and unrelated
binary image records are also retained byte-for-byte. Authoring/source receipts
and output hashes are pinned in the staging receipt.

The installed Strider/Orion packs and launcher remain untouched. These staged
candidates still require bundled-skin alignment, live directional lighting,
close-up contours, UV seams, damage and LOD review. Other mech materials and
world coverage remain within the original unfinished goal.

## Live Strider/Orion selection and gameplay comparison

The current retail Mech Lab list is alphabetized; the inherited script selected
Annihilator rather than its labeled Bushwacker row. The isolated input route was
corrected using captured list geometry. `mechlab-orion-candidate-r2` confirms
Orion selection and its 33-batch close-model load. A matching original-normal
run completes with identical draw totals and pixel-identical frames 650/699.
This is not visible collar-relief evidence: the current host's
`sun_capture_model` explicitly excludes frontend/status previews. Environment
normal overrides are read directly when the model loads; lazy catalog replacement
was investigated but is not the explanation. No lighting policy was changed to
manufacture a passing preview. Earlier incorrect-selection runs are retained.

The corrected list route also selects Strider. The original Accept/Launch flow
then reaches gameplay in `strider-gameplay-candidate-r1` and matching
`strider-gameplay-original-r1`, each completing 2,200 Vulkan presents with the
expected frame-budget exception. Both record 1,692,939 logical draws and 911,681
GPU draws. Model logs identify default Strider LOD0 world draws (`preview:false`,
role 0), distinct from its status preview. The private runner applies staged
Strider and Orion sidecars after composing the profile; baseline runs explicitly
restore their selected original sidecar paths. The host and original gameplay
inputs remain unchanged.

Matched gameplay captures at frames 1600 and 2100 each change 5,935 pixels,
confined to x1507..1960, y894..1439 in the 3440x1440 image. The inspected
before/after crop shows the rear armor, pipe/port region and legs; background
and HUD are unchanged. This demonstrates visible staged-normal use on those
surfaces, not all nine material views or final art approval. Fine contours,
front/underside views, alternate skins, damage, UV seams and LOD transitions
remain open. Orion still requires a gameplay-lit collar view. Nothing was
installed, promoted or credited toward the 131/144 acceptance count.

## Orion gameplay-lit comparison, limited exposure

The corrected Orion Mech Lab selection now continues through the same original
Accept/Launch route as Strider. `orion-gameplay-candidate-r1` and
`orion-gameplay-original-r1` each complete 2,200 Vulkan presents, with 1,562,751
logical and 776,308 GPU draws and the expected frame-budget termination. Only
the staged/original mech normal bindings differ; the host, route and manual
lighting are the same. Source model selection and 33-batch close-model load are
confirmed, followed by gameplay rendering at the full target resolution.

Frames 1600 and 2100 each differ by just 123 pixels, bounded by x1777..1819,
y1296..1298 at 3440x1440. The inspected rear-view comparison exposes only this
thin strip of changed collar shading. This is insufficient for broad collar
contour or seam approval and must not be described as a useful full collar
close-up. The captured route is retained; a side/front or elevated camera is
still needed. Existing photo/orbit controls were located, but this private host
does not expose the old capture-key/view environment instrumentation, and photo
controls read host key state rather than the guest DirectInput script. No
instrumentation layer or altered lighting policy was added to bypass that
review gap. Candidate assets and the complete original goal remain open.

## Interactive photo-control attempt

The existing native photo controls were tried through the Windows computer-use
API against the uniquely identified private game window. `orion-photo-review-r1`
reached its 12,000-frame bound before interaction; terminal process/run evidence
was checked before creating `orion-photo-review-r2`. The second bounded run also
closed normally at its expected frame-budget exception (224.453 seconds), with
no overlapping game process or change to the host, installed profile or assets.

Two F11 attempts, including one after explicit window activation, produced no
visible photo-mode transition. F9 did succeed and saved the native screenshot
`orion-photo-review-r2/photo-review/screenshots/mw3_20261026_050435_545.png`.
This distinguishes responsive host capture input from the unresolved photo-mode
transition; it does not establish the cause of the F11 behavior. A later F11
action encountered the already-closed window and was not retried with its stale
handle. No orbit/side close-up was obtained, and none of this grants new art or
acceptance credit. The collar camera gap remains explicit; repeated identical
camera attempts should not be treated as normal-authoring completion.

## Operation 2 current concrete/wall candidates

The actual selected C2 bank inventory supplied 18 distinct variants across
`c2conc01/03` and `canlwal02/03`. Current variant boards and the largest concrete
sources were inspected before new UV recipes were authored. Explicit paths
follow the concrete crack networks, canal joints and vent structure at each
actual source size, including 4096x512 wall strips and 2048x2048 surfaces.
Canal-wall fine grain is independently seeded physical concrete roughness;
algae, damp staining and color variation are not differentiated into height.
The two mossy `gwall` atlases (nine current variants) were inspected but remain
deferred for separate sculpted rock contours.

`operation2-concrete-authored-r1/` retains all 18 heights, normals, recipes,
current source identities and source/light/height previews. Full source/hash,
dimension, vector length, slope and PNG pixel checks pass. Manual broad-layout
review is recorded explicitly rather than converted into numerical alignment
passes. Preview inspection is preliminary; fine crack/edge matching, UV tile
seams and native directional-light review remain required.

The additive private overlay is 43,275,240 bytes and contains all 18 exact keys;
all 18 also match the retained installed Operation 2 world metadata. Existing
authored pages remain intact with no duplicate binding keys. Combined unique
decoded authored pixels total 222,265,344 bytes, beneath the unchanged budget.
Python readback is exact and the compiled native parser decodes all 18 bindings
and 14 deduplicated images with their content hashes checked. The combined authored manifest
is local only; installed profiles/assets and 131/144 acceptance are unchanged.

## Operation 2 mossy rock candidates

Nine current `gwall01/02` variants now have full-size candidates, including
2048x4096 atlases, in `operation2-rock-authored-r2/`. Their existing source
boards and enlarged primary views were inspected. Broad relief uses authored
rock contours and rounded profiles independently of albedo brightness; moss
colour islands and a four-pixel neighboring guard contribute no fine grain.
The underlying rock geometry continues beneath moss rather than making moss
green intensity into a raised boundary.

The first export's flat-topped polygon mounds and straight cliff-mass cutoff
were rejected after preview inspection. The retained r2 uses continuous
elliptical profiles fitted to authored contour points and a varying, inspected
left cliff boundary. Existing r1 exports remain preserved. New source/light/
height previews were inspected, and full source identities, exact dimensions,
normal vectors, slope limits and PNG pixel readback pass. Clipping stays below
0.629 percent. Fine strata/contour matching and tiled seams are still unresolved;
these are broad sculpting candidates, not final art approval.

The additive overlay is 39,754,047 bytes. All nine keys match the retained
Operation 2 world metadata. Prior authored pages remain intact with no duplicate
keys; combined unique decoded authored pixels total 423,591,936 bytes, under
the unchanged 512-MiB ceiling. Python decoded readback is exact and native
parser/content-hash checks pass. Further global authored additions must respect
this existing limit rather than raising it; the streamed per-operation world
lane remains available for the larger scope. No installed pack/profile changed,
and native directional-light, seam and remaining world/mech work stays open.

## Streamed Operation 2 assembly

`operation2-current-fullsize-r1/` combines all 111 authored current C2 keys:
84 shared current-source candidates and the 27 new concrete/rock variants.
Every original world key remains: 111 maps are replaced, no keys added, and
1,245 bindings retained byte-identically on decode. Explicit flat bindings are
preserved; none overlaps this replacement set. The package contains 1,356
bindings in 22 v3 pages, totaling 187,002,092 bytes. Page/file and decoded-pack
limits are unchanged, exact Python readback passes, and all pages pass the
compiled native parser/content-hash check.

Two native CPU-cache traversals retain 1,041 stable slots with 31 evictions and
peak retained pixels of 534,183,936 bytes beneath the fixed 536,870,912 ceiling.
This validates CPU page loading/eviction, not GPU residency or visible art.
The paired `operation2-authored-precedence-r1/` catalog removes 32 superseded
non-null bindings, preserves 117 unrelated bindings exactly, and preserves
explicit flat exclusions (none overlaps). Every retained page passes native
decode. The local `private-native-environment.json` provides the two paired
catalog paths with receipt pins for the existing compatible private host.

The recent Strider/Orion gameplay-review environments were also inspected:
their world normals still point to the installed Training catalog. Consequently
those mech runs provide no native-art evidence for this Operation 2 package.
A selected C2 route, close-up directional-light/contour/seam review and the
remaining world/mech scope are still required. No installed assets/profile or
131/144 acceptance changed.

## Operation 2 deck, roof and airfield hardware

Fifteen current variants across `deck01`, `noruff01`, `airp10a` and `airp20`
now have full-size candidates in `operation2-deck-roof-authored-r2/`. Actual
variant boards were inspected, including aspect-ratio changes and black damaged
areas. Recipes follow physical deck joints/handles/fasteners, roof ribs/vents,
elliptical grille rims, grid bars and gate bracing. Painted chevrons, caution
stripes, a red oval and the roof arrow do not supply grain/structural height.

Initial r1 guards classified near-black pixels and dilated four pixels, visibly
suppressing thin intact grille members. R2 supersedes that attempt with exact
black pixels and a one-pixel neighbor guard; dark intact metal remains eligible
for relief. Normal guard masks are retained alongside editable heights. Intact
source/light/height previews and both most-guarded damaged-grille previews were
inspected. Exact current source identity/dimensions, vector lengths, slope limits,
black-guard flats and PNG readback pass. Fine hardware edge/paint/damage-border
alignment, tile seams and native directional-light checks remain open.

The additive private overlay is 26,285,143 bytes, with all 15 keys matching the
retained Operation 2 world metadata. Python decoded readback and native parser/
content-hash checks pass. Prior authored pages remain intact without duplicate
keys. Combined unique decoded authored pixels are 512,720,896 bytes, within but
close to the unchanged 536,870,912-byte ceiling. Further additions should use the
streamed world lane rather than enlarge this resident set. These 15 candidates
are not yet in `operation2-current-fullsize-r1`; the existing 111-map streamed
candidate and this additive set are separate versions pending reconciliation.
No installed resources, profile or acceptance changed. Full remaining world and
mech authoring/validation still applies.

## Operation 2 facade candidates in separate streamable pages

Nine current variants across `apt01/03/04` and `hotel08` now have full-size
candidates in `operation2-buildings-authored-r2/`. Source/variant boards were
inspected before explicit panel-seam, frame, vent and masonry recipes were
authored. Grain is independently seeded rather than extracted from baked lamp
halos or window brightness. Window interiors are explicitly flat; hotel mortar
is clipped to the inspected exposed-brick polygon so it does not cover intact
plaster. Review caught a wrongly horizontal upper hotel vent in r1; r2 corrects
it to vertical slots and preserves the earlier exports.

All nine source identities/dimensions, vector lengths, slope caps, window flats
and PNG pixel readback checks pass. Source/light/height previews were inspected,
including the corrected hotel vent. Fine facade, vent/window classification,
mortar/contour alignment, lamp-frame edges, tile seams and native directional
lighting remain open; these are candidates, not final art approval.

`candidate-pages/` contains two native-readable bounded pages, 18,223,865 bytes
combined. Python decoded readback is exact and each page passes native parser/
content-hash checks. These pages have not been appended to the near-full resident
authored catalog, and matching existing C2 world keys must be replaced during
streamed assembly rather than duplicated. The existing 111-map streamed version,
15-map deck/roof set and these nine facade candidates remain separate until
reconciled. No installed resources, launcher profile or acceptance changed; the
original whole-world and mech authoring/validation goal remains unfinished.

## C2 reconciliation preparation while another capture owns the GPU

The existing 111-map streamed set, 15 deck/roof maps and nine facade maps were
reconciled by exact key: 135 distinct current C2 candidates, with no overlaps.
`package_operation2_current_fullsize_r2.py` prepares their combined assembly,
but it has not run and its output directory does not yet constitute a package.
The existing r1 remains authoritative until a completed r2 receipt exists.

The closed Gorge mech-run surface-binding log was matched against the selected
bank inventory. None of `gwall01/02`, `c2conc01/03`, `canlwal02/03`, `deck01`,
`noruff01`, `airp10a/20`, `apt01/03/04` or `hotel08` occurs there. Shared source
keys occur across regions, so regional intersection counts alone do not prove
a C2 route. Gorge must not be used as the new C2-specific art validation route.

A preserved prior C2-probe pilot was located (6,822 bytes, SHA-256
`4a9785bff582fdb6239a06d506612069d6cbf6a327fe55e1b99e72ebcfdea83c`).
Its bytes contain no explicit mission identifier; the old probe ended in a
ReadFile ownership failure before an expected frame-budget stop. Its directory
name therefore proves neither mission selection nor a valid current route.
`run_operation2_materials.py` prepares an isolated unmodified pilot/config copy
and original Load UI route for a future attempt; it is unlaunched and must be
validated by successful mission-reader identity and current material use.

Fresh process inventories found separate owner capture jobs (Marauder, then
Bushwacker/Sommerset) using `D:/CoreCriticalOrbit-20261025-r1/CaptureHost/`.
PID 38324 was confirmed live through a bounded wait during this work. No game
or heavy packing job was launched alongside that capture queue, and none of its
processes or outputs was changed. This is preparation/route evidence and a
verified wait, not new normal-art approval or a completed combined package.

## C2 combined full-size package completed: 2026-10-26

`operation2-current-fullsize-r2/` now has a completed receipt and manifest:
1,356 existing bindings, 135 exact current-key replacements, 1,221 unrelated
bindings retained byte-identically on decode, and no added keys. All 24 bounded
pages total 230,543,814 bytes. Source/authoring pins, exact Python readback and
native parser/content-hash checks pass. This supersedes the preparation-only
state above for this private package; the historical r1 is preserved.

Two native CPU cache traversals pass: 1,041 stable image slots, 38 evictions,
534,872,064 peak retained bytes, within the unchanged 536,870,912-byte cap.
This bounds retained CPU pixels only, not total process or GPU memory.
`operation2-authored-precedence-r2/` retains 117 unrelated authored bindings
and removes 47 superseded nonnull bindings, with no flat-exclusion collision.
All four paired authored pages pass native decoding. The matching pair prevents
older authored maps from masking the streamed C2 replacements.

The advanced boundary is authored full-size C2 assets -> exact-key streamed
catalog -> native page decoding and bounded CPU reload. No live C2 shading,
seams, fine-detail approval, installed-resource change or acceptance credit is
claimed. The isolated C2 save route remains untested. Another owner launched
`CaptureHost/mech-marauder-original-rolling-hills-3440` (PID 32188) during the
CPU checks; no competing gameplay capture was started or owner output changed.
The whole-world and mech normal authoring/review goal remains unfinished.

## Additional C2 roof candidates: six current variants

`operation2-roof-extension-sources-r1/` extracts and validates the six current
`noruff02/03/04` keys against actual bank bytes. Source/variant boards were
inspected. `operation2-roof-extension-authored-r3/receipt.json` records six
new exact-size candidates, including 2048x1024 and 1024x2048 maps. Their artwork
uses explicit grille channels, panel joints, pipe relief and analytic curved
fan/intake rings, plus independent seeded fine metal grain. Pale paint stripes
are omitted from relief; exact black/alpha openings and a one-pixel guard are
flat. No resized normal or albedo-luminance height conversion was used.

The first attempt stopped on an out-of-range radial endpoint; its partial output
is retained. r2 bounded those endpoints but preview review found misplaced fan
centers/radii. r3 corrects those broad positions and retains earlier attempts.
All six pass source-identity, exact dimensions, vector-length and PNG byte
readback checks. Source/tangent-light/height boards were inspected, including
the corrected three-fan board. These are broad-detail candidates: precise
housing contours, blade/fastener classification, vent alignment, fine wear,
seams and native directional lighting remain open. They are not appended to the
resident catalog or the completed 135-map streamed package.

This advances source artwork -> six authored full-size normal PNGs, not native
visual acceptance. The separate Marauder capture remained active during this
work; no game was launched or owner process/output modified. Whole-world/mech
completion and acceptance credit remain unchanged.

## Roof fan refinement and native page check

Full-resolution inspection of `noruff04` found that r3's fan centers were still
too low and its eight generic radial marks did not match the source. The r4
revision measures centers/outer radii directly on the 1024x2048 source, replaces
those marks with six mounting straps, adds rounded annular plate edges, bolt
seats and recessed blade bands, and explicitly flattens each bore. Top slots,
center service plate/fasteners and horizontal vents use measured source points.
The revised source/light/height preview was inspected. The analytic blade count
and fine wear are still authored approximations, not recovered geometry or final
art approval. Earlier candidates remain intact.

`operation2-roof-extension-authored-r4/` contains all six exact-size maps. The
maximum clipped-slope fraction is 0.000703 (about 0.0703%); unit-length and PNG
readback checks pass. `candidate-pages/` packages six bindings/six images into
one 7,516,774-byte page (23,592,960 unique decoded bytes), with exact Python
roundtrip and native parser/hash checks. All six keys already exist in the C2
world catalog, so future integration must replace those keys, not append them.
The completed 135-map package remains unchanged; native light/seam review and
precise fine-detail approval remain open. This advances refined artwork through
native-readable transport, with no installed assets or acceptance changed.

The separate owner capture was rechecked live as PID 25100, Marauder gunmetal
Rolling Hills, with runner PID 24984. It was neither interrupted nor duplicated.

## C2 incremental integration: 141 current authored replacements

`operation2-current-fullsize-incremental-r3/` combines the completed 135-map
candidate with the six refined roof maps: 1,356 unique existing bindings,
141 current authored replacements, 25 pages and 238,060,252 bytes. Assembly
filters only the six replaced bindings out of five existing page tables,
retaining their compressed image payloads byte-identically. Every retained
binding in each filtered page has exact Python decoded equality; all five
filtered pages pass native decoding/hash checks. Other pages are immutable
hardlinks to the prior candidate. The new roof page already passes native
readback. Old unreferenced images remain inside their original page limits;
this avoids a full re-encode and does not remove unrelated images or bindings.

The existing `operation2-authored-precedence-r2` has no collision with any of
the six roof keys and remains the matching paired resident catalog. Native
aggregate cache check passes two traversals: 1,047 stable slots, 39 evictions,
533,913,600 peak retained CPU bytes, below the unchanged 512 MiB limit.
No total-process/GPU memory bound or native art approval is implied.

A live C2 route attempt was stopped by the runner's competitor assertion before
creating a run: owner ffmpeg PID 38296 was encoding the Sommerset orbit. Bounded
waits confirmed it live, then a fresh inventory showed a subsequent encoder
PID 34120. No game was launched and neither process was interrupted. The private
runner still points at the preserved 135-map r2 package; future review can use
the incremental r3 plus existing paired catalog after updating its recorded
paths. C2 save/mission identity and native lighting/seams remain unproven.
The advance here is six additional exact-key assets integrated into a native
readable, bounded streamed catalog. Installed resources and acceptance remain
unchanged; the full world/mech goal is still incomplete.

## Combined-catalog route attempt and preserved interruption

`run_operation2_materials_r3.py` now points at the incremental 141-map world
catalog and the existing matching authored precedence catalog. A fresh header
check confirms exactly 1,356 unique combined bindings and all 141 distinct
current authored keys present. This check covers combined key conservation,
not artwork quality.

The prior owner encoder PID 34120 finished. The isolated run
`native-runtime-candidate-r2/c2-save-route-current-r3` then launched native host
SHA256 `6cea4c878d739afe1f36267ad4c0f3cc3de42fa6635ed07235c1d1f0afa010c1`
as PID 4352. Its recorded first present was about 0.766 seconds. After 2.891
seconds the runner observed a new owner ffmpeg process, PID 28856, and terminated
only its own child as designed. Three presents contain zero scene draws. The
run receipt records the competing process and exit code 1. This is an interrupted
pre-mission attempt, not a C2 save/reader failure, expected frame-budget stop,
material-use result or art validation. All files are preserved.

PID 28856 was independently identified live as the owner's Marauder two-skin
video compositor; no owner process or output was changed. The C2 mission and
lighting review remain pending. Installed resources and acceptance are unchanged.

## Eight current C2 ventilation-fan candidates

`operation2-vent-fan-sources-r1/` validates/extracts eight current keys across
`ventfan01/02/03/x`, at 512x1024 and 256x512. Source/variant boards and the
full-resolution ventfan03 source were inspected. Separate blade polygons,
curved blade relief, casing rings, guard bars, hub/fastener seats and independent
fine grain are authored in `operation2-vent-fan-authored-r3/`. Exact black/alpha
openings and a one-pixel guard stay flat; no albedo brightness is converted to
structural height. Damaged fan geometry has its own recipe.

The r1 previews exposed an undersized damaged right blade and insufficient
curvature. r2 corrects these and adds exposed backing slats; r3 keeps those slats
out of the hub. Earlier outputs remain. All source/light/height family previews
were inspected, followed by the corrected damaged-fan r3 preview. Fine jagged
blade contours, casing alignment, rear-slot extents and native directional light/
seams remain unapproved; this is candidate artwork, not finished fan acceptance.

All eight exact-size/vector/PNG readback checks pass. The r3 candidate page is
2,379,752 bytes, with exact Python roundtrip and native decoding/hash checks for
eight bindings/eight images. All eight keys match existing C2 world metadata;
they must replace existing keys during reconciliation, not be blindly appended.
The 141-map combined streamed candidate and installed resources are unchanged.
The advance is eight additional current source variants -> authored full-size
maps -> native-readable bounded transport. Acceptance remains 131/144.

Owner encoder PID 28856 was still confirmed live at this turn's start; its
runner changed to the Marauder editing job. No competing gameplay was launched.
The full world/mech authoring and visual-validation goal remains unfinished.

## Fan integration and first successful current C2M1 route

Correction to the prior fan entry: the candidate-page receipt reports **four**
existing installed C2 key matches, not eight. Four ventfan02/03 current-source
keys were absent from that older world catalog. The r4 incremental assembler
correctly stopped at its all-replacements assertion; its partial directory is
preserved without a completed receipt. No installed data changed.

`operation2-current-fullsize-incremental-r5/` integrates all eight fan maps as
four replacements and four added current keys. It preserves all prior keys and
explicit-flat exclusions, checks exact retained bindings/native decoding on
filtered pages, and verifies 1,360 unique combined keys with no authored-resident
collision. There are now 149 distinct authored current-source keys, 26 pages,
and 240,439,780 bytes. Native cache traversal passes twice: 1,055 stable slots,
41 evictions, 533,708,800 peak retained CPU bytes within the existing 512 MiB
limit. The existing paired authored-precedence-r2 catalog remains appropriate.

After owner encoder PID 3576 closed, `c2-save-route-current-r5` launched the
private native host as PID 33924 with the incremental r5 catalog and unmodified
copied pilot/configs. It completed in about 74.953 seconds. Stderr confirms
`Campaign lighting: selected c2m1 from successful mission-reader open`, then
the intended 2,600-frame Vulkan budget stop (exit 1). Submission reports
3,062,123 logical draws and 1,311,002 GPU draws. This proves the previously
unproven saved-pilot route now reaches C2M1; it is neither the earlier ReadFile
failure nor an owner-process interruption.

`current-authored-binding-review.json` joins actual model-log surface binding
keys to current source inventory and finds 49 authored keys with nonnegative
normal indices, including concrete/canal/rock, deck, roof, facade, airfield and
all four vent-fan families. Registration alone is not visibility. Captures at
1190/1600/2100/2500 were saved; the 2100 overview was inspected and shows a
wide outdoor scene behind the mech with distant ruins/nearby vehicles. It does
not provide the needed close surface, fine-contour, seam or matched baseline
comparison. No full-art approval, installation, acceptance change or whole-goal
completion is claimed. The advance is the combined authored catalog reaching
verified live native C2M1 and its actual material binding path.

## C2 loaded-pilot movement route resolved

Two isolated r6-runner routes completed at the expected 2,600 Vulkan presents
with successful C2M1 mission-reader identity. The runner now accepts an explicit
campaign2 input script. `c2-forward-material-review-r1` moved the default Up
scan-code events to frames 1350-2250 after confirmed loading, but its 2100
capture remained stationary. This disproves timing alone as the cause; it is
not useful close-up evidence.

`c2-forward-material-review-r2` changes only those movement events to W (DIK
0x11), retaining the same pilot, host, assets and original camera key. Its 1600
capture visibly approaches the ruins and reads 76.6 KPH; its 2500 capture has
passed them and is stationary after key release. It completes in about 72.765
seconds with the expected budget stop. No binding, save-state or runtime
movement patch was made. This establishes the loaded pilot's working movement
route rather than assuming the documented default arrows apply.

`c2-close-ruins-review-r1.txt` prepares a shorter W hold ending at frame 1700
and the original camera toggle afterward, to stop near the ruins for surface
review. It has not been run. The two completed movement runs are route evidence,
not matched normal-map visual comparisons or fine seam/contour acceptance.
All original inputs, outputs and failed route evidence are retained. Installed
assets and acceptance remain unchanged; the full normal-authoring goal is open.

## Matched stopped C2 ruins comparison

`c2-close-ruins-review-r1` completes the shorter W route, stops near the ruined
buildings and reaches the expected 2,600-frame Vulkan budget in about 71.782
seconds. The 2100 capture provides a closer wall view than the initial overview.
The subsequent X camera event does not establish a new camera mode; the capture
still shows the mech from behind. No camera-mode success is claimed.

`run_operation2_materials_r7.py` makes the C2 baseline option select the prior
C2 world-normal manifest while retaining the exact same 117-binding paired
resident catalog. It corrects the older runner option ordering, which otherwise
overwrote baseline selection with the C2 candidate path. The baseline run
`c2-close-ruins-baseline-r1` uses the same input script bytes, lighting, profile,
unmodified pilot and host; only world normals and isolated run/log paths differ.
It completes the same 2,600 presents in about 68.844 seconds. Draw counts and
hashes match at every frame (2,600/2,600); submission totals agree.

`paired-world-normal-review.json` records 38,822 changed pixels at frame 1600,
2,512 at 2100 and 2,605 at 2500, maximum channel deltas 29/16/16 respectively.
The 2100 source/baseline wall crops were inspected. Their 750x570 crop has only
463 changed pixels; the central wall region also has 463. The visible wall
therefore supplies little evidence of improved fine surface detail, despite the
world catalog's measurable shading contribution. This comparison must not be
promoted to all-149-map or ruin-facade art approval. Precise material-to-face
identification, remaining ruin authoring, and close roof/fan/façade seam review
are still needed. No installed resources or acceptance changed; full goal open.

## Eleven current ruin variants: preliminary authored pass

`operation2-ruin-sources-r1/` validates/extracts eleven actual current keys for
`ruin01/ruin1/ruin2/ruin3`, including 2048x1024, 1024x512 and square 512x512
facade variants. Both primary and all-variant boards were inspected. These are
source-aligned atlases, not evidence that each belongs to a particular visible
wall face in the completed run.

`operation2-ruins-authored-r1/` was rejected on preview: broad damage became flat
polygon cutouts and the bare-concrete map introduced unsupported recesses.
The preserved r2 revision removes those concrete islands, uses shallow seeded
concrete grain, irregular chipped boundaries and varied depth inside traced
broad fracture regions, plus explicit floor seams/window-frame recesses and
flat window interiors. Rust, stains and baked shadow brightness do not drive
height. Source/light/height previews for all four r2 families were inspected.

This is an initial structural candidate, not full-detail approval. Broad fracture
shapes and window placement still need finer measurement; procedural chips and
grain do not prove alignment of actual source fissures/aggregate. In particular,
window grids must be checked against each damaged opening before promotion.
No native close-up improvement is claimed from these offline previews.

All eleven r2 source identities/dimensions, unit-vector limits and exact PNG
readback checks pass. Maximum clipped-slope fraction is about 0.000010014.
The standalone candidate page is 13,813,694 bytes (39,845,888 decoded bytes),
with exact Python roundtrip and native parser/content-hash checks for eleven
bindings/images. Its receipt confirms eleven matches in older C2 metadata;
these must replace existing keys, not be appended blindly. It is not integrated
into the current 149-map streamed candidate or the resident catalog. Installed
assets and acceptance remain unchanged. Whole-world and mech completion is open.

## Measured ruin windows, integration and matched live wall effect

`operation2-ruins-authored-r3` replaces the r2 facade window grids with manually
measured intact-opening boxes from the three 2048x1024 sources. Broken frames
are omitted pending their own contours; no grid creates invented complete
windows through damaged areas. The source images and revised ruin2 preview were
inspected. Exact-size/vector/PNG checks pass for all eleven maps. The candidate
page is 13,760,240 bytes and passes exact Python roundtrip/native decoding.

`operation2-current-fullsize-incremental-r6` replaces all eleven existing ruin
keys, retaining all 1,360 unique keys and the same paired resident catalog.
It now contains 160 authored current-source keys, 27 pages, 254,199,404 bytes.
Filtered-page retained bindings are exact and native-readable; no explicit flat
exclusion is replaced. Two aggregate native cache traversals pass with 1,066
stable slots, 42 evictions and 536,649,728 peak retained CPU bytes, under the
unchanged 536,870,912 cap. Unreferenced prior images remain within page limits.

The private r8 runner uses this catalog. `c2-close-ruins-authored-r3` reaches
C2M1 from the successful mission-reader open and the expected 2,600 Vulkan
present budget stop in about 72.297 seconds. It reproduces the prior stopped
route with identical draw counts/hashes at all 2,600 frames and the same
submission totals. Compared with the preserved 149-map candidate, frames
1600/2100/2500 change 21,231/158,559/148,093 pixels; the central wall region
changes 10,683/51,638/50,653 pixels. The matched 2100 wall crop was inspected.
This establishes visible use of the new ruin maps, unlike the prior largely
unchanged wall result; it is not fine-art acceptance. Spall/rebar/aggregate
alignment, broken frames, seams and tile borders remain incomplete. Nothing is
installed or committed; acceptance stays 131/144 and the full world/mech goal
remains active.

## Ruin exposed-metal refinement; rejected fine crack proposal

The r4 offline proposal added fine crack paths and exposed-metal lines. Direct
source overlays for all three facade families showed that the proposed crack
zigzags did not follow the source closely enough; those paths are rejected and
are absent from `operation2-ruins-authored-r5`. r4 outputs/overlays are preserved
as failed alignment evidence, not promoted artwork.

The r5 revision retains only the measured exposed-metal additions over r3:
frame/rod segments in visible openings, including the top-center reinforcement
on ruin3. The source/tangent-light metal-detail crop was inspected against the
actual bars. `refinement-delta.json` confirms nine facade variants change,
while both bare-concrete ruin01 variants remain exactly unchanged. No
unsupported proposed crack path survives. These additions do not complete the
missing fine concrete fracture/aggregate detail.

All eleven emitted r5 maps retain exact source dimensions and pass unit-vector,
clipped-slope and PNG readback checks. The 13,774,217-byte candidate page passes
exact Python roundtrip and native decoding/content-hash checks for eleven
bindings/images. It remains separate from the live-tested 160-map r6 streamed
catalog; that catalog still contains r3 ruin maps. Native viewing of r5, more
precise broken edges/window shards, seam validation and whole-world/mech scope
remain open. No installed resource, acceptance criterion or accepted count
changed, and no game run was repeated for this offline refinement.

## Current mech/skin source revalidation and missing Sommerset coverage

A fresh read of the selected prepared model-pack registries and actual batch
headers reproduces the earlier counts in `current-prepared-mech-dimensions-r2`:
2,176 exact-size, 512 undersized, 624 oversized and 400 explicit-flat bindings.
These are repeated skin/LOD binding counts, not unique maps. This confirms the
selected installed pack has not adopted the private Avatar/Owens/Firefly/Strider/
Orion candidates. No installed registry or payload was modified.

The earlier audit explicitly excluded separate prepared-skins-v1 packs, leaving
a concrete coverage gap. `audit_separate_skin_normals.py` now reads their actual
color batch tables and inherited chassis normal sidecars. The current Sommerset
skin has Body/Variant/Weapons colors at 2048x2048 but inherited Bushwacker normals
at 4096x4096, at both close and distance LODs. Window remains an explicit-flat
64x64 glass binding; MissileHead is exactly 64x64. The separate receipt records
six oversized, two exact and two explicit-flat bindings, with registry pins.
These counts must stay separate from the earlier model-pack totals.

Read-only Blender inspection of the preserved Bushwacker normal-12x source
project shows Body/Variant/Weapons use imported donor tangent normal textures,
not a procedural height network that can simply be evaluated at a new size.
`bushwacker-normal-source-nodes-r1.json` records actual material image/link
provenance. The Sommerset native albedo bake remaps its source materials into
native atlases; a dedicated normal authoring/bake must preserve that UV/material
mapping and the existing approved material response, including its flat glass
exception. A file resize alone would not complete per-skin detail/alignment.
No replacement normal or full-skin quality approval is claimed by this inventory.
The advance is closure of a specifically excluded skin dimension/provenance
criterion, identifying three actual material targets at two LODs. All media and
inspection output remain local; acceptance and installed resources are unchanged.

## Dedicated Sommerset 2048-square normal candidates

`sommerset-native-normals-r1/` pins and exports exact inherited native Body/
Variant/Weapons normal pixels (including their stored-row flip), validated by
native pixel hashes. Blender 5.2.2 evaluates those authored chassis details on
Sommerset's native atlas geometry/UVs and preserved custom loop normals, adding
shallow UV metal grain independently of the color/paint textures. It bakes three
2048x2048 maps through the material network; this is a native-UV bake with
additional grain, not new hand-authored replacement of every donor feature.
Source normal strength is 1 and runtime material tuning remains unchanged.

Normal/tangent-light atlas previews were inspected. Filtering/dilation left some
raw baked vectors short (raw unit-error maxima about .423/.279/.345). Raw bakes
are preserved. `normalized/` renormalizes their directions before quantization;
all three then pass exact dimension, unit-vector and PNG readback checks. A small
number of Body texels have negative tangent Z, retained without arbitrary clamp;
steep detail and seam margins need inspection in live shading before approval.
The bake/normalization receipts record these limits rather than hiding them.

Private close/distance BWNRM2 sidecars replace only Body/Variant/Weapons with
the 2048-square candidates. `check_sommerset_normals.exe` uses the maintained
native parser and the actual separate-skin albedo material order. Both checks
pass: 34 batches, four nonnull normal images, exactly three replacements, all
other decoded pixels/bindings exact. The Window flat exclusion and 64x64
MissileHead remain unchanged. These files do not modify the shared Bushwacker
sidecars or the installed skin pack.

This advances three identified skin-size mismatches through native-UV normal
baking, normalized full-size images and native-readable private sidecars. Proper
skin-specific normal routing, native material/LOD/damage/seam views and fine-art
approval remain open; a sidecar parser pass is not those results. No runtime,
installed pack, acceptance or release changed. The broader all-world/all-mech
normal authoring goal remains unfinished.

## Sommerset private native material comparison

The isolated additional-skin attempt `sommerset-normal-gameplay-r1` reaches C2M1
and the expected 2,600-present stop, but logs only base skin slot 0 and does not
announce an additional skin. The capture retains the default appearance.
Although the binary contains additional-skin capability strings and the private
catalog's mesh identities match both active LODs, those are not proof of executed
selection. This attempt does not validate Sommerset selector routing; its files
are preserved without promoting that claim.

`run_sommerset_normals_r2.py` uses an explicit private base-slot color override
pointing to the actual validated Sommerset BWTEX payload at both LODs, paired
with the dedicated candidate normal sidecars. It disables the unproven
additional-skin path for this fixture. `sommerset-normal-base-slot-r2` displays
the colored Sommerset atlas, reaches C2M1 and 2,600 Vulkan presents in about
71.610 seconds. `sommerset-normal-base-slot-original-r2` keeps the same colors,
world, input and lighting but restores inherited chassis normals; it completes
the same budget in about 72.687 seconds. No installed or shared pack was edited.

The paired-normal review records identical draw counts/hashes at every frame
(2,600/2,600) and matching submission totals. Frames 1600/2100/2500 change
22,745/29,904/27,636 pixels, confined to the mech bounds. Actual replacement
logs contain one non-preview Bushwacker world root and 287 Bushwacker replacement
events. The matched 2100 rear/arm crops were inspected. These prove visible use
of the dedicated normals with Sommerset's atlas in this explicit fixture, not
production skin-specific routing, every material face, distant LOD, damage or
seam approval. Broad detail remains inherited authored chassis detail plus
shallow grain; a full new per-skin art pass is not claimed. Front/side views and
steep/margin texels still need review. Acceptance remains 131/144; full goal open.

## Bushwacker bundled-skin exact-size normal combinations

The current eight unique Body atlases were decoded from their actual RGB565
payloads and inspected in `bushwacker-current-skin-layout-r1/body-skins.png`.
Broad hardware layout is shared, while palette, camouflage and markings vary.
Seven Body atlases are 2048-square; skin D is 1254-square. Every bundled Variant
and Weapons atlas is 1254-square. This corrects any assumption that all alternate
Body textures use the smaller dimension. Layout inspection does not approve all
paint edges or per-skin hardware alignment.

`bushwacker-native-normals-1254-r1` reevaluates the same pinned native-UV material
bake used for the Sommerset candidates at 1254x1254 for Body/Variant/Weapons,
retaining inherited authored detail and shallow paint-independent grain. Raw
bakes are preserved and filtered vectors renormalized with PNG/unit checks.
No 2048/4096 normal image is resized into these new maps. The normal/light atlas
preview was inspected. The mixed-size combination reuses the existing evaluated
2048 Body candidate, with the new 1254 Variant/Weapons images.

Two private BWNRM2 packs are staged: all-1254 (18,886,920 bytes) for skin D and
mixed-2048-1254 (29,374,072 bytes) for the other seven skin layouts. Native parser
checks pass against actual material orders: 34 batches/four nonnull images,
three exact-size replacements, unchanged other pixels/bindings. Both glass flat
exclusions and MissileHead are retained. A metadata join confirms exact sizes
for all 16 current Bushwacker bundled texture bindings (eight skins/two LODs).
This is coverage of dimension combinations, not eight unique new art passes or
all-LOD live proof. Sommerset keeps its separate all-2048 candidate.

These files are not installed. The current runtime's shared per-chassis normal
selection does not yet route these distinct size combinations per skin, so they
must not be globally activated as if that issue were solved. Per-skin selection,
front/side/damage/seam views and remaining chassis authoring remain open. This
advances three additional evaluated target-resolution maps through native-ready
packs; acceptance stays 131/144 and the full goal remains active.
