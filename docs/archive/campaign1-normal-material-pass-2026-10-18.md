# Campaign 1 material-normal refinement pass

Date: 2026-10-18. Continues the user-authorized normal-map work after the
[storage relocation](storage-relocation-2026-10-18.md). Acceptance stays **131/144**.

## Scope and result

Campaign 1's shared scene/archive references and current upgraded banks were
enumerated across `c1m1`–`c1m4`. The [material ledger](campaign1-normal-materials-2026-10-18.csv)
records 355 world material families. The selected larger terrain, structure and
vehicle-component scope contains 287 families: 265 receive this refinement and
22 retain earlier work. All 1,367 source identities in this scene inventory were
already registered by the automatic preview; this pass improves their treatment
rather than claiming previously absent game-wide coverage.

Among the 265 refined families, 108 have explicit UV-authored structural features;
157 have restrained material-specific grain or a flat-decal treatment. Features
include traced cliff crevices, masonry courses, door/window recesses, bridge and
industrial panel seams, tracks and vehicle covers. Glass and transparent holes
stay flat; paint/emissive color is excluded from shallow grain where appropriate.
Color-derived grain remains an estimate, not recovered physical height. This is
a completed first refinement pass for the selected scope, not final art approval
or a claim that every material has individually sculpted height.

The other 68 scene families retain their existing treatment: small characters,
props, footprints/effects, foliage and the separate water/shore path. Water/cloud
settings and existing work are preserved. Thin bridge pieces and vehicle gun
components missed by the initial size heuristic were explicitly added after
source review. Sizes are local geometry measures, not screen-visibility proof.

The world catalog preserves all 4,001 keys, refines 907 bindings and retains the
other 3,094 normal-image tuples byte-for-byte, including earlier selected work.
It occupies **493.63 MiB in 56 pages** under the unchanged 512 MiB package and
resident limits. A lossless global repack first reclaimed 17.8 MiB by grouping
identical complete image tuples; it reduced no image resolution. Selected
previously small masonry/ground maps receive more resolution within that space.

## Original and replacement mechs

Original Avatar/Owens/Firefly variants receive 91 additional exact-content
bindings. Seventy-seven bank/material rows reuse existing authored maps after
coarse screening and visual layout review; 26 rows use separately authored
layouts, producing 24 distinct images across their bank variants. UV layouts
are not admitted by filename alone. Combat/damage/LOD appearance still needs
individual review. The existing 15 replacement-model registrations and their
normal maps remain selected, including detailed original-MW3 Strider geometry.

The two observed shared mech families outside the static scenery list are also
reconciled: the upgraded `mcat20` atlas receives explicit panel/glass treatment,
and the upgraded `footpad` receives raised rails. The tiny 32×16 stock pad has an
explicit flat binding. Two earlier generic Mad Cat draft bindings are replaced;
the other 145 bindings from the preceding 147-key catalog remain byte-identical.
The resulting dedicated catalog has **149 keys and 81 images in two pages**
(178.56 MiB), including 93 added identities
relative to the earlier 56-key catalog. Previous stock maps and corrected ground
selection are preserved except for those explicitly selected Mad Cat drafts.

Authored surface catalogs can now span bounded `MW34SNA1` pages while retaining
single-file `BWSNR2` compatibility. Each page still supports at most 64 images;
the authored aggregate stays within 256 MiB. Duplicate identities, invalid/missing
pages and excessive packages fail visibly. This removes a capacity obstruction
without changing shaders, world limits, normal strengths or original gameplay.
Launcher capability/snapshot checks reject these manifests on unsupported hosts.

## Native validation and screenshots

Three bounded original-UI/save comparisons each preserve all 2,600 original draw
triples. They include a fresh C1M1 route and the preserved verified C1M3 save route.
The first attempt at the latter selected the earlier save row; its folder label
is retained with a correction in its metadata, and it is not counted as another
C1M3 verification. All test stops are the expected presentation budget.
The final shared-material catalog also passes a fresh 2,600-frame comparison
against the original C1M1 control. It loads all 149 dedicated keys, and its three
captures are byte-identical to the earlier published candidate screenshots.

The initial fresh route observes 62 refined world keys and 15 newly registered
original-mech variant keys; the preserved C1M3 route observes 126 refined world
keys. These are registration/submission observations, not proof that every key
was visible. C1M4 has static source/catalog coverage, not a live playthrough.
Close-range facade/vehicle review, extended combat and full mission runs remain.

The C1M1 cliff comparison changes 2,103,401 pixels, with mean absolute channel
difference 1.66/255 at frame 1900. The village view mainly uses earlier preserved
materials and changes very little; it is not presented as a new improvement.
The distant C1M3 views also provide limited art evidence. Full-resolution native
cliff screenshots are in the existing private Drive folder:

- [42 — before](https://drive.google.com/file/d/1fhzf9XC_CCSyyh0u0kmcFI17GiXtWhL3/view?usp=drivesdk)
- [43 — after](https://drive.google.com/file/d/19ng5Dsz3xvcmatgItMb6EWd5D8_Kycvh/view?usp=drivesdk)

Names, sizes and folder membership were read back after uploading. Sharing is
unchanged; raw color, height and normal-map sources are not uploaded.

Eighteen Python checks pass for alpha-source conversion/identity, lossless page
grouping/bounds, grain masks, packing and launcher capabilities. The native C++
contract/cache fixture passes, including multi-page image offsets, duplicate-key
rejection and byte budgets. The selected existing sky/water host was cloned;
only authored-catalog loading and its shared header changed. Water/cloud extras,
menu rollover work, models and original services were retained.

Single warm-route timing samples show approximately 144→142 FPS for C1M1 and
88→86 FPS for C1M3. They are limited regression spot checks, not a controlled
performance benchmark. C1M1 world-normal residency rises from 127.35 to 139.59 MiB
despite the smaller total package, reflecting the new maps/page grouping. No
claim of zero performance impact is made; replay video remains off.

## Testing entry point and evidence

Use `Play MW3 - Material Normal Preview.cmd`. Its normal strength remains **1.5**;
upgraded albedo, all 39 banks, graphics, sun/sky/ambient settings and replay-off
default remain selected. This pass is selected in that preview only. The portable
execution boundary advanced is authored material-catalog loading and native GPU
material binding; it grants no game-function acceptance credit.

Host SHA-256:
`a836293e08397c3228efdd768ad08c0877a451d1e3f4f32db153ecb7964c924f`.

Private source pins, recipes, editable maps, candidate packages, source boards,
native logs and screenshots:
`C:/Users/jcbla/MW34SunTests/campaign1-complete-20261018/`.
The scene archive pin is
`6f6e5b9d80952f6546f0a0655b155b875a0e2c819dae1d64b87ac534a09a27ef`.
Original media and generated assets remain outside public source control.
The first-100 queue retains its ranks: 88 entries are included or reconciled by
this pass; the other 12 are deferred small characters/props or separate surf work.

The separate standard launcher check exposes an existing controls-build metadata
mismatch: its executable/profile select `42672b…`, while its source snapshot
still selects `292602…`. Those files predate this material work and were not
modified here. Material Normal Preview has its own matching snapshot and passes
its launch check. Standard-launcher metadata reconciliation remains separate;
verification was not bypassed.
