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
