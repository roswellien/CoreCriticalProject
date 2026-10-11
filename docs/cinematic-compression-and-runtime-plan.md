# Cinematic compression and recompile playback plan

Status: proposed format contract and local compression screening. Integration
remains deferred until the native recompile is ready, as requested by the user.
Complete-library encoding settings remain undecided pending sample review.

## Preserve and deliver

Keep all 19 FFV1/PCM masters as archival sources. They already use lossless video
compression and total 101856777978 bytes (94.86 GiB). They are 2880x2160, 4:3,
30 fps, SDR 8-bit YUV 4:4:4; they are not uncompressed buffers or 3840x2160 video.
The opening master reports limited range but no color primaries, transfer or
matrix tags. Verify the actual source/render color interpretation before adding
explicit delivery color tags. Do not label this footage HDR or assume an HD
matrix solely because it was upscaled.

Recommended first native delivery candidate:

| Property | Proposed contract |
| --- | --- |
| Container | Matroska `.mkv` |
| Video | AV1 Main profile, 10-bit 4:2:0, 2880x2160, square pixels |
| Timing | Original timeline, constant 30 fps, original complete endpoint |
| Audio | FLAC, original 22050 Hz and original mono/stereo channel count |
| Random access | Approximately two-second keyframe interval; explicit endpoint handling |
| Framing | Preserve 4:3, pillarbox wider displays, no cropping |
| Quality | Constant quality, no hard file-size cap; choose after visual comparison |
| Compatibility | Existing H.264/AAC MP4 exports retained as a fallback |

10-bit encoding does not restore new source detail or make HDR. It may improve
compression/gradient behavior; delivery 4:2:0 also reduces chroma resolution
relative to the masters. Compare fine colored edges, gradients and text before
acceptance. AV1 is lossy here. Keep masters rather than treating delivery files
as replacement archives.

FLAC avoids repeatedly re-encoding the original low-rate audio. For unsigned
8-bit PCM sources, encode a reversible 16-bit representation and prove conversion
back to source PCM bytes matches the source hash. Retain the seven-sample tails
where present. The prototype sample workflow performs this hash check. A native
audio backend may resample to the device rate at playback; do not stretch timing.

Matroska specifies both AV1 and FLAC codec mappings:
[official codec mappings](https://www.matroska.org/technical/codec_specs.html).

## Native playback architecture

Vulkan remains the selected graphics backend. Add a small media boundary with
open, advance, present, skip, end and close operations. The script requests an
original movie identifier; a manifest maps it to a local replacement file and
records dimensions, rate, duration, audio contract and SHA-256. Movie names stay
independent of codecs. Originals remain a fallback for absent enhancement files.

Proposed portable implementation: pinned FFmpeg libavformat/libavcodec for
demuxing and decoding, with dav1d available for software AV1. Use hardware decode
when the device, driver and chosen decode backend pass capability checks. Vulkan
rendering does not guarantee Vulkan Video or AV1 hardware support. Implement a
software-decoded YUV upload path first, then add a measured hardware path without
changing the game-facing interface. Avoid launching an external ffmpeg process
for normal in-game playback.

Use a small bounded decoded-frame queue, audio-driven presentation timestamps,
and aspect-preserving YUV rendering into the current Vulkan presentation target.
Handle seek/skip, decoder drain, audio tail, cancellation and device/window changes
explicitly. Record matrix/range interpretation and validate color conversion.
Keep decoder surfaces and synchronization separate from legacy guest addresses.

[dav1d](https://images.videolan.org/projects/dav1d.html) is cross-platform and
BSD-2-Clause. FFmpeg supports software and device-specific hardware paths; support
must be detected and tested, not inferred from a codec name:
[FFmpeg hardware options](https://www.ffmpeg.org/ffmpeg.html).

Build and pin a decoding-focused LGPL-compatible FFmpeg configuration for the
runtime, with matching source, notices and reproducible build flags. The installed
full FFmpeg encoding tool is an offline experiment dependency, not the runtime
distribution. Offline libx264/libx265 encoders need not be linked into the game.
Follow the project's dependency pin/hash rules and
[FFmpeg's configuration and distribution guidance](https://www.ffmpeg.org/legal.html).

## Compression screening

Local experiment: `local/work-ahead/cinematic-compression-pilot-v1/`.
Three six-second sections: INTRO at 65 seconds, CAMPAIGN at 80 seconds and C3M5
at 15 seconds. Selection is a first cross-movie sample, not proven whole-library
coverage. Reference clips are lossless FFV1/PCM from the 30 fps masters.

Candidates: H.264 CRF16 slow (current quality baseline), HEVC CRF20 slow 10-bit,
and SVT-AV1 CRF20/24 preset6 10-bit. All use MKV/FLAC in this screening so size
comparisons do not mix audio policies. CRF values across codecs are not equivalent.
Six-second keyframe overhead is not representative of every complete movie.

Record per-output commands, bytes, encode time, software decode throughput,
decoded frame count, SHA-256 and byte-exact source audio. SSIM is computed after
both sides are converted to common 8-bit 4:2:0; it is a coarse diagnostic and
does not measure the delivery chroma loss against original 4:4:4. It cannot
certify perceived equality or assess the original interpolation quality.

Before a full-library encode, review the original master and candidate in motion
and at native resolution, including hard cuts, fine detail, smoke, moving edges,
gradients and any text. Expand the samples when these features are missing.
Choose the least compressed setting that meets the user's visual acceptance;
do not claim a predicted library size from three short sections.

## Playback acceptance before release

Require sustained 30 fps with margin on the target minimum hardware, including
frame upload/presentation and audio. A short decode-to-null test on the current
machine establishes neither minimum requirements nor integrated performance.
Test Windows/Linux decoder paths, fallback, skip, repeated movies, missing files,
endpoints, audio sync, color and fullscreen/windowed resizing. If AV1 software
decoding is insufficient on supported hardware, use H.264 or a lower-resolution
compatibility pack; the existing H.264 files are still 2880x2160.

The first future integration proof remains INTRO. No legacy-game hook work is
started by this format planning task.

## Measured screening results

All twelve six-second exports completed. Every candidate has 180 fully decoded
2880x2160 frames at 30 fps, with decoded audio matching its reference PCM hash.
Lossless references, candidates, logs, toolchain identity and exact command
vectors remain in the local pilot directory; `results.json` records the results.

| Candidate | Combined size for 18 seconds | Reduction versus H.264 sample baseline | Software decode range on this machine |
| --- | ---: | ---: | ---: |
| H.264 CRF16 slow, 8-bit | 117.3 MiB | baseline | 190–395 fps |
| HEVC CRF20 slow, 10-bit | 69.9 MiB | 40.4% | 151–216 fps |
| AV1 CRF20 preset6, 10-bit | 83.1 MiB | 29.2% | 114–143 fps |
| AV1 CRF24 preset6, 10-bit | 66.7 MiB | 43.1% | 117–128 fps |

These are actual measured sizes at the listed settings, not equal-quality
efficiency claims. Decode includes process startup and writes no video frames
to the renderer. Short throughput measurements are not sustained game playback
or minimum-hardware verification. The common-format SSIM values ranged from
0.981969 to 0.988531; visually significant damage can be missed by this metric.

Recommendation after screening: retain AV1/MKV/FLAC as the first native format
candidate and use CRF20 as the more conservative initial visual-review option.
CRF24 is a smaller alternative to review. Do not select the whole-library
compression setting from the size or SSIM table alone. HEVC remains a viable
comparison format, but no HEVC-only runtime requirement is proposed.
All original masters and current whole-movie exports remain unchanged.
