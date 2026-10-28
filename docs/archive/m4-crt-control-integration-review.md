# Connected game CRT control independent review

The [final independent review](../../reports/m4-crt-control-integration/independent-final-review-r1/report.json)
accepts the complete game wrapper at `0x5AC5A0`, its import thunk at `0x5AC5D6`
and the four actual staged MSVCRT control bodies through unchanged shared
Runtime r9. Independent source-derived models check 192 original and 384
native O0/O2 records, complete CPU/defined flags, all 4,096 stack bytes, all
3,504 native State bytes, guest FX/legacy state and explicit host restoration.
All 4,992 native phase events and 768 completed Runtime call records match.

The wrapper's compiled CALL already pushes provider return word `0x5AC5AF`.
The import-tail supervisor projects Runtime's caller ESP above that existing
word; r9 rewrites the same word at the same address. This is a declared
orchestration convention. It creates no second guest CALL or additional stack
word. The actual compiled provider returns to the wrapper, which executes its
real `ADD ESP,8` and RET. Only the original observation's final capture PC is
projected; native execution returns to the actual boundary `0x5AC436`.

The review rejects 132 raw corruptions and five static source controls. A
separate compiled harness passes 347 checks across 33 scenarios at each
optimization level, including 26 repaired-trigger poisoned-context retries
and six masked boundary/unaligned positives. One normalized unmasked native
positive remains outside the measured equivalence corpus and grants no
original or numerical floating-point coverage.

Static reversal verifies all six game instruction PCs, all 34 exact guest/host
layouts, State alignment eight, four precise linker helper aliases and all
eleven unchanged provider definitions. Twenty actual COFF objects are freshly
decoded across the static and final reviews. All 2,493 author bindings, four
historical literal source replacements and 410 actual compiler-read header
associations are checked physically. Root acceptance rehashes all 3,069
independent [bindings](../../reports/m4-crt-control-integration/independent-final-review-r1/pins.json).
Reviewer failures and literal versions remain preserved.

Quantified equivalence covers twelve masked incoming control words with empty
TOP-zero/status-zero x87 state, trusted serial ownership and stable checked
mappings. This gate executes no following numerical initializer, full CRT
entry, SEH dispatcher, complete initializer table or native menu. Those remain
required for M4. The [experiment and recipe](m4-crt-control-integration-experiment.md)
record its reproduction inputs and bounded provider selection.
