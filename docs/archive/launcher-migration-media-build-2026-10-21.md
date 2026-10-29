# Launcher migration and installer extraction dependencies

Launcher **1.0.9-preview is deployed** at the ordinary
`tools/remaster-launcher/MW3RemasterLauncher.exe` location. It replaces the old
1.0.4 GUI, preserving the user's game directory, graphics, music toggle, both
mech packs and their order. The locally authored soundtrack archive was imported
through PackStorage and appended to enabled packs, maintaining existing music
through the new pack contract. The launcher now displays three active packs.
The ordinary GUI is left open on the dashboard; no game or build job is running.

Prior launcher files and exact settings are retained in
`reports/launcher-migration-20261021/before-update/`; the intermediate 1.0.8
entry files are retained in `reports/installer-media-20261021/before-1.0.9/`.
No original game files or selected private host were replaced in this pass.

## Environment selection migration

`EnvironmentPackSelectionInitialized` distinguishes the existing development
setup from an explicit environment-pack selection. Before any environment pack
is discovered/imported, that existing setup retains the published environment
bindings. The Mods page explains this state. Importing/discovering an environment
pack permanently selects the pack workflow, including a deliberately empty
selection after disable/uninstall. Disabled packs do not silently restore the
legacy registry. An installed Runtime always uses explicit pack roots, even on
first launch with no optional packs; it never inherits development content.

This advances the existing GUI upgrade boundary without replacing its visuals.
It is a compatibility migration for the current checkout, not a native execution
fallback. No original-code or interpreter fallback was introduced.

## Source-built media extractor

The new maintained `build_media_tools.ps1` downloads only two pinned open-source
archives, verifies their hashes, builds Unshield with static zlib and MSVC runtime,
runs zlib's CTest suite and emits a payload with both licenses and provenance.
It requires a fresh output directory and never deletes earlier build evidence.

Sources:

- Unshield commit `51de441ba6893f11026d4671ccef9e8e2a4634fa`, archive SHA-256
  `4bb95bd438faa717a05eda658a324562ce4e4243372a5d19e47f7e01634f7fe2`,
  from the [upstream project](https://github.com/twogood/unshield).
- zlib 1.3.2, archive SHA-256
  `bb329a0a2cd0274d05519d61c667c062e06990d72e125ee2dfa8de64f0119d16`,
  published by [zlib](https://zlib.net/).

The tested toolchain was MSVC 19.51.36260.0, Visual Studio 18 2026 generator,
Windows SDK 10.0.26100.0 and CMake 4.3.1-msvc1. Release builds use `/Brepro`.
The initial isolated build and the subsequent fresh maintained-script build
produced the same Unshield SHA-256:
`134d597a3d5d764188acfa57815d96c88c5ce4a8cb135a548fa78917a9fc2cc2`.
This is measured agreement for these two builds, not a guarantee across arbitrary
toolchains. Dependency inspection reports only KERNEL32.dll: neither Python's
zlib1.dll nor the Visual C++ redistributable is an extractor prerequisite.

The maintained script's completed payload is
`local/tools/installer-media-20261021-r2/payload`; its log is
`reports/launcher-migration-20261021/media-build.log`.
`stage_media_tools.ps1` now stages that exact admitted static executable, both
licenses and its provenance. Inno Setup requires those files and excludes the
old development zlib DLL/notice. The exact legacy extractor/DLL pair remains
admitted for retained local trials; arbitrary tools still fail visibly.

## Executed checks and limits

- Full C# launcher suite passes, including environment migration, explicit empty
  installed selections, disabling migrated packs, and rejecting unknown extractors.
- All 13 upstream zlib CTest checks pass in both dependency builds. Both maintained
  PowerShell scripts parse; fresh self-contained 1.0.9 publication/staging passes.
- Actual ISO-plus-patch installation using the new static extractor verified the
  original-data closure in `D:/MW3InstallerMediaTrial-20261021-r1/OriginalGame`.
- Manual GUI check confirmed three active packs, the migration notice, version,
  both original-game setup choices and the optional pack chooser/cancel route.
  No complete install-and-multiple-pack UI transaction was performed; backend
  installation and pack transaction checks are separate evidence.
- Actual Play from the deployed GUI reached the live native menu at the existing
  3440x1440/FXAA/AF16 settings. Its session profile retained legacy environment
  bindings and selected the installed soundtrack registry. Alt+F4 returned native
  exit 0. Evidence is under the per-user sessions directory, session
  `5ebb947303484959be398192fef48d8b`. No frame limit or input script was used.
  This pass does not claim a new Training, audio-quality or fidelity comparison.

The remaining major installer boundary is still the native user-file generation
path. The selected host's build depends on private generated sources, entry/CRT
objects, provider inputs and historical object lists/CMake definitions. The
source-built extractor closes its separate Python-DLL/provenance defect; it
does not make those generated game/codec artifacts distributable. Do not ship
the private runtime as a public payload. Follow with the permitted generation
workflow and clean-Windows install/update/uninstall checks before calling a
Setup.exe playable. No native host/gameplay change, commit or upload was made.
Strict acceptance remains 131/144.
