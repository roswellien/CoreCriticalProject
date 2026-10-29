# Announcement trailer revision 2

The user subsequently released both model holds and requested fresh R4 Mad Cat,
Vulture and night weapon-lighting footage for revision 3. This older edit still
contains rejected geometry and remains held; it is not the source for the new
model shots.

**HOLD — user review rejected the new Mad Cat on 2026-10-19.** Trailer work is
paused at the user's request. Do not use this revision or resume Mad Cat
captures/inclusion until the user explicitly releases the hold. Its Drive
folder and 1080p file are marked HOLD. Vulture remains excluded.

The user rejected Vulture's model for announcement use and then released the
Mad Cat hold. Review 2 removes all three Vulture sections and uses newly captured
Mad Cat walking video and a front screenshot. The 2:30 duration, original Core
Critical intro, announcement titles, music and other selections are retained.
The first review is preserved and its Drive folder is marked SUPERSEDED.

## Updated Mad Cat capture

The main registry selects `madcat-torso-follow-r3`, whose BWMESH6 payload anchors
the complete replacement arms to the lowered torso. The capture freezes both
model distances and the existing upgraded albedo/normal packs and saves SHA-256
pins. No earlier Mad Cat video or screenshots are substituted.

A private copy of `capture-host-r2` receives the existing
`tools/remaster-launcher/apply_joint_anchor.py` change in `mesh_override_stage.inc`.
This retains the capture camera and material/lighting renderer while adding the
same BWMESH6 support used by the installed model build. Installed profiles and
assets remain unchanged. The private build completes successfully.

Native takes `orbit-r4-madcat` and `orbit-r5-madcat` both reach their explicit
2046-presentation budgets. The second rotates the sun to light the front of the
model more clearly; it is the selected source. The logs confirm native Mad Cat
replacement batches and material normal maps. Original gameplay and animation
matrices remain read-only. These controlled-clock captures are not benchmarks.

The selected source provides two clean native screenshots and a 12-second,
720-frame walking orbit. Weapon pulses were not visually confirmed in the
reviewed samples, so this edit adds no laser sound to Mad Cat's shots. Other
action selections retain the original game audio mix.

## Artifacts and delivery

The ignored `reports/announcement-trailer-20261019-r2` directory resolves onto
the Games drive archive. It holds the full-quality master, 1080p60 Drive copy,
720p60 review copy, timeline, soundtrack/effect cues and final-file checks.
Fresh Mad Cat sources and their provenance are under
`reports/mech-orbits-20261019-r5/madcat`.

The [Review 2 folder](https://drive.google.com/drive/folders/14rQI97AWSkuu8HyLOhHZkUz4EoPICoNV)
is separate from the superseded first edit. Daishi remains excluded for the
previous capture-material issue. Vulture is excluded until the user releases
it after model repairs. No commit, public publication or acceptance credit is
added; strict acceptance evidence remains intact at 131/144.
