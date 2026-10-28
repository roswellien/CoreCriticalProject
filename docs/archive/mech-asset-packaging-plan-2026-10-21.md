# Launcher-installable mech assets

Follow-up: the user authorized creating the two local packs. The resulting
prepared-runtime contract, actual sizes and integration instructions are in the
[launcher developer handoff](mech-pack-launcher-handoff-2026-10-21.md). That
implementation uses prepared binary resources to preserve selected profile
overrides and avoid end-user image conversion; the source-payload option below
remains the original investigation proposal.

2026-10-21. Packaging investigation and proposed implementation contract. No
asset archive was produced, installed, uploaded or cleared for redistribution.
The current policy in [legal.md](../legal.md) keeps proprietary and derived assets
local. Public delivery needs a separate rights decision; owning a game is not
recorded here as permission to redistribute its assets. A local import/build
workflow can use user-supplied inputs without publishing replacement content.

Use the existing ZIP-based `.mw3pack` container. Keep native mesh payloads,
material ordering, LOD bindings, skins and normal-map encoding intact. Packaging
must preserve the selected visuals without changing recompiled gameplay.

## What exists today

- [PackManifest.cs](../../tools/mw3-remaster-launcher/Core/PackManifest.cs) defines
  schema-1 `pack.json`, declared capabilities and dependency metadata.
- [mw3pack.py](../../tools/mw3-remaster-launcher/mw3pack.py) builds ZIP containers.
  Its validation checks basic metadata, not a complete runtime dependency set.
- [PackManager.cs](../../tools/mw3-remaster-launcher/Core/PackManager.cs) extracts
  archives into `mods/<id>`. The current import is incremental and has documented
  path-containment defects. It needs repair before handling external packages.
- [GameRunner.cs](../../tools/mw3-remaster-launcher/Core/GameRunner.cs) currently
  uses the enabled `com.mw3remaster.upgraded-mechs` ID as a model on/off switch.
  It does not compose models or textures from installed pack directories.
  Existing stock pack directories contain descriptors, not their asset payloads.
- [play_remaster.py](../../tools/remaster-launcher/play_remaster.py) selects the
  profile's `native.model_registry`; the current profile selects
  `local/material-authoring-r1/normal-registry.json`, not the older base registry.
  [native_assets.py](../../tools/remaster-launcher/native_assets.py) prepares
  BWTEX1 color and BWNRM2 normal resources from that registry.

Read-only inventory of the selected registry, deduplicated by resolved file path:

| Proposed collection | Models | Referenced files | Source size, uncompressed |
| --- | ---: | ---: | ---: |
| MW5 replacement mechs | 14 | 189 | 351.46 MiB |
| Updated MW3 mechs | 4 | 337 | 392.73 MiB |
| Total | 18 | 526 | 744.19 MiB |

MW5: Bushwacker, Mad Cat, Vulture, Thor, Orion, Daishi, Shadow Cat, Puma,
Annihilator, Cauldron-Born, Sunder, Supernova, Black Hawk and Champion.
MW3: Strider, Avatar, Owens and Firefly. These numbers include `required_files`,
mesh environment paths, batch metadata, color/normal sources, skins and texture
variants. All those file references existed when inspected. They are a sizing
snapshot, not immutable release pins or a complete gameplay validation.
Compression, byte-identical deduplication and prepared-cache size were not measured.
Most registry entries retain `runtime-candidate` status.

The 39 configured environment texture banks and world/surface normal catalogs
are a separate asset family; they are excluded from this mech estimate.

## Proposed packs and payload

Create two independently selectable collections, with each model's related
textures inside the same pack:

- `com.mw3remaster.mw5-mechs`: the 14 MW5 replacements.
- `com.mw3remaster.updated-mw3-mechs`: the four updated MW3 models.

Keep terrain/world textures in a separate HD environment pack. Do not require
that larger pack just to select mech replacements. Support per-chassis splitting
later if update/download sizes warrant it; the first implementation needs only
the two collections above.

Proposed source payload layout:

```text
pack.json
models/models.json
models/mechs/<chassis>/lod0.bin
models/mechs/<chassis>/lod1.bin
models/mechs/<chassis>/lod0.json
models/mechs/<chassis>/lod1.json
textures/mechs/<chassis>/...color and normal PNGs...
```

Names are illustrative; preserve every actual registered LOD, skin and material.
Normalize runtime-relevant paths to pack-relative paths. Do not copy development
trees wholesale: exclude Blender projects, donor archives, screenshots, videos,
reports, executables and generated game code. JSON batch metadata may contain
development provenance; export the runtime fields deliberately and keep private
source-to-package provenance outside the archive.

Extend the manifest with a versioned native payload contract: model registry
entry point, required chassis/skin support, mesh and normal format capabilities,
and an exhaustive relative file list with byte sizes and SHA-256 hashes.
Use a new schema version and explicitly reject it in older launchers. The
current schema-1 importer does not enforce this contract. Generic version strings
alone do not prove the selected host supports a particular mesh format.

Prefer source PNGs plus existing native meshes for the first local prototype.
Prepare color/normal sidecars into a versioned writable cache at install/first
use, reusing the current encoders. That path still needs Python/Pillow until a
packaged preparation runtime is supplied. A later prepared-resource profile can
remove end-user encoding; measure its compressed download and installed sizes
before choosing it. Do not ship both full source and generated caches by default.

## Required launcher work

1. Repair import containment and update behavior. Validate pack IDs and all ZIP
   paths before extraction, reject absolute/traversal/ADS/reserved names,
   case-colliding duplicate entries and links, and bound file counts and expanded
   sizes. Extract and verify into a fresh launcher-owned staging directory;
   preserve the working version until validation succeeds. Activate through a
   recoverable version switch. No package-provided scripts or arbitrary commands.
2. Resolve installed model registrations relative to their own pack root.
   Compose enabled packs into a private per-launch registry. Use the launcher's
   existing first-priority-wins convention by chassis ID, choosing the complete
   mesh/material/normal/skin record together; filename conflict display alone
   cannot decide a model conflict. Enforce dependencies and host capabilities.
3. Remove developer-profile mech path overrides from the composed launch profile.
   `play_native.ps1` applies `native.runtime_environment` after Python asset
   preparation and can overwrite newly prepared bindings. The current Orion and
   Annihilator fixes explicitly account for this; migrating only models.json
   would not preserve the assets actually loaded. Generate allowed native
   bindings from the selected records, with no stale paths for disabled models.
4. Separate bank preparation from mech preparation. The current preparer and
   launch planner unconditionally read the development configured-bank manifest.
   Disabled/missing optional HD banks must use the admitted user's original
   assets through the existing original-compatible path, while a selected
   incomplete pack must fail visibly. Implement and check that routing explicitly.
5. Install under a writable per-user content root, for example
   `%LOCALAPPDATA%/MW3Remaster/mods/<id>/<version>/`. Keep preparation caches and
   launch snapshots separate. Do not overwrite the original game installation.
   Make disable, update, rollback and uninstall operate on launcher-owned files.

The standalone application also currently discovers a repository-local native
profile/scripts. Asset packs solve content delivery, not the separate portable
host/toolchain installation prerequisite. Keep native executables and their
admission/profile identity outside content packs.

## First implementation and acceptance

First build an asset-free synthetic pack fixture and connect import -> installed
registry -> private launch bindings. Test rejected paths, corrupt/truncated files,
unsupported schema/formats, interrupted update, disable and rollback. Then use
the latest Orion and Annihilator as local relocation checks: they exercise
recent geometry/material changes and the profile-override defect.

For the local real-asset prototype, freeze selected inputs, preserve model
status/identity, build under ignored `local/`, and install into an isolated test
content root. Move that root to a path with spaces, outside the checkout. Verify
all declared payload hashes and successful preparation without access to former
C:/D: asset locations. Check the final child environment, not just --prepare-only,
because the PowerShell coordinator can replace bindings. Compare prepared mesh,
color and normal identities with the frozen local baseline at both LODs and for
alternate skins. Follow with bounded live appearance checks on a compatible host.

Only after those checks expand to all 18 models. Current host/model capability
and candidate labels remain authoritative; packaging does not close combat,
damage, muzzle, LOD or performance validation.

Boundary for this investigation: development asset references -> a concrete
portable-content contract and identified launcher integration defects. No native
execution boundary advanced. Strict acceptance remains 131/144. No commit,
game launch, active SQLite access or change to other asset/graphics work.
