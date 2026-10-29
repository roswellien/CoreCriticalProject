# Launcher 1.0.45 playtest release preparation

Prepare Core Critical Launcher 1.0.45-preview from reviewed main source. This
document records intended release scope, not a completed publication. Merge the
version preparation into develop, promote through a develop-to-main release PR,
then build and record the exact merged main SHA before signing or publishing.

## Changes and compatibility

The published 1.0.44-preview launcher was built from main commit
45fb81f1dbb16e779f4b6e6f35df1507812f9a3e. Since then, main gained DirectInput
joystick identification and selection controls. A distinct 1.0.45 version lets
existing clients discover the updated launcher without replacing immutable
1.0.44 artifacts with different bytes.

The launcher can save a selected device or None and pass the choice into its
launch profile. The canonical native host does not yet consume that selection;
the selection integration exists in the legacy override source only. Do not
describe selected-device routing as working in the shipped game. Native input
integration and hardware validation remain separate follow-up work.

Retain the approved MW3 native runtime 1.0.44 and its existing signed update.
This launcher release does not rebuild native code or deliver the newer merged
force-feedback startup fix. No native gameplay execution boundary advances.
Original-file verification, optional update checking, settings, saves, packs and
custom game paths must retain their existing behavior. Unmerged crash-reporting
work, local normal-map experiments and native MP4 playback are excluded.

## Artifacts and checks

- Full setup: corecriticalinstaller-1.0.45-preview.exe, retaining runtime 1.0.44.
- Launcher update: 1.0.45.ccupdate and matching 1.0.45.zip.
- Optional offline wrapper: 1.0.45-cc-update.zip.

Before publication, run launcher joystick-selection, controls, installation and
online-update checks, and compile the self-contained Windows x64 launcher.
Verify timestamped Windows signatures and update signatures. Test isolated
installed upgrade and full setup, including preservation of player data and
runtime identity. Keep existing historical objects and protected pack downloads.

Follow docs/launcher-and-website-release.md: upload immutable objects, verify
hashes and range downloads, update protected Setup listings, and promote the
signed online catalog last with a concurrent-change guard. Retain receipts and
the previous catalog. Failed signing, installation, preservation or download
checks block publication. Broader external-PC gameplay coverage remains open.
