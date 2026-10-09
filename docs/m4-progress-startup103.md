# Accepted native startup sequence: 103 selected roots

Updated 2026-10-09. Coverage increased from **71/144 to 103/144**, adding the complete 32-root MFC allocation family. **41 inventory roots remain.** The 71.5% figure measures the selected initializer inventory; native menus and Training remain open.

The [acceptance receipt](../reports/m4-joint-startup103-root/acceptance-r1/report.json), SHA `13cc2567f30f2dae2d12991a3a76aa6c953c70a49148dc4ed13df34837b14c7c`, combines **34 passed gates**. A final conflict-normalized check rehashed all **7,192 physical dependencies**, without a metadata-only cache. It extends [accepted71](m4-progress-startup71.md); earlier captures, failed attempts and receipts remain preserved.

## Behavior established

The roots execute in their original relative table order, carrying complete machine state, pages and actual owners from one bootstrap. The sequence registers 75 cleanup callbacks and retains 35 MFC allocations, 16 duplicated strings and the callback-vector owner. Three new roots allocate twice; requests range from 12 to 128 bytes.

The native code executes the literal positive MFC allocator and matching free wrapper through their exact named CRT dependencies. A genuine 32-bit loader establishes the loaded import identities; stale raw bound addresses remain provenance and are not executed. Source CALL/RET frames, initialized object nodes, self-links, pointer publications and saved stack-byte headers are checked against the recovered instructions.

Additional source-driven registration calls exercise real growth without earning root credit. Cleanup source-frees all 35 MFC allocations, 16 strings and the vector, deletes four critical sections and destroys the matching heap. The native provider proof verifies 624 source frees, 144 successful growth operations and 12 heap lifecycles across the two build modes.

## Validation

| Gate | Verified extent |
| --- | --- |
| Actual original x86 reference | Six persistent sequences, 618 root calls, 35 observed pages |
| Original constructor model | 450 constructor prefixes, 210 actual MFC allocation flows, 96 string flows and 15,300 whole nonstack-page checks |
| Actual native O0/O2 and persistent source model | 12 sequences, 1,236 root calls, 86,520 whole-page BEFORE/AFTER checks, complete State/CPU/FX/environment |
| Original/native comparison | 84,048 whole nonstack-page relations, 420 complete MFC owner relations, 48 vector-endpoint relations and 864 saved-byte derivations |
| Independent provider model | 17,652 complete machine checkpoints, 1,274,988 whole-page checks and full allocation/growth/cleanup ownership |
| Compiled controls and independent audit | 84 attempts, 40 actual refusals, 42 unchanged retries, six exact partial-write prefixes, 84 hardware comparisons and 42 HeapDestroy identity triplets |

The models do not reset machine state between phases or seed it from candidate AFTER observations. Each branch's actual allocation backing is captured before constructor writes. Source writes predict initialized bytes and self-links; untouched padding retains each branch's own original backing.

The paired comparison permits only authenticated differences: six exact game import DWORDs, 511 independently authenticated MFC import DWORDs, 39 MFC pointer fields, 16 string fields, 36 source-derived byte headers and the inherited bounded numeric/byte relations. Four MFC fields are genuine one-past-end vector pointers. Raw differing bytes are retained; no whole page is masked.

The [independent control audit](../reports/m4-mfc-control-audit/audit-r3/report.json) verifies actual fault causes, whole owned write prefixes, hardware preservation and cleanup. Request research tests establish the combined root/site/request admission refusal, rather than a uniquely isolated size guard. The 128-byte constructor uses a literal DWORD loop, with its pointer published before the first loop store. Handler/TLS and actual allocation-null execution receive no credit.

## Build and evidence corrections

Both native modes reused the parent inputs and added 65 game bodies plus two MFC bodies. The [final link scope](../reports/m4-mfc-control-audit/link-scope-r2/report.json) and [independent Ninja audit](../reports/m4-joint-startup103-root/control-link-r3/report.json) correct the earlier count: each mode has **295 actually linked source COFFs plus one retained, unlinked historical FDIV proof archive**. The archive supplies no required symbols to the admitted path. This is a metadata correction; the successful workers and captures were not rebuilt or changed.

The first paired attempt omitted four vector-endpoint relations. Exact source-derived field contracts corrected the comparison without changing candidate behavior or recapturing execution. The second control fixture adds immediate input/fault observations to distinguish its admission scope; prior evidence remains preserved. Audit-reader corrections for archives and inherited DWORD records likewise remain separate from the passed result.

The [scope receipt](../reports/m4-mfc-source/paired-scope-r1/report.json) distinguishes native backing guards from separately dumped bytes, and original MFC cleanup CALL/return evidence from a separate HeapFree-result ledger that was not captured.

## Remaining frontier

Stored callbacks, broader handler/TLS/null-allocation paths, complete CRT/MFC attach, environment/mainargs, original startup scheduling, whole-game alias liveness and native windows/menus remain open. Earlier user-confirmed live helper/numeric Training tests are separate from this standalone startup sequence. Native Training through the full project runtime remains M5.

The [physical lookahead](../reports/m4-joint-startup103-root/next-frontier-r2/report.json) identifies 41 remaining roots, including 31 with FS thread-state accesses and 17 with unresolved controls. The next bounded group contains six constructors sharing three normal exception-chain frame patterns. Its [static plan](../reports/m4-mfc-source/normal-FS-plan-r1/report.json) verifies 307 original instructions, including one nested chain and a shared lazy global; it earns no execution credit. Actual allocation counts must come from persistent execution.

The [execution plan r6](m4-execution-plan-r6.md) pairs that group with a validated shared-capture pilot. Current native execution took 106.90 seconds at O0 and 70.61 seconds at O2, and each level emitted 7.402 GB. These are stage timings, not total investigation time or a demonstrated workflow speedup.
