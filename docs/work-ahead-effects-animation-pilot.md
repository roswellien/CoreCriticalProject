# Six-frame AI dust animation pilot

Recorded 2026-10-07. Following the eight-material normal-map batch, the user
authorized the next step: an effects animation pilot. The first sequence is
`kickdust`, a six-frame dust effect selected from the admitted MW3 installation.
It uses the approved full-AI dust look and generated transparency.

## Source and sequence evidence

The original textures are entries 364–369, `kickdust01` through `kickdust06`, in
`MW3/zbd/c1/rtexture.zbd`, SHA-256
`56afd5738562ffd51596ce4b3557b734cacedfd187b09307e9b94281dd39269f`.
All six are 32 x 32 RGB565 images with a separate byte alpha plane, supported
by the strict local decoder. Each decoded PNG and entry span has an identity
record; the original container is not included in the working package.

Sequence order has stronger evidence than filename adjacency. A bounded parser
of `MW3/zbd/interp.zbd`, SHA-256
`f4ae013c419984cd1139dcbe06695efddd1875e88baa55bf0997adf36907b171`,
finds the `kickdust` node in script 14, `Support\effects.gw`. It configures six
maps in order 01–06, looping `on`, and speed token `15`. The source record offsets
and payload hashes are kept in the local `sequence-evidence.json`.
Other nodes use different ordering of these same images, so this package binds
to the selected `kickdust` configuration.

The parser checks container and line/token bounds; it does not execute the
interpreter. Speed units, actual activation, particle tint/scale/fade, blending,
depth behavior and renderer sampling remain unverified. The gallery's default
15 fps is an adjustable review assumption, not a recovered native frame rate.

## Artwork and exports

One built-in image-generation edit creates all six frames together on a
transparent 2-column by 3-row atlas, using original silhouettes and alpha guides
plus the approved dust artwork as a style reference. The generated atlas is
1024 x 1536; each native cell is already 512 x 512. FFmpeg extracts each cell,
then the export is a byte-identical copy. No additional resize, original color
restoration, original mask restoration or interpolated frames are applied.
The atlas, prompt, input references, actual commands and hashes are retained.

Generated dust is more opaque than the originals: the source alpha peaks reach
118 of 255, while the AI atlas reaches 254. Source alpha remains a separate
reference. These differences need visual and combat-visibility review; they are
not a compatibility pass. The preview's AI-opacity control only changes display.
Faint tails touch some cell boundaries and near-transparent alpha=1 pixels occur
throughout the cells; packing, clipping and overdraw need subsequent review.

The ignored `local/work-ahead/effects-animation-pilot-v1/` contains six exports,
native cells, original references, editable frame layers, source mappings,
sequence evidence, independent checks and a self-contained offline gallery.
The ZIP and SHA-256 sidecar sit alongside that directory. Earlier sealed texture
and material packages remain unchanged. INTRO remains first in the planned full
video queue, with processing held.

## Review and readiness

The gallery compares synchronized original and AI frames with play/pause,
stepping, speed, loop/single-pass and last-to-first inspection. Background,
alpha/RGB inspection, opacity, zoom and source-over/additive preview controls
help expose edge and visibility changes. Canvas blending is an approximation;
it does not establish the game's renderer behavior.

Independent checks re-decode source spans, compare native cells with the raw
generated atlas, bind final exports and sequence evidence, and describe alpha
and adjacent-frame differences. Static gallery and package checks establish
resource identities and structure, not rendered browser or native-game behavior.

Status: **six prepared AI effect frames; motion and visibility review pending**.
Following the user's opacity feedback, a [softer transparency revision](work-ahead-effects-transparency-revision.md)
lowers actual alpha while retaining this first pilot as a comparison.
Mapped effect playback, native speed semantics, correct blending and replacement
routing remain gates before integration. This is a local experiment under the
[content policy](legal.md), with no distribution approval established.
