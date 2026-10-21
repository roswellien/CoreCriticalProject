# Mod Tools setup

The Mod Tools source preview is separate from the Game / Launcher. It contains
the desktop editor and browser Studio source, not a native game executable,
original archives, extracted preview models or ready-to-share mission packs.
The desktop editing slice is further along than Studio's map-play workflow.

## Requirements

- Windows x64 and CPython 3.11–3.14, including Tkinter and the Python launcher
  or `python` on PATH. The initial setup needs Internet access to PyPI for Pillow.
- Your legally obtained MW3 installation, outside the extracted tools folder.
  Setup checks for `zbd/reader.zbd` and `zbd/rimage.zbd`; mission operations need
  their own GameZ/reader archives. This archive check is not native game admission.
- The extracted Windows x64 **Mech3AX v0.7.0-rc3** conversion tools, obtained from
  [TerranMechworks' releases](https://github.com/TerranMechworks/mech3ax/releases).
  Keep its EUPL-1.2 license and distribution together. We do not bundle or download
  these binaries automatically. Setup requires the recorded `unzbd.exe` and
  `rezbd.exe` hashes; a different build fails instead of being silently accepted.

The source preview preserves the repository layout so relative imports and
documentation work. Extract it into a writable folder such as
`C:\Games\MW3 Mod Tools`, outside your original installation.

## Configure the desktop editor

From the extracted folder, open a terminal and run:

```powershell
& ".\Setup Mod Tools.cmd" --game-root "C:\Games\MechWarrior 3" --mech3ax-dir "C:\Tools\mech3ax-v0.7.0-rc3"
```

Use the actual folders on your machine. Setup creates only a dedicated
`.venv-mod-tools` Python environment and `local/mod-tools/settings.json`. It
installs hash-pinned Pillow 12.3.0 Windows wheels in that environment, tests a
real image operation and checks Tkinter. It does not change global Python,
extract game content or write to your original installation. Existing source
archives and working developer game/launcher profiles are untouched.

Check an existing setup without installing or changing settings:

```powershell
& ".\Setup Mod Tools.cmd" --check
```

Launch `Play MW3 - Mission Editor.cmd`. The configured game folder is used from
any working directory; `--game-root` can override it for a session. The existing
operation/mission options, for example `--operation c1 --mission c1m1`, remain
available. Extraction caches live in `local/mod-tools/cache` under a folder for
the selected installation; desktop exports go to
`local/mods`, and saved project locations are chosen in the editor.

## Visual Map Studio limitations

`Play MW3 - Visual Map Studio.cmd` starts a loopback-only HTTP preview and opens
the local address in a browser. Its Three.js renderer and license are included.
Real MW3 preview geometry is generated locally from your own archives and is
intentionally absent from the package. An empty/missing preview asset catalog
must not be represented as a complete in-game asset browser.

Studio export currently also depends on extracted operation caches; its native
play command still targets prepared development profiles. Setup does not create
those caches or make the play button a portable game installer. Do not expose
the server to a LAN. Full custom mission loading, objectives, enemies, save/load
and completion need separate native validation. A successful HTTP export is
not that validation.

## Updating, removing and sharing

Close the editors before updating. Keep your `local/` folder and authored project
files; extract updated source separately if comparing versions. Rerun setup when
dependency pins or paths change. Removing the extracted tools folder removes its
environment/caches; save projects and exports elsewhere first. The original game
and externally installed Mech3AX are independent and must not be removed by setup.

Exported ZBD archives incorporate game content and remain local under the
[distribution policy](legal.md). Share only reviewed authored changes and
references whose distribution is allowed. The package builder includes source
and notices from an explicit file list, not `local/`, extracted geometry,
game installs, caches, exported maps or development binaries.

See [the online code guide](https://github.com/roswellien/MW3Recomp/blob/main/docs/code-guide.md),
[format matrix](../games/mw3/mod-tools/docs/format-support-matrix.md) and
[release readiness](https://github.com/roswellien/MW3Recomp/blob/main/docs/public-release-readiness.md).
This setup advances editor
configuration/dependency preparation; it does not advance native-game acceptance.
