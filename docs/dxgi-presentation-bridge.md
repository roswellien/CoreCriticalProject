# Vulkan/DXGI presentation compatibility

Issue [#102](https://github.com/roswellien/MW3Recomp-Private/issues/102) adds an
experimental presentation transport for Windows. Vulkan renders the game on the
selected physical GPU. A shared GPU texture carries the completed frame to a
DXGI swapchain on that same adapter. The native translated module is unchanged.

This addresses the observed RX 9070 configuration where Win32 Vulkan surface
capability queries return `-13`, including in an independent small program,
while DXGI presentation succeeds. The installed driver remains Adrenalin 26.7.1
(RX 9070 Windows driver 32.0.31035.1003). No driver or system settings are changed.

## Developer contract

Use a development host containing this change and set `MW34_DXGI_PRESENT=1` in
its launch environment. Unset/`0` retains the existing Vulkan WSI path; other
values reject visibly. The option is absent from the launcher UI. Windowed and
borderless modes are supported; exclusive fullscreen is explicitly rejected.
Validation below covers windowed presentation.

The bridge requires Vulkan 1.1, `VK_KHR_external_memory_win32`,
`VK_KHR_win32_keyed_mutex`, importable BGRA shared images and compatible image
limits. It matches the Vulkan physical-device LUID to the DXGI adapter LUID and
creates a hardware D3D11 device for that adapter. Missing identity, capabilities,
matching adapters or memory types fail rather than selecting another device.

The execution boundary advanced is completed native Vulkan frame -> GPU sharing
-> visible DXGI presentation. This does not change game logic, guest surface
dimensions or world shaders. The FidelityFX work in
[PR #100](https://github.com/roswellien/MW3Recomp-Private/pull/100) remains separate;
bounded combined integration checks are recorded in the
[Stage 2 evidence](fidelityfx-world-resolution.md#combined-rx-9070-integration).
Retained-color reconstruction remains incomplete.
SDK integrations that wrap a Vulkan swapchain, including frame-generation pacing,
are not covered by this transport check.

## Ownership and synchronization

`host/dxgi_present.hpp` owns the D3D11 device/context, swapchain, shared texture,
keyed mutex, imported Vulkan image and dedicated memory. The renderer detaches
it before destroying the Vulkan device. A temporary exported NT handle is closed
after import; both APIs retain their own payload references.

For each frame:

1. Vulkan acquires mutex key 0 and external-image ownership, clears the shared
   BGRA image and blits the source into its fitted destination rectangle.
2. Vulkan returns the image in `GENERAL` layout to external ownership and
   releases key 1 through the queue submission's keyed-mutex structure.
3. D3D11 acquires key 1, copies the shared texture to the DXGI backbuffer, flushes
   that work and releases key 0.
4. DXGI presents. Only `S_OK` increments the presentation counter; occlusion
   does not count as a presented frame. Mutex timeout/abandonment are errors even
   though their HRESULT values are positive.

Resize waits for Vulkan completion and the D3D11 read before retiring imported
memory. Parent-window changes reset swapchain ownership. Hidden/minimized
windows submit no presentation. Source upload and resident paths both support
the bridge. RGBA rows retain their supplied pitch; wide-world uploads use the
configured output aspect. The shared image is cleared each frame, including
single-pixel bars after rounding.

Normal presentation transports pixels entirely through GPU operations. The
explicit one-pixel test capture reads the actual backbuffer after its copy and
before `Present`; it is inactive during normal play. Keyed-mutex waiting can
serialize CPU/GPU work, and the bridge adds a GPU copy. No performance gain or
displayed-FPS claim is made.

Relevant contracts: [Win32 memory import](https://docs.vulkan.org/refpages/latest/refpages/source/VkImportMemoryWin32HandleInfoKHR.html)
and [keyed-mutex queue synchronization](https://docs.vulkan.org/refpages/latest/refpages/source/VkWin32KeyedMutexAcquireReleaseInfoKHR.html).

## Build and focused checks

Use the maintained [host build](../tools/m4-crt-heap-carry/HOST_BUILD.md).
The Windows SDK supplies `dxgi` and `d3d11`; no additional binary is packaged.
The new host source and modified host files are pinned in the source manifest.

The existing display fixture also links `dxgi.lib` and `d3d11.lib`:

```powershell
clang-cl /nologo /DNOMINMAX /DWIN32_LEAN_AND_MEAN /std:c++20 /EHsc /MD /Itools/m4-crt-heap-carry/host /I"<Vulkan-Headers>/include" tools/remaster-launcher/test_launcher_display.cpp /Fo"<local-output>/display.obj" /Fe"<local-output>/display.exe" /link user32.lib gdi32.lib dxgi.lib d3d11.lib /incremental:no
$env:MW34_TEST_GPU = 'AMD Radeon RX 9070'
& <local-output>/display.exe --dxgi-present
& <local-output>/display.exe --dxgi-exclusive-reject
& <local-output>/display.exe --dxgi-setting-reject
```

The fixture verifies actual copied backbuffer pixels for RGB565 and padded RGBA
uploads, resident HUD/color output, guest depth, fitted bars after resize, and
minimize/hide restoration. Sixteen alternating resident frames run without
diagnostic readbacks, followed by a distinct green frame with pixel verification.
It completes 25 presentations on the RX 9070 with
Khronos synchronization validation enabled and no errors. A black replacement
for the GPU copy fails its color assertion. Mismatched mutex keys reject with
timeout 258, rather than acknowledging a frame. Removing configuration guards
or denying the import capability fails the corresponding checks. Temporary
controls are restored before building the host.
An invalid physical-adapter identity is also rejected before texture sharing.

## Native validation and remaining limits

The development host uses published runtime 1.0.44 support inputs and the 13
verified published pack archives already prepared for Stage 2. It preserves the
translated DLL SHA-256
`6d6e3c25fef68727113a6d52859253883dbb554958ddaa5a091187667aa8bfa5`.
Private receipts, isolated games and captures remain under `local/9070/`.

The initial 1,000-frame and longer 2,200-frame visible runs reach native Training
at 3440x1440, FXAA and 16x AF on `AMD Radeon RX 9070`. Both report the hardware
LUID match and complete every requested presentation through the bridge, with
Khronos synchronization validation enabled and no diagnostics. The longer run
records 6,142 native scenes. GPU lighting/shadow paths are enabled with sun
strength 0 and ambient 1; this does not validate nonzero directional lighting.
Runs deliberately stop at their configured frame budget (the existing harness
reports that stop as exit 1), rather than demonstrating normal shutdown.

Rendered-target captures at frames 1801/2101 are byte-identical to the published
runtime reference: `0c822b3dd82b25444b1c0dc66dd14bdc26ffb1f49c89a64087404b4ff24389cd`
and `0f7f6f526a793c5cbdd63748fd69949471a298582e83544fe87111dd4d52638e`.
These compare Vulkan render output; the independent backbuffer fixture checks
the presentation copy. This is not an original-executable equivalence claim.

Default-path checks, final source/build validation and any later native run are
recorded in the PR. The final source-pinned host
(`4b21e64d18560be523d7ac03d8ed2f280dc677c7150ba856203e73d4edf4257d`)
repeats the 2,200-frame visible run with the same 6,142 scenes, matching reference
captures and clean synchronization validation (`native-bridge-review`). CMake
build, 25 CTest cases, format-check and report-only style checks pass. The default
headless Vulkan fixture and explicit rejection modes pass as well.

Broader play, device loss, borderless/VRR/HDR behavior,
performance, another physical PC and independent review remain open. The raw
Vulkan WSI failure is still present; this optional transport avoids that failing
surface path. No driver update, merge or release is performed by these checks.
