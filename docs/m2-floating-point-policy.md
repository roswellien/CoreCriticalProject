# M2 admitted floating-point and status policy

Established 2026-10-07. This document consolidates the frozen bounded x87
contracts and supplementary pre-entry exclusions required by M2-05. Numerical
acceptance applies only to the exact sequences, raw inputs, control words and
entry states below. **Consolidated M2 acceptance remains pending the final
live-state repair evidence and independent review.** No native game execution
or general x87 compatibility follows from this policy.

The asset-free [profile admission policy](../tools/m2-fp-policy/policy.py)
recognizes these domains for planning and always returns
`general_execution_allowed=false`. Actual execution is restricted to each
frozen worker's own hash-admitted fixture, corpus, ABI and memory contract.
Unknown instruction sequences, inputs and dependencies reject before entry.

## Control words, precision and rounding

Every admitted CW is `0x007F | (PC << 8) | (RC << 10)`, with PC0/2/3 and RC0..3.
All six exception masks are set. PC1, other bits and every unmasked CW reject.

| Significand precision | Nearest even | Down | Up | Toward zero |
| --- | --- | --- | --- | --- |
| PC24 | 007F | 047F | 087F | 0C7F |
| PC53 | 027F | 067F | 0A7F | 0E7F |
| PC64 | 037F | 077F | 0B7F | 0F7F |

FADD/FSUB/FMUL/FDIV round their arithmetic result at PC/RC. FLD preserves the
loaded format's value without a preliminary PC clamp. FSTP rounds to its
destination width at RC; FISTP rounds to an integer at RC. PC53 and PC64 may
produce different binary64 results because the arithmetic rounding precedes
the store rounding. Exact halfway rounding uses even significands or integers.
Each numerical oracle uses exact integer/rational arithmetic and exact bit
comparisons, without epsilon or a measured-result substitute.

The [control repair contract](x87-repair-contract.md) admits `FNSTCW m16; RET`
(`D939C3`, 12 cases) and `FLDCW m16; FNSTCW m16; RET` (`D929D93AC3`, all 144
transitions). These validate stored and resulting CW, CPU and complete memory.
They do not establish arithmetic or undefined condition-code equivalence.
The preceding Remill precision-clamp failure stays preserved separately from
the repaired control results.

## Exact numerical profiles

The [authored domain manifest](../tools/m2-fp-policy/profiles.json) contains
every permitted raw binary64 pair. Its SHA256 is
`d6488bfec316d20949a89bb7ed87350fc182a76d2a76b4ac9737134ddcfe5fb8`.
Opcode recognition alone never admits arbitrary operands or an enlarged CFG.
All listed numerical profiles enter with clean status and empty x87 stack;
their balanced sequences end with TOP0 and physical abridged FTW0.

| Profile | Complete sequence before RET | Bytes including RET | Cases | SW mask | Strongest evidence |
| --- | --- | --- | --- | --- | --- |
| numeric-add-sub | FLD m64; FADD m64; FSUB m64; FSTP m64 | DD01DC4108DC21DD1AC3 | 240 | 38FF | [numeric contract](x87-numeric-contract.md) |
| spill64 | FLD m64; FADD m64; FSTP m64 spill; FLD spill; FSUB m64; FSTP m64 | DD01DC4108DD5A08DD4208DC21DD1AC3 | 240 | 38FF | [C1 regression contract](x87-c1-contract.md) |
| fistp32 | FLD m64; FISTP m32int | DD01DB1AC3 | 384 | 3AFF | [conversion C1](x87-c1-contract.md) |
| mul64 | FLD m64; FMUL m64; FSTP m64 | DD01DC4908DD1AC3 | 1152 | 3AFF | [store C1](x87-store-c1-contract.md) |
| div64 | FLD m64; FDIV m64; FSTP m64 | DD01DC7108DD1AC3 | 1152 | 3AFF | [store C1](x87-store-c1-contract.md) |
| mul-special | multiplication sequence above | DD01DC4908DD1AC3 | 480 | 3AFF | [store C1](x87-store-c1-contract.md) |
| div-special | division sequence above | DD01DC7108DD1AC3 | 480 | 3AFF | [store C1](x87-store-c1-contract.md) |
| mul-range | multiplication sequence above | DD01DC4908DD1AC3 | 1920 | 3AFF | [range contract](x87-range-contract.md) |
| div-range | division sequence above | DD01DC7108DD1AC3 | 1920 | 3AFF | [range contract](x87-range-contract.md) |

Arithmetic memory operands retain the exact addressing in the fixture:
FLD reads ECX, FADD/FMUL/FDIV read ECX+8, the subtraction reads ECX, final
stores use EDX, and the explicit spill uses EDX+8. Division is the loaded
first operand divided by the second memory operand. Authored entry is
0x10000000 with return sentinel0x10000100. Each contract requires checked
guest32 spans, disjoint operands/output/frame, unchanged integer CPU except
ESP+4 and return EIP, unchanged observed integer flags0xCD5, and exact full
4096-byte page effects. These profiles are whole-function measurements.

The cancellation and spill domains are base +/-1 and both signs of
2^-30, 2^-54, 2^-24, 2^-53 and 2^-64. The spill oracle includes explicit
binary64 store/reload rounding before subtraction. Both spill words are
observed. Exact cancellation produces negative zero under round-down and
positive zero otherwise. PE accumulates any admitted inexact arithmetic or
store stage; final condition codes are excluded for these two profiles.

Finite mul64/div64 use the exact 24 magnitude pairs expanded across four sign
pairs and twelve CWs. Operands and outputs are nonzero normal binary64 in
this profile. Range profiles separately use 40 magnitude pairs, four sign
pairs and twelve CWs. Admission never combines or interpolates these lists.

## Conversion and final-store status

FISTP32 admits exactly the 32 listed finite input encodings, including signed
zero, ties, fractions and representable signed32 endpoints. Its unused second
operand is zero. Every admitted input rounds to representable signed32 under
every RC. FISTP uses the fully loaded value rather than clamping it to PC.
The stored integer loses a zero sign as required by that integer format.

For admitted conversion x to integer r, PE is set iff r differs from x and
`C1 = abs(r) > abs(x)`. C1 records the final operation's significand-magnitude
increment; it does not accumulate. For example -0.75 rounded to -1 sets C1.
Out-of-range or huge finite values, infinities, QNaNs, SNaNs, subnormals and
all unlisted encodings reject before entry. There is no claim for a masked
invalid conversion storing integer indefinite0x80000000 or its C1 behavior.

For finite final binary64 stores, A is the full PC/RC-rounded arithmetic
value and S the destination-rounded value. Final-store C1 is
`abs(S) > abs(A)`. Earlier PE can remain set while an exact final store clears
C1. The selected masked zero, infinity, single-NaN and indefinite stores
clear C1. The earlier C1-only failures are retained under their stronger
status masks; the latest passing evidence does not rewrite them.

## Signed zero, infinity and selected NaNs

Special profiles admit the four sign variants of (0,1), (1,0), (0,0),
(0,infinity), (infinity,0), (infinity,1), (1,infinity), (infinity,infinity),
then each of these exact single NaNs paired with positive1 in either position:

`7FF8000000001234`, `FFF8000000004321`, `7FF0000000001234`, `FFF0000000004321`.

The first two are quiet, the last two signaling. A single QNaN propagates
its full payload and sign without IE. A single SNaN sets IE and quiet bit51
while retaining the selected source sign and remaining payload. The load's
IE must survive a subsequent operation. Two-NaN selection/ties, every unlisted
payload or sign/payload combination, and arbitrary NaNs reject before entry.

Admitted signed zero/infinity results use XOR of operand signs. Zero times
infinity, zero divided by zero, and infinity divided by infinity produce
binary64 floating indefinite `FFF8000000000000` and IE. Finite nonzero divided
by zero sets ZE. Infinity divided by zero returns infinity without ZE.
The remaining admitted zero/infinity pairs raise no exception. No payload
equivalence is replaced by mere NaN classification. The preserved right-SNaN
IE and final-store C1 failures remain separate historical evidence.

## Denormals, range and sticky exceptions

Only the exact range vectors admit binary64 subnormal operands and range
boundaries. Their extended arithmetic intermediates remain normal. The
classification of a raw subnormal source sets sticky guest DE. Arithmetic
and final-store classification OR newly observed DE with the previous guest
DE; neither assignment may erase it.

Masked overflow sets OE and PE. Nearest and directed rounding away from zero
produce signed infinity with C1 set; the other directions produce signed
maximum finite with C1 clear. Store underflow sets UE only when the value is
tiny under the contract's discriminating rounding-boundary policy and the
store is inexact. Exact subnormal output does not set UE; an earlier arithmetic
PE alone does not manufacture store UE. Signed tiny zero retains the XOR sign.
The independently measured min-normal boundary and exact rational oracle in
the range contract govern tininess; this policy makes no general extended
register range claim. Host DAZ/FTZ must not alter these guest observations.

IE/DE/ZE/OE/UE/PE accumulate across the admitted numerical sequence. SF remains
clear in the empty-entry numerical domains. ES remains clear for these fully
masked states. C1 is an operation result rather than a sticky exception bit.
The live-state extension additionally tests seeded DE+PE and IE+SF+C1, but
its integrated acceptance remains pending below. Arbitrary nonclean numerical
entry status is rejected, so these numerical probes do not establish every
possible sticky combination.

## Defined observations and excluded state

SW mask38FF observes exception bits0..5, SF6, ES7 and TOP11..13. Mask3AFF
adds C1 bit9. C0 bit8, C2 bit10, C3 bit14 and busy15 are excluded from these
numerical observations. Raw SW remains saved; excluded bits do not become
zero expectations. Spill and cancellation exclude C1. FISTP and the latest
store/range gates include it. Their original stronger-mask baselines stay
unchanged. A previous weaker-mask pass cannot establish a stronger bit.

Control probes exclude instruction-undefined condition codes and claim CW
only for their FP boundary. All numerical cases observe CW before/after,
empty physical tags, TOP and status under their declared masks. They do not
observe live register payloads or undefined empty payloads.

The pending [live-state contract](x87-state-contract.md) separately specifies
four exact fixtures: FLD m80 (`DB29C3`), FSTP m80 (`DB3AC3`), FXCH ST1
(`D9C9C3`) and FFREE ST1 (`DDC1C3`). Each admits3456 exact states, including
all TOPs, contiguous depths, noncontiguous logical mask02, and sticky seeds.
Logical ST(i) maps to physical(TOP+i)&7; physical FTW and full two-bit tags
must agree with actual occupied ten-byte values. Full tags are normal00,
zero01, special10 and empty11. Only empty payload numerical equality is excluded.

The narrowed raw80 domain comprises listed canonical normals with significant
low64 bits, signed zeros/infinities and selected quiet NaNs. Extended SNaNs,
subnormals, pseudo-denormals, unnormal/unsupported encodings and arbitrary
raw80 patterns reject. Masked stack overflow/underflow uses exact indefinite
`00000000000000C0FFFF`; raw80 transport must not lose precision or quiet a
listed QNaN. Push checks the new physical slot, pop clears old TOP, FXCH
replaces missing operands before exchange, and FFREE clears ST1 occupancy.
Existing exception flags/SF stay sticky. Entry C1 is observed for every
profile under3AFF; free exit uses38FF because its condition codes are undefined.

The immutable [canonical live-state failure archive](../reports/x87-state/baseline-failure/report.json)
contains13,824 matching originals and22,272 failures among27,648 native
observations. Its report SHA256 is
`7b0c935743991ecef15174d7c3d343852a772d63e0fc6d52a2cecf3198c88f11`,
manifest SHA256
`21d69c5a0539ba6166a8e49e3101b906dc9b66d5776371437a5b54073991c048`.
These are incompatibilities. Design-helper tests and a research archive
cannot substitute for integrated original/O0/O2 acceptance. Profile admission
currently emits `pending_live_state_final_acceptance` for all four live forms.

## Host isolation and rejected execution paths

The frozen arithmetic workers save/restore the host FP environment on the
tested normal returns and maintain separate guest State. Ten-byte pointer
storage/internal LLVM values avoid the Windows scalar long-double ABI.
No scalar80 C bridge truncation, fast-math, JIT/interpreter fallback or
expected-result observer is admitted. Final observer fields come from actual
State or original hardware; native FX/env arrays are declared synthetic
serialization when used for State snapshots.

Range workers set guest MXCSR0x1F80 within the saved host scope and restore
the complete host FXSAVE64 environment. Each native level checks384 combinations
of host DAZ/FTZ/rounding, guest CW and left/right subnormal positions. Earlier
normal-return environment checks have their own frozen scope. Exceptional-exit
FIP/FDP equivalence/restoration, guest SEH, callbacks, concurrent mutation,
TLS/FS state, MMX/SSE instruction semantics and unmasked guest trap delivery
remain unsupported. A host exception-dispatch control does not implement
guest exceptions.

Guest FNCLEX, FNINIT, FWAIT and guest status-clearing/trap sequences are
excluded. Harness FNINIT/FNCLEX and per-operation host exception collection
occur outside the guest fixture; they establish neither guest clearing nor
trap semantics. Planning rejects guest-clear, guest-trap, exceptional-exit,
unknown sequence and nonclean numerical entry requests. Clearing can become
supported only after a new exact state/status gate; unmasked traps additionally
need an explicit delivery/control-flow contract and measured implementation.

The next real MW3 slice is governed by [its separate context contract](m2-next-slice-context.md).
Its planning layer denies execution until exact translation and flags/state
preservation are accepted. The enclosing timer dependency's FILD64, FMUL32,
FSTP64 sequence is not admitted by these superficially related fixtures.
Unknown forms or mixed sequences hard-reject; no fake API/body return closes
a missing dependency.

## Supplementary evidence and remaining acceptance

The new [worker exclusions](../reports/m2-fp-policy/worker-exclusions.json)
execute the frozen FISTP32, mul-special and div-special original/O0/O2 workers.
Nine positive full-corpus replays match all4,032 prior raw records byte-for-byte.
174 negative runs reject unsafe conversions, two/unlisted NaNs, every individual
unmasked exception bit, reserved PC, and fixture prefixes FNCLEX/FNINIT/FILD64.
Every operand/CW mutation changes only the last record of a valid complete
corpus; all earlier records/header/count/extent remain valid. Rejection is
exit1 with the expected diagnostic and zero output bytes. This demonstrates
whole-input pre-entry admission, rather than a partially emitted corpus.

The [planning controls](../reports/m2-fp-policy/planning-controls.json) cover
all8,124 listed mode/vector/control cases,186 rejected admission calls and a
separate domain-identity corruption. All execution remains denied by this
planning API. [The reproduction instructions](../tools/m2-fp-policy/README.md)
and final pins bind new sources, input/fixture mutations, positive outputs,
worker/source/tool identities and the unchanged frozen acceptance reports.

Completion of M2-05 requires accepting this bounded policy and its exclusions,
then binding the final passing live-state repair and separate saved-record
review. M2-02/04 and the enclosing M2 acceptance stay open until those required
fields pass. Existing excluded behavior stays rejected for the selected
next slice; supporting a larger game dependency requires a new exact gate.
