# Supernova default skin review — 2026-10-24

This pass updates the **default MW5 replacement Supernova skin**. It does not change geometry, animation, other skins, the native renderer, or gameplay.

The MW3 `supernova08` shoulder source shows four short red service bars. The new Body atlas restores those bars on the corresponding shoulder housing. An attempted second copy crossed a UV seam, so it was removed after a rendered check. The blue cockpit and existing pale worn armor were retained. UV-covered flat black mechanical paint was replaced with textured blue-gray gunmetal. Body, Variant, and Weapons maps received brighter worn metallic edges, with corresponding offline metallic and roughness authoring maps.

The previous MW3-to-MW5 standing-height ratio is 0.999999685195 (see `docs/supernova-port-progress-2026-10-16.md`), so no size change was applied. Matched Blender renders verified the color treatment from front, opposite, rear, and close views. The render script verified unchanged geometry, UV, pose, and animation digests. `play_remaster.py --check` passed after installing the new BWTEX default color payload in both local pack roots. This check does not substitute for an in-game visual inspection.

Remote review: [Supernova default skin review](https://drive.google.com/drive/folders/1mg6ISQEV6Y1kr243feZrR2MIUq4eKrC4). It contains front/close and opposite/rear before-and-after boards. Local sources, receipt, render script, and installation backups are in `local/work-ahead/supernova-default-skin-20261024-r1/` (ignored by Git). Original media remains local.

No native-game acceptance credit is claimed; the verified count remains 131/144. Weapon and damage alignment, LOD transitions, and live lighting still require in-game review.
