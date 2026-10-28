# Vulkan textured raster experiment and MW3 creation leads

Executed 2026-10-09, Windows x64, AMD Radeon RX 9070. Vulkan remains the selected
renderer target. This is an authored offscreen scene, separate from MW3 startup.

## Accepted authored scope

The prototype uploads a 2x2 RGBA texture through a staging buffer into an
optimal-tiled sampled image. GLSL shaders draw two full-target triangles into a
256x256 RGBA8 attachment with a D32 depth attachment. Three ordered draws exercise
opaque texturing, rejection of farther geometry, and a nearer surface with fog
and alpha blending. Image transitions, transfer/host barriers and a fence precede
readback. Resource teardown occurs before final validation acceptance.

Four experiments passed Khronos validation, including synchronization validation,
with zero warning/error callbacks. An independent Python oracle checked every
pixel against texture quadrant, fog and blend equations. It allows one channel
unit for UNORM rounding; observed maximum error was zero in every experiment.

| Mode | What changes | Pixels checked | Maximum channel error |
| --- | --- | ---: | ---: |
| default | Depth test, 50% fog toward gray, 50% foreground alpha | 65,536 | 0 |
| depth-off | Farther black geometry overwrites the opaque baseline | 65,536 | 0 |
| fog-off | Foreground retains original texture colors | 65,536 | 0 |
| opaque-front | Foreground fully replaces the baseline | 65,536 | 0 |

All three controls were also rejected against the default oracle. A deliberately
changed pixel was rejected. This gives 262,144 independently checked pixels and
causal evidence that the selected depth/fog/blend operations affect output.
It does not cover perspective geometry, interpolated depth, texture filtering,
legacy color keys, arbitrary meshes, presentation or game behavior.

Sources: `tools/vulkan-probe/raster.cpp`, `scene.vert`, `scene.frag`,
`verify_raster.py`, `run-raster.ps1`. Local output and receipts:
`reports/vulkan-probe/raster-{mode}.ppm`, corresponding run text and verification
JSON. CMake builds both probes and compiles shaders. MSVC `/W4 /WX` passed.

## Toolchain and validation environment

Khronos headers remain pinned to the first probe's version. Shader compiler:
glslangValidator 15.3.0 from LunarG SDK 1.4.321.0. Validation manifest reports
API 1.4.321. Installer SHA-256:
`14ebc56ef981e03a292adadd2559fbbfcd0289ec157bfd0f0d5f9fdcb40042a9`.
Validation DLL SHA-256:
`e67f0dd9c196f1c9730f49b2be0313bc974e8c8851782cf9934430ed7a0f12c8`.

The normal SDK install required administrator access and rolled back. Instead,
tools were extracted from its embedded 7z archive into ignored
`local/tools/vulkan-sdk-portable`. No installed SDK or registry modification is
required for this experiment. The unused initial glslang main-tot download is
not the compiler used for accepted shaders.

Initial runs reported installed overlay naming and duplicate-driver-layer loader
warnings. These failures were not counted as clean passes. The accepted runs
use `VK_LAYER_PATH` for the extracted explicit validation layer and
`VK_IMPLICIT_LAYER_PATH` pointing to an empty local directory. This isolates the
child from implicit overlays without muting warning callbacks or changing system
configuration. The runner restores both environment variables. Loader behavior
is documented in the [Khronos loader architecture](https://github.com/KhronosGroup/Vulkan-Loader/blob/main/docs/LoaderInterfaceArchitecture.md).

## MW3 static creation path

Analysis is bound to admitted MW3 U.S. 1.2 SHA-256
`95bc2c114c9b2e5c5ada8e40ca78cc79470f862e45313ffad0d1e8e6d4d916bf`.
LLVM 21.1.8 private linear disassembly and SDK GUID definitions give these
specific static leads, beyond the earlier broad GUID block:

| Site | Static observation and interpretation |
| --- | --- |
| `0x5AC644` | Import thunk targets the admitted DirectDrawCreate IAT slot at `0x5BB044` |
| `0x577D51` | Candidate routine `0x577D40` calls that thunk, testing the returned status |
| `0x577D7E` | Returned object's first vtable slot is called with IID_IDirectDraw4; output destination is `0x809358` |
| `0x577D9E` | Success path calls original object's slot+8, consistent with Release |
| `0x578C4D` | Object read from `0x809358` receives IID_IDirect3D3 through slot zero; destination `0x80936C` |
| `0x578C82` | Result receives slot+0xC call with callback `0x578CD0`, consistent with IDirect3D3::EnumDevices |
| `0x57A95C` | Another initialization candidate requests IID_IDirect3D3 from `0x809358` |
| `0x57A997` | Result receives slot+0x28 call with a device GUID and callback `0x57B100`, consistent with EnumZBufferFormats |
| `0x57A572` | Separate capability candidate requests IID_IDirectDraw2; this does not establish the main rendering interface |

The DirectDraw4/Direct3D3 interpretations follow matching constant addresses,
COM slot ordering and surrounding argument setup. These are static candidate
contracts: runtime branch reachability, provider identity, return behavior,
object lifetimes and complete function/control-flow recovery are still unproven.
Do not install hooks or declare a complete D3D interface bridge from this table.
Private disassembly remains `local/analysis/mw3-vulkan-disassembly.txt`.

## Next work

Update 2026-10-09: [live graphics tracing](mw3-live-graphics-trace.md) now confirms
the DirectDraw4/Direct3D3 chain and 64 successful transformed-vertex draws in the
original game. The sampled layout is documented there; complete frame resources
and state remain open.

Recover the DirectDrawCreate/QueryInterface boundary and capture actual interface
requests with typed instrumentation. Then establish device creation and the
draw-call/vertex contract before recording a replayable game frame. Window and
swapchain presentation is a separate authored prototype gate. Native M4/M5
milestones remain unchanged; Linux execution and ray tracing are untested.
