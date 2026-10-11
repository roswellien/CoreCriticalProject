# Accepted native startup sequence: 120 selected roots

Updated 2026-10-09. **120/144 selected startup initializers are accepted**, up from [116](m4-progress-startup116.md), with **24 inventory roots remaining**. This is 83.3% of the initializer inventory. Full M4, project-built native menus and native Training remain open.

The [final acceptance](../reports/m4-joint-startup120-root/acceptance-r1/report.json), SHA `e640ff4eaa068a039a5e810ad99b4c0ca0336821b8b1a6f33f81012ad43ed0ee`, binds **44 passed gates and 324 explicit measured predicates**. Its conflict-normalized union rehashed all **10,276 physical dependencies** in 69.96 seconds without a metadata cache. The accepted 116-root evidence remains unchanged.

## Added behavior

Roots `40F0E0`, `4795F0`, `47F5F0` and `4B5220` execute in original relative table order. Their recovery contains fifteen new game bodies, 184 physical instruction rows and 596 bytes. They add four callback registrations and one normal game exception-chain record. Their constructor bodies introduce no new provider, ordinary object allocation or string-copy operation. The complete selected schedule has **92 ordered callbacks, 50 MFC allocations, 19 strings and one callback vector: 70 live owners before cleanup**.

Six reached calls use three physical target cells. Four calls use absolute cells; two genuinely read the constructor-installed instance vtable. The derived vtable is committed before its instance use. The literal helper ORs the global DWORD at `5F49B8` into the object and retains its complete flag effects before the caller clears the field. The pointer helper is admitted only for the reached zero argument, with no pointee read. General virtual dispatch and the nonzero pointer path remain open.

The original observes genuine target entry and pre-RET CPU/FX/environment and stack frames; its post-RET CPU is derived from the literal RET. Native captures observe actual entered and returned State/CPU/FX checkpoints. These are distinct observation boundaries.

## Passed evidence

| Gate | Measured extent |
| --- | --- |
| [Original x86 execution](../reports/m4-vtable-original/validation-r1/report.json) | Six persistent sequences, 720 root calls, forty observed pages |
| [Original source](../reports/m4-next-source/original-game-source-r1/report.json) | 552 constructor prefixes, 21,528 whole nonstack-page checks and 36 complete indirect entry/pre-RET pairs |
| [Persistent native source](../reports/m4-next-source/connected-native-source-r2/report.json) | Twelve sequences, 1,440 root calls, 57,600 whole-page checks before plus 57,600 after; no per-phase or AFTER state seeding |
| [Finite indirect source](../reports/m4-next-source/indirect-source-r1/report.json) | 72 actual native CALL/RET joins, 144 full native boundaries, 36 original pairs and 72 paired interfaces |
| [Whole paired data](../reports/m4-next-source/paired-policy-r1/report.json) | 1,440 phases and 109,440 ordinary nonstack-page relations |
| [Normal chain relation](../reports/m4-next-source/paired-FS-normal-policy-r1/report.json) | 180 paired game frames, 360 complete installed/restored twelve-byte relations and 180 nested CRT null-free accesses |
| [Typed ownership](../reports/m4-next-source/paired-owned-policy-r1/report.json) | 96 carried owner relations, 288 complete selected/grown/cleaned endpoints and 204 vector-field commits |
| [Independent fault audit](../reports/m4-vtable-control-audit/audit-r5/report.json) | 108 attempts, 52 causal refusals, 54 unchanged retries, 358,404 byte-exact retry records and 54 HeapDestroy identity triplets |

The [provider proof](../reports/m4-vtable-review/provider-source-r1/report.json) checks 22,812 complete State/CPU/FX checkpoints and 1,987,524 whole checkpoint pages. It verifies 600 MFC allocations, 228 duplicated strings, 840 source frees, 192 source growth operations and twelve real heap destructions. In every sequence, the first additional registration makes two genuine size queries to the same old owner. Measured capacity and used size are both 368 bytes; the literal four-byte append independently predicts the observed first-replay growth.

The [raw paired audit](../reports/m4-joint-startup120-root/paired-review-r2/report.json) derives six observed compiled diagnostic spans totaling forty bytes and verifies all 17,280 exact span relations. Each remaining page difference has an explicit typed or branch-input relation; no blanket mask is granted. The complete original initialized MFC loader page and native raw PE page are carried separately, with all actual differences retained. The borrowed pointee remains outside the read/mapping domain.

The controlled original RET hook at `59FF0D` replays the genuine one-byte RET. Its unused tail contains two NOP bytes and two bytes of the unselected neighboring body at `59FF10/11`. Independent review excludes that neighbor from the complete selected 120-root closure; whole-game use is outside this fixture.

## Build, tools and remaining scope

The [link audit](../reports/m4-joint-startup120-root/link-r3/report.json) verifies **351 literal COFFs, 27 compiled objects and two capture objects per level: 380 actual inputs**. One historical FDIV archive per level remains physically retained and unlinked. The [actual native run](../reports/m4-joint-startup120-root/execution-r3/report.json) completes all 120 roots in 151.32 seconds at O0 and 114.42 seconds at O2. Each level emits 2,955,462 canonical logical records and 11,446,566,451 logical payload bytes. These are worker measurements, not a whole-workflow speedup estimate. The isolated control fixture additionally links its rich hardware capture object, totaling 381 inputs per level.

Warm Ghidra exports cover all fifteen requested bodies without a cold import. A missing `59FF80` boundary uses an explicit unsaved, physical-source-bound annotation. Focused [REA evidence](../reports/m4-vtable-rea/review-r1/report.json) corroborates five boundaries and two fixed targets, while retaining the missing boundary and unresolved instance target. Literal physical bytes remain primary. These measurements do not establish whole-workflow speedup.

Earlier rejected preparations, invocations and proof scripts remain preserved. Corrections are additive. The final fault audit authenticates committed source prefixes, actual private mutations, full retries and cleanup. Hardware preservation covers the authored caller boundary through C++ catch; it gives no naked throwing Session guarantee.

[Plan r9](m4-execution-plan-r9.md) starts with authentic MSVCP initialization and the four smaller Lockit roots, while the complex tree root is recovered concurrently. The [physical next frontier](../reports/m4-joint-startup120-root/next-frontier-r1/report.json) verifies the 24 remaining roots: 4,614 instruction rows, seventeen roots with FS sites, thirteen with unresolved controls and one with floating-point sites. Remaining graph, service and numerical roots, startup scheduling, environment/mainargs, required thread/exception behavior and menus must still pass before M4 closes. Earlier live helper/numeric Training tests do not establish project-built native Training.
