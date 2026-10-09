# Bounded live x87 register-stack contract

Established 2026-10-07. This new offline gate observes a live x87 stack before
and after one admitted instruction. It extends the previous empty-stack
arithmetic gates without modifying their sources or evidence. It is one part
of CPU/ABI Milestone 2, not native game integration or a complete x87 policy.

## Instructions and admitted entry states

Four complete authored fixtures execute at0x10000000 and return to0x10000100:

| Profile | Bytes | Instruction before RET |
| --- | --- | --- |
| push | DB29C3 | FLD tbyte [ECX] |
| pop | DB3AC3 | FSTP tbyte [EDX] |
| exchange | D9C9C3 | FXCH ST(1) |
| free | DDC1C3 | FFREE ST(1) |

Each profile admits3456 states. The main1728 states cross nine contiguous
logical occupancies of depth0..8, eight TOP values, twelve masked CWs and two
raw80 patterns. CW is0x007F|(PC<<8)|(RC<<10), PC0/2/3 and RC0..3. Another1728
states cross the same TOP/CW/pattern values with nine directed logical-mask
and initial-status pairs: mask02 with SW0,22,241; and masks00,01,FF with
SW22 and241. These hexadecimal status seeds represent clean entry, sticky
DE+PE, and sticky IE+SF+C1. TOP is supplied separately and merged into SW.
ES and busy are clear; all exceptions are masked.

Logical ST(i) maps to physical register(TOP+i)&7. Physical abridged FTW is
derived from logical occupancy under that mapping, not from stack depth alone.
Mask02 specifically admits empty ST0 with occupied ST1, which discriminates
masked FXCH direction and tag handling.

Pattern0 has distinct signed canonical normal values with nonzero low64
significand bits. Significands in logical order are8000000000000001,
9000000000000003,A000000000000005,B000000000000007,C000000000000009,
D00000000000000B,E00000000000000D,F00000000000000F; sign/exponent words
are3FFF,BFFF,4000,C000,4001,C001,3FFE,BFFE. Its input is significand
8000000000000055 and sign/exponent4002. Pattern1 contains positive and
negative zero, positive and negative infinity, then four signed quiet NaNs
with low payload words1234,4321,5678,ABCD. The latter two significands also
retain their authored high payload bits. Its input is positive quiet NaN
payloadBEEF.
All encodings use the explicit integer bit where required. Request bytes
must match the fixed pattern exactly, including payload bytes in empty slots.

Extended signaling NaNs, subnormals, pseudo-denormals, unsupported encodings,
other values or occupancies and unmasked states are rejected before execution.
Their semantics remain a separate policy requirement.

## Independent transition oracle

Use integer byte operations and physical/logical tag mapping. No host
floating conversion, native observation or original result supplies an
expected value. The full ten bytes of every occupied value are compared.
Payloads in registers tagged empty are retained in raw evidence but excluded
from numerical equivalence; occupancy and both tag forms remain observed.

Push decrements TOP modulo8 and writes the input into the new ST0. If that
physical slot was occupied, masked stack overflow writes extended indefinite
(sign/exponentFFFF, significandC000000000000000), sets IE and SF, and sets C1.
Otherwise it copies the raw input and clears C1. Other occupied physical
values are unchanged. Pop writes the original ST0, marks its physical slot
empty, and increments TOP. Empty ST0 produces indefinite in memory, sets IE
and SF, and clears C1. Successful raw80 stores copy all ten bytes without
precision reduction; the bounded original measurement must verify C1 clear.

Exchange first replaces any empty operand with indefinite and marks it
occupied, then exchanges ST0 and ST1. A missing operand sets IE and SF; C1
is cleared. Free marks ST1's physical tag empty without changing TOP or
other occupied payloads. It does not generate a floating exception.
Preexisting exception flags and SF remain sticky in all profiles.

These masked stack responses and the FXCH replacement-before-exchange rule
follow [Intel SDM Volume1, section8.5.1 and Table8-10](https://cdrdv2-public.intel.com/843827/253665-sdm-vol-1-dec-24.pdf#page=228).
The instruction definitions are [FLD](https://cdrdv2-public.intel.com/812383/253666-sdm-vol-2a.pdf#page=513),
[FST/FSTP](https://cdrdv2-public.intel.com/812383/253666-sdm-vol-2a.pdf#page=547),
[FXCH](https://cdrdv2-public.intel.com/812383/253666-sdm-vol-2a.pdf#page=567)
and [FFREE](https://cdrdv2-public.intel.com/812383/253666-sdm-vol-2a.pdf#page=500).

Observe entry SW mask0x3AFF for every profile because entry C1 is controlled.
Exit uses0x3AFF for push, pop and exchange; free uses0x38FF because its
condition codes are undefined. All exception bits, SF, ES and TOP remain
observed for free. The preserved initial probe's historical free mask stays
0x38FF at both ends; its correct entry C1 is checked separately by this new
gate. C0/C2/C3/B are excluded in every profile. Full tags are physical two-bit fields: valid00, zero01,
special10 and empty11. They must agree with occupied raw80 classification
and physical FTW. See [Intel FXSAVE tag reconstruction](https://cdrdv2-public.intel.com/812383/253666-sdm-vol-2a.pdf#page=575).

## CPU, page and measurement protocol

Header24 retains MW34REQ1/MW34RES1, v1 and explicit count/record-size/pointer
width. Request156 consists of CPU40, six uint32 fields(CW, memory seed, TOP,
physical FTW, initial SW, pattern), eight logical raw80 values, input raw80,
and two reserved zero bytes. Result5416 consists of CPU40, worker status4,
full page4096; eight uint32 CW/SW/FTW/full-tag before/after fields; eight
before and eight after logical raw80 values; two raw512-byte FXSAVE images;
two raw28-byte FNSTENV images; and a uint32 host-restored indicator.

The4096-byte guest page begins at0x20001000. Initial bytes are(37*i+seed)&255.
Frame12 at ESP holds return sentinel, CW and seed. Input10 at ECX and
output10 at EDX must fit and avoid the frame and each other, even when unused
by a profile. Push reads input without guest writes; pop writes only output10;
exchange and free leave the complete page unchanged. Vary every GPR, observed
integer flag, DF, alignment and page margin. Expected CPU preserves GPRs
except ESP+4 and EIP at the sentinel; observed flags0xCD5 are unchanged and
worker status is0.

Original entry and exit state comes directly from FXRSTOR/FXSAVE; FNSTENV
records full tags outside guest memory after the FX capture. The original
worker has no transition oracle. Every observed scalar and occupied payload
must agree with the corresponding raw capture. Native snapshots reflect the
actual State values; native FX/env arrays serialize these observations rather
than claiming to be hardware guest snapshots. Raw FIP/FDP/opcode, XMM, reserved capture bytes and empty
payloads are saved but do not acquire a cross-mode equality claim here. Host
restoration is required independently of guest stack correctness.

## Evidence and completion

Before executing a worker, admit exact authored code, complete entry corpus,
source/contract/tool identities, reviewed guest IR, State ABI, adapter policy,
generated artifacts and worker hashes. Bind the previous immutable range
gate and its historical failure archives without reinterpreting their masks
or inputs. Retain any initial discrepancy with its original sources,
binaries and raw records before a repair. Comparator, protocol, unsafe-state,
metadata and semantic negative controls must reject meaningful corruption.

The preserved initial `semantic_stage=unrepaired` build admits the exact preceding
lifted instructions with `status_lowerings={}`. It declares separate memory,
FP-environment, MXCSR-isolation and adapter-mutation checks as0; these are
not completed checks. Three object-symbol rejection checks per native level
remain required. Actual record snapshots still require host-restored1.
Canonical initial failures and their complete source/artifact/worker binding
must be archived before a semantic repair changes this stage. A later repair
requires a separately reviewed exact adapter policy and a new source binding.

The immutable canonical archive is `reports/x87-state/baseline-failure`.
Its1,137 snapshots preserve complete authored sources, generated IR/objects,
all twelve exact worker images, request/result records and negative controls.
An independent logical-rotation oracle confirmed13,824 original matches and
exactly22,272 failing cases among27,648 initial native measurements; every
native entry state was correct. The new repaired gate requires
`state_baseline_path`/`state_baseline_sha256`, rehashes every snapshot and
reproduces each failure's field/index list under the original masks. Its
`state_baseline_proof` retains that failed gate rather than relabeling it.
The earlier80-file preliminary probe and separate reviewer remain bound
as historical evidence.

The repaired stage uses reviewed internal, always-inline LLVM helpers that
read actual guest State tags/TOP and actual loaded raw80 bytes. They update
physical occupancy and sticky IE/SF/C1, replace empty operands with indefinite
before the instruction's existing raw moves, and clear tags on pop/free.
Pop additionally ORs the prior shadow DE into its existing classification
assignment. The helpers have no request, case index, expected-result table
or native observation access. They do not add external bridges or calculate
floating arithmetic. The native observer and numerical transition oracle
remain independent of these helpers.

Admit the exact approved helper-source SHA256
`77fbd3b2f13fa25f0401c48c39551a776f771670666b8a43964bb4868b71804e`.
The adapter policy `raw80_physical_tags_masked_stack_faults_sticky_de` binds
normalized generated helper-body hashes, exactly one entry-helper call at
the reviewed insertion site and one sticky-DE site only for pop. The
comparator checks the actual generated host IR independently; missing,
duplicate, moved or altered helpers and loss of sticky DE are rejected.
Comparator/layout corruptions supplement separately executed adapter input
mutations, raw80 memory-boundary checks, FP restoration and host MXCSR
isolation checks recorded by the final build recipe. Host DAZ/FTZ/rounding
configuration must not change the admitted guest observations; the saved
host environment is restored on return.

Completion requires13824 original matches and27648 O0/O2 native matches,
zero differences in every declared CPU/page/CW/status/tag/occupied-payload
field, full source/evidence binding, and a separate saved-record oracle.
Additional instructions, arbitrary raw80 states, extended signaling or
denormal policy, unmasked exceptions, FIP/FDP equivalence, import/call routing
and a native game subsystem remain outside this gate's completion claim.
