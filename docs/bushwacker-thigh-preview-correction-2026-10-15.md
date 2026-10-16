# Bushwacker thigh preview correction - 2026-10-15

The user reported slight inward upper-leg cocking during the walking/light
preview. Straight-on renders and pose inspection isolated sideways tilt/twist
in the retargeted thigh transforms. This revision changes the offline preview
animation only; it does not install a game model or change original gameplay.

The thigh controls now swing in sagittal planes. A two-circle knee solve keeps
the original hip/ankle locations and both segment lengths, followed by a minimal
rigid calf rotation. Original foot/toe world poses are retained. Only Thigh,
Knee and Foot0 curves on each side change; other curves remain identical. No
mesh parts, rest-shape edits, scaling or stretching are introduced. Normal maps,
R7 colors, material settings, camera and circling-light setup are retained.

The initial57-point correction was exact at its keys but failed a between-frame
foot-drift check: maximum matrix difference0.1032. The retained repair bakes
those six controls at eighth-frame intervals,449samples. Foot/toe matrix error
at these keys is at most0.00000382; non-leg bone and attached-object differences
are zero. Upper/lower segment-length errors are below0.0000022asset units.
An independent897-point check at sixteenth-frame intervals measures foot/toe
matrix difference at most0.00314 and upper sideways angle0.00652degrees.
Maximum thigh rotation correction is11.382degrees; knee displacement0.417asset
units. These are preview measurements, not validated physical units or gameplay.

Ignored workspace:
`local/work-ahead/mw5-bushwacker-extract/normal-light-walk-r2-thighs/`.
The packed scene, source/check scripts, initial diagnosis, final sample checks,
video/GIF and frontal before/after comparisons remain local. Existing source
scene, textures, models.json and launcher.json hashes are pinned unchanged.

[Organized R2 Drive previews](https://drive.google.com/drive/folders/1qbGudrqd5blHDREpzWKUqnY6xeBk4Rjc).
The video is336frames at1280x960,30fps and11.200seconds; media/source checks pass.
All five uploads were read back to verify IDs, names and destination folder.
[Corrected video](https://drive.google.com/file/d/1DO0NStdYIYQwA0pWJEFYLUER-ldHaiRp/view)
and [frontal comparison](https://drive.google.com/file/d/1AVsSFqoe3v5zFkA_qlDnqL5QWb_P7GMV/view).
The earlier R1 folder remains available as the before reference. No game launch,
desktop screenshot, pilot/registry edit or commit. Native execution boundary
unchanged; accepted131/144 and strict lane paused.
