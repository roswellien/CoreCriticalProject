# First MW3 texture decoding pilot

Recorded 2026-10-07. The strict project-authored decoder has accepted all 6,040
entries in the three initial image packages. It checked descriptors and exact
payload spans for all entries; it exported six selected research previews,
not the whole collection. No upscale, remake or normal-map generation is
claimed by this decoding result.
The later [enhancement experiment](work-ahead-enhancement-experiment.md) records
4x candidates, faithful resize baselines and a failed generative alpha gate.
The subsequent [12-texture batch](work-ahead-texture-batch.md) packages guarded
4x exports, editable sources and independent preservation checks. Mapped review
remains open.

## Evidence and supported subset

The local structural findings are corroborated by the authored
[Mech3ax descriptor definitions](https://github.com/TerranMechworks/mech3ax/blob/cbb838fd8b628417abe61dee6132c350a2375f33/crates/image/src/lib.rs)
and [image reader](https://github.com/TerranMechworks/mech3ax/blob/cbb838fd8b628417abe61dee6132c350a2375f33/crates/image/src/read.rs).
These sources identify the descriptor values as flags: 5 is opaque RGB565,
3 keys raw black to transparent, and 11 adds a byte-per-pixel alpha plane after
the color plane. The decoder implements only these flags with zero palettes,
zero stretch and the observed package header. Unsupported forms fail visibly.

The [pixel converter and channel scaling](https://github.com/TerranMechworks/mech3ax/blob/cbb838fd8b628417abe61dee6132c350a2375f33/crates/pixel-ops/src/lib.rs)
corroborate little-endian RGB565 and sequential pixel order. Channel values are
scaled to eight bits using integer nearest rounding; no gamma assumption is
encoded in the PNG. The [format research](https://github.com/TerranMechworks/mech3doc/blob/2ad5a1de82553bec4d8d0188d9ff95e6619aac81/src/texture-packages.md)
leaves gamma behavior unresolved. Extractor agreement does not establish the
original renderer's sampling, orientation, blending or color treatment.

| Package | Opaque | Black-key | Full alpha | Rejected |
| --- | --- | --- | --- | --- |
| `rmechtex` | 3,350 | 0 | 10 | 0 |
| `rmechtex16` | 2,285 | 0 | 1 | 0 |
| `rimage` | 90 | 198 | 106 | 0 |

The 117 entries previously unresolved by a two-byte-span hypothesis match
color-plus-alpha spans under this supported subset. No palette or stretch
entries were observed in these packages; support for those features is deferred.

## Local review batch

Current batch: ignored `local/work-ahead/pilot-v2/`. Each package's manifest
records source hash, decoder/parser hashes, entry offset, span, dimensions,
alpha statistics and output hashes. Earlier v1 evidence remains preserved.
`review.html` lets the reviewer vary background and display scale to inspect
transparent pixels without altering the image files.

| Package / entry | Stored dimensions | Review purpose |
| --- | --- | --- |
| `rmechtex / 0` | 128 × 64 | Metal detail and colored marking preservation |
| `rmechtex16 / 0` | 64 × 64 | Lower-resolution artwork; its relationship to the first sample is unverified |
| `rmechtex / 1513` | 32 × 32 | Full-alpha damage mark and soft edges |
| `rimage / 21` | 51 × 58 | Black-key UI line art |
| `rimage / 86` | 82 × 82 | Full-alpha button and graduated edges |
| `rimage / 53` | 600 × 95 | Dark UI text; review against a light background |

Visual inspection confirms recognizable mech texture and UI icon/button
artwork. Orientation against original-game display remains unverified; dark
or low-opacity artwork must be inspected on a suitable background. Filenames
and appearance are selection aids, not verified gameplay/rendering mappings.

## Preparation and next gate

Use a faithful restoration direction for the first pilot: retain palette,
markings, cables, panel boundaries and silhouette cues. Texture artwork may
gain legibility, but text and line-art UI should receive a separate treatment
from noisy metal surfaces. Preserve each image's alpha mode in any future
export recipe. Do not infer geometric depth from painted shadows or labels
when preparing normal maps.

Next verify at least one opaque texture, keyed UI icon and full-alpha image
against the original renderer or a captured reference. Establish UV usage and
tiling before selecting a tiling pilot. Then choose a bounded enhancement
recipe and record settings, editable sources and artifact review. Generated
replacement packs remain subject to the content/provenance release gate.

Validation: thirteen authored-fixture checks pass, including color endpoints,
rounding, row order, keyed/plane alpha, unsupported headers/palettes/stretch,
bad lengths/offsets and PNG CRC/scanline structure. The registered `asset_tools`
CTest passes. Original proprietary images are absent from test fixtures and
repository content; the local preview paths are verified ignored by Git.
