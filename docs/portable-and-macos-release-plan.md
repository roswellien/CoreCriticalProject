# Windows portable and macOS Apple Silicon release plan

Prepared November 24, 2026 for [issue #478](https://github.com/roswellien/CoreCriticalProject/issues/478).
Status: proposed implementation plan; no Windows portable ZIP producer, shared `CoreCritical.Core` library, Avalonia desktop shell, or macOS Core Critical Vulkan build/notarization pipeline is implemented or verified yet. Source baseline: `a7564173b1edf8c517ec607aaa7c6b449c2b34aa` on `develop` (following `v1.0.55-preview` at `b1d91989afdfc5b75c54caf1b2300b4c606c59a0`). Recheck affected files before starting each implementation PR.

## Goal and settled decisions

Extend Core Critical's release platform under the [faithful modernization plan](faithful-modernization-plan.md) and [status reporting rule](project-status-reporting.md) with a signed Windows portable distribution and first-class macOS Apple Silicon support (`WP20` in [renderer-feature-parity.md](renderer-feature-parity.md)), while preparing the shared foundation for Linux (`WP19`) and Android (`WP21`).

The following owner decisions fix the architecture for implementation:

1. **Windows signed portable `.zip`:** Ship a signed portable `.zip` (`corecritical-portable-<version>-win-x64.zip`) alongside `corecriticalinstaller-<version>.exe` starting in the next release cycle (`1.0.56-preview` target), keeping `%LOCALAPPDATA%\MW3Remaster` as the default writable data root so in-place `.ccupdate` upgrades continue to work and `OneDrive` / `Program Files` write issues are avoided.
2. **Cross-platform launcher architecture (Option A):** Extract platform-neutral launcher logic into a shared `CoreCritical.Core` (`net8.0`) library and build an **Avalonia UI** desktop shell targeting `osx-arm64`, `linux-x64`, and eventually `win-x64`, retaining the existing `Planner/*.py` launch-planning scripts through a SHA-256-pinned relocatable Python build on non-Windows OSes.
3. **macOS Apple Silicon (`arm64`, M1+):** Target Apple Silicon M1 and newer exclusively for initial macOS releases (`Core Critical.app` inside `CoreCritical-<version>-macos-arm64.dmg` plus signed in-app self-updates), signed with an **Apple Developer ID Application** certificate and **Apple notarized** (`--ad-hoc` retained only for unprivileged local development builds), with live hardware qualification on the maintainer's **M1 Mac mini**.

## Track 1 — Release platform: Windows portable `.zip` and multi-OS update feed

Before shipping new OS builds, update the existing Windows release automation and update service so multiple OS artifacts share one signed pipeline cleanly.

### 1A. Windows signed portable `.zip` (`1.0.56-preview` target)

The existing Windows launcher in `tools/mw3-remaster-launcher/` is self-contained `net8.0-windows` (`win-x64`) and [installer.iss](../tools/mw3-remaster-launcher/installer.iss) uses `PrivilegesRequired=lowest` without HKLM registry requirements. The signed `NativePreview`, `Planner`, `Tools\Unshield`, `Tools\PlannerPython`, and launcher PE tree verified by `Assert-AllBinariesSigned` in [native_preview_helpers.ps1](../tools/mw3-remaster-launcher/native_preview_helpers.ps1) can therefore run from any writable user folder once packaged directly.

- **New producer script (`tools/mw3-remaster-launcher/build_portable_zip.ps1`):** Invoked from [build_launcher_release.ps1](../tools/mw3-remaster-launcher/build_launcher_release.ps1) after `Assert-AllBinariesSigned` passes on the pre-signed staging tree (`PublishDirectory` with signed `NativePreview`, `Planner`, `Tools/Unshield`, `Tools/PlannerPython`, `Assets`, `update-trust.json`, and `launcher-mw3re-installation.json`).
- **Archive layout and naming:** Name the artifact `corecritical-portable-<version>-win-x64.zip`, placing all files inside a single top-level `Core Critical Launcher/` directory plus a short `README-PORTABLE.txt`. Update [release-filenames.md](release-filenames.md) and [launcher-and-website-release.md](launcher-and-website-release.md) to codify portable ZIP and non-Windows release filenames before publishing.
- **Writable state and self-updates:** Keep `LauncherPaths.DataRoot` at `%LOCALAPPDATA%\MW3Remaster` by default rather than placing 15+ GB of `.mw3pack` mods, settings, and crash logs inside the unzipped binary directory. Because [LauncherUpdates.cs](../tools/mw3-remaster-launcher/Core/LauncherUpdates.cs) runs the `NativePreviewUpgradeOnly` setup with `/DIR=<app>`, `Uninstallable=no`, and `CreateUninstallRegKey=no`, `.ccupdate` in-place upgrades will update a portable folder without creating Add/Remove Programs entries or shortcuts. An opt-in single-folder portable marker can be considered separately if removable-drive use is ever required.
- **Windows security and UX considerations (`README-PORTABLE.txt`):**
  - Unlike an Inno Setup `.exe` (where SmartScreen checks the signed installer once), extracting a downloaded `.zip` via Windows Explorer propagates the Mark of the Web (`Zone.Identifier`) onto extracted `.exe`, `.dll`, and `.pyd` files, causing initial SmartScreen/Defender inspection across the launcher, Python, `unshield.exe`, and `mw3.exe`, though all binaries already carry valid timestamped Azure Authenticode signatures (including Windows 11 Smart App Control compatibility).
  - Warn users to extract the archive completely (never launch from Explorer's ZIP preview) and avoid `Program Files`, `Downloads`, or `OneDrive`-synced folders.
- **Verification gate:** Extract `corecritical-portable-<version>-win-x64.zip` into a clean directory, verify timestamped Authenticode signatures on every extracted `.exe`, `.dll`, and `.pyd`, verify fresh ISO setup + first-frame launch + in-place `.ccupdate` upgrade, and publish beside the installer on `playtest.corecritical.dev` with `SHA256SUMS.txt`.

### 1B. Cloudflare Worker allowlist and multi-OS online catalog

- **Worker route scaling ([worker.mjs](../tools/update-service/worker.mjs)):** `PUBLIC_OBJECTS` is near Cloudflare's 5,120-byte plain-text variable limit, and `PUBLIC_OBJECTS_EXTRA` grows on every release. Move the route allowlist from plain-text Worker environment variables to an R2-backed signed allowlist manifest (or Workers KV) while keeping the strict path/bucket validation rules (`online-updates/` prefix, byte-length checks, ETag matching, `Range` support) and preserving every historical `1.0.x` Windows route untouched.
- **Multi-OS catalog ([build_catalog.py](../tools/update-service/build_catalog.py)):** Remove the hardcoded `os='windows'`, `architecture='x64'`, and `contract='launcher-inno-v1'` assumptions so one signed `corecritical-release-catalog-v1` sequence can publish releases keyed by `(product_id, os, architecture, contract)`:
  - Windows `x64`: `launcher-inno-v1` (`<version>.ccupdate` + `<version>.zip`)
  - macOS `arm64`: `launcher-macos-app-v1` (`<version>-macos-arm64.ccupdate` + `.tar.gz`/`.zip`)
  - Linux `x64`: `launcher-linux-appimage-v1`
  - Existing Windows `<= 1.0.55` launchers continue filtering safely on `windows` / `x64` / `launcher-inno-v1`.

## Track 2 — macOS Apple Silicon (M1+ `arm64`) engine and MoltenVK (`WP20`)

The underlying `runtime/mw3-re/` engine already compiles and runs natively on macOS `arm64`, as documented in [macos.md](../runtime/mw3-re/docs/macos.md) and built by [make_app.sh](../runtime/mw3-re/tools/macos/make_app.sh) and [build_deps.sh](../runtime/mw3-re/tools/deps/build_deps.sh) (`SDL3 3.4.12`, `FreeType 2.13.2`, `SDL3_ttf 3.2.2`, `SDL3_sound 3.2.0`, minimal LGPL `FFmpeg 8.1.2` for native `mw3import` Indeo movie conversion, `zlib`, `xz`, `libarchive`, plus `-ffp-contract=off` for x87-compatible rounding on `arm64`). In `runtime/mw3-re/src/frontend/core_critical/`, `WP18` also established [vk_loader.hpp](../runtime/mw3-re/src/frontend/core_critical/platform/vk_loader.hpp), [wsi_surface.hpp](../runtime/mw3-re/src/frontend/core_critical/platform/wsi_surface.hpp), and the non-Windows compile check [platform_nonwin_contract.cpp](../runtime/mw3-re/src/frontend/core_critical/platform_nonwin_contract.cpp).

The following concrete code work is required to run Core Critical's Vulkan renderer natively on Apple Silicon via MoltenVK:

1. **Remove Win32-only CMake restrictions:**
   - [runtime/mw3-re/CMakeLists.txt](../runtime/mw3-re/CMakeLists.txt): Relax the `if(NOT WIN32 OR NOT SDL3_FOUND)` and x64 checks on `MW3_CORE_CRITICAL_VULKAN` to accept `APPLE` (`arm64`) and `UNIX` (`x86_64`).
   - [src/frontend/core_critical/CMakeLists.txt](../runtime/mw3-re/src/frontend/core_critical/CMakeLists.txt): Move `NOMINMAX`, `WIN32_LEAN_AND_MEAN`, `user32`, `gdi32`, `dxgi`, `d3d11`, and DXGI-only `mw3ccvulkan_checks` registrations under `if(WIN32)`.
2. **MoltenVK portability extensions and feature negotiation ([vk_scene.hpp](../runtime/mw3-re/src/frontend/core_critical/renderer/vk_scene.hpp)):**
   - **Instance creation:** Enumerate instance extensions; whenever `VK_KHR_portability_enumeration` is advertised, append it alongside `VK_KHR_get_physical_device_properties2` and set `VK_INSTANCE_CREATE_ENUMERATE_PORTABILITY_BIT_KHR` on `VkInstanceCreateInfo::flags`.
   - **Device creation:** Whenever the chosen physical device advertises `VK_KHR_portability_subset`, enable it in `VkDeviceCreateInfo::ppEnabledExtensionNames`.
   - **`VK_FORMAT_D32_SFLOAT` depth-blit handling:** `vk_scene.hpp` currently throws if `VK_FORMAT_D32_SFLOAT` lacks `VK_FORMAT_FEATURE_BLIT_SRC_BIT | VK_FORMAT_FEATURE_BLIT_DST_BIT` in `optimalTilingFeatures`. Test what Metal/MoltenVK reports on M1+ and add a `vkCmdCopyImage` or compute/fullscreen depth-transfer fallback if MoltenVK omits either blit bit. (`VK_FORMAT_R5G6B5_UNORM_PACK16` already falls back safely to `VK_FORMAT_R8G8B8A8_UNORM`.)
   - **ImGui overlay and shader translation:** Review `#if defined(_WIN32)` around `editor_imgui.h` / `imgui_impl_vulkan` in `vk_scene.hpp` so non-Windows targets either enable portable ImGui cleanly or isolate Windows-only DXGI paths; validate all 18 compiled SPIR-V shaders (notably `light_cull_tiled.comp`, `sun_scene.frag`, `world_coverage.frag`, `fixture_shadow.*`, `fxaa.*`, and `menu_ripple.frag`) under SPIRV-Cross → MSL with `VK_LAYER_KHRONOS_validation`.
3. **Bundle MoltenVK inside the `.app`:**
   - Pin an official MoltenVK release tarball (matching SHA-256 verification pattern in [build_deps.sh](../runtime/mw3-re/tools/deps/build_deps.sh)), adding an `arm64`-only `mac-arm64` mode alongside universal `mac` so CI/release builds stay small and fast.
   - Ship `libMoltenVK.dylib` (plus Vulkan loader + `MoltenVK_icd.json` or direct `SDL_Vulkan_LoadLibrary` discovery in [vk_loader.hpp](../runtime/mw3-re/src/frontend/core_critical/platform/vk_loader.hpp)) inside `Contents/Frameworks/` so Mac players never install the Vulkan SDK or Homebrew.
4. **CI build gate & M1 Mac mini qualification:**
   - Add a `macos-14` (or `macos-15`, Apple Silicon) job to [.github/workflows/build.yml](../.github/workflows/build.yml) configuring `runtime/mw3-re` with `-DMW3_CORE_CRITICAL_VULKAN=ON`, compiling all SPIR-V shaders, and running non-GPU `mw3core` / `mw3ccvulkan` contract tests on every PR.
   - Qualify live Metal/MoltenVK execution on the maintainer's **M1 Mac mini**: Retina HiDPI swapchain sizing (`SDL_GetWindowSizeInPixels`), macOS fullscreen Spaces transitions, `mw3import` conversion of all 19 movies, `c1m1`, `MechLab`, and all 6 environment packs.

## Track 3 — Cross-platform launcher (`CoreCritical.Core` + Avalonia UI, Option A)

Our current desktop launcher (`tools/mw3-remaster-launcher/`) uses `net8.0-windows` WPF. Under Option A, extract platform-neutral business logic into a shared core library consumed by both the existing Windows WPF frontend (during transition) and a new cross-platform Avalonia UI frontend.

1. **Extract `tools/core-critical-core/CoreCritical.Core.csproj` (`net8.0`):**
   - Move packs, manifests, profiles, graphics settings, online catalog/update cryptographic verification (`RSA` SHA-256 PSS), crash diagnostic bundling, launch-profile generation, and SDL3 gamepad bindings (`ControllerInput.cs`) into `CoreCritical.Core`, keeping all existing Windows `LauncherChecks` passing throughout the extraction.
   - Replace direct Windows APIs behind clean platform interfaces (`IPlatformServices` + per-OS adapters):

| Component | Current Windows coupling | Planned macOS (`arm64`) / POSIX abstraction |
| --- | --- | --- |
| [LauncherPaths.cs](../tools/mw3-remaster-launcher/Core/LauncherPaths.cs) | `%LOCALAPPDATA%\MW3Remaster`, `\<sd>\Games\Core Critical` | `~/Library/Application Support/Core Critical/` (`$XDG_DATA_HOME/core-critical` on Linux); avoid `~/Desktop` and `~/Documents` to prevent macOS TCC / iCloud Drive conflicts |
| [GameInstallation.cs](../tools/mw3-remaster-launcher/Core/GameInstallation.cs) | `kernel32.dll`, `Mount-DiskImage` via PowerShell, `unshield.exe` | Native `hdiutil attach -nobrowse -readonly` / `detach` for ISO setup or direct `mw3-re` `libarchive` setup flow; platform `unshield` / extractor staging |
| [DirectInputJoysticks.cs](../tools/mw3-remaster-launcher/Core/DirectInputJoysticks.cs) & [ControllerInput.cs](../tools/mw3-remaster-launcher/Core/ControllerInput.cs) | `dinput8.dll` P/Invoke alongside SDL3 gamepads | Use cross-platform `SDL3` gamepad/joystick APIs on macOS & Linux; isolate `dinput8.dll` behind a Windows-only provider |
| [HardwareInventory.cs](../tools/mw3-remaster-launcher/Core/HardwareInventory.cs) | `System.Management` WMI + `dxgi.dll` | `sysctl` CPU/RAM queries + Vulkan physical device properties on macOS/Linux |
| [PackStorage.cs](../tools/mw3-remaster-launcher/Core/PackStorage.cs) | `kernel32.dll` `GetFinalPathNameByHandleW` | POSIX `realpath` + `lstat` symlink rejection and physical path pinning |
| [WindowsPublisherTrust.cs](../tools/mw3-remaster-launcher/Core/WindowsPublisherTrust.cs) & [LauncherUpdates.cs](../tools/mw3-remaster-launcher/Core/LauncherUpdates.cs) | `wintrust.dll` `WinVerifyTrust`, `launcher-inno-v1` | `codesign --verify --deep --strict` verification + RSA-PSS signature check + `launcher-macos-app-v1` atomic `.app` updater |
| [SteamHelper.cs](../tools/mw3-remaster-launcher/Core/SteamHelper.cs), [GameValidator.cs](../tools/mw3-remaster-launcher/Core/GameValidator.cs), [PlaytestDiagnostics.cs](../tools/mw3-remaster-launcher/Core/PlaytestDiagnostics.cs) | `Microsoft.Win32` Registry lookups | `~/Library/Application Support/Steam` shortcut path on macOS; remove Windows Registry reads on non-Windows OSes |

2. **Bundled Planner Python:**
   - The `Planner/` launch pipeline (`mw3_re_launch.py`, `prepared_skin_packs.py`, `prepared_mech_packs.py`, `content_capabilities.py`, `native_assets.py`, `legacy_content_capabilities.json`) stays shared across platforms by bundling a SHA-256-pinned relocatable `python-build-standalone` (`aarch64-apple-darwin`) runtime inside `Contents/Resources/Tools/PlannerPython/`, mirroring Windows' pinned embeddable Python `3.14.10`.
3. **Avalonia UI shell (`tools/core-critical-launcher-avalonia/`):**
   - Implement the charcoal/amber launcher screens (Play/Setup Wizard, Mods & Packs, Graphics & Lighting, Controls/Controller, Updates, Crash Reports) in Avalonia XAML (`net8.0`), publishing self-contained `osx-arm64` first, followed by `linux-x64` and later optional migration for Windows once parity and visual checks match WPF.

## Track 4 — macOS packaging, Developer ID signing, notarization, and self-updates

1. **Self-contained bundle layout (`Core Critical.app`, `dev.corecritical.launcher`):**
   - `Contents/MacOS/`: Avalonia self-contained `Core Critical Launcher` (`osx-arm64`), Core Critical Vulkan `mw3`, and `mw3import`.
   - `Contents/Frameworks/`: `libSDL3.0.dylib`, `libSDL3_ttf.0.dylib`, `libSDL3_sound.2.dylib`, minimal LGPL FFmpeg dylibs, `libMoltenVK.dylib` (plus Vulkan loader/ICD if used) — all rewritten to `@rpath` and verified with `sandbox-exec` (zero `/opt/homebrew` or local machine path leaks, matching [make_app.sh](../runtime/mw3-re/tools/macos/make_app.sh)).
   - `Contents/Resources/`: `CoreCritical.icns`, `Assets/`, `Planner/`, `Tools/PlannerPython/`, `NativePreview/runtime.json`, `update-trust.json`, `online-updates.json`, `THIRD-PARTY.txt`, `licenses/`.
2. **Developer ID signing and Apple notarization:**
   - Maintain a clean `--ad-hoc` build path (`codesign -s -`) for local developer testing and PR builds without secrets.
   - For releases (either from a dedicated CI macOS runner with GitHub Secrets or local maintainer release script, keeping `.p12` and App Store Connect API `.p8` keys strictly outside Git):
     - Sign **inside-out** using `codesign --force --timestamp --options runtime --sign "Developer ID Application: ..."`: first every `.dylib`/`.so` in `Contents/Frameworks/` and `Tools/PlannerPython/`, then nested executables (`mw3`, `mw3import` with empty entitlements; `.NET 8` hosts + Python with minimal Hardened Runtime entitlements `com.apple.security.cs.allow-jit` and `com.apple.security.cs.allow-unsigned-executable-memory`), and finally outer `Core Critical.app`.
     - Verify `codesign --verify --deep --strict`, assemble `CoreCritical-<version>-macos-arm64.dmg`, sign the `.dmg`, submit to Apple via `xcrun notarytool submit --wait`, staple both the `.app` and `.dmg` (`xcrun stapler staple`), and gate with `spctl -a -vvv -t exec` + `spctl -a -vvv -t open`.
     - Verify clean download → drag-to-Applications → double-click launch with **zero Gatekeeper warnings** on the **M1 Mac mini**.
3. **macOS online self-updates (`launcher-macos-app-v1`):**
   - Sign and publish a notarized `Core Critical.app` archive alongside `<version>-macos-arm64.ccupdate` metadata (RSA-PSS SHA-256).
   - After staging and verifying both RSA-PSS metadata and `codesign --verify --deep --strict` on the unpacked `.app`, a detached helper waits for launcher exit, atomically swaps the `.app` bundle (leaving `~/Library/Application Support/Core Critical/` untouched), and relaunches via `open -a`.

## Future platform alignment (`WP19` Linux & `WP21` Android)

- **Linux `x64` (`WP19`):** Reuses Tracks 1–3 directly (non-Win32 `MW3_CORE_CRITICAL_VULKAN`, `CoreCritical.Core` + Avalonia UI, POSIX `IPlatformServices`, `PlannerPython`, multi-OS catalog) without MoltenVK or Apple notarization. Target Mesa/RADV/NVIDIA Vulkan (and `lavapipe` for CI smoke tests) packaged as an AppImage (building on [make-appimage.sh](../runtime/mw3-re/tools/linux/make-appimage.sh)), covering desktop Linux and Steam Deck.
- **Android `arm64` (`WP21`):** Builds on the non-Win32 `arm64` Vulkan/C++ engine work from Track 2, then adds Android-specific work separately: NDK/Gradle toolchain, `ANativeWindow` lifecycle/suspend handling, Storage Access Framework (SAF) game-data/pack import, tile-based GPU memory/normal-cache tuning for Adreno/Mali, touch/gamepad-first UI instead of desktop Avalonia, and APK/AAB signing. Dedicated design docs will be prepared for `WP19` and `WP21` when scheduled.

## Milestones and prerequisites

| Milestone | Scope | Entry prerequisites | Completion gate |
| --- | --- | --- | --- |
| **T1 — Windows portable + feed prep** | `build_portable_zip.ps1`, `release-filenames.md`, Worker R2/KV allowlist, multi-OS `build_catalog.py` | Clean `main` release workflow (`1.0.55-preview` baseline) | Extracted portable ZIP passes all signed-PE checks, ISO setup, first frame, and `.ccupdate` upgrade; Worker passes existing `1.0.54`/`1.0.55` compatibility tests |
| **T2 — macOS Vulkan on MoltenVK (`WP20`)** | Unlock `MW3_CORE_CRITICAL_VULKAN` on `APPLE`/`arm64`, portability extensions, `D32_SFLOAT` check, bundled MoltenVK, `macos-14` CI job | **M1 Mac mini** for live GPU/Retina testing | `macos-14` CI builds and passes CTest shader/contract checks; M1 Mac mini renders `c1m1`, `MechLab`, and 6 packs cleanly under Vulkan validation |
| **T3 — `CoreCritical.Core` + Avalonia** | Extract `net8.0` core + POSIX adapters, pin macOS `PlannerPython`, build Avalonia shell (`osx-arm64`) | T2 `mw3` + `mw3import` bundle working cleanly on M1 | Existing Windows `LauncherChecks` stay green; Avalonia launches on M1 Mac mini, imports retail ISO/files, manages packs, and exports crash reports |
| **T4 — Signed/notarized `.dmg` + self-update** | `Core Critical.app` / `.dmg` Developer ID signing, `notarytool` stapling, `launcher-macos-app-v1` updater, R2/feed publish | Active Apple Developer ID Application cert + App Store Connect notarization key + M1 Mac mini | `codesign --verify --deep --strict` and `spctl` pass cleanly after fresh web download on M1 Mac mini; in-app self-update swaps `.app` cleanly |
