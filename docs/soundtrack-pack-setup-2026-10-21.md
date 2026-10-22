# Soundtrack packs and first-run content selection

Launcher 1.0.7-preview consumes soundtrack `.mw3pack` files through the same
**Mods & Packs → Install Pack** action as other content. This supersedes the
individual-track selection UI described in the earlier installed-content trial.
Setup no longer asks players to choose individual audio files.

The first enabled soundtrack in pack order wins. Conflict inspection reports
competing soundtracks. The soundtrack setting and original in-game music controls
still apply. No enabled soundtrack means music off, including in development
launches of the updated GUI; an old private music configuration cannot silently
override a disabled pack. Legacy stored individual-track paths are retained in
settings for compatibility but the updated runner does not use them.

## Authoring contract

The archive has root `pack.json`, schema 2, ordinary pack identity/name/version,
`provides: {"cd_music": true}`, a size/SHA-256 file table, and:

```json
"native_payload": {
  "profile": "prepared-music-v1",
  "registry": "music/music.json",
  "path_base": "pack-root"
}
```

`music/music.json` contains:

```json
{
  "schema_version": 2,
  "payload_profile": "prepared-music-v1",
  "tracks": [
    {"cd_track": 2, "source": "music/track02.flac"},
    {"cd_track": 3, "source": "music/track03.flac"}
  ]
}
```

Both distinct audio sources and the registry must appear in the file table.
Sources can be FLAC or stereo 16-bit/44100 Hz PCM WAV. Archive traversal, links,
undeclared files, hash mismatches, missing tracks and wrong track order are
rejected. Registry and audio integrity are checked again when selecting music
for launch. Packs supply data, never a decoder program or arbitrary command.
WAV needs no decoder; FLAC uses the runtime's local decoder and existing PCM
verification. Preparation caches belong to writable user storage.

`tools/remaster-launcher/build_music_pack.py` authors this contract using
`--track-2`, `--track-3`, `--output` and optional `--id`/`--name`. It refuses to
overwrite an existing output and leaves original sources unchanged. Community
authors use their own pack identity and audio they are entitled to distribute.
Format support does not change the project's original-content distribution rules.

## Next installer step implemented

The original-game setup page now allows optional multi-selection of `.mw3pack`
files. After verifying an existing installation or importing the ISO and patch,
the launcher installs those packs through the same verified importer. Players
can select soundtrack, mech and environment packs in one setup visit or add them
later. Every successful pack import immediately persists enabled selection;
if a later import fails, verified game data and completed imports remain usable
and the error directs the player to retry through Install Pack. A previously
disabled pack remains disabled when updated, matching ordinary pack imports.

## Validation and staging

The full C# launcher suite passes, including new authored soundtrack archive
checks for installation, precedence/conflicts, music off, absent optional packs,
corruption and path escape. Twenty Python checks pass across soundtrack authoring,
installed music/cache repair, dispatch, installed runtime and prepared packs.
The WPF GUI publishes self-contained; media tools are staged alongside it at
`reports/soundtrack-pack-20261021/launcher`. The first-run UI compiles; its new
multi-pack interaction has not yet received a complete manual UI test.

A local user-supplied soundtrack pack is at
`local/asset-packs/soundtrack-20261021-r1/CD-Audio-Soundtrack.mw3pack`.
It was installed through the actual C# importer into
`D:/MW3SoundtrackTrial-20261021-r1/mods/com.mw3remaster.cd-audio`.
The resolved registry was prepared by the external installed runtime's Python
and decoder, writing its tracklist/PCM to an external user cache.

The subsequent bounded native run used the pack-derived music inputs with the
previously tested mech/environment selection. Evidence is under
`D:/MW3SoundtrackTrial-20261021-r1/training-session/native`.
It reached Training, presented all 340 requested frames through Vulkan and
issued music play commands for tracks 2 and 3. Its exit 1 is the explicit frame
budget stop, not normal quit or an unresolved service repair. No subjective
audio-quality claim or gameplay/fidelity acceptance follows from this check.

The ordinary 1.0.4 GUI files, global pack installation and graphics settings were
not replaced. That old GUI cannot install this new soundtrack contract; use the
staged 1.0.7 code only with the appropriate content-selection migration. The
current soundtrack and native runtime artifacts stay local under `docs/legal.md`.

Remaining gates: migrate the legacy development environment selection before
replacing that GUI, finish the permitted user-file generation/build path and
dependency provenance, then assemble and test actual installation/update/
uninstall on clean Windows. There is still no complete shareable game Setup.exe.
No native host or gameplay code changed in this follow-up. Acceptance remains
131/144; no commit, upload or publication was performed.
