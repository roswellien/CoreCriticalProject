# Five-second video upscaling pilot

Recorded 2026-10-07, following [disc-video discovery](work-ahead-enhancement-experiment.md).
The user selected video upscaling and requested a shorter first test. The shortest
complete disc clip is `VIDEO/C2M1.AVI;1`, 379 frames and 25.266667 seconds, so this
pilot uses its first five seconds rather than processing the whole clip.

Source identity: ISO SHA-256
`08c26c0d71375d6130df7716abc2c282147494d869bd48ce13bd5f972f763e49`;
entry offset 280098816, length 5003912, SHA-256
`a4ceb7c9cc222fe4a690717d670449cc2dacdc251512c9708fd9e29a62881385`.
The bounded extraction reads the supplied ISO without mounting it or modifying
the game installation. Output stays under ignored `local/work-ahead/`.

## Comparison assets

| Method | Output | Observed model processing time |
| --- | --- | --- |
| Decoded reference | 640x480 FFV1 + original PCM | Not benchmarked |
| Conventional Lanczos | 1280x960 FFV1 + copied PCM | Not benchmarked |
| Real-ESRGAN anime-video native 2x | 1280x960 FFV1 + copied PCM | 4 seconds / 75 frames |
| Real-ESRGAN general 4x, Lanczos reduced to 2x | 1280x960 FFV1 + copied PCM; 2560x1920 intermediate retained | 52 seconds / 75 frames, excluding reduction/export |

The two AI runs use the installed Video2X 6.4.0 and AMD Radeon RX 9070 Vulkan
device 0. The general model's sampled still retains more fine map texture; the
native model is smoother. Neither observation establishes motion approval.
Both learned models process frames individually, and no motion interpolation
or frame-rate increase was requested or applied.

`local/work-ahead/video-pilot-v2/review.html` provides a single synchronized
side-by-side MP4, with original enlarged on the left and general AI on the right,
plus all four individual previews and matched frame-30 stills. Browser exports
use H.264 CRF 16, slow preset, yuv420p and faststart. One AAC audio encode from
the reference is copied into every comparison. Lossless masters retain PCM.
The gallery received static resource checks; automated file-URL navigation was
blocked, so browser rendering and full-speed perceptual review remain open.

## Timing and audio evidence

An initial decode trimmed the first 75 emitted decoder frames. Indeo contains
held display frames that are not emitted as new pictures, so this produced
5.667 seconds instead of five. That failed reference is retained locally in
`video-pilot-v1`. The corrected decode applies `fps=15` before frame trimming to
reconstruct the original display holds, then resets PTS on the exact 15/1 grid.
This duplicates held pictures; it does not synthesize motion.

The source excerpt is display frames 0–74 and mono 22050 Hz 8-bit PCM samples
0–110249. The four masters pass:

- 75 display frames, 15/1 fps, five-second duration and preserved 4:3 framing.
- Video PTS within 0.333334 ms of the exact grid, allowing Matroska millisecond
  rounding; continuous audio starts at zero with no measured timestamp error.
- 110250 audio samples identical to the original source excerpt, SHA-256
  `af8bfc9de15e6081bd49152e7934a26a94f7a8d1f3f54681aaa2b88072d50257`.

All five MP4 previews have 75 frames, 15/1 fps and five-second duration. Their
encoded audio payload hash is identical. This supports consistent comparisons;
AAC encoding is lossy and does not replace the PCM master evidence.

The preparation script hash reflects the revision actually used for decoding.
Stricter source-audio range guards were added afterward and rechecked against
the extracted source. The initial validation report is preserved; the current
report adds audio timestamp checks. No media changed during these refinements.

## Tooling, provenance and readiness

`prepare_video_pilot.py` selects exactly one hash-bound ISO entry, validates the
observed source stream contract and saves a lossless bounded reference.
`validate_video_pilot.py` checks the four fixed five-second pilot masters for
dimensions, frame/audio timestamp grids, duration and exact PCM identity. Its
contract is intentionally specific to this pilot, rather than a general video
validator. Twenty-four authored asset tests and the registered `asset_tools`
CTest pass, including hash rejection, source contract rejection, missing video
frames and audio offset/gap checks. Test fixtures contain no game content.

Local `manifest.json` records tool/version/weight hashes, normalized processing
argument vectors and all output identities. Tool executables and model files
remain in their installed locations. Existing FFmpeg 9.0.1, FFprobe 9.0.1 and
Video2X 6.4.0 were used; nothing was installed or downloaded for this pilot.
Third-party dependency licenses remain separate from project-authored tooling.

Status: **WA02 prototype**. Next review the clip at full speed for lettering
drift, flicker, halos, moving-window detail and audio sync. If a method survives
that review, sample a more motion-heavy section before full-clip or batch work.
Native playback, optional replacement routing, skip/cue timing and fallback
still depend on the recompilation's video subsystem.

## 4:3 at 2160p

The user clarified a target closer to 4K. For a 3840x2160 UHD display, a
preserved 4:3 image at the same height is **2880x2160**, with 480-pixel side bars.
Keeping UHD's width instead would produce 3840x2880, which exceeds its height.
The selected target is 4.5x the original 640x480 dimensions.

`local/work-ahead/video-pilot-2160p-v1/` reuses the hash-verified 2560x1920
general AI intermediate and applies a final 1.125x Lanczos resize. It also
exports a direct conventional resize of the decoded source at the same size.
This uses one native 4x AI pass, with no additional AI generation, cropping,
stretching or motion interpolation. A larger output canvas does not establish
recovered source detail.

Both 2880x2160 masters preserve all 75 frames, five-second duration, exact
15/1 fps and original PCM samples. The H.264 browser previews retain the same
frame grid and copy the previous reference's AAC stream. The local manifest
records input/output/tool hashes, exact export commands and timing/audio checks.
`review.html` provides both videos and full-resolution frame-30 stills. Motion
and original-game playback review remain pending.

## First planned full upscale: opening movie

Update 2026-10-08: the user requested starting this project. See the
[opening cinematic project](opening-cinematic-upgrade.md). The full upscale,
2880x2160 master and browser previews are now complete and technically validated.
Full-speed perceptual review and game integration remain pending. The following
paragraph records the earlier hold state.

The user selected the general AI result and placed the full upscale on hold
while the texture batch is prepared. **`VIDEO/INTRO.AVI;1` is position 1 in the
full-video queue.** This records a plan only; no full-movie extraction, decoding,
upscaling or encoding has started. The machine-readable queue is saved locally
at `local/work-ahead/video-discovery/upscale-queue.json`.

The opening movie is 2737 display frames at 15/1 fps, **182.466667 seconds
(3 minutes 2.47 seconds)**, originally 640x480 IV50. Its disc entry starts at
462899200, is 82169804 bytes long and has SHA-256
`8a4276231b81a2edc064f3c88af1ee5aa780e080e2e00a9f5c43711ec62891e4`.
It belongs to the same hash-bound ISO used for the pilot. The planned path is
the installed Real-ESRGAN general 4x model through Video2X 6.4.0, producing a
2560x1920 intermediate, then a 1.125x Lanczos resize to **2880x2160**. Preserve
4:3 framing, the original 15/1 display timeline and original audio; generate a
lossless master and a separate browser review export.

The five-second general-model pilot took 52 seconds for 75 frames. Linear
scaling gives 1897.65 seconds, approximately **32 minutes for the AI stage** on
the same RX 9070. This is a planning estimate; the full-movie run will measure
its own elapsed time. Decode, final resize, validation and encoding add time.

The intro has stereo 22050 Hz **16-bit PCM**, unlike the pilot's mono 8-bit
audio. Its header reports 4023397 interleaved sample frames (16093588 bytes),
seven sample frames longer than the video timeline. Before the full run, extend
the preparation and validation contract for this source rather than applying
the fixed five-second, mono-8-bit validator. Verify all 2737 display frames,
held-frame reconstruction, the 15/1 timestamp grid, decoded stereo sample
count and exact source PCM identity. Preserve the original audio tail instead
of forcing it to the video duration. Full-speed review must cover motion,
lettering, scene transitions and audio synchronization before replacement use.

Primary method references: [Video2X 6.4.0 source](https://github.com/k4yt3x/video2x/tree/6.4.0),
[Real-ESRGAN model documentation](https://github.com/xinntao/Real-ESRGAN),
[FFmpeg fps/trim/atrim filters](https://ffmpeg.org/ffmpeg-filters.html) and
[FFmpeg Lanczos scaling](https://ffmpeg.org/ffmpeg-scaler.html).
