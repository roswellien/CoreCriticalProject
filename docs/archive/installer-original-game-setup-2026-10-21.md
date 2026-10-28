# Installer and original-game setup

The intended distribution is an installed application. A separate portable ZIP
is not required. The application still needs a runtime/content preparation path
that works outside this development checkout; that requirement also applies to
an installer. It is not a reason to replace the installer with a portable build.

## Implemented boundary

Launcher 1.0.4-preview adds a shared original-data setup wizard, opened by the
installer's post-install `--setup-game` launch or Settings & Steam → Set Up Game.
It offers the two requested choices:

1. Use an existing original installation. Verify the complete supported original
   data closure, without changing files or saves, then retain the selected path.
2. Select the user's ISO and cumulative English 1.2 patch, and a new destination.
   Mount the ISO, extract the retail InstallShield cabinets, extract replacement
   files from the patch, copy disc movies/marker, and verify before publishing
   the new game folder. Existing destinations are refused, including empty ones.

The old loose-file importer and its unconditional disc-free success message
have been removed. No original setup, updater, game executable, registration
utility, codec installer or DirectX installer is executed. No machine registry
configuration or modification of an existing game installation is needed for
this native data-input path. This is not a replacement retail Windows setup.

The extraction contract currently supports exactly the verified U.S. retail
cabinet/header and English cumulative 1.2 patch identities in
`Core/SupportedMedia.json`. It contains metadata and hashes only. The patch's
embedded Microsoft CAB has a verified offset, length and digest; Windows
`expand.exe` unwraps it, then the existing pinned Unshield 1.6.2 extracts its
InstallShield payload. All 31 replacement files independently match the
previously verified patched installation. Optional variant/locale admission is
not implied. No original media or payload is included in the application bundle.

Input cabinet/patch bytes are copied into private scratch and checked before
extraction. Every selected output is checked against the embedded metadata.
Only a fully verified folder is moved into the new destination. Failure removes
owned scratch, including read-only copies from CD media, and leaves existing
destinations untouched. ISO filenames are passed through an environment variable,
not interpolated into PowerShell code; child exit codes/stderr are checked. An
ISO already mounted by the user is left mounted. A mount made by this operation
is dismounted afterward. The latter ownership branch still needs a clean-machine
exercise; the current real-media test used the already mounted ISO.

## Checks and deployment

- Complete original-file verification passed for the current installed game.
- Actual mounted-disc extraction and ISO-path extraction each produced a new
  verified local installation: 127 original data files plus 20 disc media files.
  Private outputs are under `local/work-ahead/installer-media-20261021-r1/`.
  The existing F: mount remained attached; the original installation stayed selected.
- Authored checks cover damaged hashes/sizes, missing closure, existing-folder
  preservation, failed-stage cleanup and drive-root containment. The full existing
  launcher check program also passes.
- Release self-contained publication succeeded. The complete .NET desktop runtime
  is included; copying only the five launcher binary files is insufficient for
  this publication mode. The complete bundle was deployed to the stable local
  launcher, preserving artwork, settings and packs. No separate .NET installation
  was performed.
- Actual WPF UI showed both choices and ISO/patch/destination fields; existing
  folder verification completed through the UI and returned to the launcher.
  ISO installation was exercised through the same backend from the test CLI,
  not by completing the file-pickers in the UI.

Reproduce local publication from the repository root:

```powershell
dotnet publish tools/mw3-remaster-launcher/MW3RemasterLauncher.csproj -c Release -r win-x64 --self-contained true
./tools/mw3-remaster-launcher/stage_media_tools.ps1 -PublishDirectory tools/mw3-remaster-launcher/bin/Release/net8.0-windows/win-x64/publish
```

The staging helper reuses the existing hash-pinned local extraction binaries
and includes Unshield's MIT license. The exact Unshield source commit is
`51de441ba6893f11026d4671ccef9e8e2a4634fa`. Its existing local zlib DLL is the
Python 3.14 supplied `1.3.1.zlib-ng` build; the source/build/license provenance
must be completed before redistributing that dependency. This staging is for
local development, not release clearance. No new external dependency was downloaded.

Inno Setup now launches this shared wizard instead of a separate existing-folder
page, and no longer creates competing initial settings. Required runtime/extractor
entries prevent compiling that installer from a GUI-only publish directory.
Inno Setup is not installed here, so an installer executable was not compiled
or exercised. Its filename remains explicitly GUI-development setup.

## Still required for a tester installer

Package the native host and its providers, replace development-checkout paths,
provide the permitted local generation/import workflow, and integrate the
remaining world/texture/audio content. Then validate a clean-machine installation,
first launch, update and uninstall with preserved user saves/settings/packs.
The original-data installation step now works for the admitted supplied media;
the complete playable installer is not finished.

This change advances user media → verified native-runtime data inputs. It makes
no gameplay/renderer change and earns no native-game acceptance credit. Strict
acceptance remains 131/144. Original media, extracted files and generated game
code remain local; no commit, upload or publication was performed.
