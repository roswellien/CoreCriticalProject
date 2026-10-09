# First native startup initializer

Accepted 2026-10-07 as one prerequisite for [M4](m4-startup-plan.md).
The complete original initializer at `0x410910`, including its tail body at
`0x410920`, now has a statically compiled native x64 translation. **5,320
original cases and 10,640 native O0/O2 comparisons pass with zero defined
differences.** Full native startup and menus remain open.

The actual CRT table slot at `0x5E0058` points to this wrapper. It clears one
byte in each of 167 records, with a 20-byte stride, and returns. Both complete
functions were lifted from the hash-admitted executable. The combined lift
contains eight reachable original instructions and eleven unreachable padding
bytes. No outgoing game function or imported service is required by this body.
The [contract](m4-initializer-contract.md) defines its exact admitted domain.

## Measurement and review

The [fresh build](../reports/m4-initializer/stage-safe/build.json)
binds 48 source files, 25 tools and 69 artifacts. The unchanged guest IR is
compiled at O0 and O2, with no semantic repair or fast-math. Native bridge
accesses use checked 32-bit guest addresses; execution enters the compiled
translation, with no interpreter or expected-value execution.

The [final comparison](../reports/m4-initializer/stage-safe-normal-windows/report.json)
has SHA-256
`5aaa1d32b961aed010d5de85388e976ff2674df12428f8faefcaba2fd04fd135`.
Its 5,320 inputs cover 128 entry-flag combinations, 4,096 TOP/tag/storage cases,
72 control-word/direction-flag cases and 1,024 register/padding seeds. Actual
CPU and return state, all 8,192 mapped stack/data bytes, admitted floating-point
and vector state, and protected native State storage match. Final DEC's AF is
defined and compared; no arithmetic exit flag is excluded.

Every native case observes 167 ordered byte writes followed by the return-frame
dword read. Original per-access events and Remill State are explicitly
unobserved zero fields. The original worker executes the admitted wrapper/body
offline in an isolated 32-bit process. These are directed original-operation
records with authored input perturbations, rather than an in-game startup trace.

All 126 saved-record observer corruptions reject. All 66 actual invalid worker
requests reach their intended diagnostic, return failure and publish no result.
Compiled checks exercise protocol/admission, context bounds, protected State
storage and actual host floating-point restoration on normal and checked-fault
paths. Each worker passes 32 protocol checks, including two SHA known answers;
the native workers additionally pass 16 context, 288 storage and 24 host-state
checks each. Four public CLI checks per worker also pass; one repeats the
protocol check, so these counts are not disjoint. Three separate actual-worker
staging controls preserve pre-existing ordinary sentinel files; four real
PowerShell recipe controls preserve partial report/build directories unchanged.

The [independent raw review](../reports/m4-initializer/independent-review/stage-safe-raw-review.json)
reconstructs all 15,960 actual records without importing the implementation's
corpus or comparator. It independently audits the complete instructions, nine
reachable IR blocks, 34 LLVM structure layouts, all 3,504 native State bytes,
actual object imports and all 66 causal diagnostics. A separate
[root oracle](../reports/m4-startup/root-review/initializer-oracle-stage-safe.json) also
reconstructs CPU, complete pages and ordered events with zero differences.
The [superseding final review](../reports/m4-initializer/independent-review/stage-safe-final-review.json)
accepts this exact fresh gate, fully rechecks both preservation maps and
independently verifies the filesystem controls within their stated scope.

## Preserved attempts and repair

The first sandbox comparison passed the positive records but failed one
invalid-input check before reaching its intended rejection: the required
original guest reservation was unavailable. That attempt remains a failure.
An unchanged-worker comparison in normal Windows subsequently passed the
precise causal checks.

Before acceptance, review found that the new harness freed a caller-owned
SHA hash buffer before destroying its handle. The old sources, builds,
streams and failed controls were preserved in the
[pre-repair manifest](../reports/m4-initializer/pre-hash-lifetime-repair/manifest.json).
The new helper uses provider-owned storage, releases the hash handle before
the provider, and adds empty/ABC known-answer checks. Microsoft's
[CNG contract](https://learn.microsoft.com/en-us/windows/win32/api/bcrypt/nf-bcrypt-bcryptcreatehash)
defines that lifetime requirement and allocation option.

Further review found that the original worker's rejection of an existing stage
could delete that file, and that the recipe could overwrite a partial prior
output. The next complete source/build/record baseline was preserved in a
[separate manifest](../reports/m4-initializer/pre-staging-ownership-repair/manifest.json)
before the new shared ownership check and early directory guards were changed.
The new controls invoke those actual paths and verify unchanged complete
sentinel bytes and directory inventories.

A fresh build and complete normal-Windows comparison passed after both host
harness repairs. All three result streams remain byte-identical to the earlier
positive measurements. Original initializer instructions, guest IR and native
translated objects did not change; host IR differs only in output-path comments.
Earlier M1–M3 sources and evidence remain preserved.

## Reproduction and limits

From normal Windows PowerShell, use two fresh output directories and the
accepted local LLVM/Remill/Visual Studio toolchain plus admitted user image:

```powershell
Set-Location D:/Projects/MW34Recomp
powershell.exe -NoProfile -ExecutionPolicy Bypass -File tools/m4-initializer/build_slice.ps1 `
  -OutputDirectory D:/Projects/MW34Recomp/reports/m4-initializer/replay-FRESH
C:/Python314/python.exe tools/m4-initializer/compare.py `
  --build D:/Projects/MW34Recomp/reports/m4-initializer/replay-FRESH/build.json `
  --out D:/Projects/MW34Recomp/reports/m4-initializer/replay-FRESH-normal-windows
```

Existing report directories and all three derived build directories reject
before extraction or compilation. The recipe requires the durable M3 pins;
it keeps original bytes, lifted IR, full records and binaries in ignored local
directories. Restricted-process guest-address conflicts are genuine failed
attempts and cannot satisfy a causal rejection check.

The tested floating-point domain includes twelve masked control words, all
TOP/occupancy combinations and admitted raw storage. Guest FOP/FIP/FDP must
be zero and their actual captures are compared exactly. Nonzero guest metadata,
unmasked traps, arbitrary generated-frame exception unwinding and high 64-bit
host instruction/data pointers remain excluded. Full transitive Windows SDK
headers/import libraries are not independently pinned. Publication is scoped
to sequential offline workers and fresh private ordinary directories. Concurrent
staging writers, reparse points/dangling links and atomic file ownership are
outside this gate; broader publication needs an exclusive handle-based design.

Only one of 144 nonzero CRT initializer roots is accepted here. The adjacent
initializer at `0x410940` and its two callees now have a
[complete static recovery](../reports/m4-startup/next-initializer-410940/report.json):
no outgoing unresolved call or FP instruction was found, and it writes 66
bytes in a separate part of the same global page. It is the next connected
startup-data candidate; translation and execution admission remain open.
The complete application constructor, callback at
`0x480000`, CRT/SEH/MFC environment, required services and frame/menu/input paths
still need recovery, implementation and original/native comparisons. No new
game launch is needed to use this result.
