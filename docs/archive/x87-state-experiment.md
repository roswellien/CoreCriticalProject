# Live x87 stack, register and tag validation

The four authored raw80 profiles pass the final original/native comparison:
13,824 original x86 observations and 27,648 statically compiled native O0/O2
observations, with zero declared CPU, full-page, CW, status, TOP, occupancy,
full-tag or occupied-register differences. The
[contract](x87-state-contract.md) defines the exact inputs and observed fields.
The separate [logical-register oracle](../../reports/x87-state/independent-review/logical-oracle-summary.json)
and [physical-register review](../../reports/x87-state/independent-review/adapter-review/review-summary.md)
both pass all 41,472 saved observations. The physical review also replays all
twelve workers byte for byte, all 504 worker exclusions and 3,288 compiled
host-isolation checks. Their frozen identities are recorded in the
[M2 acceptance record](m2-acceptance.md).

| Profile | Original cases | Native cases | Defined behavior |
| --- | --- | --- | --- |
| FLD m80; RET | 3,456 | 6,912 | Exact raw80 push, TOP rotation, physical occupancy and masked overflow |
| FSTP m80; RET | 3,456 | 6,912 | Exact ten-byte store/pop, physical empty tag and masked underflow |
| FXCH ST1; RET | 3,456 | 6,912 | Exchange, sparse occupancy, missing-operand indefinite and sticky faults |
| FFREE ST1; RET | 3,456 | 6,912 | Clear the selected physical tag, preserve other live values and TOP |

Each profile covers all eight TOPs and twelve masked precision/rounding modes,
contiguous depths zero through eight, the noncontiguous logical mask02 and
directed sticky-status seeds. The payloads distinguish raw80 precision below
binary64 and include signed normal values, zeros, infinities and listed quiet
NaNs. Physical full tags and the original hardware FX/env captures independently
agree with the logical occupied-register values. Native FX/env arrays serialize
actual guest State; they are not hardware capture or an expected-result oracle.

The [immutable failed baseline](../../reports/x87-state/baseline-failure/report.json)
preserves 1,137 files and all twelve exact worker images. A separate logical
rotation oracle confirmed all original results and 22,272 failing initial
native cases, with correct native entry state. The earlier preliminary probe
and its independent review remain preserved separately. The repaired gate
rehashes and reparses that baseline under its original masks.

The repair adds internal always-inline LLVM helpers at four exact reviewed
instruction sites. They read actual guest TOP/tags and actual loaded raw80
bytes, update physical occupancy and masked stack-fault flags, and supply
floating indefinite for missing operands before the original instruction's
value moves. Pop also preserves sticky DE through its existing classification
assignment. The helpers use no request, case index, oracle or result observer.
Original guest instructions, State layout, bridges and observer are unchanged.

The canonical reports record 1,263 comparison, metadata, generated-IR and worker
admission rejection controls, plus 37 checks of deliberately excluded
observations. Adapter checks reject another 49 source/body/site mutations and
admit eight positive transforms. The eight native workers separately pass
96 raw80 memory-boundary checks, 120 host-environment checks and 3,072 host
MXCSR isolation combinations. Normal returns restore full64-bit host pointer
metadata; the exception-dispatch control has its separately stated scope.

Final [source/build/report pins](../../reports/x87-state/independent-review/final-pins.json)
bind shared source digest
`33e0881be27e2944ccde5faba749fe1df120fb1f6c7428951e37cb15faacbc05`.
The corpus is unchanged from the preserved canonical baseline. Reproduce the
entire gate in a fresh PowerShell7/Visual Studio process with
`pwsh -NoProfile -File tools/x87-state/build_state.ps1 -RunComparison`.

This gate admits the four exact sequences and their listed states. Other
instructions, arbitrary raw80 operands, extended signaling/subnormal encodings,
unmasked guest traps, cross-mode FIP/FDP/opcode/XMM equivalence and native game
execution need separate contracts. FFREE exit C1 is excluded as undefined;
entry C1 is observed for every profile. The
[consolidated floating-point policy](m2-floating-point-policy.md) retains those
distinctions and the tested pre-entry exclusions.
