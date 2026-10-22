# Graphics compatibility boundary

Follow the [current integration plan](../../docs/faithful-modernization-plan.md):
connect the recovered game-facing graphics contracts to Vulkan in the native
host, and keep capture replay separate from live translated producers. Reuse the
[video contract](../../docs/m4-video-backend-contract-r1.md),
[presenter extraction review](../../docs/m4-vulkan-presenter-extraction-review-r1.md)
and [active graphics work](../../docs/live-native-rendering-current-work.md).

Reserved for observed legacy graphics/COM contracts. No integrated renderer exists yet.
Vulkan is the user-selected backend target as of 2026-10-08. The standalone
[learning prototype](../../docs/vulkan-learning-prototype.md) proves bounded GPU
transfer/readback only.
The later [authored raster prototype](../../docs/vulkan-raster-prototype.md)
passes texture/depth/fog/blend checks offscreen with validation; native graphics
integration remains open. First preserve surfaces, formats, state, presentation
and error behavior. [Live tracing](../../docs/mw3-live-graphics-trace.md) now
confirms the sampled DirectDraw4/Direct3D3 path and a transformed 32-byte vertex
layout; full frame state/resource recovery remains open. Correct rendering precedes visual
enhancements. Game-facing interfaces remain separate from backend objects.

The [isolated Vulkan HUD pass](../../tools/vulkan-hud/README.md) now uploads
selected private v3 vector/glyph components at output density and emits ordered
screen-space draws with separate logical sizes. Six offscreen GPU/oracle checks
passed at 4:3, 16:9 and ultrawide, including 4x texture density without layout
growth. Recovered gameplay state, original HUD suppression and world/HUD
presentation ordering remain open; this is not an integrated game renderer.
