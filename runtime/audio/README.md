# Audio compatibility boundary

The [current plan](../../docs/faithful-modernization-plan.md) treats modern audio
services as part of the native runtime. Preserve the observed guest buffer,
format, playback/cursor, loop, ownership and notification contracts; validate
audible and timing behavior separately from selecting a host library.

The current native host already supplies the observed DirectSound services for
game sound effects through its COM bridge.

`local_cd_audio.hpp` supplies a file-backed CD device when `MW34_MUSIC_PACK`
names a prepared local music manifest. The translated game retains track
selection, playback state and repetition. The provider returns a three-slot
virtual TOC: unplayable data slot 1 and the supplied audio tracks 2/3. Its total
duration describes the available audio, not the unrecovered physical data track.

One native worker owns WaveOut buffers and the real playback cursor. It implements
the original TMSF commands, including continuation via PLAY without FROM, and
posts completion/abort messages to the actual game window. A private AUX device
appears first so the original music slider applies software stereo gain to this
stream. Physical AUX queries retain shifted IDs; their volume writes remain
outside the authorized music boundary. Sound effects and system mixer levels
are unaffected by music gain.

Movie MCI devices retain their existing host boundary. Unknown commands/flags,
malformed media and hardware failures return errors. The local music provider
does not execute guest code on the audio thread or invent successful playback.
See [preparation and launch notes](../../tools/music/README.md).
