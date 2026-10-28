# Reviewed texture light placements - 2026-10-20

The user's final complete 40-page review supersedes the two interrupted partial
lists. [The saved review](texture-light-review-2026-10-20.json) maps the exact
PDF page order to stable T/M IDs. All **239** entries have decisions: **71
approved** and **168 no-light exclusions**. No other texture IDs are implicitly
approved. The selected-light budget remains **16**.

The user subsequently authorized judgment for the page-6 ID discrepancy and
requested pictures on Google Drive for remote verification. Page 6 contains
T0310/LFLARE1, while the supplied T1641 identifies a Black Hawk texture outside
that page. The draft uses a centered T0310 beacon. A separate reference image
shows both identities, and the assumption is flagged explicitly.

## Authoring result

`tools/remaster-launcher/prepare_reviewed_fixture_placements.py` reads the pinned
upgraded pixels referenced by the audit and stages proposed emission masks,
normalized UV centers, colors, roles and page diagrams. Selected source pixels
must match the audit hash. Outputs stay local under the existing Games-drive
reports junction:

`reports/reviewed-light-placements-20261020/draft-r3`

The directory contains `placements.json`, `decisions.csv`, 71 masks and 21 page
preview boards, plus the page-6 comparison. The complete ZIP is in its parent
directory. `checks.json` records narrow validation. Earlier draft directories
are retained as superseded diagnostics.

| Intended rendering role | Approved variants |
| --- | ---: |
| World UV lights | 42 |
| Screen/cockpit glow | 24 |
| Replacement model UV lights | 1 |
| Atmospheric glow | 2 |
| Moving effect lighting | 2 |

The red rectangles on the Training bay atlases each receive their own proposed
center. M0069 has two red Avatar panel centers; unrelated borders and panels are
excluded. T0311/T0313 and the LFLARE2 variant use colored outer ring regions with
empty centers. Warm panel lights use the bulb or lit band rather than bolts or
every checker-plate tread. HUD/Mech Lab graphics and auroras are marked as glow
without finite world point lights. Rocket regions follow graded plume pixels,
excluding the pure-red sprite backing.

The proposed masks retain source coverage. Faint flare rings have alpha below
32 and must not be discarded by an arbitrary coverage threshold. Replacement
model PNG alpha is ignored, matching the existing RGB565 model upload path;
those alpha channels are not reliable visibility masks.

There are 644 authoring centers across the drafts. This is not a simultaneous
light count or a proposed budget increase. Radius/intensity values remain
calibration proposals. Fourteen records contain explicit authoring assumptions
for ring palettes, broad lit bands or the proposed purple aurora tint; none of
the 71 approvals lacks placement data.

## Verification and current execution boundary

All 239 IDs are unique and belong to their saved PDF pages. Every approval has a
mask and placement data; exclusions have neither. Masks match their recorded
hashes and never exceed source coverage. Ring centers stay non-emissive, M0069
has exactly two panel centers, and altered reviewed source identities are
rejected. Representative page layouts and placements were visually inspected.

These are **technical placement drafts, not in-game captures**. No runtime code,
executable, original artwork or launcher profile was changed or published in
this authoring step. The next runtime change must consume the reviewed regions
and apply UV-aware emission/geometry attachment; the current game does not read
the new JSON or masks. Acceptance remains **131/144**. The requested remote
verification concerns proposed positions and colors, not repeating all existing
approval/no-light decisions.

The [Drive preview folder](https://drive.google.com/drive/folders/1DqYkLytJ_YzrEy6z_rNuhkK-evioUkvQ)
contains the labeled page images and complete authoring package.

## Required runtime handling

Use the latest published launcher host as the integration base. At authoring
time it selects `local/operation2-load-crash-r1/candidate-host`, executable
`dc01af620445772d06532593c402d2686fa810a339476926a7ccd9da02b8f2e1`.
Retain its later crash fixes and recheck for concurrent publications; do not
rebase this work on an older R7/F12 host solely because the original audit used it.

- The review's no-light decisions must override previous automatic fixture
  registration for the reviewed identities; original artwork/effect sprites
  remain in control. An absent new mask must not silently re-enable an old
  incorrectly inferred fixture.
- World source positions must follow visible UV regions on actual submitted
  geometry, including repeated/cropped UVs and moving sources. Atlas-wide
  polygon centroids are insufficient for multiple LEDs and colored rings.
- Model M0069 needs material/batch-aware UV placement with the model texture
  row convention (`1-v` relative to the source PNG). Screen/cockpit and sky
  effects require their respective passes; they are not world point emitters.
- T5063 (page 39, no light) and T5065 (page 40, white) share two converted runtime
  keys despite distinct source banks: `zbd/c2/texture1.zbd` versus
  `zbd/c2/rtexture2.zbd`. The colliding keys are 128x256/ARGB1555,
  `be534459dc529325`, and 128x256/ARGB4444, `1fbc338e39417325`. Preserve the
  decisions separately and require source context; a content-hash-only catalog
  cannot honor both. Do not silently choose one decision for both variants.
- Keep the shared 16-light scene budget and weapon reservation unchanged.
  Validate emission-only behavior and actual UV/world placement before main
  launcher promotion; report visual assumptions honestly.
