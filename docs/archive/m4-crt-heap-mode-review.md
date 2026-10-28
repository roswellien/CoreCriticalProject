# Heap-mode selector/probe review

The bounded path preserves the accepted literal caller, actual `HeapCreate(0,4096,0)` ownership bridge and source token publication. It adds the selector prefix `[0x78003A0C,0x78003A31)` and complete probe `[0x780058B5,0x780058E6)`. The probe's loopback JMP is guarded and compiled but is not taken by the fixed `0x122C` allocation path.

Static source recovery and an independently authored contract verify the unique original `KERNEL32.dll!GetVersionExA` import at `0x7802E0A0`, whose raw guest target is `0x00034600`. The query CALL is at `0x78003A2B`. Execution refuses there with `unresolved_import`, before any native OS-version query.

## Source and state contract

The source saves EBP, supplies the allocation size and genuinely calls the probe. The probe saves ECX, touches `0x20000850` and `0x20000624`, restores ECX, moves the actual return word to `0x20000620` and executes RET. Selector source then saves EBX, passes `0x200017B8`, writes the structure size `0x94` and executes the query CALL, storing `0x78003A31` at `0x20000618`.

The terminal ordinary state is EIP `0x00034600`, ESP `0x20000618`, EAX `0x200017B8`, EBP `0x20001850`. Other registers follow source effects and carried input. The heap-mode global remains unproduced. Probe RET is complete; selector RET and heap-initializer RET are not.

The fresh owned page at `0x20000000` is declared input admitted before execution and is never reseeded. The original TIB StackLimit and runtime Policy stack limit stay at `0x20001000`. Mapping the page below that limit does not establish original guard-page growth or original lower-stack byte equivalence. The raw probe code page at `0x78005000` and all original code/import identities are guarded.

The final TEST uses the declared DWORD at `0x20000624` AND the old stack address `0x20001848`. Ordinary zero input yields defined arithmetic flags `0x44`. The four source AF representatives are qualified at `0x780039BF`, `0x780039D6`, `0x780058DB` and `0x780058C5`; undefined AF is not a universal original-machine assertion.

## Ownership and fault scope

The guest token `0x48450001` refers to one privately owned full-width Windows HANDLE; truncation is forbidden. The owner stays live through probe execution and the query frontier. Successful cleanup destroys that same handle once and restores the caller's LastError. On ordinary rows, source stores alone change guest stack and globals. Fault fixtures deliberately corrupt selected return words through test hooks. Diagnostic permission restoration permits complete fault snapshots without changing bytes or retrying source execution.

Fault controls cover code identity, read and write permissions, saved and relocated return integrity, query import identity, exceptions at partial progress, and cleanup. Separate independently authored initial stack patterns exercise both probe TESTs. The original API's volatile-register and flag internals are outside the finite bridge contract.

## Verification receipts

Static recovery, independent source/ABI/COFF review and the root draft model passed. The frozen draft audit checks 48 ordinary models, 12 directed stack formulas and 4,044 comparisons.

Across O0 and O2, the native runs passed 72 author scenarios and 132 independently authored scenarios, for 204 scenarios overall. The independent corpus records 6,770 assertions, six declared initial lower-stack patterns, 38 malformed-token denials and 264 actual host-state pairs. Its hardware checker rejects 548 selected semantic corruptions and 39 inventory/request corruptions. The author and reviewer witness 156 actual heap creations with 156 matching successful destructions.

The root ordinary comparison checks 48 rows across 34 checkpoints with 155,741 checks and 2,352 selected corruption denials. An independent final audit verifies 1,632 complete machine/ownership checkpoint pairs, 11,052 comparisons, 1,248 unused service records and 48 distinct constructor/resource owner associations. Four strict archives contain 292,782 logical records in total, with complete whole-file and per-entry hash validation.

The initial hardware checker had a CPU-field ordering error. Its refusal is retained as history, and the corrected checker passed on the same frozen native captures. No native rerun or extra native-execution credit follows from that correction. No new nonzero caller-LastError fixture is claimed; the prior accepted gate remains the historical evidence for that separate case.

Current receipts are [author execution](../../reports/m4-crt-heap-mode/execution-r1/report.json), [ordinary comparison](../../reports/m4-crt-heap-mode-root/observe-r1/report.json), [independent final model audit](../../reports/m4-crt-heap-mode-root-audit/final-r1/report.json), and [independent source/native/hardware seal](../../reports/m4-crt-heap-mode-review/sealed-r1/report.json). [Root admission](../../reports/m4-crt-heap-mode-root/root-acceptance-r1/report.json) binds these frozen receipts. Final verification rechecks its dependency closure, Python/PowerShell syntax and document links.

All accepted heap-create sources and receipts remain unchanged. See [project progress](m4-progress-heap-mode.md) and [the preceding technical gate](m4-crt-heap-create-review.md).
