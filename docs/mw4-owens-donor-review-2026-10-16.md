# MW4 Owens donor review

2026-10-16. The user asked to examine the MW4 Owens for a possible MW3 port.
This pass recovered and reviewed an offline donor. It does not install a new
runtime model or change gameplay. Strict acceptance remains paused at 131/144.

## Recovered inputs and tools

Read the existing local MW4 Mercenaries installation's `RESOURCE/core.mw4`,
`props.mw4` and `textures.mw4` directly. No game content was downloaded and no
game or installer was launched. Archive identities, selected members, payload
offsets and decoded hashes are retained under ignored
`local/work-ahead/mw4-owens-r1/`.

REA rejected this custom #VBD archive as an unsupported format. The existing
directory observations were reused, followed by the source-only
[MW4 Tools importer](https://github.com/voidvoidvoid/MechWarrior4_Tools/tree/a4275d44f0b396d6aeee5fda76acf05bca6caf99),
pinned to commit `a4275d44f0b396d6aeee5fda76acf05bca6caf99`. The 22 downloaded
Python/documentation files total 256,497 bytes; Git blob identities and SHA-256
hashes were checked. No license file was found, so the tool source stays local
and is not incorporated into distributed project code. Existing Blender 5.2.2
was used without installing an add-on into the user's preferences.

The archive reader requires exact-size LZW decoding and bounded resource
extents. A catalog limited to the three named archives avoids recursive scans
of unrelated folders. Only plain stored/LZW members are used; no decryption
profile or protected-wrapper keys are required.

## Result and comparison

- Recovered 36 hierarchy joints, original rest transforms and rigid bindings.
- Exterior: 20 mesh objects, 935 triangles, including the original torso canopy.
- Separate interior: four cockpit cage/dashboard meshes, 186 triangles.
- Six textures resolved without import errors; exterior body detail is 512x512.
- Most intact body parts have six source LODs. Only LOD 0 is displayed here.
- Recovered 146 animation Actions, including shared Raven locomotion clips
  explicitly selected by the Owens animscript. Fourteen original MW3 Owens
  motion clips were also recovered as future fitting inputs.

The initial all-parts render included `joint_cage`, a first-person interior
resource. Inspection showed it uses only dashboard/frame textures and distinct
component masks. Its four meshes are hidden in the exterior reviews and excluded
from the exterior glTF. No canopy geometry was added or moved. The original
all-parts scene and intermediate render remain available as diagnostic history.

Original MW3 geometry has 347 source polygons, triangulating to 774 triangles.
The donor's triangle count is about 21% greater; this is a modest geometry
increase. The MW4 shape is wider and has different leg/body proportions.
Comparison PNGs use uniform complete-height normalization, including MW3's
antenna tips. This exaggerates relative donor hull bulk and is explicitly
labelled as a static comparison, not the final scale. Native fitting should use
hull and pivot landmarks while preserving donor segment lengths.

## Motion and materials limits

The walking video repeats the recovered 2/3-second `rvn_walk` cycle six times:
32 distinct phases at 48 fps, encoded as 192 frames / four seconds / 960x960
with H.264 CRF 8. It is a Blender donor-motion review, not a MW3 gait port.
Geometry/topology/UV hashes match before and after rendering. The source clip's
end/start matrices differ by up to 0.0022592 after display normalization;
this retained source seam was not silently corrected. Native blend decisions,
motion-bearing root channels and runtime procedural controls are not emulated.

The still comparisons use original MW3 textures and MW4 raw detail textures.
MW4 camouflage/team composition and native shader states are not reproduced;
the raw detail colors are dark. Body alpha is a camouflage mask, not body
transparency. UVs remain unchanged. No upgraded paint, scars or normal maps
were authored. Recovered torso UVs use a restricted atlas region; texture-stage
or native composition behavior remains unverified. Existing MW5 12x normal-map
approval does not make a new MW4 normal map available automatically.

## Saved output and next boundary

[Front comparison](https://drive.google.com/file/d/1tIhsrhVYFo_5qYEazNuSqPjq4tQUFlWr/view).
[Recovered walk](https://drive.google.com/file/d/1fzr2YYsMbTX94sa-A4B2cJbR6eZhYCol/view).
[Organized Drive folder](https://drive.google.com/drive/folders/1W9xIqZEEiBaZ09VuHWjOmkUZYCcUnJdL)
contains front/rear/side comparisons, donor views, motion review, scope notes
and original texture files under separate Previews and Textures folders.
Ten uploaded files and three folders were verified by metadata readback.
Remote byte counts match the saved local files. Sharing was not changed.

Local `previews/comparison.html` links the lossless images, video and packed
Blender scenes. `candidate-assets.json` identifies the exterior-only static
glTF at original donor scale, recovered source scene and review scene.

Execution boundary advanced: installed MW4 archives -> bounded decoded
resources -> assembled textured donor and offline source-motion review.
Next is scale/control/gait retargeting onto MW3's controls without limb
stretching, followed by MW3-inspired maintained-but-well-used materials and
weapon/firepoint, damage/detachment, LOD and live performance validation.
Six visible missile openings per pod do not establish weapon or muzzle parity.
No native compatibility or completed-port claim is made.

All asset/tool outputs remain ignored local. Existing launchers, model
registrations, other asset work and protected processes were left alone.
No desktop screenshots, registry/pilot edits or commit were performed.
