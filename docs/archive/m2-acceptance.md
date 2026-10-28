# Milestone 2 acceptance record

Prepared 2026-10-07 against all twelve requirements of the
[completion audit](m2-completion-audit.md). The technical gates and ordinary
checks are accepted within their stated domains. **All twelve M2 requirements
are accepted.** The separate [independent objective audit](../../reports/m2-acceptance/final-independent-audit/report.json)
and [root acceptance decision](../../reports/m2-acceptance/root-review/technical-acceptance-final.json)
record completion after reviewing the immutable technical map. The parent owns
the final goal status and milestone register update. This record does not replace
T12, architecture or any wider mandatory requirement.

M2 establishes bounded CPU, floating-point, calling and import contracts plus
the context for a next game slice. It establishes neither a running native game
nor general x86/x87/Win32 compatibility. The selected game slice remains denied
for execution until M3 supplies its exact translation and defined state proof.
All general execution permissions remain false.

## Twelve-item requirement map

| Item | Accepted bounded result | Evidence |
| --- | --- | --- |
| M2-01 | FNSTCW across 12 masked CWs and all 144 FLDCW/FNSTCW transitions; stored/resulting CW, integer state and complete page agree at original/O0/O2. | [Control contract](x87-repair-contract.md), [independent verification](../../reports/x87-repair/independent-verification.json). The preceding precision-clamp failure remains preserved. |
| M2-02 | All numerical domains listed in the consolidated contract: PC24/53/64, all four RCs, extended arithmetic, explicit binary64 spill/reload, valid signed32 conversion, selected zeros/infinities/NaNs and range/denormals. Stronger conversion/store/range C1 gates pass. | [Floating-point policy](m2-floating-point-policy.md), [supplement review](../../reports/m2-acceptance/fp-policy-review/report.json), state addendum below. Earlier exact integer/rational independent oracles remain bound. |
| M2-03 | DE/OE/UE/PE/C1, tiny signed zero, infinity/maxfinite and discriminating tininess boundaries agree for 3,840 original and 7,680 native range observations. Host DAZ/FTZ/RC cannot change them. | [Range contract](x87-range-contract.md), [independent review](../../reports/x87-range/independent-review/independent-verification.json), [separate review](../../reports/x87-range/independent-review/read-only-review-summary.json). The 91-file archive retains 3,072 DE-only failures. |
| M2-04 | Canonical ten-byte live80 values, logical/physical mapping, all TOPs, full/abridged tags, contiguous and selected noncontiguous stacks, push/pop/exchange/free and masked faults with sticky seeds. | [State contract](x87-state-contract.md), [canonical pins](../../reports/x87-state/independent-review/final-pins.json), [logical oracle](../../reports/x87-state/independent-review/logical-oracle-summary.json), [physical/replay pins](../../reports/x87-state/independent-review/adapter-review/final-pins.json). All 41,472 original/native records match. |
| M2-05 | Exact admitted domains and defined observations; sticky flags within admitted sequences; tested exclusions for unsafe conversion, two/unlisted NaNs, unmasked CWs, clearing/trap/exceptional exits and unknown instructions/state. | [Frozen policy](m2-floating-point-policy.md), [fresh policy review](../../reports/m2-acceptance/fp-policy-review/report.json) and final addendum below. Frozen pending annotations remain historical. |
| M2-06 | Actual stack argument consumption independently of poisoned EAX, RET4 callee cleanup, caller-cleaned indirect frames, CPU/flags/return/page effects and preserved logical FP/SIMD storage. | [Boundary contract](m2-boundary-extension-contract.md), [independent root review](../../reports/m2-boundary-extension/root-review/report.json). 13,776 controlled raw records and fresh compiled context/storage controls pass. |
| M2-07 | Explicit guest32 global/IAT layout, initialization and read/write effects, complete two-page observations and bounds/wrap/permission rejection; host pointers remain private. | [Integration contract](m2-call-integration-contract.md), [integration root review](../../reports/m2-integration/root-review/report.json), boundary regression. General loader/global recovery remains a later task. |
| M2-08 | Actual observed MW3 WINMM.timeGetTime IAT/CALL identity bound to a selected private provider/bridge/context. Same path executes deterministic or real trusted Win32 provider, exactly once each per record. | [Boundary contract](m2-boundary-extension-contract.md), [live observations](../../reports/m2-boundary-extension/live-comparison.json), [root review](../../reports/m2-boundary-extension/root-review/report.json). All 24 real live records pass full declared state/page/progress checks. |
| M2-09 | Both admitted indirect targets execute through the frozen guest-address registry; bad target/continuation rejects with guest diagnostics. | [Integration contract](m2-call-integration-contract.md), [root review](../../reports/m2-integration/root-review/report.json), compiled boundary context controls. Unregistered/unbounded targets remain denied. |
| M2-10 | Hash/address registration, generated defaults and selected replacement/original routes without recursion; direct/indirect selection, conflict and frozen mutation controls. | Same integration and boundary reviews. These use actual statically generated functions, with no interpreter/JIT fallback or host pointer in guest storage. |
| M2-11 | Full 43-byte next function, RET8/two stack reads/five globals/incoming CALL and dependency/state/routing contracts reviewed from actual private PE. | [Next-slice context](m2-next-slice-context.md), [root review](../../reports/m2-slice-admission/root-review/report.json). 15 frozen identities, five reviewer corruptions and six asset-free groups pass. Execution remains denied pending M3 translation and AF/CPU/full-memory/live-state preservation. |
| M2-12 | Frozen source/tool/artifact/worker/result pins, exact defined observations and independent saved-record reviews, meaningful negatives, immutable failure archives, fresh prior replays and all eight ordinary groups with no skips. | [Acceptance summary](../../reports/m2-acceptance/summary.json), [ordinary checks](../../reports/m2-acceptance/ordinary-checks/report.json), [G1/G2 replays](../../reports/m2-acceptance/prior-gates-replay/report.json), earlier 57-worker replay and state reviews. The separate objective audit and root decision accept all twelve requirements. |

## Floating-point policy addendum

This separate record resolves, for M2 acceptance, the historical
`pending_live_state_final_acceptance` annotations in the immutable FP
supplement. It does not alter its source, domain manifest, failures, worker
outputs or planning API. That planning API continues to deny live profiles and
all general execution. The exact state workers are admitted only through their
own frozen fixture/state/memory contracts.

The supplement final-pins SHA256 is
`1e85288d1b97d400f91400482bea22f3d3a3790acca0326e875ca65b0673f7c1`.
The fresh independent reviewer rehashes all 536 identities before and after;
rederives each mode/vector Cartesian domain and declared complete CPU/page/CW/
status observations for 23,904 raw numerical records; replays nine full corpora
(4,032 records) byte-for-byte; and runs all 174 saved unsafe controls against actual original/O0/O2 workers:
147 mutations of only the final input record and 27 fixture-identity changes.
Every late input mutation leaves prior records and header/extent valid. All
174 controls reject with the expected diagnostic and emit zero bytes.
The planning checks cover 8,124 credited admissions, 186 rejections and a domain
identity corruption. Numerical expected values continue to be established by
the separate previously accepted exact-oracle gates, not by copying measured
results into an oracle.

The separately accepted canonical live-state pins SHA256 is
`3d93c36c3bb3d4c7839555fa2171b250a4fa1a849d9e51178ff402fefd1dd78d`,
source digest
`33e0881be27e2944ccde5faba749fe1df120fb1f6c7428951e37cb15faacbc05`.
All four profiles include 3,456 original and 6,912 native observations each:
13,824 originals and 27,648 natives, zero defined differences. The separate
logical-oracle summary SHA256 is
`5daf7e519f3035f9c57ea258805fe8b11fd6a83f94acfa6b489126be287da90b`.
The physical/replay review pins SHA256 is
`65512f5ed01b4418e139eda9a92d6aafa3f5592a2a3d5bd3fbce0bd4ddfc4fd2`;
it binds 78 review artifacts and 2,806 inputs, 12 byte-identical worker replays,
3,288 fresh native checks, 504 saved worker exclusions, 271 field corruptions,
56 coherent semantic corruptions and 37 excluded-observation controls.
These independent reviews and root acceptance resolve the state requirement;
the preceding 22,272 native failures remain preserved as incompatibilities.

The exact domains retain all twelve masked PC/RC modes. Numeric cancellation
and spill observe SW38FF: their final C1 is **defined but deliberately
unobserved**, rather than an undefined zero expectation. Conversion, final
store and range observe SW3AFF including actual C1. The state profiles retain
their exact masks; FFREE exit condition bits are instruction-undefined and
excluded. Raw status remains saved. Empty payloads are excluded while occupied
ten-byte values, physical occupancy, full tags and TOP remain observed. No
consumer or enlarged instruction sequence becomes admitted through these
exclusions.

Only listed canonical raw80 normals, signed zeros/infinities and quiet NaNs
are admitted by state probes. Extended signaling/subnormal/pseudo-denormal/
unnormal encodings, arbitrary patterns and unsupported states remain rejected.
Only the listed single binary64 NaNs admit exact payload/sign propagation;
two-NaN selection and unlisted payloads remain denied. FISTP32 admits only the
listed valid finite values whose results are representable at every RC.
Out-of-range/nonfinite/subnormal conversion remains rejected before entry.
All observed exception masks are set. Guest FNCLEX/FNINIT/FWAIT, unmasked trap
delivery, guest SEH/callback/thread/TLS/FS/MMX/SSE semantics and exceptional-exit
pointer restoration remain unsupported. Harness clearing is not guest clearing.
Normal-return host FP isolation and tested Windows dispatch controls are
credited only under their individual contracts.

For store-only control planning, `loaded_CW` is inert metadata. The actual
FNSTCW worker's second frame word is unused, its domain has twelve entry CWs,
and it has no FLDCW. Only the load/store fixture credits all 144 transitions.
The redundant legal metadata field grants no execution and never enlarges
the measured store count.

## Preservation, regressions and ordinary checks

The boundary review rehashes 21 prior G1/G2/x87/range/integration evidence entries.
Its fresh 57-worker replay preserves 49,812 saved records byte-for-byte,
including named historical defects. The separate fresh final G1/G2 replay
executes all fifteen original/O0/O2 workers: 40,576 G1 originals, 81,152 G1
natives, 16,609 G2 originals and 33,218 G2 natives, totaling 171,555 unchanged
raw records. No prior gate is rebuilt or overwritten. State physical review
also replays 24,372 prior strongest-profile records and its twelve canonical
workers. Counts describe each evidence set; overlapping replays are not added
as unique compatibility cases.

Current ordinary CMake configure/build pass with warnings-as-errors. CTest
registers exactly runtime, binary tools, asset tools, in-game hook evidence,
game monitor, invalid monitor handles, MW3 comparison controls and host adapter
controls. All eight pass with the process-local LLVM adapter opt-in enabled;
there are no skipped or empty test groups and source identities stay unchanged.
The first restricted build timeout and the first disabled optional test are
recorded separately and receive no final pass credit. No missing private input
is interpreted as success.

The [summary](../../reports/m2-acceptance/summary.json) binds the contracts, trusted
anchors, review/replay code and report hashes. The separate root and independent objective reviews close M2-12; the parent
records the goal completion decision.
M3 begins with exact translation and preservation of the selected admitted
integer game slice; unresolved timer/FILD64/FMUL32 dependencies remain denied.
