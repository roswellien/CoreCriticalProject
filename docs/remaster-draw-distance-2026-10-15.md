# Remaster scenery distance, 2026-10-15

The native renderer inherited the original main camera's 800-unit far plane.
The investigated IA route did not establish a Vulkan-only distance regression.
The extended Remaster option increases that plane to 3200 units and moves the
distance haze outward proportionally during the main scenery draw. This advances
the native live-mission scenery boundary; it grants no new acceptance credit.
The retained strict count remains 131/144.

After the user rejected the roughly 50% FPS loss, the living launcher's default
was restored to800. The extended settings remain optional; the latest executable,
assets and earlier repairs stay selected. A matched 1800-frame full-profile IA
traversal/yaw check at1600 measured8.295 ms median versus7.462 ms at800,
approximately121 versus134 median-equivalent FPS (about10% lower). That is a
bounded compromise measurement, not approval to change the default again.

The user subsequently approved1600 with fog as the default. At that point the
living launcher selected1600; the scoped fog extension retained haze and doubled its
distance range (64..1500 in the tested IA scene). No executable rebuild was
needed: this is the exact option exercised by the retained1600 test above.

Latest user-requested configuration, 2026-10-15: both **Play MW3Remaster** and
**Play MW3 - Alpha GPU Tests** now select the stock800-unit distance after
another performance report and a report of no visible fog. At800 the Remaster
distance extension leaves the original camera and scene-defined fog settings
in place; fog ranges are no longer multiplied. Executable selection and other
graphics settings stay as configured. Both launcher checks pass. This restores
the stock configuration, but does not establish that visible fog is correct in
the user's reported scene. That visual issue remains open.

Follow-up: the [fog rendering investigation](fog-rendering-investigation-2026-10-15.md)
reproduces the missing fog with the user's actual display-mode setting. A stale
fog cache suppresses initialization on the new gameplay device. Both launchers
now enable the scoped cache repair and select fixed builds, retaining stock800
distance and original weather. The earlier fog-positive tests used a different
original display mode and did not reproduce this failure.

The user's observation of no obvious fog remains valid as a visual report.
Support for fog in a shader alone was insufficient evidence of visible fog.
The controlled Big Lake run subsequently confirmed original renderer fog enabled,
linear mode, range 32..750, fog-enabled terrain batches, and vertex fog alpha
spanning 0..255. Raising clipping alone left the sampled images unchanged;
extending haze as well visibly revealed distant mesa walls and structures.
This does not establish the fog appearance in every reported scene.

## Implementation

`tools/remaster-launcher/apply_draw_distance.py` installs the authored
`native-overrides/draw_distance_stage.inc` into a completed source snapshot.
The local candidate is `local/remaster/gpu-native-long-distance-r1`, based on
the exact published r17 arm-damage source. Its 37,201 translated objects are
unchanged. Only `mfc_stage.hpp`, `d3d_provider.inc` and the new include differ
from that host-source snapshot. The installer reproduces the candidate and is
idempotent. Original media and generated game code remain local.

`MW34_REMASTER_DRAW_DISTANCE` accepts 800, 1600, 2400 or 3200. Missing/800
preserves the original behavior; bad values fail visibly. The extension gates
on the active full-viewport world camera, excludes labcam/zoomcam/camx, and
never reduces a mission's larger original far plane. It restores ownership
before original near/far setters and marks the original footprint dirty.
Original near clipping and object LOD settings remain intact.

Original boundaries used:

- 004F3A70: original near/far setter.
- 004F4170/004F41B0: camera frustum and terrain footprint rebuild, including the
  fused tail body.
- 004B52C0/004F6DC0/004F7030: complete camera draw scope; 004B52C0 covers the
  fused alternate path. Main-camera identity is evaluated after original setup,
  at frustum preparation. Nested scopes do not multiply haze twice.
- 00526BA0/00526C00/00526CD0: recovered renderer fog fields. The extension
  snapshots/restores near, near squared, far, far squared, inverse range and
  density around the complete draw, including exceptions/non-local returns.
  Host FP mode ends before original execution resumes. Fog enable, color and
  altitude behavior stay original. World fog data is never changed.
- 004F5C80/004F61B0: original terrain selection. The original 50 rings and 30
  cells per ring remain fixed. Their exact overflow error is intercepted at
  0049BFD0 to fail visibly before out-of-bounds admission.

Optional `MW34_VIEW_DISTANCE_LOG` records camera range, terrain occupancy,
fog parameters and sampled render fog state. It is disabled in normal play.

## Retained validation

Local evidence is in `local/terrain-distance-investigation-r1/`:
`long-distance-measurements.json`, `long-distance-source-check.json`,
`terrain-800-vs-3200.png`, and the named `runs/` directories.

- Final 800 setting: all 116 Training CPU PPMs and all 1150 Training GPU draw
  records match r17 exactly (`long800-final-TrainingCpu-v2`,
  `long800-final-TrainingGpu-v2`).
- Earlier 800 control: all 1700 IA draw records and four sampled target PPMs
  match r17. The final binary's compatibility path is also covered by the
  final Training checks above.
- Final 3200 setting: IA traversal1700, full Remaster traversal/yaw1800,
  Campaign Mission 1 waterfront2600, Training1150 and cockpit/zoom1000 reach their scripted
  frame budgets. IA/Training/zoom use virtual clocks; Campaign uses the real
  codec/clock and original campaign menu path. These are bounded diagnostic
  exits, not normal-quit evidence or complete mission acceptance.
- IA traversal and yaw reached at most ring33 and 26 cells per ring. Campaign
  and Training also stayed within the original capacity. Full-profile runs
  retain the current seven model bindings, GPU HUD, 3440x1440, FXAA and AF16;
  this does not claim all seven models were observed in each run.
- The zoom run enters, moves and closes the original zoom window. Its terrain
  camera remains at800 while the main camera stays at3200; captured framing,
  target markers and cockpit remain coherent. A separate source review found
  no concrete blocker in the scope, FP restoration, compatibility or tiler guard.
- On the matched IA route, median frame time over frames401..1600 was
  6.94 ms at800 versus7.50 ms at3200 with original geometry/AAoff/AFoff.
  With current models, FXAA/AF16 and HUD assets, the matched yaw route measured
  7.46 ms at800 versus15.02 ms at3200. This is a material rendering-cost
  increase, approximately134 versus67 median-equivalent FPS on the RX9070,
  and is not a benchmark guarantee for other hardware or scenes.
- Initial hidden-window runs either paused after losing focus or failed to
  enter 3D. They are retained and excluded from successful coverage. The
  visible reruns provide the checks listed above.

3200 is a tested extended option, not an all-map safety proof. Cell dimensions,
view direction and map layout affect the unchanged tiler capacity; another map
can still trigger its visible capacity failure. Higher ranges are deliberately
unsupported. Zoom and Mech Lab cameras keep original distance/fog behavior.
Mech Lab layout issues and muzzle/normal-map work are separate and remain open.

The local living launcher stores the setting in `local/remaster/launcher.json`
under `graphics.draw_distance`; changing it to800 restores original distance
and haze. The Python launcher displays the selected distance, and its native
PowerShell helper explicitly passes the same setting. No commit was made.
