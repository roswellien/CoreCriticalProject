# Opening cinematic 30 fps pilot

Completed 2026-10-08 at the user's request, using the installed Video2X 6.4.0
RIFE v4.6 model on Vulkan device 0 (RX 9070). No tools or weights were downloaded.
This is a motion-interpolation test of the existing general-model 2880x2160
opening upscale, preserving 4:3 framing.

The source excerpt covers original display frames 976–1203 inclusive, 65.066667
through 80.266667 seconds, and PCM sample frames 1434720–1769879 inclusive.
There are 228 original display frames and 335160 stereo 22050 Hz PCM sample
frames over 15.2 seconds. Audio was trimmed from the original AVI by sample
index and verified exactly against the lossless excerpt. Source PCM SHA-256:
`8bad057ee06eec6ed4c2ac4242fd22878b82fe56e6a2274fc4191fa5b60f5c5f`.

The local project is `local/work-ahead/opening-cinematic-30fps-v1/`. RIFE ran on
the upscaled lossless excerpt with multiplier 2, UHD mode enabled, scene threshold
20, and FFV1/yuv444p output. The tool reported 72 seconds for 455 output frames.
Scene detection is a heuristic and does not establish that all cuts are clean.

RIFE emits 2*N-1 frames. One held final picture was appended to fill the last
1/30 second, preserving the complete 15.2-second video/audio duration. The
normalized master has 456 display frames at 30/1 fps, zero start, and original
PCM unchanged. Both raw and normalized masters passed frame-packet timeline
checks with maximum 0.333334 ms Matroska rounding error and exact PCM equality.

The matched review exports use H.264 CRF 16, slow preset, yuv420p and faststart.
One AAC encode was copied into the 15 fps baseline, giving identical encoded
audio in both previews. Full decoded frame checks confirm 456/228 frames,
30/15 fps respectively, 2880x2160, and 15.2-second duration. Both files fit under
the connector's 100 MiB transfer limit without a bitrate cap or stronger export
compression. `manifest.json` records tool/model hashes, source and master checks,
output hashes, encoder settings and the endpoint policy. Command logs remain
with the local assets.

Private Google Drive downloads:

- [30 fps RIFE test, 57,373,076 bytes](https://drive.google.com/file/d/19SZsus69A66zdJPTdk_EfJZhi3xTTrYI/view?usp=drivesdk)
- [15 fps matched baseline, 61,308,010 bytes](https://drive.google.com/file/d/1TWNe4qv8M4L7ixh2H4hBSABhSUoCRs1x/view?usp=drivesdk)

Status: technical validation passed; perceptual motion review pending. Review
moving silhouettes, weapons and explosions, background detail, scene cuts,
and audio synchronization before deciding on whole-movie interpolation.
