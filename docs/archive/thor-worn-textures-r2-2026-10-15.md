# Thor wear and surface-detail revision R2

Reviewed again and retained unchanged on 2026-10-16, alongside the stronger
[Vulture R2 and combined previews](thor-vulture-service-wear-2026-10-16.md).

The user rated the first Thor skin subpar and identified wear/surface detail
as the problem. R2 retains its MW3-inspired pale gray/olive colors and armor
zones, adding clearer directional steel-exposing cuts, irregular paint chips,
recess dirt, service marks and localized soot. Built-in image generation edited
only the Body and Variant color atlases. Weapons, Window and MissileHead are
byte-identical to the prior installed set. No normals, roughness or metallic
maps were changed; the new painted scars have no newly authored normal relief.

Ignored revision: `local/work-ahead/orion-thor-vulture-worn-r2/thor/`. It retains
exact prompts, generated sources, five PNGs, a texture ZIP, packed Blender
scene and matched front/opposite/rear/unlit comparisons. The two edited maps
are 1254x1254. Geometry, UVs and pose across all 21 fitted parts retain digest
`83ed0874ef0efd197aa27f2362973dfec48d5a0c8f21bf1031b385e2b2362053`.
Diffuse and unlit comparisons were reviewed; this remains pending user review.

Installed only Thor's texture paths in `local/remaster/models.json`. The actual
root `Play MW3Remaster.cmd --prepare-only` path exits 0, without a game launch.
Independent parsing verifies every packed RGB565 pixel, dimensions, material
mapping and boundaries in the staged Thor sidecar: 21 batches, 9,451,820 bytes,
SHA256 `7fbd2abe18a56ee906148c02deb0a7f208eaa49e86365632a9e915819b183822`.
The other nine prepared sidecars are byte-identical. Other six model records,
the installed Bushwacker waist correction, native build/profile and seven-model
roster remain intact. Prior registry/Thor sidecar are retained in publication/
before/. This revision follows the existing Thor registration; it does not
claim to publish an additional runtime LOD.

[Organized comparisons and texture set on Drive](https://drive.google.com/drive/folders/1ndBarMrjHudGPku6iDDAjKMMnO0GOdXz).
Twelve uploads were verified by identity/name/parent metadata readback, under
separate Previews and Texture set folders. No sharing changes or email.

Execution boundary: current launcher preparation resolves the revised Thor
colors. Offline rendering and asset preparation do not establish in-game
appearance, performance or native acceptance. No desktop screenshots, game
launch, protected registry/pilot changes or commit. Strict acceptance stays
paused at 131/144. The future 12x-equivalent native normal response remains
separate renderer work.
