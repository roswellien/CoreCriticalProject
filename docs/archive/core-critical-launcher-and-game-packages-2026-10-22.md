# Core Critical launcher and game package identities

Core Critical is the shared launcher. Version 1.0.19 introduces a dedicated
launcher-update route, an explicit game catalog, and game-specific content
libraries. Only MW3 has an implemented play/runtime adapter. Registering future
titles does not grant gameplay or install support. Native acceptance stays 131/144.

## File types and stable identities

| Product ID | Product | Update metadata | Content archive |
| --- | --- | --- | --- |
| corecritical | Core Critical launcher | .ccupdate | No launcher-content contract yet |
| mw3 | MechWarrior 3 | .mw3update | .mw3pack |
| mw3pm | MechWarrior 3: Pirate's Moon | .mw3pmupdate | .mw3pmpack |
| mw4 | MechWarrior 4: Vengeance | .mw4update | .mw4pack |
| mw4bk | MechWarrior 4: Black Knight | .mw4bkupdate | .mw4bkpack |
| mw4mercs | MechWarrior 4: Mercenaries | .mw4mercsupdate | .mw4mercspack |

The MW4 suffixes are explicit catalog entries, not wildcard acceptance. Future
products need their own registered ID and adapter. Filename extensions never
authorize a payload by themselves. Renaming a Pirate's Moon pack to .mw3pack
does not permit it to install into MW3.

Pack manifests carry game_id. Existing manifests without that property are
MW3-only, preserving installed packs without migration. New MW3 pack builders
write it explicitly. Generic .zip imports remain for compatibility but still
check the manifest target. Prepared schema-2 payload readers are currently
MW3-specific; other games' prepared contracts fail visibly.

The MW3 mods directory and settings remain at their existing per-user locations.
Other games have separate games/<id>/mods directories. Matching pack IDs in two
games cannot replace each other. Discovery and rollback enforce the owning game
as well as import. No user media, saves or settings are moved.

Mods & Packs selects a game library and groups its installed packs by category.
Planned games show an explanatory empty state with installation disabled. This
selector changes the pack library only; the Dashboard still launches MW3.

## Launcher update protocol

A .ccupdate contains the same RSA-PSS/SHA256 signed envelope used for game
updates, with a separate strict launcher manifest:

- schema_version: 1
- product_id: corecritical
- update_type: launcher-inno-v1
- version: numeric target launcher version
- sequence: positive monotonically increasing launcher release sequence
- minimum_launcher_version: minimum version that can consume this contract
- package_bytes and package_sha256: exact companion ZIP identity
- installer: bytes and sha256 for its single CoreCriticalSetup.exe entry

Deliver matching basenames, for example corecritical-1.0.20.ccupdate and
corecritical-1.0.20.zip. Import through Settings & Steam, Core Critical Updates.
The ZIP contains only a launcher-only Inno setup; it does not carry original
inputs, packs, saves or the bundled first-install preparation archive.

The existing update-trust.json public keys authenticate the envelope. Launcher
and runtime sequences and state are stored separately. The launcher rejects
wrong products/contracts, unknown keys, modified signatures, invalid sizes,
already-installed/older versions, incompatible minimum versions and repeated
sequences. Windows Authenticode policy must also accept the exact installer.

Update and restart verifies and stages all bytes before application mutation,
copies the current application/framework files to an owned helper directory,
then starts that helper and shuts down. The helper has a separate startup path
with no main window. It waits for the exact parent process identity to exit,
checks that no other instance of the target launcher or game remains, rechecks
the signed metadata and installer, and holds the installer read-only while
running setup at the existing installation path. Silent setup does not execute
the first-install launch action or repeat optional Steam tasks. After success,
the installed launcher DLL version must match the signed target before recording
the sequence and restarting.

Before setup starts, any failure preserves the application. Failures during
setup are reported with an exit code and retained setup.log/result.txt. This
version does not promise transactional whole-application rollback if the
installer is interrupted midway: rerun the signed setup to repair. Runtime
rollback remains separate. Staging/results are retained rather than deleting
evidence after an interrupted upgrade.

## Release workflow

For native/performance updates, the owner's later October 22 direction requires
the [precompiled `.mw3update` route](precompiled-performance-updates-2026-10-22.md).
`build_precompiled_update.py` produces the existing signed metadata/ZIP protocol
with an already compiled Runtime and native copy tool. It supports installed
1.0.24 launchers without code generation or a replacement full installer. An
outer ordinary ZIP can deliver both matching files when unfamiliar metadata
extensions are inconvenient to download. Launcher-only releases remain separate.

Owner direction, October 22: every future launcher release delivers both
`corecriticalinstaller-<version>.exe` for fresh installs and a matching signed
`.ccupdate` plus ZIP for existing launchers. Use `build_launcher_release.ps1`
after publishing/staging the launcher without a Runtime subdirectory. Supply
Compiler, PublishDirectory, RuntimeDirectory, a fresh OutputDirectory, Version,
a new launcher Sequence, the existing update SigningKey/KeyId, and the three
Windows signing inputs (WindowsSignTool, SigningDlib, SigningMetadata).

The command builds a signed launcher-only setup and its update first, then the
full precompiled installer. It verifies the update key against the publication's
public trust before building, and writes `launcher-release.json` with artifact
sizes, hashes and exact download filenames. Deliver the versioned executable
from `Setup/` without renaming it, plus both files
from `LauncherUpdate/`. The update ZIP retains the `CoreCriticalSetup.exe`
internal entry for compatibility with existing installed launchers. Publication
and an actual isolated upgrade check remain separate release steps.

The individual build steps remain available:

1. Publish the launcher and stage its ordinary media helper dependencies.
2. Build a launcher-only setup using build_installer.ps1 without PreparationBundle or RuntimeDirectory,
   supplying Windows signing inputs. Keep the existing installer AppId and
   application directory to upgrade existing installations.
3. Run build_ccupdate.ps1 with that signed installer, its installer-build.json,
   target version, new launcher sequence, existing update SigningKey/KeyId, and a
   fresh OutputDirectory. It verifies the receipt, hash, version, Windows signature
   and timestamp, then produces the ZIP and signed .ccupdate. Private keys stay
   outside the output.
4. Test an actual upgrade of the previous installed version on an isolated
   Windows installation, including failure/retry and preserved user state, then
   deliver the matching metadata and ZIP together.

Existing launchers before 1.0.19 cannot consume .ccupdate. They need one normal
setup upgrade first. Subsequent launcher updates can use this route. Updates
currently use manual download/import; no automatic launcher feed is configured.

Game RuntimeUpdateManifest now has game_id with an MW3 default for old signed
metadata. A non-MW3 target is rejected until its adapter exists. Newly built MW3
source updates explicitly include game_id and require 1.0.19 because old strict
parsers do not recognize that new field. Previously signed MW3 updates retain
their existing compatibility. Combined launcher/game release orchestration is
not implemented; upgrade Core Critical first, then import the MW3 update.

The internal executable/assembly name and per-user MW3 storage name are retained
for shortcut, Steam and existing-install compatibility. The visible launcher and
setup product name are Core Critical. These changes do not rebuild native game
code, publish a signed release, upload files, commit, or push source.

## Validation and remaining integration

The launcher build and complete C# fixture suite pass, including game extension
mapping, separate stores with matching IDs, legacy MW3 packs and update metadata,
wrong-game import/discovery rejection, signed launcher targeting, signature/key,
downgrade/sequence/size rejection and preservation on unsigned installer rejection.
Real Windows trust and successful staging were exercised using an existing
Microsoft-signed tool as a fixture; that tool was never executed as setup.
Twenty-one focused pack/startup Python tests pass.

The pack selector, category groups, planned-library states and launcher update
screen were inspected in an isolated UI trial using authored metadata. Normal
player settings and the existing open launcher were left alone. Release closure
still requires a genuinely Windows-signed Core Critical setup, a complete real
upgrade/restart test and a clean-PC test. Verification/staging fixtures do not
establish those results.
