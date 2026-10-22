# D7VK evaluation for the MW3 recomp

Evaluated 2026-10-12. **Decision: retain D7VK as a strong adaptation candidate;
do not adopt the released DLL as the production x64 renderer yet.** Its actual
Windows Vulkan path passes an authored graphics fixture, and its source contains
an MW3-specific compatibility profile. It still needs an x64 source build,
guest/host adapters, validated presentation, and stricter error propagation.

This advances backend readiness from source plausibility to executed
DirectDraw4/IDirect3DDevice3 surface/draw interoperability on the local GPU.
It advances no translated application execution boundary. E1/E2/E3 remain open;
the last verified selected-startup count remains 131/144 in its retained scope.
No game launch, original executable fallback, capture replay, acceptance job,
system DLL replacement, or commit occurred.

## Inputs and isolation

- Source: [D7VK v2.3](https://github.com/WinterSnowfall/d7vk/tree/ff123cb08ff1fcf6575a6ef8fb79d824a84e56c4),
  commit `ff123cb08ff1fcf6575a6ef8fb79d824a84e56c4`.
  Tag object `05061164a95d25506a6e23326d95eb0f3fbf5ae5` peels to that commit.
  A shallow, unmodified checkout is under ignored
  `local/work-ahead/d7vk-evaluation/source-v2.3/`.
- Official [release archive](https://github.com/WinterSnowfall/d7vk/releases/tag/v2.3):
  `d7vk-v2.3.zip`, SHA256
  `ed7eec7d622d81c3606e3a7e705de955da65aba9d16ea812aa88711980b1bb66`.
  The downloaded bytes match the digest published by GitHub's release API.
  This binds the artifact; no source-to-binary reproducible build was established.
- Released `x32/ddraw.dll`: SHA256
  `00211f2f9f8589845940973ad8195f08f5f724510a2b800566e31f7c170e9f34`.
  The archive contains one DLL and no x64 binary.
- Host: Windows, MSVC 19.51.36256.0, Windows SDK 10.0.26100.0.
  Provider log identifies AMD Radeon RX 9070 and AMD proprietary driver 2.0.395;
  the integrated AMD adapter was also enumerated. No cross-vendor check.
- Process inspection found controls acceptance PID43820 and eight CRT/MFC lift
  workers active. They were left untouched; no active SQLite was opened and no
  long acceptance/translation job was duplicated. Existing modified graphics,
  asset and documentation files were not edited.
- The AGENTS.md paths `m4-Codex-work-review-2026-10-11.md` and
  `Codex-m4-continuation-handoff.md` are absent. The existing Claude-named review
  and continuation documents were read along with the current plan/roadmap.

## Which interface implementation matters

Our [observed graphics boundary](mw3-live-graphics-trace.md) includes
`IDirectDraw4`, `IDirect3D3`, `IDirect3DDevice3`, transformed triangle fans,
FVF `0x1C4`, 32-byte vertices and flags `0x18` in the sampled original run.
The [surface work](live-native-rendering-current-work.md) additionally records
RGB565 write locks and full/partial D16 zero depth fills. Those observations
are bounded and used an app-local dgVoodoo provider; they are not a complete
inventory or an unwrapped retail-driver baseline.

In D7VK, `src/ddraw/d3d6/d3d6_interface.h` implements `IDirect3D3`, and
`d3d6_device.h` implements `IDirect3DDevice3`. The `d3d3/` directory instead
implements older interfaces/execute-buffer work. API interface suffixes must
not be confused with the DirectX generation. The correct MW3 path is:

```text
DirectDrawCreate -> DDraw4Interface -> D3D6Interface / D3D6Device
    -> modified D3D9 implementation -> DXVK Vulkan backend
```

`d3d6_device.cpp:1504` forwards transformed primitive draws to D3D9
`DrawPrimitiveUP` after legacy state and dirty-surface handling. The D3D9
backend is linked into D7VK's DDRAW library; v2.3 does not require a separate
stock DXVK `d3d9.dll` for this path. Its private
`IDxvkLegacyD3DDeviceBridge` also means replacing that backend with arbitrary
stock D3D9 is not an equivalent integration.

## Contract assessment

| MW3-related contract | D7VK implementation / measured result | Remaining limit |
| --- | --- | --- |
| DD4 -> D3D3 -> HAL device3 | QI and creation passed on Windows | x32 authored fixture, not guest ABI or game startup |
| Transformed FVF/fan draws | Six scene intervals; actual pixel checks pass | No varied RHW/interpolation, full frame or indexed live case |
| RGB565 textures and updates | 2x2 texture upload, mutation/rebind and later draw pass | No other texture formats, mip chain, filtering or color keys |
| D16 full/partial zero fill | Later depth-tested draws distinguish cleared region from preserved exterior | Authored GREATER comparison; not asserted as MW3's recovered state |
| CPU backbuffer-like writes | Green write survives later unrelated GPU draws | Offscreen target, positive pitch, no Flip chain or guest-memory copy |
| GDI writes | GetDC/SetPixel/ReleaseDC blue write survives a later draw | One normal-mode offscreen write, not MW3's GDI/menu composition |
| Presentation and menu transitions | Source has MW3-specific options | Not executed by this fixture; no live menu claim |
| Failure/resource semantics | Many provider failures propagate | Concrete masked transfer failures and success stubs need treatment |
| x64 recomp integration | x64 build recipe and MSVC branches exist | No D7VK x64 source build or guest adapter was executed |

The MW3 entry in `src/util/config/config.cpp:1987` enables
`ddraw.forceLegacyPresent=True` and `ddraw.emulateFrontBuffer=True` to address
missing menu backgrounds on exit/other transitions. This is a useful source
lead, not proof that our native menu works. The fixture executable has a
different name, so this profile was not automatically selected. A future native
host must select justified options explicitly rather than depend on its filename.

## Executed checks and retained failure

The authored [fixture](../tools/d7vk-evaluation/README.md) builds with `/W4 /WX`
as Win32 and x64. It uses no game content, DLL imports from the game, original
game code, or generated translations. The normal-mode window stays hidden.

- `local/work-ahead/d7vk-evaluation/run-r1/`: initial authored target requested
  SYSTEMMEMORY while creating a HAL device. D7VK rejected it with
  `D3DERR_SURFACENOTINVIDMEM` (`0x887602EB`), and the fixture failed visibly.
  Source confirms the relevant validation in `ddraw_common_surface.h:434`.
  This is a fixture setup mismatch, not evidence of an MW3 defect.
- `run-r2/`: target/depth changed to VIDEOMEMORY; six sampled pixel checks
  passed for draw/depth/CPU-write behavior, exit 0.
- `run-r3/`: extended with texture mutation and GDI preservation. Six scene
  intervals, eleven exact RGB565 pixel checks, successful exercised HRESULTs,
  exit 0. Provider log confirms Vulkan loading/device creation and has no
  `warn:`/`err:` lines. Vulkan validation layers were not enabled; absence of
  log warnings is not a Vulkan validation-layer result.
- The x64 fixture built successfully, but loading the shipped x32 DLL failed
  with Windows error 193, exit 3. This confirms that artifact cannot be used
  in our x64 host; it does not establish that an x64 source build is impossible.

`run-r3/` retains fixture source/CMake snapshots, executable, output, provider
log and input hashes. Source/build/result identities are in `inputs.json`.
No final-frame screenshot or image was used as an output seed. Pixel reads are
sampled correctness checks, not exhaustive images. No presentation, playable
Training, original/native image comparison or memory-leak proof was performed.

## Concrete adaptation gaps

1. **DirectDraw provider.** `ddraw_main.cpp` loads `ddraw_.dll` or system
   `ddraw.dll`; surface creation, locks, fills and GDI still depend on that
   implementation. DD4 QI for `IDirect3D3` also first queries the proxied object.
   D7VK is not a complete portable DirectDraw runtime. For Windows-first reuse,
   evaluate its native system-provider path in x64. For portability or owned
   guest surface storage, supply/adapt that provider boundary.
2. **Guest memory and COM.** Preserve 32-bit guest layouts, objects, vtables,
   handles and callback calling conventions. Keep x64 pointers in a host
   registry. Marshal pointer-bearing descriptors/effects/callbacks explicitly;
   do not pass guest structs directly to x64 SDK interfaces. Lock readback must
   expose validated guest memory with the expected pitch/format, and Unlock
   must transfer the actual guest writes without inventing prior contents.
3. **Truthful failures.** `d3d6_device.cpp:553` and `:584` contain
   success-returning BeginIndexed/Index stubs. LINEPATTERN/WRAPU/WRAPV and other
   states also contain unimplemented/ignored behavior. Current captures do not
   establish that MW3 requires these; do not claim a demonstrated game defect.
   Fail required unsupported operations at the adapter boundary until admitted.
   More critically, `ddraw_format.h:903` / `:949` transfer helpers return void
   and log lock failure; `ddraw4_surface.cpp:1172` / `:1190` clear dirty flags
   without returning transfer failure. A wrapper alone cannot recover that lost
   status: change the helpers/callers or replace that transfer path before
   granting our strict resource/error contract.
4. **Presentation/settings.** Exercise primary/backbuffer ownership, Flip and
   menu-to-Training-to-menu transitions with explicitly selected profile options.
   Review automatic resize, pixel-center changes, FSAA, timing and format
   substitutions against original-compatible requirements before enabling them.

## Build and license feasibility

The source includes `build-win64.txt`, a packaging path for both architectures,
Windows/MSVC branches in Meson, and a DDRAW target without an x86-only guard.
The recipe requires Meson, a compiler/resource compiler, glslang, Vulkan and
SPIR-V headers, `dxbc-spirv` and `libdisplay-info`. Meson and the recipe's MinGW
compiler were absent from PATH here. Existing MSVC/CMake could build our fixture;
that does not prove they can build all of D7VK. No source build, global tool
installation or submodule initialization was attempted during this evaluation.

Pinned submodule commits declared by this source:

| Dependency | Commit |
| --- | --- |
| Native DirectX headers (non-Windows path) | `9df86f2341616ef1888ae59919feaa6d4fad693d` |
| SPIR-V headers | `04f10f650d514df88b76d25e83db360142c7b174` |
| Vulkan headers | `8864cdc896bbc2a9b6eb36b3218fc9ef57908d77` |
| dxbc-spirv | `bf14419e5fa7eacb817b7b632f03cb61d61bbad7` |
| libdisplay-info | `275e6459c7ab1ddd4b125f28d0440716e4888078` |

D7VK's top-level LICENSE is zlib/libpng; preserve its notice, mark modified
versions and attribute upstream. Its SHA256 is
`8221f636c9298344a6a98a4aa38c15b616d62126d2b0cf40ddc0ba50a57f1f3c`.
Pinned dxbc-spirv and libdisplay-info LICENSE files were downloaded/read and
are MIT. These inspected notices support reuse feasibility; a full transitive
notice inventory remains required before adoption/distribution. D7VK's release
notes put it in maintenance mode; plan to own integration and regression work.
No third-party implementation has been added to our production build.

## Decision and next executable boundary

Prefer an **adapted D7VK frontend plus its matching Vulkan backend** over
reimplementing all fixed-function rendering immediately, conditional on the
following next check: build the pinned DDRAW target as x64 with DDRAW/D3D9
enabled and DXGI/D3D8/D3D10/D3D11 disabled, then run this same fixture against
that x64 DLL and its actual DirectDraw provider. Use an isolated local toolchain
and build directory; retain unsuccessful builds rather than infer support from
recipes. The release DLL remains an x32 diagnostic provider only.

If that passes, implement the smallest guest DD creation/QI adapter to the
actual host provider, with failure outputs/lifetimes tested against the recovered
[video contract](m4-video-backend-contract-r1.md). Surface Lock/Unlock and
required callbacks follow. Patch masked transfer failures before treating that
surface boundary as admitted. The existing application execution lane can
continue independently; neither this fixture nor wrapper adoption bypasses
startup or supplies native-game acceptance credit.

For the separate original-game x32 development lane, follow the
[MW3 D7VK wrapper plan](mw3-d7vk-wrapper-plan.md). Its first live test uses the
existing x32 release; the x64 build above belongs to native recomp integration.
