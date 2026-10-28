# Mad Cat maintained and well-used texture prototype

2026-10-15. The user requested the Bushwacker wear approach on the Mad Cat, with
the appearance of a maintained but well-used machine. This isolated base-color
prototype keeps the MW3-inspired muted sage/gray/olive armor and charcoal steel,
adding chipped paint edges, thin cuts exposing steel, dirty recesses, restrained
vent/weapon soot and more readable mechanical surfaces. Broad painted panels
remain intact; there is no simulated damage, new geometry or gameplay change.

Workspace: `local/work-ahead/mw3-cinematic-mechs-r1/madcat-worn-textures-r1/`.
Built-in image_gen edited Body and Variant color atlases and painted the formerly
flat Weapons atlas using its existing donor normal map solely as a layout guide.
The three generated PNGs are retained at their native 1254x1254 dimensions;
source main maps were 2048x2048. Window and MissileHead retain their exact 64x64
source PNGs. Final prompts are saved in `generation-prompts.json` and the input
identities in `source-manifest.json`. No normal, roughness or metallic map is
modified; new paint scars have no authored normal relief yet. The selected future
12x-equivalent normal response remains a separate native material integration task.

The source is the existing fitted Mad Cat walking scene, with 38 fitted parts.
The preview uses fixed diffuse-only materials with zero specular and an identical
pose, camera and light setup for both texture sets. Emission-only views isolate
the painted appearance. Original MW3 comparison objects are hidden for review;
the fitted mesh topology, UVs, material assignment and placement are preserved.
The packed scene, five-map ZIP and self-contained comparison HTML stay local.

No game launched, desktop screenshot, pilot/registry edit or commit. Other
processes/writers were left untouched; rendering was deferred until the observed
performance test had ended. Live assets and registration remain unchanged. This
advances offline art authoring only, with no native execution or performance
claim. Strict acceptance stays paused at 131/144. Generated atlas seams, mip
behavior and game readability remain validation work before live publication.

Validation completed: all pinned source images, fitted scene, native source
payloads and registration/profile files matched their starting hashes after
rendering and packaging. The fitted geometry/UV/pose digest remained
`aa46bd18a1700f351adb3c0d8872e533f3c4b2450ad1cdddda1ea1e9dca558ec`.
Both front sides, rear and texture-only views were visually inspected. The
diffuse views are intentionally matte; the texture-only pair best exposes the
painted difference. Sixteen Drive files were verified by metadata readback for
identity, name and parent. Sharing permissions were not changed. Folder
organization is Textures / Mad Cat / dated prototype / Previews and Texture set.

- [All prototype files](https://drive.google.com/drive/folders/1qmixvZwjNdplg7P6QX807oN6gbmvwdFY)
- [Texture-only comparison](https://drive.google.com/file/d/1--QRJGSEw0EoJ-I8NppUxQf2MiWDjeQe/view)
- [Five-map ZIP](https://drive.google.com/file/d/1jxtyS1TC0VmSVYXAyVcJC3Hfs2GJiCSY/view)

Later on 2026-10-15, the user authorized installing this set for the regular
Remaster launcher. [Publication and preparation checks](worn-mech-textures-launcher-install-2026-10-15.md)
record the new texture registration; the earlier prototype/source-pin evidence
above retains its original scope.
