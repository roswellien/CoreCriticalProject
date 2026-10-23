# Precompiled playtest delivery replaces first-install code generation

The current installer is [1.0.24-preview with the large texture archive repair](large-texture-archive-repair-2026-10-22.md).
It retains the [1.0.22 clean-install renderer setup repair](clean-install-renderer-repair-2026-10-22.md).
It also includes [asset installation status and progress](asset-installation-progress-2026-10-22.md). The 1.0.20 delivery evidence
below records the initial precompiled release; 1.0.24 adds the scoped native
texture-offset repair and reuses the translated module unchanged.

The owner explicitly authorized precompiled native runtime delivery for private
playtests on October 22. The source-only installer required 37,201 body builds
plus startup/linking and took hours. That delivery restriction is superseded
for this scope, recorded in legal.md. Original game data verification remains;
testers no longer regenerate game code. Original media and content packs are
not included in the launcher installer. Generated source is not committed.

Core Critical 1.0.20-preview includes native playtest-20261022-r5. It packages
the same already-tested signed native host/module and portable runtime. There
is no compiler toolkit or source-preparation archive in the publication. The
original ABI, native gameplay, renderer, controller support and recent
performance fixes are unchanged. Strict acceptance remains 131/144.

The installer builder accepts a validated RuntimeDirectory, mutually exclusive
with PreparationBundle. Runtime files are explicitly included by Inno. Setup
verifies the complete runtime manifest instead of starting NativePreparer.
An explicit manifest marker prevents stale source-update metadata from selecting
the old preparation flow. Inno also removes the two obsolete installer-owned
Preparation/initial files on upgrade, preserving player data and optional packs.
Legacy source preparation remains available for legacy packages.

## Validation

The full C# launcher suite passes, including precompiled delivery with stale
source metadata and preserved legacy source behavior. Complete runtime validation
passes before packaging and on the installed payload. Unknown precompiled
manifest versions fail visibly. Signing and original-input checks remain required.

An isolated install seeded with old preparation triggers completes in **5.819
seconds** on the development PC. Both triggers are removed. Full original-file
verification and support setup take **5.636 seconds**, measured separately,
including test-tool startup. Native game-code generation is not invoked. These
are local measurements, not a promise for ISO extraction or another machine.

The installed runtime reaches the live original menu and exits normally with
code 0 in session b0d31ceb837c4622b0d22a18e96344e0. The signed native host/module
are the same identities verified by the prior release. Setup and installed
uninstaller signatures are Valid and timestamped. Uninstall succeeds and removes
its test registration. The real clean-machine trial remains with the owner;
extended gameplay and broad device compatibility remain open.

## Delivered artifact

Private evidence root: D:/MW3PrecompiledPlaytest-20261022-r1.

Final setup is 92,295,656 bytes, SHA256
`1b90d078e2989c9c48997018473864678066ec784c40cf55d634a25bbf887c3f`.

Download:
https://playtest.corecritical.dev/installers/2026-10-22-r5/MW3Remaster-Playtest-Preview-Setup.exe

The exact signed installer, README and checksum are uploaded to the existing
core-critical-playtests R2 bucket. Both current and stable catalog Setup lists
replace the source-only installer with this precompiled build. The complete
remote installer readback matches SHA256 and retains a valid timestamped Windows
signature. Catalog snapshots are checked for concurrent changes before upload,
and remote pages/sidecars are compared to the intended bytes afterward. Existing
asset, ISO and patch links are preserved; Access policy and update feeds are
unchanged. Previous release objects are retained as historical artifacts.

For the interrupted clean-machine install, cancel old native preparation and
close the old launcher, run the new installer, then choose the already-created
original game-data folder in Set Up Game. Do not repeat source generation or
discard downloaded packs/original data. No source commit is made.
