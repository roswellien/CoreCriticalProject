# M4 analysis tooling and batch execution

Updated 2026-10-09. This supplements [execution plan r3](m4-execution-plan-r3.md) with the measured [REA/Ghidra evaluation](m4-tooling-evaluation.md). The [connected54 unit is now accepted](m4-progress-startup54.md); prior evidence remains preserved. Static analysis adds no initializer credit.

## Analysis lane

Use one persistent Ghidra project for each exact admitted artifact version. Verify its original SHA before import and before reuse. For MW3, seed function entries from the actual 145-word initializer table and refuse conflicting bodies rather than deleting existing analysis. Keep created entries distinct from byte-checked exported bodies and runtime acceptance.

Use REA for focused questions about already recognized EXE functions, structured dossiers, instruction details and bounded value-flow traces. Keep the target open across related requests and export the complete evidence before closing it. Its neutral snapshot did not avoid cold initialization in the measured test. Use direct headless Ghidra for the staged CRT DLLs and for persistent table-seeded analysis; keep its inferred names/types separate from admitted ABI and provider facts.

Before implementing the next whole family, export only its changed roots and unresolved dependencies: original instruction ranges and bytes, direct calls, indirect-call sites, data references, inferred object fields, and pseudocode. Record uncertainty about ECX arguments, stack cleanup, x87 effects and function boundaries explicitly. Reuse these exports across agents instead of importing the same binary in each lane. Resolve a specific gap before requesting broader analysis.

## Concurrent work

Keep three independent lanes: implementation/native integration, original behavior and contract preparation, and independent review of boundaries/ownership. The coordinator integrates and validates the changed functional batch. Static Ghidra requests share one Program and do not gain proportional throughput from extra agents; parallelize engineering from frozen exports. Schedule heavy original captures and provider analysis so they do not compete unnecessarily.

Remill/LLVM remains the executable translation path. Use Ghidra to shorten investigation and expose missed dependencies or field extents. Check recovered interfaces against assembly and original execution before compiling them into host boundaries. Preserve the existing meaningful ABI, x87/status, committed-write, relocation and cleanup checks. Run changed-batch validation and reuse unchanged accepted objects and receipts by identity.

## Immediate execution order

The 26-root callback-registration batch completed with connected28 as the accepted 54-root sequence. Physical `_body` symbols, the shared lower continuation, the measured zero-FSQRT repair, current original input pages, typed provider ownership and independent fault controls are covered by its acceptance receipts.

Proceed with the [17-root duplicated-string family](m4-next-string-batch.md), targeting 71/144 after acceptance. Reuse the live allocation/registration components and persistent game/CRT projects, export only the changed constructor inputs and three string bodies, and keep implementation, original behavior and independent review concurrent. The 32-root MFC allocation family follows, subject to its additional provider and handler ownership. Environment/mainargs completion and original startup scheduling remain necessary for native menus. Table entry count is a planning inventory, not a recompilation percentage.

## Efficiency measurements

For each changed family, record elapsed time for static recovery/contract preparation, implementation/build, original/native comparison, fault controls and integration. Also record cold imports, repeated analyses, manual interventions, failed builds, existing components reused and newly accepted roots. Compare accepted roots per active engineering hour and total time to an accepted family against the previous workflow. Warm decompiler latency alone cannot establish the overall speedup.

For the accepted54 version, both native builds took 19.42 seconds and actual native execution took 39.65 seconds combined. The final independent compiled controls ran in 64.17 seconds combined. These measure automated stages; investigation and comparison time are additional. Each optimization level reused 187 physical COFF objects. The capture audit also identified repeated provider snapshots as a remaining overhead: each native archive contains 1.217 GB, including repeated selected/grown/cleaned ledgers. A future transport revision should emit immutable shared records once with checked references while retaining full observations and comparisons; it must not omit evidence or rewrite the accepted captures.
