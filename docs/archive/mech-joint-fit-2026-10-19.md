# Mad Cat / Vulture elbows and Bushwacker inner toes

**Mad Cat R3 and Vulture R1 attachment claims below are superseded by the
[R4 live-joint repair](mech-live-attachments-2026-10-19.md).** Live forearm
translations absent from these saved-clip tests still detached the elbows.
The earlier evidence and failures retain their dated scopes.

2026-10-19. Optional visual work; strict acceptance remains **131/144, paused**.
Original game files and generated game/asset data remain local. No commit.

The user reported lower arms seated incorrectly on Mad Cat and Vulture, and
completely detached inner Bushwacker toes. Renders of the exact registered
payloads reproduced both defects. The old upper-arm fitter rotated and stretched
each donor upper arm independently of its forearm: approximately 1.44x on Mad Cat
and 1.70x on Vulture. The Bushwacker inner toes used independent original toe
pivots and vertical fits, while the foot shell used a separate piecewise fit.

Vulture now retains the donor upper-arm shape and elbow spacing; the complete
forearm and mounted weapons follow the relocated elbow in the current upper-arm
frame. Bushwacker's existing inner toe geometry uses the foot's fitting and its
existing donor hinge position. The toe retains its original independent motion
with a relocated visual pivot in the current foot frame. Both original distances
are updated, including Freya's shared geometry. The approved Bushwacker shoulder
and waist geometry, legs, artwork and gameplay firepoints are unchanged.

The user's subsequent Mad Cat reference exposed another error: the shoulder
anchors were still those of the original MW3 skeleton, too far down/inward
relative to the donor torso and missile pods. The first elbow-only candidate is
retained as superseded R1 evidence. The final `madcat-reference-r2` keeps the
donor arm shape/spacing and mounts the complete assembly under the missile-pod
shoulders, relative to the fitted torso. This is an authored adaptation of the
attached reference, not a claim of identical proportions across different models.

Mad Cat needs two independent visual translations: shoulder placement follows
the torso, while elbow spacing follows the upper arm. Using one frame appeared
correct standing but introduced up to about 0.24 units of extra elbow travel in
running. Optional **BWMESH5** extends BWMESH3 with one additional bounded ancestor
name/offset. The adapter applies both before GPU bounds/projection and the CPU
near-plane path; source transforms and weapon origins remain read-only. Legacy
formats 1–4 retain their previous parsing and drawing paths. The authored
`tools/remaster-launcher/apply_joint_placement.py` reproduces this narrow adapter
change against the inspected source and refuses an incompatible source layout.

Validation:

- Vulture: 349 source stand/walk/run/limp/fall/get-up poses; close contact probes
  at most 0.000609 units, distance stand/walk probes at most 0.001879. Fixed donor
  elbow-pivot residual below 0.000002 units in these clips.
- Bushwacker: 59 stored stand/walk samples; inner toe/foot surface probes at most
  0.002782 units close and 0.0000151 distant. Existing non-toe batches are unchanged.
- Final Mad Cat: all 15 recovered Mad Cat clips at both original distances,
  **1542 pose/LOD evaluations**. Placement residual below 0.00000197 units after
  separating the original authored hand translations in `collapser`/`getup`.
  Those source translations (up to about 0.2465 units) and authored upper-joint
  translations remain intact; no pose values are forced to make a test pass.
  Physical elbow probes remain within about 0.020 units in the sampled poses.
- Exact changed adapter: **1496 checks, zero failures**, covering all six new
  model/LOD payloads, both Bushwacker skins, actual queued geometry/materials,
  hidden forearms, independent rotated torso/upper-arm offsets, GPU and CPU
  projection paths, and four malformed second-frame inputs.
- Existing actual-adapter fixture: **10,370,925 checks, zero failures** against
  the retained original fixture inputs/sidecars. A first replay used mismatched
  historical material packs; that failure is retained and the final replay uses
  the matching 32-batch historical Bushwacker packs.
- Serialized triangle/vertex counts and all triangle UV corner bytes are
  conserved. No connector pieces or other geometry are added. Matched Blender
  renders inspect standing and walking from front and side; these are offline
  base-color previews, not native-lighting or live-game evidence.

The standard launcher also had a **pre-existing** build-record mismatch:
registered executable `42672b40…`, source snapshot `2926029b…`. This had already
been recorded by the October 18 controls and campaign work. No old snapshot was
relabeled to claim a source/binary relationship. A fresh native host was built
from a frozen copy of the current source with only the adapter change, retaining
the exact translated-object list. It is published under the versioned directory
`local/remaster/gpu-native-joint-attachments-r1`, with its actual executable hash
and new source snapshot. The previous executable and snapshot remain intact.

Published executable SHA256:
`be9bc313a3dbef86151fd20a9c9731f99eb3dae445dcf07b51f2b33fa49f80bd`.

`play_remaster.py` normalizes the settings UI's `aa: "off"` to the existing native
one-sample representation; the profile retains the user's AA-off choice. The
published capability record includes the current host's existing fullscreen and
windowed choices. Resolution 3440x1440, AF off, scenery1600, fog1100, fullscreen,
39 banks, music, other model entries and current controls are retained. The main
and original-models launcher checks and main asset preparation are checked
separately from actual gameplay.

Native tests started only after inspecting process identities and after the
independent announcement/model capture session closed. A singleton refusal
during a later overlapping capture was retained; no process was interrupted.
Fresh runs on this exact be9bc313 host match the saved original-rendering
baselines: **Training 116/116, GPU draw stream 1150/1150, IA 116/116**.
Receipts are `runs/stock-TrainingCpu-r1/comparison.json`,
`runs/stock-TrainingGpu-r1/comparison.json`, `runs/stock-IA-r1/comparison.json`
and aggregated `regressions.json` in the private work namespace below.

Bounded native Instant Action runs reach **1400 Vulkan presentations each**
with final Mad Cat, Vulture and Bushwacker payloads. `instance_validated` and
positive `replacement_queued` GPU records establish actual use, beyond file
loading: Mad Cat and Vulture select LOD0; Bushwacker selects both LOD0 and LOD1,
including positive individual inner-toe and combined-foot draw records.
The first Mad Cat navigation attempt remained in the menu and is excluded.
`madcat-reference-live-r2` reaches the cockpit; `madcat-reference-live-r3`
uses the original F2 exterior-view selector. Vulture and Bushwacker also reach
exterior view. Native targets were inspected, but rear-view framing leaves
small toe/elbow contacts partly off screen; matched offline renders and pose
probes remain the detailed visual-fit evidence. These are intentional frame-
budget stops (exit 1), not normal mission completion or a real-time FPS test.
Run identities and observed LOD/owner records are in `live-validation.json`.

Extended combat, visual muzzle/effect alignment after the arm moves, damaged
limbs/debris, all LOD transitions, Freya skin-D live replay on this host and
performance remain open. Runtime normal-map status is unchanged.

Execution boundary advanced: optional serialized joint placement now reaches the
compiled native adapter's GPU/CPU draw-command paths with independently moving
shoulder and elbow frames, and the corrected assets reach live native IA GPU
draws for all three chassis. This adds no accepted game-function credit;
strict acceptance remains paused at 131/144.

Assets: `local/work-ahead/mech-joint-fit-20261019-r1/` (Mad Cat final is the
`madcat-reference-r2/` subfolder; Vulture and Bushwacker retain their R1 folders).
Private tools, build logs, fixtures and receipts:
`C:/Users/jcbla/.codex/workspace-storage/MW34Recomp/joints-20261019-r1/`.

Private previews: [all three](https://drive.google.com/drive/folders/1fzRm4eG81jofdeSTI8Yz9bGZAdAgmGpx),
[final Mad Cat reference revision](https://drive.google.com/drive/folders/1XHakISSeDm96ejNObO9AI4YihuqtxVGc).
Sharing permissions were not changed. No desktop screenshots, original registry/
pilot writes or acceptance-chain work.

## R3: arms follow the lowered torso

User review rejected the Mad Cat R2 motion and identified the missing movement:
the arms had looked connected against the raised torso but did not descend with
it. Recovered poses reproduce this. Standing sample 0 places the torso at
Z8.7182; walking sample 14 places it at Z6.5648. The original upper-arm animation
compensates with an approximately 2.0888-unit local pivot translation. R2 kept
that translation after restoring donor-relative shoulders, leaving the MW5 arms
too high while walking. The prior test treated this as preserved source joint
travel rather than enforcing the required visual shoulder attachment. Its
passing elbow residual and live GPU draws did not establish correct shoulders.
R2 is superseded for Mad Cat; its evidence is retained with that limitation.

Optional **BWMESH6** extends V5 with a bounded anchor-controller name and a
fixed anchor position in the existing placement frame. At emission, the adapter
recovers the current torso and original upper-arm transforms for this exact
instance. It adds the difference between the torso-space shoulder position and
the current original arm-pivot position to every batch in the complete arm.
Upper arm, forearm and mounted weapons receive the same correction, so both
follow the torso downward. Original upper-arm rotations, aiming and relative
hand motion remain; source animation matrices, firepoints, simulation and
visibility are read-only. The translation is applied before GPU bounds and
projection and before CPU near clipping. Formats 1–5 remain unchanged.
`tools/remaster-launcher/apply_joint_anchor.py` reproduces the narrow adapter
change and refuses an incompatible source layout.

Both Mad Cat distances now use `madcat-torso-follow-r3/`. Vertex/normal/UV bytes,
triangles, materials and all other chassis assets are unchanged. The new
shoulder criterion checks all 15 recovered clips at both distances: **1542
pose/LOD samples**, maximum attachment residual 0.00000107 units versus the
previous 2.088815-unit detachment. The actual compiled adapter passes **15,183
checks with zero failures**, including 180 recovered side/LOD/clip/sample cases,
GPU matrices, CPU emission, unchanged guest pose bytes, invalid anchor fields
and nonancestor rejection. The recompiled legacy fixture passes **10,370,925
checks with zero failures**. These remain scoped fixture/offline evidence.

Fresh source-matched native host:
`local/remaster/gpu-native-madcat-torso-follow-r1/build/entry_commandline.exe`,
SHA256 `546c5616e44f20888ea312c8126440cec9986e64650f2d8c3769e6ac2926f912`.
On this exact host, new stock comparisons match **Training116/116,
GPU1150/1150 and IA116/116**. Source files outside the adapter and the exact
translated-object list match the previous installed host. The launcher now
selects this build and Mad Cat R3, retaining source-snapshot verification,
all 15 chassis/30 bindings, user settings, 39 texture banks and 32 sidecars.
Vulture and Bushwacker corrections from the preceding section are retained.

Private tools, build, fixtures and publication receipt:
`C:/Users/jcbla/.codex/workspace-storage/MW34Recomp/joints-20261019-r1/torso-follow-r3/`.
Matching before/after walking and corrected front views are in
[the R3 Drive folder](https://drive.google.com/drive/folders/1lx6N77iOrW6J8jxDH0jVNeKH9J1Z5rSM).
These are Blender base-color renders; sharing permissions were not changed.

Final R3 native check: `runs/torso-r3-madcat-live` reaches **1400 Vulkan
presentations** using the published 546c5616 host and corrected V6 payloads.
The Mad Cat LOD0 instance validates and queues positive GPU batches for both
upper arms, both forearms and their weapons. The original F2 exterior view
shows the arms below the missile-pod shoulders as the torso lowers; detailed
small contacts remain partly outside the native rear-view framing. Native
framebuffer targets were inspected; no desktop screenshot was taken. The
intentional frame-budget stop is exit 1, not mission completion. Live LOD1,
extended combat/damage, visual weapon-effect origins, clipping extremes and
performance remain open. The final receipt verifies unchanged original
registry/pilot hashes, all source artwork, other chassis registrations, user
settings and eight affected material packs. Launcher checks and preparation
pass. No commit; strict acceptance remains **131/144, paused**.

Execution boundary advanced by R3: the optional native replacement emitter now
keeps an entire donor arm attached to the current torso during original pose
translation changes, through both GPU and CPU projection. Original simulation
and its animation matrices are unchanged. This is a visual adaptation and
bounded native execution result, not accepted-function credit.
