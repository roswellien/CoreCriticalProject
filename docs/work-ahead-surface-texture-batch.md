# Work-ahead surface texture batch v1

Status: **prepared for visual review**. Scope: eight non-effect assets, five mech panels and three terrain materials. The accepted full-AI direction from the earlier texture batch is used for these new drafts.

The offline [review gallery](../local/work-ahead/surface-texture-batch-v1/review.html) compares decoded sources with aspect-preserving 4× AI review exports. The [complete package](../local/work-ahead/surface-texture-batch-v1.zip) contains exact inventory source/container/index mapping, hashes, generation prompts and settings, raw generated results, editable OpenRaster documents, a manifest and checksums.

| Asset | Type | Source size | Review size | Source record |
| --- | --- | ---: | ---: | --- |
| `annihilator01` | Mech panel | 128×64 | 1024×512 | `rmechtex.zbd` index 80 |
| `bushwacker04` | Mech panel | 128×64 | 1024×512 | `rmechtex.zbd` index 576 |
| `firefly01` | Mech panel | 128×64 | 1024×512 | `rmechtex.zbd` index 1400 |
| `orion01` | Mech atlas | 128×128 | 1024×1024 | `rmechtex.zbd` index 1750 |
| `puma01` | Mech panel | 128×128 | 1024×1024 | `rmechtex.zbd` index 2158 |
| `c1m4road` | Terrain | 64×128 | 512×1024 | `c1-rtexture.zbd` index 52 |
| `rockfbase` | Terrain | 128×128 | 1024×1024 | `c1-rtexture.zbd` index 232 |
| `sandtrans2` | Terrain transition | 128×128 | 1024×1024 | `c1-rtexture.zbd` index 235 |

These are AI drafts, not accepted replacement assets. Compare markings, panel boundaries, terrain features and especially the broad `sandtrans2` transition in the gallery. The source identity is inventory-backed; UV assignment, tiling, renderer behavior and in-game compatibility are still unknown. No effects textures are included.
