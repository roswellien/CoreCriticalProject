# Visible installer defaults — launcher 1.0.36

The owner selected this layout on October 25, 2026:

- Launcher: `C:\Games\Core Critical\Launcher`
- Original game files: `C:\Games\Core Critical\MechWarrior 3`

Use the Windows system drive rather than assuming it is always C:. Both paths
remain editable. If the launcher uses the standard `Core Critical\Launcher`
layout on another drive, game setup suggests its sibling `MechWarrior 3`
directory there. An arbitrary application folder, including Program Files or
a development build tree, is not used as the game library root.

Previously the installer suggested hidden Local AppData under
`Programs\MW3Remaster`, and first-run game setup suggested the launcher's
hidden data directory plus `OriginalGame`. The folder picker also used the
internal name `MW3-Original`. These are replaced with the visible product/game
names. Logs, preferences and pack state retain their established per-user
location; changing defaults does not move or delete existing content.

`UsePreviousAppDir=yes` is explicit in the Inno installer. Existing installs
retain their previous application directory, and `.ccupdate` installation
continues to pass the exact existing application path. Existing game selection
remains in settings and the setup wizard's existing-installation field.

Execution boundary: installer destination selection and first-run game-folder
suggestion. No native game code or gameplay change; acceptance stays 131/144.
The full installer retains the published stable runtime 1.0.34. It does not
promote the separate 1.0.35 DPI retest candidate or replace ongoing DEV native
work. Launcher version is 1.0.36-preview, update sequence 2026102501.

Evidence is retained at `D:/CoreCriticalInstallPaths-20261025-r1`:

- Full launcher fixtures and the actual four-step WPF setup check pass,
  including source validation, review, cancellation and saved choices.
- An isolated actual setup-control check verifies the visible default,
  preservation of an explicitly supplied game path and user-edited destination,
  alternate-drive library handling and protected-application-folder fallback.
- Full signed installer is tested in a fresh private directory with all
  registered runtime-file hashes checked. Launcher-only upgrade uses an
  isolated installed 1.0.34 baseline; uninstall registration is restored.
- The actual installed 1.0.34 updater verifies and stages the signed 1.0.36
  package. Its signed launcher-only installer is then run without `/DIR`,
  proving that Inno reuses the previous path despite the changed fresh default.
  The installed launcher matches the fresh 1.0.36 build, runtime hashes are
  unchanged by the launcher-only update and the user fixture is preserved.
- Update attempts rejected while video-capture game processes were active are
  retained as failed/interrupted checks. No game session was terminated.

The versioned installer is `corecriticalinstaller-1.0.36-preview.exe`.
The launcher update is `1.0.36.ccupdate` with matching `1.0.36.zip`, delivered
inside `1.0.36-cc-update.zip`. Signing and publication receipts are retained
with private evidence. No commit is made.

Release links:

- [Full signed installer](https://playtest.corecritical.dev/installers/2026-10-25-r1/corecriticalinstaller-1.0.36-preview.exe)
- [Launcher update](https://playtest.corecritical.dev/updates/corecritical-1.0.36/1.0.36-cc-update.zip)

Both catalog edits preserve the existing game update and all asset/media rows.
Publication is recorded by the private completion receipt after full R2
readback and Access checks. The separate clean-Windows test and automatic
updater-helper restart UI are not claimed by the isolated installation checks.
