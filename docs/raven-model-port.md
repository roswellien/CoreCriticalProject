# Raven model port: local motion prototype

Issue [#133](https://github.com/roswellien/MW3Recomp-Private/issues/133),
2026-10-30. An assembled MW5 Raven RVN-3L now follows original MW3 Owens and
Strider motion through the existing donor retarget solver in offline previews.
Owens is the preferred starting point for leg motion, not Raven aim limits.
The owner selected completing the RVN-3L visual/animation prototype and deferring
the playable loadout. This is **not an installed chassis,
a playable Raven, or a native gameplay result**. No runtime source or installed
pack changed, and no native execution boundary advanced.

## Donor assembly

The owner's installed MW5 archive supplied the body, exterior cockpit, shared
skeleton, declared RVN-3L loadout/hardpoints and weapon meshes. The assembled
LOD0 model has 16,954 triangles: 14,325 body, 679 cockpit and 1,950 across the
five weapon modules. The source assembly includes two medium lasers, SRM-6,
TAG and NARC. Its six attachments use source-declared bones/sockets and retain
ten muzzle markers, including the six SRM tubes. This does not execute any
MW5 weapon or equipment behavior.

The body has 136 skeleton joints and 29 bones used by vertex weights. Its
inspected vertices each use one bone, and every named joint required by the
native donor solver exists. Source metadata declares four LOD entries; only
LOD0 is converted in this prototype. The initial motion preview uses donor Body/Variant mask
and normal textures, an authored olive palette and the existing 12x-equivalent
normal reference. Weapons and glass use review materials. It is not a final
skin or demonstrated native material response.

## MW3-inspired texture study

The first local field-enamel set applies muted olive-grey armor, dark
machinery, dusty mottling and restrained scuffing to the same RVN-3L assembly.
Local Owens textures and the existing Strider texture study informed the
appearance. This is an authored interpretation, not an original MW3 Raven skin.

The set has 17 PNG maps: Body and Variant each have 2048-square base color,
roughness, metallic and normal maps; Weapons and MissileHead each have
512-square base color, roughness and metallic maps; Window has three constant
16-square maps. Base colors use sRGB, while material data uses non-color space.
The two normal maps are unchanged donor files, with the existing Blender 10.2
strength. They are not newly authored normals.

An authored enamel swatch combines with the donor color and wear masks in
Blender, then emission-bakes into the existing UV layouts without scene
lighting. Green wear-channel values provide light scuffing and red values dark
lines as an artistic choice, not a recovered claim about MW5 shader semantics.
The saved scene uses those baked maps, including weapon and cockpit materials.

The local build checks vertex, face and UV fingerprints before and after the
material assignment. Front, rear and walking-pose Cycles renders support the
visual review. These are offline views: native response, gameplay-distance
readability, mipmaps, damage states and pack integration remain unvalidated.
The motion/contact limitations below are unchanged.

The texture study lives in ignored `local/raven-textures-mw3-r1/`, with
`review.html`, the editable `raven-mw3-field-enamel.blend`, `maps/`,
`build_texture_set.py`, the artwork prompt and `texture-set.json`.

### Revision 2: maintained but well used

The owner's review found the first set too plain. Revision 2 makes worn edges
lighter and more metallic, with lower roughness at exposed metal while keeping
most armor painted. It adds sharper surface scratches, localized gouges and
soot-marked impact scars on inspected armor UV regions. Existing MissileHead
surfaces use yellow enamel. These are authored appearance details, not game
damage events or new damaged-mesh states.

The revision keeps the 17-map layout and unchanged donor normals. Source art,
the bake recipe, previews and packed Blender scenes remain under ignored
`local/raven-textures-mw3-r2/`. Revision 1 is retained. No original installation,
runtime or installed pack changes.

### Independent torso aim

The Raven rig contains `Torso_Twist`, and the existing donor solver separately
derives it from the original `torso` control while deriving `Pelvis` from `hip`.
Reusing Owens leg motion therefore does not require locking Raven torso yaw.
The decoded stock MW3 definitions list Owens `maxYaw` as 15 degrees and Strider
as 75 degrees; neither is a recovered Raven limit.

An offline diagnostic passes an authored +/-45-degree yaw sweep through the
existing compiled solver. It rotates torso and arm controls together while
holding pelvis and leg controls at their respective standing or walking poses.
The resulting Blender scene retains separately named standing and walking aim
actions. The sweep is a binding check, not native gameplay or an assertion of
the final Raven yaw range. Final aim limits and gameplay integration remain
deferred with the playable loadout.

Across 33 standing and 57 walking samples, the diagnostic's lower-body matrices
match their neutral counterparts exactly. Maximum tested upper-body matrix
error against the requested yaw is 0.000001431, and maximum attachment error
is 0.000001908. Reach-clamp counts are unchanged. These checks establish the
offline solver/binding behavior, not live aim input, collision or firing.

## Source identity

The current archive differs from the older extraction inventory. Its freshly
read main-index SHA-1 verifies; footer/main-index SHA-256 values are respectively
`38ee021b623a5b6c5c3df38ae6534456f04786cb82ffbca416d6a4030580853a`
and `03334ce11e0ff66a1cb3ba5e5eef74993f74c398a8cfa80cf7b83a56ea2ac1b5`.
The full archive was not hashed or unpacked. Existing repak 0.2.3, the local
CUE4Parse exporter configured for UE4.26, and Blender 5.2.2 performed the
conversion. A skeleton-only glTF export is unsupported by the exporter; the
body glTF includes the reference rig and the body/cockpit exports succeeded.

## Controller comparison and fit

Raven's measured upper/lower leg ratio is 0.383, against Owens' 0.515 and
Strider's 0.822. This favored Owens for the first experiment; motion testing
then provided stronger evidence. Both comparisons use the same Raven geometry,
uniform scale and 9.9015-unit standing-height target derived from stock Owens.
This is an authoring size choice, not recovered Raven collision dimensions.

The initial numbered toe mapping was wrong. Owens controls 01/02 own rear
toes and 03/04 own front toes; Strider 02 is medial. Correcting those mappings
still produced excessive Raven sole penetration. The retained locomotion fit
therefore keeps Raven toe rest transforms under its animated feet. It does
not independently animate the toes or alter source MW3 animation decisions.

The existing rig's gait-dependent hip drop is set to 0.5 model units, leaving
standing height unchanged. Bounded trials at 0.1, 0.2, 0.3 and 0.5 reduced Owens
run reach clamps from the initial 15 to 11, 6, 5 and 0. This is a visual fit
parameter, not a gameplay movement change. Falls/get-up remain unresolved and
some such poses clamp more often with this locomotion fit.

| Stored-pose check, retained fit | Owens | Strider |
| --- | ---: | ---: |
| Clips evaluated | 14 | 14 |
| Total stored poses | 614 | 608 |
| Walk poses / reach clamps | 57 / 0 | 57 / 0 |
| Run poses / reach clamps | 49 / 0 | 49 / 17 |
| Trot poses / reach clamps | 48 / 0 | 48 / 4 |
| Stand, step, limp and backward-limp reach clamps | 0 | 0 |
| Maximum measured segment-length error, model units | 0.0000020 | 0.0000031 |
| Lowest walk sole relative to z=0, model units | -0.0004 | -0.0622 |
| Highest lower sole during walk relative to z=0, model units | 0.0654 | 0.0646 |

The remaining clips are fall backward/forward, land backward/forward, get up
backward/forward and collapse. Reach clamps remain in those clips: 272 total
for Owens and 291 for Strider, in addition to Strider's 21 locomotion clamps.
Clamps are explicit length-preserving limits, not passing fidelity checks.
All generated matrices were checked for finiteness by the unchanged solver.
Running/limping also retain sole intersections; no terrain/contact solution is
claimed. Sole heights use the numeric z=0 reference; the rendered review plane is at
z=-0.01. Walk ground clearance is measured, not treated as a blanket contact pass.

Both original walk clips contain 57 stored samples including the loop endpoint,
with a 1.866666675-second loop. Previews retain those sampled transforms and
source timing. Horizontal travel is removed only for the in-place review
camera. There is **no per-frame vertical correction or planar contact bake**.
The material pass retained identical solved-transform files before toe/hip
fit changes. Editable scenes, matched stills and walking GIFs remain local.

The solver source used by the fresh local C++ harness matches both maintained
copies (`tools/remaster-launcher/donor_retarget.hpp` and
`tools/m4-crt-heap-carry/host/donor_retarget.hpp`), SHA-256
`4431287ddf541d671578d0ec904f2933f16567b617d06695d280a7f837acb4d5`.
The runtime's active donor reader and geometry binding are in
`tools/m4-crt-heap-carry/host/donor_runtime.inc` and
`tools/m4-crt-heap-carry/host/mesh_override_stage.inc`; the older baseline
override-stage file is not the current complete model implementation.

## Gameplay and packaging boundary

Use the [additional-mech authoring workflow](authoring-additional-mechs.md) for
a separately selectable Raven. Owens provides matching 35-ton light Inner
Sphere metadata. Controller and metadata template are independent; they do not
make a copied stock definition a Raven. Both stock references are OmniMechs
with their own engines, armor, equipment and torso limits.

The RVN-3L source identifies standard structure, ferro-fibrous armor, XL 210,
single heat sinks, Beagle probe and Guardian ECM. Two concrete MW3 differences
prevent claiming a faithful playable RVN-3L from a direct data-only copy:

- The decoded stock equipment table has no Inner Sphere `ecm` entry
  (`sphere: NONE`), although a Clan entry exists. It must not be silently
  substituted or advertised as working Guardian ECM.
- Stock MW3 `TAG` is an airstrike designator, with five-ton/two-slot Inner
  Sphere metadata and a 60-second recharge. It is not MW5 TAG behavior.

MW3 definitions exist for medium laser, SRM6, NARC and Beagle probe. Armor
units, cooling, ammunition counts, mass/slot accounting and the intended
equipment semantics still need explicit mapping through original rules.
No incompatible loadout, fake equipment success or gameplay substitution was
installed by this prototype.

Prepared BWMESH4/BWTEX1 payloads, both exact controller LOD rosters, damage and
muzzle bindings, and an authored gameplay definition remain before packaging.
The active Owens close roster emits four toes per foot and no separate foot
mesh; its distant roster emits feet. Emission ownership therefore cannot be
copied directly from Raven bone names or the comparison's pose-control map.
The existing pack builder does not itself convert glTF files.

Next implementation work is contact/fall fitting, correct close/distant
emission and damage ownership, and an explicit choice between a faithful
RVN-3L equipment implementation and a clearly named MW3-compatible refit.
After those, validate Mech Lab/Instant Action, aiming/firing, collision, damage,
AI, save/reload and pack removal in a compatible native runtime.

## Private evidence

All original and derived media remain ignored under the isolated checkout's
`local/raven-investigation-20261030/`, `local/raven-prototype-20261030-r1/`
and `local/raven-textures-mw3-r1/` plus `local/raven-textures-mw3-r2/`.
The motion prototype directory retains:

- `extraction-files.json`, decoded metadata and source attachment selections.
- `compare_motion.py`, `compare_foot_follow.py`, `compare_locomotion_fit.py`,
  the fresh harness source/binary and preserved trial logs.
- `owens-r7-locomotion-fit/` and `strider-r7-locomotion-fit/`: pose inputs,
  solved outputs, per-clip/per-pose measurements and editable review scenes.
- Earlier failed assembly attempts and rejected numbered-toe fits, retained
  separately from the selected locomotion fit.

These are offline authoring receipts, not live game evidence. No new runtime
dependency, release artifact, installed pack or published content is created
by this documentation. Follow the [distribution policy](legal.md).
