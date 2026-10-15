# Local MW3 music preparation

The native CD-audio service uses the two user-supplied soundtrack FLACs in
`MW3/Music`. It retains the translated game's track selection, music volume,
pause/continue and completion-driven repeat behavior. Cutscene audio remains
part of the existing AVI path; the Intro/Ending FLACs are not CD playlist tracks.

Build the preparation tool with `tools/music/build.ps1`. It uses the existing
compiler and Windows Media Foundation; no package installation is required.
The tool decodes to canonical stereo 16-bit PCM at 44100 Hz. The launcher checks
the exact sample count and the FLAC's decoded PCM checksum before publishing
the cache under `local/remaster/prepared/music`.

The local `local/remaster/music.json` configuration names the decoder and maps
CD track 2 to `1-02. MechWarrior 3 - Track 01.flac`, and CD track 3 to
`1-03. MechWarrior 3 - Track 02.flac`. The original game skips the data slot 1.
Changing these configured source files refreshes the cache on the next launch;
missing or invalid configured sources fail visibly. Setting `enabled` to false
disables the local soundtrack provider.

Both Remaster launchers and the current `Play-MW3.cmd` native build prepare the
music before starting the game. `--check` on the Remaster launcher is read-only;
`--prepare-only` prepares music and graphics without starting a game session.
Direct native diagnostics opt in with `MW34_MUSIC_PACK=<tracklist.bin>`.
`MW34_MUSIC_LOG=<path>` requests bounded playback, gain and hardware-cursor logs.

All original media and decoded music stay local. The source FLACs are unchanged.
