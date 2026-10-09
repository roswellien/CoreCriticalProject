# Bounded binary64 x87 operand and result range contract

Established 2026-10-07. This separate offline gate extends multiplication and
division to listed subnormal operands and binary64 store range limits. It is
progress toward CPU/ABI Milestone 2; it does not redefine that milestone or
prove native game integration. Every earlier source, contract and evidence
record remains frozen.

## Authored fixtures and admitted matrix

Entry is `0x10000000`, return sentinel `0x10000100`. The two complete fixtures
are `DD01DC4908DD1AC3` (FLD qword [ECX]; FMUL qword [ECX+8]; FSTP qword [EDX];
RET) and `DD01DC7108DD1AC3` (the same sequence with FDIV). Profiles are `mul64`
and `div64`; division is the first operand divided by the second.

Use exactly forty positive raw magnitude pairs in the public comparator's
`RANGE_MAGNITUDES` and reference protocol's `range_magnitude_pairs`. Expand
each pair with signs ++, +-, -+, -- in that order, then cross with twelve CWs
`0x007F | (PC << 8) | (RC << 10)`, PC0/2/3 and RC0/1/2/3. Each profile has
160 signed vectors and 1920 cases. Reject every other code sequence, mode,
vector, duplicate, count or unsafe memory extent.

The matrix includes smallest and largest binary64 subnormals in both operand
positions, minimum normal values, subnormal half/tie cases, normal/subnormal
boundary products, maximum finite values, overflow to infinity or saturation,
very small nonzero values rounded to signed zero, and previously discriminating
two-stage precision cases. Inputs are finite and nonzero. The exact multiply
and divide results remain normal within the extended-format exponent range;
the range exceptions studied here arise at the final binary64 store, while
denormal-operand exceptions arise at the binary64 load or memory operand.

Index37 is `(0x0018000000000000, 0x3fe5555555555555)`. Its multiplication is
minimum-normal minus one quarter of the minimum subnormal quantum. PC64 can
retain the tiny input while a nearest binary64 store rounds to minimum normal.
This case discriminates store tininess policies. The original measurements confirm this destination-precision tininess
policy. Preserve raw observations; changing the status mask to hide a
boundary disagreement is prohibited.

## Independent exact result and status expectations

Decode raw binary64 inputs with integer/rational arithmetic. Do not use host
floating calculations, epsilon or hardware results as expected-value input.
Round the exact arithmetic result to PC24/53/64 under RC nearest-even, down,
up or zero. Then round that full value directly onto the binary64 destination
grid: normal spacing follows its binade; subnormal spacing is fixed at 2^-1074.
Zero from underflow keeps the XOR of operand signs. Do not flush subnormal
operands or outputs to zero. Record both rounding stages and raw output bits.

DE is sticky when either admitted raw source is subnormal. A masked load
normalizes the value into extended format without discarding its magnitude.
See [Intel SDM Volume 1, section8.5.2](https://cdrdv2-public.intel.com/843827/253665-sdm-vol-1-dec-24.pdf#page=230).

The accepted rational oracle checks overflow against the result rounded at destination
precision with an unbounded exponent. A magnitude at or above 2^1024 is
overflow. Masked overflow returns signed infinity for nearest or rounding
away from zero, and signed largest-finite for the other directed modes;
OE and PE are set. Final C1 is one for infinity and zero for saturation.

The accepted tininess test follows the destination-precision result with
unbounded exponent: nonzero magnitude below 2^-1022 is tiny. Masked UE is
set only if that store is inexact as well; sticky arithmetic PE alone must
not manufacture store UE. Exact subnormal stores do not raise masked UE.
PE is sticky across arithmetic and store. All 3840 original x86 measurements match this policy, including index37
and half-quantum boundaries. Independent signed-floor and Fraction oracles
confirm the same full CPU/page/CW/status/tag observations. See [Intel SDM Volume 1,
sections4.9.1.4-4.9.1.6](https://cdrdv2-public.intel.com/843827/253665-sdm-vol-1-dec-24.pdf#page=107).

For a finite destination, C1 is `abs(stored) > abs(full arithmetic result)`;
this tests magnitude increment, including negative values. It is overwritten
by the final FSTP. Observe all exception bits, SF, ES, TOP and C1 using
SW mask0x3AFF at both ends. C0/C2/C3/B stay excluded. Clean entry status and
empty stack must end with TOP0 and empty abridged tags. See [Intel SDM
Volume 2A, FST/FSTP](https://cdrdv2-public.intel.com/812383/253666-sdm-vol-2a.pdf#page=547).

## CPU, memory, protocol and isolation

Retain v1 Header24, Request64 and Result4152. Each request carries eight GPRs,
flags, EIP, CW, memory seed and two raw uint64 operands. Required flags are
0x202, with additional observed bits0xCD5. Input pointer width is32; outputs
identify32 for original execution or64 for native. Strictly validate every
header field and complete byte extent.

Initialize all4096 guest bytes at `0x20001000` with `(37*i+seed)&255`. Frame12
at ESP holds sentinel, CW and seed. Input16 at ECX and output8 at EDX must
fit the page and avoid one another and the return frame. Vary GPRs, flags,
DF, alignment and page margins. Only output8 may change. Full CPU/page
comparison requires unchanged GPRs except ESP+4, EIP at sentinel, observed
flags unchanged, worker status0, CW unchanged, tags empty and reserved field0.
Original CW/SW/tags are captured directly by FXSAVE outside guest memory.

All new writes belong under `reports/x87-range`; copied pipeline profiles
use `x87_range_<kind>`. Before worker execution, bind source, contract, tools,
repair provenance, authored code, admitted guest IR, State3504 ABI, generated
IR/objects/layout, workers and commands. The initial lowering is the exact
preceding store-C1 lowering with the new profile identity. Capture any defect
before changing that lowering, and preserve its sources, binaries and results.

The repaired lowering retains that admitted arithmetic and store model, but
preserves sticky DE at the two existing assignments: the arithmetic result
classification and final-store classification each OR the previous guest DE
with the newly classified value. The recorded `sticky_denormal` policy requires
two sites, State byte2753, operation
`or_previous_shadow_and_new_classification`, and both `arithmetic` and
`final_store` true. It does not infer expected results in the worker or add an
exception classifier. The original promotion-exception and unconditional
final-store C1 policies remain required.

The host scope saves the complete FXSAVE64 environment, sets guest MXCSR to
0x1F80, and restores the saved environment after execution. This disables host
DAZ/FTZ effects on the binary64 classification while preserving request CW
precision and rounding for x87 execution. Each native level must pass384
actual-fixture isolation and restoration checks: sixteen host DAZ/FTZ/rounding
combinations crossed with twelve guest CWs and two left/right subnormal
operand positions. Build metadata requires numeric `guest_mxcsr`8064 and
`mxcsr_isolation_checks_per_native`384, in addition to eight memory-bridge,
fifteen FP-environment and three object-symbol checks per native level. This
does not expand the prior exceptional-exit FIP/FDP restoration claim.

Bind the prior store-C1 final pins under `previous_gate_provenance_path` and
`previous_gate_provenance_sha256`. Retain the historical right-SNaN IE archive
under `initial_failure_provenance_*` and the prior C1 archive under
`c1_baseline_*`, at their original paths. Hash-admit the immutable old authored
validator before importing its archive-only checks. Its original masks and
corpora remain unchanged; never reinterpret historical inputs with this
new range oracle.

Completion requires 3840 original oracle matches and 7680 O0/O2 native
matches, every declared output/status/CPU/page field, meaningful comparator,
admission and metadata negative controls, plus a separate saved-record oracle
review. A failing case remains a failure, with its raw bits and status retained.
Negative controls include missing or spurious DE, lost or false store UE/OE,
incorrect directed overflow or signed zero, the discriminating tininess case,
missing or sticky C1, changed two-site DE policy, and inherited host MXCSR or
missing isolation checks. The status mask and numerical oracle stay identical
before and after the repair.
Arbitrary operands, extended-register range exceptions, other destination
formats, nonempty entry stacks, unmasked exception delivery and full game
compatibility remain unproven by this gate.

## Preserved initial observation

Before any range repair, all 3840 original records match the exact range
contract. Each of four native workers loses DE in 768 cases, totaling3072
DE-only differences. Every other declared CPU/page/CW/status/C1/tag/output
observation matches. Preserve the preliminary observation under
`reports/x87-range/pre-repair-observation`; it is a measurement before final
source binding, not a passing acceptance report. Its original worker paths
were relinked before the six measured executable images were archived; the
preserved records therefore retain a historical worker-identity limitation.

The authoritative initial canonical failure is preserved separately under
`reports/x87-range/baseline-failure`: report SHA256
`f52847eb4f286ae7e6af20835898981a4ef0f8e7823d3eb46e6b803c6a7320fd`,
manifest SHA256
`3c81e9b0f2d2dae1028b0382fde785235041c4e56bdcf64503151f1ccd4fb7c6`.
Its91 archived sources, binaries, generated artifacts and evidence files bind
the canonical pre-repair execution. Every final build must bind this record
with `range_baseline_path` and `range_baseline_sha256`. The comparator rehashes
the complete archive and independently reparses all3840 original and7680
initial native records, requiring exactly3072 DE-only failures and no other
declared differences. The final repair must then pass the unchanged full
contract. No status mask, output oracle or observer may be weakened to accept
the original failures.
