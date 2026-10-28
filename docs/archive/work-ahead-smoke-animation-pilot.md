# Two-frame white-smoke pilot

Recorded 2026-10-07. After the user flagged the first four-frame smoke concept
as too opaque, source review found a stronger effect candidate: the original
`wtsmoke1` and `wtsmoke2` texture pair, associated with compiled smoke-puffer
records and a `jump_smoke.flt` load command. The two-frame AI review pilot is
under `local/work-ahead/smoke-animation-pilot-v1/`.

## Source evidence

C1 `rtexture.zbd` entries 440 and 441 are 32 × 32 RGB565 plus byte alpha.
Their source means are 27.99 and 22.78 / 255, with peaks 111 and 97. The
container SHA-256 is
`56afd5738562ffd51596ce4b3557b734cacedfd187b09307e9b94281dd39269f`.

The bounded interpreter parser records `LoadGameGen smoke_wht.flt jump_smoke.flt`
in `Support\weapons.gw` at byte offset 55040. C1 `anim.zbd` contains nearby
compiled name references to `jumppuffer1`, `jumppuffer2`, `wtsmoke1`,
`wtsmoke2`, and `jump_smoke.flt`. This evidence supports the source association
for a native smoke effect. The compiled animation structure was not parsed, so
the exact texture-cycle order, timing, looping and runtime activation are not
verified. The local `native-sequence-evidence.json` records source hashes,
offsets and these limits.

## Artwork and review

The two source sprites and exact alpha masks guide one AI-generated transparent
atlas. The first generation attempt baked a checker pattern and is retained only
as a rejected draft. The selected atlas was generated with transparency
enabled; an alpha-only multiplier of 0.38 was then applied to each cell. This
keeps RGB and spatial alpha pattern while reducing mean alpha below the source
means. The selected average alpha is 21.13 and 18.05 / 255, with peaks of 96.
The AI footprint remains broader than the original masks, and renderer
compatibility has not been tested.

One whole-atlas bicubic resize prepares a 1024 × 512 atlas, followed by exact
512 × 512 crops. Each frame has an editable OpenRaster document with hidden
original, alpha-guide and approved-style layers. The offline [review page](../../local/work-ahead/smoke-animation-pilot-v1/review.html)
compares each AI frame against its source and allows stepping, playback,
background selection and alpha inspection. Six FPS is a review assumption.

Status: **two source-associated AI smoke frames ready for visual review**.
Native order, speed units, blending, emitter behavior and in-game visibility
remain open. This does not approve a replacement pack.
