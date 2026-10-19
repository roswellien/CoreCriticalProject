# Mad Cat and Vulture: live arm attachments

R4, 2026-10-19. This supersedes the Mad Cat R3 and Vulture R1 attachment claims
in [the earlier joint-fit record](mech-joint-fit-2026-10-19.md). Strict acceptance
remains **131/144, paused**. No commit, desktop screenshot or original pilot/
registry write was made. Original assets and generated executables remain local.

## Reproduced defect and cause

User review still found detached or incorrectly placed arms in-game. Native
front/side captures confirmed it. A private build of the installed host then
recorded original and emitted arm matrices during actual IA walking, mouse
aiming and stopping. Each chassis reached 2500 Vulkan presentations. These are
live translated producers, not substituted saved poses.

The earlier fit used the recovered stand clip's forearm translation. The live
game uses different translations, including the model's loaded bind positions
and aiming updates. Mad Cat's original right-hand lateral offset is about
1.29565 in these live samples, versus 2.442307 in the exported stand reference.
Vulture's live offsets differ still further from that reference. The earlier
shoulder fix left this forearm displacement in place, producing measured elbow
separations up to **1.147158** units on Mad Cat and **1.797140** on Vulture.

Prior fixture counts and clip checks did not cover these live joint positions.
The rear-view native framing also obscured the joints. Those earlier checks
retain their original scope; they do not establish correct R3/R1 attachments.

## Optional visual correction

The existing BWMESH6 format already represents the required fixed links; no new
format or main-engine code change was needed. Each upper arm anchors to its
donor shoulder in the current torso frame. Each forearm anchors to that same
shoulder plus the donor elbow vector rotated in the current upper-arm frame.
The original forearm rotation still aims the arm and all mounted weapons.
Incompatible original pivot translations no longer move the replacement elbows
away from their upper arms. Original animation matrices, weapon origins,
collision, damage decisions, AI and simulation remain read-only.

The existing donor clavicle/shoulder-connector triangles are assigned to the
torso, keeping them seated while the upper arm rotates at its own hinge. No
connector geometry is added. Close geometry uses the recovered donor weighting;
distance triangles are attributed against the corresponding donor component
surfaces. Vulture's complete arm mounts also receive the donor-relative torso
placement that the preceding Vulture revision lacked.

Both distances are registered under
`local/work-ahead/mech-live-attachments-20261019-r4/`:

| Chassis | Close batches / triangles | Distance batches / triangles |
| --- | --- | --- |
| Mad Cat | 40 / 23,084 | 23 / 14,000 |
| Vulture | 34 / 29,822 | 22 / 15,101 |

Triangle counts and triangle-UV multisets are conserved. Other chassis, torso/
leg geometry, source albedo/normal artwork and material choices are preserved.
Material and normal sidecars are repacked for the changed batch ordering.

## Validation and actual execution

- All 15 recovered runtime Mad Cat clip families on both chassis and both
  distances: **3084 pose/LOD samples**. Source Vulture locomotion uses these
  Mad Cat families. Shoulder/elbow pivot residuals remain below 0.000002 units.
- Independent replay of the captured live matrices against the serialized
  payloads: **318 frame/LOD pose sets**. Sampled physical surface probes retain
  small donor hinge clearances, rather than the previous unit-scale gaps.
- Actual installed-adapter fixture: **154,247 checks, zero failures**, including
  636 live side/LOD cases, repacked materials, torso connectors, GPU matrices,
  CPU emission and unchanged guest pose bytes. Existing legacy cases remain
  included. These are fixture checks, not native-game acceptance credit.
- Corrected native base-color diagnostics reach **2500 Vulkan presentations
  per chassis**, with ordinary game camera/input and live aiming. Maximum
  measured elbow residuals: Mad Cat **0.00006394**, Vulture **0.00006232** units.
  Matrix-stack float precision contributes to this small residual.
- Separate material/normal native runs reach **2500 presentations per chassis**
  with live walking/stopping and camera-only front/side diagnostics. Maximum
  elbow residuals are below **0.00006476** units. F9 captures were inspected
  from front and side, including the complete arms. Detached-camera runs do not
  independently establish the full live aiming range; the ordinary-camera
  diagnostics above cover the requested mouse aiming inputs.
- All successful bounded native runs end with the explicit presentation budget
  (exit 1). This is not a normal mission completion, damage test or FPS result.
  Failed capture setup attempts and singleton refusals are retained separately;
  no other game session or writer was interrupted.

The private native builds add read-only matrix logging, and the material capture
build additionally reuses the existing camera automation. Neither diagnostic
addition is shipped in a playable profile.

## Installed launch paths

`Play MW3Remaster.cmd` now selects R4 assets for both chassis. Its executable
remains the already source-matched host:
`local/remaster/gpu-native-madcat-torso-follow-r1/build/entry_commandline.exe`,
SHA256 `546c5616e44f20888ea312c8126440cec9986e64650f2d8c3769e6ac2926f912`.
The original-compatible 116/1150/116 evidence on that unchanged executable keeps
its previous scope; it is not relabelled as a new binary regression run.

`Play MW3 - Material Normal Preview.cmd` had a separate registry still pointing
to the old Mad Cat/Vulture V2 assets and a host supporting formats 1–4. That
profile now uses the same R4 geometry, with its existing normal artwork and
lighting/material settings. Its fresh host adds only the already-authored V5/V6
adapter extensions to the previous material-preview source; all other host
sources and the translated-object list are retained. The mesh adapter is
byte-identical to the completed material capture host's adapter before adding
private probe logging. Capture hotkeys and probe logging are absent from the
playable source.

New material-preview executable:
`local/material-authoring-r1/native-live-attachments-r4/build/entry_commandline.exe`,
SHA256 `a85f211dc4b5e27e39e5e63c1997d5ea9caf82782fb97d4479c3c27db7a468ee`.
Fresh comparisons on this exact binary match **Training116/116,
GPU1150/1150 and IA116/116** against the retained original-compatible baselines.
Its profile points to a new matching source snapshot; no old snapshot is
relabeled.

Both paths retain all 15 model registrations, user graphics/music settings,
39 texture banks and source-snapshot verification. Only the two requested
chassis registrations change. Versioned prepared directories keep the new batch
layouts paired with their material/normal sidecars; the ordinary living launcher
continues preparing current registered assets on each launch. Old prepared packs,
executables and source snapshots are retained. Main, original-model and material-
preview launcher checks pass.

## Review and remaining boundaries

[Private native front/side review](https://drive.google.com/drive/folders/1Qx34jJGwLTQiAHC92EjCaLdEmQQ8CQEm).
These are full-resolution native F9 PNGs with lossless, pixel-identical
recompression only. No generated imagery, resizing, relighting, desktop capture
or sharing-permission change. The separate announcement/trailer hold is not
released by these diagnostic previews.

Detailed logs, frozen build source, fixtures, input routes and publication pins:
`C:/Users/jcbla/.codex/workspace-storage/MW34Recomp/joints-runtime-20261019-r4/`.

Next: observe actual distance transitions and damaged/stump states, then verify
presentation-only weapon-effect alignment. Detailed distance connector
attribution, clipping extremes and final per-chassis performance remain open.
This repair establishes connected visual arm pivots for the observed live
states; it does not close complete model or game-function acceptance.
