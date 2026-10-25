# Vulture default skin and size review — 2026-10-24

The default Vulture/Mad Dog color textures now expose gunmetal detail at the
hip, knee, arm, weapon and foot mechanics. Pale worn color stays inside armor
edges. The previous MW3-derived blue contours, yellow service marks, red tabs
and blue cockpit remain. Local PBR authoring maps add metallic and lower
roughness at those edges for Blender review; the current native BWTEX color
pack does not consume metallic or roughness maps.

The revised Body, Variant and Weapons color records are installed for both
native detail levels in the standard and Codex-app local mech packs. Their
Vulture model records and both color payloads match across the two roots.
The BWTEX batch tables and Window/MissileHead records are preserved. Other
models, alternate skins, geometry, controls, normal payloads and game logic
were not edited. The fitted preview retained its geometry/UV/pose and action
digests. This is a texture-resource change, with no acceptance credit; the
strict count remains 131/144.

In the standing authoring scene at identical world scale, raw MW3 bounds are
6.47 × 7.64 × 10.52 units and updated-model bounds are 9.08 × 10.99 × 11.91.
The updated antenna produces most of the height excess: the 99th-percentile
torso top is 10.27 versus MW3's 10.52, about 2.4% lower. The different arm
and weapon stance expands the full horizontal bounds, while the torso group
itself measures 5.17 × 3.88 versus 6.47 × 5.03 for MW3. Scaling the whole model
to match raw bounds would shrink the hull and legs, so geometry was retained.
This is a standing-pose offline comparison, not live animation or combat proof.

Evidence, receipts, source maps and comparison views are in
`local/work-ahead/vulture-default-skin-20261024-r2/`. Remote previews:
[Drive folder](https://drive.google.com/drive/folders/1YrKuMMwNq3U844CTpHjp3_HCAVhok8Mb).
No commit, installer or R2 publication was made.
