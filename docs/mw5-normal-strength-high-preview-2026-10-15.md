# MW5 normal strength 8x/12x preview - 2026-10-15

The user requested 8x and 12x normal-map strength after the 2x/4x experiment.
This offline Bushwacker preview uses Body/Variant/Weapons shader values 6.80 and
10.20 relative to the original 0.85. Glass stays 0.30; previous 4x (3.40) provides
the reference. Requested values are verified after assignment; 12x is retained
as 10.1999998, ordinary float precision around 10.20.

The R2 corrected walk, R7 colors, existing normal maps, mesh/UVs, material values,
camera/light/world/floor remain unchanged. Scene signature excluding only target
Strength sockets stays identical across 4x/8x/12x; source file/profile hashes are
unchanged. Fresh 4x frame 15 is pixel-identical to the R3 reference. No additional
normal detail or mesh displacement is authored. At 12x, broad panels show some
rippling and small seams become exaggerated; strength is not a physical-depth
multiplier. The original silhouette and painted-scar limitation remain.

The user game was observed running before expensive work. Only the Blender
worker priority was changed (BelowNormal, verified 0x4000), with two CPU threads
and 0.08-second yields between frames. The active game/composer processes were
untouched. No game run, desktop screenshot, pilot/registry edit, runtime feature,
native performance/acceptance claim or commit. Accepted 131/144; strict paused.

Ignored workspace:
`local/work-ahead/mw5-bushwacker-extract/normal-light-walk-r4-strength-high/`.
Packed 8x/12x scenes, same-pose/neutral stills and matched walking/light animations
are retained separately from earlier previews. This advances offline material
comparison only; live assets/settings and the native renderer remain unchanged.

Both new walks have 336 frames, 11.2 seconds at 30 fps, H.264 1280x960. The
three-way video is 1920x540 with the same duration/frame count. Source pins,
scene signature and reference equality checks passed. At frame 85, 115,136 pixels
(8x) and 134,443 pixels (12x) differ from 4x by more than 4/255 in a channel.
Colored closeups and neutral stills were visually inspected. Ten uploaded files
were verified by metadata readback for identity, name and parent folder; delivery
receipt is retained locally in `drive-previews.json`. No sharing settings changed.

- [Organized Drive folder](https://drive.google.com/drive/folders/1cH42ScTE9Xx6S4NR7z54eZkdkLMgBm84)
- [4x / 8x / 12x comparison](https://drive.google.com/file/d/1WdkKJEkCeU-GkUtgaYEm-MN11zveF7-J/view)
- [8x full walk](https://drive.google.com/file/d/1Kvu1MovvVPB94D87MioULZB6i_9yE5gv/view)
- [12x full walk](https://drive.google.com/file/d/1eoSfJUR1e8pCPDHdkwMQTOqp-CmXc3k3/view)

## Approved target for future native normal mapping

The user selected the **12x-equivalent appearance** on 2026-10-15 as the planned
target when normal mapping is integrated into the game. Use the retained R4
Bushwacker 12x scene/video as the visual reference. Its Body/Variant/Weapons
normal Strength is **10.20**, which is 12 times the original 0.85; it is not a
request to blindly enter 12 into a different shader. Preserve the glass exception
(0.30 in the reference). This decision applies to the MW5 replacement-model
material direction; it does not select a strength for original MW3 meshes.

Bring-up plan:

1. Establish enhanced per-pixel lighting and the geometry/material handoff,
   including UVs, linear normal textures, tangent basis and mirrored-part
   handedness, on the native replacement-model path.
2. Match the 12x reference response under a controlled moving light and matched
   pose/camera/materials. Calibrate the native strength to that appearance rather
   than assuming numeric equivalence between Blender and the game shader.
3. Carry this as the target for enhanced MW5 materials, with per-material/chassis
   adjustment available where maps differ. Review seams and broad-panel rippling
   against the approved reference before changing the target. Keep glass and
   materials without normal maps on their appropriate separate handling.
4. Validate animation, damage/LOD states, near clipping, cockpit/zoom views and
   both model projection branches. Measure the added CPU/GPU cost in matched
   gameplay scenes. Keep normal mapping independently configurable and verify
   the disabled path preserves the existing rendering baseline.

No runtime option, renderer code, launcher default or game asset is changed by
this decision. Native integration still needs the lighting/material foundation
and normal-texture/tangent support; a Blender preview is not runtime validation.
No native execution boundary or acceptance credit advances; strict 131/144 stays
paused. The reference adds shading detail, not silhouette displacement, and does
not author normal relief for the R7 color-only paint damage.
