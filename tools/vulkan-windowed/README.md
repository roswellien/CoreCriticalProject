# Windowed Vulkan replay

Double-click [Launch Vulkan Replay.cmd](../../Launch%20Vulkan%20Replay.cmd) at
the repository root. The viewer opens at 960 × 720 and redraws a saved MW3
Training scene through the project-built x64 Vulkan renderer. Resize the
window normally; the scene keeps its aspect ratio with black borders. Press
**Escape**, or use the window's close button, to quit.

This is a fixed captured viewpoint, with no movement or game controls. The
renderer executes the saved draw sequence on every presentation. The capture
contains one BeginScene/EndScene interval and retained initial color/depth;
whole-frame capture and live native gameplay remain separate work.

The launcher verifies captured resources and filtering evidence, creates a
fresh run under `reports/vulkan-windowed/`, enables Vulkan and synchronization
validation, and logs to `run.txt`. After closing it, `report.json` records the
window lifecycle and `presentation-verification.json` checks GPU image
readbacks against an independent aspect-fit/pixel oracle. Execution policy is
set for this launcher process only.

Requirements: the local captures, Python 3.14 at `C:/Python314/python.exe`, the
portable validation layer under `local/tools/vulkan-sdk-portable/Bin`, and a
Vulkan driver with Win32 presentation and KHR/EXT swapchain maintenance1.
The tested driver exposes the KHR version; extension selection is automatic.
No original-game process is started or modified.

Build in its separate directory from PowerShell, using CMake on PATH:

```powershell
cmake -S tools/vulkan-windowed -B build/vulkan-windowed -A x64 -DVULKAN_HEADERS="$PWD/local/tools/vulkan-headers-v1.4.321/include" -DGLSLANG_VALIDATOR="$PWD/local/tools/vulkan-sdk-portable/Bin/glslangValidator.exe"
cmake --build build/vulkan-windowed --config Release
```

The new build uses the original raster shaders and scene reader without
changing the offscreen prototype. MSVC builds with `/W4 /WX`.

Run the six-second resize/minimize/restore/Escape test, or a normal timed close:

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File tools/vulkan-windowed/run.ps1 -AutoCloseSeconds 6 -SelfTest
powershell.exe -NoProfile -ExecutionPolicy Bypass -File tools/vulkan-windowed/run.ps1 -AutoCloseSeconds 2
```

The alternate admitted capture can be selected with
`-CaptureRun reports/graphics-trace/20261009-061307-498`.
See [the implementation and acceptance record](../../docs/vulkan-windowed-replay.md).
