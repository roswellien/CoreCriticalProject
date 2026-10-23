# Opening cinematic working source

Current full-opening candidate (2026-10-22): the user selected the restrained
960p24 test over the historical 4K versions, reviewed its second AI pass, and
requested the same two passes across the entire opening. Completed viewing copy:
`local/work-ahead/cinematics-960p24-restrained-v1/INTRO-full-two-pass-v1/opening-full-960p24-two-pass.mp4`.
The matching FFV1 master retains the complete original PCM. Both fully decode to
4,380 frames at 1280×960 and 24 fps, with the original 4:3 framing and bars.
All 719 comparable frames of the reviewed excerpt match the full two-pass master
exactly. Technical checks pass; full-movie playback review remains pending.
See [processing details](cinematics-960p24-restrained-2026-10-22.md).
This is a full-length local candidate, with no runtime installation or upload.

The earlier excerpt experiments below remain as historical work and are not
the source of this new full-opening conversion.

Second 2× upscale to 2560×1280: `local/work-ahead/opening-cinematic-2to1-v1/upscale4x-text-preserved-v1/` starts from the latest 1280×640 detail-cleanup master. Native anime-video-v3 2× GPU enhancement supplies the scene. To avoid thicker AI-redrawn letters, selected HUD text rectangles use a conventional bilinear 2× resize of the input, with stable feathered boundaries. Protected core pixels match that resize exactly in every frame. There is no added text sharpening/thinning, frame interpolation or reframing. Plain AI baseline is retained for comparison. The RGB lossless master remains 2:1 at 15 fps with original PCM; MP4 preview and close-up comparisons remain local. Consult its manifest for completed verification; subjective VLC playback review is pending.

Next 2× detail cleanup: `local/work-ahead/opening-cinematic-2to1-v1/upscale2x-detail-cleanup-v1/` starts from the text-thinned 1280×640 master after the user reported retained text legibility. It uses frame-local edge-aware luma filtering and radius-two noise-gated detail contrast. A binary expanded green HUD mask protects detected text pixels and immediate surroundings; the processing script asserts those decoded RGB pixels are unchanged in every frame. No extra upscale, temporal filtering or interpolation. Output uses explicit full-range planar RGB and original audio, with local-only master/preview/stills. Completion and technical checks are recorded in its manifest; user playback quality review remains pending.

2× text-focused upscale: `local/work-ahead/opening-cinematic-2to1-v1/upscale2x-text-v1/` starts from the second native text pass, using Video2X anime-video-v3 native 2× on the AMD RX 9070. The plain lossless upscale is retained. A separate master applies soft 3×3 erosion in selected green HUD text regions, at 25% strength with a 10-level brightness cap and equal RGB-channel deltas. Output is 1280×640 at 15 fps, still 2:1, with original PCM audio and explicit full-range planar RGB tags. Final master/preview decoded-frame, timestamp and audio checks passed. Close-up still review shows subtly less heavy bright stroke boundaries, with unresolved blur remaining. Neither text recognition nor full motion quality is established. Local-only outputs; source chain preserved.

Second text pass: `local/work-ahead/opening-cinematic-2to1-v1/native-text-pass2-v1/` uses the cleaned planar RGB master. Expanded green HUD masks select existing stroke edges for noise-gated luma sharpening, capped at 8 levels. The same integer delta is applied to each RGB channel; there is no selective green brightness boost, retyped text, temporal processing or upscale. FFV1 planar RGB master and MP4 preview remain local. All 450 frames retain 640×320 at 15 fps; decoding, timestamps, RGB format/range tags and exact original master audio passed validation. The still-image effect is subtle; user motion/readability review remains pending.

Second native pass: `local/work-ahead/opening-cinematic-2to1-v1/native-detail-cleanup-v1/` works from the text pass's planar RGB master. It applies spatial edge-aware luma cleanup and bounded, noise-gated detail contrast, protecting green HUD pixels and preserving R/G/B channel differences. Output remains 640×320 at 15 fps in FFV1 planar RGB with explicit full-range RGB metadata and original PCM audio. Frame count, timestamps, decoding and exact audio identity passed. Still changes are subtle; motion review remains pending. Source/master files are retained and no Drive upload was performed, per the user's local-only preference.

Native text-legibility pass: `local/work-ahead/opening-cinematic-2to1-v1/text-legibility-native-v1/` contains the 640×320, 15 fps 30-second FFV1 master, MP4 review, source-versus-output stills, script and validation manifest. It applies bounded spatial sharpening and a small brightness lift to green-dominant HUD pixels within border regions. No generated/retyped characters or temporal filtering. Original source remains unchanged. Technical validation passed; subjective motion review remains pending. The observed still-image change is subtle and does not recover missing letter strokes.

User selected the native 2:1 picture with only the top and bottom black bars removed. Work from `local/work-ahead/opening-cinematic-2to1-v1/opening-60-90s-640x320-source-master.mkv`: 640×320, 15 fps, lossless FFV1 and original PCM audio. This is the 30-second excerpt from original time 01:00–01:30, not a full-length movie master.

Preserve full picture width. No side cropping, stretching or frame interpolation. On 2026-10-11 the user authorized removal of all earlier opening-cinematic upgrades and experiments locally and on Drive, while preserving other cinematics. Seven obsolete opening work directories and the INTRO-only compression pilots were deleted; 22 obsolete Drive files were deleted. Historical documents describe removed experiments, not current deliverables.

The clean working folder also retains `original-INTRO.avi`, the full-length untouched decoded `original-640x480-reference.mkv`, the bars-only MP4 viewing copy, and a historical source/toolchain record. The selected 640×320 master has SHA256 `9f462f7e96e39522abad0ca000a549145cb199051616aafcdbca66130ea16cdf`. The original AVI matches its source inventory hash `8a4276231b81a2edc064f3c88af1ee5aa780e080e2e00a9f5c43711ec62891e4`.

[Current native-resolution Drive folder](https://drive.google.com/drive/folders/1SA3Y59fvnRlLK0sfBoSM01UGNDEiGUFg) retains the bars-only master, viewing copy and original excerpt. Original game media and other cinematic upgrades were preserved.
