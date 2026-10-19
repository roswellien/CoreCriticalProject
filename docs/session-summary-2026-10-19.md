# Development session summary — 2026-10-19

The [photo-mode crash repair](photo-mode-crash-fix-2026-10-19.md) records the
target-marker failure, narrow dispatcher fix, native camera/screenshot checks,
installed build identity and remaining physical-key verification limit.
Its follow-up covers water/HUD composition, camera-layout corrections, preserved
entry framing, live draw comparisons and the verified test-media restoration.

The [Big Lake surface-lifetime repair](big-lake-surface-lifetime-fix-2026-10-19.md)
addresses a subsequent scene-loading failure after 60,589 presented frames.
It adds pressure-driven reclamation of released virtual-surface pages, with
reference/lock/provider pin checks and a matching native pressure/control pair.

The [screenshot readback repair](screenshot-readback-fix-2026-10-19.md) corrects
RGB565/RGBA8 decoding into the PNG/video BGRA contract. It adds decoded color
and row-layout checks plus same-frame native screenshot/reference comparisons,
and corrects the earlier PNG validation scope.

The public website note is [the October 19 MechLab update](mechlab/2026-10-19.md).
The [photo texture-state repair](photo-mode-texture-state-fix-2026-10-19.md)
addresses the remaining terrain streaks in the corrected PNG sample. Photo
snapshots now restore host graphics settings with the guest's cached settings,
preserving each material's sampling. Saved rewind files use version 3.
The Material Normal Preview is updated; the regular launcher is not promoted.
The [Instant Action environment baselines](instant-action-environment-baselines-2026-10-19.md)
add two visible, real-clock timing runs per map on Big Lake, Grasslands,
Rolling Hills and Gorge, plus separate environment captures. Settings and
the playable build are preserved for later per-map lighting comparisons.
Formal acceptance remains 131/144. Changes remain uncommitted.

The [announcement capture plan](announcement-capture-plan-2026-10-19.md) now
records a first private review collection: five stills and six silent 12-second,
60 FPS clips of models, coastal/dockside lighting and a live laser-firing pass.
Photo-mode status messages from technical proof images are excluded. All video
exports fully decode and retain their expected frame counts. The playable preview
is unchanged; later-operation coverage and the finished announcement edit remain.

## 2026-10-19 — Model joints and reference-corrected Mad Cat

[Joint-fit record](mech-joint-fit-2026-10-19.md): reproduced Mad Cat/Vulture
elbow fitting and detached inner Bushwacker toes. Vulture retains donor upper/
lower arm spacing; inner toes now use the existing fitted foot hinges. The
user's subsequent Mad Cat art reference exposed low/inward original shoulder
anchors: final Mad Cat restores donor-relative shoulders beneath missile pods
and keeps separate torso/upper-arm corrections through optional BWMESH5.
Both source distances and Bushwacker primary/Freya geometry are registered.
No added pieces, artwork changes or gameplay firing-point edits.

Fresh current-source host be9bc313… is published at
local/remaster/gpu-native-joint-attachments-r1 with an actual matching snapshot;
the prior42672b40/2926029b source-record mismatch is preserved as history, not
relabeled. Main launcher supports the existing AA-off/fullscreen settings,
passes normal/original-model checks and asset preparation. Current settings,
39banks/32sidecars, other chassis and original pilot/registry hashes preserved.
1496changed-adapter checks and10,370,925legacy checks pass. Mad Cat1542offline
pose/LOD cases checked; retained original collapser/getup hand translations
are distinct from fitting residual. Vulture349poses, Bushwacker59samples.
Fresh be9bc313 stock comparisons pass: Training 116/116, GPU draw stream
1150/1150, IA 116/116. Separate native IA runs reach 1400 Vulkan presentations
with each corrected chassis: Mad Cat/Vulture LOD0, Bushwacker LOD0 and LOD1.
Positive instance-validation and queued GPU records establish actual use;
original F2 exterior views were inspected. Small joint contacts remain partly
outside the rear-view framing, so offline front/side poses provide detailed
fit evidence. One menu-only attempt is excluded; budget exit 1 is intentional.
No game ran concurrently with another native session; singleton refusals were
respected. Extended combat/damage/effect alignment, full LOD transitions,
Freya replay on this host and performance remain open. Protected originals
and artwork hashes remain unchanged. Strict 131/144 paused; no commit.
[Final Mad Cat previews](https://drive.google.com/drive/folders/1XHakISSeDm96ejNObO9AI4YihuqtxVGc).

## 2026-10-19 - Orion and Annihilator arm alignment

The announcement screenshots exposed actual imported forearm reference-pose
errors. Corrected Orion BWMESH2 forearm geometry/normals around the existing
pivots and Annihilator BWMESH4 forearm rest matrices with dependent bones. Both
close/distance assets are separate revisions. The normal-preview and main model
registries point to them; textures, normal maps, unrelated models and concurrent
joint-fitting revisions are preserved. Native neutral front/side comparisons
and movement checks keep both weapons forward. The normal-preview prepare-only
check passes; the main launcher plan resolves the corrected bindings. Gameplay
muzzle origins, simulation and animation controls are unchanged. Full combat,
damage/detachment and exact visual muzzle-origin fitting remain unverified.
Details and local hashes: docs/orion-annihilator-arm-alignment-2026-10-19.md.
Strict acceptance remains 131/144. No commit or public publication.


## 2026-10-19 — Mad Cat torso-follow correction R3

User review supersedes the preceding Mad Cat R2 shoulder claim: walking lowers
the torso but the source arm joints compensate upward by about2.0888 units.
The previous fitting test retained that travel and missed the visual detachment.
Optional BWMESH6 now fixes the replacement shoulder in torso space and gives
the same live translation correction to each complete upper/lower arm and its
weapons. Original rotations, aiming, hand motion and guest simulation remain;
no geometry or artwork added/changed. Both distances updated; other chassis,
settings,39banks/32sidecars and original registry/pilot/artwork hashes preserved.

Main launcher selects source-matched native host546c5616 at
local/remaster/gpu-native-madcat-torso-follow-r1. All15recovered MadCat clips at
both distances pass1542attachment cases (max residual0.00000107, formerly2.088815).
Actual adapter15183/0 and legacy10370925/0 checks pass. Fresh exact-host stock
Training116/116 GPU1150/1150 IA116/116 match. Native IA1400 Vulkan presentations
validates/queues MadCat LOD0 complete arms; F2 exterior target inspected.
Small joint contacts partly leave the rear-view frame; detailed fit evidence
uses matched Blender standing/walking poses. Intentional budget exit1, not
mission completion or measured FPS. Live LOD1, extended combat/damage, effect
origins, clipping extremes and performance remain open. Strict131/144paused.
No commit, desktop screenshots or writes to original registry/pilot files.

[Detailed R3 record](mech-joint-fit-2026-10-19.md#r3-arms-follow-the-lowered-torso).
[R3 before/after walking previews](https://drive.google.com/drive/folders/1lx6N77iOrW6J8jxDH0jVNeKH9J1Z5rSM).
Private receipts: C:/Users/jcbla/.codex/workspace-storage/MW34Recomp/joints-20261019-r1/torso-follow-r3/.

## 2026-10-19 - Native walking/firing orbit gallery

Completed 14 native walking-and-firing orbit clips across all four Instant
Action maps, with sunrise/sunset lighting. The active gallery has 42 screenshots;
30 were refreshed, including all three current Vulture/Bushwacker views on two
maps each. Mad Cat was explicitly put on hold by the user; no new Mad Cat run
was made, its older folder is labelled HOLD, and both active indexes exclude it.
Current main Mad Cat is format6 and needs its completed adapter in the lighting
capture host before a future retake, after the user says it is ready.

Selected clips total 156 seconds: 11 full 12-second orbits and 3 eight-second action
cuts (Bushwacker, Thor, Black Hawk) avoiding fire-obscured closing views. All
selected outputs are silent 2560x1440 at 60 FPS. Actual gait and visible original
weapon effects were reviewed for every chassis. Full decode, dimensions, frame
counts, local hashes and Drive name/byte-size readback checks pass. All 28 frozen
and current close/distance payloads match the source pins. The private host adds
capture camera/input automation and the authored joint adapter; installed
launcher profiles and original pilot/config data are not changed by this work.

The first paused-to-live Vulture prototype failed and remains excluded; the
final camera initializes directly in live gameplay. Successful runs ended at
explicit presentation budgets, not mission completion or real-time benchmarking.
Full combat, damage transitions and exact muzzle alignment remain separate.
Record: docs/mech-orbit-captures-2026-10-19.md. Media and indexes are under the
existing report junction; Drive review folder remains 1jwO2_iNAH4mKdKMZ5_5LU0KVnQuLG2zR.
Strict 131/144 unchanged. No commit, sharing change or public publication.


## 2026-10-19 — Mad Cat / Vulture live arm attachment R4

[R4 live-joint repair](mech-live-attachments-2026-10-19.md) supersedes the previous
Mad Cat R3/Vulture R1 attachment claims. Actual gameplay forearm translations
differ from the saved stand reference, causing measured1.147158/1.797140-unit
elbow gaps. Existing BWMESH6 data now anchors both shoulder and elbow, preserving
source rotations; existing clavicle triangles follow torso. No added geometry,
artwork edits or guest pose/simulation writes. Both distances and both main/
material-preview registries updated; all other chassis/settings preserved.

Native base-color walk/aim/stop2500presentations per chassis and separate lit/
normal front/side2500per chassis verify live corrected geometry; max elbow
residual below0.00006476.3084clip/LOD checks,318captured-pose/LOD replays and
actual adapter154247/0 checks pass. Main host546c5616 unchanged. Material Preview
gets source-matched V5/V6 hosta85f211d; fresh stockTraining116/116 GPU1150/1150
IA116/116 match. Versioned matching albedo/normal packs,39banks and15models in
each profile. Original-model/main/material launcher checks pass. Future model
promotions must keep both geometry registries compatible with their hosts.
Live LOD transitions, damaged/stump states, effect origins, clipping extremes
and final performance remain open. Strict131/144paused; no commit or desktop
screenshots, original registry/pilot writes, or release of the trailer hold.
[Native game previews](https://drive.google.com/drive/folders/1Qx34jJGwLTQiAHC92EjCaLdEmQQ8CQEm).
Private receipts: C:/Users/jcbla/.codex/workspace-storage/MW34Recomp/joints-runtime-20261019-r4/.

## Website publication and October 18–19 summaries

The public notes in `docs/mechlab/2026-10-18.md` and `2026-10-19.md` now summarize the current results, superseding the accumulated draft publication text. They distinguish preview, main-play and filming boundaries and preserve the 131/144 acceptance count. The website adds Mechs and Gameplay categories, fourteen profiles with corrected orbit captures, and the user-published YouTube announcement on Gameplay and the homepage. AI-development disclosure is explicit on Home and About; the www Pages domain is configured.

Website source lives in the separate `CoreCriticalWeb` repository. Its media manifest points to verified copies in the pinned Cloudflare deployment so future Git builds do not require local game media. The dated notes remain the sole input to automatic MechLab publishing. No new native execution boundary is advanced by this publication work.
