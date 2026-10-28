# Launcher preparation for playtesting

Local build 1.0.3-preview, October 21, 2026. This advances the installed launcher's
settings/session/error-reporting boundary. Native gameplay and strict acceptance
remain unchanged at 131/144. The standalone game installer is still incomplete.

## Available now

- Launch from the existing MechWarrior 3 Remastered shortcut. Existing shortcuts
  still target `tools/remaster-launcher/MW3RemasterLauncher.exe`; that local binary
  has been updated and its prior version/settings retained under ignored
  `local/work-ahead/playtest-support-20261021-r1/`.
- Settings migrate once from the application-local `user/settings.json` into
  `%LOCALAPPDATA%/MW3Remaster/settings.json`. Later installs do not reimport older
  choices. Saves use an atomic replacement and retain `.previous`; invalid JSON
  is backed up before defaults can be saved, with a visible recovery message.
  This moves launcher settings, not original-game save files.
- Native launch snapshots, logs and game diagnostic output live in a unique
  `%LOCALAPPDATA%/MW3Remaster/sessions/<id>/` directory. Prepared-asset caches live
  under its sibling `cache/`. Early failures create a log before validation or
  serialization. CLI/research launches retain their previous output defaults.
- **Settings & Steam → Open Logs** opens the latest native session.
  **Export Report...** creates a local ZIP containing only report.json and up to
  64 KiB each of launcher/stdout/stderr tails. Metadata includes launcher/system
  versions, selected display settings and pack IDs/versions/order. Paths are
  redacted. Profiles, game paths as metadata, saves, archives, media, executables,
  dumps and recursive content are excluded. Review the report before sharing;
  nothing is uploaded automatically.
- Launch failures display the recorded cause. Already-exited coordinators are
  observed correctly; output is drained before the failure summary is read.
  Native preparation/game activity disables pack mutation, and ordinary exit
  restores the Play button.
- The settings page scrolls and displays the launcher build. Disc-media import
  describes its limited scope instead of claiming a complete standalone install.

The Inno GUI-installer source now uses a writable per-user application directory
and preserves both persistent and legacy settings during updates. It no longer
offers a pack checkbox that merely copied an archive into a directory the new
launcher does not auto-import. Packs use **Mods & Packs → Install New Pack...**.
Its former nonterminating backslash replacement was replaced by a one-pass JSON
path escape. The installer was not compiled: Inno Setup is not installed locally.
These source changes do not make its payload a complete game installer.

## Validation

- C# build/publish and launcher checks passed, including migration with exact
  original bytes preserved, newer persistent choices winning over an older
  installation, removal of an authored old app directory, repeated atomic save,
  corrupt-settings recovery, prelaunch failure logs, bounded/redacted exports,
  allowlisted ZIP contents and an already-exited process returning its real code.
- Six Python pack-composition and six dispatch checks passed. PowerShell's parser
  accepted the changed native coordinator.
- The deployed GUI's actual Play button launched the current native host in
  session `efff0cd88fb54d95aeeadcf87de510ff`. The intro and live main menu displayed;
  a normal Alt+F4 window-close request returned exit 0. Play became available again.
  No frame budget or production fallback was used. Native logs and run.json were
  produced beneath the same per-user session. This is a startup/quit check, not
  additional Training/combat/save-load validation.
- Actual legacy settings compared equal after migration, and the legacy file was
  unchanged. The support page and save dialog were exercised in the deployed UI;
  the dialog was canceled during automation. The same compiled exporter then
  produced an inspected real-session report at ignored
  `reports/playtest-support-20261021/support-report.zip`: four allowlisted entries,
  2,658 bytes, no checked personal/project path strings and no GamePath metadata.

The installed test also exposed Windows MSIX file redirection: resolving an
existing manifest returned a physical path while resolving its parent directory
returned the logical path. Pack loading now rejects links first and anchors its
strict descendant checks to the manifest's physical parent. It does not allow
per-file path escapes. A regression checks manifest anchoring and traversal
rejection; installed content was verified through the actual redirected path.

The selected host had advanced to
`bf9c4b5e3e626ea542a52100325508897a22355c82dbb22680b90273cce62b44` through the
separate fixture-UV work. Its executable and snapshot were rehashed. The pinned
mesh_override_stage.inc, material_normals.hpp and donor_runtime.inc hashes match
the three previously reviewed mech readers exactly; that one host identity was
added to the explicit admission set. Future changed hosts are still rejected
until reviewed. No renderer source or selected graphics profile was altered.

## Remaining before sending a standalone playtest installer

1. Finish the installed native runtime/import or generation path. The current
   host still requires the private checkout, staged providers and generated
   inputs. The GUI installer alone cannot supply that path.
2. Package and integrate the remaining content families. Two mech collections
   are installed; environment/world/audio content still comes from the authored
   development profile. The 39 configured texture archives currently occupy
   28,398,717,910 bytes (~26.4 GiB) expanded, so examine a sparse replacement/import
   format before copying whole development banks into a tester package. No large
   content compression job was started and no extra content packs were produced.
3. Complete prerequisite deployment and clean-machine setup/update/uninstall.
   The [1.0.4 follow-up](installer-original-game-setup-2026-10-21.md) replaces the
   old media importer with verified existing-folder and ISO-plus-patch setup,
   tested against the supplied U.S. retail media. Broader locale admission and
   the complete playable installer remain open. Preserve original files and saves.
4. Exercise sustained Training/campaign, save/load, input/audio and supported
   graphics/device configurations. Bug reports should include build, mission,
   reproduction steps, expected/actual result and the reviewed local report.

Original media, prepared assets, native generated code and local diagnostic
artifacts remain local under the existing distribution policy. Nothing was
committed, uploaded or published by this preparation pass.
