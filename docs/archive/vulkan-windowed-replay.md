# Windowed Vulkan replay

Implemented and tested 2026-10-09. The [launcher](../../launchers/Launch%20Vulkan%20Replay.cmd)
opens an independent x64 Win32 Vulkan viewer of the previously captured
Training scene. It redraws the saved sequence for each presentation, preserves
the aspect ratio when resized, pauses drawing while minimized, restores the
swapchain, and closes through Escape or the ordinary window close path.

The primary capture is `reports/graphics-trace/20261009-055506-103`: 589 draws,
51 captured textures plus a white fallback, captured linear filtering, 640 ×
480, RGBA8/D32, pixel offset 0.5. The original offscreen raster source, shaders,
capture payloads and historical receipts remain unchanged. The additive viewer
is in `tools/vulkan-windowed/`, with build output in `build/vulkan-windowed/`.

Presentation uses a FIFO swapchain, GPU blit and centered black borders. Each
swapchain image has its own render-finished semaphore and presentation fence.
Extension selection supports the promoted KHR variant or its EXT predecessor;
the AMD RX 9070 tested here exposes `VK_KHR_swapchain_maintenance1`.
Presentation fences cover reuse and destruction, following the
[Khronos semaphore guidance](https://docs.vulkan.org/guide/latest/swapchain_semaphore_reuse.html)
and [presentation-fence contract](https://docs.vulkan.org/refpages/latest/refpages/source/VkSwapchainPresentFenceInfoKHR.html).
The acquired-image layout transition uses the transfer stage on both sides
so it participates in the semaphore wait's execution dependency.

The final tests used Windows PowerShell 5.1, the same host as the root launcher:

| Test | Result | Acceptance receipt |
| --- | --- | --- |
| Six-second lifecycle test: 640 × 480 → 853 × 480, minimize/restore, return to 640 × 480, Escape | 757 presentations; 758 raster passes; four swapchain generations; all presentation fences waited; zero validation messages including teardown | [Self-test](../../reports/vulkan-windowed/20261009-205010-187-690216e1/presentation-verification.json) |
| Default 960 × 720, ordinary timed close | 274 presentations; exact scaled image; zero validation messages | [Default launch](../../reports/vulkan-windowed/20261009-204941-725-46144d7f/presentation-verification.json) |
| Alternate delayed laser capture, 140 draws, default window and close | 274 presentations; exact scaled image; zero validation messages | [Alternate capture](../../reports/vulkan-windowed/20261009-205019-629-a759c4f7/presentation-verification.json) |

Each run records the executable, shaders, source, validation layer, capture
metadata and resource hashes before execution, then rechecks them after close.
The independent verifier checks runtime counts, window lifecycle, package
identity and scope. The primary tests physically checked 667 input hashes.
GPU readbacks of the first presented image in each swapchain generation match
the CPU aspect-fit/nearest-pixel oracle exactly, including both black borders
in the 853 × 480 window. The native raster output also matches the earlier
accepted offscreen Vulkan replay byte for byte. Scene-pixel and border-pixel
corruption controls are rejected. This verifies the GPU image submitted for
presentation, rather than claiming an independent photograph of the display.

Earlier failed runs are preserved. One required the promoted KHR extension
name, another exposed an acquire/layout-transition synchronization hazard,
and the first PowerShell 5.1 check exposed UTF-16 log encoding. The implemented
fixes passed the fresh runs above; failed runs add no acceptance credit.
The final double-click launcher also exposed an unavailable `Get-FileHash`
cmdlet in its child environment. Hashing now uses .NET SHA-256 directly, and
the launcher names the Windows PowerShell executable explicitly. The resulting
interactive launch produced a visible, responding 960 × 720 window and its
GPU image witness in
`reports/vulkan-windowed/20261009-205229-796-4990e7cd/`.

Scope: the view stays fixed because this input is one saved scene interval.
Initial color and depth include earlier original-renderer work. It is not a
complete flip-to-flip frame, native menus or playable Training. This step adds
no initializer credit. The accepted startup inventory is **130/144**, as
recorded in the [current startup acceptance](../../reports/m4-joint-startup130-root/acceptance-r1/report.json).
The [existing live-replay fidelity comparison](vulkan-live-replay.md) remains
separate from exact presentation transport checks here.

The next rendering step is to capture and replay every scene interval and
clear in one complete presented frame, then a short sequence of those frames.
Live runtime integration additionally requires the recovered game logic and
its native input, timing and asset paths.

## Ordered clear/copy support (2026-10-10)

The windowed viewer now uses the shared SCN4 ordered-command executor described
in [the replay notes](vulkan-live-replay.md). An authored copy followed by a
combined clear and depth-tested geometry matched the independent CPU oracle
exactly. Four GPU presentation witnesses also matched across resize and
minimize/restore; 740 presentations completed with zero validation messages,
normal Escape close and resource teardown. Receipt:
`reports/vulkan-windowed/ordered-commands-20261010/verification.json`.
Reproduce with `tools/vulkan-windowed/verify_ordered.py`, supplying a build
directory and a fresh report directory.

The earlier 589-draw package also passed the windowed regression and independent
presentation verifier in `reports/vulkan-windowed/20261010-054054-018-4da93ce7`.
Both checks used `build/vulkan-windowed-commands` because the default viewer
executable was open and locked. `run.ps1 -BuildDirectory` selects this alternate
build without interrupting the existing viewer. The default launcher executable
has not yet been rebuilt with these commands.
