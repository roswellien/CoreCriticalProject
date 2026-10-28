# MW3 runtime 1.0.40 dynamic-lighting texture fix

Published October 25, 2026 to the signed playtest update feed and the protected
playtest download page. The launcher remains 1.0.41-preview.

The remote playtest screenshot `mw3_20261025_163353_513.png` showed RGB normal
directions in place of the original base texture colours across terrain and
the player mech with Dynamic Lighting enabled. The native sun uniform assigned
the normal-map enable flag to `ambient.w`, but the fragment shader interprets
that field as “display normals as colour.” The fix clears that diagnostic field
while continuing to bind normal maps for lighting.

The published 1.0.39 native host source snapshot reproduced the defect with
the updated GPU lighting fixture: `Normal mapping must not replace textured
colour with normal diagnostics`. Applying only the uniform correction to that
snapshot made the same fixture pass on the Vulkan device. The signed native host
was rebuilt from that pinned source. Runtime 1.0.40 changes only the host and
its profile pin; 667 other registered runtime files match 1.0.39 exactly.

The signed `1.0.40.mw3update` and matching `1.0.40.zip` passed original-input
verification, installed/activated runtime validation and rollback with sequence
retention. Both public objects passed complete download/hash and HTTP Range
checks. The protected website wrapper and both Setup catalogs passed R2 readback.
Signed catalog sequence 2026102508 was promoted last. A real 1.0.41 launcher
client discovered the 1.0.40 MW3 update alone from the live feed. The external
test laptop has not yet confirmed the visual result.

The current full installer is still launcher 1.0.41 with runtime 1.0.39. Fresh
installers should use the launcher Updates screen to install runtime 1.0.40
after game setup. Existing captures and selected game paths remain intact.

Private local evidence: `D:/CoreCriticalLightingRepair-20261025-r1/`.
No original game media or generated game code was committed. Strict native
acceptance remains 131/144; this repairs enhanced lighting presentation.

Download: [MW3 runtime 1.0.40 update](https://playtest.corecritical.dev/updates/1.0.40/1.0.40-mw3-update.zip).
