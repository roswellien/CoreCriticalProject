# Graphics compatibility boundary

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
