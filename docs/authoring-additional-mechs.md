# How to add a mech to MW3 with an asset pack

This is the maintained modder how-to for adding a selectable chassis through
Core Critical. Start with a portable project, build a data-only `.mw3pack`,
install it through the launcher and test it in Instant Action. A mech within
the runtime's supported content contract needs no per-mech source registration
or hard-coded numeric ID.

The [Atlas worked example](atlas-asset-pack-authoring.md) records the ongoing
Pirate's Moon port, its exact commands, demonstrated behavior and unfinished
engine support. This guide explains the reusable workflow; the worked example
records what Atlas has actually passed. Update both in the same PR when that
work changes a step, format requirement or compatibility claim.

## Rigid STL bindings with measured hinges (development only)

`tools/remaster-launcher/rigid_donor_payload.py` writes real BWMESH4 rigid
batches and BWTEX1 constant review materials from supplied triangle corners,
rest frames and original controller references. It does not split, synthesize
or deform geometry. Keep licensed source assets and derived model files local.
The constant materials are inspection colors, not a finished texture pipeline.

A controller can have different joint axes and footprints from the donor.
Setting `hinge_axes=True` opts the mesh into measured hinge retargeting:

- BWMESH4's existing flags field (little-endian uint32 at byte 20) uses bit 0
  for ground reference and bit 1 for measured hinges. Flags 0/1 retain the
  existing solver. Older hosts reject flags 2/3.
- Six unrendered metadata bones named `HingeAxis_Calf_Left/Right` and
  `HingeAxis_Forearm_Left/Right` and `HingeAxis_Foot0_Left/Right` describe
  the original model's axes. Their parents are the respective thigh/upper arm/calf,
  with empty control names.
  Each frame's Y column is the hinge axis; its Z column is a nonparallel
  motion guide. Frames use the donor's world rest space.
- Optional `HingeAxis_<toe bone name>` frames constrain toe rotation. Bind
  fixed knee/elbow housings to the upper segment; use distinct housing names,
  since the older `Knee_Left/Right` convention follows the calf.
- Each side needs 3�64 unrendered `Sole_Left_*` / `Sole_Right_*` points on
  existing foot/toe surfaces. Bind them to that side's controlled foot or toe.
  Include all vertices that can become lowest in the tested motion range;
  sparse points do not prove clearance for untested rotations or terrain.

The solver reads original control transforms, preserves rigid limb lengths
and measured knee/elbow/ankle axes, projects toe/elbow/ankle rotations onto those axes,
and compensates ankle height using the measured footprint. Positive controller
lift is smoothly limited to 8% of the donor's total leg length, retaining the
source timing and horizontal foot path while avoiding hip-high marching. The
controller's greater clearance is retained where long strides need it to keep
the rigid leg in reach.
It does not change simulation, collision, weapon origins or movement timing.
Unreachable goals remain explicitly logged as visual reach clamps. Foot contact
uses a bounded height bracket (up to 16 expansions) and up to 40 bisections.
Unresolved contact is rejected with a visible error instead of returning an
unreported ground penetration.

The additional-chassis and stock replacement builders detect the flag and require
`donor-rig-hinges` version 1. Python and C# admission reject a flagged mesh
whose manifest omits the requirement. This capability is **unreleased**;
only a matching development host/profile may advertise it. Existing runtime
profiles and the historical capability table are unchanged. Importing a pack
cannot add runtime support. Both LODs should use the same rig/rest/reference
metadata; a distance dispatch owner may be an ancestor such as the toe's foot.

## 1. Choose the supported authoring route

| Your goal | Project resources | Required `additional-mech-chassis` capability |
| --- | --- | --- |
| Add a mech using an existing MW3 gameplay controller | Prepared `BWMESH4` geometry, `BWTEX1` textures and JSON definition overrides | Version 1 |
| Add icons, a base-skin label or weapon socket adjustments to that mech | The same resources, with optional fields below | Version 2 |
| Preserve an MW3/PM donor's own hierarchy and motion tracks | Converted original-format resources and a `legacy` descriptor | Proposed version 3; **unreleased**, used by the Atlas prototype |

Version 2 support was introduced with launcher 1.0.42 and native runtime
1.0.41. Check the selected runtime's declared capabilities, not just the
launcher version: supported versions are explicit entries in its profile.
The builder declares the version the pack needs; the launcher/coordinator
rejects incompatible runtimes. See [capability rules](content-pack-capabilities.md).

Atlas's version 3 is deliberately unadvertised in released runtimes. Importing
its pack does not make it playable on those runtimes. Do not edit a runtime
profile or lower a pack's requirement to bypass this check.

The controller route inherits the stock skeleton, collision and damage
topology. Use it only when that behavior is intended. For a faithful PM port,
retain the donor's data and identify missing engine functions/resources as
compatibility work; an ignored definition field is not implemented behavior.

## 2. Prepare the workspace and inputs

You need Python 3.11+, this source checkout, a working native MW3 installation
from your own game files, and a launcher/runtime supporting the chosen route.
The prepared-model route also requires already exported compatible model and
texture payloads. **The pack builder is not a general GLB/FBX/PNG converter.**
The Atlas route uses the separately installed Mech3AX version recorded in
[dependencies](dependencies.md), only on the author's machine.

Keep the original game directories read-only. From the repository root, create
a project under ignored `local/`, or use a separate writable directory:

```text
local/my-mech/
  project.json
  definition.json
  close.bin
  distance.bin
  close-textures.bin
  distance-textures.bin
  README.md                 # Author notes; not packed automatically
```

Choose a pack ID such as `community.example` and a chassis ID such as `example`.
Together they form the permanent identity `community.example:example`. Use
lowercase letters, digits, dots, underscores or hyphens, beginning with a
letter or digit. Keep both IDs unchanged when updating the same mech; bump
the version instead. Numeric session indices and generated resource aliases
are managed by the coordinator.

## 3. Describe the mech

For the prepared-controller route, save this as `local/my-mech/project.json`.
It is a configuration example: supply real compatible payloads for the named
files before building.

```json
{
  "pack_id": "community.example",
  "name": "Example Mech",
  "version": "0.1.0-preview",
  "author": "Your name",
  "chassis": [{
    "id": "example",
    "name": "Example Mech",
    "metadata_template": "orion",
    "controller": "orion",
    "definition": "definition.json",
    "meshes": { "close": "close.bin", "distance": "distance.bin" },
    "textures": { "close": "close-textures.bin", "distance": "distance-textures.bin" }
  }]
}
```

`controller` selects the stock gameplay/animation structure; `metadata_template`
supplies mass, weight class and technology through the original game's metadata
getters. The latter may use another stock chassis only when those values match
your resulting definition. Arbitrary independent metadata is not supported by
this contract.

Save this minimal `definition.json` to start with the controller's rules:

```json
{
  "schema_version": 1,
  "template": "orion",
  "fields": {}
}
```

The definition's `template` must match `controller`. In `fields`, use existing
typed definition names: JSON objects represent named field pairs, scalar values
represent a single typed value, and arrays preserve ordered lists. The
coordinator preserves template floating-point fields; the original game parser
constructs the resulting object. Unknown top-level fields and changes to
`version` or `skins` are rejected. A mass/class/technology change must still
match the metadata template. Use separate skin packs for named appearances.

### Optional version-2 presentation fields

Add these fields inside the chassis object when you have matching resources.
The socket position below is illustrative; measure it for your model.

```json
"base_skin_name": "Olive Drab",
"silhouette": "example-icon.bin",
"sockets": [
  {"node": "firepoint01", "bone": "Forearm_Right", "position": [4.0, -0.01, -1.13]}
]
```

The base label renames the original first skin choice without changing its
saved index. Added skin packs continue to supply additional named choices.
The silhouette is a `MW3ICON1` mask: eight ASCII magic bytes, little-endian
uint32 width 41 and height 50, then 2,050 intensity bytes. Zero is transparent.
The launcher composes green, grey, red and yellow original-compatible teammate
icons using the chassis resource identity. No source registration is needed.
`render_chassis_icon.py` can produce a front mask from a BWMESH4 rest pose;
Pillow is needed only on the author's machine, not in the receiving runtime.

Socket positions use the named donor bone's local coordinates, before the
bone's prepared rest scale. Supply 1–64 unique `firepointNN` bindings and
check that the bones exist in the close model. The runtime evaluates the same
animated donor pose used for rendering and adjusts successful original weapon
origins by the socket displacement. Original firing direction and spread remain
unchanged. Socket data does not replace the original weapon definition, damage,
collision, ammunition or firing logic.

### Atlas route: retain the donor's own resources

Follow the [Atlas extraction/build commands](atlas-asset-pack-authoring.md#build-from-the-users-original-installation).
`prepare_legacy_chassis.py` generates the portable project and resource
descriptor from the local donor installation. Then use the same pack builder
in step 5. It does not require the prepared-controller `definition.json` above.
Keep legacy and prepared-visual chassis in separate packs.

The generated project includes the primary configuration and skin, both model
LODs, cockpit, motions and silhouette. It is not a promise that every MW3/PM
chassis is supported. Atlas still needs PM headlight and compiled effect/
footprint work before this route can become an advertised runtime capability.

## 4. Check the asset bindings

For the prepared-controller route, meshes use the existing `BWMESH4` donor-rig
format and must satisfy the chosen controller's original close/distance mesh
rosters and transform contracts.
Textures use `BWTEX1`, with batch-to-material indices matching the exact mesh.
A GLB or PNG renamed to `.bin` is not a prepared payload. The Marauder's local
export project demonstrates the conversion; a general interactive model export
tool is not supplied by this pack builder.

For prepared visuals, both LOD bindings are required. Pack paths are relative
to the project, without `..`, absolute paths, links or executable commands. The builder gives payloads
content-addressed names and creates the integrity table and registry. Check
scale, facing direction, moving parts, UV/material assignments and the chosen
controller's attachment/damage layout before exporting. A visually similar
rest pose alone does not establish compatible movement or collision.

For legacy projects, preserve the converter's hierarchy and motion track
names. MW3 derives some fall/get-up clip names dynamically. Keep resource names
unique across texture, motion and animation tables; the composer supplies the
final namespace and material relocation.

## 5. Build the pack

Run from the repository root, using a fresh output directory:

```powershell
python tools/remaster-launcher/build_chassis_pack.py `
  --project local/my-mech/project.json `
  --output local/my-mech-build-001
```

Expect `local/my-mech-build-001/community.example-0.1.0-preview.mw3pack` and
a `pack/` directory containing `pack.json`, `chassis/chassis.json` and hashed
payloads. The builder validates the contract and creates the file integrity
table automatically. Do not hand-edit the built payload or manifest; edit the
source project and rebuild into another fresh directory.

A pack may contain up to 128 chassis. Community content packs need no signing
certificate and contain data only. They cannot install executable functions;
new engine behavior requires a separately implemented and validated runtime
capability. Building successfully proves packaging, not gameplay fidelity.

## 6. Install and select the new mech

1. Select MW3 in a compatible Core Critical Launcher.
2. Open **Mods & Packs → Install Pack** and select the built `.mw3pack`.
3. Enable the pack and launch the native game. If a capability check fails,
   resolve it before attempting gameplay; Atlas version 3 remains unreleased.
4. Start unlimited-inventory **Instant Action**, open **Mech Lab**, and find
   the added chassis in the stockpile list. Scroll past stock entries if needed.
5. Select it, inspect its loadout and preview, then accept it and enter a mission.

Installing a chassis does not grant campaign salvage. Keep a stock-only test
profile and a separate pack-testing profile/library so comparisons are repeatable.
Save a copy of configurations you care about before testing pack updates or
removal. Do not overwrite original game archives to install a pack.

### Add separate skins to prepared visuals

For a separate skin pack, set its `chassis` to the full stable ID, such as
`community.example:example`. Supply the close/distance mesh SHA-256 identities
and matching textures through the existing skin-pack format. The coordinator
discovers the enabled mech and skin together, in either installation order,
and passes the additional name to the normal Mech Lab selector. Disabling its
required model produces a compatibility error.

This separate-skin route is not yet supported for Atlas's legacy-resource
prototype. See the worked example's current limits before adding appearances.

### Include original skins in an owned legacy chassis pack

For a converted MW3/PM chassis, use `prepare_legacy_chassis.py --skins all`
to retain the supported original skin block and its textures in the same pack.
The default `--skins primary` preserves the previous single-skin workflow.
This route uses the original Mech Lab skin rows, not prepared-visual skin
overrides or additional chassis entries. Keep the primary configuration and
existing chassis identity when updating a project.

The legacy descriptor uses `schema_version: 2` and adds ordered metadata:

```json
"skins": [
  {"id": "primary", "message": "MSG_SKIN_PRIMARY", "suffix": ""},
  {"id": "variantb", "message": "MSG_SKIN_VARIANTB", "suffix": "_b"}
]
```

The supported grammar has one primary and up to seven consecutive alternatives
(`MSG_SKIN_VARIANTB` through `H`), followed by optional damage bindings. These
are existing game message keys. IDs must be unique lowercase resource IDs;
keep them and row order stable across updates. Each alternate supplies one
unique suffix beginning with `_`, followed by 1–8 lowercase letters or digits.
Metadata must agree with the embedded definition. Unknown donor grammars fail
instead of silently losing skins.

Primary entries are texture names or two-name aliases. Supply both alias names
with every suffix, as well as all material and damage textures. The composer
preserves these implicit relationships when it namespaces resources. Shared
textures outside the skin block, such as cockpit glass, are not automatically
suffixed. The existing limits remain: 512 textures, 31-byte texture names and
16 MiB per raw resource. Ambiguous families, missing resources, invalid paths
and collisions fail before launch. Schema-1 packs cannot carry alternate skin
declarations; rebuild them with schema 2.

The builder adds `legacy-mech-skins: 1` alongside the chassis capability.
Use a runtime containing the matching reviewed coordinator. Editing an older
profile's capability strings is not an upgrade. Launcher import checks metadata,
pins and file closure; the coordinator additionally checks binary resources and
embedded skin lookups before composing private banks. Original archives remain
read-only. Keep other required capabilities, including headlights, intact.

Skin choice and original/upgraded appearance mode are independent. This contract
provides original paints; upgraded colors and normals require the separate
appearance contract and validation. Back up the previous pack, settings and
saved selections before testing updates. Retain a separate test library until
all declared skins, aliases, damage, LODs and save/reload behavior are checked.

## 7. Test the exact installed pack

Record the pack version/hash, launcher/runtime versions, settings and result
for each check. Mark untested behavior **Not tested**, not passed. For faithful
ports, compare with the donor game under equivalent conditions.

| Check | What to verify |
| --- | --- |
| Import and identity | Clean import, correct additional name/tonnage, existing stock chassis still separate |
| Lab and appearance | Model, materials, silhouette, loadouts and supported skin choices |
| Models and motion | Close/distance transitions, standing, walk/run, turning, falls/get-up, torso/arm limits |
| Combat and collision | Weapon origins/directions, recoil, ammunition, heat, equipment, terrain and actor collisions |
| Damage and effects | Armor display, limb loss, damaged materials, death/ejection, footprints and required lights/effects |
| Cockpit and AI | First/third-person views, camera alignment, AI-controlled copy of the mech |
| Persistence | Save/reload, same IDs after pack order changes, useful missing-content error, re-enable and reload |
| Regression | Disable the pack, verify stock-only behavior; normal quit and repeated mission loads |

Atlas has demonstrated native Lab selection and a bounded live mission render.
That does not close all checks above. Keep the detailed evidence and open items
in the [Atlas record](atlas-asset-pack-authoring.md#demonstrated-native-boundary).

## 8. Update the pack and write its README

Edit source assets/definitions, retain IDs, bump `version`, build into a new
output directory, and install that archive through the launcher. Repeat affected
checks using that installed version. Keep the previous pack and test evidence
available for rollback. Do not promise old-save compatibility without testing it.

Keep a `README.md` beside the source project. For an eligible distribution,
deliver its instructions alongside the `.mw3pack`; the current builder only
packages declared resources and does not automatically include this README.
Use this starting template:

```text
# <Mech name> asset pack
Pack ID / chassis ID: <permanent IDs>
Version: <pack version>; status: prototype / tested candidate
Target: MW3 native; required additional-mech-chassis version: <1, 2 or proposed 3>
Tested launcher/runtime: <versions and build identities>

Included: <models/LODs, loadouts, skins, icons and effects>
Behavior basis: <stock controller or preserved donor resources>
Requirements: <compatible runtime and any author-side conversion tools>
Install: Mods & Packs -> Install Pack -> enable -> Instant Action -> Mech Lab
Build: <exact project and build commands; tool versions>
Checks: <test, result, date and evidence; distinguish Not tested>
Known limitations: <specific missing behavior/resources>
Updates/removal: <stable IDs, tested save behavior and rollback instructions>
Credits/provenance: <authors, asset origins, licenses and local source hashes>
Distribution status: <what is permitted to share; local-only inputs excluded>
```

Keep original media, generated game code and local donor-derived experiments
out of Git and public pack delivery. A conversion does not change distribution
eligibility; follow the project's [distribution policy](legal.md).

## Troubleshooting

| Symptom | Next action |
| --- | --- |
| Output directory already exists | Pick a fresh build directory; retain the previous result for comparison |
| Runtime update/capability error | Check the pack requirement against the selected runtime; do not lower the requirement or forge a profile declaration |
| Wrong format, missing file or integrity error | Check relative source paths and actual exported formats; rebuild instead of editing hashed payloads |
| Metadata mismatch | Match definition mass/class/technology to a supported metadata template; changing the label does not fix the data |
| Model looks right but moves or takes damage incorrectly | Check controller topology, attachment/damage bindings, or missing donor runtime behavior |
| Chassis missing from the list | Check selected game, enabled pack, compatibility errors and unlimited-inventory Instant Action stockpile; scroll through the list |
| Saved mech fails after disabling its pack | Re-enable the required pack with the same stable IDs; capture an error if recovery still fails |
| PM field/resource appears to have no effect | Verify the runtime implements its consumer and dependencies; track it as an unsupported behavior until demonstrated |

## Optional headlights (development runtime)

This adapter is a development feature, not general PM compatibility. Use a
runtime that explicitly advertises `mech-headlights: [1]`; never add that claim
to an older binary. Nonempty lists also require additional-mech-chassis version
2 for prepared visuals or version 3 for legacy resources. The builder declares
these requirements automatically. Published runtime profiles remain unchanged.

Add `headlights` alongside `sockets` in each project chassis. Omit it or use `[]`
for an unequipped mech. This authored two-lamp example demonstrates independent
offsets; it does not claim that the PM Atlas has two lamps:

```json
"headlights": [
  {"id":"left", "space":"guest_node", "attachment":"torso",
   "position":[-1,2,-2], "direction":[0,0,-1], "color":[1,0.95,0.85],
   "intensity":2, "range":80, "inner_angle":15, "outer_angle":30},
  {"id":"right", "space":"guest_node", "attachment":"torso",
   "position":[1,2,-2], "direction":[0,0,-1], "color":[1,0.95,0.85],
   "intensity":2, "range":80, "inner_angle":15, "outer_angle":30}
]
```

Up to eight lamps may share or use different attachments. Each has a unique
1–31 character lowercase ASCII ID (letters, digits, underscore or hyphen).
Attachment names use 1–31 ASCII letters, digits, periods, underscores or hyphens.
Unknown fields, duplicate IDs, nonfinite numbers and Boolean numbers are rejected.
Position components are within ±100 game units. Direction must be nonzero and
is normalized. RGB is 0–1, intensity 0–8, range 1–256 game units, and cone
half-angles satisfy `0 <= inner_angle < outer_angle <= 89` degrees after conversion
to runtime float precision.

`guest_node` resolves a live node under the actor's current root. `donor_bone`
requires prepared visuals and names a donor skeleton bone, using the same axis
conversion and root-world basis as firepoints. Direction receives rotation/scale
and normalization, never translation. Missing required mounts fail visibly;
reconstructed visual bones alone cannot keep a removed component's lamp alive.

Build, import and enable the pack normally. Enable Dynamic Lighting and Headlights
in Display, then assign a key or enabled-controller button in Controls → Headlight
controls. Both bindings start unassigned; avoid conflicts with existing actions.
One press toggles all player lamps; another reverses a fade immediately. The
roughly 0.8-second fade uses simulation time, so pause/photo mode holds it.
Disabling Dynamic Lighting keeps the saved Headlights preference. Headlights off
suppresses the feature on the next launch; bindings and original controls remain.

New actors start off. Shutdown suppresses on requests; destruction discards lamp
state. Original campaign saves are unchanged. Host replay v4 carries lamp state;
v3 remains readable with lamps off. Stock MW3 missions have no imported PM AI
headlight policy and leave AI lamps off. Each lamp consumes one shared light slot
and respects weapon reservation. Scenery fixtures can be off independently.
This adds cone illumination, not PM's lamp facade or volumetric beams.

The coordinator emits MWCHAS5 only for nonempty lists and retains MWCHAS1–4
compatibility. Presentation-policy v2 must ship with its matching host; copying
the coordinator alone does not upgrade an older runtime.
