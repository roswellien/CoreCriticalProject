# MW3 live graphics creation and bounded draw trace

Executed 2026-10-09 against admitted MW3 U.S. 1.2. This is original x86 game
execution with authored call-through observation, not native gameplay or a Vulkan
renderer. It advances graphics recovery without changing M4/M5 acceptance.

## Instrumentation and checks

The new `tools/graphics-trace` Win32 DLL uses the existing hash-bound pre-entry
launcher. It changes the process-local DirectDrawCreate IAT slot and selected
object vtable pointers; game and provider files on disk are unchanged. Original
method arguments and results are forwarded. Per-object tables copy full SDK
interface sizes, preserving every untouched method pointer. Tables/forwarding
metadata persist until process exit and support cached table addresses.

The observer covers DirectDrawCreate, QueryInterface, IDirect3D3::CreateDevice,
IDirect3DDevice3::BeginScene/EndScene, DrawPrimitive and DrawIndexedPrimitive.
FP/vector state and Win32 last error are preserved around instrumentation;
underlying methods retain their own observable effects. Authored fixtures check
seven typed method kinds, actual successful and failed HRESULT propagation,
caller vertex/index memory, failed QueryInterface output, last error and a
512-byte FXSAVE guard under deliberate MXCSR/last-error corruption. These fixtures
are marked non-live. They do not prove every register/flag or all live provider
behavior. Win32 Release builds pass MSVC `/W4 /WX`.

The trace is capped at 1,024 total events, 64 combined draws, 64 combined scene
calls and 512 object registrations. Samples contain at most three vertices or
256 bytes. Those budgets are declared observation limits; they are not full
frame coverage. Synchronous logging and vtable indirection can affect timing.
Unknown layouts are reported without inferred samples. No graphics code hook or
replacement rendering is installed; DLL initialization does no work in DllMain.

## Live results

Run: `reports/graphics-trace/20261009-050919-885`, game PID 15704. The launcher's
temporary debugger detached before gameplay. The resulting live records contain:

| Observation | Count |
| --- | ---: |
| Successful DirectDrawCreate | 2 |
| Instrumented interface objects | 8 |
| QueryInterface results | 5 |
| Successful CreateDevice | 1 |
| Successful DrawPrimitive samples | 64 |
| BeginScene / EndScene samples | 32 / 32 |

Actual successful interface requests include IDirectDraw4 and IDirect3D3; the
created device is IDirect3DDevice3 with the HAL device GUID. The import target
belongs to the app-local `DDRAW.dll`, SHA-256
`612a24408a090a3c6f3886557fa18034ee742e94ad0a40ebdf854d2816176c2e`.
Its identity matches the loaded-module inventory and a fresh on-disk rehash.
The inventory also records app-local `D3DImm.DLL` and the loaded graphics modules.
These results describe this compatibility-provider configuration, not every
possible MW3 driver/runtime setup.

All 64 sampled draws returned success. They use primitive type 6 (triangle fan),
FVF `0x1C4` (452), flags `0x18` and vertex counts ranging from three to eight.
The FVF specifies transformed XYZ/RHW, diffuse/specular packed colors and one
default 2D texture-coordinate set. Its SDK-defined vertex stride is 32 bytes.
No live indexed draw was observed within this budget; the indexed wrapper is
fixture-tested only. Draw attribution to terrain/mechs/HUD and mission stage
requires additional correlation, not inference from the vertex format.

The verifier independently checked input/tool/source hashes, trace ordering,
process identity, non-live fixture separation, actual provider identity, live
creation results, FVF stride/transform interpretation and bounded sample lengths.
Nine causal controls reject fixture-only logs, missing records, failed draws,
wrong stride, wrong transformed flag, short samples, missing device output,
failed state guard and incorrect provider identity. Receipts are
`verification.json` and `controls.json` in the run directory.

Passive monitor: `reports/mw3-monitor/20261009-050953-4595d822`. It attached after
initialization and observed exit code zero, no alerts and no dropped segments.
It did not capture debugger exceptions, visual defects or frame timing. In reply
to the requested Training movement/firing and normal-quit check, the user
confirmed on 2026-10-09: "everything ran normally". This accepts the requested
live session's user-observed behavior alongside the independently verified trace
and zero exit; it does not establish extended stability or comprehensive visual
equivalence. The session is closed, with no instrumentation left
in a running game. Normal future launches use the original files.

## Sampled vertex contract and renderer implications

| Byte offset | FVF-defined field | Vulkan recovery requirement |
| --- | --- | --- |
| 0, 4 | Screen-space X/Y floats | Recover viewport and original pixel-center convention |
| 8 | Screen-space depth float | Recover depth range, comparison and any game conversion |
| 12 | Reciprocal homogeneous W float | Preserve perspective interpolation when reconstructing clip coordinates |
| 16 | Packed diffuse color | Decode legacy channel order; verify alpha/color-space behavior |
| 20 | Packed specular color | Recover specular/fog state and its use in fixed-function shading |
| 24, 28 | U/V floats | Recover bound texture, dimensions, sampler and address modes |

This draw boundary already receives transformed screen-space geometry. It is a
promising faithful Vulkan compatibility boundary. It cannot supply world-space
geometry for ray tracing by itself. A world-scene renderer needs earlier mesh,
transform, camera and material recovery. The observed format applies only to
sampled draws; other formats remain possible.

Do not assume a modern projection, a half-pixel correction, UV orientation or
sRGB conversion before comparing the recovered behavior. Preserve legacy depth,
RHW, packed-color and texture-stage semantics first.

## Next capture gate

The first bounded capture and offscreen Vulkan replay are now documented in
[Vulkan live replay](vulkan-live-replay.md). The requirements below describe the
remaining comprehensive capture gate; the new observer covers a selected draw
profile and has not established command closure or visual equivalence.

Extend recovered instrumentation to the required surface/texture creation and
uploads, render target/viewport, texture bindings/stages, depth/blend/fog state,
presentation boundaries and lifetime updates. Capture all vertices/indices and
resources for one explicitly selected frame with declared size limits. Replay
that frame offscreen in Vulkan and compare against its original output. Current
three-vertex samples are not a replayable frame. Keep payloads and full traces
local; commit only authored bridge code and reviewed metadata/contract summaries.
