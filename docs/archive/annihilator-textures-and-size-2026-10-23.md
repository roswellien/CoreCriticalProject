# Annihilator textures and visual size — 2026-10-23

The local developer mech pack now carries an Annihilator that is 5% larger at
both native detail levels. The complete corrected-neck assembly is scaled
together around its existing actor-local origin / foot baseline. This advances
the native replacement-model asset boundary only. No native executable rebuild,
original gameplay change or acceptance credit is involved (131/144 retained).

The BWMESH4 donor rest matrices have their first three rows multiplied by 1.05.
That scales each bone's basis and actor-local position once. Original control
references, gait metadata, bone-local vertex bytes, normals, UVs, material and
visibility bindings remain identical. The existing arm alignment and both neck
covers are retained. Standing world positions at every vertex were compared to
the prior payload multiplied by 1.05: maximum error 3.56e-15 at both LODs.
LOD0 retains 34 batches / 86,526 vertices; LOD1 retains 34 / 52,878.

The accompanying default color pass replaces tan paint with pale gray, lightens
painted bevel wear, and uses original MW3 red/gold torso details as references.
It was made with the built-in image generation tool. The Body and Variant
atlases remain 1254 × 1254. Weapons, Window, MissileHead, the normal payload and
alternate-skin texture payloads remain unchanged. The geometry increase applies
to all skins. Both default BWTEX1 payloads use the same revised color bank; the
batch table and the three other material records are byte-identical.

Assets, imagegen instruction records, matched assembly stills, source pins,
packing checks, installation backup and receipts are under:
`local/work-ahead/annihilator-markings-20261023-r1/`.

Installed content-addressed payload identities:

- LOD0: `3e10b0190931afaa1632a11315f8c3fb1ec15c936cc682e7e85e6918028b0900`
- LOD1: `1a3db67d24af15bd749c1f12851c31c8c37ef4f59b2883a1890ad8bcb27faea6`
- Default colors: `d771f54d1455c0cf4d3032a683d99da05aa323c0971ed56201ab9bdebf500a85`

Only Annihilator bindings and the matching pack manifest pins were changed.
Both local authoring registries reference the revised mesh/metadata and colors.
Other models and current native host/profile settings were preserved with
compare-before-write checks. No setup, R2 download or published pack was rebuilt.

Validation: assembly review includes all 12 mesh objects, including the cockpit
and neck covers. Geometry/UV/pose and action digests are unchanged by the color
pass. Pack payload/registry SHA checks passed. `play_remaster.py --check` passed
with all 38 environment banks and 18 models recognized. The matched Blender
stills review colors and assembly, not live-game behavior or the new scale.
An independent native performance benchmark was running, so no additional game
session was started. Live motion, damage, distance transition and visual firing
alignment still require an in-game check; no new coverage is claimed.
