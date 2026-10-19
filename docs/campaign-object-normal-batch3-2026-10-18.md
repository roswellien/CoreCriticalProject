# Campaign object normal refinement — batch3, 2026-10-18

This batch addresses campaign encounter ranks7–10: `rockblok`, `txwall09d`,
`fishvill01` and `fishvill02`. It retains the preceding terrain and road work,
with terrain/object strength1.5. Only Material Normal Preview selects the new
candidate. Regular Play and the other previews are unchanged.

## Artwork and relief

The live `rockblok` replacement was128×128, enlarged from a32×32 original.
No detailed alternative was located in the saved candidate/export folders.
A new AI-assisted stone color candidate is imported at512×512 across all six
C1 banks and receives a matching512×512 color-derived normal draft. This is
new interpreted stone artwork, not recovery of missing original detail or a
claim of exact preservation of individual stones. Source images, prompt and
installed RGB565 pixels remain local for art review.

The bank rewrite updates offsets and the rock descriptor/dimensions. Every
other entry payload is checked byte for byte against its source bank:581 entries
in each texture bank and580 in each rtexture bank. This preserves the upgraded
road, shoreline, other artwork and their existing normal identities. Original
source banks stay unchanged. A single new full-pixel rock key covers the common
replacement across six banks; old keys remain registered for other use.

Separate AI-assisted height candidates for the wall and wooden planks pass
coarse zero-offset alignment for three identities each. Wall correlations are
.900–.933; plank correlations are .911–.912. A fourth wall identity
`(1024,1024,1,2436716351456778965)` instead prefers a vertical shift and keeps its
previous normal map. The first preparation attempt fails visibly on this
identity; the successful configuration explicitly selects the reviewed keys.
Coarse correlation does not establish physical height or perfect fine detail.

The second village texture is an atlas. Four explicitly selected vertical
panels receive independent shallow grain estimates; the left checker/window
strip stays flat. Each panel is filtered and differentiated independently with
clamped boundaries, with a two-pixel flat normal guard. Neither painted panel
color changes nor neighboring panel content are allowed to create boundary
ridges. This is a technical masked refinement, not a completed authored height
map for every feature of the atlas.

The final catalog has4,001 identities: eight previous bindings change,3,992
previous normals remain byte-identical and one new rock identity is added.
It contains76 pages and500,081,176 bytes (476.91MiB), under the existing512MiB
limit. This is a content/memory tradeoff; no performance improvement is claimed.

## Native and narrow checks

Fresh baseline/candidate runs follow the same original C1M1 route with the
resolved midday preset, identical camera inputs, world strength1.5 and replay
video off. All2,600 original frame/draw-count/hash triples match. The candidate
loads all4,001 normal identities and reads the new rock page during gameplay.
Budget exits are intentional test stops, not crashes or normal mission quits.

Four synthetic atlas checks pass: adjacent flat colors make no ridge, changing
one panel cannot affect its neighbor, excluded regions stay flat, and overlap
fails explicitly. Six existing relief checks also pass. Full catalog reads
verify the declared binding changes and retained data. No runtime executable,
gameplay source, simulation setting or acceptance count changes.

- [Stone walls before](https://drive.google.com/file/d/1OShEuoxPyMI3tX5FTlwcyPIo5ffBGYxt/view)
- [Stone walls after](https://drive.google.com/file/d/1H8TLZLjcuaVchn1QRqtPT5MvYCYU4fHF/view)
- [Village before](https://drive.google.com/file/d/14fVMAL6fVoXkspFTal28eq2IrpkDSSpP/view)
- [Village after](https://drive.google.com/file/d/1tCaBoujDF6z7UTpWwB9OesabaT_x6Edi/view)

These3440×1440 captures compare the combined rock-color and normal batch; they
do not isolate each change or guarantee that all plank details are visible at
the village camera distance. Private Drive uploads retain existing sharing.

Execution boundary advanced: the next four C1 material families now have
reviewed relief treatments/new rock content reaching the live native preview.
Final artwork approval, the excluded wall variant and the rest of the100 remain
open. The next queued families are fishing-boat textures. Acceptance stays131/144.
No commit is made.

Local evidence: `C:/Users/jcbla/MW34SunTests/campaign-object-batch3-20261018/`.
Workspace art/prompts: ignored `local/material-authoring-r1/authored-batch3/`.
The [campaign preparer](../tools/remaster-launcher/prepare_campaign_terrain_relief.py)
now supports explicit reviewed-key selection and isolated atlas panels, reusing
[height differentiation](../tools/remaster-launcher/prepare_authored_relief.py)
with a clamped option. [Atlas tests](../tools/remaster-launcher/test_atlas_relief.py)
cover the concrete cross-panel leakage risk.
