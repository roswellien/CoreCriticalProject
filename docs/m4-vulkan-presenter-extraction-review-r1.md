# M4 Vulkan presenter extraction review r1

Recorded 2026-10-11. This is a read-only architecture review of the windowed
Vulkan replay's presentation code. It changes no C++, CMake, script, capture or
report, and does not run the viewer, the game, the active verifier or the
144-root gate. M4 initializer acceptance stays **131/144**, as supplied for this task. The
context-controls verifier and the original 138-root capture passed. Strict
validation is still pending. This review adds no initializer, startup or
rendering credit.

**Observation** labels describe code as it exists today, with file and line
references. **Recommendation** labels are proposals for later work. **Unknown**
labels depend on evidence not yet available, mostly from the separate
DirectDraw/COM analysis. That analysis was not duplicated here. No binary analysis was needed:
REA was registered for this Claude Code client and its doctor reported
`claude_code` + Ghidra healthy. However, no REA target or Ghidra session was opened.

## Sources reviewed

| Source | Role |
| --- | --- |
| [viewer.cpp](../tools/vulkan-windowed/viewer.cpp) | Executable entry, Vulkan instance/device, scene resources, raster command buffer |
| [presenter.hpp](../tools/vulkan-windowed/presenter.hpp) | `NativeWindow` and `SwapchainPresenter` |
| [replay_scene.hpp](../tools/vulkan-probe/replay_scene.hpp), [ordered_commands.inc](../tools/vulkan-probe/ordered_commands.inc) | SCN1–SCN4 package parser and ordered draw/clear/copy executor shared with the offscreen probe |
| [CMakeLists.txt](../tools/vulkan-windowed/CMakeLists.txt), [run.ps1](../tools/vulkan-windowed/run.ps1), [Launch Vulkan Replay.cmd](../Launch%20Vulkan%20Replay.cmd), [README](../tools/vulkan-windowed/README.md) | Build, launch, input hashing and receipts |
| [verify.py](../tools/vulkan-windowed/verify.py), [verify_ordered.py](../tools/vulkan-windowed/verify_ordered.py) | Independent receipt and pixel-oracle verification |
| [Windowed replay acceptance record](vulkan-windowed-replay.md) | Accepted tests and scope |
| [Native build path r1](m4-native-vulkan-build-path-r1.md), [video backend contract r1](m4-video-backend-contract-r1.md), [graphics boundary](../runtime/graphics/README.md) | Existing integration direction and DirectDraw static evidence (read, not re-derived) |

Acceptance receipts referenced by the replay record, all inspected read-only:

| Receipt | Recorded result |
| --- | --- |
| [Self-test, 589 draws](../reports/vulkan-windowed/20261009-205010-187-690216e1/presentation-verification.json) | 757 presentations; generations 640×480, 853×480 (×2), 640×480; content rectangle `[106, 0, 640, 480]` at 853×480; both negative controls rejected; 667 input hashes |
| [Default launch](../reports/vulkan-windowed/20261009-204941-725-46144d7f/presentation-verification.json) | 274 presentations; one 960×720 generation |
| [Alternate capture, 140 draws](../reports/vulkan-windowed/20261009-205019-629-a759c4f7/presentation-verification.json) | 274 presentations; one 960×720 generation; 184 input hashes |
| [Ordered clear/copy](../reports/vulkan-windowed/ordered-commands-20261010/verification.json) | 740 presentations; 4 generations; 64 exact raster pixels; 4 witnesses |
| [589-draw regression after ordered commands](../reports/vulkan-windowed/20261010-054054-018-4da93ce7/presentation-verification.json) | 732 presentations; 4 generations; 668 input hashes |
| `reports/vulkan-windowed/20261009-205229-796-4990e7cd/` | Interactive launcher witness |

## Current ownership

**Observation.** A presenter class already exists, but it is not a reusable
boundary. It owns the event loop, test script and receipt side effects.
Device creation, scene upload and the raster live in one `main`.

| Concern | Current owner | Evidence |
| --- | --- | --- |
| Win32 window class, `WndProc`, message pump, client size | `NativeWindow` | [presenter.hpp:3-95](../tools/vulkan-windowed/presenter.hpp#L3) |
| Window events → presenter state | `NativeWindow` flags `resized`, `minimized`, `quit`, plus test flags `minimizeSeen`, `restoreSeen`, `escapeSeen` | [presenter.hpp:5-6](../tools/vulkan-windowed/presenter.hpp#L5), [15-42](../tools/vulkan-windowed/presenter.hpp#L15) |
| Main loop, time-based close and scripted resize/minimize/restore self-test | `SwapchainPresenter::run` | [presenter.hpp:364-400](../tools/vulkan-windowed/presenter.hpp#L364), assertions at [518-520](../tools/vulkan-windowed/presenter.hpp#L518) |
| Vulkan loader, instance, **required** validation layer and synchronization validation, debug messenger | `main` | [viewer.cpp:85-174](../tools/vulkan-windowed/viewer.cpp#L85), global counter [26-34](../tools/vulkan-windowed/viewer.cpp#L26) |
| Win32 `VkSurfaceKHR` | `main`, from `NativeWindow::handle` | [viewer.cpp:180-185](../tools/vulkan-windowed/viewer.cpp#L180) |
| GPU/queue selection (graphics + present, swapchain + maintenance1) and device | `main` | [viewer.cpp:186-269](../tools/vulkan-windowed/viewer.cpp#L186) |
| Swapchain, per-image present semaphores and fences, recreation, FIFO, format choice | `SwapchainPresenter` | [presenter.hpp:147-276](../tools/vulkan-windowed/presenter.hpp#L147) |
| Aspect-fit letterbox (clear black, nearest blit) and present | `SwapchainPresenter::run` | [presenter.hpp:443-511](../tools/vulkan-windowed/presenter.hpp#L443) |
| Capture parsing (SCN1–SCN4 limits and ordered commands) | `readScene` | [replay_scene.hpp](../tools/vulkan-probe/replay_scene.hpp) |
| Scene resources: textures, vertex buffer, initial color/depth, samplers, descriptors, render pass, 8 pipelines | `main` | [viewer.cpp:419-679](../tools/vulkan-windowed/viewer.cpp#L419) |
| Raster: one command buffer recorded once and resubmitted for every presentation | `main` + `ordered_commands.inc` | [viewer.cpp:680-800](../tools/vulkan-windowed/viewer.cpp#L680), redraw [827-833](../tools/vulkan-windowed/viewer.cpp#L827) |
| Raster readback → `replay.ppm` | `main` | [viewer.cpp:774-821](../tools/vulkan-windowed/viewer.cpp#L774) |
| Presented-image readback → `<output>.presented-N.ppm`, `SWAPCHAIN:` log lines | `SwapchainPresenter` | [presenter.hpp:247-298](../tools/vulkan-windowed/presenter.hpp#L247), [273-275](../tools/vulkan-windowed/presenter.hpp#L273) |
| `WINDOWED_RESULT:` receipt line | `main` | [viewer.cpp:842-858](../tools/vulkan-windowed/viewer.cpp#L842) |
| Input hash pinning, environment, `report.json` | `run.ps1` | [run.ps1](../tools/vulkan-windowed/run.ps1) |
| CPU aspect-fit/nearest oracle, accounting checks, negative controls | `verify.py` | [verify.py](../tools/vulkan-windowed/verify.py) |

Further observations:

- `presenter.hpp` is not self-contained. It depends on `check`, `<windows.h>`
  with `VK_NO_PROTOTYPES`, `<functional>`, `<chrono>` and `<fstream>` being
  defined or included by `viewer.cpp` before
  [viewer.cpp:60](../tools/vulkan-windowed/viewer.cpp#L60).
- The presenter only borrows the instance, physical device, device, queue and
  surface ([presenter.hpp:301-307](../tools/vulkan-windowed/presenter.hpp#L301)).
  It owns its own command pool, acquire semaphore, copy fence, swapchain
  objects and readback buffer.
- The source image contract is implicit. The presenter blits from `source` in
  `TRANSFER_SRC_OPTIMAL` and validates blit support only for
  `VK_FORMAT_R8G8B8A8_UNORM`
  ([presenter.hpp:203-208](../tools/vulkan-windowed/presenter.hpp#L203)).
  It records no barrier for `source`. Correctness relies on the raster command
  buffer ending with a color-write → transfer-read transition
  ([viewer.cpp:774-777](../tools/vulkan-windowed/viewer.cpp#L774)), and on
  `redraw` waiting for its fence on the host before the presenter records
  ([viewer.cpp:828-831](../tools/vulkan-windowed/viewer.cpp#L828)).
- `redraw()` runs after a successful acquire and the image's present-fence wait
  ([presenter.hpp:411-426](../tools/vulkan-windowed/presenter.hpp#L411)).
  Acquire timeout and out-of-date paths `continue` before the redraw. That
  ordering produces the verifier identity `render_passes == presented_frames + 1`
  ([verify.py](../tools/vulkan-windowed/verify.py), `verify()`).
- Each frame serializes fully on the host. The copy fence is waited before the
  redraw and again after present
  ([presenter.hpp:424](../tools/vulkan-windowed/presenter.hpp#L424),
  [512](../tools/vulkan-windowed/presenter.hpp#L512)). That host serialization
  is what makes one shared `available` acquire semaphore safe.
- Swapchain recreation is event-driven, not extent-driven. Any `WM_SIZE`,
  including a restore at an unchanged size, sets `resized`
  ([presenter.hpp:15-24](../tools/vulkan-windowed/presenter.hpp#L15)). The
  accepted self-test therefore records **four** generations, two of them at
  853×480. `verify_ordered.py` requires at least four witnesses.
- The first presented image of each generation is copied to a host buffer and
  written as a PPM
  ([presenter.hpp:469-480](../tools/vulkan-windowed/presenter.hpp#L469),
  [513-514](../tools/vulkan-windowed/presenter.hpp#L513)). `verify.py` depends
  on the file name pattern and on the `SWAPCHAIN:` lines.
- Raster settings are constants with inherited dead branches:
  `colorMode = "rgba8"`, `depthMode = "d32"`, `scale = 1`, plus unreachable
  `rgb565`/`d16` conversions
  ([viewer.cpp:78-82](../tools/vulkan-windowed/viewer.cpp#L78),
  [439-463](../tools/vulkan-windowed/viewer.cpp#L439)). The non-Win32 `dlopen`
  branch is unreachable because
  [CMakeLists.txt](../tools/vulkan-windowed/CMakeLists.txt) rejects non-Win32
  builds.
- The viewer is a standalone CMake project, not part of the root build or
  `ctest`. MSVC uses `/W4 /WX`. `tools/vulkan-windowed/` is currently
  **untracked** in git, and so are `ordered_commands.inc` and
  `verify_ordered_commands.py`.
- **Receipt reproducibility.** `verify.py` rehashes every pinned input against
  the current files. A read-only hash comparison on 2026-10-11 found the
  following:
  - The three 2026-10-09 receipts differ from current `viewer.cpp`,
    `replay_scene.hpp`, `run.ps1`, `package_replay.py` and `verify_capture.py`.
  - The 2026-10-10 regression receipt differs on `run.ps1`,
    `package_replay.py` and `verify_capture.py`.
  - Only the ordered-command receipt matches every pinned file.
  - `presenter.hpp` is unchanged since all receipts.

  Re-verifying old receipts cannot guard a refactor. Only fresh runs can.

## Proposed presenter interface

**Recommendation.** Extract the narrowest boundary that the current replay can
call without any change in observable behavior. Add an owned-pixel path in a
separate component, so the replay never depends on it. Names are proposals.

```cpp
namespace mw34::present {

// Borrowed; created and destroyed by the host. Outlives the presenter.
struct VulkanDeviceContext {
    VkInstance instance;
    VkPhysicalDevice gpu;
    VkDevice device;
    VkQueue queue;              // graphics + present family
    uint32_t queueFamily;
    PFN_vkGetInstanceProcAddr getInstanceProc;
    PFN_vkGetDeviceProcAddr getDeviceProc;
};

// Supplied per call by whoever owns the HWND; the presenter never pumps messages.
struct PresentTarget {
    VkSurfaceKHR surface;       // borrowed
    VkExtent2D clientExtent;    // 0 x 0 => Skipped
    bool minimized;             // true => Skipped
    bool resizeEvent;           // any WM_SIZE since last call => recreate (today's semantics)
};

// Stage-1 source contract, exactly what the replay already provides.
struct GpuSource {
    VkImage image;              // TRANSFER_SRC_OPTIMAL; writes complete and visible to transfer reads
    VkFormat format;            // VK_FORMAT_R8G8B8A8_UNORM today
    VkExtent2D extent;          // fixed per presenter today
};

enum class FrameStatus { Presented, Skipped };

// Replaces stdout/PPM side effects inside the presenter; the replay's observer
// keeps writing the identical SWAPCHAIN lines and .presented-N.ppm witnesses.
struct PresentObserver {
    virtual ~PresentObserver() = default;
    virtual void swapchainCreated(uint64_t generation, VkExtent2D, uint32_t images, VkFormat) = 0;
    virtual void firstImageOfGeneration(uint64_t generation, VkExtent2D, VkFormat,
                                        std::span<const std::uint8_t> pixels) = 0;
};

class SwapchainPresenter {
public:
    SwapchainPresenter(const VulkanDeviceContext&, VkExtent2D sourceExtent, PresentObserver*);
    // Acquire; on success call produce() exactly once, then letterbox-blit source and present.
    FrameStatus presentFrame(const PresentTarget&, const GpuSource&,
                             const std::function<void()>& produce);
    void close();               // idle, wait every pending present fence, release; idempotent
    PresentationStats stats() const;
};

// Owned-pixel path (new, separate component; the replay does not use it).
enum class PixelFormat { R8G8B8A8, B8G8R8A8, R5G6B5 /* others only after DirectDraw evidence */ };
struct PixelSurfaceView {       // borrowed bytes, read only during the call
    const std::byte* base;
    uint32_t width, height;
    int32_t pitchBytes;         // signed until the DirectDraw analysis settles it
    PixelFormat format;
};
class HostSurfaceUploader {     // presenter-side staging buffer + device image
public:
    HostSurfaceUploader(const VulkanDeviceContext&, VkExtent2D, PixelFormat);
    GpuSource source() const;
    void upload(const PixelSurfaceView&);   // copy/convert now; barriers end in TRANSFER_SRC_OPTIMAL
};

} // namespace mw34::present
```

Why this boundary keeps replay behavior unchanged:

- **Call ordering.** The `produce` callback keeps the scene redraw after a
  successful acquire. `render_passes == presented_frames + 1` therefore still
  holds when acquires time out.
- **Recreation.** `resizeEvent` keeps event-driven recreation, so the self-test
  still produces four generations and four witnesses.
- **Teardown accounting.** `close()` keeps the existing guarantee that every
  presented image's fence is waited once (`present_fence_waits == presented_frames`).
- **Test policy.** The 640 × 480 → 853 × 480 → minimize → restore → 640 × 480
  script, the timed close and the Escape handling move into the viewer's own
  loop, together with `NativeWindow`. They are application and test policy,
  not presentation.
- **Owned-pixel path.** A later compatibility layer calls
  `uploader.upload(view)` inside `produce`, then presents
  `uploader.source()`. The presenter snapshots the bytes during the call, so
  the guest can relock its surface immediately afterwards.

## Ownership split

**Recommendation.**

Must remain presenter-owned (host only; never exposed to guest code):

- The swapchain, its images, extent, format/color-space choice, present mode
  and generation counter.
- The acquire semaphore, the per-image render-finished semaphores, and the
  `VK_KHR/EXT_swapchain_maintenance1` present fences. Also the pending flags
  and the rule that fences are waited before reuse, recreation and destruction.
- The presentation command pool/buffer and copy fence.
- All layout transitions of swapchain images, including the transfer-stage
  wait on the acquire semaphore.
- Letterbox policy: the black clear, the integer aspect-fit rectangle and the
  nearest filter. This is the policy that `verify.py`'s oracle encodes.
- Upload staging memory, the device-local source image and their barriers and
  fences. The guest never holds a `VkImage`, mapped Vulkan memory or a fence.
- Readback and witness capture, delivered through the observer.

Can be supplied later by a DirectDraw compatibility layer:

- Surface width, height, pitch, the pixel format and channel masks, the pixel
  bytes (copied, not retained), and an optional dirty rectangle.
- For 8-bpp modes, palette entries applied at upload time.
- The presentation trigger: a Flip, a Blt to primary, or an observed callback.
  Also any source rectangle the game requests.
- Guest-facing status semantics stay entirely in the compatibility layer. That
  covers `DDERR_SURFACELOST` 0x887601C2 and restore/retry, the busy retry on
  0x8876021C, GetFlipStatus/GetBltStatus normalization and error-helper effects
  ([video contract](m4-video-backend-contract-r1.md)). The presenter reports
  only host outcomes (`Presented`, `Skipped`, or a thrown Vulkan error).
- Window ownership: the HWND and its messages belong to the host or the
  compatibility layer. The presenter receives a `VkSurfaceKHR` plus per-call
  extent and state.

## Staged extraction plan

**Recommendation.** Each stage is one reviewable change and leaves the replay
behaviorally identical.

| Stage | Change | Regression guards |
| --- | --- | --- |
| 0. Baseline | Track `tools/vulkan-windowed/`, `ordered_commands.inc` and `verify_ordered_commands.py` in git. Rebuild the default `build/vulkan-windowed` (the record says it predates ordered commands). Make fresh baseline runs with current hashes. | `run.ps1 -AutoCloseSeconds 6 -SelfTest`, `run.ps1 -AutoCloseSeconds 2`, `run.ps1 -AutoCloseSeconds 2 -CaptureRun reports/graphics-trace/20261009-061307-498`, each followed by `verify.py`; `verify_ordered.py <build> <fresh-dir>` |
| 1. Self-contained header | Move `check`, the validation counter and the required includes into a small shared header. Keep the `presenter.hpp` and `viewer.cpp` names, because `verify.py` requires both in the pin manifest. Add any new file to the `run.ps1` and `verify_ordered.py` pin lists in the same change. | Build with `/W4 /WX`; all stage-0 runs |
| 2. Invert the loop | Move `NativeWindow`, the self-test script and the timed close into the viewer. Add `presentFrame` with `produce`, `PresentTarget.resizeEvent` and the observer. The viewer's observer prints the same `SWAPCHAIN:` lines and writes the same `.presented-N.ppm` files. | `replay.ppm` equal to `preview/vulkan-0.5.ppm`; every witness pixel-exact; self-test generations `= 4`; `render_passes == frames + 1`; `present_fence_waits == frames`; zero validation messages including teardown; Escape/close/minimize/restore flags true |
| 3. Device context | Factor instance/device creation into a `VulkanDeviceContext` factory. Validation stays required for the replay (an option, default on). Selection criteria are unchanged. | Same as stage 2; run log still names `VK_KHR_swapchain_maintenance1` and the same device |
| 4. Owned-pixel fixture | Add `HostSurfaceUploader` and a **new** executable and CPU oracle in a separate directory, with `verify.py`-style receipts. Cover RGBA8/BGRA8 first, then 16-bit 565 per the existing static evidence. Include padded pitch, odd and 1-pixel sizes, resize, minimize/restore and teardown. The viewer does not link it. | New oracle plus negative controls (scene pixel, border pixel, pitch-padding byte); stage-2 replay suite unchanged |
| 5. Compatibility hookup | After the DirectDraw analysis is admitted, connect the guest lock/unlock/flip path to `upload`/`presentFrame` in the M4 host target, as in the [build path](m4-native-vulkan-build-path-r1.md). | Stage-4 fixture; synthetic guest-surface round trips; no startup credit without the separate 144-root gate |

Throughout:

- Do not edit or re-verify historical receipts in place. `verify.py` refuses
  to overwrite a differing `presentation-verification.json`, and old pins no
  longer match current sources.
- Use a fresh `-BuildDirectory` when the default viewer executable is locked
  by an open window.

## Unknowns and design choices

These depend on the separate DirectDraw analysis:

1. **Pixel formats.** Which bpp and masks are actually selected (global `0x802718`;
   16-bit RGB with 4:4:4:4 and 1:5:5:5 texture variants in static evidence).
   Whether 8-bpp palettes reach presentation. These decide whether the
   uploader converts on the CPU to RGBA8 (simplest exact oracle) or uploads
   packed 16-bit images. A packed upload needs blit-source support checks the
   presenter does not perform today.
2. **Pitch.** The sign, padding and memory extent of locked surfaces, and the
   observed constrained row-copy path in `0x57B6C0`.
3. **Presentation trigger.** Whether Flip or Blt is used (`0x8026E0`). Whether
   one guest flip should map to exactly one `presentFrame`, and how
   GetFlipStatus timing relates to FIFO pacing and present fences.
4. **Window mode.** The original requests exclusive fullscreen and
   SetDisplayMode. Presenting into a resizable window is a deliberate
   behavior change and needs a decision. That includes whether the
   compatibility layer or the host creates the HWND, and how cooperative-level
   calls are answered.
5. **GDI composition.** The DIB/memory-DC callbacks write into surface memory.
   It is unknown whether composited GDI content must be visible in the
   uploaded bytes at present time, and whether partial or dirty-rectangle
   uploads are safe.
6. **Surface loss.** How guest-visible surface loss is mapped from host events
   such as minimize or display change. The presenter's skip-while-minimized
   policy must not silently change guest return codes.
7. **Direct3D surfaces.** Whether Direct3D-rendered surfaces (texture/device paths) must reach the presenter as
   GPU images rather than CPU bytes. That would use the `GpuSource` path
   directly and need an explicit cross-component synchronization contract
   instead of today's host fence wait.

Presenter-internal questions, independent of DirectDraw:

1. **Present-fence semantics.** Is an image's present fence guaranteed to
   signal when `vkQueuePresentKHR` returns `VK_ERROR_OUT_OF_DATE_KHR`? The
   code marks the fence pending in that case
   ([presenter.hpp:506-510](../tools/vulkan-windowed/presenter.hpp#L506)).
   This should be confirmed against the swapchain maintenance1 specification
   before the presenter is reused in a long-running host.
2. **Pipelining.** Do later hosts need frames in flight? Today's design
   serializes each frame on the host. Pipelining requires per-frame acquire
   semaphores and a source-image fence or semaphore handoff.
3. **Validation policy.** Should a game host make the validation layer
   optional while the replay keeps it required? Instance creation currently
   fails without it ([viewer.cpp:160](../tools/vulkan-windowed/viewer.cpp#L160)).
