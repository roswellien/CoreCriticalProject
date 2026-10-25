# CD-audio startup repair and default soundtrack — 1.0.33

The 1.0.32 clean-install report `MW3-Playtest-20261024-125757.zip` stops at
`0x001df74c` with `auxSetVolume would change the host CD-audio mixer level`.
The report has no packs, music enabled, and 1920x1080/FXAA/16x AF. The owner
confirmed the ISO lacks the separate CD soundtrack and requested default
soundtrack delivery. Effects/speech in the original data archives are a separate
audio path; this report identifies the CD volume adapter.

## Cause and repair

Without local soundtrack files, the private PCM CD device is absent. An invalid
or absent AUX volume-device request was nevertheless reaching the fatal guard
against physical host mixer writes. Running the previous signed host without
`MW34_MUSIC_PACK` reproduces the exact reported address, volume and error.
The dev setup normally has original CD tracks available, enabling its private
device and taking the successful branch instead.

`runtime/audio/local_cd_audio.hpp` now provides bounded host-AUX ID validation,
including the private device's one-position enumeration shift. The maintained
native `mfc_stage.hpp` adapter returns `MMSYSERR_BADDEVICEID` for absent/invalid
volume-device IDs. It does not claim successful volume changes or call a physical
volume setter. Requests to an actual host mixer remain blocked; private CD
volume continues through the existing PCM player's worker.

This follows the [WinMM auxSetVolume contract](https://learn.microsoft.com/en-us/windows/win32/api/mmeapi/nf-mmeapi-auxsetvolume).
The repaired execution boundary is guest WinMM device/error handling, not game
logic or a replacement music API. No backend fallback or AFTER-state seeding.

## Default base-game soundtrack

The owner-requested private installer/update now includes the same two verified
original CD tracks already distributed by the approved protected
`CD-Audio-Soundtrack.mw3pack`. The source pack SHA256 is
`b3c1c84cd95cd2e945ba879a06e6633097bfe10932fc6c34ee78da191409fb4c`;
the two FLAC files total 24,818,236 bytes. The other intro/ending FLAC files,
disc images and game-data archives are not bundled. The scoped distribution
instruction is recorded in `docs/legal.md`; audio remains outside Git.

The component resides under `Runtime/resources/stock-soundtrack`, not the
user's enabled mod list. `MusicPack.Apply` uses this priority when music is on:
an explicitly enabled replacement pack, original tracks in the chosen game's
Music folder, then the bundled default. With music off, none is selected. It
validates component metadata, registry and track hashes, using the existing
runtime decoder. Corrupt components fail visibly; legacy runtimes without the
component keep their previous behavior. Runtime staging preserves the binding.

The cumulative game update `mw3-cd-audio-20261024-r1` and launcher 1.0.33 use
sequence 2026102408 in their separate state domains. **The game update requires
launcher 1.0.33+** for the bundled component selection. The full installer
contains both; no separate soundtrack pack or game update is needed after a
fresh install. The translated game module remains unchanged. Signed host SHA256:
`77461fadb550efa3cb950b43e10d30c7875b53e44151cb97daa57cd98e8cda15`.

## Verification and limits

Private evidence: `D:/MW3AuxAudioRepair-20261024-r1`.

- Parent native source pins verified; exactly `mfc_stage.hpp` and
  `audio/local_cd_audio.hpp` change among the 150 frozen source files. The
  original translated module and linked supporting objects are reused.
- Audio fake-driver tests report zero failures, including AUX sentinel,
  absent/shifted/unshifted boundaries and exact private stereo-volume storage.
  Existing worker wait, output, shutdown, notification and cursor tests pass.
- Full launcher fixtures pass, including bundled-default selection without
  packs, replacement priority, original-file priority, disabled music and
  corrupt registry rejection. Previous first-run wizard behavior is retained.
- The old native host reproduces the reported startup fault without music.
  The fixed host presents 150 menu frames and 500 Training frames without
  music. With decoded bundled music, it presents 500 Training frames and logs
  real nonzero PCM completion plus the original private volume/seek/play calls.
  The native runs end with the deliberately requested frame-budget exception
  (exit 1), not an interactive-quit success claim.
- The actual freshly installed 1.0.33 launcher selects and prepares the bundled
  tracks with no original Music folder and no enabled packs. Its installed
  embedded coordinator decodes/verifies the music; the off case creates no
  tracklist. This avoids relying on music present only in the dev environment.
- Signed full setup passes fresh isolated installation and all 664 runtime
  hashes. An actual installed 1.0.32 updater verifies/stages the signed 1.0.33
  launcher upgrade; runtime/user fixtures are preserved. Signed cumulative
  game installation/activation/validation/rollback passes from the older
  controller runtime and the published 1.0.32 runtime. Uninstall registration
  is restored after tests.
- Retained harness failures include omitted adjacent DLLs, using an executable
  basename incompatible with translated-module imports, and an update test
  correctly rejected while the bounded game test was still running. These
  were corrected before final validation and are not counted as passing runs.

Separate clean-Windows retesting, all campaign missions and automatic updater
helper/restart UI remain unverified. Formal native acceptance remains 131/144.
No performance improvement is claimed from these checks.

## Protected playtest publication

- [Full signed 1.0.33 installer](https://playtest.corecritical.dev/installers/2026-10-24-r5/corecriticalinstaller.exe)
- [Launcher update bundle](https://playtest.corecritical.dev/updates/corecritical-1.0.33/CoreCriticalLauncherUpdate.zip)
- [Cumulative native/audio update](https://playtest.corecritical.dev/updates/mw3-cd-audio-20261024-r1/CoreCriticalGameUpdate.zip)

Publication receipts and final link/Access checks are retained in the private
root. Setup catalog replacement preserves all other content/media rows and
checks for concurrent changes. Original game verification remains required.
The existing owner-approved individual signing identity is unchanged. No Git
commit/push is made by this work.
