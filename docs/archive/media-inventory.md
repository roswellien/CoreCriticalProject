# Local media and installation provenance

Recorded 2026-10-06 from the user-supplied media, completed installation, and
independent file verification. No original files or extracted payloads are
stored in this document.

## Completed installation

MechWarrior 3 was installed through the original wizard into
`D:\Projects\MW34Recomp\MW3`, then updated with the supplied cumulative 1.2
patch. The user completed the installer and updater's interactive steps.
The selected folder also contains three preexisting media directories; those
directories were excluded from game-file inventories and backups.

| Property | Verified installed value |
| --- | --- |
| Research profile | `mw3-us-1-2-retail` |
| Executable | `MW3/Mech3.exe` |
| Size | 2,384,384 bytes |
| SHA-256 | `95bc2c114c9b2e5c5ada8e40ca78cc79470f862e45313ffad0d1e8e6d4d916bf` |
| File and product version resources | `1, 2, 22, 0` |
| Game registry version | `1.2` |
| PE identity | PE32 / i386, preferred base `0x00400000`, entry RVA `0x001AC3A0` |

The exact identity is admitted in
[`supported-binaries.json`](../../games/mw3/config/supported-binaries.json).
The binary validator and metadata analyzer with `--require-supported` both
passed. PowerShell independently confirmed the full SHA-256 digest.
Installation and input identity are verified; gameplay and recompilation have
not been tested.

Before patching, the original 1.00 installation was preserved at ignored
`local/mw3-baseline-v1.00/`: 118 game files totaling 421,460,111 bytes. Every
source/copy path, size, and digest matched. Its executable exactly matches the
staged base executable documented below. Post-patch verification rehashed this
backup and confirmed it was unchanged.

The patched installation contains 130 game files totaling 422,066,496 bytes:
20 changed, 12 added, 98 unchanged, and none removed relative to the baseline.
Both inventories were stable during verification. Private local evidence:

* `local/tools/mw3-base-installation.json`: original inventory and registry snapshot.
* `local/tools/mw3-patched-installation.json`: patched inventory, differences, and provenance.
* `reports/mw3-installed-v1.2.json`: PE/import metadata for the admitted image.

SignalRGB was restored after the updater exited; both its normal launcher and
application processes were verified running. The ISO remains mounted as F:.

## Media observations

* An ISO under the user's `MW3/` media folder has ISO9660 volume label `MW3`.
  The listing contains `DATA1.CAB`, `DATA1.HDR`, setup utilities and DirectX 6
  redistributables. The later extraction described below recovered the game
  executable from those cabinets. The small registration utility on the disc
  is not the game executable.
* The supplied `mw3v12.exe` patch package is 6,335,192 bytes, is an i386 PE, and
  contains an InstallShield marker. Its SHA-256 is
  `4409f3122553d68d3cfc9b0b0694300b3349d1584af3fa87654ddd7ae9edd50d`.
  This is the **patch package hash**, not the patched game executable hash.

The initial media inventory used read-only ISO directory traversal and SHA-256
hashing, without executing an installer. Local `MW3/`, `MW4/`, `local/`, `reports/` and common
media formats are ignored by Git. Later-game media have not been analyzed.

The repository analyzer also inspected the patch package successfully:

```powershell
python tools/analysis/analyze.py "MW3/MechWarrior-3_Patch_Win_EN_Patch-12/MW3 - Patch 1.2/mw3v12.exe" --output reports/mw3-patch-package.json
```

The local report records preferred image base `0x00400000`, entry RVA `0xCE00`,
five sections and 147 imports across seven libraries. These are installer
dependencies and must not be reused as the game's API inventory. The validator
rejects this installer hash because it is not the admitted game image. The report
remains ignored local research output.

## Subsequent installation attempt and media evidence

On 2026-10-06, the user requested an installation from the supplied ISO. It was
mounted as drive F: during that attempt. The disc's `README.TXT`, lines 2 and 4,
identifies the media as Version 1.00 (U.S.), dated 11 May 1999. This is evidence
about the base media; installed executable identity was established separately
as recorded above.

The ISO is 545,073,152 bytes with SHA-256
`08c26c0d71375d6130df7716abc2c282147494d869bd48ce13bd5f972f763e49`.
The hash was calculated with PowerShell `Get-FileHash -Algorithm SHA256`.

The first setup attempt reached Windows' administrator permission
prompt without completing installation. The user subsequently
reported being remote and unable to approve it, and requested planning work.
Later attempts rechecked mounted drive letters and installer state before
continuing.

The patch wrapper's version metadata identifies an InstallShield package stub;
it does not establish the patch's prerequisites. Preserve base-executable
metadata before updating, inspect the patch instructions, and record any patched
game executable as a separate identity. See [the execution plan](initial-phase-plan.md).

## Resumed installation and verified staging

The user resumed installation on 2026-10-06 and reported approving Windows'
administrator prompt. Both the automated launch and a subsequent manual launch
left `SETUP.EXE` running without an installer window. The disc launcher identifies
itself as 32-bit InstallShield 5.52 (`5,52,164,0`), so a replacement for a 16-bit
launcher is not justified by this observation.

A read-only wait-chain query from the ordinary process token returned Windows
error 5 (access denied); it did not identify a blocking process. A subsequent
elevated diagnostic launch was canceled before running. Task Manager was opened
for a manual **Details > SETUP.EXE > Analyze wait chain** check because its
elevated controls were unavailable to the automation helper. That initial
diagnostic attempt did not identify the blocker.

A later diagnostic ran after user-approved UAC elevation and temporarily enabled
the diagnostic process's already-granted `SeDebugPrivilege`, restoring its
previous state after each read. The first capture found that setup had already
exited. A subsequent observed launch captured the following wait chain in
multiple snapshots: `SETUP.EXE` thread -> synchronous `SendMessage` ->
`SignalRgb.exe` thread. This identifies SignalRGB as an observed startup blocker
on this machine. The local evidence is in ignored
`local/diagnostics/setup-startup-20261006T230113.154318Z.json`.

Closing SignalRGB's window left it running in the tray. Stopping that specific
blocking process caused its launcher to restart it. Temporarily stopping the
identified SignalRGB launcher and application together cleared the hang, and
setup proceeded to its wizard. SignalRGB's supported tray-menu **Quit** is a
manual alternative. Both processes were restored after installation and
patching. Do not infer that every InstallShield hang has the same cause.

Separately, upstream Unshield 1.6.2 at commit
`51de441ba6893f11026d4671ccef9e8e2a4634fa` was built using the existing local
toolchain, without installing a system package. The disc's `DATA1.CAB` passed
Unshield's test for all 126 files, totaling 423,912,438 expanded bytes. Reviewed
archive paths were extracted to ignored `local/mw3-staged/`, which retains the
installer's file-group layout. **This is verified staging, not a completed
installation.** No registry configuration, patch, or game launch is implied.

The staged `Program_Files/Mech3.exe` has:

| Property | Observed value |
| --- | --- |
| Size | 2,357,248 bytes |
| SHA-256 | `1c6419fcdbb0503d2dee006861477fc7354039e6ce95c431b5ac5e4995b465bc` |
| File version resource | `1, 0, 0, 8` |
| Product version resource | `1, 0, 0, 0` |

PowerShell independently calculated the digest with `Get-FileHash`. The base
media's 1.00 release label and the executable's version resource are recorded
separately. The completed base installation matched these bytes exactly. Only
the subsequently installed 1.2 image is admitted in the current manifest.

The supplied patch's MD5 also matches the package associated with the preserved
[1.2 release instructions](https://www.moddb.com/games/mechwarrior-3/downloads/mechwarrior-3-v12-english-patch):
`63bc6d69001e4ab44d8e546f6b978fa9`. Those instructions state that 1.2 includes
the 1.1 changes and can update either 1.0 or 1.1. This is a mirror of the release
instructions; the installed result was independently verified as recorded above.
