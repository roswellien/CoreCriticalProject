# Private source installer integration, October 22

Later continuation: [updates/save backups and rebuilt playtest setup](playtest-updates-and-save-backups-2026-10-22.md)
records launcher 1.0.17, the rebuilt lower-horizon host, successful full packaged
first-install generation/activation after resume, removal of the old R2 setup,
and Windows signing pending the user's Azure CLI browser sign-in. Historical
running/pending notes below describe the earlier checkpoint.

Execution boundary: original files -> reproducible objects -> native game DLL ->
installed runtime -> signed atomic activation. Acceptance remains **131/144**.
No Training entry is credited. Original/derived game material remains local.
No commit, publication or normal user deployment was performed.

## Completed evidence

All paths below are private local evidence.

- `D:/MW3NativePreparationTrial-20261022-r1/Bodies/generation.json`: 37,201
  exact unique bodies, all generated from original files; finished October 21
  at 23:28 local, approximately 2h34m. No old-cache substitution.
- `LinkedRuntime/generation.json`: all 37,348 generated objects linked with
  seven authored host objects. EXE SHA256
  `8ea8f9bd74bd5591ee0a1211ea1af6ddf936f7c0c32f0c9ea2fddd354ce7d63c`.
  `LaunchTrial-r1`: live menu, normal exit 0, 6,135 frames, replay 0.
- `SplitHost-r1`: host SHA256
  `e293b3a5f79d3d85f7c04ddcd9f857046e66583f6c7d18255e3ceb43c2cfc46c`.
  Host contains authored objects and import metadata; translations are a DLL.
  `SplitLaunch-r1`: live menu, normal exit 0, 4,587 frames.
- `SdkFree-r1`: deterministic translated DLL SHA256
  `a71796e1d679322e2adf2c1e36309fd22ed9b418e3992fa9971b071c392a2654`.
  No SDK/CRT import libraries, stripped compiler environment, /NODEFAULTLIB;
  imports only the authored host. `SdkFreeLaunch-r1`: live menu with initially
  empty registry, normal exit 0, 1,632 frames. Translated code creates defaults.
- `Bootstrap-r2/NativePreparer.exe`: authored static bootstrap SHA256
  `75e803545daacadd8ce2cdf3a9a9f9b41efa5b99f7a22f38a772b9aa55551ed4`.
  Runs bundled Python/tools; no installed developer SDK is required to link.
- `PreparedUpdate-r1`: real preparer output passes complete launcher validation.
- `D:/MW3SourcePreparerTrial-20261022-r3`: 690 tool/payload files, no original
  images or compiled game module. Inputs are pinned. Synthetic import libraries
  and symbol metadata do not contain translated game code.
- `D:/MW3SourceInstallerBundle-20261022-r2`: signed private source package,
  version playtest-20261022-r2, sequence 2. ZIP 232,100,820 bytes, SHA256
  `5802abcf1350d27b91761e64baee115f472b1eaadce3a3a5afe125b9f959f4da`.
  Trial signing private key stays outside the package. Public trust only;
  feed URL empty. No production release identity was configured.
- `D:/MW3 Bundled Preparation Trial-20261022-r1`: real signature/archive/input
  checks, child preparation with spaces in paths, verified prior native code
  reuse, complete runtime validation and atomic activation pass. This trial's
  private prior Runtime was never copied into the installer publication.

## Installer and launcher

Source version 1.0.15-preview connects existing-installation/ISO-plus-patch setup
to signed preparation automatically. It reports counts, supports cancellation
and owned resume, retains per-attempt logs, and verifies original inputs before
and after. A running game prevents activation. Completed output can be reused on
retry after that guard fires. Writable player registry is separate from verified
runtime versions. Installed Python does not write bytecode into those versions.
Launcher and coordinator verify the native DLL. Pack readers recognize this
exact compatible host; alternate skins remain pack data.

Built private preview:
`D:/MW3SourceSetupPreview-20261022-r1/MW3Remaster-Playtest-Preview-Setup.exe`.
Read `installer-build.json` for size/hash. The publication includes signed ZIP,
metadata and public trust, not original files or a private compiled Runtime.
The receipt retains clean-Windows/full-packaged-generation as unverified.

Owner authorized upload for second-PC testing on October 22. Uploaded to existing
R2 bucket `core-critical-playtests`, key
`installers/2026-10-22-r1/MW3Remaster-Playtest-Preview-Setup.exe` (267,718,249 bytes).
Complete remote download SHA256 matches
`46f61a0fb30b8324f0e7e670ad5f9598650435b31782debf18c25770f1ec0bf3`.
Protected download URL:
https://playtest.corecritical.dev/installers/2026-10-22-r1/MW3Remaster-Playtest-Preview-Setup.exe
Adjacent README.txt records pending first-install validation and compilation time;
SHA256SUMS.txt contains the checksum. No Access policies, public development URL,
existing download catalog, pack objects or native-update feed were changed.
Local upload/readback evidence: installer output `cloud-upload/upload-receipt.json`.

Subsequently, at the owner's request, both current and stable download catalogs
(`packs/2026-10-21-r2/index.html` and `packs/2026-10-21-r1/index.html`) were updated
to list the installer first in Setup, with notes/checksum links and the pending
validation warning. Existing download links were preserved. Both pages were
read back and compared to the prepared HTML. Backups and readbacks are in the
same local cloud-upload evidence folder.

## Current first-install run: do not duplicate

Root `D:/MW3 Fresh Install Trial-20261022-r1` deliberately includes spaces.
App contains source tools/trust only, no prior Runtime. Harness was frozen from
the passing Release checks. Original inputs:
`D:/MW3InstallerProvidersTrial-20261021-r2/OriginalGame`.

Initial harness PID 7088, bootstrap 61368, orchestrator 82840, body producer 7880;
verify command lines/creation times before acting. Exec session 75768 runs this
single test. `preparation.log` shows counts. Wrapper writes `result.json` only
after completion. Require exit 0 AND complete validation/activation message.
Old body receipts do not prove completion of this packaged path. Task processes
were set BelowNormal after the user restarted their normal game. Leave that game
alone. If activation encounters the game-stopped guard, rerun the identical
frozen harness with --prepare-bundled, App, original directory and UserData after
the game closes; verified completed output can be reused.

Protected controls Python 6536/5196 and unrelated server 4164 remain untouched.
No SQLite was opened. Do not overwrite the frozen producer/tools mid-run.

## Checks and remaining gates

Full C# LauncherChecks passed, including signed child preparation, activation,
cancel/resume, tampering, unknown keys/services, source integrity, failed output,
downgrade, rollback/locking, registry and DLL integrity. These authored fixtures
confer no gameplay credit. Twenty-eight focused launcher Python checks and five
authored preparation checks passed. Broad Python discovery was not passing:
unrelated asset tooling requires NumPy; no dependency installation was attempted.

Fresh packaged first-install generation/link/activation remains running. Then
verify installed GUI setup/launch and a clean Windows installation. Preparation
time currently measured in hours needs improvement for easy playtester use.
Production trust/feed, payload distribution review and release configuration
remain open. No public feed or upload was made.
