# Remote Op1M1 texture-loading fault after content compatibility migration

`MW3-Playtest-20261023-053322.zip` identifies launcher 1.0.26 and the selected
`mw3-content-capabilities-20261023-r1` runtime. All 464 enabled content files
pass the existing unchanged-file verification receipts; both model packs,
38 texture banks, HUD/menu and music are selected. Native execution reaches
c1m1 and faults at `7800160e` with destination zero before any geometry submission.
This is distinct from the earlier launcher HUD admission failure.

The return chain again includes the texture loader's palette fread return
`517ea7`, through `517fbc`, `518e16` and the archive lookup. The report contains
no unsigned replacement seek messages. The absence does not establish why
the seek adapter was not triggered, nor which texture or bank was being read.
Do not claim a missing update or stale executable: the report identifies the
correct successor runtime.

Read-only inspection of the corresponding local installed environment banks
finds zero palette and stretch fields throughout their record descriptors.
Those metadata checks do not rehash the entire pack payload, reproduce the
remote failure, or prove that the in-memory descriptor is correct. A bad file
position or descriptor corruption remains possible; heap exhaustion has not
been established by the remote report. With only Shared Original Mech
Textures disabled, the owner reports reaching Launch Mission and crashing
immediately after clicking it. No report from that selection has been read yet;
do not assume the same fault address or that this excludes a second crash.

## Added evidence

The derived diagnostic host preserves the same original translated module,
renderer, resources, game bodies and existing seek-repair behavior. It records
the eight most recent actual SetFilePointer attempts and the most recent guest
heap failure. Logging happens only on an existing SEH fault when MW34_SEH_LOG
is enabled. No API result, allocation, seek or game behavior is replaced.

The fault report includes heap live/free/high-water accounting, failed size,
actual fread arguments, the recovered texture descriptor's scalar fields,
CRT FILE metadata and the matched archive-table entry name/offset. It never
exports texture pixels, original files, saves or arbitrary memory dumps.
Each guest memory read is bounded and gated by the exact recovered return
sites; unreadable metadata leaves the original fault intact.

Original binary inspection establishes these stack contracts:

- MSVCRT fread at `78022459` pushes EBP then ESI. The saved ESI at the caller's
  return slot minus eight is the live texture descriptor for the three
  texture fread sites (`517e2d`, `517e5d`, `517ea7`). Arguments follow the
  return slot in the original cdecl order.
- Texture lookup calls `517f80` with return `518e16`. Its first push saves
  the caller's ESI, the matched 40-byte archive-table record, at slot minus four.
- The known null destination occurs after palette malloc; the existing report
  does not contain the allocation size or that record, so it cannot distinguish
  a negative/corrupt palette count from another allocation failure.

The authored helper fixtures pass 21 checks for valid frames, exact call sites,
unreadable/boundary rejection and bounded seek history. Reapplying the source
adapter rejects before changing the staged source. The maintained adapter is
`tools/remaster-launcher/apply_texture_read_diagnostics.py`; its helper and
asset-free C++ fixture are beside the other launcher native tools. Complete
REA evidence, source/build records and the supplied report remain private under
`D:/MW3Op1M1Diagnostics-20261023-r1`.

This is diagnostic work, not a confirmed crash fix or native gameplay credit.
Formal acceptance remains 131/144. Nothing is committed.

## Withdrawn r1 diagnostic delivery (historical)

The signed diagnostic host is
`125abad661f9bff66be8c48654e673072faffd1ec636b64cee6b27f5e4a0d73d`.
The translated module remains byte-identical to its signed predecessor.
The complete staged runtime validates. Its exact signed update verifies the
original executable, copies 652 runtime files, activates, validates and rolls
back successfully in an isolated installed baseline. No local c1m1 reproduction
or game completion is claimed. Earlier local live-menu tests do not prove this
remote crash repaired.

[MW3 Op1M1 diagnostic update](https://playtest.corecritical.dev/updates/mw3-op1m1-diagnostics-20261023-r1/MW3Op1M1Diagnostics.zip)
is listed under Setup on both protected download catalogs. It requires launcher
1.0.26, uses sequence 2026102304, and includes the current resource-capability
coordinator and prior performance changes. No launcher reinstall or content
repackaging is required. New runtime capabilities retain the existing reader
versions; the new executable needs no per-pack hash admission.

The wrapper is 35,581,506 bytes, SHA-256
`a2a034667177107b32d38b8ceb0be50773f7b0c9b86abb8ae2d35d4a2b8c4cb5`.
Full remote wrapper, signed metadata and payload readbacks match local bytes.
Native signing is timestamped and verifies successfully. Existing stable
installer, content/texture packs and performance download links are retained.
After import, retry the failing pack selection and export the fresh report.
The remote diagnostic result remains pending. Keep the shared texture pack
disabled for that next report, matching the owner's latest isolation attempt.

## Corrected r2 delivery and hardware evidence

The October 23 06:58:09 remote report never starts the diagnostic host:
Windows rejects it with error 193, “not a valid Win32 application.” Local
Windows process creation reproduces the failure. The r1 host was accidentally
linked with Microsoft link.exe and a LIBRARY export definition, setting the
PE DLL characteristic (0x2022) despite its EXE filename. Its valid Authenticode
signature and previous install/activation checks did not establish executable
process startup. This is our packaging regression, separate from the original
Op1M1 texture-read crash. Both catalog links to r1 were withdrawn.

R2 uses the baseline LLVM lld-link executable linker. The final signed host is
`70b15dd5630861e8810ff99cc9f2e05ff8811f9769381849e9a0fe589e6d8097`.
Actual Windows process creation succeeds before signing, after signing, and
from the exact host installed through the signed update. Those bounded checks
reach the normal argument guard with expected exit 1; they do not establish
menu or mission success. Source, logs and receipts remain private under
`D:/MW3Op1M1Diagnostics-20261023-r2`.

The launcher now rejects native DLLs masquerading as executables during
runtime validation and before launch. Fixtures cover a real authored EXE,
a DLL-characteristic mutation and malformed bytes. The complete launcher check
suite passes. The r2 signed update verifies originals, installs 652 runtime
files, activates, validates and rolls back in an isolated baseline.

The remote reports identify AMD Radeon 760M, 64-bit Windows build 26200 and
.NET 8, but lack CPU and physical RAM. They do not establish a hardware cause.
R2 logs CPU brand/logical processors, total/available physical RAM and memory
load at startup, plus Vulkan vendor/device/driver/API and device-local heap
size on graphics initialization. Device-local heap is not labeled dedicated
VRAM because integrated GPUs may share system memory. No hardware minimum or
remote gameplay claim is inferred from the development PC.

[Corrected diagnostic r2](https://playtest.corecritical.dev/updates/mw3-op1m1-diagnostics-20261023-r2/MW3Op1M1Diagnostics.zip)
uses sequence 2026102305 and requires launcher 1.0.26. It is under Setup in
both protected catalogs. Full wrapper, payload and signed metadata remote
readbacks match local bytes. Wrapper SHA-256:
`a5becf323396f9ebecf3ea48efd75f87600ac693ff41d6fd17cfad775be416af`.
No reinstall is required. Leave Shared Original Mech Textures disabled for the
next comparison, retry Op1M1, and export the report. The original mission
crash is still unresolved. Acceptance remains 131/144; nothing is committed.
