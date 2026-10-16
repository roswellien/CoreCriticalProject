# Orion, Thor and Vulture maintained and well-used textures

2026-10-15. The user requested the new Bushwacker/Mad Cat surface standard on
Orion, Thor and Vulture. Six new Body/Variant color atlases retain the existing
MW3-inspired palettes and paint zones, adding irregular edge chips, thin
steel-exposing scrapes, dirt in recesses, restrained soot and service wear.
Orion retains blue-gray angular markings over warm gray; Thor keeps muted
gray/olive armor; Vulture keeps pale gray, warm gray and blue-gray panels.

Built-in image_gen authored the six color edits. Body normal maps were layout
guides for painted mechanical detail, not modified outputs. All three donor
Weapons normal atlases are byte-identical to Mad Cat's
`1a85f78797f2bd4d646093d471c7160c5b1c12b3afe0792794d685332e95f611`,
so its completed gunmetal color atlas is reused with the UV/detail identity
verified. Each set has five base-color PNGs: Body/Variant/Weapons at the native
generated 1254x1254 size; Window/MissileHead retain their exact 64x64 source
files. Previous main sources were 2048x2048; this is painted readability rather
than a resolution increase. No normal/roughness/metallic maps are modified.
New painted scars have no authored normal relief; the future 12x-equivalent
normal response remains separate native material work.

Ignored workspace: `local/work-ahead/orion-thor-vulture-worn-r1/`.
Each chassis has retained generated art, texture PNGs, a five-map ZIP, source
identities and a packed Blender scene. Exact final prompts, including the shared
weapon-color prompt, are in root `generation-prompts.json`. The self-contained
comparison HTML includes matched front/opposite/rear and emission-only pairs.
Fixed diffuse lighting, pose and camera are identical within each pair; no
normal maps or specular reflections are used. Mech geometry, UVs, material
assignments and placement are preserved, as are source scenes and payloads.

| Chassis | Fitted parts | Preserved geometry/UV/pose SHA256 |
| --- | --- | --- |
| Orion | 32 | `70574a5fd4329df186a7b942ee7313809321e303c0419907bfad41f4895d96ad` |
| Thor | 21 | `83ed0874ef0efd197aa27f2362973dfec48d5a0c8f21bf1031b385e2b2362053` |
| Vulture | 32 | `026e153cabe4b67afe2f841cd7bdc37850fc84d5410154d4cad9f51250096616` |

Updated only these three models' five texture paths in local `models.json`.
The regular `Play MW3Remaster.cmd` now repacks these registered colors each
launch. Its actual `--prepare-only` execution exited successfully without
starting the game. Independent parsing verifies every RGB565 pixel, material
name, content hash, dimension, batch mapping and file boundary in four staged
files: Vulture 32 batches/9,451,864 bytes; Thor 21/9,451,820; Orion LOD0
32/9,451,864 and LOD1 22/9,451,824. Six unrelated prepared files, including the
installed Bushwacker/Mad Cat sets, remain byte-identical. Other model records,
mesh bindings, launcher scripts, current native build/profile and old/new source
PNGs retain their identities. Existing seven models and 39 banks remain; Avatar
is excluded. Rollback registry/prior sidecars and checks are in `publication/`.

Reviewed the armor/weapon atlases and rendered texture-only views for all three,
with additional opposite/rear and diffuse before/after views. Twenty-five Drive
files and nine child folders were verified by metadata readback, including
identity/name/parent checks. No sharing settings changed. Files are organized
under Textures / this dated batch / chassis / Previews and Texture set.

- [All comparisons and texture sets](https://drive.google.com/drive/folders/1JHLP161TwOdbraA9DIs1wM_CyPalZk0B)
- [Orion texture-only comparison](https://drive.google.com/file/d/1IZZpXUsO-HdrE8fF2U92N_fWx0iwE6HM/view)
- [Thor texture-only comparison](https://drive.google.com/file/d/1Fgt5ga5ks84dt5xZPr6hDbC7c7nTxelL/view)
- [Vulture texture-only comparison](https://drive.google.com/file/d/1CKG6ybQDb-e_wQt6FfC-4nrRs6FXJO53/view)

Execution boundary advanced: selected color files now resolve and prepare for
the existing native model adapter. This is asset preparation and offline art
review, not new in-game execution, seam/mip acceptance or performance evidence.
No game launched, desktop screenshot, MW3/mw34-registry.txt or pilot edit, or
commit. Other active builders and the composer/watcher were untouched. Strict
acceptance stays paused at 131/144; in-game appearance/playtesting remains open.
