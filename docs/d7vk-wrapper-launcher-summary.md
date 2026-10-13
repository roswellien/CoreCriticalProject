# MW3 D7VK Vulkan Wrapper and Launcher — Technical Summary

**Date**: 2026-10-13
**Status**: Reported operational in the prepared local development profile; broader compatibility validation remains open.
**Execution Boundary**: Isolated private profile running US retail 1.2 `Mech3.exe` on D7VK (DirectDraw4/Direct3D3 -> Direct3D9 -> Vulkan) with camera FOV widescreen fix, MSAA, anisotropic filtering, and cumulative AI textures.

This is the original-executable wrapper track alongside
native recompilation (local reference: `docs/faithful-modernization-plan.md`). D7VK supplies Vulkan
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
  `esi` is loaded from `[0x008027C8 + 0x20]` = `[0x008027E8]` (the backbuffer surface pointer).
  Tracing back to initialization function `0x00577EE5` in `zVideo\zvid_dd.c`:
  The investigation identified these contributing compatibility issues:
  1. **Uninitialized Stack Garbage**: The 1999 game allocated a 4-byte `DDSCAPS` struct on stack rather than a 16-byte `DDSCAPS2` struct. Modern Windows `SysWOW64\ddraw.dll` strictly validates `dwCaps2..4`. Because these fields held stack garbage, the proxy rejected the call with an error.
  2. **D7VK Fallback Omission**: D7VK already enumerates and caches the swapchain backbuffer (`m_nextFlippable`) during primary surface construction, but `DDraw4Surface::GetAttachedSurface` forwarded strictly to the proxy and returned NULL if the proxy failed.
  3. **WDDM 16-Bit Desktop Mode Rejection**: On Windows 11, physical monitor mode switches to 16-bit color at high resolutions (e.g. 2560×1440 16bpp) fail in `m_proxy->SetDisplayMode`. In D7VK, this failure was bubbled up, causing `Mech3.exe` to abort before creating 3D surfaces.
* **Code Fixes Applied to D7VK Source**:
  * **`src/ddraw/ddraw4/ddraw4_surface.cpp`** (patched source remains under ignored `local/work-ahead/mw3-d7vk-wrapper/d7vk-source/`):
    Sanitized `DDSCAPS2` by zeroing `dwCaps2..4` for `DDSCAPS_BACKBUFFER` queries. Added fallback to return `ref(m_nextFlippable)` when the proxy lookup fails and a cached backbuffer exists.
  * **`src/ddraw/ddraw4/ddraw4_interface.cpp`** (same local source tree):
    Allowed `SetDisplayMode` to proceed with virtual presentation mode when physical 16-bit desktop mode switches are rejected by modern WDDM drivers.

---

## 4. Build and Artifact Manifest

These identities describe local artifacts; they do not distribute them. Rows
marked "Verified bootstrap" or "Verified batch entry point" contain no SHA-256
pin in this report. The hash-pin row records the expected DLL digest, not the
digest of the text file containing that pin. D7VK, DXVK and the FOV plugin retain
their own licenses; the project's MIT license covers its own contributions.

| Component | Path | SHA-256 Digest |
|---|---|---|
| Recompiled D7VK `ddraw.dll` | `local/work-ahead/mw3-d7vk-wrapper/game/ddraw.dll` | `57b84ffe136db85e567c09ada00c3d39666f823f2c1e4b1406e35b42a445ac11` |
| Hash Admittance Pin | `local/work-ahead/mw3-d7vk-wrapper/launcher-ddraw.sha256` | `57b84ffe136db85e567c09ada00c3d39666f823f2c1e4b1406e35b42a445ac11` |
| Primary Launcher | `mw3_launcher.py` | `b6572f390a8311edb6083e3fe008516867733dd1a298bc614f4e94b7449baee5` |
| Root Launch Batch | `Launch MW3 (D7VK Vulkan Launcher).cmd` | Verified batch entry point |
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
