# Heap mode publication and initializer return

The candidate reuses the complete original 77-byte heap initializer already translated to x64. A fresh typed binding owns the actual full-width HeapCreate handle. The genuine selector RET returns through the existing translated CALL chain while that ownership remains live. No old cleaned-up AFTER capture is resumed and no host store skips the source continuation.

The qualifying source sequence is CMP at `0x780039E8`, mode publication at `0x780039EB`, two conditional branches, PUSH at `0x78003A08`, POP at `0x78003A0A` and RET at `0x78003A0B`. The first comparison produces arithmetic flags `0x91`; the final comparison produces `0x95`. The final machine has EAX 1, EIP `0x78001843` and ESP `0x2000185C`, where the original cdecl argument remains. The caller has not executed.

The checked PUSH store precedes ESP publication. Existing generated POP code advances ESP before its checked read, then publishes EAX only after success. The RET read precedes EIP and ESP publication. Directed controls must preserve those actual partial effects. A failed store receives no publication credit; a committed store remains visible after a later failure.

All 38 original COFF objects, two FDIV libraries, 21 mappings and 2,086 source-identity bytes are unchanged. There are no new guest objects or guarded bytes. Actual query output transport remains separate from the 35 source accesses: 37 DWORD stores, complete 148-byte input and output, full BOOL and two API-return reads. Other actual responses retain the unresolved environment-query frontier.

Every qualifying ordinary capture includes 44 whole machine and memory checkpoints, full query metadata, live/closed private ownership and genuine source progress. Unused heap-create, heap-mode and heap-version bindings have distinct constructor-only owners and zero runtime ledgers. The source model starts from original BEFORE data; native AFTER State is never used as its expected seed.

The initial build passed compilation but independent review refused readiness because one generated wrapper retained the ancestor owner. The original preparation and build are preserved. The corrected preparation changes that wrapper's owner reference and passes independent source, ABI and object review before native execution. The previous gate's unexplained legacy floating-point metadata failure also remains preserved without passing credit or weaker checks.

The first author execution summary counted two deliberate public-metadata forgeries as mode stores. A fresh read-only summary counts only the genuine committed source store in the original archives. The original summary remains preserved; no binary change or repeated native execution supplies the corrected count.

The enlarged independent capture exceeded the unchanged 200,000-file archive limit. Publication uses two disjoint, byte-identical copy partitions per optimization level, preserving every original relative path and hash. The failed aggregate publication and unavailable hardlink operation are retained. Neither caused a native test rerun or a transport-limit change.

The archive preflight caught a checker expectation that replaced the ordinary 35-access count with a partial 32-access count. The refused checker is preserved; its corrected expectation passes the same first-level archives. Candidate code and native captures are unchanged.

The [corrected author execution](../reports/m4-crt-heap-return/execution-r2/report.json), [ordinary source observer](../reports/m4-crt-heap-return-root/observe-r1/report.json) and [independent full-capture audit](../reports/m4-crt-heap-return-root-audit/final-r1/report.json) record the completed source and machine comparisons. The author passed 72 cases; the independent harness passed 244 integrated cases and four separate host API diagnostics, with 15,042 assertions and 44 malformed-token refusals. These host-only diagnostics do not add integrated source coverage.

The bounded source initializer return is credited separately from persistent heap ownership or full allocator behavior. Full CRT initialization, original attach scheduling, remaining services, native menu/input and Training remain unproved.
