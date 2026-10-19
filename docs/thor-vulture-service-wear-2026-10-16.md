# Thor and Vulture stronger service wear

The user reminded us that both sets should follow the maintained-but-well-used
directive. Review found Thor already had its stronger R2 revision installed,
while Vulture was still on the weaker R1. Retain Thor R2 unchanged and bring
Vulture to the stronger standard. This is not a new Thor R3 revision.

Vulture R2 adds visibly readable tapered paint cuts exposing steel, irregular
edge chips, contact abrasion, dirty seams, maintenance wipe areas and stronger
localized launcher/vent fouling. It preserves the existing MW3-inspired warm
gray, pale gray and blue-gray paint zones. Most paint remains intact. Body and
Variant were edited with the built-in image generation tool, using their exact
prior color atlases, matching donor normal-layout guides and Thor R2 as the wear
reference. Exact prompts and generated source identities are saved in the
ignored `local/work-ahead/orion-thor-vulture-worn-r2/vulture/` revision.

Both edited maps retain the prior generated 1254x1254 dimensions. Weapons,
Window and MissileHead remain byte-identical to Vulture R1. No normal,
roughness or metallic edits; the new painted cuts have no newly authored normal
relief. The future approved 12x-equivalent normal response remains separate
renderer work. These are static service markings, not dynamic damage states.

## Review and launcher delivery

Matched front/opposite/rear diffuse and front emission-only views isolate the
color change. Generated atlases and model front/unlit/rear views were reviewed.
Vulture's 32 fitted parts preserve coordinates, topology, UVs and standing pose:
SHA256 `026e153cabe4b67afe2f841cd7bdc37850fc84d5410154d4cad9f51250096616`.
Existing source scenes, mesh payloads and original controller/weapon behavior
are unchanged. Generated paint detail still needs live seam/mip review.

Only Vulture's texture paths change in `local/remaster/models.json`. Rollback
registry and previous Vulture sidecar are retained in the revision's publication/
before/. Actual root `Play MW3Remaster.cmd --prepare-only` exits 0. Independent
parsing verifies every RGB565 pixel, dimension, material name, hash, batch
mapping and file boundary of the new Vulture sidecar: 32 batches, 9,451,864 bytes.
The other nine staged sidecars, including installed Thor R2, are byte-identical.
The other six model records, meshes, native executable/profile, seven-model
roster and 39 texture banks are retained; Avatar remains excluded.

Thor's current five registered color paths and PNG identities match its R2
manifest; the staged Thor sidecar retains its previously pixel-verified R2
digest `7fbd2abe18a56ee906148c02deb0a7f208eaa49e86365632a9e915819b183822`.
Its existing geometry/UV/pose digest remains
`83ed0874ef0efd197aa27f2362973dfec48d5a0c8f21bf1031b385e2b2362053`.
The installed sidecar checks use the existing registration scope, not an
unpublished additional LOD.

[Both current R2 sets and comparisons on private Drive](https://drive.google.com/drive/folders/1_OrNxlxZ7SFANNRF3mbkU1dIyy6YR0BJ).
Twenty-five files and seven folders were verified by metadata identity/name/
parent readback. Organized under Textures / dated review / chassis / Previews
and Texture set, with five PNGs, ZIP and notes per chassis. Thor's art is reused
unchanged; its package/labels simply join it with the newly revised Vulture.
No sharing changes or email. Local overview/HTML and publication receipt are in
`local/work-ahead/thor-vulture-wear-review-2026-10-16/`.

Execution boundary: the regular launcher now prepares both latest color sets.
No game was launched, so this is asset-preparation and offline visual evidence,
not live appearance/performance validation or a new native execution result.
No desktop screenshots, protected registry/pilot edits or commit. Composer/
watcher processes and other writers were preserved. Strict acceptance remains
paused at 131/144; no native credit is claimed.
