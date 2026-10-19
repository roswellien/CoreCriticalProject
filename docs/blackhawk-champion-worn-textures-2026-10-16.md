# Black Hawk and Champion maintained-but-well-used color sets

The user correctly observed that Black Hawk's improved walking preview still
used the clean initial color draft. Both Black Hawk and Champion lacked the
stronger surface treatment. They now have separate revised Body and Variant
albedo atlases: visible tapered paint-cut scars exposing dark steel and small
silver cores, irregular chips, rubbed edges, local soot/heat staining at existing
hardware, dirty seams and maintenance wear. Most muted MW3 gray/olive paint
remains intact. This is static painted service history, not combat damage.

The built-in image generation tool edited four atlases, using each existing
color atlas as the edit target, the matching donor normal as a hardware/layout
guide and Thor R2 as a wear-intensity reference. Exact prompts and generated
source identities are retained in the ignored revision:
`local/work-ahead/mw3-blackhawk-champion-r1/maintained-worn-r1/`.
New Body/Variant colors are the tool's native 1254x1254 output; prior inputs
were 2048x2048. Normalized UV coordinates are unchanged; this is an art/detail
revision, not a texture-resolution increase.

Both donor Weapons normal atlases exactly match the existing Mad Cat atlas:
`1a85f78797f2bd4d646093d471c7160c5b1c12b3afe0792794d685332e95f611`.
The completed 1254x1254 worn gunmetal Weapons albedo can therefore be reused.
Window/MissileHead, all normals, roughness and metallic maps remain byte-identical
to each initial set: 17 preserved maps per chassis. New paint scars have no newly
authored normal relief. Existing Blender normal response is retained; the future
approved 12x-equivalent native response remains separate renderer work.

## Geometry, animation and review

Black Hawk uses the user-approved donor-proportion `leg-correction-r2` scene.
Champion uses its existing fitted candidate. The texture pass changes no mesh
coordinates, topology, UVs, weights, part placement, rest joints or action curves.
The saved packed scenes retain the previous PBR normal/roughness/metallic setup;
only the existing Base Color image connections change.

| Chassis | Visible model parts | Preserved geometry/UV/pose digest | Preserved animation digest |
| --- | --- | --- | --- |
| Black Hawk | 14 | `df5b1b944a17d16d852e2c347bca18e404395abca216dc39ce5b6e0e0cf4cf03` | `21937b3d618bffc83cc55c579d9989a1dc625824537352988586854901d52ed7` |
| Champion | 30 | `4840e4d0a7d24e1e040f904c0cb0630552dbda8f486360e79bf7955f937d4523` | `b2eeaf1c6b2c5247d95f87762f714ccf6fdeaee306c3e2d3346f118f11a3faf5` |

Matched front/opposite/rear/close diffuse and front emission-only views isolate
the actual color revision, without normal/specular enhancement. The generated
atlases, front/close/unlit and rear model views were reviewed. Seams, mipmaps and
native appearance remain pending live review. Generated painted detail is not
a guarantee of pixel-exact donor hardware preservation.

The new Black Hawk walking video uses the same approved animation, materials,
normal response, lighting and front/side cameras, with revised colors. It is
1440x720, 336 frames, six cycles over 11.2 seconds. Independent evaluation of
the saved worn scene repeats the 449-time joint contact check: maximum knee
error 0.00000258, ankle error 0.00000160, local scale error 0.00000036. Geometry
and animation identity checks are independent of texture appearance.

## Delivery and execution boundary

Each chassis has a packed `.blend`, full 20-map texture ZIP, five standalone
albedos, material manifest, README and matched comparisons; local HTML links
the views and video. `latest-materials.json` and the existing selection record
now identify these color sources for future port integration.

[Private Drive comparisons and texture sets](https://drive.google.com/drive/folders/11aIvVfTZvc31I1EdX44pZ1NTHdqasHUr)
are organized under Textures / dated batch / chassis / Previews and Texture set.
The publication receipt records upload and metadata readback identities.

Both chassis remain offline port candidates. The playable launcher still uses
its existing seven model registrations. The rejected stretched Black Hawk
payload remains guarded; its proper native visual retarget, damage/falls,
firing-origin alignment, LODs and performance checks remain open. Champion's
existing fitting/muzzle limitations are unchanged. No live game result or
native execution advance is claimed by this art pass.

Source scene/map identities and the installed registry/profile are unchanged.
No game launch, desktop screenshot, protected registry/pilot edit or commit.
The composer/watcher processes were preserved. Strict acceptance stays paused
at 131/144; this work grants no native acceptance credit.
