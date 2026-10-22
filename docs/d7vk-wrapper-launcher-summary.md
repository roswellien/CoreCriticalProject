# MW3 D7VK Vulkan Wrapper and Launcher — Technical Summary

**Date**: 2026-10-13
**Status**: Reported operational in the prepared local development profile; broader compatibility validation remains open.
**Execution Boundary**: Isolated private profile running US retail 1.2 `Mech3.exe` on D7VK (DirectDraw4/Direct3D3 -> Direct3D9 -> Vulkan) with camera FOV widescreen fix, MSAA, anisotropic filtering, and cumulative AI textures.

This is the original-executable wrapper track alongside
[native recompilation](faithful-modernization-plan.md). D7VK supplies Vulkan
rendering in place of dgVoodoo in this profile. Original game execution does
not complete native host/menu/Training milestones or change the last verified
selected-startup acceptance count of **131/144**. The observations below describe
the local setup as of the date above, not a claim of full campaign or cross-GPU
compatibility. See the [wrapper plan](mw3-d7vk-wrapper-plan.md) for validation gates.

---

## 1. Executive Summary

A modern, standalone game launcher and patched Vulkan wrapper pipeline was developed for MechWarrior 3. The launcher enables high-resolution rendering (both 4:3 pillarboxed equivalents and unstretched 16:9/21:9 widescreen), multi-sample anti-aliasing (MSAA), anisotropic filtering (AF), and cumulative AI texture pack injection—all while maintaining complete isolation from the original game installation (`MW3/`) and leaving all existing reverse-engineering/recompilation acceptance criteria intact.

### Key Capabilities
* **Resolution Management**:
  * **4:3 High-Res Equivalents**: 1024×768 (Native), 1440×1080 (1080p eq), 1920×1440 (1440p eq), 2880×2160 (4K eq) presented cleanly pillarboxed.
  * **Widescreen**: 1920×1080 (1080p), 2560×1440 (1440p), 3440×1440 (21:9 Ultrawide), 3840×2160 (4K) with in-engine camera FOV correction to prevent horizontal stretching.
* **Anti-Aliasing**: Forced hardware MSAA (2x, 4x, 8x) via D7VK DirectDraw FSAA emulation.
* **Anisotropic Filtering**: Hardware sampler anisotropy (2x, 4x, 8x, 16x) via DXVK.
* **AI Texture Pack**: Switching of 39 cumulative AI-upscaled `.zbd` archives via NTFS hard links, with automatic registry configuration (`TextureMemory_HW = 6`). Each profile directory entry is replaced atomically; the entire bank set is not one atomic transaction. The configured manifest is a dated snapshot and may change during ongoing asset work.
* **Zero Modification of Original Files**: The user's `MW3/` folder (including retail binaries and `dgVoodoo`) remains completely untouched.
* **Registry Protection**: User registry keys (`InGameVMode` and `TextureMemory_HW`) are backed up before launch and restored upon exit.

---

## 2. System Architecture

```text
┌────────────────────────────────────────────────────────┐
│               mw3_launcher.py (GUI / CLI)              │
│    (Root folder & local/work-ahead/mw3-d7vk-wrapper)   │
└──────────────────────────┬─────────────────────────────┘
                           │ Stages config & profile
                           ▼
┌────────────────────────────────────────────────────────┐
│     Isolated Game Profile (game/Mech3.exe, PID)        │
│                                                        │
│  ┌───────────────────────┐   ┌──────────────────────┐  │
│  │ MechWarrior3FOVFix    │   │  D7VK ddraw.dll      │  │
│  │ (Camera Aspect / FOV) │   │  (Patched W6/W7)     │  │
│  └───────────┬───────────┘   └──────────┬───────────┘  │
│              │                          │              │
│              ▼                          ▼              │
│  ┌───────────────────────┐   ┌──────────────────────┐  │
│  │   DirectDraw4 / D3D3  │──▶│  D3D9 / DXVK Layer   │  │
│  └───────────────────────┘   └──────────┬───────────┘  │
│                                         │              │
│                                         ▼              │
│                              ┌──────────────────────┐  │
│                              │ Vulkan Physical GPU  │  │
│                              │ (AMD Radeon RX 9070) │  │
│                              └──────────────────────┘  │
└────────────────────────────────────────────────────────┘
```

### Component Breakdown
1. **Launcher**:
   * [`mw3_launcher.py`](../mw3_launcher.py): Python 3.14 Tkinter graphical interface + headless CLI. Available in the repository root and in the wrapper directory.
   * [Root launch batch](../Launch%20MW3%20%28D7VK%20Vulkan%20Launcher%29.cmd): Double-click batch script with automatic Python path resolution.
2. **D7VK Vulkan Wrapper**:
   * Upstream commit `ff123cb08ff1fcf6575a6ef8fb79d824a84e56c4` compiled with MSVC 2026 Developer Command Prompt v18.9 (x86 32-bit).
   * Maps `IDirectDraw4` and `IDirect3DDevice3` (`D3D6Device`) to DXVK D3D9, which compiles shaders to SPIR-V and renders directly on the host Vulkan driver.
3. **Camera FOV Hook (`MechWarrior3FOVFix.asi`)**:
   * Version 1.6 by AlphaYellow.
   * Bootstrapped at runtime using `mw34_fov_launcher.exe` and `mw34_fov_bootstrap.dll` in `build/widescreen-test/Release/`.
   * Staged with a dynamically generated `MechWarrior3FOVFix.ini` containing target width, height, and `FOVFactor=1.0`. Intercepts aspect ratio and horizontal/vertical camera FOV instructions in `Mech3.exe` without altering the executable binary.
4. **AI Texture Hard-Link Layer**:
   * Reads manifest `local/work-ahead/texture-launcher-audit-v2/configured-banks.json` (39 verified banks).
   * Uses NTFS hard links (`os.link`) to switch `.zbd` files instantaneously without copying gigabytes of archive data.
   * Private original archives are safely cached in `local/work-ahead/mw3-d7vk-wrapper/original-banks/`.

---

## 3. Critical Bugs Diagnosed & Resolved

### 3.1 "Video Device Failed to Initialize" Crash
* **Symptom**: Game crashed during initial window creation when higher resolutions were selected.
* **Root Cause**: `d3d9.forceAspectRatio = 16:9` was configured in `dxvk.conf`. DXVK implements `forceAspectRatio` by filtering enumerated DirectDraw display modes to strictly match 16:9. Because MechWarrior 3's front-end menu initializes in 640×480 (4:3), the adapter mode list contained no compatible mode, causing DirectDraw device creation to fail.
* **Fix**: Removed `d3d9.forceAspectRatio` from `dxvk.conf`. Proper widescreen display is achieved through `MechWarrior3FOVFix` camera projection correction while preserving all enumerated modes.

### 3.2 Foreground Focus Loss on Exclusive Fullscreen
* **Symptom**: Window focus conflicts and sporadic display initialization failures on startup.
* **Root Cause**: The Tkinter launcher window remained visible in the background, intercepting mouse capture and focus transitions during `Mech3.exe`'s exclusive mode switch.
* **Fix**: Updated `mw3_launcher.py` to withdraw the GUI (`root.withdraw()`) during process execution and de-iconify (`root.deiconify()`) cleanly once the game process terminates.

### 3.3 Menu Resolution Architecture Clarification
* **Finding**: The 1999 retail game executable hardcodes all 2D user interfaces (menus, Mech Lab, briefings, video cinematics) to 640×480 16-bit DirectDraw. Configured high resolutions only apply once the 3D world simulation starts.

### 3.4 Instant Action Transition Crash (`0x00177648` / `0xC0000005`)
* **Symptom**: Game loaded menus successfully, but crashed with Access Violation (`0xC0000005`) upon clicking **Launch** into Instant Action or Campaign missions.
* **Disassembly Diagnosis**:
  Application Event Log identified fault offset `0x00177648` (`0x00577648` VA) in `Mech3.exe`:
  ```asm
  00577648: 8B 06          mov eax, dword ptr [esi] ; Dereferencing NULL surface pointer
  0057764A: 6A 00          push 0                   ; hEvent = NULL
  0057764C: 6A 01          push 1                   ; dwFlags = DDLOCK_WAIT
  0057764E: 53             push ebx                 ; lpDDSurfaceDesc (dwSize = 0x7C)
  0057764F: 6A 00          push 0                   ; lpDestRect = NULL
  00577651: 56             push esi                 ; this = esi
  00577652: FF 50 64       call dword ptr [eax+64h] ; IDirectDrawSurface4::Lock (vtable index 25)
  ```
  `esi` is passed from `0x005775C3` (`[0x008027C8 + 0x20]` = `[0x008027E8]` backbuffer surface) or `0x0057BA3C` (`[ecx]` texture surface).
  Tracing through the complete mode-switch sequence `0x00577CD0`:
  1. `0x00578740` releases the previous 2D 640×480 menu surfaces.
  2. `0x00577C40` calls `IDirectDraw4::SetDisplayMode(width, height, 16)`.
  3. `0x00577DF0` allocates new 3D surfaces: Primary (`0x00577EAB`), Backbuffer (`0x00577EEC`), and Depth/Stencil Z-Buffer (`0x00577F79`), then attaches Z-buffer via `pBackBuffer->AddAttachedSurface(pZBuffer)` (`0x00577FA0`).
  The investigation identified the exact chain of failures in modern Windows 11:
  1. **Z-Buffer Hardware Emulation Rejection**: Modern `C:\Windows\SysWOW64\ddraw.dll` has no Direct3D hardware support and rejects all `DDSCAPS_ZBUFFER` creation with `DDERR_NOZBUFFERHW` (`0x88760064`).
  2. **Dimension Mismatch on Surface Attachment**: Because Windows 11 WDDM drivers reject 16-bit physical mode switches, the underlying proxy desktop retains native display dimensions (e.g. 3440×1440), while `Mech3.exe` requested custom resolution (e.g. 2560×1440). When `pBackBuffer->AddAttachedSurface(pZBuffer)` was forwarded to the proxy, it failed with `DDERR_CANNOTATTACHSURFACE` / `E_INVALIDARG` due to mismatched proxy surface bounds.
  3. **Uninitialized Stack Garbage**: The 1999 game allocated a 4-byte `DDSCAPS` struct on stack rather than a 16-byte `DDSCAPS2` struct for `GetAttachedSurface`.
  When any of these steps failed, `Mech3.exe` aborted initialization before `0x008027E8` was populated, leaving the backbuffer NULL. The render loop then dereferenced NULL `esi` at `0x00577648`.
* **Code Fixes Applied to D7VK Source**:
  * **`src/ddraw/ddraw4/ddraw4_interface.cpp`**:
    - Enforced `dwSize = sizeof(DDSURFACEDESC2)` sanitization.
    - Added proxy fallback in `CreateSurface`: when `m_proxy->CreateSurface` fails for non-primary surfaces (e.g. Z-buffers or VRAM textures), retries with `DDSCAPS_SYSTEMMEMORY` and maps `DDSCAPS_ZBUFFER` to an offscreen plain backing in system memory. D7VK manages the actual Vulkan depth-stencil texture in D3D9, so the proxy object serves as an error-free placeholder.
    - Updated `SetDisplayMode` to maintain virtual primary surface dimensions.
  * **`src/ddraw/ddraw4/ddraw4_surface.cpp`**:
    - In `AddAttachedSurface`: when `m_proxy->AddAttachedSurface` fails due to WDDM desktop size mismatches, logs a warning and proceeds with virtual attachment in D7VK (`m_depthStencil = attachedSurf`), returning `DD_OK`.
    - In `GetAttachedSurface`: added fallback for `DDSCAPS_ZBUFFER` to return `m_depthStencil.ref()`, and sanitized `cleanCaps` for `DDSCAPS_BACKBUFFER`.
  * **`mw3_launcher.py`**:
    - Enabled `D7VK_LOG_LEVEL = "debug"` by default so all surface calls and mode switches are logged to `Mech3_ddraw.log`.

### 3.5 Surface Descriptor Format Overwrite Fix ("Failed to Initialize Video Source")
* **Symptom**: Game immediately failed with "failed to initialize video source" dialog and reset back to the launcher.
* **Root Cause**: An initial surface descriptor sync in `d7vk-source/src/ddraw/ddraw4/ddraw4_interface.cpp` copied the caller's descriptor into the primary surface wrapper. For primary flippable surfaces created by `Mech3.exe`, the caller passes `dwFlags = 0x21` (`DDSD_CAPS | DDSD_BACKBUFFERCOUNT`) without `DDSD_PIXELFORMAT`. Copying this descriptor directly zeroed out the valid 16-bit RGB pixel format established by the proxy, causing DXVK `ConvertFormat` to fail with `D3DFMT_UNKNOWN` and `CreateDevice` to reject initialization with `D3DERR_INVALIDCALL`.
* **Fix**: Scoped descriptor mutation strictly to the `isZBufferFallback` code path, ensuring primary flippable surfaces retain their valid pixel formats and display mode settings.

### 3.6 Mission Mode Switch Primary Surface & Backbuffer Proxy Fix
* **Symptom**: Game booted successfully into 2D menus, but crashed with Access Violation (`0xC0000005`) when clicking **Launch** into an Instant Action point.
* **Root Cause & Disassembly Diagnosis**:
  When loading into the 3D simulation, `Mech3.exe` calls `00578740` to release all 2D surfaces, calls `SetDisplayMode` for the target 3D mode (e.g. 1024×768), and then calls `IDirectDraw4::CreateSurface` for the new flippable primary surface:
  1. On modern Windows WDDM drivers, `m_proxy->CreateSurface` returned `0x88760234` (`DDERR_PRIMARYSURFACEALREADYEXISTS`): the proxy DirectDraw driver retained the existing primary display surface allocation across mode switches.
  2. While D7VK's primary surface recovery acquired the existing GDI primary surface via `GetGDISurface`, the proxy GDI surface has no attached backbuffer. When `Mech3.exe` subsequently queried `primary->GetAttachedSurface(&caps, &pBackBuffer)` (`0x00577EEC`), the proxy returned `DDERR_NOTFOUND`.
  3. D7VK attempted to create a fallback backbuffer proxy surface, but the fallback descriptor copied the primary surface's descriptor (`dim=0x0`) and included `DDSCAPS_BACKBUFFER | DDSCAPS_OFFSCREENPLAIN`. According to DirectDraw specifications, standalone `CreateSurface` strictly forbids `DDSCAPS_BACKBUFFER` and rejects contradictory caps with `DDERR_INVALIDCAPS` (`0x88760168`).
  4. Because `m_proxy->CreateSurface` failed, `GetAttachedSurface` returned failure to `Mech3.exe`, leaving backbuffer pointer `[0x008027E8]` NULL. The 3D render loop then crashed dereferencing NULL `esi` at `0x00577648`.
* **Fix Applied to D7VK Source**:
  1. **Primary Surface Recovery**: In `DDraw4Interface::CreateSurface`, when `m_proxy->CreateSurface` returns `DDERR_PRIMARYSURFACEALREADYEXISTS` (`0x88760234`), D7VK acquires the proxy surface via `GetGDISurface`, marks it as primary, calls `SetDesc2` with requested `DDSCAPS_FLIP | DDSCAPS_COMPLEX | DDSCAPS_3DDEVICE`, and returns `DD_OK`.
  2. **Sanitized Backbuffer Proxy Creation**: In `DDraw4Surface::GetAttachedSurface`, the fallback backbuffer proxy descriptor is sanitized to use non-zero display dimensions and valid standalone capabilities (`DDSD_CAPS | DDSD_WIDTH | DDSD_HEIGHT` with `DDSCAPS_OFFSCREENPLAIN | DDSCAPS_3DDEVICE | DDSCAPS_SYSTEMMEMORY`). Once created on the proxy, D7VK wraps it and patches its common descriptor with `DDSCAPS_BACKBUFFER | DDSCAPS_3DDEVICE | DDSCAPS_FLIP` via `SetDesc2`, ensuring `GetAttachedSurface` returns `DD_OK` and `Mech3.exe` receives a valid backbuffer.
  3. **Virtual Attachment Enumeration**: In `DDraw4Surface::EnumAttachedSurfaces`, if the proxy driver reports no attached surfaces, D7VK injects virtually attached surfaces (`m_nextFlippable` and `m_depthStencil`) so downstream enumeration callbacks find all expected surfaces.

---

## 4. Build and Artifact Manifest

These identities describe local artifacts; they do not distribute them. Rows
marked "Verified bootstrap" or "Verified batch entry point" contain no SHA-256
pin in this report. The hash-pin row records the expected DLL digest, not the
digest of the text file containing that pin. D7VK, DXVK and the FOV plugin retain
their own licenses; the project's MIT license covers its own contributions.

| Component | Path | SHA-256 Digest |
|---|---|---|
| Recompiled D7VK `ddraw.dll` | `local/work-ahead/mw3-d7vk-wrapper/game/ddraw.dll` | `bb6f56375c37c3de013e905328e3a81f52a1f8a3efc6355e6c28b6d72d943385` |
| Hash Admittance Pin | `local/work-ahead/mw3-d7vk-wrapper/launcher-ddraw.sha256` | `bb6f56375c37c3de013e905328e3a81f52a1f8a3efc6355e6c28b6d72d943385` |
| Primary Launcher | `mw3_launcher.py` | `006b1218f323aa112506f13b80daf609cfaff7f0e5afad2c585c550109aa6ef1` |
| Root Launch Batch | `Launch MW3 (D7VK Vulkan Launcher).cmd` | Verified batch entry point |
| Root Launch Alias (.cmd) | `Launch MW3 (D7VK Vulkan).cmd` | Verified batch entry point |
| Root Launch Alias (.bat) | `Launch MW3 (D7VK Vulkan).bat` | Verified batch entry point |
| Verified Game Executable | `local/work-ahead/mw3-d7vk-wrapper/game/Mech3.exe` | `95bc2c114c9b2e5c5ada8e40ca78cc79470f862e45313ffad0d1e8e6d4d916bf` |
| Camera FOV Fix Plugin | `local/tools/mw3-fov-v1.6/MechWarrior3FOVFix.asi` | `57afb226033790cafa36f6409ee036c03dc38e42b6cc1fe8d62880b03be2205d` |
| FOV Launcher Binary | `build/widescreen-test/Release/mw34_fov_launcher.exe` | Verified bootstrap |
| FOV Hook DLL | `build/widescreen-test/Release/mw34_fov_bootstrap.dll` | Verified bootstrap |

---

## 5. Usage Instructions

These commands require the prepared Windows development profile. The current
launcher fixes `ROOT` to `D:\Projects\MW34Recomp`; it is not yet a portable
installer. Supply your own admitted MW3 U.S. retail 1.2 installation, the pinned
x32 D7VK build and hash-pin file, the configured texture-bank manifest (currently
read for both original and AI modes), and the FOV plugin/bootstrap components
for widescreen. Hard-linked banks require an NTFS volume shared with the profile.
The root launcher alone does not provision these dependencies. Original media,
AI texture banks, generated game code and local builds remain excluded from Git.

### Running with GUI
Double-click [the launch batch](../Launch%20MW3%20%28D7VK%20Vulkan%20Launcher%29.cmd) in the repository root, or run:
```powershell
python mw3_launcher.py
```

### Running Headless / Command-Line Options
```powershell
# Launch directly at 2560x1440 16:9 widescreen with 8x MSAA, 16x AF, and AI textures:
python mw3_launcher.py --no-gui --resolution "2560x1440 (1440p Widescreen 16:9)" --aa "8x MSAA" --af "16x" --textures ai

# Launch at 4:3 1440p pillarboxed equivalent (1920x1440):
python mw3_launcher.py --no-gui --resolution "1920x1440 (1440p 4:3 Equivalent)" --aa "8x MSAA" --af "16x" --textures ai

# Stage files and configuration without running the game:
python mw3_launcher.py --no-gui --prepare-only
```

Here "headless" means running the launcher without its GUI; the game still
opens a graphical window and uses Vulkan. `--prepare-only` changes profile
textures/configuration without starting the game. The launcher records and
checks registry restoration in its normal cleanup path; forced termination of
the launcher can prevent cleanup.

---

## 6. Safety & Compliance Constraints Maintained

* **Acceptance Criteria**: Recompilation criteria remain 131/144 unchanged; no fake criteria closure was claimed.
* **Process Protection**: No active long-running jobs, background watchers, or SQLite databases were disturbed.
* **Local Assets**: All media, textures, and builds remain local; no copyright assets were added to git tracking.
* **Registry Hygiene**: Registry values are always inspected, backed up to session records, and restored on exit.
