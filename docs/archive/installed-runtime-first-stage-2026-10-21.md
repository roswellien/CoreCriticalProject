# Installed runtime: first local integration

The first installed-layout boundary now works: the C# launcher runner selected
an application-local runtime, started its bundled Python and native host, reached
the actual live main menu, and returned exit code 0 after a normal Alt+F4 close.
No game-original execution fallback was used. This is a local integration trial,
not a completed installer or a distributable package.

## What changed

`Core/NativeRuntimeLayout.cs` reads `Runtime/runtime.json` beside the application.
Its entry files have size/SHA-256 pins. Explicit `@runtime/` paths resolve inside
that runtime; `@game/` inputs resolve inside the selected original-data folder.
Traversal and linked paths are rejected. A present but incomplete runtime fails
visibly instead of searching for a development checkout. Existing development
launches remain available when no installed Runtime directory exists.

The coordinator and PowerShell helpers accept an explicit runtime root and find
each other beside the coordinator. Installed startup takes its entry-object,
CRT-pack and user-provider paths from the profile. It requires the existing
host-initialized loader mode. The old original-process `before-inputs.bin` is
neither staged nor read in this mode; the unused CLI slot is `host-initialized`.
The selected original executable also overrides `MW34_GAME_EXE`, so file-service
lookups cannot retain a developer's old game-directory binding.

The ISO importer now extracts the exact admitted CRT provider from the user's
cabinet into `native-inputs/MSVCRT.DLL`. It is read as native-host input data,
not executed as an original-game process. Fresh ISO installation produced 148
verified files including this provider. It is not bundled as project-owned data.

The isolated launch found a concrete empty-selection defect: preparation bound
an MWBANK1 index with count zero, while the native reader rejects count zero.
Both asset and environment preparation now omit that binding for empty
selections, retaining the original archive reader. The regression tests exercise
the real preparation functions with authored empty inputs and no Pillow.

## Trial and evidence

`stage_native_runtime.py` creates a fresh, explicitly private trial directory.
It copies stable inputs with integrity checks, relocates paged catalogs, bundles
a local standard-library Python runtime, and writes the runtime file table.
It deliberately selects original archives/models and no CD music. It never
rewrites the published development profile or persistent player settings.
This is a diagnostic configuration, not a change to the normal playtest visuals.

The completed runtime trial is at `D:/MW3InstallTrial-20261021-r2/App/Runtime`.
The first original-data trial is outside the checkout at
`D:/MW3InstallTrial-20261021-r1/OriginalGame`; a second ISO import, including the
new provider import, is at `D:/MW3InstallTrial-20261021-r2/OriginalGame`.

The C# `GameRunner` trial used its installed-runtime branch, original data from
the first external directory, and private user state under the second trial's
`UserData`. It did not run repository discovery or use the Codex Python runtime.
The actual coordinator and host working root was the external Runtime directory.
The resolved launch profiles contain no checkout or Codex workspace paths.
The host/source snapshot identity is
`a16f28ad4e16abb13095d2e34d991a8577303375d6eab0399477afd1f084313b`.

Successful session:
`D:/MW3InstallTrial-20261021-r2/UserData/sessions/9c5fd13ad44b49eeae530d78741e1cbb/`.
The actual Windows game window showed the live main menu. Normal Alt+F4 shutdown
returned exit 0 through native host, coordinator and C# runner. No frame budget
or input script was used. Failed initial trials and their logs remain preserved.
This was not an OS-enforced denial of checkout access or a clean-machine test;
the initiating test harness itself ran from the checkout.

Checks passed: C# launcher suite (including installed discovery, damaged/missing
entry files, containment, nested-array profile resolution and captured-startup
rejection); Python dispatch, mech-pack, environment-pack and new empty-selection
tests; PowerShell parsing; fresh original ISO installation. A self-contained
1.0.5-preview launcher publication is staged under
`reports/installed-runtime-20261021/launcher` and copied into the external trial
App folder. The normal open launcher and its settings were not replaced.

## Next implementation boundaries

1. Resolve provider acquisition for the existing-installation-only route. An
   ordinary original installation may not retain the admitted legacy CRT DLL;
   it must be imported from user-supplied media rather than shipped silently.
2. Connect installed music inputs and a writable music cache. Installed launch
   now fails visibly if CD music is requested without its configuration. This
   trial explicitly disables music; the ordinary player setting was preserved.
3. Exercise installed mech/environment packs, compatible host admissions and
   final visuals in this layout. Reuse the separately developed environment-pack
   loader; do not copy 26 GiB of development texture banks into the base installer.
4. Replace the remaining local generated-host/CRT build inputs with the permitted
   generation/import workflow, complete dependency notices/build provenance,
   compile Inno Setup, and test actual installation, update and uninstall on a
   clean Windows machine. The external trial contains local generated/derived
   artifacts and is not eligible for distribution under current policy.

This advances application-local native startup and user-data path binding.
It changes no gameplay/renderer implementation and adds no native-game acceptance
credit. Strict acceptance remains 131/144. No Training or campaign fidelity is
claimed. No files were committed, uploaded or published.
