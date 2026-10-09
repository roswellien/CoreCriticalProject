# Root review of the bounded mainargs prefix

This independent source model starts from pinned original FDIV BEFORE inputs,
decodes literal game/provider instructions, and compares the isolated native
startup chain through the actual `GetModuleFileNameA` import attempt. It does
not use native AFTER state as an expected seed or import the author's model.
The final [acceptance receipt](../../reports/m4-crt-mainargs/root-acceptance-r1/report.json)
passes; the [review note](../../docs/m4-crt-entry-mainargs-review.md) describes
the admitted boundary and remaining services.

The real route is game CALL `0x5AC468` → `__getmainargs` `0x7800BA5E` → ordinary
builder `0x7800BBBC` → CALL `0x7800BBD0`, provider IAT `0x7802E018`. The compiler
owns complete literal 66-byte and 140-byte bodies. Nineteen source PCs, sixteen
accesses and four typed routes execute before deterministic refusal of the
filename API. The raw IAT is `0x343B0`, return is `0x7800BBD6`, and actual
arguments are `[NULL,0x7803B3F0,260]`. API execution, argument/environment
outputs, provider RET, main-table callbacks and menus receive no credit.

The [root proof](../../reports/m4-crt-mainargs/root-model-r2/report.json) checks
48 positives and 120 causal cases, with 330 ordinary host pairs and 88,806
corruption denials. Causal source predictions cover 118 cases; the two inherited
mode43 mutations retain only their separately reviewed artifact contract.
State3504, FX512, all sixteen pages and 1,140 source identity bytes persist
without reseeding or remapping. The [source review](../../reports/m4-crt-mainargs/independent-contract-r4/report.json),
[root-model audit](../../reports/m4-crt-mainargs/independent-root-model-audit-r2/report.json),
[compiled review](../../reports/m4-crt-mainargs/independent-compiled-review-r1/report.json),
[observer controls](../../reports/m4-crt-mainargs/independent-compiled-observer-controls-r1/report.json)
and [data audit](../../reports/m4-crt-mainargs/independent-data-r2/report.json)
remain separate evidence. Independent compiled review adds 2,078 checks,
64 scenarios, 128 rich host pairs, 420 malformed-token denials and 548 observer
denials.

Run from `D:\Projects\MW34Recomp` with the pinned local Python runtime. Each
output must be a fresh immediate directory under `reports/m4-crt-mainargs`;
replace the example names with unused names. Preserve the accepted build and
earlier reports.

```powershell
& C:/Python314/python.exe tools/m4-crt-mainargs-root/run.py reports/m4-crt-mainargs/build-r2 reports/m4-crt-mainargs/root-execution-fresh
& C:/Python314/python.exe tools/m4-crt-mainargs-root/observe.py reports/m4-crt-mainargs/build-r2 reports/m4-crt-mainargs/root-execution-fresh reports/m4-crt-mainargs/root-model-fresh
& C:/Python314/python.exe tools/m4-crt-mainargs-root/accept.py reports/m4-crt-mainargs/root-acceptance-fresh
```

The seal rechecks its explicitly selected reviewed receipt set and physical
dependency hashes; a new replay directory is separate evidence until that
selection is reviewed. Source, object, compiler-read headers and SDK search
identities are bound, with no exhaustive SDK linker-file-open attestation.
The guest FP domain remains the inherited twelve masked empty-stack inputs;
rich caller FP/legacy metadata preservation and ABI XMM6–15 have separate
hardware evidence. No arbitrary guest trap or volatile SIMD equality is
assumed. The ordinary installed game need not be launched for this recipe.
M4 stays active at 27 of 144 selected roots, with 117 remaining.

Next work needs an explicit filename service/native-host module identity,
reviewed command-line producer carry in the existing mappings, then
locale/parser, allocator and environment contracts before the main table.
