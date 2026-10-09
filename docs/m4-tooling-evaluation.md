# REA and Ghidra evaluation

Evaluated on 2026-10-09 against the exact admitted MW3 executable. The installed versions are REA 6.1.0, Ghidra 12.1.4 and JDK 21.0.12.1. This evaluation adds no executable initializer credit; the accepted count remains 28/144.

## Measured results

The [benchmark receipt](../reports/m4-rea-evaluation/benchmark-r1.json), [complete REA evidence](../reports/m4-rea-evaluation/rea-game-evidence-r1.json) and [neutral analysis snapshot](../reports/m4-rea-evaluation/rea-game-analysis-r1.json) retain the observations and their original artifact identity.

| Experiment | Observed result |
| --- | --- |
| First query after cold import | 95.757 seconds, then an explicit missing-function result for initializer 410210 |
| Four helper/wrapper pseudocodes in the open session | 41 milliseconds; all four succeeded |
| Constructor 51B020 complete dossier | 46 milliseconds; six field stores and their exact assembly were visible |
| Bounded high p-code value trace for 51B020 | 31 milliseconds |
| Same dossier after closing and reopening with a saved snapshot | 93.811 seconds; the snapshot did not avoid cold provider initialization |
| Default function inventory | 10,575 entries: 10,113 internal and 462 external |
| Exact initializer roots recognized by the default function inventory | 3/144: 4C19F0, 4C3250 and 4C4980 |
| Direct Ghidra initializer-table seeding | 141 missing entries created in 22.7 ms; 144/144 exact entries available, zero conflicts |
| Direct Ghidra game pilot | Seven representative functions exported and 143 body bytes checked; 79.32 seconds cold CLI, 7.90 seconds saved-project CLI reuse |
| Saved-project game export work inside that CLI | 85.5 milliseconds for seven functions; persisted 144 entries, no new entries needed |
| Direct Ghidra staged MSVCRT pilot | Two functions exported and 361 body bytes checked; 30.66 seconds cold CLI, 8.21 seconds saved-project CLI reuse |

These are individual measurements on this machine, not a benchmark-derived overall project speedup. Warm pseudocode latency does not measure engineering, compilation, or runtime-validation time.

The 51B020 pseudocode made the ECX-relative offsets 4844 through 4858 immediately apparent. This corroborates the previously measured extra object page at 63C000. It also demonstrates a limitation: Ghidra's default recovered signature says `__stdcall` and has no declared object parameter, while the assembly uses the incoming ECX object. The pseudocode cannot serve as an unchecked ABI declaration.

## Division of work

| Tool | Use in this project |
| --- | --- |
| Ghidra | Recover function bodies, calls, data references, field offsets, control flow, type hypotheses and readable pseudocode |
| REA | Request batched/focused analyses, retain artifact-bound evidence and expose structured dossiers/value-flow observations to agents |
| Remill and LLVM | Keep translating exact instruction semantics and producing the native x64 objects |
| Original x86 workers and existing comparison harnesses | Establish actual behavior, x87/status/ABI results, committed memory, ownership, growth and cleanup |

Ghidra labels its pseudocode as decompiler-generated non-source, with no compilation guarantee. Recovered types, calling conventions, indirect targets and alias relationships remain hypotheses until checked against original bytes and execution. The project must retain its x87 precision/status, ABI, callback-frame and native-allocation ownership tests.

## Required adaptations

1. Seed the known initializer table before treating Ghidra output as a complete M4 inventory. The [seed generator](../tools/m4-rea-evaluation/initializer_inventory.py) verifies the original executable hash and all 145 table words, producing [144 original entry seeds](../reports/m4-rea-evaluation/initializer-inventory-r1.json). The [direct game pilot](../reports/m4-rea-evaluation/game-headless-r1/report.json) created the 141 missing entries without conflicts and retained all 144 on reopening the project. Entry availability is distinct from full recovery: this pilot byte-checked and decompiled seven representative functions, not all 144 bodies or ABI contracts.
2. Analyze each artifact once per batch, retain its session while requesting related functions, and export the results for parallel agents. Ghidra serializes function requests per Program; additional agents do not create a proportional decompiler speedup. Agents can work independently from the shared frozen exports on reconstruction, model/original comparison, and integration.
3. Keep a persistent local Ghidra project or exported batch results where useful. The neutral REA snapshot retains evidence but did not eliminate the measured cold startup when reopened. Reopening the EXE for every function would waste time.
4. Use ordinary headless Ghidra for shared DLLs. The [direct provider pilot](../reports/m4-rea-evaluation/provider-headless-r1/report.json) successfully exported `_onexit` at 78004A36 and `_msize` at 7800151D from the exact staged MSVCRT image and verified their original body bytes. The current [REA Windows P0 integration](https://github.com/morluto/rea/blob/main/docs/windows-ghidra-p0.md) excludes DLLs and database mutation. That is an adapter boundary; use the tested direct route rather than changing the installed adapter. Import names can reflect the current host export cache, so they are hints to check against the admitted provider and original execution.
5. Bind each exported body to its original byte ranges and SHA, and keep inferred names/types separate from accepted interfaces. Physical COFF symbol attribution remains a compiler-artifact check; decompiler names cannot substitute for it.

## Adoption decision

Adopt these tools for static recovery, dependency triage and batch specification. The [independent process assessment](../reports/m4-rea-evaluation/process-review-r1/assessment.md) confirms that current scripts already automate byte checking, graph walks and literal translation; the principal opportunity is reducing manual ABI, field and dependency investigation. The [r4 execution plan](m4-execution-plan-r4.md) adds a persistent shared analysis lane and measurable batch costs. Use the existing executable pipeline to establish correctness. The current 26-root registration work and its original54 captures remain preserved; changing analysis tools does not restart the accepted work or turn static results into 54/144 acceptance.

The next useful efficiency measurement is time to a complete accepted family: static recovery and contract preparation, implementation/build, original/native comparison, fault controls, and final integration. Record repeated work, manual interventions, cold-analysis count and newly accepted roots separately. This will reveal whether the new analysis lane reduces the actual critical path.
