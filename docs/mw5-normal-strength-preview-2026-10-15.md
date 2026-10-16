# MW5 normal-map strength preview - 2026-10-15

The user requested amplification of the MW5 models' normal-map effect. The
Bushwacker test compares its existing shader strength0.85 against1.70 and3.40
(current,2x and4x) on Body, Variant and Weapons. Glass remains0.30. No normal
image is repainted; this changes response to the retained donor normal detail.
The new R7 painted gouges still lack separately authored normal relief.

The corrected R2 upper-leg walk, mesh/UVs, colors, material constants, camera,
world, ground and light orbit are retained. A scene signature excluding the
three target Strength sockets remains identical across the variants at frame1;
it covers geometry/UVs, current object/bone transforms, action curves, material
defaults/image references and lights. Source scene, textures, model registry and
launcher hashes remain unchanged. A new1x frame15 render is pixel-identical to
the earlier R2 frame used by the baseline video.

The ignored workspace
`local/work-ahead/mw5-bushwacker-extract/normal-light-walk-r3-strength/`
contains packed2x/4x scenes, two-pose still comparisons, neutral-color views and
walking/light videos. Multipliers describe shader parameters, not physical
depth or displacement. Extra strength can exaggerate normal noise/seams and
does not change silhouette or add source geometric detail.

This advances offline material preview only. It does not enable normal mapping
in the native renderer or install amplified materials across all live models.
No game run, desktop screenshot, pilot/registry edit, performance/acceptance
credit or commit. Accepted131/144; strict lane stays paused.

[Organized Drive previews](https://drive.google.com/drive/folders/1JO84sIanUBUodW0pqs4dQ7W6vqLgODSz).

Both new passes rendered336frames; all three encoded videos verify30fps and
11.200seconds. Individual views are1280x960; the three-way comparison1920x540.
The grazing-light still differs from baseline at92583pixels for2x and126522
for4x by more than4/255 in at least one RGB channel. These are image differences,
not physical-depth percentages. All source pins and non-strength scene signature
checks pass. Colored and neutral-color comparisons were visually reviewed.
All10Drive uploads were read back to verify IDs, filenames and destination.

[Current/2x/4x video](https://drive.google.com/file/d/1kaoxqFyk6Uz-Y_CJvx28yn4rDW6WAAM_/view),
[2x full view](https://drive.google.com/file/d/1zcm-4DM2vcs48Nke7EGIEGqxm4aJJ_2V/view),
[4x full view](https://drive.google.com/file/d/1DEbu2kKkEov9rQLz12UM1k4udJzmX2kb/view),
[close comparison](https://drive.google.com/file/d/1B6QXwMF1m0GlCVk4VVLAgb5kqE2gayXD/view).
