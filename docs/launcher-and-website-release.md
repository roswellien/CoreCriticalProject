# Launcher and website release checklist

This checklist is the maintainer's ordered release path. It uses the committed
launcher builders and update-catalog tool; interactive review, installed tests,
Cloudflare uploads and feed promotion are written steps. Only the maintainer's
account publishes. Keep credentials, local dependency outputs, precompiled
runtime inputs and release artifacts outside Git.

## Launcher release

1. **Start from reviewed source.** Merge the release PR from `develop` to
   `main`, then make a fresh clone of the repository and check out that exact
   merged `main` SHA. Confirm the clone is clean and record the SHA. Read the
   launcher version from `tools/mw3-remaster-launcher/MW3RemasterLauncher.csproj`;
   do not edit release source after this point. Use a new public version and
   positive update sequence for a new release.

2. **Supply the build inputs.** Use Windows with the .NET SDK required by the
   launcher project, Inno Setup 7 (`ISCC.exe`), and the Windows SDK SignTool.
   Supply a validated precompiled runtime directory from its separately
   reviewed native build, including its `runtime.json` receipt. The runtime is
   generated output and stays local. The release builder validates it before
   packaging. The maintainer also supplies, outside the clone, the update
   signing PEM and key ID, plus Azure Artifact Signing's SignTool Dlib and
   metadata file and its locally authenticated signing credentials. Never
   commit any private key, signing metadata with credentials, or token.

   If the runtime changes and existing players need an update, package it with
   the committed `tools/native-preparation/build_precompiled_update.py`, using
   the same runtime directory, reviewed `InstallPrecompiledRuntime.exe`,
   original-file input directory (read-only), and a fresh output directory:

   ```powershell
   python tools/native-preparation/build_precompiled_update.py `
     --runtime '<validated local precompiled runtime directory>' `
     --preparer '<reviewed InstallPrecompiledRuntime.exe>' `
     --game '<user-supplied original game directory>' `
     --output '<fresh runtime update output>' --version '<public-version>' `
     --sequence <positive-runtime-sequence> `
     --signing-key '<external update-signing PEM>' --key-id '<trusted-key-id>'
   ```

   Keep its output names `<version>.mw3update` and `<version>.zip`. Do not
   include the original game directory in the output.

3. **Stage the pinned launcher dependencies.** Run
   `tools/mw3-remaster-launcher/fetch_controller_runtime.ps1`; it downloads and
   hash-checks SDL 3.4.18 into ignored `local/`. Build Unshield from the pinned
   source recipe and stage its reviewed output:

   ```powershell
   pwsh -NoProfile -File tools/mw3-remaster-launcher/fetch_controller_runtime.ps1
   $mediaBuild = Join-Path $env:TEMP 'mw34-installer-media-release'
   pwsh -NoProfile -File tools/mw3-remaster-launcher/build_media_tools.ps1 `
     -OutputDirectory $mediaBuild
   pwsh -NoProfile -File tools/mw3-remaster-launcher/stage_media_tools.ps1 `
     -PublishDirectory local/launcher-release/Publish `
     -MediaBuildDirectory (Join-Path $mediaBuild 'payload')
   ```

   Use fresh ignored output directories. The media-tools build requires an
   installed CMake and Visual Studio C++ toolchain; it downloads only the
   source archives whose hashes are pinned in the committed script.

4. **Publish and package.** Publish the launcher into the same fresh
   `Publish` directory (so staged dependencies are not overwritten):

   ```powershell
   dotnet publish tools/mw3-remaster-launcher/MW3RemasterLauncher.csproj `
     -c Release -r win-x64 --self-contained true `
     -o local/launcher-release/Publish `
     --artifacts-path local/launcher-release/dotnet-artifacts
   ```

   Then run the committed orchestrator with the maintainer-supplied inputs:

   ```powershell
   pwsh -NoProfile -File tools/mw3-remaster-launcher/build_launcher_release.ps1 `
     -Compiler '<path to ISCC.exe>' `
     -PublishDirectory 'local/launcher-release/Publish' `
     -RuntimeDirectory '<validated local precompiled runtime directory>' `
     -OutputDirectory 'local/launcher-release/Release' `
     -Version '<public-version-preview>' -Sequence <positive-sequence> `
     -SigningKey '<external update-signing PEM>' -KeyId '<trusted-key-id>' `
     -WindowsSignTool '<path to signtool.exe>' `
     -SigningDlib '<external Azure signing Dlib>' `
     -SigningMetadata '<external Azure signing metadata>'
   ```

   The orchestrator calls `build_installer.ps1`, `build_ccupdate.ps1`,
   `sign_windows.ps1` and `sign_runtime_update.ps1`. Review
   `Release/launcher-release.json` and each installer receipt. Publish the exact
   `setup_filename` from `installer-build.json`. The installer must keep its
   version in its filename, and the update files must be named
   `<version>.ccupdate` with the matching `<version>.zip`.

   For offline launcher updates, create the optional wrapper
   `<version>-cc-update.zip` containing the two files at the archive root named
   exactly `<version>.ccupdate` and `<version>.zip`, plus a `README.txt` with
   import instructions. Test the ZIP before publication. Write a `README.txt`
   and `SHA256SUMS.txt` for each installer/update download directory using the
   exact receipt filenames and SHA-256 values; do not rename the built installer
   or either update file.

5. **Review and test before upload.** Verify the source SHA and artifact hashes
   in the receipts; verify every Windows signature and timestamp; inspect the
   installer contents and confirm the original game media and signing material
   are absent. On an isolated Windows test account or VM, install the signed
   setup with user-supplied original game files, upgrade an existing supported
   install using the signed `.ccupdate` and matching ZIP, confirm settings,
   saves, packs and the precompiled runtime are preserved as expected, then
   test runtime update/rollback when the release changes the runtime. Record
   results and clean up only the isolated test installation. Do not publish
   until these checks pass.

6. **Prepare the signed online catalog.** Use the committed
   `tools/update-service/build_catalog.py` with the new launcher metadata and
   the current approved signed runtime metadata/package (or the new runtime
   package when it changes). It requires version-matched `.ccupdate`/`.mw3update`
   files and companion ZIPs, the installed `update-trust.json`, the external
   update signing key, key ID, approved origin and a new catalog sequence:

   ```powershell
   python tools/update-service/build_catalog.py `
     --launcher '<fresh-output>/<version>.ccupdate' `
     --runtime '<approved-runtime-output>/<runtime-version>.mw3update' `
     --base-url 'https://core-critical-updates.jcblackwell84.workers.dev' `
     --sequence <new-catalog-sequence> --output '<fresh-catalog-output>' `
     --signing-key '<external update-signing PEM>' --key-id '<trusted-key-id>' `
     --trust-file tools/mw3-remaster-launcher/update-trust.json
   ```

   This verifies both signed packages and writes a signed catalog plus
   `publication.json`; it does not upload. If only the launcher changed, retain
   the existing runtime version and signed package. Catalogs expire after 30
   days, so a renewal still needs a new higher catalog sequence.

7. **Upload immutable release objects to R2.** The R2 bucket is
   `core-critical-playtests`. The public read-only Worker is
   `core-critical-updates`, with R2 binding `UPDATES`; its public base URL is
   `https://core-critical-updates.jcblackwell84.workers.dev`. Use the
   maintainer's authenticated Wrangler session. For each entry in the
   `objects` array in `publication.json`, upload its exact local file to the listed key, first
   confirming that an existing immutable key is either absent or already has
   the same size and SHA-256. The catalog builder names update objects under
   `online-updates/launcher/<version>/` and
   `online-updates/mw3/<version>/`. Never overwrite a versioned key with
   different bytes.

   The signed installer is a separate, protected Setup download. Upload it
   under `installers/<release-date>-<revision>/<setup_filename>` in that same
   bucket, with the `README.txt` and `SHA256SUMS.txt` for the exact artifact.
   Preserve the private playtest Setup catalog history and all existing rows;
   add the new installer/update links and checksums to both current catalog
   snapshots at `packs/2026-10-21-r1/` and `packs/2026-10-21-r2/`. Preserve old
   release objects and compatibility URLs. The public update-only Worker must
   not expose installer, pack, ISO, patch or other protected objects.

   Wrangler command form for each object (use a new local readback file):

   ```powershell
   npx --yes wrangler@4.151.0 r2 object put 'core-critical-playtests/<object-key>' `
     --file '<local-file>' --remote --content-type '<content-type>'
   npx --yes wrangler@4.151.0 r2 object get 'core-critical-playtests/<object-key>' `
     --file '<fresh-readback-file>' --remote
   ```

   Compare readback byte count and SHA-256 to the local receipt. For public
   update objects, download them through the Worker and verify full SHA-256,
   byte count and a resumed Range request as well.

8. **Promote the feed last.** Extend the existing Worker's `PUBLIC_OBJECTS`
   allowlist with the four exact new update metadata/package paths and byte
   counts from `publication.json`, retaining every existing entry. Deploy the
   `core-critical-updates` Worker with the existing `UPDATES` binding to
   `core-critical-playtests`; do not replace the allowlist with only the new
   release. Upload the signed catalog first to its sequence archive key
   `online-updates/catalogs/playtest/<sequence>.json`, then to the live feed
   object `online-updates/catalogs/playtest/catalog.json`. This live object is
   the **playtest update feed**. Confirm the prior live catalog has not changed
   since review before promotion. Read back the live object, verify its hash and
   signature, then check discovery and download through the public Worker.
   Retain the prior catalog and publication receipts for rollback evidence.

   The exact upload/readback and catalog checks are also documented in
   [`tools/update-service/README.md`](../tools/update-service/README.md).

9. **Verify the protected Setup listing.** Read back both playtest Setup
   catalog snapshots from these R2 keys: for each of `r1` and `r2`,
   `packs/2026-10-21-<revision>/index.html`,
   `packs/2026-10-21-<revision>/packs.json` and
   `packs/2026-10-21-<revision>/SHA256SUMS.txt`. Verify only the intended
   setup rows, release fields and checksum lines changed; retain every existing
   pack, asset and native-update row. Read the objects back after upload, then
   check the versioned installer URL and download filename through
   `playtest.corecritical.dev`. Keep this protected installer publication
   separate from the public update-only feed.

## Website deployment

The public project site at `corecritical.dev` is a separate Cloudflare Pages
project. From `website/`, run `python build.py`, inspect the generated `dist/`,
and confirm the complete deployed site source is present. This repository
snapshot does not contain the linked `projects.html`, `media.html`, `about.html`
or `project.html` pages, and the approved artwork in ignored
`website/assets/plates/` needs to be staged by the maintainer. Reconcile those
inputs with the current Pages site, and verify all links and assets in `dist/`
before deployment. Then publish with:

```powershell
npx --yes wrangler@4.151.0 pages deploy dist --project-name core-critical
```

The maintainer supplies Cloudflare authentication locally. Confirm the deploy
URL and inspect the live homepage, generated development news, navigation and
assets. Do not put Cloudflare tokens in Git. See [website/README.md](../website/README.md)
for the local preview and site details.

## Evidence and external inputs

Record the merged `main` SHA; tool versions; runtime and artifact identities;
signature, install, upgrade, update and rollback results; R2 keys and readback
hashes; catalog sequence and public discovery result; Setup listing readback;
and Pages deployment URL. The maintainer supplies the precompiled runtime,
Inno Setup, Windows SDK, Visual Studio/CMake toolchain, Azure signing
credentials, update signing private key, and authenticated Cloudflare access.
These are deliberate external inputs; no local orchestration script or private
path is required from the previous machine.
