# Opening cinematic: text restoration review

User reported unreadable lettering at 1:00–1:05 and 1:27–1:33. Those observations
are a perceptual rejection of the current opening upscale. Previous timing,
frame-count and audio validation remains valid but does not establish visual
acceptance. No existing master or download was replaced during this investigation.

Local evidence: `local/work-ahead/opening-cinematic-text-review-v1/`.
At five seconds, the original title lettering is softer but preserves letter
shapes better than the general Real-ESRGAN 4x result. The 15 fps lossless upscale,
30 fps master and GPU-compressed result carry similar malformed lettering at
that inspected frame. This identifies upscale damage before interpolation and
delivery compression in this example; it does not clear every interpolated frame.

At 65 seconds the HUD numbers/labels and synthetic scanlines are changed by the
general model. At 90 seconds the original upper-right weapon list remains partly
readable, while the general model converts many letter interiors to blocks.
These are points within/adjacent to the reported ranges, not complete motion
review of either range.

GPU pilot: one-second original-source excerpts at 5, 65 and 90 seconds, native
Real-ESRGAN anime-video v3 2x through installed Video2X, lossless FFV1 output.
Still comparisons resize the 1280x960 output to 2880x2160 using Lanczos before
display reduction. The native-2x samples preserve more faithful lettering and
less aggressive detail than the old general4x model at these inspected frames.
They still alter some shapes and soften scenery. They are candidates, not an
approved whole-movie replacement. Logs preserve model/processor commands.

## Recommended revision

Restart from the decoded original 640x480 reference at 15 fps. Compare a gentler
2x enhancement plus conventional final resize, conventional upscale alone, and
a commercial restoration candidate if available. Judge original lettering,
logos, thin edges, scanlines, scene detail and frame-to-frame stability before
another complete-movie run. Approve a new 15 fps lossless master before RIFE
interpolation and AV1 delivery encoding.

Text-sensitive regions should retain conventionally resized original pixels
through tracked masks where enhancement changes readable glyphs. For titles,
high-resolution re-typesetting is an optional editorial restoration only after
confirming exact wording, font, position and fade timing. Moving HUD content
requires preservation/tracking rather than inventing plausible labels. Do not
apply deinterlacing globally merely because synthetic HUD scanlines are visible.

Topaz Video Proteus is a commercial candidate with adjustable enhancement and
source-detail recovery; Gaia is another candidate described for high-quality
computer-generated footage. Neither was run in this investigation and neither
is guaranteed to repair lettering. Benchmark original-source clips before
purchase or a full render. The initial conventional Program Files inspection
found no Topaz installation.
[Topaz enhancement controls](https://docs.topazlabs.com/video-ai/filters/enhancement),
[model descriptions](https://www.topazlabs.com/learn/topaz-video-enhancements-1-output-resolution-video-types).

Current state: defect reproduced; gentler installed-model pilots show improvement;
full affected-range motion comparisons, model selection and replacement master
remain pending. The other 18 cinematics have not been cleared of similar defects.
