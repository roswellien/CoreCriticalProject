# Launcher native runtime updates

**Current private playtest delivery, October 22:** performance/native updates
can use the existing `.mw3update` protocol with a precompiled runtime. See
[precompiled performance update delivery](precompiled-performance-updates-2026-10-22.md).
The source-generation route below remains available; code regeneration is not
required for the owner-authorized private precompiled delivery.

Launcher 1.0.13-preview adds a manual **Game Updates** window under **Settings &
Steam → Playtest Support**. It checks a configured HTTPS feed, imports a signed
`.mw3update` file, prepares an update, cancels preparation and selects a previous
installed runtime. Launcher self-replacement and automatic content-pack updates
are separate work; this change updates the native game runtime.

The boundary advanced is signed update acquisition → local preparation process
→ verified version publication → atomic runtime selection. It does not implement
the missing whole-game translation/build producer or change acceptance (131/144).
No production feed, signing identity or generated game binaries are included.
The shipped preview reports that updates are not configured until the project
provides the feed and trusted public key. It does not pretend to find a release.

## Storage and activation

Each application location has its own SHA256-derived identity under
`%LOCALAPPDATA%/MW3Remaster/runtime-updates/<identity>/`. This avoids changing the
ordinary development runtime when testing a separate application folder.

* `versions/<version>/` contains one complete generated runtime.
* `selection.json` names active/previous versions and the highest installed
  update sequence. Replacement is atomic, after a flushed temporary-file write.
* `.preparing-<guid>/` retains acquired tools and bounded preparation logs.
  Failed and cancelled attempts remain available for diagnosis. No automatic
  pruning is implemented yet.
* `.update-lock` serializes preparation and rollback across launcher instances.

The launcher verifies original inputs before invoking the preparer, checks the
download and every extracted file, and checks the complete generated runtime
before publishing it. All generated files must be registered in `runtime.json`;
the native executable must be pinned inside the version. Original input hashes
are checked again after preparation. A completion receipt permits retrying a
crash between directory publication and pointer selection. Failed selection
never falls back silently to a development checkout.

`NativeRuntimeLayout.FindInstalled` selects the active version before the
application's included `Runtime`. Existing installs with no selection retain
their previous behavior. Rollback validates the target and preserves the highest
sequence, so replaying an older remote release is rejected. The first update can
return to an included Runtime if one exists. A first-ever runtime with no included
Runtime has no previous playable version to return to. Rollback preserves settings,
packs and originals; pack host/version compatibility checks still apply at launch.
The game must be stopped when changing versions; retained directories also keep
an already resolved launch path stable. Runtime retention is not proof of game
compatibility or successful normal shutdown.

## Signed metadata and release setup

The release owner supplies `update-trust.json` beside the launcher executable:

```json
{
  "feed_url": "https://YOUR-RELEASE-HOST/stable.mw3update",
  "public_keys": { "release-key-id": "-----BEGIN PUBLIC KEY-----\n...\n-----END PUBLIC KEY-----" }
}
```

This is a schema illustration, not an active endpoint/key. An empty feed URL
allows offline signed imports. Trust is installed with the launcher, never
taken from the update server. Keys are RSA at least 3072 bits; signatures use
SHA256/RSA-PSS. Private keys stay outside publication inputs. HTTPS redirects
are rejected rather than following an unreviewed redirect chain. The update
signature authenticates exact decoded payload bytes, not reserialized JSON.

The `.mw3update` envelope has `key_id`, base64 `payload` and base64 `signature`.
The UTF-8 payload contains:

```json
{
  "schema_version": 1,
  "version": "1.0.0",
  "sequence": 1,
  "minimum_launcher_version": "1.0.13",
  "preparation_contract": "mw3-local-runtime-v1",
  "package_url": "https://YOUR-RELEASE-HOST/source-tools.zip",
  "package_bytes": 123,
  "package_sha256": "64 hexadecimal digits",
  "preparer": "prepare-runtime.exe",
  "files": { "prepare-runtime.exe": { "bytes": 123, "sha256": "64 hexadecimal digits" } },
  "original_inputs": { "MECH3.EXE": { "bytes": 123, "sha256": "64 hexadecimal digits" } }
}
```

Sizes and hashes above are placeholders, not accepted inputs. Include every
required tool/source file and original input. The original executable is mandatory.
The ZIP must contain exactly the registered files, with slash-separated relative
paths, no directory-only entries, links, duplicates or extras. Package/download
limits are 512 MiB compressed and 2 GiB expanded; generated runtimes are bounded
at 4 GiB. Unknown preparation contracts reject visibly.

`tools/mw3-remaster-launcher/sign_runtime_update.ps1` signs an existing manifest
using a release-owner private PEM key and writes a fresh output file. It creates
no production key and uploads nothing. Offline imports accept a sibling ZIP with
the same basename as the `.mw3update`; otherwise the signed package URL is used.
Release review must ensure packages contain only permitted project-authored
tools/source/metadata and licensed dependencies. A signature does not establish
distribution permission. Generated translations, original images and derived
game assets remain local under `docs/legal.md`.

## Preparation contract

The signed package contains a native executable that the launcher invokes
without a shell:

```text
prepare-runtime.exe --game <verified-original-folder> --output <fresh-runtime-folder>
                    --version <release-version> [--previous <previous-runtime-folder>]
```

The preparer owns source extraction/translation, compilation and reuse of
unchanged components. It must read originals and previous runtime without
modification, produce a complete existing-schema `runtime.json` layout, and
return zero only after successful completion. It must not copy private developer
reports/caches as a substitute for generation. Captured-state seeding,
production interpretation and original-code execution remain unauthorized.
The launcher supplies no shell commands or arbitrary extra arguments from the
feed. Signed tools are trusted executable code, not sandboxed third-party mods.
Cancellation stops the preparation process tree and retains the current selection.
Output streams drain continuously with bounded logs.

The actual whole-game preparer is still the next installer dependency. The
launcher plumbing is testable now without misrepresenting a fixture as a game.

## Verification

The complete launcher C# checks pass. New authored-only tests start a real child
preparation process and exercise successful activation/discovery, rollback to a
previous version and included baseline, interrupted activation retry, replay/
downgrade rejection, concurrent writer exclusion, mutated caller metadata,
untrusted keys, bad signatures, unsupported services, HTTP rejection, archive
tampering/traversal, corrupt originals, nonzero preparation exit, invalid output,
cancelled preparation and corrupt rollback targets. Their fake host files are
never executed as a game. Existing pack and original-setup checks remain separate.

Clean Windows, production HTTPS delivery, real native generation, update-specific
pack compatibility and game launch/normal quit after an actual release update
remain required before describing this as end-to-end playtester updates.

The release signing script was also executed with an ephemeral authored test key;
the launcher accepted its output. One initial test-only relative path was one
directory too high; correcting it made the actual signing test pass. No production
private key was created. Test keys and fixture outputs were removed with their
owned temporary test directories.

The current launcher deployment at `tools/remaster-launcher` was updated from
1.0.11 to 1.0.13 and reopened. The selected development native profile remained
byte-identical, as did the current settings during deployment. The actual GUI
shows the existing five packs active and prior 3440×1440/FXAA/16× settings.
The new update dialog was inspected and its missing-feed/key message verified.
The preview launched through the reports junction exposed a resolved G: window
identity; the returned identity was used to select it, and it was closed after
inspection. No game/native build, asset writer or controls process was stopped.

The rebuilt local installer is
`reports/runtime-updates-20261021-r2/installer/MW3Remaster-Launcher-Preview-Setup.exe`,
70,035,787 bytes, SHA256
`78ec3bfa74fb37ad077cb0bcaaf3e2b2a4c028ee63b5e2545a15ae06b94b1ae4`.
It remains launcher-only. Build identity, deployment evidence and the test output
are retained under `reports/runtime-updates-20261021-r1` / `r2`.
