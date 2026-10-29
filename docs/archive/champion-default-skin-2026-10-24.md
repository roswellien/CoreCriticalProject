# Champion default skin review — 2026-10-24

The optional MW5 replacement Champion default skin now carries three faded yellow service chevrons on the upper pod, based on the MW3 `champion06` source. Placement was checked with a marked Body-atlas render. The blue cockpit and pale worn armor remain. UV-covered flat black mechanical paint was revised to textured gunmetal, and Body, Variant and Weapons color maps received lighter worn edges. Matching metallic and roughness maps are offline authoring assets.

This installation changes only the default LOD0 and LOD1 BWTEX color payloads in both local model packs and the two authoring registries. Other Champion skins, model geometry, animation, weapon bindings and other chassis are unchanged. The earlier 5% Champion size correction remains in place. Local preinstallation bytes are retained under `local/work-ahead/champion-default-skin-20261024-r1/installation-backup/`.

Matched Blender front, close, opposite, rear and unlit renders verified the color placement. Geometry, UV, pose and animation digests did not change in the comparison scene. `play_remaster.py --check` passed after installation. A live in-game check remains needed for lighting, damage, LOD and weapon views.

[Private Google Drive comparison boards](https://drive.google.com/drive/folders/1qx3HQ7nwBb2XBDVFDLQSOuTJNSd6MMDK) show before and after. Local textures, mapping evidence, scripts and receipts are under ignored `local/work-ahead/champion-default-skin-20261024-r1/`. Original media remains local. No commit was made; this asset pass makes no native-game acceptance claim, which remains 131/144.
