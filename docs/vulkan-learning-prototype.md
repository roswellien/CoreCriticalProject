# Vulkan renderer direction and first learning experiment

Decision: 2026-10-08, explicitly requested by the user. Vulkan is the target
graphics backend for MW3. Windows x64 is the first implementation platform;
Linux portability is a design goal. Native gameplay startup remains M4 work.
Graphics research and isolated authored prototypes can proceed now; enhanced
graphics still require recovered behavior and the compatibility baseline.

## Design direction

Keep three boundaries: guest DirectDraw/Direct3D compatibility objects and
32-bit ABI; authored renderer commands/resources; Vulkan backend. Native Vulkan
handles stay in host tables, never in guest fields. Implement only recovered
interface contracts. Missing commands fail explicitly, with call/object identity.

Use Vulkan directly for the first experiment; do not introduce NVRHI or select
a whole replacement engine. Evaluate SDL3 for window/surface creation, volk for
dispatch and VMA for memory allocation when the real renderer needs them.
Those libraries are candidates, not current dependencies. Add SPIR-V shaders
and Khronos validation layers for the next raster prototype. Require a clean
validation run before describing that prototype as accepted.

Maintain a raster baseline. Ray tracing is an optional capability tier, requiring
feature/property queries and dependencies beyond extension-name enumeration.
macOS needs a separately validated portability implementation and feature subset;
Vulkan does not guarantee identical advanced capabilities on every platform.
References: [Khronos ray tracing guide](https://docs.vulkan.org/guide/latest/extensions/ray_tracing.html),
[portability sample](https://docs.vulkan.org/samples/latest/samples/extensions/portability/README.html).

## First executed prototype

`tools/vulkan-probe/main.cpp` builds independently of the game runtime. On this
Windows x64 host, MSVC 14.51 `/W4 /WX` passed after adding the required explicit
`<string>` include. The Vulkan loader enumerated:

| Device | Advertised Vulkan version | Relevant advertised extensions |
| --- | --- | --- |
| AMD Radeon RX 9070 | 1.4.349 | swapchain, acceleration structure, ray query, ray tracing pipeline |
| AMD Radeon(TM) Graphics | 1.4.315 | same four |

The first graphics-capable device was selected. A graphics queue executed four
buffer fills, with explicit transfer/host synchronization and a completion fence.
All 65,536 readback words matched their authored expected values. The output is
a 256x256 four-band PPM swatch. This establishes device creation, allocation,
command submission and coherent readback on this host. It establishes no
rasterization, presentation, validation-layer correctness, ray tracing, game
compatibility or Linux execution. The command semantics follow the
[Khronos buffer-fill reference](https://docs.vulkan.org/refpages/latest/refpages/source/vkCmdFillBuffer.html).

Local receipts: `reports/vulkan-probe/run.txt`, `swatch.ppm`, `mw3-pe.json`,
`mw3-guid-leads.json`. Headers are pinned in the tool README.

An independent Python read of the PPM verified its header, exact payload size and
every RGB byte against the four expected bands. A one-byte-mutated executable
was rejected by the GUID tool before output creation. The probe's missing-output
argument returns usage with exit code 2. Swatch SHA-256:
`a9f426511a429660362a85e8902c6b2ebb811c5fe6e344fb87bcd52c623d1e9b`.

## First MW3 investigation

Fresh PE analysis admitted the exact MW3 U.S. 1.2 identity. The SDK GUID scanner
found 34 exact graphics GUID matches in `.rdata`, including DirectDraw 1/2/4,
surface 1/2/3/4, Direct3D 1/2/3, Device 1/2/3, Texture 1/2, execute buffer and
vertex buffer. They form a contiguous block. This broad block may include unused
linked constants; it does not identify the actual runtime interface version.

Start recovery at the known application service candidate `0x480570` and the
DirectDraw creation IAT sites. Follow actual QueryInterface GUID arguments,
returned objects and vtable calls. Bind all findings to the admitted hash.
Prioritize these observations in one original-game menu/Training session:

1. Provider/module identity and requested interfaces; creation results, object
   relationships, AddRef/Release ownership and cleanup.
2. Display/surface formats, dimensions, pitch, locks, blits, flips, palettes,
   color keys, texture uploads and lost-surface/focus behavior.
3. Draw entry points, primitive topology, vertex layout and transformed versus
   world-space vertices; matrices, viewport, depth, fog and blend state.
4. Separation of menu/HUD/particles/world, frame boundaries and resource updates.

Record complete return/failure behavior. Use the existing launcher only after
recovering each instrumentation ABI; the numeric/helper hook is not a generic
graphics hook. Full traces, texture payloads and frame captures remain local.
The next deliverable is a recovered creation/draw contract and one bounded frame
capture, not an assumed D3D version based on GUID presence.

## Next prototype gates

Update 2026-10-09: the authored textured raster/depth/fog/blend experiment passes
in its bounded offscreen scope, including synchronization validation and four
independent full-frame pixel comparisons. See [the raster record](vulkan-raster-prototype.md)
for accepted scope, controls, toolchain pins and specific MW3 creation-path leads.
The subsequent [live trace](mw3-live-graphics-trace.md) confirms actual interface
creation and bounded transformed-vertex draw observations with a clean monitored
exit. Complete captured-frame replay and native renderer integration remain open.

1. Authored Vulkan raster scene: textured triangles, depth, transparency and fog,
   offscreen readback; shader toolchain and validation layers recorded.
2. Surface/swapchain presentation: resize, minimize, focus, teardown and portable
   window abstraction, without coupling render frequency to game simulation.
3. Replay one admitted captured frame, preserving command order and state. Compare
   textures, alpha, depth, fog and output against original reference captures.
4. Integrate recovered menu services into native startup, then Training geometry.
5. After gameplay compatibility, add texture/display modernization; only pursue
   ray tracing after world geometry, transforms and material semantics exist.

No milestone completion credit is granted by the transfer prototype or GUID scan.
