# Prepared mech packs: launcher integration

2026-10-21. Implements the consumption boundary from the
[pack handoff](mech-pack-launcher-handoff-2026-10-21.md). Existing WPF launcher,
native coordinator and native binary encodings are retained. No commit,
publication, asset upload or native-game acceptance change; strict count remains
131/144.

## Behavior

- The launcher imports root-manifest schema-1 containers and schema-2
  `prepared-native-v1` mech packs. Unknown versions/profiles fail explicitly.
  Schema-2 hashes are content integrity checks, not publisher authentication.
- PackStorage bounds JSON, file count and expanded bytes; rejects unsafe Windows
  paths, links, duplicate JSON properties, destination collisions, undeclared
  members, missing resources and bad hashes. It verifies a fresh staging tree
  before replacing an installation. Failed verification preserves the installed
  version. Previous versions support rollback and interrupted-activation recovery.
- UI content lives at `%LOCALAPPDATA%/MW3Remaster/mods/<id>/`, with retained
  `.rollback-<id>` directories. Installation runs off the UI thread. Import,
  enable/disable, priority, rollback and uninstall use the existing pack page.
  Archives left in `mods/` no longer auto-import at startup. Installed discovery
  errors are displayed. Development availability stubs are no longer created as
  though their payloads were installed; old application-directory packs are not
  silently migrated or deleted.
- Enabled schema-2 registries compose by whole chassis record, first enabled pack
  wins. The coordinator verifies installed file hashes, format headers, model/LOD
  binding keys, candidate settings, skins and the exact admitted host. The final
  private profile contains installed paths; PowerShell cannot restore the old
  development mech bindings. Disabling all collections clears all known model
  resource keys while retaining unrelated renderer settings.
- Prepared resources bypass source-image conversion. Python 3.11+ still runs the
  development coordinator, but this path no longer needs Pillow. The legacy
  source-image path loads Pillow only when actually encoding images. Missing
  optional bank configuration can use original archives in the prepared-pack
  path; a present configured replacement bank must still validate successfully.
- Prepared packs are rejected for D7VK. These changes implement mech resources,
  not generic mission/world/audio payload application. Prepared-pack dependency
  and conflict declarations are currently rejected explicitly; these two packs
  have none. Legacy nested-manifest containers must be repacked with `pack.json`
  at the archive root.

Main source: `Core/PackStorage.cs`, `Core/PackManager.cs`, `Core/PackManifest.cs`,
`Core/GameRunner.cs`, `MainWindow.xaml[.cs]` under `tools/mw3-remaster-launcher/`,
and `prepared_mech_packs.py`, `play_remaster.py`, `native_assets.py` under
`tools/remaster-launcher/`. D7VkRunner's existing Python probe now also supports
checking Python 3.11 without requiring Pillow.

## Exact host admission

The packs reference `a2e3f32d40904e7e2bf6e99f426cb758f47c3a14743dcdab3dd9895d607efb74`.
The independently rehashed current host is
`e3ea21dba813995bc6d47dd75f0bb5d572b4ff92c7908b8eaea57c0088e93ae7`.
This exact identity pair is admitted in the authored coordinator, alongside
checking the profile's chassis, mesh-version, normal-version and skin capability
lists. No newer-host wildcard exists. The ordinary launch planner separately
checks the executable hash and matching source snapshot.

Reviewed the current pinned host's 36 compiled chassis/LOD rows, Bushwacker skin D,
BWMESH1–6/BWTEX1 readers and material-name BWNRM2 routing. Rehashed the actual
host-source files against the snapshot:

| Source | SHA-256 |
| --- | --- |
| mesh_override_stage.inc | 422035cbf68dee94cc61796b631debc207a305151922880b9e1c4c9ecf226b0a |
| material_normals.hpp | 419385f6163870ab8ff0c7f32dbd32381e24ae92f64a7bb3addf86bda53bf36d |
| donor_runtime.inc | 8aa72151d32f909fdfb20ea83f98f4e54368448afd67822088d806d291804d5a |

This admission establishes resource interface compatibility, not general visual,
combat, damage, timing or performance fidelity.

## Checks and local evidence

- WPF build/publish and C# authored checks passed. Checks cover install, traversal,
  reserved names, alternate streams, links, duplicate paths, corruption, missing
  declarations, truncated archives, unsupported schemas, update preservation,
  disabled selections, rollback, uninstall and interrupted-update recovery.
- Eleven Python dispatch/composition tests and eight existing normal-material
  tests passed. Tests include relocated roots, first-chassis priority, disabled
  bindings, unsupported hosts/formats and the profile passed to PowerShell.
- A `python -S` check prepared the real 18-model candidate successfully without
  site packages/Pillow. A separate authored fixture used original archives with
  no development bank manifest and emitted a zero-replacement bank index.
- Both actual archives were installed using the C# installer outside the checkout
  at `%LOCALAPPDATA%/MW3Remaster Integration 20261021/`. Their `mods/` directory was
  moved to `relocated mods/`. Each collection alone, both and neither resolved
  respectively 14/4/18/0 chassis and 86/24/110/0 installed resource bindings.
- Native run `local/remaster/runs/20261021-115458-442/` used those installed paths
  and ordinary scripted UI input into Training. It loaded all 18 models at both
  LODs (36 enable events and 36 normal loads), queued Bushwacker replacement
  geometry during gameplay, and presented 340 Vulkan frames. The explicit frame
  budget terminates with exit 1 and an `unresolved_translation` budget diagnostic;
  this is not a normal-quit test. It is not a visual review of every chassis,
  damage/skins/LOD transitions or sustained play.

Private profiles/prepared outputs and a review launcher build are in ignored
`reports/mech-pack-integration-20261021/`. Original/derived content remains local.
The ordinary Release build also exists under
`tools/mw3-remaster-launcher/bin/Release/net8.0-windows/`.

## Existing graphics blockers and remaining work

The published development profile names the C3 effect catalog in its environment
but the C2 catalog in its integrity pin; the planner correctly rejects it. The
first isolated live attempt also stopped at `Duplicate authored surface normal
key` after loading the installed mech resources (run `20261021-115344-155`).
For the bounded successful Training check only, a separate candidate profile used
the existing hash-verified C2 effect catalog and removed `MW34_SURFACE_NORMALS`.
No published profile, graphics source or asset catalog was modified to hide these
failures. Resolve those graphics defects before testing the ordinary launch path.

The launcher still discovers the private checkout host/profile/scripts. Standalone
runtime preparation, distribution eligibility, ISO installation, save/settings
storage across application updates, missing dependency deployment and a clean
machine installer rehearsal remain separate work. No playable public installer
is claimed by this integration. The review build does not replace active launch
shortcuts or the existing launcher binary.

## Follow-up: ordinary launcher repaired and updated

After the user reproduced failed launches, all four recent GUI logs showed the
effect-catalog registration mismatch. The active shortcut still used the older
binary in `tools/remaster-launcher/`. Version 1.0.1-preview is now deployed there,
with hash-checked copies and backups under ignored
`local/work-ahead/launcher-startup-repair-20261021-r1/`. Existing shortcut targets,
resolution, input, audio and other saved settings are preserved. The old enabled
all-mechs selection was migrated to the two actual installed per-user packs.

The C3 effect catalog's SHA-256 matches the already published C3 audit receipt
(`e55d3776916963af541261e6e94aa0dfad92b04fe12c76627bd052d8119f8aba`, 1,067 records).
The profile now registers that exact selected resource. Diagnostics distinguish
a missing catalog from a selected/registered path mismatch, without bypassing
hash verification. The C3 publication script had updated the environment path
without updating the effect integrity record; future publications must keep both
fields synchronized.

`surface_catalog_composition.py` losslessly composes the existing authored images:
five identical duplicate bindings collapse and two explicit full-content keys
choose the selected C3 catalog over the earlier C1 images. The choices are
`(512,512,1,249754739172991640)` and `(512,512,1,1768456475036307863)` from C3
`normals-0.bin`. All 495 unique keys remain, including original flat exclusions.
Unknown image conflicts still fail; input order does not resolve them. Source
catalogs and renderer code are unchanged. The source hashes, output hashes and
pre-repair profile/settings are retained locally. Two authored regression tests
cover identical deduplication, conflicting-image rejection, explicit selection,
round-trip pixels and source conservation.

Run `local/remaster/runs/20261021-120816-148/` then reached live Training using the
corrected ordinary graphics configuration, C3 effect catalog, composed authored
normals and the two installed mech packs. It presented 340 Vulkan frames and
queued replacement geometry. The explicit test frame limit again ends with the
budget diagnostic/exit 1; ordinary interactive launches have no such frame limit.
No graphics feature was disabled for this follow-up test. C# launcher checks and
the new composition tests passed. Standalone distribution and broad gameplay
validation remain open; acceptance is still 131/144.

### GUI serialization follow-up

The user then reproduced a separate error before process launch: new JsonArray
pack-root nodes could not serialize with options lacking a TypeInfoResolver.
GameRunner now uses an explicit DefaultJsonTypeInfoResolver. The regression check
serializes and reads back an authored pack-root array, covering the previously
untested GUI write boundary. Version 1.0.2-preview is deployed to the existing
shortcut target. Actual GUI launch is confirmed by session
`local/remaster/launcher-runs/e68d6276155042cd9aafbb07295ed8b4/`, native run
`20261021-121220-321`, and the live native game window. Two installed mech packs
are expected; environment/world/audio content still uses the development profile
and is not yet a portable content-package delivery path.
