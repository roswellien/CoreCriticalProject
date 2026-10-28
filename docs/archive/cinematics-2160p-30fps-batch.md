# Remaining MW3 cinematics: 2160p at 30 fps

Completed all 18 movies after starting 2026-10-08 at the user's request, following the completed
[30 fps opening movie](opening-cinematic-30fps-full.md).

Scope: all 18 remaining videos on the admitted original MW3 ISO. They contain
13674 source display frames at 15 fps, totaling 911.6 seconds. `INTRO` is already
complete and is excluded. Priority is `C4WIN`, `CAMPAIGN`, `C1`, `C2`, `C3`, then
all 13 mission clips in filename order. Filenames suggest roles; gameplay
dispatch is not verified by this media workflow.

The target and quality policy match the accepted opening workflow: general
Real-ESRGAN 4x through installed Video2X, retained 2560x1920 intermediate,
Lanczos resize to 2880x2160, then RIFE v4.6 UHD mode at 2x frame rate with scene
threshold 20. Final lossless masters preserve the original complete PCM and
timeline; one final held frame fills the last 1/30 second. Source disc hashes,
entry bounds and each movie's own header/PCM sample contract are checked.
Most clips have mono 22050 Hz 8-bit PCM; `C1` has stereo 16-bit PCM. Neither
format is normalized into the other's sample contract.

Local project: `local/work-ahead/cinematics-2160p-30fps-batch-v1/`. `batch.json`
is the authoritative current per-movie processing state. Each movie retains
source, lossless intermediates, 15 fps upscale, raw RIFE result, normalized
30 fps master, CRF16 slow H.264/AAC review export, exact command logs and a
manifest of stage checks and output hashes. The final browser export receives
a full decoded frame-count check. Checks include video timestamp grids,
channel count/sample rate, complete duration, continuous PCM timestamps and
byte-exact source PCM identity at each lossless stage.

`upgrade_cinematic_batch.py` runs GPU stages serially and supports `--resume`
for verified completed stages. Changed or unvalidated partial outputs are not
silently reused. Failures are recorded and other movies continue; failed items
must be repaired before declaring the batch complete. Source extraction uses
the admitted ISO directly without modifying the game installation.

Full-quality exports below 100 MiB can be uploaded directly. Larger exports are
split into exact 90 MiB byte parts with reconstruction hashes and Windows/Python
reassembly instructions. Packaging adds no further compression. Results are
uploaded to private per-movie folders as they become ready and checked by Drive
metadata readback. Delivery receipts are separate from processing manifests.

Initial validation: three authored per-source contract tests and three package
round-trip/corruption tests pass, including generic movie filenames. The prior
opening workflow remains separate. Based on measured opening stage times, this
is a multi-hour batch, approximately 4–5 hours plus transfer/check overhead.

Native replacement integration and full-speed perceptual review of every movie
remain separate milestones. Scene detection is heuristic; interpolation can
produce warping, flicker or cut artifacts despite passing technical validation.

## Completed collection

All 18 movies passed technical validation: 27348 decoded output frames at
2880x2160 and 30 fps, spanning the original 911.6-second video timelines.
All lossless stage PCM hashes match their respective source PCM. No jobs failed.
Final MP4 exports total 4500504148 bytes. A final collection audit rehashed all
18 MP4s against their processing manifests and matched each delivery receipt
to the complete expected file list. Local `collection-audit.json` records
per-movie duration, frames, size, SHA-256, part count and private folder URL.

The [private download collection](https://drive.google.com/drive/folders/1zTxmJNYbKVepIFlLsp4hAPfeHNK9IlVI)
contains 18 movie folders. Seventeen exports use exact byte parts; `C2M4` is a
direct MP4 below the connector limit. All 124 movie-package files were uploaded
and their size and destination checked by metadata readback. The collection
README links every folder and the separately completed opening movie.
`delivery-receipts.json` records successful uploads. A transient final-part
upload timeout was retried successfully. The collection remains owner-only.

Each local movie folder contains `{CLIP}-2160p-30fps.mp4` and the lossless
`master-2160p-30fps.mkv`, alongside intermediates and validation logs. The opening
movie is separate under `local/work-ahead/opening-cinematic-30fps-full-v1/`.
All 19 disc movies are now processed; full-speed perceptual review and native
game playback integration remain pending.
