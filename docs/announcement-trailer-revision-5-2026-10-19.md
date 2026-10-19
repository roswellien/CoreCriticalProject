# Announcement trailer revision 5 — walking and firing orbits

The user requested replacement of the static mech screenshots in review 4 with walking/firing orbit footage, plus two additional mechs at night. This edit replaces exactly 16 static mech slots and preserves the other 15 scenes, their timing, the Core Critical intro, announcement titles, environmental stills and the 2:30 structure.

## Capture and selection

Twelve new native takes cover Thor, Black Hawk, Champion, Shadow Cat, Strider, Orion, Supernova, Cauldron-Born, Sunder, Annihilator, Mad Cat and Vulture. They reuse the corrected private R8 filming camera, whose executable SHA-256 is `6be5eea2924012424aebbdb58e03c3f9e194305cb30a49710a63bc34db4dec6d`. Each run reaches its explicit presentation budget. Original gameplay, movement, weapon cooldowns and animation execute while the detached camera follows the mech.

The camera moves from approximately 15 degrees off the front toward a 100-degree side view. Individual trailer selections favor clear front and three-quarter views. Late building occlusion and foreground explosions are excluded from selected shots. Three initial recording seconds are trimmed to remove capture notifications. The exports crop the native 3440×1440 image to 2560×1440 without stretching; each new source clip contains 720 frames at 60 FPS over 12 seconds.

Thor and Black Hawk add moonlit scenes on Rolling Hills, showing warm ballistic flashes and green laser illumination respectively. These complement the existing corrected Bushwacker laser and Puma PPC night takes. Daytime selections retain Grasslands, Gorge and Big Lake environments at sunrise or sunset. The film applies no additional exposure or lighting boost.

Mad Cat and Vulture retain their approved R4 attachment geometry and matching upgraded textures and normal archives. Other chassis retain their pinned upgraded assets, including the detailed original-MW3 Strider and corrected Orion/Annihilator assets. Previously held Daishi footage remains excluded. Older R2 live firing orbits are not reused.

## Edit and sound

All 14 featured chassis now have moving in-game footage. The former screenshot slots contain walking and firing arcs, with existing corrected Bushwacker footage filling its two slots. The earlier safe coastal hero orbits and environmental sequences remain unchanged.

Source videos are silent native captures. The final mix retains the original MW3 music source and uses original game sound effects edited to visible firing cues. Trigger presses suppressed by weapon cooldown do not receive invented firing sounds. Quiet engine and footstep sounds are editorial accompaniment, not captured live audio. Source hashes, selected ranges and cue times are retained with the private edit.

## Storage, validation and scope

The full-quality master, edit and delivery records are under `reports/announcement-trailer-20261019-r5`, resolving to `G:\MW34Recomp-Archive\storage-relocation-20261018\reports\announcement-trailer-20261019-r5`. New source clips and their manifests are under `reports/mech-orbits-20261019-r7`. Existing sources and earlier revisions are preserved.

The [1080p60 trailer](https://drive.google.com/file/d/1CdtyNesZ7YMle5azs7JuRdSjFRKxIU1v/view) and [720p60 review copy](https://drive.google.com/file/d/1ei1XIuJITnUmMP3IdPbh5gYw09xHH_De/view) are uploaded to the [Review 5 Drive folder](https://drive.google.com/drive/folders/1F2Rd5ZvR0rXQ72y3_a1-6j3njDG2aek9), alongside the two additional night source clips, two night screenshots, storyboard, poster and review notes. Sharing remains unchanged. Source game assets, binaries and generated game code stay local.

The master contains 9,000 frames over 150 seconds at 1920×1080/60 FPS, with stereo 48 kHz AAC audio. Full decoding passes for the master and both viewing copies. The audio measures -16.06 LUFS and -1.50 dBTP; no black gaps are detected. Source hashes match, all 16 replacement slots contain video, and the other 15 scene records and every scene's timing match review 4. All twelve new native source recordings contain the expected 900 frames before trimming and use the pinned R8 executable. Final contact frames and selected weapon-flash frames were visually reviewed.

The full-quality master is 259,458,702 bytes. Drive copies are 90,329,023 bytes at 1080p and 52,581,050 bytes at 720p. Folder readback verifies all nine deliverables and their exact byte sizes; metadata also verifies all four video destination parents. The connector exposes no remote checksums, so these are metadata readback checks in addition to local decoding and hashes. The receipt is `reports/announcement-trailer-20261019-r5/drive-delivery.json`.

This advances the announcement edit and capture coverage, not the native execution boundary. It reuses the [previously validated private filming camera](announcement-trailer-revision-4-2026-10-19.md), changes no installed playable host, and grants no whole-game acceptance credit. These controlled captures are not performance benchmarks. Acceptance remains **131/144**. No commit or public publication is performed.
