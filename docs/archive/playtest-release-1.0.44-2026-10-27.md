# Launcher 1.0.44 playtest release

Release preparation, 2026-10-27. Publish only after the version change is merged
into `develop`, the release PR is merged into `main`, and the exact merged source
has been built, signed and validated. Record the resulting main SHA and artifact
identities in the private release receipt. This document does not assert that
publication is complete.

## Player-visible changes

- The MW5-style factory control layout now includes Ctrl + numpad 0 for the
  original torso-mode toggle. The launcher repairs only an untouched older MW5
  preset; custom names, bindings, cleared controls and the selected layout are
  preserved. Torso mode is saved independently of the key layout and is not
  forcibly reset when switching layouts.
- Game setup verifies required retail files separately from optional support
  tiers. Missing optional files no longer reject an otherwise valid supported
  installation; malformed or incomplete required inputs still fail verification.

## Products and delivery

This is **Core Critical Launcher 1.0.44-preview**, retaining the existing signed
**MW3 native runtime 1.0.44**. There are no new native source changes since the
published runtime, and no native version bump or new `.mw3update` is needed.
The existing runtime update remains available for players who need it.

Expected new downloads:

- `corecriticalinstaller-1.0.44-preview.exe`, including native runtime 1.0.44.
- `1.0.44.ccupdate` with its matching `1.0.44.zip` launcher payload.
- Optional offline wrapper `1.0.44-cc-update.zip`, containing those two files.

Existing users can check for updates in the launcher's Updates window. Automatic
checking remains optional; download/install remains the user's choice. Close the
game before installing. Settings, saves, packs and custom game paths must survive
the upgrade. Fresh installs still require original supported game files or the
user's supported ISO and English 1.2 patch; no compiler/SDK is required.

The cinematic changes in the integration branch are an implementation plan only;
this release does not enable native MP4 playback. Uncommitted local normal-map
experiments are excluded. Original media and optional packs remain separate from
the public update-only feed.

## Required release checks

Run focused controls, installation and online-update checks; publish a fresh
self-contained Windows x64 launcher; validate the retained runtime; verify
timestamped Windows signatures and signed update metadata; test an installed
launcher upgrade and full installer against isolated player-data fixtures; verify
the existing native update/rollback path remains compatible. Preserve the real
installation registration and remove only the explicitly scoped test installs.

Upload immutable versioned objects first, verify hashes and HTTP range downloads,
then promote the signed catalog last with a concurrent-change guard. Retain the
previous feed and setup records for rollback. Block promotion on failed signing,
input verification, user-data preservation, update application, or public readback.
Keep historical downloads and compatibility URLs intact.
