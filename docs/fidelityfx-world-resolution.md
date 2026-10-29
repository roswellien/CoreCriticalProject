# Independent world resolution (FidelityFX P1)

This development-only renderer step separates world raster dimensions from the
output/HUD target. It implements issue #99, following the
[implementation plan in PR #96](https://github.com/roswellien/MW3Recomp-Private/pull/96)
and the [P0 feasibility work in PR #98](https://github.com/roswellien/MW3Recomp-Private/pull/98).
It does not load FidelityFX, dispatch FSR, add motion vectors or generate frames.
Neither earlier PR is implicitly merged by this change.

## Contract

The canonical host accepts `MW34_WORLD_SCALE_PERCENT=50..100` (integer, default
100). The percentage applies to each output dimension, rounding down. For
1920x1080 output, 50 selects a 960x540 world raster. Set an explicit
`MW34_REMASTER_WIDTH` / `MW34_REMASTER_HEIGHT`; reduced mode supports AA Off or
FXAA and rejects SSAA. FXAA retains its existing resident-rendering/GPU-HUD
requirements. This control is intentionally absent from launcher settings.

The renderer owns a second color/D32-depth image pair and framebuffer. A leading
full color clear can begin reduced work. Live Training instead submits a separate
full depth clear: this begins reduced work only at a new target or after resident
presentation. A mid-frame depth clear cannot restart reduced work after the HUD.

Before HUD, guest readback, capture or resident presentation, the world image is
linearly scaled to output size and D32 depth is transferred with nearest sampling.
FXAA runs before HUD. Subsequent mixed world passes stay at output size until a
new frame boundary or full color clear; they cannot repeatedly filter the HUD.
Menus/frontend canvases retain their existing fitted output size. Target changes and shutdown retire
both image pairs after device work completes. Guest surface dimensions, D16
upload/readback conversion and translated code stay unchanged.

Depth-only starts preserve prior color by sampling it into the reduced target.
Content retained from an earlier frame therefore inherits world sampling until
redrawn. This is a diagnostic scale path, not a claim that every persistent HUD,
fade or guest-written overlay sequence is ready for temporal reconstruction.
The 100% default retains the original allocation and rendering path.

## Reproduce focused checks

Build the maintained host with the command in
[HOST_BUILD.md](../tools/m4-crt-heap-carry/HOST_BUILD.md), omitting `-Release` for
local edits. Refresh the canonical source manifest for intentional source changes.

In an x64 Visual Studio developer shell, with the pinned LLVM and Vulkan headers:

```powershell
clang-cl /nologo /DNOMINMAX /DWIN32_LEAN_AND_MEAN /D_CRT_SECURE_NO_WARNINGS /std:c++20 /EHsc /MD /Itools/m4-crt-heap-carry/host /I<Vulkan-Headers>/include tools/remaster-launcher/test_launcher_display.cpp /Fo<local-output>/display.obj /Fe<local-output>/display.exe /link user32.lib gdi32.lib /incremental:no
$env:MW34_REMASTER_WIDTH = '1280'
$env:MW34_REMASTER_HEIGHT = '960'
$env:MW34_REMASTER_AA = '1'
$env:MW34_REMASTER_AF = '1'
$env:MW34_SUN = '0'
$env:MW34_WORLD_SCALE_PERCENT = '50'
& <local-output>/display.exe --world-resolution
```

Repeat with 67 and 100, and with FXAA (`MW34_LAZY_RT=1`, `MW34_GPU_HUD=1`).
The existing display fixture now checks actual raster dimensions, sharp HUD edges,
interleaved world draws, close-surface depth occlusion after promotion, guest color
and depth readback, depth-only frame boundaries, and frontend target recreation.
Unsupported percentages and reduced mode with SSAA must fail visibly.

## Local native evidence, 2026-10-29

The development host was built from `5b046813c6ffbeac009f7c48c38cb18ccd968063`
plus this patch. Build receipt: seven authored host objects, zero translated object
inputs, `generation_required=false`, `translated_module_unchanged=true`.
Host SHA-256: `57fe7a2cda10950b5166216c08bfd9d46a4fc5110dcacebc939542910427efc5`.
Translated DLL SHA-256: `6d6e3c25fef68727113a6d52859253883dbb554958ddaa5a091187667aa8bfa5`.

On AMD Radeon RX 9070, driver 32.0.31035.1003, native menu -> Training completed
2,200 offscreen frames at 1920x1080, FXAA, 16x AF and the recorded replacement-pack
profile. At 50%, the renderer recorded 5,565 reduced scenes and 1,855 promotions.
Both 50% and 100% runs stopped at the configured presentation budget (the existing
harness reports this deliberate stop as exit code 1). Neither used the swapchain.

A separate 900-frame Instant Action -> MechLab -> briefing run entered the
640x480 logical frontend canvas at frame 281 and left it at frame 535. Its fitted
raster stayed 1440x1080 for 1920x1080 output, without the world percentage.

The 100% output was byte-identical to the previously built host at frames 1801 and
2101. The unchanged reference host SHA-256 is
`01b17fa52ba1f939d271a412c50c5353b2e1fcd885367549e25897dff67cb714`.
The foreground timer glyph masks matched between 50% and 100% at both captures;
the world pixels differed as expected. These are matched native host comparisons,
not comparisons with the original executable.

The mean host frame interval over frames 1200-2200 was 7.340 ms at 50% and
6.894 ms at 100% in these single runs. The additional transfers currently cost more
than this workload saves; no performance gain or displayed FPS is claimed.

Private receipts, isolated game copies and captures remain under
`D:/Projects/MW34-world-resolution/local/world-resolution/`. No original media,
generated game code, executable or game capture is included in this PR.

## Check results

- Maintained host build and canonical source pins: passed; translated DLL unchanged.
- CMake default build, all 25 CTest cases and `format-check`: passed.
- Style `--fix` and report: passed; all languages remain report-only, with existing
  repository findings. No bulk formatting was applied.
- Vulkan display fixture: default/unset, 100%, 67%, 50% and 50% with FXAA passed.
- Deliberately removing HUD promotion made the fixture fail with
  `HUD did not promote to output resolution`; restoring the source passed.
- Invalid percentages 49, 101 and nonnumeric input, and reduced SSAA: rejected.
- Existing D32 fixture: native, scaled, odd guest dimensions, 2x and 4x SSAA passed,
  including all 65,536 guest depth values and 64 close-surface positions.

## Remaining limits

This advances the live native rendering resource boundary, not gameplay coverage.
FSR remains disabled. Comprehensive overlay/persistent-pixel ordering, stock/no-pack
coverage, resize/minimize and visible swapchain validation, Vulkan validation-layer
coverage and a second physical PC remain open. The earlier visible surface-capability
failure is not resolved by these offscreen runs. Mixed world work after HUD stays
full resolution; P4 cannot assume the whole frame is one low-resolution world pass.
Independent review is required before this draft is ready. This is not a packaged,
signed, merged or published playtest release.
