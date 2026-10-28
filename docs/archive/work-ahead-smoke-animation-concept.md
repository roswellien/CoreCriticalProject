# White-smoke motion concept

Recorded 2026-10-07. The prepared effect-sequence inventory initially identified
one standalone white-smoke texture: `wtsmoke1`, C1 entry 440, 32 × 32, in
`MW3/zbd/c1/rtexture.zbd` (SHA-256
`56afd5738562ffd51596ce4b3557b734cacedfd187b09307e9b94281dd39269f`). Its
stored mean alpha is 27.99 / 255. This inventory result does not prove that no
other smoke sequence exists elsewhere in the game. Subsequent source review
identified the paired `wtsmoke2` texture and a likely jump-smoke association;
see the [two-frame source-associated pilot](work-ahead-smoke-animation-pilot.md).

The local [lower-opacity revision gallery](../../local/work-ahead/smoke-animation-concept-v2/review.html)
shows four AI-authored states alongside the earlier opacity version, the
standalone sprite and the approved full-AI smoke look. It lowers alpha per
frame while preserving the generated RGB shapes. The atlas is converted once
as a whole and cropped into four 512 × 512 concept cells. Each editable
OpenRaster document contains the selected cell plus hidden original and
approved-style references. Raw prompts, iterations, hashes and export details
are in the local package.

This is an art-direction concept only, not a mapped game animation or
replacement pack. It does not establish frame order, timing, looping,
activation, tint or blending. The gallery's six-frame-per-second playback is
for review. Revised average alpha is 20.0, 27.5, 18.7 and 9.8 / 255, compared
with v1 at 44.7, 72.4, 60.6 and 37.8 / 255. This deterministic reduction is
an art-direction adjustment, not a recovered source alpha curve. Alpha and
browser compositing still need renderer review.

Next work should find a source-configured smoke sequence before preparing any
native replacement. If none can be identified, choose another evidenced effect
family rather than treating these four concepts as native frames.
