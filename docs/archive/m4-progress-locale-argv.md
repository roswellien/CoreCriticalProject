# M4 progress: complete locale and argument startup batch

Updated 2026-10-09. The complete bounded locale/argument startup batch passes native execution, independent original-source comparison and compiled review. The [whole-batch acceptance receipt](../../reports/m4-crt-locale-batch-root/acceptance-r1/report.json) seals the current evidence and physical dependencies.

The native startup research sequence now establishes the original heap, returns through its caller, initializes four static critical sections, creates the required lazy locale lock, completes default `_setmbcp(-3)` and character classification, and runs both original command-line parser passes. The original builder publishes `argc` and `argv` and returns to `7800BA9E`. This completes the behavior targeted by the [locale batch plan](m4-next-locale-batch.md).

The compiled x64 worker executes the recovered original instructions and uses real, typed Windows API bridges. It preserves native pointer widths while exposing checked 32-bit guest aliases. The required x64 critical sections have separate native storage. Parser output and lazy-lock allocations coexist on the same live heap; cleanup deletes critical sections, frees allocations and destroys that heap in order.

The next unresolved dependency is environment construction. The current stop occurs before the final `__getmainargs` output/return sequence. The zero environment pointer in the original data page is not a constructed environment. Original attach scheduling, complete CRT startup and a native game window/menu remain open.

## Current evidence

| Proof | Current result |
| --- | --- |
| [Canonical native execution](../../reports/m4-crt-locale-batch-root/execution-r7/report.json) | Passed 12 ordinary cases and 24 deliberate fault cases across O0/O2; 56.99 seconds including direct emission and verification |
| [Independent compiled native fixtures](../../reports/m4-crt-locale-batch-review/native-r2/report.json) | Passed 24 rows over 12 native stages with six additional command-line patterns per level; 28.17 seconds including direct emission and strict reads |
| [Independent original-source comparison](../../reports/m4-crt-locale-batch-model-review/observe-r10/report.json) | Passed all 12 ordinary cases and 441,746 comparisons; 175 complete phases per case; 60.37 seconds |
| [Independent raw-result and ABI review](../../reports/m4-crt-locale-batch-review/check-r3/report.json) | Passed 96 rich hardware pairs, 306 complete milestones, 7,956 full-page observations, 12 owner-thread refusals and ordered allocation/critical-section/heap cleanup; 9.33 seconds |
| [Whole-batch acceptance](../../reports/m4-crt-locale-batch-root/acceptance-r1/report.json) | Current source/build/native/review identities and strict archives verified together; previous diagnostic revisions receive no admission credit |

Execution costs are measured after implementation and compilation. They are not development-time or whole-project speed estimates. Actual NLS responses select the source branches; API counts can differ between runs or optimization levels and are checked against each case's measured witnesses.

## Efficiency changes now used

The [revised execution plan](m4-execution-plan-r2.md) is applied to this entire functional unit. Source recovery/modeling, native implementation and independent compiled review ran concurrently with integration. The worker directly emitted compact strict archives from its first run. There was no per-record physical capture tree, later packing pass or expansion of historical captures. Unchanged translated objects, libraries and accepted dependencies were reused by exact identity. Tests targeted the changed source routing, NLS bridges, ownership and failure cleanup.

The new compilation adds 51 literal entry bodies, including overlapping interior entries, covering 2,032 new unique original bytes. These are dependency bodies rather than 51 new game initializer roots. The selected initializer inventory remains 27 of 144 and is not an overall project completion percentage.

Each earlier failed build/run remains preserved. The successful native candidate is [preparation-r9](../../reports/m4-crt-locale-batch/preparation-r9/report.json) and [build-r9](../../reports/m4-crt-locale-batch/build-r9/build.json). Independent review rejected its predecessor because deferred NLS callbacks referenced an expired local flag and could select the wrong API signature. The corrected callbacks capture that flag by value. The [defect receipt](../../reports/m4-crt-locale-batch-review/api-lifetime-r1/report.json) preserves the earlier actual inputs and outcomes without admission credit. Genuine source returns, actual API outcomes, whole-machine observations and independent expected state are distinct proof domains; a transport receipt alone does not establish functional completion.

The [next implementation unit](m4-next-environment-batch.md) is the complete environment acquisition/vector construction and genuine `__getmainargs` return, carrying forward this unit's live owners. It must not resume from cleaned final captures or treat zero environment data as success. Its [static recovery](../../reports/m4-crt-environment-recovery/recovery-r2/report.json) is already prepared: 13 exact source spans, 1,170 unique bytes and 427 instructions. That preparation has no native execution credit.
