# M4 progress: functional native allocation and direct captures

The current native batch executes the recovered mode-1 `malloc` and `free` paths, uses the allocated memory, and returns through `free(NULL)`. It carries the real heap established by the earlier initializer through its genuine return and the original caller's return-value test and stack cleanup. The allocator tests then enter through explicit external cdecl research callers.

This removes the usable-allocation prerequisite for the blocked locale lock path. The next functional batch is critical-section creation and default locale/lead-byte initialization, followed by full parser sizing, argument output and environment ownership. A complete native game window and menu remain M4 objectives; native Training remains M5.

## What now works

- Actual Windows `HeapAlloc` supplies privately owned full-width native memory on the initialized heap. The guest receives a checked address at `0x31000000`; the original runtime's reserved `0x30000000` page remains intact.
- Requests of 0, 1, 24, 31, 32 and 4096 bytes follow the recovered size normalization and rounding. A client writes and verifies a declared byte pattern through the guest/native memory bridge.
- The recovered non-NULL free path invokes actual `HeapFree` on that same allocation. The NULL path returns without a second free call. Normal FS exception-chain installation and removal are checked; heap destruction follows allocation release.
- Invalid ownership, stale authority, invalid memory permissions, modified imports, partial effects and observer failures are tested. Source frees and diagnostic cleanup frees have separate evidence and counters.

Thirteen literal translated bodies add **26 x64 object files** across O0 and O2. They cover eight unique source spans totaling **469 bytes**, with five overlapping entries adding 63 bytes of compiled overlap. All 38 earlier guest object files and both FDIV libraries are reused unchanged.

## Verification

The coordinator's [native execution](../reports/m4-crt-allocation-root/execution-r6/report.json) passed 12 successful sequences and 24 directed failure sequences at O0 and O2. Across those 36 cases, actual API witnesses record 32 allocations, 18 source frees and 14 cleanup frees. These counts include failure controls; each successful sequence uses exactly one source allocation and one source free, with no cleanup free.

The independent [original-source observer](../reports/m4-crt-allocation-model-review/observe-r3/report.json) passed **828 complete machine checkpoints**, 69 for each successful sequence. Expected state comes from original BEFORE inputs and recovered instruction semantics. It checks State, floating-point state, runtime CPU, all 21 captured baseline pages, and the actual allocation page while mapped. It independently verifies the Windows export forwarding chain and the source/API/access ledgers.

The independent [compiled review](../reports/m4-crt-allocation-review/check-r3/report.json) passed another **48 native cases**: 24 successful sequences and 24 independently designed controls. Its checks include 96 caller hardware-state pairs, allocation/import/source mutations, memory permissions, 48 read-only alias checks and two wrong-thread denials. It checks 1,008 full machine milestones and preserves the reserved runtime heap page. The [final current-dependency acceptance](../reports/m4-crt-allocation-root/acceptance-r1/report.json) ties the exact builds, native commands, stage outputs, archives and independent reviews together.

The original provider and game are not launched by these research workers. Other allocator modes, exception-handler dispatch, original attach ordering and full CRT initialization remain outside this completed test domain.

## Efficiency changes actually used

All new main native captures are written directly into compact strict archives. The coordinator run contains **175,900 logical records** in two archives and two manifests, with **zero per-record physical files** and **zero later copy or pack passes**. The existing strict reader, hashes, logical-name rules and archive limits remain unchanged.

| Measured stage | Seconds |
| --- | ---: |
| O0 native execution plus direct emission/finalization | 3.08 |
| O2 native execution plus direct emission/finalization | 1.88 |
| O0 strict capture verification and row review | 2.14 |
| O2 strict capture verification and row review | 2.17 |
| Coordinator run including current dependency verification | 11.42 |
| Independent source observation | 7.86 |
| Independent compiled native run and strict verification | 8.77 |
| Independent raw-result review | 5.25 |

These are execution costs after implementation and compilation, not total development time. A separate [same-input transport experiment](../reports/m4-capture-direct-root/review-r1/report.json) measured about **15 times faster** emission, finalization and verification for 2,945 representative records. That local workload ratio is not a whole-project speedup estimate. The final checked writer also passed [strict compatibility](../reports/m4-capture-direct-root/current-r1/report.json) and [failure/host-state controls](../reports/m4-capture-direct/sealed-r2/report.json).

The [revised execution plan](m4-execution-plan-r2.md) now governs functional batches, concurrent independent work, reuse of unchanged objects, targeted checks and separate timing of native execution and evidence handling. The selected initializer inventory remains **27 of 144**: this batch advances the CRT dependency frontier and does not add game initializer roots. That inventory is a coverage measure, not an overall completion percentage.
