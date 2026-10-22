# Mech pack handoff for the launcher developer

Follow-up: [launcher integration and test results](mech-pack-launcher-integration-2026-10-21.md)
records the implemented schema-2 consumption path, local installed-pack Training
check, exact host admission and remaining graphics/standalone-install blockers.

The two local `.mw3pack` files are under
`local/asset-packs/mechs-20261021-r1/`. See `packs.json` beside them for final
archive sizes, SHA-256 hashes, installed sizes and chassis lists. These are ZIP
archives with **schema 2 / prepared-native-v1**, a new contract requiring launcher
integration. Do not import them through the unchanged schema-1 installer.

| Pack ID | Contents |
| --- | --- |
| `com.mw3remaster.mw5-mechs` | 14 MW5 replacement chassis |
| `com.mw3remaster.updated-mw3-mechs` | Strider, Avatar, Owens, Firefly |

Built archives: MW5 **340.62 MiB**, updated MW3 **330.00 MiB** compressed.
Expanded contents occupy 1,493,336,507 and 922,009,765 bytes respectively.
The earlier investigation estimated source PNG/mesh size; these ready-to-load
packs instead contain expanded native color/normal resources, deduplicated by
content hash. Their installed sizes therefore differ from those estimates.

Every pack contains meshes, close/distance color textures, close/distance normal
maps and registered alternate-skin color resources. They use the existing native
binary encodings. Users need no image conversion or Python/Pillow to consume
these prepared mech resources. Terrain banks, world models, HUD/menu assets,
audio, executables and source artwork are not included.

## Exact file contract

`pack.json` is at the archive root. Its important fields are:

```text
schema_version = 2
id, name, version, author, category, description
provides.mechs = list of chassis IDs
provides.textures = true
provides.normal_maps = true
native_payload.profile = "prepared-native-v1"
native_payload.registry = "models/models.json"
native_payload.path_base = "pack-root"
native_payload.reference_host_sha256 = known source host identity
native_payload.required_formats = binary formats used by this pack
files[relative/path] = {sha256, bytes, format?}
```

`files` declares **every member except pack.json itself**, including the registry.
Verify the archive hash against trusted `packs.json` when available; an archive's
self-declared member hashes provide integrity, not publisher authentication.
`pack.json` intentionally cannot contain its own hash.

`models/models.json` has `schema_version: 2`,
`payload_profile: "prepared-native-v1"` and a `models` array. Each model contains:

```json
{
  "id": "orion",
  "name": "Orion",
  "backend": "native",
  "status": "runtime-candidate",
  "environment": {
    "MW34_ORION_MESH": "payload/<sha256>.bin",
    "MW34_ORION_LOD1_MESH": "payload/<sha256>.bin",
    "MW34_ORION_TEXTURES": "payload/<sha256>.bin",
    "MW34_ORION_LOD1_TEXTURES": "payload/<sha256>.bin",
    "MW34_ORION_NORMALS": "payload/<sha256>.bin",
    "MW34_ORION_LOD1_NORMALS": "payload/<sha256>.bin"
  },
  "required_formats": ["BWMESH2", "BWNRM2", "BWTEX1"],
  "skin_ids": []
}
```

The placeholders above illustrate the shape; use the real archive values. All
paths resolve **from the installed pack root**, including paths in the nested
registry. Payload names are content hashes. Multiple bindings may deliberately
share one file; do not infer chassis, role or LOD from a filename. Preserve the
environment key exactly, including `MW34_BUSHWACKER_TEST` and alternate-skin keys.
The model's environment object contains file bindings only, never shell commands.

## Implementation checklist

1. **Install safely.** Add explicit schema/profile dispatch; reject unsupported
   versions rather than accepting them as schema 1. Validate IDs, relative paths,
   unique Windows-normalized destinations, file sizes, expanded-byte budgets and
   member hashes. Reject traversal, absolute/drive/UNC/ADS paths, links, reserved
   names and undeclared members. Stage in a new owned directory, verify complete
   closure, then activate; retain the previous version if any step fails. Bound
   pack.json/registry sizes before parsing and extraction. Never execute content.
2. **Read enabled content.** Replace the hard-coded
   `com.mw3remaster.upgraded-mechs` on/off test in
   [GameRunner.cs](../tools/mw3-remaster-launcher/Core/GameRunner.cs). Read the
   schema-2 registry from each enabled pack. First enabled pack in priority order
   wins for a duplicate chassis; choose its whole record together. Support either
   collection alone, both, or neither. Retain the candidate label in the UI.
3. **Check the native host.** Require the compiled chassis IDs, alternate skin IDs,
   and each declared BWMESH/BWTEX/BWNRM format. These packs require mesh versions
   through BWMESH6 in the MW5 collection and BWNRM2 normal support. The reference
   host hash records the source configuration; it is not proof that an arbitrary
   newer host is compatible. Until a capability contract is available, explicitly
   admit matching host identities rather than assuming compatibility. Reject
   use with the D7VK/original-executable backend.
4. **Resolve and bind.** For each selected record, resolve environment values
   beneath its installed root and validate against the file table. Construct an
   allowlisted, private launch environment from these absolute resolved paths.
   Validate keys against the host's chassis/binding table; a generic `MW34_`
   prefix check is insufficient. Do not pass these schema-2 records into the
   schema-1 PNG preparer: they already contain native texture/normal binaries.
   Keep graphics settings (GPU models, normal-map enable, lighting strength)
   under launcher/renderer settings; pack metadata must not set global flags.
5. **Fix the final override point.**
   [play_native.ps1](../tools/remaster-launcher/play_native.ps1) currently writes
   `native.runtime_environment` into its process after Python preparation.
   Remove stale per-mech profile paths before applying selected pack bindings,
   or apply the selected bindings at that final point. Strip bindings for
   disabled collections as well. Preserve unrelated graphics/world settings.
   Merely setting a Python environment earlier will be overwritten.
6. **Separate unrelated assets.**
   [native_assets.py](../tools/remaster-launcher/native_assets.py) and
   [play_remaster.py](../tools/remaster-launcher/play_remaster.py) still require
   the development configured-bank manifest. Route prepared mech packs around
   model encoding, and handle original/HD banks independently. Disabling these
   two packs must select original geometry without requiring their payloads.
7. **Keep installation portable.** Use a writable owned content location, such as
   `%LOCALAPPDATA%/MW3Remaster/mods/<id>/<version>/`, without rewriting the user's
   original game. Maintain enabled IDs/order, update/rollback and uninstall.
   The existing native host still has repository/profile/toolchain prerequisites;
   these content packs do not supply a standalone engine installation.

## Validation to perform in the launcher

- Install both archives into an isolated root with spaces, then move the root.
  Check every payload through the relocated path and verify declared hashes.
- Test each collection alone, both enabled, both disabled, and duplicate-chassis
  precedence. Disabled models must leave no stale mesh/texture/normal bindings.
- Test corrupted members, unsupported schema/host/formats, path rejection and
  interrupted update while preserving the installed version.
- Inspect the final child environment after the PowerShell override point.
  It must contain installed-pack paths only for enabled model bindings.
- Use the latest Orion collar and Annihilator neck covers as visual spot checks;
  test close/distance LOD and Bushwacker skin D. Then expand to the other chassis.
  Container integrity does not establish gameplay, damage or performance fidelity.

## Build and evidence

The builder is
[build_mech_packs.py](../tools/remaster-launcher/build_mech_packs.py). It reads the
selected profile and normal registry, freezes inputs, takes explicit per-model
profile bindings in preference to preparer results, and packages native resources.
For bindings absent from the profile (Owens/Firefly textures and normals), it uses
the existing encoder with frozen registered inputs. No game/world banks enter
the packs. Identical payload bytes are deduplicated within each archive.

The final build marker is `packs.json` with `verified: true`; absence means the
build did not complete. Every member is read back and hashed, all registry file
references are checked, and selected original inputs/profile/registry are
rehashed before that marker is published. Private source paths/pins are recorded
beside the archives in `private-build-provenance.json`, not inside them. Keep
that file local. Compression and relocation do not alter payload bytes.

These are local content artifacts authorized by the user, with no public upload
or distribution clearance. Model candidate labels and strict acceptance remain
unchanged at 131/144. Boundary advanced: machine-specific selected mech assets
to portable prepared-content archives. Launcher consumption and live installed
pack testing belong to the integration work above. No commit or gameplay change.

Completed package checks: both archives were independently extracted outside the
checkout into a temporary path containing spaces, their install directories were
renamed, and all 18 model records resolved from the relocated roots. 223 file
identity/binding checks passed, including all explicit selected profile resources
and matching color/normal batch counts. Registry corruption was detected for
both packs. Full archive/member hash readback and source-pin rechecks also passed.
The handoff's five source links and builder syntax were checked. No native game
was launched; final launcher-child binding and live installed-pack checks remain.
