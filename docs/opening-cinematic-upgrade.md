# MechWarrior 3 opening cinematic upgrade

Started 2026-10-08 at the user's request. This project resumes the opening
movie selected in the [video pilot](work-ahead-video-pilot.md).

## Scope

Upgrade the complete `VIDEO/INTRO.AVI;1` with the previously selected general
Real-ESRGAN 4x model through the installed Video2X workflow. Retain a
2560x1920 intermediate and resize with Lanczos to 2880x2160 for 4:3 playback
on a UHD display. Preserve the original 2737 display frames at 15/1 fps,
framing, scene order, and stereo 22050 Hz 16-bit PCM. No motion interpolation.

## Current state

Later visual review: the user reported unreadable text in two opening sections.
The defect is reproduced in the lossless general-model upscale. The current
movie requires revision before visual acceptance; technical checks below remain
valid. See [text restoration review](opening-cinematic-text-restoration-review.md).

The complete movie upgrade finished on 2026-10-08. The source ISO and opening
movie identities matched the existing inventory. Media stays in ignored
`local/work-ahead/opening-cinematic-v1/`; the game installation was not modified.
The video queue records completion with perceptual review pending.

| Output | Size | State |
| --- | --- | --- |
| `reference.mkv` | 640x480 | Lossless decoded reference, validated |
| `ai-general4x-intermediate.mkv` | 2560x1920 | General-model AI result, validated |
| `opening-2160p-master.mkv` | 2880x2160 | FFV1 and original stereo PCM, validated |
| `opening-2160p-review.mp4` | 2880x2160 | H.264 CRF 16, slow preset, AAC review export |
| `original-review.mp4` | 640x480 | Matching original-quality browser comparison |

All five outputs contain 2737 display frames on the 15/1 grid. The lossless
reference, intermediate and final master retain all 4,023,397 stereo PCM sample
frames, including the seven-sample tail. Their decoded PCM is byte-identical to
the source, SHA-256
`27e76684cec7fe93684d2ba9bf16fde87c245c52006626fa0efe7e909f8d68f6`.
Maximum master frame timestamp error is 0.333334 ms; maximum continuous audio
timestamp error is 0.480726 ms, within the Matroska millisecond rounding limit.

The AI tool reported 30 minutes 55 seconds; measured command elapsed time was
1856.64 seconds. Final lossless resizing took 55.46 seconds. Validation and
browser encoding added time. `processing.json` records exact argument vectors,
tool/model identities, elapsed times and output hashes. `manifest.json` records
the final project state. The original and upgraded previews have identical AAC
payload hashes, confirmed in `review-validation.json`.

`review.html` supplies synchronized original/upgraded playback and a fullscreen
upgraded view. All five local resource references were checked. Browser navigation
to a temporary localhost server timed out, so browser rendering was not verified;
the temporary server was stopped. The upgraded MP4 is also available directly.
Four new authored timeline/audio/identity tests and ten existing video tests pass.
The existing tests used workspace-local temporary storage because the default
sandbox temporary directory denied fixture writes.

## Work and acceptance

1. Add full-movie preparation and validation. The current five-second pilot
   extractor has a 64 MiB limit and accepts mono 8-bit audio, so it cannot be
   reused unchanged for this movie. Keep that pilot's contract intact.
2. Decode a lossless reference, reconstructing Indeo display holds on the
   original 15/1 grid. Verify decoded audio against the source; preserve the
   header-reported 4,023,397 stereo sample frames, including its seven-sample
   tail beyond the video. Treat header values as expectations until decoded.
3. Run the selected general 4x model, record actual elapsed time and tool/model
   identities, and produce the 2880x2160 FFV1 master with original PCM.
4. Export a separate H.264/AAC comparison for browser review. Check complete
   frame count, dimensions, frame timestamps, audio continuity, and exact master
   PCM identity. Keep source and lossless intermediates for reproducibility.
5. Review the entire movie at full speed for flicker, halos, lettering drift,
   scene-transition artifacts, and audio synchronization. Review failures
   require revised settings before replacement use.

The lossless master, browser comparison, provenance manifest and technical
validation report are complete. Steps 1–4 above are complete. Full-speed
perceptual review in step 5 remains pending.

Game replacement routing, skip behavior, and fallback remain a later playback
integration milestone. All proprietary media stays under ignored `local/`.

A separate [30 fps motion-interpolation pilot](opening-cinematic-30fps-pilot.md)
provides matched 15.2-second 15/30 fps review exports. The user selected that
method and the [full 30 fps opening](opening-cinematic-30fps-full.md) is now
complete and technically validated, with a separate lossless master and
full-quality remote download. The earlier 15 fps master remains available.
Whole-movie perceptual review and playback integration remain pending.
