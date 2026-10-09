# Milestone 2 completion audit

Completed audit 2026-10-07: **M2 CPU and ABI validation is accepted**.
The completed range and live-state experiments are dependencies of that goal.
All twelve requirements are accepted within their explicit bounded domains.
The [final acceptance record](m2-acceptance.md), separate objective audit and
root decision close this checklist; the parent records goal completion.
No game launch is required for the authored probes.

## Authority and scope

[The milestone register](project-milestones.md) defines M2 as reviewed contracts
and original/native comparisons for required floating-point behavior, direct
calls, global data, an observed import bridge and bounded indirect dispatch.
Unsupported behavior must be identified and rejected. Guest state and routing
for the next game slice must be defined.

[T12 in the initial-phase plan](initial-phase-plan.md#t12-next-phase-probes-after-a-successful-integer-proof)
adds explicit hash/address-based selection of generated and authored replacement
routes. [Architecture](architecture.md) supplies the guest-address, calling,
state, routing and unsupported-path invariants. The
[roadmap](roadmap.md) retains those dependencies after the floating-point work.
This audit does not replace or narrow those definitions.

M2 is a bounded CPU/ABI validation milestone, not native startup or gameplay.
It does not require implementing every x86 instruction or every Win32 import.
Each supported domain must pass its contract; excluded behavior needs an explicit,
tested rejection policy before it can be encountered by the next admitted slice.
Callbacks, threading, SEH, TLS/FS, MMX/SSE and unusual control flow require
additional implementation only if that slice admits them. Unknown dependencies
cannot silently become supported paths.

## Durable completion checklist

| ID | State | Required result and evidence |
| --- | --- | --- |
| M2-01 | Complete within tested domain | Control-word storage and all 144 transitions across the 12 masked PC/RC modes match original x86 and native O0/O2. Keep the reproduced precision-clamp failure and isolated toolchain repair. Evidence: [control repair](x87-repair-experiment.md). |
| M2-02 | Complete within consolidated bounded domains | Arithmetic at PC24/53/64 and every RC, extended intermediates, explicit binary64 spill/reload, finite signed32 conversion, signed zero, infinity, selected single-NaN propagation, range and denormals have exact original/native evidence. Finite conversion C1 and final FSTP C1 match under their stronger masks. The [final policy addendum](m2-acceptance.md#floating-point-policy-addendum) binds the accepted numeric, range and live-state domains; the [independent supplement review](../reports/m2-acceptance/fp-policy-review/report.json) rehashes 536 identities, checks 23,904 numerical records and replays 174 late exclusions. General x87 and arbitrary exceptional inputs remain rejected. |
| M2-03 | Complete within tested domain | The two authored range profiles pass 3,840 original and 7,680 O0/O2 native observations across 40 magnitude pairs, four signs and all 12 modes. Exact output/full memory/CPU/CW/DE/OE/UE/PE/C1/tag results include signed tiny zero, overflow infinity versus maximum finite, and discriminating tininess boundaries. The 91-file failing baseline preserves 3,072 DE-only losses; a two-site sticky-DE repair and guest MXCSR isolation now pass. Evidence: [range experiment](x87-range-experiment.md), [independent verification](../reports/x87-range/independent-review/independent-verification.json), [separate review](../reports/x87-range/independent-review/read-only-review-summary.json). |
| M2-04 | Complete within bounded live-state domain | The [state contract](x87-state-contract.md) and [experiment](x87-state-experiment.md) define canonical raw80, physical occupancy/full tags, all TOP rotations, contiguous and selected noncontiguous states, push/pop/exchange/free and masked stack faults with sticky seeds. Actual hardware and compiled O0/O2 State captures match all 41,472 records. Separate [logical oracle](../reports/x87-state/independent-review/logical-oracle-summary.json) and [physical/replay review](../reports/x87-state/independent-review/adapter-review/final-pins.json) accept the defined registers/status/tags, 12 byte-identical worker replays, 3,288 fresh selfchecks and explicit excluded payload/condition-code policy. |
| M2-05 | Complete within bounded admitted policy | The frozen [floating-point policy](m2-floating-point-policy.md), [fresh supplement review](../reports/m2-acceptance/fp-policy-review/report.json) and [separate final state addendum](m2-acceptance.md#floating-point-policy-addendum) consolidate defined versus unobserved/undefined bits, exact payloads, sticky exception accumulation, masked faults and tested exclusions. 174 fresh actual worker runs reject unsafe conversions, two/unlisted NaNs, unmasked CWs and changed clearing/instruction sequences before output. Guest clearing, unmasked delivery, arbitrary state/inputs and unsupported instructions remain denied. Historical policy pending markers are resolved for milestone acceptance by the separately accepted state bindings without editing frozen evidence or granting general execution. |
| M2-06 | Complete within bounded authored ABI | The [boundary extension](m2-boundary-extension-contract.md) executes a caller that pushes its argument and poisons EAX, followed by a generated callee load from the actual stack frame and RET4. Original/O0/O2 full CPU, flags, return traces, globals and both pages match in 4,592 controlled cases. The [root review](../reports/m2-boundary-extension/root-review/report.json) independently checks 13,776 controlled records and 24 live records, all linked/source/PE identities, 15 reviewer corruptions and fresh compiled context/storage controls. Caller-cleaned indirect frames and explicit original/replacement routing remain covered. |
| M2-07 | Complete within bounded authored integration | The [call integration](m2-call-integration-contract.md) and [root review](../reports/m2-integration/root-review/report.json) validate explicit guest32 global layouts, initialization, global/IAT reads and writes, complete two-page effects, permission and bounds/wrap rejection. Host code pointers remain in the registry. A general loader/global recovery remains a later game-slice task. |
| M2-08 | Complete within bounded synchronous import contract | The [boundary extension](m2-boundary-extension-contract.md) binds the actual MW3 WINMM.timeGetTime IAT and two static CALL identities. A frozen private deterministic/live provider executes through the same selected guest bridge/context, with exactly one actual provider and bridge call per record. Eight live calls in each original/O0/O2 worker pass full state/page/return and DWORD progress checks; provider architecture and the actual linked original shim are bound. The [root review](../reports/m2-boundary-extension/root-review/report.json) independently accepts those 24 live and 13,776 controlled records. No host64 code pointer enters guest data. This establishes provider/ABI integration, not original-game reachability or timing fidelity. |
| M2-09 | Complete within bounded authored integration | The [call integration](m2-call-integration-contract.md) and [root review](../reports/m2-integration/root-review/report.json) execute both admitted indirect targets and reject invalid/unregistered targets and continuations with guest PC/target diagnostics. Guest integers are resolved through a frozen registry, never cast to host function pointers. Unbounded dispatch remains rejected. |
| M2-10 | Complete within bounded authored integration | The [call integration](m2-call-integration-contract.md) and [root review](../reports/m2-integration/root-review/report.json) validate hash/address registration, default generated routes, selected replacement/original routing without recursion, direct/indirect selection controls, conflicts and mutation after freezing. This is an isolated authored registry, not a whole-game replacement runtime. |
| M2-11 | Complete for static planning; execution denied | The [next-slice context](m2-next-slice-context.md) selects the complete 43-byte sub_00558290 after reviewing the full timer wrapper and rejecting its unresolved dependencies for execution. The [root review](../reports/m2-slice-admission/root-review/report.json) independently reparses the actual PE/function, RET8, two stack reads, five globals and incoming CALL; verifies 15 frozen files and runs six asset-free admission groups plus five reviewer corruptions. Register/subregister/flag, live80/TOP/tag, stack, memory/global/import, host ABI and frozen routing contracts are explicit. Unsupported callbacks/SEH/TLS/threading are rejected. M3 must still supply exact translation and live AF/CPU/full-memory preservation validation; this admission layer always rejects execution and makes no native game-function claim. |
| M2-12 | Complete within full M2 acceptance | Re-run the accepted M2 corpus and meaningful negative controls at O0/O2, independently reparse saved results, verify source/tool/contract/artifact/worker identities, preserve all preceding failures, and replay the earlier accepted gates. Run the ordinary checks appropriate to changed project code. The [final acceptance record](m2-acceptance.md), [fresh ordinary checks](../reports/m2-acceptance/ordinary-checks/report.json), [15 G1/G2 worker replays](../reports/m2-acceptance/prior-gates-replay/report.json), separate objective audit and root decision accept every checklist item. Eight ordinary groups run with LLVM opt-in and no skips; 171,555 integer records and 49,812 earlier x87/integration replay records remain byte-identical. All prior failure evidence is unchanged. |

Completion boxes for mandatory work:

- [x] M2-01: bounded control-word evidence accepted.
- [x] M2-02: all floating-point domains required by the consolidated bounded contract accepted.
- [x] M2-03: bounded range and denormal evidence accepted.
- [x] M2-04: bounded live extended state, stack and tags accepted.
- [x] M2-05: defined/undefined and exception/unsupported policies accepted.
- [x] M2-06: bounded direct-call ABI comparison accepted.
- [x] M2-07: bounded global-data comparison accepted.
- [x] M2-08: bounded observed import/provider bridge accepted.
- [x] M2-09: bounded indirect dispatch accepted.
- [x] M2-10: bounded generated/replacement/original routing accepted.
- [x] M2-11: reviewed next-slice guest state and dependency planning accepted; execution remains denied.
- [x] M2-12: integrated evidence and final full M2 review accepted.

## Audit of implementation and tests

The runtime currently builds `memory/guest_memory.cpp` only.
[Its documented contract](../runtime/README.md) covers checked byte-backed memory,
32-bit addresses, little-endian scalar serialization, permissions and failed
write atomicity. `tests/runtime_tests.cpp` tests those bounds and permissions.
The runtime explicitly has no general guest state, loader, calling ABI,
exception translation, function registry or indirect dispatcher.
[The Win32 boundary](../runtime/win32/README.md) has no implemented import APIs.
Those foundations alone cannot be credited as M2-06 through M2-11 evidence.
The separate frozen `tools/m2-integration` prototype now supplies the bounded
global/indirect/routing evidence listed above; it leaves the earlier runtime and
its source identities unchanged.

The frozen standalone lifting/x87 workers have pinned Remill State layouts and
tested harness-specific ABI/memory/FP bridges. They establish their admitted
fixtures, not a reusable game execution context or dispatch policy. The existing
in-game authored x86 hook and native x64 leaf proof remain separate M1 results;
neither proves native multi-function routing or a native Win32 import bridge.

The top-level CMake currently registers eight ordinary CTest groups: runtime,
binary tools, asset tools, in-game hook evidence, monitor, invalid monitor handles, MW3
comparison controls and host-adapter controls. Heavy x87 worker recipes and
native toolchain-dependent comparisons are separate opt-in experiments. Tests
for new runtime/state/routing code must remain usable without proprietary input;
game-specific evidence remains an explicit local admission path, never a
missing-input pass.

The existing floating-point evidence now includes the admitted binary64
denormal/range and live80 stack/tag cases. It still excludes arbitrary live
encodings/states, two-NaN selection, unmasked guest traps and exceptional-exit
pointer restoration. Normal-return host FP restoration and bounded Windows
exception-dispatch control tests are recorded, but they are not guest SEH or
guest trap implementations. The accepted M2-05 policy and final addendum state
which domains are measured and which remain rejected for the next-slice context.

## Execution order and acceptance discipline

1. Preserve the accepted range/denormal gate and its exact exception/status policy.
2. Complete the live-stack/tag and remaining required floating-point policies.
   Keep unsupported guest traps and instruction/state families explicit.
3. Extend the bounded call context to prove stack-argument consumption independently
   from EAX while retaining accepted global-data evidence.
4. Exercise the observed import's real provider through the selected bridge/context,
   retaining accepted indirect and generated/replacement/original routing evidence.
5. Review a dependency-bounded next MW3 slice and finish the integrated M2
   acceptance record. Only that review can close M2 and hand off to M3.

Every accepted item needs its contract, original bytes or private admitted slice
identity, initialized state/memory, generated static native path, exact defined
observations, meaningful rejection/corruption controls, saved outcomes, exact
source/tool/artifact identities and replay recipe. Preserve old authored sources,
tool binaries, failure reports and successful measurements. New failures stay
distinct from new repairs. No interpreter/JIT fallback, fast-math substitution,
expected-result observer computation or fake-success API path satisfies a gate.

This checklist may be updated as new evidence arrives. Completed entries must
link that evidence; planned implementation or a passing smaller probe cannot
close an enclosing requirement.
