# Avatar nose and capture repair â€” 2026-10-23

The Avatar evolution footage exposed an attached original cockpit in detached stock views, an incompletely seated detailed nose, a pale front-panel UV sample, and incorrectly assigned dark canopy facets crossing the painted windshield frame.

## Presentation changes

- Detached stock Avatar views omit only the authenticated attached cockpit roster. The complete original Avatar LOD0/LOD1 chassis and cockpit mesh names/counts must match. First-person views, unknown trees and the original exterior remain intact.
- The detailed nose has a rearward skirt seated into the hull. Original model points and rig controls are unchanged.
- The detailed nose and canopy use the full original painted `avatar02` layout. Seventy-two facets previously selected by a donor-normal heuristic no longer draw dark glass across the windshield frame. The separate original head glass remains.
- The detailed mesh has 36,071 triangles and 117 batches at both detail levels. Primary and Bâ€“H skin tables are matched to the revised batches. Existing color/normal image bytes are preserved; only geometry, UVs and batch bindings change.

Local editable assets: `local/work-ahead/avatar-nose-repair-20261023-r1`. The active authoring registry and installed Updated MW3 Mechs pack have matching Avatar resources. Other chassis entries are unchanged. Prior manifests and launcher profile are backed up under `reports/avatar-nose-fix-20261023`.

## Engine and capture correction

The earlier series used an October 20 capture fork and a compatible older frozen configuration. Its overrides also stripped HD menu resources and surface/world/water/surf/cloud normal resources. This did not represent the complete current engine setup.

The replacement capture fork derives from `D:/MW3PerformanceUpdate-20261023-r1/host-source`, retaining October23 body dispatch and rendering changes. Only camera automation, bounded encoder backpressure in offline capture mode, and the scoped Avatar interior filter differ. Video runs explicitly disable diagnostic frame dumps, matching the ordinary launcher default; periodic diagnostic readbacks otherwise bypass the full-resolution video path. The translated game module is byte-identical to the selected October23 runtime. The local play runtime at `D:/MW3AvatarRepair-20261023-r1` includes the two-file interior filter without camera automation.

The corrected capture executable is `D:/MW3AvatarCapture-20261023-r2/entry_commandline.exe`; the recipe is retained at `C:/Users/jcbla/MW34SunTests/avatar-evolution-repair-20261023`. The 120-frame control and complete 1,680/1,680/3,120-frame source checks pass. Discarded shorter first attempts remain local and are not delivery inputs.

Replacement comparisons retain the current environment assets and global normal mapping in all stages. For the first two stages, 17 full-content Avatar surface-normal bindings are explicitly unperturbed while all other catalog bindings and image payloads remain unchanged. The original-texture bank index changes only the two mech archives; all 37 other current bank paths remain intact. Sunset, spawn and camera framing remain consistent.

## Checks

- Latest-engine native four-angle detailed Avatar review: front, 30Â°, 60Â°, 90Â°; windshield artifacts and pale panel removed; nose seating reviewed.
- Export: both LODs, 336 pose frames, maximum owner/object matrix error 1.4305e-6; rig retained.
- Selected play runtime: ordinary first-person Instant Action run reached its 1,400-frame budget. The active launcher plan validates with preserved graphics settings and resource capabilities.
- Installed pack validates on the selected engine; all Avatar mesh, albedo, normal and skin batch tables equal 117.
- Matched source sky and terrain patches are pixel-identical across all three stages; global normal mapping and current menu/world/surface resources are retained.
- Actual updated menu capture confirms the 5760Ã—4320 HD background and 53 sprite entries; full current environment capture reaches Grasslands.

Execution boundary advanced: presentation and media capture only. No translated gameplay code, guest initialization contracts, acceptance criteria or native-game credit changed. Strict acceptance remains 131/144. No commit, YouTube publication or public asset release is authorized by this repair.

## Delivery

The corrected Avatar video, both thumbnail files and description replaced their existing Drive files in place, preserving IDs, parent folder and sharing. Readback verifies sizes. The local full-resolution master is `reports/avatar-evolution-repair-20261023/avatar/Avatar-Evolution_YouTube_1440p60.mp4` (287,324,810 bytes). Both delivery video versions contain 6,361 frames at 60 fps and pass full decoding. Source nose close-ups, final transition review and receipts are retained alongside the new master. Other existing mech videos were not re-recorded in this Avatar repair.
