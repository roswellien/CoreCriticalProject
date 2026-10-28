# Latest native playtest installer

Superseded for first-install delivery by the [precompiled 1.0.20 installer](precompiled-playtest-installer-2026-10-22.md).
The source-only build below is retained as historical evidence.

The user paused further performance work and requested a complete private
playtest installer from the latest selected native code, with Azure Artifact
Signing. The working development launcher and player settings are preserved.
Formal native acceptance remains 131/144.

The selected development host is
`d52fbf63c9bfbb04344bfa2fe78f81f6a85488011b16ca18144c1f4fb42d53dc`.
The release uses the same seven authored host objects and the verified 37,348
original-file-generated objects to establish the split host/module boundary.
Only the authored host, generation tools, recipes and detached certificate
information may enter the installer. Original inputs and generated game code
remain local. Content packs remain separate imports.

The private build root is `D:/MW3NativePlaytest-20261022-r3`. The launcher target
is Core Critical 1.0.19-preview; the source runtime version is
playtest-20261022-r4, sequence 4 (sequence 3 belongs to an older unsigned build).
This replaces neither the selected development
profile nor any existing release artifact while validation is incomplete.

The release carries the performance monitor, resource and pipeline warmups,
submission optimization, bounded texture preparation, texture staging, cached
world setting and controller support. Runtime capability fields and launch
flags must match the selected code. Replay and monitoring default off; player
choices remain independent.

At the unsigned checkpoint, Azure account inspection succeeded and the corecritical-playtest PublicTrust
certificate profile is Active. A staged bootstrap signing request returned
403 Forbidden. The account currently lists Artifact Signing Identity Verifier
at the signing-account scope; Certificate Profile Signer access is pending
the owner's response. No valid signature or completed signed installer is
claimed at that checkpoint. The signing continuation below supersedes the blocker.

Required final checks are signature and timestamp verification for the final
staged payload, signed source-envelope verification, isolated preparation and
activation, a real live-menu/normal-exit smoke test, and the signed outer setup
and uninstaller. The previous packaged first-install generation passed in its
recorded scope; clean Windows testing of this new release remains separate.
No cloud publication or commit is authorized by this build record.

## Unsigned review build completed

`Setup-unsigned-review/MW3Remaster-Playtest-Preview-Setup.exe` is 268,340,434
bytes, SHA256
`036a27379838953d304a14b659053c63c44a647e028556edcab2145944a46d1f`.
This is a review draft, not the Windows-signed delivery artifact.
Its signed source envelope targets launcher 1.0.19 and source runtime r4,
sequence 4. The source archive contains 692 pinned files, no original images
and no generated game module. The separate envelope signature verifies.

All 37,348 generated object hashes and both ABI interface files match the
previous release. The current seven authored objects produce unsigned split
host `d47ff4312bb23527451d0dc72f5abb31c520ae65eed199ad3709041b5c65a64a`;
exact pack compatibility admissions are added. The deterministic locally
generated module remains
`a71796e1d679322e2adf2c1e36309fd22ed9b418e3992fa9971b071c392a2654`.
The module remains outside the installer.

The full C# launcher suite, 12 prepared-pack checks, five preparation checks
and four certificate-framing checks pass. Real source preparation reuses only
the verified previous module, passes complete runtime validation, and passes
signed-envelope preparation and atomic activation in isolated user storage.
The rebuilt host displays the original live menu and closes normally with exit
0 in isolated session 42fe0f4a718b4d4782daf2321e310197. This run uses no optional
content packs; it is not full gameplay, campaign or all-pack acceptance.

Preserved draft failures: running the preparer directly created an unlisted
Python bytecode file, which the package builder rejected. A fresh bytecode-free
source copy is used. Windows PowerShell 5.1 then refused the signing script;
the completed package uses the existing PowerShell 7 runtime. Neither failed
attempt was reused as a successful package.

After authorized signer-role access is available: sign the staged host,
bootstrap, compiler/runtime dependencies and local deterministic module;
export its certificate-only attachment; refresh exact host/media admissions,
ABI and dependency pins; rebuild the source kit and envelope; retest preparation,
attachment and launch; then build the final installer with signed uninstaller
and verify its timestamp and Windows trust. Do not just sign the unsigned draft
outer EXE and claim its inner files were signed.

## Signed installer completed

The owner explicitly approved granting their account Certificate Profile Signer
on corecritical-playtest. The role was assigned only at that certificate-profile
scope. Signing then succeeded without another login. The assignment receipt is
retained locally; other Azure permissions were not changed.

Final installer:
`D:/MW3NativePlaytest-20261022-r3/Setup-final/MW3Remaster-Playtest-Preview-Setup.exe`

- Core Critical 1.0.19-preview, source runtime playtest-20261022-r4, sequence 4.
- 268,639,616 bytes; SHA256
  `1d43508c85784e8ca12eefc1c72853fe6609a584c145e9ff634b4385472083f0`.
- Outer setup and installed uninstaller both have Valid, timestamped Windows
  signatures. Publisher identity is JOSHUA BLACKWELL. All 463 launcher PE files
  and all 65 source-preparation PE files verify with timestamps; upstream valid
  signatures are retained. The local generated module is separately signed.
- The detached module certificate reconstructs the signed file byte-for-byte.
  The source package contains only its certificate attachment, not game code.
- Signed host SHA256 is
  `9e93ed872e7426126fee78707572d02fe8f67d032b5466e68e82e7ebf448a721`.
  Signed generated-module SHA256 is
  `6d6e3c25fef68727113a6d52859253883dbb554958ddaa5a091187667aa8bfa5`.
- Exact signed-host pack admissions and signed-extractor admission are added.
  Certificate-only checks prove the host/extractor executable bytes unchanged.
  The extractor's final publication provenance records both unsigned and signed
  hashes. Tool, ABI, runtime and source-envelope pins describe the signed bytes.
- Signed source-envelope preparation and activation pass in isolated user storage,
  reusing verified unchanged native code. The selected signed host/module reach
  the live menu and close normally, exit 0, session
  34b1d05b15184613b6e5d6d2c3e3cdaf. The full launcher suite and focused pack and
  certificate tests pass.
- Final setup installs into a separate trial directory. All 475 published files
  match installed bytes; the installed setup/uninstaller/launcher/SDL/extractor
  signature checks pass. Uninstall succeeds and removes its trial registration.
  The ordinary development profile and saved settings remain byte-identical.

Evidence includes release-status.json, installer-build.json, signature receipts,
source/launcher signature audits, final-windows-signatures.json, exact source and
installed-file pins, signed activation/launch logs, and final install/uninstall
logs. The final directory includes README.txt and SHA256SUMS.txt.

This is a private playtest build, not clean-Windows or whole-game acceptance.
Fresh generation with the signed toolchain has not been repeated through all
37,348 objects; prior full first-install evidence retains its earlier scope.
Content packs remain separate imports. The signing pass made no upload, public
feed, source commit or change to the 131/144 acceptance count. The owner then
authorized the separate publication below.

## R2 publication

Uploaded the exact final signed installer, README.txt and SHA256SUMS.txt to the
existing core-critical-playtests bucket under installers/2026-10-22-r4/.
The complete remote installer download matches its 268,639,616-byte size and
SHA256 above; the downloaded Windows signature and timestamp also verify.

Download:
https://playtest.corecritical.dev/installers/2026-10-22-r4/MW3Remaster-Playtest-Preview-Setup.exe

Both current and stable catalog pages, packs/2026-10-21-r2/index.html and
packs/2026-10-21-r1/index.html, now list this installer first in Setup, with
setup notes and its checksum. Existing links are preserved. Each catalog was
checked for concurrent changes before publishing, then read back byte-for-byte.
Both sidecar files also match remote readback. Access policies, other objects
and the runtime update feed were not changed.

Private publication evidence and previous catalog copies are under
D:/MW3NativePlaytest-20261022-r3/cloud-upload/. The upload-receipt.json records
the exact remote identity and verification results.
