# Core Critical 1.0.27 private playtest installer

Owner request: offer one current installer on the protected playtest download
site, with the latest launcher and complete current native runtime together.
Existing optional asset-pack downloads remain separate.

The release combines the current Avatar/Strider host, render-state reuse with
viewport-deletion invalidation, existing texture-fault diagnostics, and the
corrected diagnostic host's CPU/RAM/Vulkan metadata. LLVM lld-link produces the
native process executable; the translated module remains unchanged. The signed
host SHA-256 is
`0c5a3a77b254ed4d462f6ab6571a63e60456a68736e51df0580fd03acb452d03`.
Frozen sources, compiler/linker inputs, signatures and test receipts are private
under `D:/CoreCriticalPlaytest-1.0.27-20261023-r1`.

The self-contained launcher is named `Core Critical Launcher.exe`; the installer
is `corecriticalinstaller-1.0.27-preview.exe`. Original game files and optional
content packs are excluded. Original-file verification and the existing ISO /
installed-directory setup flow remain required. Neither the Windows SDK nor a
native compiler is required on the tester's PC.

A full installer may declare `supersedes_runtime_versions` in its bundled
runtime manifest. Runtime discovery uses the bundled runtime in place of those
explicitly retired selected updates, retaining all stored updates, selections,
saves, packs and settings. Unlisted future updates continue to take precedence.
Fixtures cover both cases and confirm that selection data is preserved. This
closes the specific defect where reinstalling otherwise keeps launching a known
old game update from retained user storage.

Release validation builds now use an isolated output directory so an open dev
launcher does not lock the release build's application files. The full launcher
fixture suite passes. The exact signed native executable presents 1,600 Training
frames through Vulkan. All 1,600 original draw records and five full-resolution
captures match the latest validated predecessor under matched settings. The
frame-budget exit is intentional. Earlier hidden-window evidence is retained
separately and is not counted as displayed frames.

Execution boundary: current maintained native work is composed into the
installed delivery path, with explicit retirement of old runtime selections.
This is not a confirmed fix for the remote Op1M1 crash, a fresh-machine test, or
additional formal gameplay credit. Acceptance remains 131/144. No commit was
requested or performed.

## Delivery

[Current signed installer](https://playtest.corecritical.dev/installers/2026-10-23-r3/corecriticalinstaller-1.0.27-preview.exe)
is 92,585,736 bytes, SHA-256
`dab387e49cd47b685ce903d55e45e6e471aa37e67e6ce08fd8b61b0e27f9fb72`.
The full remote download matches and its Windows signature verifies as valid.
The exact final installer installs into an isolated directory; the installed
runtime validates and its native executable starts as a Windows process.

Both protected catalogs were downloaded after publication and compared against
the intended page bytes. Each has one Setup row, this installer, and unchanged
asset-pack rows. Superseded update and original-media links were removed from
Setup to present one installation path. Five identified old installer objects
were backed up locally and deleted from R2; the prior current 1.0.26 URL now
returns not found. Private deletion/backup receipts are retained with the build.
