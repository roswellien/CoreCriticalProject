# Cinematic integration assessment

User decision after this assessment: defer integration until the native
recompile is ready. The legacy-hook proposal below is retained as research,
not active implementation work. The current native format proposal is in
[the compression and runtime plan](cinematic-compression-and-runtime-plan.md).

Investigated 2026-10-08 against the identity-verified installed MW3 U.S. 1.2
executable, SHA-256 `95bc2c114c9b2e5c5ada8e40ca78cc79470f862e45313ffad0d1e8e6d4d916bf`.
This is a static feasibility assessment; no cinematic replacement has been
installed or tested in a live game. The game executable and assets were unchanged.

## Findings

The installed `MW3/zbd/reader.zbd` contains the cinematic script references.
The introduction, campaign movie and inspected mission sequences use `PLAYAVI`.
The FMV path is `./video` in Windows path notation. A separate `PLAYMCI` command
exists in the executable, but the inspected cinematic scripts use `PLAYAVI`.
Script names also include videos absent from the admitted disc inventory, such
as `c3m3.avi`; these references do not establish additional available sources.

Private linear disassembly is under
`local/work-ahead/cinematic-integration-assessment/disassembly.txt` and installed
asset string references are in `asset-string-references.json`. Linear disassembly
is evidence for candidate boundaries, not a recovered/validated ABI contract.

Candidate locations, requiring runtime confirmation before patching:

| Address | Static evidence |
| --- | --- |
| `0x599C00` | Movie command object constructor; constructs a pathname, checks the local file, then tries a fallback resolver |
| `0x599DE0` | Movie command update; calculates a frame from elapsed time and the stored movie rate |
| `0x59A4A0` | AVI playback object constructor; initializes AVIFile, audio and video streams |
| `0x59A650` | Opens video via AVIStreamOpenFromFileA, reads AVI headers, locates a VfW decompressor, allocates buffers |
| `0x59A900` | Opens the AVI audio stream |
| `0x59AAF0` | Reads a compressed video frame and calls ICDecompress |
| `0x59B080` | Separate MCI playback path; requests the MPEGVideo device |

Imports agree with these call sites: AVIFIL32 AVIStream functions, MSVFW32
ICLocate/ICDecompress and WINMM mciSendCommandA. Header-derived dimensions and
rate are used. There is no proven blanket 640x480 or 15 fps restriction in this
decoder initialization, but downstream rendering, audio synchronization and
display-mode constraints remain unverified.

The existing downloads are H.264/AAC MP4s. Simply renaming them to `.avi` does
not establish compatibility with the AVI/VfW stream and codec contracts.
Microsoft describes AVIStreamOpenFromFile as an AVI stream opener and recommends
Source Reader for new media processing code:
[AVI stream API](https://learn.microsoft.com/windows/win32/api/vfw/nf-vfw-avistreamopenfromfilew),
[modern replacement guidance](https://learn.microsoft.com/en-us/windows/win32/multimedia/opening-and-closing-files).

## Recommended implementation

Build an opt-in cinematic playback replacement for the original game first.
The full native recompiled game is not yet available. Reuse the project's
hash-bound launcher/in-memory hook infrastructure, but recover and validate
the movie command lifecycle and ABI independently of the existing integer hook.

1. Trace one original INTRO playback: resolved path, construction/update/end,
   skip controls, audio start/stop and rendering/display transitions. Recover
   object ownership, calling convention, return values and floating-point state
   obligations before installing a replacement.
2. Add an explicit filename map from requested original AVI names to the 19
   completed MP4s in a separate enhancement directory. Validate files and keep
   original playback available when replacements are missing or disabled.
3. Implement modern H.264/AAC decoding and presentation. Media Foundation is a
   Windows candidate; its Source Reader supports hardware decoding through DXVA:
   [Source Reader processing](https://learn.microsoft.com/en-us/windows/win32/medfound/processing-media-data-with-the-source-reader).
   Source Reader alone is not a complete player: supply audio output, scheduling,
   presentation and error handling. A 32-bit in-process implementation fits the
   original executable; a separate player process would need explicit lifecycle
   and window coordination.
4. Present at the actual monitor/window resolution with 4:3 aspect preservation
   and pillarboxing on wider displays. Recover interactions with the legacy
   DirectDraw/dgVoodoo display before choosing an overlay or separate surface.
   Decoding UHD frames into a 640x480 game backbuffer would lose the detail we
   want to preserve. Fullscreen ownership, focus and surface restoration are
   central parts of the prototype.
5. Preserve script completion semantics, skip, audio volume, focus behavior and
   return to menus/gameplay. Verify timing against real audio playback, including
   movie endpoints, rather than merely advancing the old 15 fps frame loop.
6. Prove INTRO plays at 30 fps and returns cleanly, then prove one mission movie
   and the final victory movie. Exercise all 19 mappings, missing-file fallback,
   repeat playback, skip and fullscreen/windowed modes before broad installation.

The current MP4s total 5139045810 bytes including INTRO (about 4.79 GiB); the
replacement player can reuse them without another upscale or encode. Lossless
masters remain archival inputs rather than the normal in-game playback package.

## Alternative: legacy AVI compatibility experiment

A short 30 fps AVI export with PCM audio and an available 32-bit VfW decoder
could test how much of the old player accepts larger frames. Codec availability
and output color format must be verified. This may reduce hook work but could
require another encode, larger downloads and rendering changes anyway. Test a
single short clip in an isolated game copy before making a complete AVI set.
Do not assume that H.264 remuxing, system codec installation or changing the
extension makes the current files compatible.

## Scope and remaining uncertainty

This is a moderate playback integration project, not a file-copy-only change.
The first deliverable should be a reversible INTRO playback proof using the
existing upgraded MP4. An effort estimate should follow the runtime trace and
display restoration prototype; static analysis cannot establish those costs.
No new AI processing is required. Full-speed visual review of the interpolated
movies remains pending independently of this integration work.
