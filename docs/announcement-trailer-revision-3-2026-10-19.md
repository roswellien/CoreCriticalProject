# Announcement trailer revision 3 — corrected models and night combat

**Superseded by [revision 4](announcement-trailer-revision-4-2026-10-19.md):** the live filming camera has been corrected and the affected footage recorded again. This historical edit remains flagged; use the separate Review 4 media.

**Review issue:** the user flagged sideways Bushwacker laser fire in the delivered review. Matched native captures with original geometry and replacement geometry reproduce the same firing direction. The Bushwacker night shot needs a forward-aimed retake; this review is not announcement-ready. Fresh Mad Cat and Vulture sources remain separate and are not newly held.

The normal-game-camera control fires forward before entering paused Orbit; live Orbit active during firing pulls the aim sideways. This isolates a live capture-camera/targeting interaction, rather than replacement geometry alone. The private repair is still under test. Early scope candidates that produced identical aim records without an active rendered Orbit are invalid controls, not successful repairs. In particular, R6/R7 have zero camera-render scope counts and cockpit-view readbacks. The final check must demonstrate a visibly active external view, nonzero render scopes, original aim/pose parity and actual movement.

Source inspection and original instructions show that context entry `0x4B52C0` tail-jumps into hardware world drawing at `0x4F7030`; the composer fuses this tail path. Hooking only the named callee misses the active path. The draw-distance early return also needs to preserve the photo-camera wrapper. Candidate changes remain isolated in the private capture host; the installed preview still uses its pinned R3 binary.

The user released both Mad Cat and Vulture holds on 2026-10-19. This edit uses fresh native captures of their corrected live-attachment R4 models and adds night walking combat with local weapon lighting. Earlier rejected model footage remains held and is not substituted into the new model sections.

## Footage and edit

- Fresh Mad Cat on Grasslands and Vulture on Gorge: front, side and elevated front screenshots, plus 12-second walking camera arcs at 2560×1440, 60 FPS. Both model distances, matching upgraded texture/normal archives and file hashes are frozen in the capture receipts.
- Puma on Grasslands: 17 seconds of walking and PPC fire under the revised moonlight preset, including blue illumination on the mech and terrain.
- Bushwacker in Campaign Operation 1 Mission 3: 18 seconds of walking and green laser fire, with visible illumination across the sand and mech. Earlier Rolling Hills takes were rejected for obscured or weakly visible fire.
- The announcement remains 2:30 with the existing ten-second Core Critical intro, original MW3 soundtrack, screenshots, moving footage and announcement titles. The two new night combat sections start at 1:53 and 2:02.
- Original game sound effects are edited onto silent native capture, with new weapon cues matched to visible pulses. This is an editorial soundtrack, not a live gameplay audio recording.

Captured frames preserve original gameplay inputs and animation. The camera follows front-to-side arcs; no animation or damage simulation is rewritten. Native stills retain the full 3440×1440 image; video exports center-crop to 16:9 instead of stretching it. Capture notifications are excluded from selected video frames. No exposure boost or invented lighting is applied in post.

## Lighting correction found during capture

Moving footage exposed a defect missed by the earlier pause-only check: the old field used for elapsed time did not advance, leaving flash illumination alive after firing stopped. The corrected preview uses a monotonic presentation clock, holds it in photo mode and excludes paused duration on resume. Backward-clock reset is tested explicitly.

The native proof keeps paused world pixels identical at frames 1050 and 1100 and records zero active lights at frame 1440 after live firing stops. The Vulkan fixture passes. Fresh night takes use executable SHA-256 `8002410fbdbb05d75021070d052201a44a21e9e2e84bc70d70ee948451369c53`.

This advances native effect-light presentation and capture correctness. It does not advance original-game acceptance beyond **131/144**. Controlled-clock recording is not a performance benchmark; the earlier off/on benchmark remains scoped to its earlier prototype.

## Storage and private review

Local media and receipts are in ignored `reports/mech-orbits-20261019-r6` and `reports/announcement-trailer-20261019-r3`, which resolve through the reports junction onto the Games drive archive. Source capture runs and pinned assets remain local. Full-quality and compressed review deliveries have separate filenames.

The [Review 3 folder](https://drive.google.com/drive/folders/1yoKIZj7OY_MiSoS36NGt9RI2wJOb7_Kw) contains the new model screenshots and source clips, night combat clips and lighting stills. The [separate weapon-lighting comparison folder](https://drive.google.com/drive/folders/1azUsrJJn1PuZiwKRpPcI9j1qOeSLgwai) preserves earlier prototype controls. Drive sharing is unchanged. No public posting or commit is performed.

## Remaining engine limits

Delivery checks confirm 150 seconds, 9,000 frames, 1080p60, full-file decoding, source hashes and stereo AAC at 48 kHz. Integrated loudness is -16.06 LUFS and true peak is -1.45 dBTP. The 255,039,847-byte master remains on Games; 88,989,556-byte 1080p and 56,007,864-byte 720p viewing copies are uploaded. Drive readback confirms the folder's 17 files, sizes and main-video parent. These delivery checks do not resolve the visual aiming issue above.

Local weapon lights currently observe submitted original effect draws. Fully offscreen emitters are not recovered, and these unshadowed lights can bleed through occluders. Whole-campaign and all-weapon coverage, water response and longer-session performance remain separate integration work. See [the lighting preview summary](weapon-night-lighting-preview-2026-10-19.md).
