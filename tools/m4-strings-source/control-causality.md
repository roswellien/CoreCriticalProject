# Independent control causality review

The final read-only gate is `reports/m4-strings-source/control-causality-r3/report.json`, SHA256 `097aa5f5525b1c4150f721ebcfbe097a872f2faf811aa51d428a07a7adb60574`. It reviews the actual O0/O2 direct archives from reviewer `controls-r4`, SHA256 `80031604b0af92783eb12cce2e401d2188fe08b660c5e142303f1bb4380c3a92`, without executing a new worker or supplying any AFTER state to a model.

It checks all 117 original provider instructions against physical MSVCRT bytes and every selected initializer slot against the original game PE. A local authored BEFORE model derives the original `Lab State\0` strlen reads and strcpy transfers: normal and first-byte-corrupted strlen both return 9; copy writes are 4, 4, and 2 bytes. Actual completed source ledgers must match those derived reads and committed write prefixes. The full guest allocation page must match the committed input prefix, remaining genuine allocation initial bytes, and initially zero extra mapped bytes. Every retained successful root record must identify its exact original table slot and entry.

| Case | Intervention and actual refusal | Last source PC | Last stable stage |
| --- | --- | --- | --- |
| 0 | Ordinary 71 roots, 16 duplicate owners, later consumed-context retry | No first fault | 45 |
| 1 | Strdup argument changed; carried stack mirror refuses | 78010A6D | 50 |
| 2 | Length-preserving input corruption; real malloc(10), immutable-input refusal before strcpy/copy | 78010A8B | 43 |
| 3 | Actual mapped source Region 5E0000 made unreadable; literal DWORD read refuses at 5E4240 | 78002F52 | 50 |
| 4 | Destination made read-only; first literal DWORD write refuses | 78002FDE | 53 |
| 5 | Destination made read-only after 4 committed bytes; next DWORD write refuses at alias+4 | 78002FDE | 53 |
| 6 | Deliberate observer exception before strdup body | 78010A6D | 50 |
| 7 | Deliberate observer exception after strlen RET | 78010A7C | 51 |
| 8 | Deliberate observer exception before strcpy body | 78002FAB | 52 |
| 9 | Deliberate observer exception before first copy store | 78002FDE | 53 |
| 10 | Deliberate observer exception after first committed DWORD | 78002FDE | 54 |
| 11 | Deliberate observer exception after genuine strdup RET, before object-field publication | 48EB28 | 55 |
| 12 | Corrected mutation of owning IAT; original CALL operand reads changed 5BB670 and refuses | 48EB22 | 45 |
| 13 | Actual full native allocation byte corrupted; complete backing mirror guard refuses | 78002FAB | 52 |

Cases 3–5 are guest-memory permission faults at literal original load/store instructions. Cases 6–11 are deliberate observer exceptions and receive no guest/API fault credit. Case 2 proves the unchanged length can legitimately reach an allocation before the original-input admission guard refuses copy. Case 13 binds the actual full-width owner pointer and compiled perturbation mechanism; it does not claim a separately captured native AFTER byte array.

The original case 12 in `controls-r3` attempted a write directly into the game's read-only `.rdata` Region. That failed within the fixture at phase 0 and never reached the intended IAT identity guard. `control-causality-r2` retains this finding in both levels and has `passed=false`; `control-causality-r1` preserves an earlier audit-checker diagnostic concerning an ordinary successful session's new retry fault. Neither is an acceptance gate. The corrected `control-build-r3` changes only the `before_phase` intervention: at phase 20 it briefly makes exact Region 5BB000 writable, changes 5BB670, restores read permission, and then proceeds. The final gate requires the actual last ledger row `(48EB22,5BB670,78010A6D,4,read)`, exact source fault `(failed,48EB22,5BB670,45)`, 20 completed roots, and no fabricated strdup witness.

The source71 proofs and all older worker captures remain unchanged. This review adds control causality evidence, not additional initializer or whole-game completion credit.
