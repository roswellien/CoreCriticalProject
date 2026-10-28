# Installed environment-pack effect lighting

After disabling Operation 1 Textures and Lighting, the remote tester can load
C1M1, Training and Instant Action, but reports no weapon/explosion/map-item
dynamic lighting and a blocky, incorrect sky. This isolates the loading failure
to the enabled Operation 1 resource path; it does not verify visual fidelity.

A separate concrete installed-profile defect was found: the staged native
runtime has `MW34_EFFECT_LIGHTS=0`, while the working development profile has
it set to `1`. `prepared_environment_packs.profile_bindings` restored a selected
pack's validated effect catalog but retained the disabled staged default.
Mission lighting does not override this global effect-light enable flag.

The maintained coordinator now enables effect lights when it binds a validated
environment pack's effects catalog. No packs or only Shared Original Mech
Textures leave the service disabled. Five asset-free environment tests pass,
including a staged disabled default becoming enabled with a selected pack and
remaining disabled without the required resources. Native rendering code is
unchanged; no original execution or gameplay acceptance is claimed.

This source correction is **not yet deployed** to the tester. A future runtime
package must copy the corrected `prepared_environment_packs.py` into its
coordinator and refresh manifest pins; rebuilding a launcher around an old
Runtime directory alone does not include this correction.

The Operation 1 pack also owns C1M1's mission lighting settings and sky texture
resources. Disabling it removes those settings and selects original textures.
The effect catalog identifies complete prepared texture contents, so merely
enabling the service does not establish that every original C1M1 effect matches.
Stock-texture compatibility and independent lighting selection remain to be
handled alongside the texture-memory repair. The blocky/off sky has not been
visually reproduced or repaired. The source change does not fix the virtual
surface arena exhaustion, and no further high-resolution pack load is claimed.
