# Community content packs and runtime capabilities

Core Critical 1.0.26 and the accompanying MW3 content-capabilities runtime
update replace content-pack executable matching with resource-reader versions.
Community packs do not need a publisher certificate, private key or project
signature. Import them through Mods & Packs → Install Pack in the selected
game's library. Prepared native content currently supports MW3; the other
games' readers still need implementation.

The selected runtime's integrity-pinned profile advertises its implemented
contracts under `native.content_capabilities`:

```json
{
  "ui-artwork": [1],
  "prepared-mechs": [1],
  "environment-resources": [1],
  "cinematic-replacements": [1],
  "soundtrack": [1]
}
```

These are exact supported versions, not minimum versions. A runtime that drops
version 1 must not advertise it. A routine native rebuild that preserves its
readers keeps the same declarations. New runtimes must declare their actual
contracts in the authored source profile; pack metadata cannot grant them.
The normal native executable/module identity checks still run.

A pack's schema-2 native payload declares its resource profile and formats.
It may also request explicit capabilities, for example:

```json
{
  "profile": "prepared-ui-v1",
  "registry": "ui/ui.json",
  "path_base": "pack-root",
  "required_formats": ["MW3H-v1"],
  "required_capabilities": {"ui-artwork": 1}
}
```

This is the `native_payload` part of pack.json, not a complete pack. The full
manifest still needs a unique ID, schema version 2, `game_id: "mw3"`, and its
file table with sizes and SHA-256 hashes. Hashes detect corruption; they do
not authenticate the author. No signature or executable hash is required.

| Existing payload profile | Implied runtime capability |
| --- | --- |
| prepared-ui-v1 | ui-artwork version 1 |
| prepared-native-v1 | prepared-mechs version 1 |
| prepared-environment-v1 | environment-resources version 1 |
| prepared-cinematic-v1 | cinematic-replacements version 1 for in-game replacements |
| prepared-music-v1 | soundtrack version 1 when enabled |

Existing v1 packs imply these requirements and need no repackaging.
`reference_host_sha256` is optional provenance and is ignored for admission.
An explicit requirement adds to the profile's implied version; it cannot
remove that base requirement. Missing/unsupported versions and unknown
requirements produce an error naming the pack and capability. An explicit
empty runtime declaration means no capabilities; it never inherits history.

Model chassis/LOD/skin support and binary format versions remain checked.
Environment/lighting formats, file integrity, archive paths, size limits,
pack conflicts and game targeting also remain checked. Movie replacements
retain the original decoder, AVI contract and existing original movie targets;
this change creates no new story hooks. Standalone movie-library additions
continue to use launcher playback and need no in-game replacement capability.

## Measured donor hinges (unreleased)

`donor-rig-hinges` version 1 is an optional BWMESH4 visual retarget contract.
It is required when an additional-chassis or stock replacement mesh sets the measured-hinge flag
(bit 1 at byte 20). The builders add the requirement; Python and C# validators
reject omission as well as unsupported runtime versions. No released profile
or historical host entry gains this capability from this change. A matching
new development build must explicitly declare it in its integrity-pinned
profile. See [rigid binding authoring](authoring-additional-mechs.md#rigid-stl-bindings-with-measured-hinges-development-only).

## Runtime migration and release

Future installer builds include the complete release version in the executable
filename, for example `corecriticalinstaller-1.0.26-preview.exe`. The installer
receipt records `setup_filename`, and the launcher release builder uses the
same name. Cloud object names, website links and download publication must
preserve that exact versioned filename; an unversioned basename is forbidden. Existing
published links below describe the original 1.0.26 delivery and stay valid.

`legacy_content_capabilities.json` is a frozen migration map for the 30
already-reviewed native identities. Both C# and Python consume the same file.
The previous per-pack reference/successor tables are removed. Do not append
routine future builds: put their declarations into the authored runtime profile.
Unknown runtimes without a declaration cannot load prepared native content.

`stage_native_runtime.py` retains capability declarations and packages the
shared coordinator/helper. `refresh_content_runtime.py` makes a separate
verified runtime copy for this migration, retaining native binaries and
refreshing the coordinator and file pins. It leaves the original runtime intact.

Existing installations need the new launcher **and** the accompanying signed
`.mw3update`: an already-selected game update includes its own older coordinator.
The 1.0.26 full installer bundles the new coordinator for fresh installations,
but deliberately preserves a player's selected update. Launcher and game code
updates still require trusted signatures. Content capabilities do not replace
code-update verification or weaken executable/module pins.

The installer builder accepts `-UpdateTrust` for the public update-key
configuration and requires that configuration for precompiled releases. This
also closes a fresh-publication omission discovered while assembling 1.0.26;
existing installations' public trust files were preserved by 1.0.25 upgrades.

## Validation

The complete launcher fixture suite passes. Asset-free Python pack/capability,
authoring, soundtrack and startup-cache checks pass: 28 tests. These include
unsigned authored HUD/model/environment content without a reference hash,
an arbitrary runtime identity with matching capabilities, legacy migration,
missing/unknown/malformed versions, attempts by packs to authorize themselves,
format/chassis restrictions and integrity/path failures. The actual staged
runtime passes full launcher file/startup validation. Formal acceptance remains
131/144; these checks do not establish mission completion or fix the remote
c1m1 memory fault.

Private release evidence: `D:/MW3ContentCapabilities-20261023-r1`. Nothing is
committed. Both native binaries retain the October 23 performance release pins.

The exact signed precompiled update passes original-input verification,
installation of 651 runtime files, activation, complete validation and rollback
in an isolated installed baseline. A first attempt was correctly refused while
another worker's game was active; that process was left untouched. Once it
finished, the complete trial succeeded. The signed launcher publication also
activates the actual installed HUD/menu packs with an unrelated test executable
identity and an explicit UI capability. No game is executed by that check.

## Downloads

- [Signed Core Critical 1.0.26 installer](https://playtest.corecritical.dev/installers/2026-10-23-r2/corecriticalinstaller.exe)
- [Companion MW3 Content Compatibility Update](https://playtest.corecritical.dev/updates/mw3-content-capabilities-20261023-r1/MW3ContentCompatibilityUpdate.zip)

Both are listed in Setup. Existing installations install the launcher first,
then extract the update wrapper and import its `.mw3update` with the matching
payload ZIP beside it. A fresh full installation already bundles this runtime.
No automatic feed is configured and no content packs are rebuilt.

Full remote installer, wrapper, signed update metadata and payload readbacks
match local bytes. The remote installer retains a valid Windows signature.
Installer SHA-256 is
`07d5d24c1ca9089a4a2a76955a38db3505b0ad2802bfb7d7ca9eed852a7e788a`;
wrapper SHA-256 is
`50341761f882c5276e5e8667b91a06e0b21eb85b006dfad23bc32afdbc8dccb4`.
Update sequence is 2026102303, minimum launcher 1.0.26. No new full-installer
upgrade trial or remote mission retest is claimed.
