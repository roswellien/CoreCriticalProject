# MechWarrior 4: Mercenaries reconnaissance

Inspected 2026-10-09. This is a static assessment of the installed game at
`D:\Projects\MW34Recomp\MW4`, using REA 6.1.0, Ghidra 12.1.4 and the existing
PE32 analyzer. It establishes research-input identity and planning constraints.
No game was launched, translated or admitted for native execution during this
assessment. See the [execution plan](mw4-execution-plan.md).

A subsequent user-authorized [normal-launch test](mw4-launch-test.md) failed
twice during startup. That runtime receipt supplements this static assessment;
the original static evidence and identities are preserved.

## Installed target and exact identities

The uninstall registration identifies **MechWarrior 4 Mercenaries**. Its game
registry key records `Version=1`, `VersionType=RetailVersion`, `LangID=9`, and
an executable directory matching this installation. Both principal files have
file/product version resource `50.06.09.3002`; this resource value is kept
separate from the registry version.

| Artifact | Bytes | PE32/i386 preferred base | Entry VA | SHA-256 |
| --- | ---: | --- | --- | --- |
| `MW4Mercs.exe` | 344,863 | `0x00400000` | `0x0041ACD0` | `fa317099c1336acabd1c1a3e9736d05533c6e19fb6603fa16e31a87d362bf8cf` |
| `MW4MERCS.ICD` | 3,895,418 | `0x00400000` | `0x0075A29C` | `37cdc4025c5dc2e8c48f22b2e02a2ef296878e5114453de40bcfaa835f0cc39c` |

The directory also contains Vengeance and Black Knight media ZIPs. A Vengeance
registry key points to `MW4/Mw4`, but the inspected `Mw4/mw4.exe` identifies
itself as Microsoft's **Machine Configuration Test Logging Tool**, original
filename `MACHINE.EXE`. That utility and registry entry do not establish an
installed Vengeance gameplay executable. The other titles need independent
installation and identity assessment.

## Game-code recovery is the first gate

**Observed:** the small EXE contains SafeDisc and driver-related markers.
Ghidra recovered its CRT-style entry and a call into a launcher function whose
pseudocode reports overlapping instructions and bad control flow. Its visible
static imports are 115 symbols across four Windows libraries.

**Observed:** the ICD has a 3,555,328-byte raw `.text` section with Shannon
entropy **7.99984 bits/byte**. Its `.data` raw bytes also have high entropy.
Ghidra's default inventory contains 169 procedures: **168 external entries and
only one internal entry**. That entry has an 11-byte body and decodes into
software-interrupt and interrupt-return instructions, rather than a credible
Windows game startup path. These counts describe this analysis result, not the
number of functions in the original game.

**Inferred, high confidence:** this is a protected launcher/payload pair, and
the ICD carries the main game image with its code unavailable as ordinary
on-disk instructions. Entropy alone would not establish encryption; the
launcher markers, implausible ICD entry and failed function recovery together
support the conclusion. The protection version and actual runtime transformation
were not determined. No readable gameplay function or original behavioral oracle
has been established yet.

**Observed:** the ICD retains substantial readable metadata: 8,352 analyzed
strings and 174 visible static-import symbols across 13 descriptors. The
`USER32` and `KERNEL32` descriptors yielded zero decoded symbols in this parser,
so this inventory is incomplete as an API dependency map. The other descriptors
include CRT, Winsock, Windows multimedia/codec, COM, protection and client
libraries. Their presence does not prove reachable execution.

Resource-path and GameOS markers connect the payload to the installed archive
layout. DirectDraw creation, DirectInput creation, DirectSound and DirectPlay
names are also present. These are **interface candidates**, not observed API
calls or a complete renderer contract. In particular, a `D3D8.DLL` marker in the
Machine configuration utility must not be attributed to the game's renderer.
The shipped October 2002 readme explicitly documents SafeDisc, disc-dependent
launch and DirectX 8.1/Direct3D requirements. Those documentation statements
corroborate the target assessment but do not establish current startup behavior
or the concrete graphics interface used by this executable.

## Installed data and a bounded first slice

The installed-only inventory excludes the original-ISO directory and media
ZIP/ISO files: **228 files, 1,218,450,366 bytes**. `RESOURCE` accounts for
162 files and 1,111,391,637 bytes.

Bounded directory parsing covered **113 `.mw4` archives** with the `#VBD`
signature. All sampled fields at offsets 4 and 8 are 4 and 63 respectively;
their semantic meanings remain provisional. Across all 113 inputs, the candidate
directory endpoint, duplicate record counts and stored payload extents are
internally consistent. The parser enumerated 47,624 records, including each
archive's first self-named record; 47,511 remain when those are excluded.
The directories occupy 3,038,436 bytes. Payloads were not extracted or decoded.
The containers comprise three shared archives, 33 maps and 77 missions.

Directory names in `core.mw4` include 51 `.abl` and two `.abi` entries; those in
`props.mw4` include 132 `.script`, eight `.campaign`, nine `.h` and three `.hpp`
entries. This supports investigating a script/data layer alongside native code.
It does **not** establish that those payloads are source text, determine their
compiler/interpreter, or identify their compression codec.

`RESOURCE/Missions/coliseum.mw4` is **58,948 bytes**, with 28 directory records,
including 11 `.abl` names. It is a suitable first archive-directory fixture.
Its associated `.nfm` contains readable scenario metadata. A playable mission
will also require map, terrain, shared assets and executable logic; this small
archive has not been shown to be a standalone scene.

All 21 loose `.nfm` files contain include/macro syntax and scenario blocks, and
have matching archive/image files. The shipped server cycle selects
`Coliseum.nfm::Coliseum3`; the installed operator documentation specifies
configuration precedence from `Options.ini` through NFM to host UI settings.
No loose `Options.ini` was present. Preserve includes, macros, repeated keys,
case and scenario scoping in future parsing work.

Standalone media headers were checked without playback: four RIFF/AVI files
have `MSVC` video handlers; eleven MPG files have MPEG pack and sequence start
codes consistent with MPEG-1 syntax; one RIFF/WAVE has format tag 2, stereo
22,050 Hz and four bits/sample, consistent with Microsoft ADPCM. Twenty-one
TGA headers identify type-2, 112-by-112, 24-bit images. Decoder behavior and
archive-member media formats remain unvalidated.

## Evidence ledger and limits

Detailed evidence remains in ignored
[`reports/mw4-recon-2026-10-09/`](../../reports/mw4-recon-2026-10-09/).
Hashes were calculated independently with PowerShell and Python; the two
principal input hashes were rechecked after native analysis. REA sessions were
exported and closed, with neutral snapshots saved for evidence reuse.

| Finding | Retained evidence |
| --- | --- |
| Exact native-file identities and versions | `native-file-identities.json`; `mercs-exe-pe.json`; `mercs-icd-pe.json` |
| Section entropy, imports, auxiliary utility and DLL metadata | `native-static-audit.json` |
| Launcher inventory | REA `ev_8f132c790b5e386695800713f1f9df96aaf9a0f5eadf9bb07daa3dae24b4faf8` |
| Launcher protection markers | REA `ev_c18b3a9153423d9126a9528dde69fbb3038e90c1667bacffff25bea8b4cfaa7b` |
| Launcher entry and called launcher function | REA `ev_4b407e188ac5cdc32048fcd96e98699b6322387e72897c25bbcc0ec3cc5324ef`; `ev_3755ed812e646f727f379417e2dc123a31d2f22e0d950d444e13dce500abef85` |
| ICD inventory and internal/external split | REA `ev_726973ea77433be4fd065bc34c132cc0ed916b9d8b7118e6922c32459fd617bf`; `ev_3d970640923fe1085e1d9c68c8be059cbd3a26327d9e435946cc5a585d55acf4` |
| Implausible ICD entry decoding | REA `ev_58834f96bfe9102acc6fd6421febfd0b238269476d4ca4f100888e0eb7c64521` |
| Resource and interface candidates | REA `ev_c57c2ef5cdc3975f87cb511ac2e9eaf18503bfc0e6563a15e49e3bdf5d226858` |
| Installed-only asset inventory and archive checks | `asset-review/installed-files.json`; `asset-review/mw4-directory-observations.json`; `asset-review/acceptance-checks.json`; retained inventory/parser scripts |
| Media headers and installed-document observations | `asset-review/standalone-media-header-observations.json`; `asset-review/README.md` |

REA IDs above are stored in `rea-launcher-evidence.json` and
`rea-icd-evidence.json`. A provider-generated pseudocode result is analysis
evidence, not original source, an accepted ABI, or behavioral equivalence.

| Planning question | Status after this pass |
| --- | --- |
| Which MW4 title/build is installed? | Answered for this Mercenaries installation; other titles not admitted |
| Can the on-disk main code be lifted directly? | Negative for ordinary default analysis of these protected bytes; runtime-readable code remains unresolved |
| Are there useful accessible asset slices? | Answered for archive directories; payload decoding partially investigated |
| Can existing MW3 foundations be reused? | Answered at source/design level in the execution plan; MW4 execution unvalidated |
| Exact gameplay function boundaries, ABI and instruction coverage? | Unresolved pending a readable code image |
| Actual renderer, startup schedule, mission dependency closure and gameplay? | Unresolved; runtime observation and further static recovery required |

This assessment completes reconnaissance for planning, not reverse engineering
of the full game. It adds no MW3 milestone credit and no MW4 compatibility claim.
