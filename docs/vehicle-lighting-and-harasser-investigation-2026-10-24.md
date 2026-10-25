# Vehicle lights and Harasser stance

Tracked centrally in [known playtest issues](known-issues.md) as MW3-001
(Harasser stance) and MW3-002 (vehicle lights).

User reports: destroyed APCs can leave ground illumination behind; vehicle lights
shine all around rather than forward; Harassers can appear rear-high/nose-low.
The investigation preserves the October 24 guest-heap collision repair and
existing content, controls and gameplay. Acceptance stays **131/144**.

## Vehicle lighting repair

The current native fixture cache retains proven sources off camera. Its source
proof deliberately excludes node visibility/activation flags to avoid losing
scenery lights during culling. Original vehicle animation definitions, however,
switch their `healthy` branch inactive and their `destroyed` branch active on
destruction. Ignoring that semantic activation lets vehicle emitters outlive
their healthy model. Wreck geometry can also reuse a light-bearing body texture.

The APC body uses the `tredtruck09` family. Its registered illumination is a point
light, explaining illumination in all directions. Original geometry confirms
front surfaces at local Z about -4.59/-3.82 have outward normals facing -Z;
three upper surfaces using the same texture face upward. Turret firepoint
positions independently establish vehicle forward as local -Z.

`apply_vehicle_lighting.py` applies a narrow repair to the completed native
lighting snapshot:

- Recognize the original `veh_` scene ancestry and its healthy/destroyed branch.
  Light-source proofs require the vehicle and healthy branch active bits, checked
  separately from unrelated rendering/culling flags. Shadow-caster proofs retain
  their existing behavior, so wrecks can still cast shadows.
- Do not admit illumination from destroyed vehicle branches or anonymously
  retained vehicle observations without a proven geometry/lifetime source.
- For the known vehicle headlamp texture, retain its exact UV regions and material
  identity, use the original vehicle's world-space forward axis, reject rear/side
  surfaces, and submit the existing spotlight protocol. Scenery point lights and
  other material definitions retain their previous types.
- Manager-owned directional definitions have stable lifetimes; registered global
  definitions are not modified. No texture repack or shader-protocol change is
  required.

The helper is `native-overrides/vehicle_lighting.hpp`. Apply the patch after the
original fixture polygon/proof and UV-region integration has completed. It fails
visibly on unexpected source structure instead of silently producing a partial
patch. Evidence/build directory: `D:/MW3VehicleRepair-20261024-r1`.

Fifteen authored checks pass for branch activation/destruction, unrelated flags,
directional definition lifetime, front/back/side admission, spotlight direction,
unchanged scenery point-light retention and source removal. Native Training smoke
checks use isolated copied saves/settings, the full prepared packs, and the
supported controller path. Live APC destruction and off-camera combat appearance
still require playtest confirmation; a frontend-only campaign attempt is not
counted as vehicle combat evidence.

DEV delivery uses `D:/MW3VehicleRepair-20261024-r2/Runtime`, signed host SHA-256
`aaa5881fa9f4b72cc9f3c1277d81c37d25510ed9ea5ced4ba49759751f4ce1a0`.
The activation check detected an intervening campaign-environment build and
refused the first activation. Revision 2 merges onto that newer snapshot,
preserving its six campaign-policy/shader files exactly, plus the heap and
controller repairs. Only the fixture manager, fixture observation stage and new
vehicle-lifetime helper differ from that parent. The merged build passed its
own 500-presentation Vulkan Training check, signature verification and coordinator
preflight. The DEV profile changes only native executable/module and snapshot
identities; other fields and user preferences are preserved. Public downloads
were not republished and no commit was created.

## Harasser investigation — unresolved

Original decoded Harasser supports are level: all four have local Y about
0.06687, with front Z about -4.67096 and rear Z about 2.45537. Neither the current
18-mech replacement pack nor stock texture pack substitutes Harasser geometry.
There is no supported basis for applying an arbitrary constant model rotation.

Read-only original-game analysis uses the existing Ghidra 12.1.4 project; the
input SHA-256 is
`95bc2c114c9b2e5c5ada8e40ca78cc79470f862e45313ffad0d1e8e6d4d916bf`.
Recovered analysis is private in `vehicle-*.json` under the evidence directory:

- `0x49eed0` extracts the four named support nodes; `0x49ef40` parses the motion
  definition. The supplied Harasser definition uses the tracked-vehicle path.
- `0x4a1240` dispatches through `0x4a12c0` and `0x4a1760` for tracked motion.
  `0x4a23f0` gathers ground contacts; `0x4a1760` derives and damps orientation from
  those contacts, then updates the original pitch/roll state.
- No verified cause or Harasser physics/model correction has been identified.
  A mission example and whether the vehicle is stopped on flat ground distinguish
  excessive pitch from normal terrain-following behavior.

An optional local-only diagnostic build and its source are retained as
`pose-trace-entry_commandline.exe` and `pose-trace-source/`. It observes original
support/contact values without changing them. Those diagnostic dispatch hooks
are excluded from the production lighting repair. The original program database,
game files, saves and configuration are not modified by the static analysis.
