# Complete fire animation pilot

Recorded 2026-10-07. Following acceptance of the
[softer dust revision](work-ahead-effects-transparency-revision.md), the user
authorized the complete sixteen-frame `fire_f` pilot. The local review and
package are under `local/work-ahead/fire-animation-pilot-v1/`; repository
documentation contains metadata only.

## Source sequence

The C1 texture container `MW3/zbd/c1/rtexture.zbd` has SHA-256
`56afd5738562ffd51596ce4b3557b734cacedfd187b09307e9b94281dd39269f`.
Entries 342–357 are `fire_f01`–`fire_f16`, each 32 x 32, flags 11,
RGB565 with a byte alpha plane. Source identity, entry spans, decoded originals
and all sixteen frame mappings are recorded locally.

Bounded inspection of `MW3/zbd/interp.zbd` (SHA-256
`f4ae013c419984cd1139dcbe06695efddd1875e88baa55bf0997adf36907b171`)
finds node `fire_f` in `Support\effects.gw`, configured with sixteen ordered map
names, raw speed token 16, and looping off. The gallery uses one-shot playback
and replay, with 16 FPS explicitly a review assumption. The script was inspected
as data; no interpreter or native effect was executed.

## Artwork and sizing

The approved full-AI fire texture serves as a style reference. All sixteen
sprites were generated together, followed by one AI edit to soften the middle
and fading tail. Selected exports keep generated RGB and alpha, with the
original RGBA available separately. Early yellow cores cool through orange to
dark translucent embers. The source's mid-sequence fluctuations are retained
as reference behavior rather than imposing a monotonic fade requirement.

The actual image-tool output is 1254 x 1254, despite the requested 2048 x 2048.
One whole-atlas bicubic resize creates a 2048 x 2048 working grid; exact crops
then produce sixteen 512 x 512 PNGs. Finals are byte-identical copies of those
working crops. This is one conventional size conversion, not intrinsic
512-pixel AI detail or a second AI upscale.

The revised art has a visibly weaker tail, but remains more opaque and brighter
than the original in places. Numeric alpha targets in the generation prompt
were not achieved exactly. Faint margin speckles, especially near the frame
05/06 boundary, require sampling review. Exact original silhouettes, native
visibility, and motion coherence are not claimed from pixel checks alone.

## Review and hand-off

The offline gallery compares synchronized original and AI frames and includes
one-shot playback, replay, frame stepping, a thumbnail timeline, alpha inspection,
backgrounds, and illustrative blending choices. Those blending and luminance
views are preview assumptions. Native timing, gamma, tint, fades, activation,
blending, depth, sampling and replacement routing remain unknown.

The local hand-off contains source mapping and hashes, original references,
raw and prepared atlases, both generation prompts, editable OpenRaster layers,
export commands, independent checks, and checksummed packaging. Independent
checks cover original RGB565/alpha decoding, all sixteen crop and final
identities, editable-layer contents, gallery assets, and archive members.
The declared bicubic pass is identity/command checked; its pixels are not
independently recomputed by another resampler. Static gallery validation does
not establish rendered browser or native-engine behavior.

Status: **sixteen-frame prototype prepared for visual review; native motion
and rendering validation pending**. Earlier sealed texture, material and dust
packages are unchanged. The user subsequently authorized the
[four-frame machine-gun impact pilot](work-ahead-weapon-impact-pilot.md);
smoke is the next recommended sequence. INTRO remains the first planned full
video upscale, with processing held.
