# M4 execution after the accepted MFC family

Updated 2026-10-09. The [connected103 sequence is accepted](m4-progress-startup103.md), adding 32 roots. This supplements [plan r5](m4-execution-plan-r5.md); exact-SHA projects, frozen sources, concurrent lanes and complete changed-batch validation remain required.

## Next counted unit: six normal FS constructors

The [physical planning receipt](../../reports/m4-mfc-source/normal-FS-plan-r1/report.json) identifies roots `46AB30`, `48F250`, `4B4C10`, `4C3250`, `4CFE80` and `4D4830`. Accepting them would advance the inventory to **109/144**. Planning earns no credit.

Five roots share helper `4E78D0`; `48F250` uses `48F290`. Root `4D4830` nests an outer frame around the shared helper. All normal paths save the previous FS0 chain and literal handler/scope record at entry ESP minus 12, then restore the caller's chain and stack. A shared global at `60B888` makes allocation counts depend on earlier roots; do not assume one new allocation per constructor.

1. Capture genuine original Windows FS0, complete 12-byte chain records and full surrounding source state at installation, nested calls and restoration. Derive reached-path contracts from actual BEFORE inputs. Keep exception dispatch, handler execution and failed-allocation branches separate until supported.
2. Implement owned native guest thread/chain memory and literal FS-addressed operations. Treat the native sentinel as an explicit chain identity with checked provenance, rather than silently equating it with an original Windows pointer. Preserve complete caller state, previous chain and each nested record.
3. Reuse accepted103 heap, MFC, strings and registration components. Recover actual shared-global allocations, owner aliases, object bytes and cleanup from persistent execution. Maintain original table order and one bootstrap.
4. Run three engineering lanes from frozen exports: native integration; actual original/source derivation; independent interface, ownership and fault review. Reuse warm Ghidra projects for changed entries and only expand analysis for a concrete missing path.
5. Execute the full extended sequence at original x86 and native O0/O2. Validate complete State/CPU/FX/environment, all pages, exact chain records, ownership and cleanup. Compile controls for chain integrity, nesting, committed writes, wrong-thread use and retry preservation. Seal evidence before counting 109.

## Capture-sharing pilot

Each current native archive has 1,931,112 logical records and 7.402 GB of payload. The [accepted71 measurement](../../reports/m4-capture-sharing-evaluation/evaluation-r1/report.json) found 96.94–96.96% globally repeated payload; it does not establish current103, part-local or runtime savings. Current emission and reading repeatedly copy/hash the same bytes.

Build an explicit additive format with part-local sharing first. A canonical index should map every unchanged logical name to a blob ID, with separate unique blob offsets, sizes and hashes. Unique payload extents must remain contiguous and bounded. Preserve logical record counts and logical byte totals separately from physical storage totals. Keep the existing format and reader intact.

The writer must copy or privately spool immutable bytes, hash at append, compare full bytes before sharing equal hash/size entries, retain atomic publication and poison semantics, and preserve the hardware/LastError boundary. The new reader must authenticate the pinned whole archive, canonical index, references, complete unique payloads and exact logical coverage. Verified immutable bytes may be reused while the existing no-write/delete file handle and read-only mapping remain held; use no cross-process metadata cache.

Required pilot gates are exact old/new logical-name-to-bytes equality; meaningful corrupt hash/reference/extent/name/part rejection; empty and repeated page records; one-byte changes and forced hash-key collisions; part rollover and bounds; incomplete-write publication/refused retry; attempted mutation while open; and existing x87/environment/MXCSR/XMM/DF/LastError preservation. Benchmark emission, finalization, reader startup, logical access, unique storage and peak memory before adoption. Do not replace acceptance evidence with a size-only test.

Run the pilot alongside FS source recovery. Adopt it only after independent compatibility/corruption review and unchanged semantic consumer results. Otherwise the next batch uses the current validated transport.

## Subsequent M4 requirements

The remaining roots include additional CRT/string/lock/font/version/registry services, unresolved control flow and a numeric `_hypot` initializer. Environment/mainargs, complete startup scheduling and native menu entry remain separate work. Callback registration does not establish callback dispatch. Native Training follows in M5; initializer inventory coverage is not full-game completion.
