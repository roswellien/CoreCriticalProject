# MW3 Vulkan wrapper plan using D7VK

Written 2026-10-12 at the user's request. Scope: an original-game x32 wrapper
lane alongside ongoing native recompilation work.

Build an MW3-specific **32-bit DirectDraw/Direct3D wrapper based on D7VK** that
runs the user's original MW3 U.S. retail 1.2 executable and renders its live
graphics through Vulkan. Start by validating the existing x32 release; modify
the pinned source only for measured MW3 compatibility defects. Retain the
original engine and simulation. No new gameplay engine is required.

This is a useful original-game compatibility deliverable and a renderer
development lane alongside the [faithful recompilation strategy](faithful-modernization-plan.md).
It does not replace that strategy, supply an original-code fallback for the
production native host, or complete its E1/E2/E3 milestones. Wrapper progress
does not change the last verified selected-startup count of 131/144.

## Architecture and scope

```text
Original 32-bit Mech3.exe
    -> app-local x32 ddraw.dll built from D7VK
        -> DirectDraw4 and IDirect3D3/IDirect3DDevice3 adapters
        -> D7VK's matching modified D3D9 implementation
        -> DXVK Vulkan backend -> display

    D7VK surface/provider operations
        -> explicitly identified native Windows DirectDraw provider
        -> surface storage, locks, fills, GDI and legacy display services
```

The DirectDraw provider is a real dependency: D7VK does not implement all
DirectDraw itself. Its current loader tries `ddraw_.dll`, then system
`ddraw.dll`. For the first experiment use native Windows DirectDraw and verify
the loaded path, architecture and hash. Do not rename dgVoodoo to `ddraw_.dll`
and assume stacking works. Any alternative provider chain needs its own
identified defect, architecture explanation and isolated comparison.

The observed interface3 path lives in D7VK's `src/ddraw/d3d6/`; the `d3d3/`
directory handles older interfaces/execute buffers. Keep the DDRAW frontend and
its matching backend together: its private legacy D3D9 bridge is not supplied
by an arbitrary stock D3D9 library. No separate stock DXVK DLL is needed for
the tested v2.3 package.

Initial scope is Windows x32 compatibility at the existing game-controlled
resolution, visual settings and provisional 30 FPS presentation cap. Preserve
input, audio, original game files and gameplay behavior. Enhanced filtering,
resolution/aspect/FOV changes, interpolation and timing patches are separate
options after their affected baseline is measured. Linux and the x64 recomp
adapter are later integration work.

## Starting evidence and pins

Use the [D7VK evaluation](d7vk-evaluation-r1.md),
[graphics trace](mw3-live-graphics-trace.md),
[surface-command investigation](live-native-rendering-current-work.md) and
[video contract](m4-video-backend-contract-r1.md). Do not regenerate existing
captures merely to prove they exist.

| Input | Pin / established scope |
| --- | --- |
| MW3 U.S. retail 1.2 executable | SHA256 `95bc2c114c9b2e5c5ada8e40ca78cc79470f862e45313ffad0d1e8e6d4d916bf`; use original user-supplied bytes |
| D7VK source v2.3 | Commit `ff123cb08ff1fcf6575a6ef8fb79d824a84e56c4` |
| Official v2.3 archive | SHA256 `ed7eec7d622d81c3606e3a7e705de955da65aba9d16ea812aa88711980b1bb66` |
| Released x32 DDRAW DLL | SHA256 `00211f2f9f8589845940973ad8195f08f5f724510a2b800566e31f7c170e9f34` |
| Authored graphics fixture | Passed six scene intervals and eleven sampled RGB565 pixel checks on AMD RX 9070; no game or presentation proof |
| Existing original-game baseline | dgVoodoo reference setup; user reported improvement with 30 FPS ceiling; not a measured physics/timestep diagnosis |

The fixture checks transformed 32-byte triangle fans (`FVF=0x1C4`, flags
`0x18`), texture mutation, full/partial D16 zero fills, and CPU/GDI writes
surviving later draws. It does not establish primary/backbuffer presentation,
menu transitions, videos, color keys, fog, blending, mipmaps or all game calls.

## Execution order

| Stage | Executed boundary advanced | Deliverable and exit criterion |
| --- | --- | --- |
| W0: isolated setup | None; configuration/input preparation | Reversible private test profile, verified inputs/provider policy, original launch path preserved |
| W1: existing x32 D7VK with MW3 | Original game -> actual wrapper/provider -> Vulkan menu | Real interactive menu and normal quit; actual module identities and Vulkan device recorded |
| W2: first Training path | Original load/update/render -> live Vulkan scene | Training movement/turning/firing/HUD, return to menu and quit; no unexplained required graphics failure |
| W3: reproducible source build | Same original-game graphics boundary, now project-built provider | Pinned x32 DDRAW/D3D9 build passes fixture and W1/W2; retained toolchain/flags/notice inventory |
| W4: MW3 compatibility corrections | Specific failing graphics/resource operation | Small source patch, regression for the observed defect, and original-game comparison at that boundary |
| W5: wrapper compatibility baseline | Sustained original-game Vulkan execution | Repeatable scenes/transitions, error/lifetime checks and tested launch/restore procedure |
| W6: timing and enhancement experiments | Only the named setting or recovered game timing boundary | Separate baseline, explicit option and behavior regression; no renderer pass counted as a physics fix |
| R: reuse in native recomp | Translated producers -> x64 host graphics service | Separate x64 source build, guest ABI/COM adapters and live native integration under E1-E4 criteria |

W1/W2 come before a custom source build so we learn which MW3 problems actually
need development. An x64 build is not a prerequisite for this x32 wrapper lane.
Stage R can use its findings later without blocking the original-game experiment.

### W0: prepare the test profile

1. Inspect process command lines and current graphics/asset writers. Do not
   touch active composer/watcher, SQLite, loaded wrapper binaries, ongoing
   translations or another game session. Use new local/build directories.
2. Create a private test installation/profile from the user's existing local
   data under ignored `local/work-ahead/mw3-d7vk-wrapper/`. Keep the existing
   MW3 installation and dgVoodoo launchers intact. Do not download media.
3. Record executable, wrapper and configuration identities. Inventory the
   private directory's DLLs and actual import resolution, including the
   existing `D3DImm.dll`; do not accidentally retain the dgVoodoo pair. Remove
   incompatible wrapper components only from the private copy, keeping its
   original manifest for restoration. Never replace system DLLs.
4. Identify save/configuration paths and registry accesses that may still be
   shared despite the private folder. Preserve affected state and use a
   disposable test save. Folder isolation alone does not prove state isolation.
5. Select the existing logical resolution and cap presentation at 30 FPS via
   D7VK's supported setting (`d3d9.maxFrameRate=30`). Record effective VSync,
   refresh rate, mode and driver. This is a reference ceiling, not a claim that
   MW3's simulation tick is 30 Hz.
6. Record D7VK's MW3 options `ddraw.forceLegacyPresent=True` and
   `ddraw.emulateFrontBuffer=True`. Verify they were selected rather than infer
   activation from the filename alone. Avoid forced AA, upscaling, filtering,
   camera changes and timing hooks for the initial comparison.

W0 output is a small launch/profile manifest and a restoration procedure,
not another acceptance framework. Logs and user-derived data stay local.

### W1/W2: test the original game through Vulkan

Use the pinned x32 release and the native DirectDraw provider first. The original
unwrapped game previously failed video initialization; that does not prove
D7VK's different device path will fail or succeed. Capture the exact first
failure if it occurs, including HRESULT, interface/method, descriptor and
provider identity. Do not force success to pass startup.

Confirm loaded module paths/hashes while the actual process is running, and
Vulkan adapter/backend identity from the same session. A present `ddraw.dll`
file, title screen screenshot or successful shader compile is insufficient.

Progress through interactive menu, Training load, stationary view, movement,
turning, firing, HUD updates, menu return and normal quit. Include the prior
cliff/terrain route where practical. Record user-observed behavior separately
from call/log checks. Compare at the same logical resolution, camera/scenario
and cap with the retained dgVoodoo reference profile. That profile is a
comparison environment, not an unquestionable original-driver pixel oracle.

First inspect existing logs/captures. Add narrow observations only when needed
to identify a failing operation. Preserve order across draws, partial depth
clears, Lock/Unlock, GDI and presentation. Never reconstruct a displayed frame
by seeding it from a reference screenshot.

### W3/W4: build and adapt D7VK

Use an unmodified pinned source build first: Win32 release, DDRAW/D3D9 enabled,
DXGI/D3D8/D3D10/D3D11 disabled. Pin the compiler, Meson, resource compiler,
glslang and all required submodules from the evaluation. Use a local toolchain
and bounded build concurrency while other jobs are active. Preserve failed
build logs. Run the existing fixture against the actual source-built DLL, then
repeat only affected original-game checks. Do not claim bit-for-bit agreement
with the upstream binary unless measured.

Keep project changes as small, identifiable patches to the pinned base, with
their tests and notices; avoid a second outer wrapper unless an actual dispatch
or deployment problem requires it. Our first compatibility priorities are:

- Primary/backbuffer/attached-depth identity, lifetime and correct presentation
  during menu -> Training -> menu, including MW3's frontbuffer options.
- RGB565 CPU writes and GDI composition without losing unaffected pixels or
  depth when downloading/uploading surfaces.
- Textures, color keys, fog, blend state and transformed RHW/pixel-center
  behavior as required by actual observed calls.
- Required failures and cleanup: allocation/upload failure, invalid descriptors,
  partial initialization, Restore/focus handling and resource release.

The evaluation identifies concrete error propagation debt: transfer helpers
return void/log lock failures while callers clear dirty flags and return success.
Propagate transfer status, retain dirty state on failed copies, and fix relevant
callers before declaring that resource boundary correct. Exercise injected
failure only in authored fixtures, not by corrupting the user's game data.

Success-returning BeginIndexed/Index stubs and ignored render states must be
checked against MW3's actual required calls. Implement a required operation or
stop visibly with its identity; do not claim a game defect from an unused stub,
and do not silently advertise unimplemented required capabilities.

### W5: validate and package the wrapper

Use a bounded test matrix: startup/video where reachable, menu widgets/text,
Training HUD/weapons/depth, return to menu, focus loss/restore, mode transitions,
normal quit, and repeated launch. Expand to a representative mission only after
Training works. Record session duration and scenario; do not call a short check
extended stability. Add another GPU vendor before claiming general device
support. Run Vulkan validation on the authored fixture and targeted sessions
where available; keep validation overhead out of performance comparisons.

Output for the user is an identified x32 wrapper, a compatible default config,
launch/restore instructions and supported/unsupported behavior. Packaging must
contain only distributable project/upstream components with notices. It must
not include MW3 executable, media, assets, generated game code or captures.
Review the pinned dependency notices before distribution: D7VK is zlib/libpng;
its inspected dxbc-spirv and libdisplay-info dependencies are MIT. Full
transitive license inventory remains open. No public release is part of this
planning task. Follow [repository distribution policy](legal.md).

## Timing and modern features stay separately measurable

First reproduce the reported cliff/view issue at controlled presentation caps
with the same wrapper/settings/scenario. Record wall time, frame pacing and,
where recoverable, update cadence. Test whether changing only the renderer
changes the symptom. A cap fixing a symptom does not identify a physics cause.

Only then inspect the relevant original timer/update code and the existing
ZipperFixup timing work. A targeted original-game timing patch is possible
without a full recomp, but it needs evidence for this exact executable and
side effects. Do not introduce it in the first Vulkan session.

Keep a timing correction named and optional; compare movement, weapons,
collision and relevant mission behavior against the baseline. Treat smoother
rendering with faithful simulation cadence as a distinct goal from increasing
the simulation rate. If interpolation needs earlier engine state that the
graphics API does not expose, recover that state explicitly through a separate
patch/recomp boundary; do not promise that Vulkan alone supplies it.

## What transfers to the recomp

Transfer the validated D7VK source/backend patches, surface/resource contracts,
configuration choices and graphics regression fixtures. Original x32 import
hooks, native COM pointers and filename-dependent settings cannot simply be
copied into the x64 native host.

Stage R requires an x64 provider build and typed adapters for 32-bit guest
objects, structures, handles, callbacks and Lock/Unlock memory. Keep host
pointers/Vulkan handles outside guest memory. Test that boundary independently
before connecting live translated producers. Wrapper success does not excuse
missing initialization, assets, input, audio or game update/render execution.

The first implementation action under this plan is W0, followed by **W1: an
isolated original MW3 menu through the existing x32 D7VK release**, preserving
the current 30 FPS reference cap. The next defect found there determines the
first source patch; the default task is not writing a new generic renderer.

Planning validation: check local links, whitespace, input pins and consistency
with the evaluation/current strategy. No game launch or graphics rerun is
required merely to write this plan.

## W0–W5 execution record (2026-10-12)

### W0: Isolated profile and state preservation

- Prepared isolated private test installation under ignored
  `local/work-ahead/mw3-d7vk-wrapper/game/` (130 retail 1.2 files copied from
  `MW3/`, excluding media ISOs/patch archives and excluding dgVoodoo's
  `DDraw.dll`, `D3DImm.dll`, and `dgVoodoo.conf`), with disposable pilot
  `pilots/D7VKTEST.mw3`.
- Installed pinned x32 D7VK v2.3 `ddraw.dll`
  (`00211f2f9f8589845940973ad8195f08f5f724510a2b800566e31f7c170e9f34`) and
  `dxvk.conf`
  (`1c43384389f8edacd84f797c6cdf113fd797692329d0ba9e8cdb6620ba7f07b3`) setting
  `d3d9.maxFrameRate = 30`, `ddraw.forceLegacyPresent = True`, and
  `ddraw.emulateFrontBuffer = True`.
- Verified `Mech3.exe` (`0x00597800..0x00598260`) reads/writes 26 configuration
  values under `HKCU\Software\MicroProse\MechWarrior 3\1.0` and reads
  `InstallOptions` from `HKLM\SOFTWARE\WOW6432Node\MicroProse\MechWarrior 3\1.0`
  while keeping asset/save/log paths CWD-relative. Backed up both registry keys
  and `MW3/pilots` + `MW3/configs` under
  `local/work-ahead/mw3-d7vk-wrapper/backups/`, verified by `restore_state.py`.
- Full static import resolution (18 DLLs) and baseline environment (`3440x1440`
  32 bpp @ `144 Hz`) recorded in
  `local/work-ahead/mw3-d7vk-wrapper/w0-profile-manifest.json`.

### W1 Run 01: First failure boundary on non-interactive sandbox desktop

- Launching `Mech3.exe` (PID `2508`) directly inside the tool runner's
  non-interactive desktop (`exebox-*`) loaded D7VK v2.3 and native
  `C:\Windows\SysWOW64\ddraw.dll`, enumerated `D6VK HAL`, and passed
  `zEffInit`..`zWepInit`, then aborted with `Error opening video... ABORTING RUN`
  immediately at `DDraw4Interface::SetDisplayMode: 640x480:16@0`
  (`src/ddraw/ddraw4/ddraw4_interface.cpp:598`, `m_proxy->SetDisplayMode`).
- Authored 32-bit diagnostic `local/work-ahead/mw3-d7vk-wrapper/probe/probe_displaymode.cpp`
  and reproduced the exact failure:
  - On the non-interactive `exebox-*` desktop, `C:\Windows\SysWOW64\ddraw.dll`
    `IDirectDraw4::SetDisplayMode(640, 480, 16, 0, 0)` returns
    `HRESULT=0x80004001` (`DDERR_UNSUPPORTED`).
  - On the interactive desktop `WinSta0\Default` (with Windows'
    `DWM8And16BitMitigation` appcompat layer), both `C:\Windows\SysWOW64\ddraw.dll`
    and D7VK `ddraw.dll` return `HRESULT=0x00000000` (`DD_OK`).
- Restored `HKCU\Software\MicroProse\MechWarrior 3\1.0\GameOptions` (`9 -> 8`)
  via `restore_state.py --restore` and updated `launch_w1.py` to launch on
  `WinSta0\Default`.

### W1 Run 02 & W2 Run 03: Live Vulkan menu, Training, and Instant Action

- **Loaded module verification (`runs/w1-run-02/live-modules.json`, PID `52068`;
  `runs/w1-run-03/live-modules.json`, PID `32972`):**
  - `Mech3.exe` (`0x00400000`):
    `95bc2c114c9b2e5c5ada8e40ca78cc79470f862e45313ffad0d1e8e6d4d916bf`
  - App-local D7VK v2.3 `DDRAW.dll` (`0x72110000`):
    `00211f2f9f8589845940973ad8195f08f5f724510a2b800566e31f7c170e9f34`
  - Native proxy `C:\Windows\SysWOW64\ddraw.dll` (`0x71CF0000`):
    `37113406967162585c9a67c252005757459d8efe87684bbc0ce184907d0566b0`
  - Native `C:\Windows\SysWOW64\D3DIM.DLL` (`0x647F0000`):
    `fadc359f132607953ac55c61ccd39ada961e1f81def31efb0bdb821e69ab7c5b`
  - Vulkan loader `C:\Windows\SysWOW64\vulkan-1.dll` (`0x6F940000`):
    `6d040e2d30e9c7ce2035cba706ca3363fe14206df79d9d0332624354d7fedae0`
  - AMD Vulkan ICD `amdvlk32.dll` (`0x6A3A0000`):
    `47a296a967aa1f9f3d16c27c5a501f717034213ef3b67150b024422f00aea221`
  - Zero dgVoodoo modules loaded (`MW3/` installation and launchers untouched).
- **Instrumented runtime evidence:**
  - `Mech3_ddraw.log` confirmed `Effective configuration: ddraw.emulateFrontBuffer = True, ddraw.forceLegacyPresent = True, d3d9.maxFrameRate = 30`,
    adapter `AMD Radeon RX 9070 (AMD proprietary driver 2.0.395)`, D3D6
    compatibility mode, `DDraw4Interface::SetDisplayMode: 640x480:16@0`
    (exclusive full-screen present mode), `IID_IDirect3DHALDevice` back buffer
    `640x480` (`D3D9Format::R5G6B5`) + depth stencil `640x480`, and Vulkan
    swapchain `VK_FORMAT_R8G8B8A8_UNORM`, `VK_COLOR_SPACE_SRGB_NONLINEAR_KHR`,
    `VK_PRESENT_MODE_FIFO_KHR`, `640x480`, `3` images.
  - In `w1-run-02` (PID `52068`, `91.8 s`) and `w1-run-03` (PID `32972`,
    `61.2 s`), `mech3.out` recorded 3D viewport buffer allocation
    (`Window (new ...) buffer: 19949028 (640 x 480 x 16)`), D7VK compiled the
    `D16_UNORM` depth copy compute/pixel shaders
    (`meta_cs_copy_image_to_buffer_2d_d16_unorm`,
    `meta_ps_copy_buffer_to_image_2d_d16_unorm`), and both sessions unloaded
    D7VK cleanly (`<<<<<<< UNLOADING D7VK <<<<<<<`) with `exit_code = 0`
    (`0x00000000`) and zero registry/file drift (`hkcu_changes: {}`).
- **User gameplay observations (distinguished from instrumented logs):**
  - User confirmed that the menu, Training, and Instant Action worked normally,
    and noted that loading into Training and Instant Action was instant compared
    to a ~30s–1m wait previously observed under the dgVoodoo setup.

### W3: Reproducible x32 source build of unmodified pinned D7VK v2.3

- Prepared an isolated build tree under
  `local/work-ahead/mw3-d7vk-wrapper/d7vk-source` at pinned commit
  `ff123cb08ff1fcf6575a6ef8fb79d824a84e56c4` with submodule commits
  `subprojects/dxbc-spirv` (`06f6dc99bd6fe7fb4cfbfacba5dde3aa7fb8dc2c`),
  `subprojects/dxbc-spirv/subprojects/spirv_headers`
  (`aa6cef192b8e69eb9ebefeb7ef8fe4bf2fa9c405`), and
  `subprojects/libdisplay-info` (`21feb0bcd8ae1fd1ffe1bcdbabbfcf3f0f8a1fb3`).
- Built unmodified x32 `ddraw.dll` using MSVC `19.51.36256` (`vcvarsall.bat x86`),
  Meson `1.10.2`, Ninja (`-j 4`), and `glslangValidator.exe` (`11.13.0`) via
  `local/work-ahead/mw3-d7vk-wrapper/build_w3_msvc.ps1` (log:
  `local/work-ahead/mw3-d7vk-wrapper/build-logs/w3-msvc-x86.log`) with
  `-Denable_d3d9=true -Denable_ddraw=true -Denable_dxgi=false -Denable_d3d8=false -Denable_d3d10=false -Denable_d3d11=false`:
  - Output: `local/work-ahead/mw3-d7vk-wrapper/build-w3-msvc-x86/src/ddraw/ddraw.dll`
  - Size: `4,026,368` bytes
  - SHA-256: `61c01a0ba100f994db9f32d084ff6552c1905f4f76571c9d3a78a249fa4a21ee`
- Verified the unmodified W3 build against `mw34_d7vk_fixture.exe` on
  `WinSta0\Default` (`local/work-ahead/mw3-d7vk-wrapper/runs/w3-fixture-unmodified/`,
  `exit_code = 0`).

### W4: Surface transfer error propagation, dirty-state retention, and visible stub failure

- Authored narrow regression fixture
  `local/work-ahead/mw3-d7vk-wrapper/probe/test_transfer_errors.cpp` ->
  `local/work-ahead/mw3-d7vk-wrapper/probe/test_transfer_errors.exe` (SHA-256
  `7d315fd594f6aaf14b48ba69390fc8bf737486041f2a9fdae0b09384410d43b2`, compiled
  with `/W4 /WX`).
- Confirmed all 8 pre-patch defects against the unmodified W3 `ddraw.dll` in
  `local/work-ahead/mw3-d7vk-wrapper/runs/w4-regression-unmodified/` (`exit_code = 1`):
  1. `IDirect3DDevice3::SetTexture` returned `0x00000000` (`D3D_OK`) when the
     bound dirty texture surface was busy (`DDERR_SURFACEBUSY`, `0x887601AE`).
  2. `IDirect3DDevice3::DrawPrimitive` returned `0x00000000` when the bound dirty
     texture surface upload failed (`0x887601AE`).
  3. After releasing the busy lock, the texture's dirty flag had been cleared
     prematurely and `D3DLOCK_DISCARD` had discarded its D3D9 contents (readback
     pixel `(6,6)` was `0x0000` instead of `0xF81F`).
  4. `IDirect3DDevice3::DrawPrimitive` returned `0x00000000` when a dirty render
     target upload failed (`0x887601AE`).
  5. After releasing the render-target lock, the CPU write at `(20,20)` had been
     lost (`0xF800` instead of `0x07E0`) because `UnDirtyDDrawSurface()` ran
     despite the failed upload.
  6. `IDirectDrawSurface4::Blt` and `BltFast` from a dirty D3D9 render target
     returned `0x00000000` when `DownloadSurfaceData()` failed (`0x887601AE`).
  7. After releasing the lock, the GPU draw at `(32,32)` was lost (`0x07E0`
     instead of `0x001F`) because `UnDirtyD3D9Surface()` ran despite the failed
     download.
  8. `D3D6Device::BeginIndexed` and `D3D6Device::Index` returned `0x00000000`
     (`D3D_OK`) instead of failing visibly.
- Patched `local/work-ahead/mw3-d7vk-wrapper/d7vk-source` (saved to
  `local/work-ahead/mw3-d7vk-wrapper/patches/w4-transfer-and-stub-contracts.patch`,
  `181,892` bytes, SHA-256
  `725c0d4d549bee6f19680504ac89702770651d6556a2a925cb0fa2d89bfedb00`):
  - `src/ddraw/ddraw_format.h`: `BlitToD3D9CubeMap`, `BlitToD3D9Texture`,
    `BlitToD3D9Surface`, and `BlitToDDrawSurface` return `HRESULT`; D3D9 upload
    helpers lock the source DDraw surface (`DDLOCK_READONLY`) before locking the
    D3D9 destination with `D3DLOCK_DISCARD`, preventing destination discard on
    source lock failure.
  - `src/ddraw/ddraw{,2,3,4,7}/ddraw{,2,3,4,7}_surface.{h,cpp}`:
    `DownloadSurfaceData` and `UploadSurfaceData` return and propagate `HRESULT`,
    clearing dirty state (`UnDirtyD3D9Surface` / `UnDirtyDDrawSurface`) only on
    `SUCCEEDED(hr)`; `Blt`, `BltFast`, `Flip`, `GetDC`, `Lock`, `ReleaseDC`, and
    `Unlock` propagate upload/download errors and defer `UnDirtyD3D9Surface` on
    full-surface overwrite/lock until the underlying proxy call succeeds.
  - `src/ddraw/d3d{3,5,6,7}/d3d{3,5,6,7}_device.{h,cpp}`,
    `src/ddraw/d3d{3,5}/d3d{3,5}_texture.cpp`, and `src/ddraw/d3d_viewport.cpp`:
    `DDrawDirtySurfaceUpload()` returns `HRESULT` and is checked across all
    `DrawPrimitive*`, `Clear`/`Clear2`, and `Load` paths; `BeginIndexed` and
    `Index` in `D3D6Device` and `D3D5Device` return `DDERR_UNSUPPORTED`
    (`0x80004001`).
- Built patched W4 `ddraw.dll` in
  `local/work-ahead/mw3-d7vk-wrapper/build-w4-msvc-x86/src/ddraw/ddraw.dll`
  (`4,026,368` bytes, SHA-256
  `c00a2ef10b6bb0c62707d7fc6497cc2f755382ccf44167ec893dd3c7c91ffbd5`; log:
  `local/work-ahead/mw3-d7vk-wrapper/build-logs/w4-msvc-x86.log`) while keeping
  the unmodified W3 build intact.
- Verified on `WinSta0\Default`:
  - `test_transfer_errors.exe` (`local/work-ahead/mw3-d7vk-wrapper/runs/w4-regression-patched/`):
    all 8 contract checks passed (`exit_code = 0`).
  - `mw34_d7vk_fixture.exe` (`local/work-ahead/mw3-d7vk-wrapper/runs/w4-fixture-patched/`):
    all offscreen draw/depth/CPU/texture/GDI checks passed (`exit_code = 0`).
  - Live `Mech3.exe` session (`local/work-ahead/mw3-d7vk-wrapper/runs/w4-run-01/`,
    PID `48436`, `77.5 s`): verified loaded `DDRAW.dll` SHA-256
    `c00a2ef10b6bb0c62707d7fc6497cc2f755382ccf44167ec893dd3c7c91ffbd5`
    (`D7VK: v2.3+`, `Build: x86 msvc 19.51.36256`), 3D viewport entry across 3
    simulation windows (`Window (new ...) buffer: 19974028 (640 x 480 x 16)`),
    `D16_UNORM` depth copy shader compilation, clean D7VK unload
    (`<<<<<<< UNLOADING D7VK <<<<<<<`), `exit_code = 0`, and zero registry/file
    drift (`hkcu_changes: {}`).

### W5: Validation and distributable wrapper package

- Staged distributable wrapper package under
  `local/work-ahead/mw3-d7vk-wrapper/package/` via
  `local/work-ahead/mw3-d7vk-wrapper/package_w5.py` (manifest:
  `local/work-ahead/mw3-d7vk-wrapper/package/package-manifest.json`), containing
  only distributable project/upstream components and notices (`contains_mw3_executables_or_assets: false`):
  - `ddraw.dll` (`4,026,368` bytes, SHA-256
    `c00a2ef10b6bb0c62707d7fc6497cc2f755382ccf44167ec893dd3c7c91ffbd5`)
  - `dxvk.conf` (`149` bytes, SHA-256
    `1c43384389f8edacd84f797c6cdf113fd797692329d0ba9e8cdb6620ba7f07b3`)
  - `patches/w4-transfer-and-stub-contracts.patch` (`181,892` bytes, SHA-256
    `725c0d4d549bee6f19680504ac89702770651d6556a2a925cb0fa2d89bfedb00`)
  - `README.md` (`4,040` bytes, SHA-256
    `2e1f9da388d882c133e5457ca67ad16252f3ace953df8d9ab59b0ec5b3e62b06`)
  - `THIRD_PARTY_NOTICES.txt` (`4,559` bytes, SHA-256
    `5ef9d198f6882da6b1031e97cb30e09c479ad10a65add5ac72f9817de01be3ec`)
- **Known fidelity and scope boundaries:**
  - Validated on a single GPU vendor (`AMD Radeon RX 9070`, driver `2.0.395`)
    across bounded interactive sessions (`w1-run-02` `91.8 s`, `w1-run-03`
    `61.2 s`, `w4-run-01` `77.5 s`) and two offscreen fixtures
    (`mw34_d7vk_fixture.exe`, `test_transfer_errors.exe`). Only 64-bit
    `VkLayer_khronos_validation.dll` is present in
    `local/tools/vulkan-sdk-portable/Bin`; no 32-bit `WOW6432Node` explicit
    validation layer is installed on the host.
  - Non-fatal `D3D9DeviceEx::SetRenderState: Unhandled render state 26`
    (`D3DRENDERSTATE_DITHERENABLE`) remains a benign D3D9 log warning on 16-bit
    render targets.
  - Frame rate remains capped at `d3d9.maxFrameRate = 30`; uncapped simulation
    timing/physics investigation remains a separate workstream.
  - Native x64 recompilation acceptance count remains unchanged at `131/144`.
