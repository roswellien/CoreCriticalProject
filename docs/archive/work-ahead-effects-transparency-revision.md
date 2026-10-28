# Dust transparency revision

Recorded 2026-10-07. The user found the first AI dust animation too opaque.
The [six-frame pilot](work-ahead-effects-animation-pilot.md) is preserved,
and `local/work-ahead/effects-animation-pilot-v2/` prepares softer AI sprites.

The change affects the alpha saved in all six PNGs, rather than relying on the
review gallery's display-opacity control. Average alpha falls by roughly 60%
relative to the first AI version. Revised means are about 44–54/255 and peaks
159–170; the previous version's means were 108–133 and peaks 253–254. Original
means are 23–31 and peaks 101–118. The revision is substantially more translucent
while still stronger than the original masks.

Built-in image-generation edits retain the broad cloud layout and fine wisps,
but also alter RGB detail toward a more fibrous or smokelike appearance. Exact
RGB identity and achievement of the prompts' numeric alpha targets are not
claimed. The previous AI artwork is available alongside the revised frames.

The selected atlas remains 1024 x 1536, with six 512 x 512 cells. Exact cell
extraction followed by file copying preserves the generated RGBA without
resizing or original-mask restoration. Configured frame order and source hashes
follow the first pilot; native timing, blending, fades and activation remain open.

The offline gallery defaults to the revised images at 100% display opacity,
with synchronized original comparison and a switch to the previous AI version.
Both alpha masks remain available for inspection. Editable layers, prompts,
provenance, source mapping, independent checks and archive hashes are packaged
locally. Earlier sealed packages remain unchanged; the full INTRO upscale stays
held. The user subsequently accepted the softer appearance ("Much better").
That review is recorded outside the sealed package to preserve its hashes.
Status: **six-frame appearance visually reviewed; native playback and renderer
validation pending**. The next recommended pilot is the complete 16-frame
`fire_f` sequence. Its interpreter configuration uses ordered frames 01–16 and
looping off: a one-shot fire burst and fade. Preserve the bright start and fading
tail while reviewing glow, frame consistency and transparency. The raw speed
token is 16, with units still unverified. The user subsequently authorized that
work, and the [complete fire pilot](work-ahead-fire-animation-pilot.md) is now
prepared for visual review.
