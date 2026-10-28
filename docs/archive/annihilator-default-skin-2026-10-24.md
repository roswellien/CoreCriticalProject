# Annihilator default skin review — 2026-10-24

The optional MW5 Annihilator's default skin now uses textured dark gunmetal on
previously flat dark Body/Variant regions and a restrained lighter-metal wear
pass on pale armor edges. Weapons metal receives a small detail lift. This is
a UV-locked edit of the existing color atlases. The earlier MW3-derived red
front-torso marks and gold grille remain visible. No new decorative decals
were adopted: an image-generated experiment introduced unsupported red accents
and was discarded before installation.

The corrected colors and PBR authoring maps are in ignored
`local/work-ahead/annihilator-default-skin-20261024-r2/textures/`. Both local
optional mech pack roots bind the new Body, Variant and Weapons color records
for both native detail levels. Window and MissileHead records, batch tables,
model geometry, normals, UVs, animation, alternate skins, and other mech
registrations were preserved. The native BWTEX path consumes the color maps;
the updated metallic/roughness maps are for authoring review and are not yet
runtime metallic/roughness inputs.

The already-installed 5% geometry increase remains. The original MW3 and
initial replacement standing heights matched to within 0.00001% in the
earlier port review; the installed replacement is therefore about 5% taller
than that original standing-height measurement, as requested in the subsequent
Annihilator size repair. The installed close-mesh hash remains
`3e10b0190931afaa1632a11315f8c3fb1ec15c936cc682e7e85e6918028b0900`.
This texture pass makes no further size or attachment adjustment.

Validation: matched Blender renders show the before/after skin and preserve
the geometry/UV/pose and animation digests. Installation checked the exact
preimage texture hash, all unchanged BWTEX material records, and both pack
roots. `play_remaster.py --check` completed with all 18 registered models.
This establishes the optional asset and launcher-registration boundary, not a
new native-game acceptance item; strict acceptance remains 131/144. Live
in-game visual, motion, firing-origin, damage and LOD review is still open.
No commit, public release, R2 upload, or evolution-video replacement was made.

Remote review: [Annihilator default-skin Drive folder](https://drive.google.com/drive/folders/1--bU6XrumK3qF8lbF6EvqomUxuXe1h8p).
