# Orion default skin caution repair — 2026-10-24

The Orion MW5 replacement's default Body and Variant colors now include the
prepared MW3-style caution bands and service marks with lighter armor wear.
The first installation of the edge-wear candidate damaged the caution bars:
its broad dark-pixel mask turned portions of their black stripes pale. The
corrected maps restore pixels around every yellow marking from the pre-wear
detail atlases. This restores stripe contrast while retaining the lighter
surrounding armor edges. The unchanged Weapons atlas already has textured
gunmetal surfaces rather than flat black.

The corrected color maps are under ignored
`local/work-ahead/orion-default-skin-20261024-r2/textures/`. Both local optional
MW5 mech packs now bind those maps for Orion at close and distant detail. Their
Body and Variant BWTEX records changed; Weapons, Window, MissileHead and Collar
records, batch tables, geometry, normals, registry entries for other mechs,
and gameplay were preserved. The existing Orion height and collar fit remains
as recorded in [the earlier repair](orion-height-and-collar-2026-10-21.md).

Checks: focused before/edge/repaired crops show the black-yellow bars restored;
the installer verified all unchanged material records byte for byte in both
detail levels and both pack roots. Native `--prepare-only` succeeded after the
correction and its session profile resolves the corrected close and distant
Orion payload hashes. A bounded native run presented 1180 Vulkan frames, but
the older scripted menu route did not enter gameplay, so it yielded no Orion
render or screenshot. A direct menu inspection was also attempted; the window
capture API returned a suspended GPU device error. That review process was
stopped after the failed capture. Live in-game visual QA remains open.
The strict acceptance count remains 131/144. No commit or public package was
made.

Remote review: [Orion Drive folder](https://drive.google.com/drive/folders/1OdgovTQzg9QVnzKyBqFxxLZ-V6mLFMw1),
including the repaired Body and Variant atlases and the caution-bar comparison.
