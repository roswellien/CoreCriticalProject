# Following-camera normal-map walks and Mad Cat 24x test

2026-10-16. Corrects a concrete presentation defect in the prior five-mech
normal-map walk previews. R1 left the camera fixed; Mad Cat, Thor, Vulture and
Champion retained horizontal hip travel and crossed the view. Nova's corrected
walk already had essentially zero horizontal root travel, so it stayed centered.

## Camera correction

New ignored workspace: `local/work-ahead/mw5-five-mech-normal-walk-r2-follow/`.
Use packed R1 scenes as pinned inputs. Author a presentation-only follow empty,
sampled from world hip/pelvis XY. Camera, light-orbit center, light aim and soft
fill follow that translation; the floor and mech remain untouched. Vertical
body bounce stays visible. Actual-vertex screen bounds now refresh the evaluated
camera inverse each frame, then reframe using all walk poses.

All 336 model/rig output poses per model equal R1 exactly (maximum matrix error0),
and original geometry/UV/weights/rest data and walk curves remain unchanged.
Camera/light tracking error is below0.0001 scene units. Actual vertices remain
inside the camera for all336frames. Verified by reopening the saved outputs,
and reviewed contact sheets sample varied gait phases as well as light angles.
No retargeting, limb alignment or silhouette changes are bundled into this fix.

Five corrected12x videos remain1280x960,336frames at30fps,11.2s: six walks and one
full moving-light orbit. The combined overview is1920x1080, same frame count and
duration. Latest worn colors and unchanged donor normals/PBR presentation are
retained. Normal strength10.20 is the approved12x reference response.

## Requested Mad Cat 24x experiment

Separate packed scene and video double Body/Variant/Weapons normal strength
from10.20 to20.40 (24x relative to0.85). Window0.30 and flat missile-head0.85
remain. Reopened12x/24x scenes have identical packed images, mesh/UV data, all
other shader inputs, camera/lights, and all336 scene/rig transform samples.
Exactly three material normal-strength inputs differ. The side-by-side video
is1920x780,336frames,11.2s; color and neutral comparisons use identical frame85.
Composite labels occupy separate header bars, outside the rendered image.
The first matched still shows a subtler increase than the prior jump to12x;
these labels describe shading response, not literal depth or displacement.
After the high-quality review, the user reaffirmed12x as the future native
target; this24x output remains an exploratory preview. No game normal-map
implementation is added.

## Delivery and execution boundary

[Mad Cat12x versus24x](https://drive.google.com/file/d/1WY1t4DFWy2l8Nf9ytjuu_3OLnywhg9_r/view?usp=drivesdk).
[Corrected five-mech overview](https://drive.google.com/file/d/136oqdnwWtN3BsTcxrrUyxZ9bY_xQe8N0/view?usp=drivesdk).
[Organized Drive batch](https://drive.google.com/drive/folders/1X3TNDdQiV1Xh5qZ0HC0dRTDxhv5BYxM2).
33files and six folders verified by identity/title/parent metadata.
Original R1 evidence remains. Editable packed Blender scenes, manifests,
individual MP4s, matched off/on comparisons and local HTML remain in workspace.
All six individual encoded videos verify1280x960/336frames/11.2s; comparison and
overview metadata also verified. No sharing changes.

Offline Blender visualization only: no new native execution, game FPS, launcher
settings, installed textures, model registrations, gameplay or acceptance credit.
All render-source hashes retained. Shared native context is read-only and its
before/observed hashes are recorded without reverting another writer's setup.
Current fitting/retarget/muzzle/damage/LOD limits and color-only scar relief limits
remain. Black Hawk and Champion are still offline candidates.
Protected composer/watcher processes left intact. One BelowNormal/two-thread
render worker, brief read-only saved-scene check. No game launch, desktop
screenshot, registry/pilot edit or commit. Strict acceptance stays paused131/144.
Another native process appeared during rendering (Bravo navigation investigation
run); this task left that process untouched and did not interact with the game.


## Mad Cat video compression correction - 2026-10-16

User reported visible video compression obscuring surface detail. Re-encoded
both12x/24x from all336 original RGB PNG frames, without a Blender re-render or
compressed-video source. H.264 CRF8/slow/grain replaces prior CRF20/fast for these
previews. Individual files retain1280x960; the new2560x1020 side-by-side preserves
all1280x960 pixels per mech and uses a separate60px header (no downscaling).
All3outputs verify H.264/yuv420p/336frames/30fps/11.2s. Original PNG sequence
hashes are unchanged. Full-frame SSIM against the same YUV420 encoder reference
improves for both variants: 12x previous Y-SSIM0.989859; 12x high_quality Y-SSIM0.996591; 24x previous Y-SSIM0.989721; 24x high_quality Y-SSIM0.996612.
This measures codec loss, not artwork/game fidelity or Drive streaming quality.

Updated existing Drive video IDs and clearly labeled their titles HIGH QUALITY:
[24x](https://drive.google.com/file/d/1st7kEiyqtcxtWayKVXykJ0aoiKtVFOmw/view?usp=drivesdk), [12x](https://drive.google.com/file/d/1h0VcHRMyCOLD6ttsxYvsS4quwEqV2ooV/view?usp=drivesdk),
[native-resolution comparison](https://drive.google.com/file/d/1WY1t4DFWy2l8Nf9ytjuu_3OLnywhg9_r/view?usp=drivesdk).
Added two lossless full-pixel PNG comparisons (frames15/85) and encoding notes
in the same Mad Cat folder. Six writes verified by id/title/parent/MIME/size.
Local prior encodes retained; high-quality files and encode/source/quality
receipts in `local/work-ahead/mw5-five-mech-normal-walk-r2-follow/madcat/high-quality-r1/`.
Local five-model comparison now points to the high-quality Mad Cat outputs.
Download MP4/PNG for inspecting detail; [Drive help](https://support.google.com/drive/answer/2423694?hl=en)
documents a1920x1080 playback limit and connection-dependent playback quality.

Delivery/encoding correction only. Same geometry, textures, normals, walk,
following camera and lighting; future native12x target unchanged. One BelowNormal
two-thread encoder; protected processes preserved. No game launch, screenshots,
registry/pilot edits, commits, native execution or acceptance credit.131/144paused.

## User decision after high-quality review - 2026-10-16

The user saw very little to no difference between the high-quality12x and24x
Mad Cat previews and explicitly chose to keep12x as the goal moving forward.
Use the approved12x-equivalent MW5 material appearance (Blender armor/variant/
weapons Strength10.20 relative to0.85; glass0.30) for subsequent previews and
future native shader calibration. Preserve existing per-material/chassis tuning
and separate original-MW3 material handling. Retain24x as comparison evidence;
it is not an approved default. This records the direction without changing
renderer code, launcher settings, live assets or acceptance credit.
