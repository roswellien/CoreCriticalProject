# First enhancement experiment and disc-video discovery

Recorded 2026-10-07, following the [texture decoding pilot](work-ahead-texture-pilot.md).
This batch creates local 4x comparison assets and identifies video sources.
It does not approve a replacement pack or establish original-renderer equivalence.
The subsequent [five-second video pilot](work-ahead-video-pilot.md) decodes a
bounded C2M1 excerpt and compares two AI models with a conventional 2x resize.

## Texture and alpha experiment

The built-in image-generation tool edited the decoded 128x64 texture and 32x32
damage mark. Initial drafts were preserved, then one targeted correction was
attempted with stricter atlas registration and alpha-footprint constraints.
The tool returned 1774x887 texture images and 1254x1254 damage images, rather
than the requested exact export dimensions. Windows System.Drawing exported
comparison PNGs at 512x256 and 128x128 with bicubic sampling. The raw generated
outputs remain alongside them; dimension conversion does not resolve art drift.

Two conventional reference methods are also saved: nearest-neighbor controls
and bicubic resizes of the decoded originals. The faithful damage resize retains
the original alpha values on the integer 4x grid. This preserves its alpha but
does not reconstruct additional original detail or create new subpixel opacity.

| Asset / method | Result | Readiness |
| --- | --- | --- |
| Mech texture, generated draft | Exact export size and opaque alpha; broad cable/island arrangement survives, but panel detail, weathering and seam registration are uncertain | Hold for original-renderer and UV review |
| Damage mark, generated draft | Alpha mean absolute error 0.25625 against the enlarged original; intersection-over-union 0.41499 at alpha threshold 128; visible holes and placement change | Rejected for source-alpha fidelity |
| Mech texture, conventional bicubic | Exact 512x256 export without new synthesized structures | Faithful resize baseline; no integration claim |
| Damage mark, bicubic color with retained original alpha | Exact 128x128; zero alpha error and intersection-over-union 1 against the original grid | Faithful alpha baseline; no integration claim |

The alpha comparison uses the original alpha expanded by nearest-neighbor as
its coordinate reference. Metrics describe this specific experiment; no general
acceptance threshold is inferred. Independent review agrees that the generated
damage draft changes the silhouette and holes. Whole-atlas generative editing
is not yet a reliable production method for these samples. A subsequent
restoration attempt should constrain individual verified UV regions and retain
source alpha separately, then check the resulting mapped geometry.

Local batch: `local/work-ahead/enhancement-pilot-v1/`. `review.html` provides
original/candidate pairs, a method selector, background selector and atlas
overlay. `manifest.json` saves all ten PNG identities, decoded source hashes,
export/comparison tool hashes, four exact generation prompts and review results.
Generated artwork and the gallery remain ignored by Git.

No in-game reference was captured in this batch: the original game was closed
and source-to-renderer mappings remain unverified. The automated browser refuses
`file://` navigation, so the gallery received static resource/control checks,
not an automated browser-rendering test. No alternate browser route was used.

## Disc videos

The read-only ISO probe found 19 AVI files in the primary disc tree, totaling
321,969,744 bytes, 16,411 frames and 1094.066667 seconds (about 18 min 14 sec).
All report 640x480, FOURCC `IV50` and exact 15/1 frames per second. PCM audio is
22050 Hz: `C1.AVI` and `INTRO.AVI` are stereo 16-bit, and the other seventeen
are mono 8-bit. The ISO SHA-256 matches the recorded supplied-media identity.

All observed video-chunk counts match the declared stream/main-header frame
counts. Audio byte counts match declared sample lengths. These are container
checks, not codec or audio/video playback proof. AVI index offsets, codec data,
embedded assets, cabinet contents and supplementary disc trees remain open.

Local metadata: `local/work-ahead/video-discovery/disc-video-inventory.json`,
`video-summary.json` and `README.md`. No video payloads were exported or decoded,
and no drive was mounted or modified. The inventory traverses primary ISO9660
extents directly, with authored bounds and endianness checks. Format sources
are listed in the probe and local report.

First video-pilot candidate: `VIDEO/C2M1.AVI;1`, 379 frames and 25.266667 seconds.
Next establish a reproducible decode and inspect full-speed playback before
enhancement. An initial proposed export is 2x (1280x960), retaining 4:3 framing,
all 379 frames, the exact 15/1 timescale and original audio. Avoid accumulating
the rounded AVI main-header value of 66667 microseconds per frame. Rerendering
and frame interpolation need separate specifications after viewing the clip.

## Tooling and validation

New authored tools are `video_probe.py`, `export_preview.ps1` and
`compare_preview.ps1` under `tools/asset-inventory/`. The Windows exporter
preserves aspect ratio, rejects existing outputs and reparse-point output
ancestors, and limits outputs to ignored project-local storage. Creative edits
use the built-in image tool; deterministic size conversion and baseline exports
use Windows System.Drawing. Read-only alpha comparisons do not modify images.

All twenty authored asset tests and the registered `asset_tools` CTest pass on
Windows. Checks cover ISO extents/endian fields/cycles, AVI chunk bounds and
stream metadata, decoder channels/alpha, exact exports, original-alpha values,
bad aspect/scales, overwrite prevention and output-root restrictions. Windows
export checks are explicitly skipped on other platforms. Proprietary inputs
are absent from tests and CI.
