# Playtest launcher 1.0.41 screenshot directory update

Published October 25, 2026 to the signed playtest update feed and the protected
playtest download page. Native MW3 runtime 1.0.39 is unchanged.

- The launcher now passes the selected, validated MechWarrior 3 installation as
  the native photo/replay root. F9 PNGs save under `<game>/screenshots/`;
  videos and replays use sibling directories.
- Screenshots, Videos and Replays buttons resolve the same selected game folder.
  A missing or invalid game selection produces a visible message instead of
  opening an unrelated launcher-relative directory.
- Existing captures are not moved.

Current filenames:

- Full signed installer: `corecriticalinstaller-1.0.41-preview.exe`.
- Signed launcher update: `1.0.41.ccupdate` and matching `1.0.41.zip`.
- Private download wrapper: `1.0.41-cc-update.zip`.
- Unchanged native update: `1.0.39.mw3update` and `1.0.39.zip`.

The signed catalog sequence is 2026102507. The new metadata and payload passed
full public download, SHA-256 and HTTP Range checks before catalog promotion.
Both private download pages and their catalogs passed R2 readback checks. The
1.0.40 client library discovered only the 1.0.41 launcher update from the live
signed feed. An isolated installed 1.0.40 to 1.0.41 upgrade retained the runtime
and a user fixture; the full installer passed runtime file-hash validation.
The update-notification UI fixture passed default-off, opt-in/out, banner,
gameplay and cleanup checks. External playtester notification remains to be
confirmed on the user's remote system. Automatic checks are optional and off
unless the user enables them in Settings & Steam.

Private local evidence: `D:/CoreCriticalScreenshotRelease-20261025-r1/`.
No running game was stopped and no commit was made. Strict native acceptance
remains 131/144; this changes launcher-managed capture paths, not game logic.

Download links:

- [Full installer](https://playtest.corecritical.dev/installers/2026-10-25-r6/corecriticalinstaller-1.0.41-preview.exe)
- [Launcher update wrapper](https://playtest.corecritical.dev/updates/corecritical-1.0.41/1.0.41-cc-update.zip)
