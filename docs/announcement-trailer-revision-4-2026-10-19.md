# Announcement trailer revision 4 — weapon camera correction

The user identified a Bushwacker firing sideways in revision 3. Original and replacement geometry reproduced the direction with the same live camera setup. Firing with the ordinary camera before entering paused Orbit pointed forward. This isolated an interaction between the live filming camera and original targeting, rather than replacement geometry alone.

## Camera repair and evidence

The private capture host now contains its detached view inside the complete world draw and restores the genuine gameplay-camera outputs afterward. It retains current original eye, world matrix, forward direction and bob inputs while rendering from the chosen filming position. Original weapon controls, hit processing and animation still execute.

The post-composer chain matters: original context entry `0x4B52C0` tail-jumps into hardware world drawing at `0x4F7030`, which the composer fuses. The draw-distance early return must retain the photo-camera wrapper at that context entry as well as the ordinary world-render entries. Original instruction inspection independently confirms the tail jump and its context-to-camera argument change. Hooking only the named callee misses the actual path.

Native ordinary-camera and live-Orbit controls cover 679 moving frames. The observed clock, player root world pose and 18 gameplay-camera words are bit-identical. The player moves about 47 world units, and the external view is visibly active with 1,198 observed render scopes. Two aim flags match exactly. A near-zero requested horizontal aim component differs in 423 records, by at most `3.665306380347226e-14`; that raw difference is preserved in the evidence and is not described as bit-identical aiming. The private filming comparison bounds the numerical direction difference at `1e-12`. It grants no native-game acceptance credit.

An additional 1,500-presentation pause/resume run preserves identical world pixels at frames 1050 and 1100 in the recorded central ROI. It resumes and records zero weapon lights at frame 1440 after firing stops. Both controls reach their explicit presentation budgets. Earlier inactive-camera comparisons are retained as invalid controls, not successful repairs.

The corrected capture executable is pinned at SHA-256 `6be5eea2924012424aebbdb58e03c3f9e194305cb30a49710a63bc34db4dec6d`. This remains a private filming host; the installed lighting preview retains its separately pinned R3 binary. Whole-game acceptance remains **131/144**.

## Fresh captures and revised edit

- Mad Cat on Grasslands and Vulture on Gorge were recorded again using their approved live-attachment R4 geometry and matching upgraded texture/normal archives. Each has front, side and elevated screenshots and a 12-second 1440p60 walking arc.
- A Bushwacker walks and fires green lasers on Campaign Operation 1 Mission 3 terrain at night. The corrected take shows the beam traveling forward from the gun, with local illumination on armor and ground.
- A Puma walks and fires PPCs on Grasslands at night. Its new take shows blue illumination from muzzle, trail and impact effects.
- The announcement remains 2:30 with the existing Core Critical intro, original MW3 soundtrack, original sound effects and announcement titles. New model sections start at 0:44 and 0:52. Corrected night action runs from 1:53 through 2:11.
- Older firing-orbit video is replaced with verified gallery stills where it could share the camera defect. The new edit retains the model roster and environmental views. The earlier held Daishi selection remains excluded.

Source clips are silent native recordings; the finished soundtrack uses original game sounds edited to visible weapon cues. It is an editorial mix, not a live game-audio recording. Native stills preserve 3440×1440 resolution. Video crops preserve aspect ratio, and the first three recording seconds are omitted to exclude capture notifications. Lighting receives no post-production exposure boost.

## Delivery and remaining integration

The [Review 4 folder](https://drive.google.com/drive/folders/1QOUqGRJfPbTJ9slS2DYeUO6lQvcQG0BL) separates the corrected media from the flagged revision 3. Ignored local artifacts and delivery receipts are under `reports/announcement-trailer-20261019-r4`, which resolves onto the Games drive archive. Fresh sources are under the `*-camera-r8` and `night-*-r8` folders in `reports/mech-orbits-20261019-r6`. Original generated code, assets and analysis stay local. No commit or public publication is performed, and Drive sharing is unchanged.

The [1080p60 trailer](https://drive.google.com/file/d/1-TCpZAuOy1bd-zjxVzIN5RnLRexiqnE5/view) and smaller 720p60 copy are uploaded. Both contain 9,000 frames over 150 seconds and pass full-file decoding. The stereo AAC mix uses 48 kHz audio, measured at -16.07 LUFS and -1.43 dBTP in the master. Source hashes are pinned. The full-quality master is 164,888,137 bytes on Games; Drive viewing copies are 87,383,151 and 36,203,812 bytes. Readback verifies all 16 folder deliverables and the exact sizes and destination parents of all six videos. The connector does not expose remote checksums, so this is metadata readback in addition to local decoding, not a remote checksum assertion.

Local REA evidence `ev_abb0cd533295304627e01683152585d32d4ea7cce98a52d26be490e259f8c716` records original camera-output writes. `ev_d21d80a59d2454045a0b350e9e4770793a6aed0e4056b48432d3f61cf3034d4f` records the hardware world draw. They corroborate the source analysis; native controls establish the runtime behavior and limits above.

The native execution boundary advanced is live camera rendering separated from the targeting camera. This capture-specific validation is not production camera admission, a whole-campaign check or a performance benchmark. Broader camera/targeting coverage and integration into the final playable host remain separate work. Weapon lights retain the experimental limits described in the [lighting preview summary](weapon-night-lighting-preview-2026-10-19.md).
