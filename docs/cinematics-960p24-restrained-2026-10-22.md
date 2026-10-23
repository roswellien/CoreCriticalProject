# Restrained 2x cinematics at 24 fps

On 2026-10-22 the user requested a smaller upscale to retain the character of
the original cinematics, selected restrained AI enhancement, and set a target
of **1280x960 at 24 fps**. Start from the original 640x480, 15 fps movies, not
the historical 2160p/30 fps exports. Preserve full picture width, original
aspect ratio, existing letterboxing, running time and audio. Do not replace or
delete the earlier experiments.

## Local review pilot

Working directory: `local/work-ahead/cinematics-960p24-restrained-v1/`.
The first pilot is opening time 01:00-01:30, with movement and green HUD text.
It retains the full 4:3 frame; the picture within the opening's existing bars
occupies 1280x640. This is a 30-second test, not a completed collection.

The initial restrained setting blends 35% native 2x Real-ESRGAN anime-video-v3
with 65% Lanczos enlargement of the source. This is a trial strength for visual
review, not an approved final appearance. No additional sharpening, text
replacement, erosion, color grading or denoising pass is applied.

For 24 fps, installed Video2X accepts only integer RIFE multipliers. RIFE v4.6
therefore generates eight samples per original interval at native resolution,
with scene threshold 20. Selecting every fifth sample gives an exact 24 fps
grid before spatial enhancement. The final source picture is held across the
remaining tail. Cut detection is heuristic; interpolation can still warp text,
edges or moving subjects. Full-speed perceptual review remains necessary.

The local processing script records source hashes, existing tool/model pins,
commands, outputs and frame/audio checks. An initial attempt exposed inherited
120 fps metadata after sampling, which caused the spatial tool to assign the
wrong timestamps. Its outputs remain as failed experiments. The corrected
`r3` outputs explicitly encode the sampled stream as 24 fps and validate
intermediate timestamps and PCM before blending.

Completed review deliverable:
`INTRO-pilot-60-90s/INTRO-pilot-60-90s-960p24-r3.mp4`.
The matching `INTRO-pilot-60-90s-960p24-master-r3.mkv` retains original PCM;
the MP4 uses AAC for convenient playback. Both decode to 720 frames at
1280x960 and 24 fps. The MP4 runs exactly 30 seconds; maximum master frame-grid
error is 0.334 ms. The master retains all 661,500 stereo PCM sample frames,
matching the prior untouched excerpt's PCM SHA-256
`de9a2d369d38be817c81e363d449b41d92a38d1846694e1c8c7170e3fe6ee18a`.
Intermediate 24 fps timestamp grids and PCM identity also pass. Still review
shows subtle enhancement with retained source texture; motion review is pending.
Only the `r3` deliverables are review candidates.

This is offline media work. No native execution boundary advances, launcher
default changes, pack installation, upload or acceptance credit are claimed.
Strict accepted count remains 131/144. Originals and derived media remain local.

## Additional AI pass on the existing pilot

The user preferred the 960p24 pilot to the historical 4K versions and requested
one more AI enhancement on that already-created clip. A separate candidate is
complete under `INTRO-pilot-second-enhancement-v1/` in the same local directory.
It starts from the validated first pilot's lossless master, applies another
native 2x anime-video-v3 pass, returns to 1280x960 with Lanczos, and blends
35% of the new result with 65% of the existing pilot. No new interpolation is
applied. The first pilot remains intact.

Review video: `opening-30s-960p24-second-enhancement.mp4`. Both its lossless master
and MP4 decode to 720 frames at 24 fps over 30 seconds. Intermediate and final
frame grids pass; original master PCM is byte-exact. Matched original-time 88s
stills show a subtle further smoothing/edge-cleanup effect, with the HUD retained.
Full-speed motion and subjective preference remain for user review. This is a
second pilot candidate, not a collection conversion or deployment.

## Full opening: two passes complete

The user authorized the full opening with the same two-pass process on
2026-10-22. The full original `INTRO.avi` was processed from its admitted source
SHA-256 `8a4276231b81a2edc064f3c88af1ee5aa780e080e2e00a9f5c43711ec62891e4`.
The first pass reuses the corrected pilot workflow; the second applies exactly
the pilot's additional 35% AI/65% prior-master blend at 1280x960.

Completed local deliverables under the working directory:

- `INTRO-full-two-pass-v1/opening-full-960p24-two-pass.mp4` — viewing copy.
- `INTRO-full-two-pass-v1/opening-full-960p24-two-pass-master.mkv` — FFV1 master
  with original PCM.

Both outputs fully decode to **4,380 frames at 1280x960 and 24 fps**, spanning
182.500 seconds. The last source picture holds across the final fractional
frame interval; the original video spans 182.466667 seconds and is not sped up
or slowed down. All 4,023,397 original stereo PCM sample frames remain intact,
including the small original audio tail. Intermediate and final timestamp grids,
audio continuity and byte-exact master/source PCM checks pass.

For both first- and second-pass masters, decoded-frame hash comparison of the
corresponding 60-90s section matches all **719 comparable pilot frames exactly**.
The final pilot frame is excluded because its excerpt boundary holds the last
source picture while the full movie continues into the next interval. Selected
full-movie stills were inspected at 15, 45, 115 and 170 seconds. Full-speed
whole-movie subjective review remains pending; no runtime deployment was made.

The full workflow, commands, tool/model pins and checks remain local in
`full_opening.py` and the two full-movie manifests. Prior tests and source files
are retained. This media completion adds no native execution or acceptance credit.

## Extreme third-pass comparison pilot

The user subsequently requested a third, extreme AI pass to compare against the
two restrained passes. A new 60-90s pilot is complete under
`INTRO-pilot-third-extreme-v1/`. It starts from the validated two-pass lossless
pilot, applies the same native 2x anime-video-v3 model, then returns to 1280x960
with Lanczos. The new pass uses **100% AI output and no prior-master blend**,
versus the earlier 35% blend. No additional motion interpolation, sharpening,
color grading or text replacement is applied.

- `opening-30s-960p24-third-extreme.mp4` — third-pass viewing copy.
- `compare-two-pass-left-third-extreme-right.mp4` — synchronized comparison,
  with the two-pass master on the left and extreme third pass on the right.
  Each pane retains 1280x960; the combined movie is 2560x960.

The lossless third-pass master and both MP4s fully decode to 720 frames over
30 seconds at 24 fps. Frame grids and exact master PCM identity pass. Matched
88s still review shows substantially smoother textures and more defined HUD
edges in the third pass; full-speed subjective comparison remains for user
review. The full two-pass opening remains the existing full-length candidate.
The third-pass test is local only; no full-movie third pass, upload or runtime
deployment was performed. The workflow and checks are in local `third_extreme.py`
and its manifest. This experiment advances no native execution boundary or
acceptance count (still 131/144).

## Remaining movies and pack queue

The user selected the restrained two-pass routine for the remaining18movies and
authorized cinematic asset-pack preparation. The [collection current-work note](cinematics-960p24-collection-current-work.md)
records the actual worker, existing graphics capture coordination, resumable
queue, per-source audio checks and automatically built local19-movie library
preview pack. Consult its `batch.json` for live progress; the collection is not
complete merely because the queue was launched. Native enhanced in-game playback
still requires the modern decoder boundary.

Completed 2026-10-23: all18remaining movies passed the two restrained AI passes,
frame/timestamp checks and original lossless-master PCM checks. The full19-movie
1280x960/24fps library preview pack is built and verified through the launcher's
existing importer in an isolated folder. Independent completion checks rehashed
all19 MP4s and the archive and matched its20declared resources. See the linked
collection note for the pack path, hash and actual playback limits. The completion
heartbeat is paused; whole-collection subjective review and native HD in-game
playback remain separate work.
