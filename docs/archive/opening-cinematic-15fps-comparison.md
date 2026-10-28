# Opening cinematic: 15 fps comparison

Two samples cover original time 01:00–01:30, at 2880×2160 in 4:3, without interpolation. Both contain 450 original frames and the original 30 seconds of stereo audio.

- **A:** Native RealESRGAN anime-video-v3 2× upscale to 1280×960, then Lanczos to the final size.
- **B:** Light luma-only bilateral cleanup at 640×480 (`sigmaS=1`, `sigmaR=0.015`), two native 2× passes with the same AI model to 2560×1920, then Lanczos to the final size. No automatic cleanup between AI passes.

This experiment uses locally available Video2X and FFmpeg, not Topaz. Both viewing copies use the same AMD GPU AV1 10-bit CQP 64 settings, with lossless FLAC audio. CQP is not CRF. FFV1 masters remain local.

Files and machine-readable validation: `local/work-ahead/opening-cinematic-15fps-comparison-v2/`. The run checks 450 decoded frames, 15 fps timestamps, 30-second duration, dimensions, full-file decoding and exact PCM audio identity against the original excerpt. Consult `manifest.json` for completion and hashes.

[Download comparison folder](https://drive.google.com/drive/folders/1SA3Y59fvnRlLK0sfBoSM01UGNDEiGUFg) includes A/B viewing copies, the original native-resolution excerpt, comparison stills at 01:02 and 01:28, and a README. No sharing permissions were added.

Still review suggests B has crisper edges but alters fine HUD strokes and letters more than A. This does not establish motion quality or a preferred full-film workflow. User playback review remains pending; prior full-film masters have not been replaced. The excerpt ends at 01:30 and therefore does not cover the final three seconds of the reported 01:27–01:33 problem range.
