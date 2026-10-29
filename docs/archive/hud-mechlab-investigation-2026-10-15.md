# HUD repairs and Mech Lab investigation — October 15

The user reports completing the first campaign mission with r8. This is a
user play milestone, beyond the previous automated mission-entry test, and is
recorded for tonight in the [rolling development summary](session-summary-2026-10-15-remaster.md).
It does not grant new strict acceptance credit. Acceptance stays 131/144, paused.

## Findings and disposition

| Report | Evidence and current disposition |
| --- | --- |
| A: player status background extends beyond frame | Reproduced at 3440x1440. Corrected by retaining the originating right anchor through the original translucent polygon queue. |
| B: enemy status background extends beyond frame | Same queue defect, with a left anchor. Corrected in matched native captures. |
| C: red/yellow small-radar lines | Not established as a defect. A matched current-native 1920/3440 comparison has identical yellow-line pixels; red differs by five edge pixels. This is not an original-executable ground-truth comparison. No radar change. |
| D: zoom fails to follow off-center aim | User clarified that the small cross moves away from the box center. Remains open. A fresh edge sweep traces the actual child sprite, including cockpit and native 4:3 controls: steady offset stays constant; brief opening/closing offsets are observed. Timing clarification is pending. No zoom repair is claimed. |
| E: missing per-part enemy condition colors | Replacement geometry used static texture/color and suppressed original diagnostic draws. Restored original MW3 schematic geometry in the two exact status-preview scopes; world models remain replacements. Both previews render in captures. Progressively damaged individual parts still need an observed controlled hit sequence; no complete damage-color validation is claimed. |
| F: weapons box much wider than names | Same deferred-anchor loss as A/B. Corrected; original padding/layout retained. |
| Mech Lab | User entered directly after completing Mission 1. Original hybrid 2D/3D frontend has inconsistent enhanced composition paths. Investigation only; no Lab implementation changes. The genuine Win/Continue/loader/Lab route is statically traced; its failing live render still needs capture. |

## Deferred panel repair

Original background producers return through 43C767 (enemy), 43C77D (player),
43C797 and 43C7C2 (weapons). Those roles were already classified correctly.
However, service 57BF80 queues translucent polygons at 80CD9C rather than
drawing immediately. Later 57E110 sorts descriptor indices and draws at
57E2EA, after the owning widget ancestry has returned. The host classified
them then as world geometry. At this aspect ratio their widths were about
43/24, or 1.79 times the corrected foreground width.

`tools/remaster-launcher/native-overrides/hud_deferred_stage.inc` retains
host-owned role metadata keyed by the exact descriptor and guarded by frame,
primitive type, vertex pointer/count and untextured identity. Sorting therefore
does not lose the owner. The D3D provider reads the original API return at
guest ESP (57E2ED); provider calls bypass the translated-call ancestry stack.
Metadata resets with the original queue lifetime, including exception cleanup.
Original vertices, descriptors, alpha, sort order and draw stream are unchanged.
Unknown polygons retain their existing classification.

`tools/remaster-launcher/apply_hud_repairs.py` applies these authored changes
to a fresh private r8-compatible host source tree. It also excludes replacements
under exact status-preview return PCs 441480 and 442A87. The original geometry,
part traversal and effective diagnostic material state execute there. There is
no host health estimate, whole-mech red tint or gameplay damage change.

An independent source review caught and corrected the initial API-return guard
before validation. Native frame 1000 subsequently records both left and right
roles restored from the late world role, across the original sorted queue.

## Validation and execution boundary

Published Remaster build: `local/remaster/gpu-native-r9-hud/build/entry_commandline.exe`, based
on frozen r8 with its unchanged 37,201 translated objects. The r8 codec timing
repair and r7 performance changes remain in the build.
Its SHA256 is `4cf4ea6a70f3f232d972a6f0478ad24f597bc0bb49662d67e250dac9e2ab3e71`.
The launcher check verifies this hash-pinned r9 profile, current 39 texture
banks, Bushwacker/Mad Cat/Vulture/Thor, music and 3440x1440/FXAA/AF16. The
previous r8 profile is retained in `local/remaster/launcher.r8-backup-20261015-hud.json`.

- Original-compatible Training: 116/116 PPM files identical to r8.
- Mode-7 GPU Training: original draw count/hash stream identical, 1150/1150.
- Original-compatible Instant Action: 116/116 PPM files identical to r8.
- Enhanced Instant Action: 720-frame matched runs at 1920x1440 and 3440x1440,
  FXAA, AF16, current texture banks, four registered model bindings and r5 HUD.
- Additional 1150-frame ultrawide run verifies left/right queue metadata at
  flush. Native target dumps show corrected player/enemy backgrounds and
  weapons padding. Original input selects an enemy, holds zoom, moves aim
  right/up and back, and releases zoom. No desktop screenshots.

All budgeted runs deliberately stop with the frame-budget exit. They use copied
installations and frozen input, and guard the user's installed registry/pilot
hashes before and after. No simultaneous user game was running. Original files
are unchanged; composer/watcher processes are preserved. No commit.

Local evidence: `local/hud-mechlab-investigation-r1/validation.json`, source
snapshot under the candidate, `runs/r9-*`, and scoped `markers/`, `damage/`,
`mechlab/` evidence. Generated code, media and full native captures remain local.
Preview delivery uses the existing private Google Drive project organization.
[Before/after panel comparison](https://drive.google.com/file/d/1nHEnZm-nu-Yg55NkpQKZPk46rEk6xxAP/view?usp=drivesdk)
and [full native view](https://drive.google.com/file/d/1_rDtmPAM7SahoaiSYQ6d8CR6BDCGUMtb/view?usp=drivesdk)
were uploaded to the Rendering/HUD investigation folder and metadata read back.

Boundary advanced: correct enhanced presentation of the original deferred HUD
panels, and original condition-schematic draw eligibility with world replacements
enabled. No new gameplay closure, Mech Lab behavior or strict acceptance advance.

## Mech Lab root cause and proposed direction

The [layout and timing follow-up](mechlab-layout-timing-investigation-2026-10-15.md)
records the user's layout-only confirmation, original delta-based preview
rotation, current clock behavior and the still-unverified high-FPS interaction
risk. No universal30 FPS Lab limit or Lab implementation is established.

Original 448960/44FFC0 creates `labworld`, `labwindow`, `labcam`. 450460/44FEA0
uses the original rectangle (210,52,430,288) for both logical and output preview
placement. The intermission loop draws original 2D controls, the embedded 3D
preview, then presents them. Its own camera is not a full-view combat camera.

The enhanced host retains original raster blit coordinates, narrows unidentified
non-world 3D draws around the target center, and presents resident targets over
the full ultrawide width. A CPU/readback presentation instead fits the complete
buffer into a centered 4:3 image. Thus UI and preview can receive different, or
repeated, mappings depending on residency. These are concrete source-level
inconsistencies. Which combination occurs in the user's broken screen has not
yet been observed: the copied current pilot opened the Mission 1 map with the
Mech Lab button disabled. No campaign flags were changed to force access.

There is also a conditional absolute-pointer route through ScreenToClient. If
active, it needs the inverse of the displayed frontend canvas mapping. Activation
has not been established, so it is a risk to verify, not an observed input bug.

Recommended first repair, for discussion: compose the original controls and
preview as one coherent 4:3 frontend canvas, then fit it once. At 3440x1440 this
is a 1920x1440 area centered at x760. Preserve widget positions, lab camera,
clipping, dragging and hit rectangles. Use an explicit frontend composition
mode across CPU blits, resident presentation and readback; pair absolute input
with that mapping only when applicable. Expanding the actual layout across all
3440 pixels requires a separate coordinated UI, scrolling and hit-test redesign.

Before implementation, capture a genuine accessible intermission Lab state.
Then validate selection/rotation, armor/weapons/ammo editing, drag/scroll,
confirm/cancel and transitions at 4:3 and ultrawide. Mech Lab remains unchanged
as requested. The next HUD blocker is an exact reproduction of the zoom drift;
damage progression and original-radar semantics also remain bounded checks.

## Follow-up: precise zoom symptom and direct postmission Lab

The user confirms the small cross inside the box is the drifting element, and
the Lab was entered directly after Mission 1 completion. These answers replace
the earlier route/element questions; a further question distinguishes steady
zoom, opening/closing and a locked zoom window.

A fresh private diagnostic host based on r9 logs original child-cross return
442F09 separately from ordinary-reticle return4441FC, and records software HUD
vertex coordinates before/after display adaptation. It is not published to the
launcher. Tests use original Z and mouse input for center, far right, far left,
return, release and another zoom/lock request. The original command binding for
Z was checked; actual child draw coverage is measured instead of inferred from
a screenshot of the ordinary aiming sprite.

Three isolated cases run1200/1150/1150 frames: ultrawide external view,
ultrawide cockpit and native1920x1440 external control. Each has493 paired
cross/border frames. In492 the midpoint difference stays approximately0.5
logical pixel in both axes. The first image frame has10.5 pixels in both axes
on all three cases. Source inspection explains the initial image-assignment
order: positioning can precede the first image being assigned, then corrects
on the next update. The ordinary aiming reticle also appears against the still
closing border for a few frames; at a clamped right edge its center can differ
by45 logical pixels. This is a separate sprite from the active child cross.
The baseline reproduces the opening transient; source control flow accounts
for the closing overlap. Persistent active-child drift remains unreproduced.
Do not widen the zoom camera or change every world/reticle anchor on this evidence.

Evidence: `local/hud-mechlab-investigation-r1/zoom-followup-validation.json`,
`zoom-edge-measurements.json`, `markers/zoom-cross-source-contract.md`, and
`runs/zoom-edge-*`. The same37,201 translated objects are used. Only private
authored logging is added; r9 launcher/hash and production rendering are
unchanged. Actual registry/pilot hashes remain unchanged, and no user game was
running when these bounded tests launched.

The direct postmission Lab route is now statically distinguished from reload:
Win/Continue47D030 -> campaign continuation47D1F5 -> original Load state6 ->
enabled campaign action2 ->448830 -> modal Lab6059F8, using the live campaign
owner and selection. Original408EF0 explicitly disables Lab when the selected
campaign identifiers are1/1. Therefore the grey button in the reloaded initial
map is expected and does not reproduce or contradict the user's postmission
case. Campaign resource `MECHLAB` is distinct from multiplayer `MECHLAB_BUTTON`;
the campaign icon center is314,442 (the earlier317,440 click remains inside it).
Detailed checked source slices and route limits are retained in
`mechlab/postmission-route.md`. The exact campaign-progress persistence
instruction remains unresolved in this bounded static trace.

Lab implementation remains paused for the requested discussion. Its eventual
rendering check must preserve and exercise combat -> Win -> loader -> Lab,
including resident-target/canvas state restoration. No save fields or mission
flags were changed to force access. The proposed unified frontend canvas is
unchanged; no new native acceptance credit is claimed.

## Resolved follow-up: locked zoom scene alignment, r12

The user clarified that the window is locked, initially observed in cockpit
view, and then identified the same symptom during the external-view test:
the **magnified world scene** separates from the cross as aim moves away from
center. This distinction resolves the earlier investigation's limit: measuring
the child cross against its border did not measure the scene beneath them.
Those cross/border measurements remain valid, but did not rule out this defect.

The source confirms a display-coordinate mismatch. Original 57AB2F..57ABA2
sets a full-target D3D viewport, while 43FA40 updates the actual movable zoom
camera viewport. Original CPU projection uses that camera's center. The host's
`WideZoom` adaptation instead used the full D3D scissor midpoint. At logical
1024x768 that midpoint is512, even when the zoom camera center is778 or225.
Scaling about the wrong point displaces the scene increasingly as the window
moves off-center. This explains the apparent acceleration mismatch without
changing mouse acceleration or original camera motion. The zoom camera retains
its original5-degree FOV; it does not receive the world camera's Hor+ widening.

The r12 repair scopes the exact442F50 zoom owner, reads its validated `zoomcam`
viewport and snapshots its center on each queued command before EndScene. This
also covers the mask issued before camera binding. Original TL geometry,
replacement GPU projection and their clipping use that common camera center;
the direct GPU HUD path obtains it within the same scope. Missing metadata
fails visibly. No guest positions, input, FOV, draw order or gameplay arithmetic
are changed. Public authored sources are
`tools/remaster-launcher/apply_zoom_alignment.py` and
`tools/remaster-launcher/native-overrides/zoom_alignment_stage.inc`.
Independent read-only source review found no blocking defect.

Validation on exact executable SHA256
`99dcd7f66679b4e9f5bb74ecab8daf1f6e8766ec7d43b371514ea01fb6875acc`:

- Training CPU116/116 PPMs, mode7 original draw stream1150/1150, and IA116/116
  PPMs match the frozen r9 baseline.
- Matched1050-frame locked-zoom sweeps at3440x1440 cover cockpit and external
  views, right/left movement, return and release. Each before/after pair uses
  identical input and identical original draw frame/count/hash. Native captures
  show the off-center scene aligned with its frame; the centered and released
  captures are unchanged.
- The matching1920x1440 cockpit control has identical original draw streams
  and all seven sampled native presented captures unchanged.
- A1500-frame real-clock cockpit run with a private copy of the current pilot
  reaches1219 frames with3D and a locked off-center anchor968. This checks
  normal timing separately from the deterministic sweeps.

`Play MW3Remaster.cmd` now selects the completed r12 executable. It retains r9
HUD repairs, r8 codec timing and r7 speed changes, the same37,201 translated
objects,39 texture banks, four registered models, FXAA/AF16 and local music.
The preserved r9 profile is `local/remaster/launcher.r9-backup-20261015-zoom.json`.
Evidence: `local/hud-mechlab-investigation-r1/zoom-alignment-validation.json`
and `local/remaster/gpu-native-r12-zoom-alignment/source-snapshot.json`.
[Before/after locked zoom](https://drive.google.com/file/d/15KlhtnTq6AMaRYGdE8UWzJ-4qMXX7g-V/view?usp=drivesdk)
and [full cockpit capture](https://drive.google.com/file/d/1rPHxNUjSWqlHiFp8B4KP2-WDQUl8Zas7/view?usp=drivesdk)
are in the existing private Rendering/HUD folder; upload metadata was read back.

Boundary advanced: enhanced zoom scene presentation follows the original camera
viewport off-center, including locked cockpit use. This is bounded IA evidence,
not a new campaign completion replay or exhaustive model-fidelity check. Original
opening/closing sprite transients remain. Controlled per-part damage and original
radar semantics remain open; Mech Lab is still diagnosis/proposal only pending
discussion. Actual registry/pilots and composer/watcher processes were preserved.
No desktop screenshots or commit. Acceptance stays131/144, strict lane paused.

## Follow-up: intermittently missing target triangle, r14

The user reports the target triangle sometimes disappearing while zooming.
Original440B00 first tests the target through the zoom camera (53CF10 return
440CC6), then falls back to the main camera when needed. It intentionally hides
a normal-view marker that would sit underneath a magnified view of a different
area. Original440510 also clips each of the triangle's three edges; a large
magnified target can legitimately leave no visible edges. These policies remain.

Two enhanced-display defects were found and reproduced:

- The normal-marker occlusion comparison still used the original full logical
  zoom rectangle, although its displayed horizontal footprint is narrower.
  In the matched cockpit test at frame490, zoom bounds were574..664, center619;
  the main target projected to583.606812. All three line widgets were hidden,
  even though that point is left of the displayed window, whose corresponding
  comparison edge is593.662781. The same input on r14 executes the original
  normal-camera triangle builder and displays the marker beside the window.
- The three line draws at returns4414B8/C8/D8 were always classified as normal
  world markers, even when440510 had used the zoom camera. Their geometry and
  clip rectangle now share the zoom scene's captured scaling center. The exact
  original camera choice is captured per owner/frame; global zoom visibility
  is insufficient. Lead cues and offscreen arrows keep their existing behavior.

The occlusion repair lets original40DA30 finish its coordinate conversion, then
adapts only the clipped-zoom temporary X at return440CD1, inside the exact
440B00 target-owner scope. That temporary is used solely by the subsequent
horizontal occlusion comparisons. The zoom-inside branch, projection clip flags,
main-camera projection, target selection and gameplay remain unchanged. The
current hardware coordinate profile0 is required; unknown alternate conversion
profiles fail visibly rather than using guessed coordinates. Original triangle
construction, per-edge clipping and legitimate overlap hiding still execute.

Authored public implementation: `tools/remaster-launcher/apply_target_marker_alignment.py`
and `native-overrides/target_marker_stage.inc` under that directory. A fresh r12
host was patched and rebuilt as r14; independent source review found no blocker.
Its SHA256 is `c57f7c5bf53c1350453d7531f615f86ba59bac64308fe4aef512d28c6e97e929`.
The same37,201 translated objects retain prior r12/r9/r8/r7 fixes.

Training116/116 PPMs, original mode7 draw1150/1150 and IA116/116 PPMs match r12.
The matched1000-frame cockpit test at3440x1440 fixes the false hide and the
zoom-projected marker; intended hiding remains at sampled frames590/610.
Original D3D draw streams remain identical. The1920x1440 control has identical
draw streams and all14 sampled native presented captures are byte-identical.
This is bounded IA coverage, not proof that every reported disappearance has
the same cause or a new campaign replay.

The requested Vulkan validation layer was unavailable: vkCreateInstance returned
-6 before game entry. That attempt is retained with no test credit; the normal
renderer run passed. A separate early diagnostic run rejected unsorted scripted
input; the corrected fresh run supplies the evidence. No validation-layer success
or zero-error claim is made. Evidence: `local/hud-mechlab-investigation-r1/target-marker-validation.json`
and `local/remaster/gpu-native-r14-target-markers/source-snapshot.json`.

The normal Remaster launcher now selects r14; r12 is preserved in
`local/remaster/launcher.r12-backup-20261015-target-markers.json`. Graphics,
textures/models, local music and Avatar exclusion are unchanged; `--check` passes.
[Before/after target triangle](https://drive.google.com/file/d/1fC3dHRi6LrtwyLeCGP6tou8ZAiwnOEuI/view?usp=drivesdk)
is in the existing private Rendering/HUD folder with upload metadata read back.
The rolling daily summary and project memory are updated. Actual registry/pilots
and existing composer/watcher processes remain unchanged; no desktop screenshots
or commit. Acceptance stays131/144, strict lane paused. Mech Lab is still
diagnosis/proposal only; progressive damage and original-radar checks remain open.
