# Accepted native startup sequence: 71 selected roots

Updated 2026-10-09. Selected initializer coverage increased from **54/144 to 71/144**, adding all 17 roots in the duplicated-string family. **73 inventory roots remain.** The 49.3% figure describes this initializer inventory; native menus and Training remain open.

The [acceptance receipt](../../reports/m4-joint-startup71-root/acceptance-r1/report.json), SHA `64c010e01930d4f84d7df9cb8cd932669ce25b6f3f1dc21989f197282025fdfc`, combines 21 passed gates and authenticates 5,322 physical dependencies. It extends the [accepted54 sequence](m4-progress-startup54.md). Earlier sources, captures, failed experiments and acceptance receipts remain preserved.

## Behavior established

The selected roots execute in their original relative initializer-table order, carrying the machine state, pages, heap and critical-section owners from one source-derived bootstrap. The complete sequence registers 43 cleanup callbacks and constructs 16 genuinely allocated duplicate strings. Root `4E6A10`, the seventeenth new root, reads a null descriptor and takes the original branch that skips duplication; it still registers its callback.

The compiled native code executes the literal CRT `_strdup`, `strlen` and `strcpy` instruction bodies. Their source models account for aligned DWORD reads beyond the terminating NUL, individual copy stores, CALL/RET frames, and the exact allocated bytes. Host string-library substitutions are not used. Every duplicate stays owned through the selected sequence.

After initialization, two additional genuine registration calls per native sequence trigger another measured heap growth; these research replays earn no initializer credit. Cleanup source-frees all 16 duplicates and the callback vector, deletes four critical sections, and successfully destroys the matching heap. The current worker observes the import identity immediately after HeapDestroy, closing the previous worker's observation gap.

## Validation

| Gate | Verified extent |
| --- | --- |
| Actual original x86 reference | Six persistent 71-root sequences, 426 root executions, 32 observed pages |
| Original constructor source model | 258 constructor prefixes, 96 actual string flows, six null-descriptor branches |
| Native O0/O2 and persistent source model | 12 sequences, 852 root executions, 54,528 whole-page BEFORE/AFTER checks |
| Paired original/native relation | 52,824 whole nonstack-page relations, 192 owned-string relations, exact ordered callbacks and null branches |
| Independent provider model | 8,688 full machine checkpoints, 442,008 whole-page checks, 192 string allocations, 204 source frees, 48 actual growth operations and 12 complete heap lifecycles |
| Compiled controls and independent audits | 56 attempts across 14 scenarios at O0/O2, 26 controlled refusals, 28 refused retries, two exact four-byte partial-copy prefixes, 56 hardware-preservation pairs and 28 post-destroy identity triplets |

The models start from a true bootstrap BEFORE and do not seed machine state from candidate AFTER observations or reset it between roots. Actual allocated guest/native ownership and complete retained bytes back the string relations. A separate physical-symbol audit verifies all 39 newly compiled game bodies and three CRT bodies at both optimization levels.

The controls cover changed arguments and string inputs, read/write permissions, committed partial copies, native-owned byte corruption, observer exceptions, and import identity. Independent review caught an earlier import fixture failing on its own protected write. The corrected test makes its setup change before phase 20 and reaches the actual source import check at `48EB22` / `5BB670`; both native builds refuse there. Deliberate observer exceptions are recorded separately from guest memory faults. The [final controls](../../reports/m4-strings-review/controls-r4/report.json), [independent control audit](../../reports/m4-strings-control-audit/final-seal-r1/report.json), and [literal causality audit](../../reports/m4-strings-source/control-causality-r3/report.json) replace that earlier interpretation.

## Explicit boundaries

The paired relation projects five exact owning import DWORDs and the 16 source-derived duplicate-pointer fields only after their constructors. The inherited `6099E8` byte relation and finite floating-point policies retain their previous bounded contracts. Every differing byte is retained; no whole page is masked. Native provider stack behavior is independently source-checked; equality with the original provider's scratch stack is outside the cross-branch relation.

Stored callbacks are not executed. Broader allocation-failure/null-`strdup` paths, TLS and handler branches, full CRT attach, environment/mainargs, original startup scheduling, whole-game pointer liveness, native windows/menus and native Training remain open. Earlier live helper/numeric Training tests are separate from this standalone startup research.

## Execution efficiency and next batch

Warm game/CRT Ghidra exports took 21.13 seconds. Both native builds took 19.33 seconds, actual native execution took 76.00 seconds combined, and the final corrected controls took 51.10 seconds combined. Each native level reused 187 accepted COFF objects and added 42, for 229 total. These are automated stage timings; investigation, source comparisons and audits are additional.

Repeated provider observations still dominate capture volume: each native archive contains 2.719 GB of payload. The [updated execution plan](m4-execution-plan-r5.md) retains all proofs and proposes immutable shared records with authenticated references for future transport work.

The next counted family is **32 MFC allocation roots**, targeting **103/144** after its own acceptance. The [static lookahead](../../reports/m4-strings-native/next-mfc-r1/report.json) and [independent import-linkage receipt](../../reports/m4-strings-native/next-mfc-linkage-r1/report.json) identify stale bound allocator pointers. Genuine loader-resolved allocator/free identities must be established before executing that provider path.
