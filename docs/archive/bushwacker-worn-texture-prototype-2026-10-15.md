# Bushwacker worn texture prototype - 2026-10-15

The user requested a separate prototype to reduce the clean, flat appearance of
the MW3-inspired Bushwacker without normal mapping or new dynamic lighting.
The existing live R6 shark-mouth set and launcher/model registration remain
unchanged. This work advances offline texture authoring and model preview only.

The prototype adds chipped paint, directional gouges exposing metal, localized
scorch, dirty seams and repair variation. Painted gunmetal detail also restores
readable machinery in areas whose old color map was almost black and depended
on material lighting. The gray/olive camouflage and approved sharp shark-mouth
design are retained. Wear is static, not a simulation of combat damage.

Ignored local workspace:
`local/work-ahead/mw5-bushwacker-extract/mw3-material-r7-worn-prototype/`.
It contains five base-color PNGs, a packed Blender scene, matched front/opposite/
rear/unlit comparisons, a self-contained comparison HTML and a texture ZIP.
Body is 4096 square; Variant and Weapons are 1254 square; Window and MissileHead
remain their existing 64-square images. Weapons previously used a constant fill.

Artwork used built-in image_gen, with the final prompts saved in
`generation-prompts.json` and `mechanical-generation-prompt.txt`. Original MW5
normal atlases served only as offline layout guides for the mechanical COLOR
maps. No normal map or specular effect is applied in the previews. Blender
integrates the painted atlases into the existing UV layout. The original nose
region overrides new paint through the approved geometry-space projection.

Validation: the mesh/topology/UV0/object placement digest remains
`ecc12d3dc3c2e54f8de382eb7b25e387e3ef3d992e8657b6354a676cbc28499a`.
All pinned live source and registration hashes remain unchanged. In the protected
166430-pixel mouth region, the 99th percentile RGB-channel difference is zero;
mean difference is 0.0111/255, maximum49. The bake is therefore not claimed to be
pixel-exact. Both sides were visually reviewed with the original tooth shapes
retained. Matched diffuse renders use identical lights and zero specular; an
emission-only pair shows the texture detail without lighting on the mech.

Private Drive uploads were read back to verify IDs, filenames and destination
folders: [all prototype assets](https://drive.google.com/drive/folders/1l4OsFsYOHbdWGPcmgFcJH_Rjv8TW6Lti),
[front comparison](https://drive.google.com/file/d/1DBQ0XebYD4OFd9-vJ--Q1tZIZHN3S2jj/view),
[unlit comparison](https://drive.google.com/file/d/17eATRqZ85e_pD77hCa8jxgAnwT_HJL-l/view),
[five-map download](https://drive.google.com/file/d/1g777Rf_iNtGfqtY3C2auO2gKa60Wn6H0/view).
Receipts are in local `drive-previews.json`. No sharing permissions were changed.

Limits: generated atlas detail still needs seam/mip and in-game review before
live publication. The expanded Weapons texture has not been benchmarked. No game
was launched, no native regressions were required for this offline art prototype,
and no runtime performance or native acceptance credit is claimed. Accepted
count remains131/144; strict acceptance stays paused. No desktop screenshots,
pilot/registry edits or commit.

Later on 2026-10-15, the user authorized installing this set for the regular
Remaster launcher. [Publication and preparation checks](worn-mech-textures-launcher-install-2026-10-15.md)
record the new texture registration; the earlier prototype/source-pin evidence
above retains its original scope.
