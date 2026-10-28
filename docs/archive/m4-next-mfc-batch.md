# MFC allocation family accepted

Updated 2026-10-09. The complete 32-root family is accepted, advancing coverage from **71/144 to 103/144**. The [progress record](m4-progress-startup103.md) and [34-gate acceptance receipt](../../reports/m4-joint-startup103-root/acceptance-r1/report.json) contain final evidence. **41 roots remain**; [plan r6](m4-execution-plan-r6.md) targets shared normal FS support next.

Current checkpoint: [109/144 is now accepted](m4-progress-startup109.md), including six normal FS constructors. **35 roots remain**, and [plan r7](m4-execution-plan-r7.md) targets the next seven container/string roots. The details below retain the historical 103-root batch scope.

## Prerequisites established

The [genuine 32-bit loader probe](../../reports/m4-mfc-source/loader-identity-r1/report.json) loads the exact staged MFC42 and MSVCRT DLLs at their expected bases. It verifies the owning module paths, hashes, export identities and loaded code bytes. MFC's malloc/free imports resolve to the exact staged CRT exports rather than the stale bound pointers in the original file. The handler value remains `FFFFFFFF` after DLL initialization. This probe executes module initialization; it does not execute the constructors, allocator or free bodies.

The [focused Ghidra exports](../../reports/m4-mfc-ghidra/export-r1/report.json) verify 67 existing game entries and the two MFC provider entries against original PE bytes. The warm game pass took 12.06 seconds. The first MFC import took 70.07 seconds and its project is now saved for reuse. Literal source recovery remains primary for shared tails and exact CALL/RET behavior.

The [MFC literal lifts](../../reports/m4-mfc-native/lifts-r1/report.json) and [physical symbol audit](../../reports/m4-mfc-native/symbol-attribution-r1/report.json) compile the positive allocator path and matching free wrapper at O0/O2. The allocation-null branch enters unresolved handler/TLS code and requires its own support before admission.

## Current implementation requirements

The [BEFORE-derived allocation contracts](../../reports/m4-mfc-source/allocation-contracts-r4/report.json) establish 35 positive allocator calls across the 32 roots. Three roots each allocate twice. Request sizes range from 12 to 128 bytes and publication fields differ by constructor. The native ledger supports 52 live owners: 35 new objects, 16 existing strings and the callback vector.

Keep prior string and registration owners alive alongside the new container storage. Extend exact MFC image/page ownership, source import relocation checks, allocation/copy witnesses and literal free cleanup without changing accepted71 sources or objects. Two additional lower game tails require separate literal entry bodies to preserve every original byte in the executable closure.

The [connected103 build](../../reports/m4-joint-startup103/build-r1/build.json) reused parent inputs and added 65 game bodies plus two MFC bodies per level. The [final link audit](../../reports/m4-mfc-control-audit/link-scope-r2/report.json) corrects the declared count: 296 retained dependencies comprise 295 linked source COFFs and one unused historical FDIV proof archive. The [native execution](../../reports/m4-joint-startup103-root/execution-r1/report.json) completed six persistent 103-root sequences at each level: 1,236 initializer calls, genuine growth and full cleanup. Actual worker time was 106.90 seconds at O0 and 70.61 seconds at O2. Each native archive contains 1,931,112 logical records and 7.402 GB of payload.

The [original x86 reference](../../reports/m4-mfc-source/original-run-r3/report.json) completed six sequences and 618 initializer calls over 35 complete pages. The [original source model](../../reports/m4-mfc-source/original-game-source-r1/report.json) checked 450 constructor prefixes, 210 actual MFC allocations and 15,300 entire nonstack-page observations. Actual HeapAlloc backing is captured before guest constructor writes, including untouched bytes.

The original process independently authenticates all 511 loader-resolved import slots on the observed MFC page, including declared and forwarded export ownership. Every other byte remains checked; no whole page is masked. Persistent native source, paired original/native, independent provider and 84 functional control attempts passed. Stored callbacks and native menus remain outside this batch.

## Capture efficiency

The [retained capture evaluation](../../reports/m4-capture-sharing-evaluation/evaluation-r1/report.json) authenticated the accepted71 archives and measured approximately 96.94–96.96% repeated payload. Whole-payload SHA/size identities account for only 82.8–83.2 MB of unique content per optimization level, compared with 2.719 GB currently stored. Index and reference overhead would be additional; this is a payload estimate, not an observed runtime speedup.

The current strict reader requires contiguous payloads and cannot silently accept shared offsets. This batch retains the validated canonical transport. A future additive shared-record format must preserve all logical records, full bytes, owner identities, authentication and failure evidence, and pass independent reader/writer and corruption tests before adoption.
