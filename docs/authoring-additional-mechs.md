# Additional mech pack authoring (experimental)

The launcher discovers enabled packs through their manifests, just as it does
additional skin packs. A compatible new mech is content data. It does not need
an entry added to launcher or engine source, a hard-coded numeric ID or another
native compile. The receiving runtime must already support
`additional-mech-chassis` version 1. Compatible packs are discovered from their
manifests without adding a per-mech entry to native or launcher code.

Version 2 adds optional pack-authored `base_skin_name`, `silhouette` and `sockets`.
These additions require launcher 1.0.42 and native runtime 1.0.41 or newer;
earlier runtimes support version 1 only. The builder automatically declares version 2
when a project uses any of these fields, so older runtimes reject it explicitly.

For example, a chassis project may add:

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

## Portable project

Keep this project and all its authored resources under one directory:

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

`definition.json` describes overrides of a definition in the player's original
MW3 media. An empty override object reuses that template's rules:

```json
{
  "schema_version": 1,
  "template": "orion",
  "fields": {}
}
```

Use existing typed definition field names. JSON objects represent named field
pairs, scalar values represent a single typed value, and arrays preserve ordered
lists. The coordinator preserves template floating-point fields; the original
game parser constructs and validates the resulting object. Unknown top-level
fields and changes to `version` or `skins` are rejected. Use additional skin
packs for named appearances.

The definition template must match the visual controller. Metadata can use
another stock template with matching mass, class and technology. Controller
reuse also reuses the original gameplay skeleton/collision and damage topology;
authors must check that their model fits it. Arbitrary new controllers and
independent metadata are not supported by this first contract.

## Prepared models and textures

Meshes use the existing `BWMESH4` donor-rig format and must satisfy the chosen
controller's original close/distance mesh rosters and transform contracts.
Textures use `BWTEX1`, with batch-to-material indices matching the exact mesh.
A GLB or PNG renamed to `.bin` is not a prepared payload. The Marauder's local
export project demonstrates the conversion; a general interactive model export
tool is not supplied by this pack builder.

Both LOD bindings are required. Pack paths are relative to the project, without
`..`, absolute paths, links or executable commands. The builder gives payloads
content-addressed names and creates the integrity table and registry:

```powershell
python tools/remaster-launcher/build_chassis_pack.py --project path/to/project.json --output path/to/new-output-directory
```

The output includes `<pack_id>-<version>.mw3pack`. A pack may contain up to 128
chassis. Each full ID is `<pack_id>:<chassis_id>`; keep that ID unchanged when
updating the same mech. Numeric runtime indices are assigned privately.

## Installing and adding skins

In a compatible Core Critical Launcher, choose **Mods & Packs → Install Pack**,
select the `.mw3pack`, enable it and launch MW3. It appears as an additional
chassis in the Mech Lab stockpile for unlimited-inventory Instant Action.
Installing a pack does not grant free campaign salvage.

For a separate skin pack, set its `chassis` to the full stable ID, such as
`community.example:example`. Supply the close/distance mesh SHA-256 identities
and matching textures through the existing skin-pack format. The coordinator
discovers the enabled mech and skin together, in either installation order,
and passes the additional name to the normal Mech Lab selector. Disabling its
required model produces a compatibility error.

Community content packs do not require a signing certificate. They contain
validated data; executable updates remain a separate update mechanism. Do not
include original MW3 media or generated game code in a project or pack.

Before release, check selection, both LODs, movement, aiming/muzzles, collision,
damage/limb loss, AI and saved configurations with the exact installed pack.
Those gameplay and save checks remain open for the Marauder candidate; a
successful import alone is not release qualification.
