# Five-mech normal-map walking previews

2026-10-16. The user requested the same Blender normal-map/walking/moving-light
test for Mad Cat, Thor, Vulture, Black Hawk and Champion. Five complete packed
scenes, individual videos, a combined overview and matched normal-off/on stills
are saved in ignored `local/work-ahead/mw5-five-mech-normal-walk-r1/`.

## Materials and motion

Use the latest registered Mad Cat worn colors, retained Thor R2, new Vulture R2
and current Black Hawk/Champion worn candidates. Normal images are unchanged
donor OpenGL tangent-space maps, loaded as Non-Color and bound to UVMap.
Body/Variant/Weapons strength is10.20: the approved12x response relative to0.85
in the Bushwacker reference. Window stays0.30; the flat MissileHead normal uses
0.85 where that material is present. No displacement or silhouette edits.
Existing painted scars have no newly authored normal relief.

All five use the same illustrative Bushwacker PBR constants: armor roughness
0.57/metallic0.12, weapons0.42/0.55, window0.20/0, missile heads0.55/0.25,
specular0.40. These are controlled preview choices, not recovered shader parity.
The orbiting area key and fixed soft fill scale energy with model height squared;
camera angle, relative light sizes and one full orbit are consistent. The floor
and lighting are authored Blender presentation, not game-environment evidence.

Each original walk has57samples/56intervals. Existing action curves are retained
and repeated six times through Blender NLA. Black Hawk's approved donor-length
walk is mapped from frames2-226 at quarter scale; its stand key is excluded.
At every one of336 output frames, model/rig poses match the corresponding source
sample exactly, including Black Hawk's corrected hips/knees. Mesh coordinates,
topology, UVs, weights, rest joints and source action curves are unchanged.

| Model | Visible parts | Maximum pose matrix error | Geometry/UV/weights/rest digest |
| --- | --- | --- | --- |
| Mad Cat | 38 | 0 | `c2fc58ccac84e51cca6e7802fc8f146ead2f148cc132186200f10bd27e88e5d8` |
| Thor | 21 | 0 | `fd161cbb1368018afe9f7def76c39155be6810b6a7a619e5ae67a9540ce9d4ce` |
| Vulture | 32 | 0 | `927ed59b84ffde2610c835a034c0c610a1a0db37673d13d3253bade2ee9b64d5` |
| Black Hawk | 14 | 0 | `cb382cdc0afccce93825d9fa8c2572f5789f93228bfd25bca2a90b7023d542db` |
| Champion | 30 | 0 | `cfa70e0933c8035feae0e984fb780de259209659340b4a091a6a220d410031ec` |

Screen framing is measured from actual model vertices over the full56-pose
cycle. Each mesh remains inside the camera; repeated cycles retain the same
poses. Camera framing changes only the offline presentation. The retained
Black Hawk/Champion fitting, native retarget, muzzle, damage and LOD limits
remain; this test does not repair or validate their native implementation.

## Output and delivery

Each individual H.264 MP4 is1280x960,336frames at30fps,11.2seconds: six walks and
one complete light orbit. The labeled combined video is1920x960 with the same
duration/frame count. Video metadata is verified. Hero stills and six-angle
light-orbit contact sheets are reviewed; same-pose colored and neutral-gray
off/on pairs isolate the existing normal-map shading. Per-model pixel-difference
metrics are retained as descriptive image differences, not a fidelity score.

[All videos and comparisons on private Drive](https://drive.google.com/drive/folders/1KcleCRlp7SFz7KBZ8rn9ICGzWuVa3OzR).
Twenty-seven files and six folders are verified by identity/name/parent metadata
readback. Each chassis has its own video, hero, two off/on comparisons and notes;
the overview video and still are at the batch root. Packed editable Blender
scenes and local comparison HTML remain in the workspace. No sharing changes.

## Execution boundary

This advances offline material/animation visualization only. It does not enable
native normal maps, dynamic lighting or shadows, install Black Hawk/Champion,
change playable model/texture registrations, or measure game FPS. High strength
can exaggerate seams/noise and does not imply a physical depth multiplier.
Future native implementation must calibrate to the approved reference rather
than blindly reuse a different shader's numerical parameter.

All rendering-source assets, model registry, root launcher and the initially
referenced executable retain their identities. During rendering, another writer
changed the shared launcher profile and a game session appeared. That profile is
not a Blender rendering input; its different before/observed identities are
recorded in input-conservation.json, and the current setup is preserved. This
task neither edits the profile nor launches/stops that session.
The full-walk Blender worker runs BelowNormal with two CPU threads and brief
frame yields. No desktop screenshot, protected registry/pilot edit or commit.
Existing composer/watcher processes are preserved. Strict acceptance stays
paused at131/144; no native execution or acceptance credit is claimed.


2026-10-16 follow-up: R1 camera presentation is superseded by the corrected
following-camera batch and controlled Mad Cat24x experiment documented in
`five-mech-camera-follow-24x-2026-10-16.md`. R1 evidence is retained.
