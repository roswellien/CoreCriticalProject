# Playtest updates and save backups

## Updating without reinstalling original files and packs

Native/runtime updates use a signed `.mw3update` metadata file and its companion
ZIP. Download both into the same folder with matching basenames, such as
`playtest-20261022-r3.mw3update` and `playtest-20261022-r3.zip`. In the launcher,
open Settings & Steam -> Game Updates -> Import signed update, select the
metadata, then Prepare and install. Close the game first. Original input hashes
are checked; existing generated code is reused only when it exactly matches the
new version. Native host/tool changes do not automatically require regeneration
of unchanged guest code. Settings and packs remain in user storage. Use previous
version provides rollback without reinstalling original files.

Content updates remain `.mw3pack` imports under Mods & Packs. Windows publisher
signing and the runtime-update envelope signature serve different purposes;
both are needed. Keep the update envelope's private key outside source packages.

For maintainers, `tools/native-preparation/build_source_update.py` packages a
staged source kit and invokes `tools/mw3-remaster-launcher/sign_runtime_update.ps1`.
Give each release a unique version and strictly increasing sequence, retaining
the trusted public key installed by setup. The current builder requires launcher
1.0.17 or later for this rebuilt host's reviewed compatibility admissions.
Rename the staged initial.mw3update/initial.zip together for manual delivery.
Do not modify ZIP bytes after signing its metadata. Verify signature, archive
hash, real preparation and activation before delivery.

The private download site requires browser Access authentication. No public
automatic update feed is configured; manual download/import is the supported
route. This engine updates the runtime/coordinator, not a running launcher EXE.
Changes to the launcher UI itself currently use a launcher setup upgrade, which
retains existing original files, packs and settings; it is not a complete game
reinstallation. Do not claim frontend self-update is implemented.

## Save backups

Launcher 1.0.17 adds Settings & Steam -> Save Backups. Back Up Now creates a local
`.mw3save.zip` under `%LOCALAPPDATA%/MW3Remaster/save-backups`. It includes player
`.mw3` files below pilots/ (including campaign games/) and configs/, plus the
native registry/settings file used by this installation when present.

Restore Selected or Load Backup File restores matching files, preserving other
saves. Current player files receive an automatic safety backup first, allowing
undo by restoring that backup. Start the game and choose Load Game afterward;
this feature does not inject a mission into a running native session.

The game must be closed. Archives are fully validated before player files change:
bounded entries and bytes, hashes, duplicates, allowed paths/extensions, link
checks and complete manifests. Writes use temporary files/atomic replacement and
roll back applied files on an error. Backup operations have a writer lock. Saves
stay local and are not part of support exports, installers, updates or R2 uploads.

## Current build evidence and continuation

User authorized native rebuild, new setup signing/upload, and removal of the old
R2 setup. Gameplay acceptance remains **131/144**. This handoff predates the subsequent source commit and website summary.

`local/remaster/gpu-native-playtest-20261022-r1` freshly compiles the selected
lower-horizon host sources. All seven authored objects were rebuilt. Relative to
the earlier installer host, only composition.cpp, sky_backdrop.hpp,
sun_tl_capture_stage.inc and vk_scene.hpp differ. Pack/resource reader sources
remain unchanged. The selected normal developer profile was not edited.

Private evidence root: `D:/MW3NativePlaytest-20261022-r2`:

- `SplitHost-r1` is a preserved failed helper attempt: it was pointed at player
  tools, which intentionally do not include developer-only llvm-lib.exe.
- `SplitHost-r2` succeeds using the full developer LLVM: 7 authored + 37,348
  generated objects. Unsigned host SHA256
  `c922df9f8663315972d14376ab5ac622cf82316d8ecf78a9c5eda7ecdca9ae95`.
- `SdkFree-r2` links the translated DLL without SDK/CRT import libraries.
  SHA256 remains `a71796e1d679322e2adf2c1e36309fd22ed9b418e3992fa9971b071c392a2654`.
- `Source-unsigned-r2` and `App-unsigned-r2/Runtime` prepare the new runtime using
  verified previous generated code; no original images or game DLL are packaged
  in the source kit. New host identity has exact reviewed pack admissions.
- `LaunchUserData` / launch-trial.log: actual isolated rebuilt host/DLL starts,
  plays intro, reaches original live menu and closes normally, exit 0. No Training
  or mission credit. Player's normal session was not launched or closed.
- `Setup-unsigned-r1`: new 1.0.17 EXE builds successfully, 267,725,888 bytes,
  SHA256 `944d4e330760cb7fedf4784c84af4e7543b08fe97390fd597ed8edfbeec6ce1b`.
  It is NOT Windows signed and was NOT uploaded. Its source envelope is signed
  using the existing private playtest update key, separately from Windows signing.
- `Setup-unsigned-r2` includes the final save-session guard and fresh-install
  restore correction: 267,724,781 bytes, SHA256
  `9913fb84a8db066b063c2380aa0c4fb77b58fb44d137874af189c91e2da84e3a`.
  It remains private and unsigned, pending the final authenticated signing build.
- Full C# fixture suite passes, including new save restore, safety-backup undo,
  corruption/traversal/executable/duplicate rejection, preservation and locking.
  35 focused launcher Python tests pass; 5 preparation and 4 signature framing
  tests pass. The save-backup UI was opened and inspected, then closed without
  backing up/restoring actual user saves. Settings hash was unchanged.
- `launcher-deployment.json`: local ordinary launcher updated to 1.0.17 with a
  retained old EXE. Current open window was not forcibly closed. Native profile
  and player settings preserved. This developer EXE is still unsigned.

`module_signature.py` exports only the public certificate table and the two
Authenticode-excluded header fields, refusing any changes to executable bytes.
After exact local generation, it attaches that pinned signature and requires
the complete signed output SHA256. No signing credentials or translated machine
code travel in that attachment. Four authored framing tests pass. An independent
local test strips/restores the signature framing of an already Microsoft-signed
tool DLL, reconstructs it byte-for-byte, and Windows reports Valid with timestamp.
This proves attachment interoperability, not that our game DLL is signed yet.
Signature-only changes also normalize back to a pinned unsigned module before
reuse, so certificate/timestamp changes alone do not force recompilation. A
changed-code fixture rejects reuse. Interrupted attachment scratch remains inside
the owned generation workspace and can be retried without publishing partial output.

`sign_windows.ps1` signs explicitly selected staged files and checks trusted,
timestamped signatures. `build_installer.ps1` optionally signs published PE files
and configures Inno to sign the uninstaller and outer setup EXE. The signing
branch still requires actual authenticated integration testing. Signed compiler
tool files require refreshing their tools.json pins before source-kit staging.

Azure signing profile: CoreCritical, East US, corecritical-playtest. Public
metadata: `D:/MW3SigningTools-20261022-r1/corecritical-playtest.json`.
Official signing client 1.0.146 and portable Azure CLI 2.91.0 are staged there.
The device-code login failed with a network timeout. A normal browser login is
waiting for the user, exec session 25833, at a Microsoft account chooser.
Do not automate authentication. No Azure credential is available to signing yet.
Ignore the expired first device code; user must finish the browser login. The
profile's actual Active status/signer role must then be read and confirmed.

After login, sign staged host/bootstrap/tools and the deterministic local DLL,
export its certificate-only attachment, pin final signed host admissions, refresh
ABI/tool hashes, rebuild source kit/update envelope, test signature attachment,
prepare/activate/launch, then build signed setup with SignedUninstaller enabled.
Re-run exact final checks; upload only the reviewed source/tool setup/update
files, never the generated game DLL or original inputs. Verify R2 readback hashes
and add final links under Setup in both current/stable catalogs.

Old cloud installer, its README and checksum were removed from
`installers/2026-10-22-r1/`. Both `packs/2026-10-21-r1/index.html` and r2/index.html
were updated and read back; only original ISO/patch remain under Setup while
the signed replacement is pending. R2-replacement/removal.json records this.
No packs, ISO, patch, Access policy or public development URL was changed.

The earlier complete first-install test stopped after 30,085 bodies without a
stderr diagnostic. Its work is preserved. Native preparation failure now reports
the child exit code in new launchers. The identical frozen harness is resuming
the old test in exec session 23096; root
`D:/MW3 Fresh Install Trial-20261022-r1`, preparation-resume-r1.log and
result-resume-r1.json. Initial resumed body PID 30616, orchestrator 86460; inspect
current identities before acting. Do not duplicate it or replace frozen tools.
The resumed lane **completed successfully at 08:12 local**: 37,201 bodies plus
the remaining startup/heap components, SDK-free link, complete runtime validation
and atomic activation. result-resume-r1.json records exit 0. The installed
preparation.json says reused_previous_native_code=false. This closes the prior
frozen package's full first-install lane; it does not replace signed-toolchain
integration or a clean Windows machine test. No NativePreparer process remains.
Protected controls Python 6536/5196 and unrelated server 4164 remain untouched.

## Core Critical continuation

Launcher 1.0.19 introduces .ccupdate launcher upgrades and explicit game-specific
package identities. See [Core Critical package contracts](core-critical-launcher-and-game-packages-2026-10-22.md)
for the current source implementation, compatibility rules and remaining real
signed-upgrade test. Rebuild the pending setup from the latest source rather than
shipping the earlier unsigned 1.0.17 artifact.
