# Command-line carry into native CRT startup

The bounded x64 startup chain now executes the original command-line writer
fragment, carries its owned guest pointer into the filename builder, and reaches
the real parser CALL. It stops before the parser body executes. This closes the
previous missing producer dependency at `0x7800BBD6`; it does not complete
argument initialization or M4.

The writer is eleven original bytes at `0x7800188C`: a CALL through the original
`GetCommandLineA` IAT followed by the MOV into `_acmdln` at `0x78037174`.
Its real zero-argument service continuation is `0x78001892`. The translated
fragment ends at `0x78001897`, before the next original instruction. There is
no original RET in this fragment.

An explicit late bootstrap seam runs this fragment after the preceding matherr,
control and first `_initterm` checks, inside the existing mainargs service
boundary. It overlays the carried State PC and uses the existing ESP
`0x20001860`. After the actual CALL and MOV, it restores only the saved PC and
transports the produced EAX into RuntimeCPU before the existing projection.
This is authored scheduling for a bounded experiment; original DllMain/process
attach ordering has not been recovered.

The actual native API supplies the research worker's ANSI command line. The
service checks its API identity and readable regions, measures a NUL within
131,072 bytes, and copies that complete input into a separately owned guest
allocation at `0x33000000`. It protects the allocation as read-only. The full
host pointer stays in uint64 receipt metadata. The sixteen existing mappings,
3504-byte State and distinct 512-byte FX image remain carried through startup.
The allocation is released by its owner after consumers and terminal retry
checks retire; preexisting mapping collisions are not owned by that scope.

The real builder then loads `_acmdln`, stores `_pgmptr`, compares the first
owned byte, executes five argument PUSHes, and performs CALL
`0x7800BBF7 -> 0x7800BC48`. The source-written return is `0x7800BBFC`, ESP is
`0x2000182C`, and arguments are `[0x33000000, 0, 0, 0x20001850, 0x2000184C]`.
No counts, parsed arguments, environment output or parser return are invented.

Completed validation:

| Gate | Result |
| --- | --- |
| Author native O0/O2 | 48 ordinary sequences and 24 required fault sequences passed |
| Fresh root native O0/O2 | The same declared 72 requests passed in separate processes |
| Independent original BEFORE/source oracle | All 48 ordinary sequences passed 118,807 checks |
| Shared semantic validator | 2,000 selected byte-corruption attempts were rejected |
| Independent source/build association | 12 prior guest objects and two FDIV libraries unchanged; two new writer objects bound to original bytes |
| Independent oracle audit | Full State, FX, sixteen pages, 1151 source bytes, owned bytes, source ledgers and normal metadata verified |
| Compiled hostile fixtures | 132 O0/O2 scenarios passed 4,878 assertions, including 42 token refusals |
| Direct hardware preservation | 264 rich caller pairs passed raw80, complete legacy metadata and FP/ENV checks |
| Independent hardware observer | 548 meaningful corruption attempts were rejected; all 131,728 physical bindings rehashed |

The root oracle derives the machine from original BEFORE captures and decoded
instructions. Measured native API inputs/results are declared service witnesses;
native AFTER State, CPU and pages are never used as expected-machine seeds.
The root models normal sequences and explicitly gives no full-machine-model
credit for the 24 standard causal sequences. Their additional lifecycle and
partial-effect proof belongs to the independent compiled review.

Actual worker command lines in this gate are nonempty. The empty-string fallback
is recovered in source and represented by the oracle, but receives no native
execution credit here. Other limits are original x86 API volatile equivalence,
guest TEB LastError initialization, allocation-generation identity and SDK
process-file-open attestation. Host LastError and the enclosing FP/ENV boundary
are checked separately.

Evidence:

- [Frozen preparation](../../reports/m4-crt-commandline-carry/preparation-r5/report.json)
- [Frozen x64 build](../../reports/m4-crt-commandline-carry/build-r6/build.json)
- [Root native execution and bundles](../../reports/m4-crt-commandline-carry/root-execution-r1/report.json)
- [Strengthened root source oracle](../../reports/m4-crt-commandline-carry/root-observer-r2/report.json)
- [Independent source and ABI association](../../reports/m4-crt-commandline-carry/source-contract-r2/report.json)
- [Independent root oracle audit](../../reports/m4-crt-commandline-carry/independent-root-model-audit-r1/report.json)
- [Independent compiled review](../../reports/m4-crt-commandline-carry/independent-compiled-review-r1/report.json)
- [Independent hardware observer](../../reports/m4-crt-commandline-carry/independent-compiled-observer-r1/report.json)
- [Root acceptance and current dependency closure](../../reports/m4-crt-commandline-carry/root-acceptance-r1/report.json)

Earlier failed builds and the narrower first root observer remain preserved.
That observer's exact source snapshot is retained; the strengthened second
observer closes filename job/reason and command-line reason metadata using the
same native captures. Final acceptance uses the complete current dependency
union, without expanding stale historical source bindings.

The three superseded independent fixture builds also remain preserved: the first
failed compilation after selecting the wrong registry include; the second exposed
an overly strict reviewer comparison of changing native heap-region extents;
the third exposed a recursive reviewer checkpoint. These were fixture or review
issues, and the frozen candidate was unchanged. The fourth fixture build passed.

The [static locale/parser workahead](../../tools/m4-crt-locale-workahead/README.md)
identifies the next bounded gate: run the real parser prefix on the current frame,
then stop before its first locale-table read at `0x7800BCE6` for the measured
command line beginning with `D`. Completing the sizing pass requires initialized
lead-byte classification. The original default initialization path first needs
CRT locks and allocation; zero source-file table bytes do not prove initialization.
After sizing, allocation, output parsing and environment ownership remain. The
selected initializer count remains 27 of 144.
