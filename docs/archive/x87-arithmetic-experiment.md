# Bounded x87 multiplication, division and masked special values

Measured 2026-10-07. This separate authored offline gate passes 3,264 original
x86 cases and 6,528 generated Windows x64 O0/O2 comparisons. It also reproduces,
preserves and repairs an exception-capture defect. M2 remains active; these
fixtures do not establish a native game or complete x87 compatibility.

## Contract and measured results

The [contract](x87-arithmetic-contract.md) admits two eight-byte fixtures:
`FLD qword [ECX]; FMUL/FDIV qword [ECX+8]; FSTP qword [EDX]; RET`.
The complete bytes are `dd01dc4908dd1ac3` and `dd01dc7108dd1ac3`.
Only the four named deterministic input profiles are accepted. Each runs all
twelve combinations of PC24/53/64 and nearest/down/up/toward-zero rounding,
with every exception masked and an initially empty x87 stack.

| Profile | Original cases | Native O0/O2 comparisons | Defined mismatches | Rejection controls |
| --- | ---: | ---: | ---: | ---: |
| Finite multiplication | 1,152 | 2,304 | 0 | 196 |
| Finite division | 1,152 | 2,304 | 0 | 197 |
| Multiplication special values | 480 | 960 | 0 | 197 |
| Division special values | 480 | 960 | 0 | 199 |
| Total | 3,264 | 6,528 | 0 | 789 |

Finite operands include exact operations, precision boundaries, both operand
signs, exponent magnitudes up to 2^500, repeating quotients and discriminating
double-rounding cases. The exact rational oracle first rounds arithmetic to
guest PC/RC, then rounds the binary64 store under guest RC. Multiplication has
320 precision-status results per worker; division has 528.

Special profiles admit signed zero, signed one, signed infinity, and a single
positive or negative quiet/signaling NaN in either operand position. Every
stored output bit is compared, including NaN sign, quiet bit and payload.
Each special profile produces 144 zeros, 144 infinities and 192 quiet NaNs;
144 cases set invalid-operation status. Division additionally has 48 finite
divide-by-zero cases. Infinity divided by zero sets no divide-by-zero flag in
this admitted matrix, as independently measured on original hardware.

The comparator observes the full 4,096-byte guest page, integer registers,
defined integer flags, return behavior, control words, final empty tags and
status mask `0x38ff`. C1 from the final FSTP, C0/C2/C3 and B are explicitly
excluded here; this does not broaden the separate finite-conversion C1 proof.
Ten exclusion checks per profile demonstrate that policy. Denormal operands,
range exceptions, two-NaN selection, live stacks and unmasked traps are rejected
or outside the contract.

The saved raw words expose a remaining final-store C1 difference: original
finite multiplication sets it in 32 cases per worker and division in 48, while
the native shadow C1 stays clear. These observations are outside the stated
mask and are not counted as C1 successes. Strengthen that final-FSTP status
contract in a separate preserved gate before broadening numerical coverage.

## Reproduced defect and bounded repair

The initial finite profiles passed, but each special profile had 24 missing
invalid-operation flags at each native optimization level: 96 failures total.
They occurred when the second operand was a signaling NaN. Stored NaN bits,
CPU state, memory, control words and all other observed status/tag fields matched.

Remill's original memory-operand promotion happened before its checked arithmetic
helper cleared host x87 exceptions. Promotion quieted the signaling NaN and raised
invalid status; the following clear erased that status before it was sampled.
This is consistent with Intel's documented masked signaling-NaN behavior.
See [Intel SDM Volume 1, section 4.8.3.5 and Table 4-7](https://cdrdv2-public.intel.com/843827/253665-sdm-vol-1-dec-24.pdf).

Before repair, a [151-file snapshot](../../reports/x87-arithmetic/baseline-failure/manifest.json)
preserved the initial sources, contract, generated IR/objects, workers and
measured records. The [failed measurement](../../reports/x87-arithmetic/baseline-failure/report.json)
retains every failure. Every final comparison verifies that archive and reparses
all initial records; the preserved failed implementation remains failed.

The new exact-IR adapter moves only the right-operand binary64-to-80-bit
promotion after the existing exception-clear/barrier and before arithmetic.
The existing exception test now captures its real hardware invalid flag.
No expected-result calculation or input-derived exception predicate is added
to the observer. There are no additional external bridges.

Arithmetic, conversions and all nine classification comparisons use constrained
strict floating-point operations; rounding-sensitive operations use dynamic
rounding. Quiet constrained comparisons replace ordinary classification FCMPs.
This follows [LLVM's constrained floating-point requirements](https://llvm.org/docs/LangRef.html#constrained-floating-point-intrinsics).
Independent relocation disassemblies show the clear, right-operand FLD,
FMUL/FDIV and exception-test sequence in all eight generated objects.

## Validation and identities

In addition to the 789 comparator/metadata/protocol rejection controls, the recipe
passes 32 altered-IR rejection checks, 24 object-symbol rejection checks,
64 memory-bridge checks and 120 host-FP-environment checks. Environment checks
include normal restoration, exception-unwind comparison and full64-bit pending
x87 instruction/data pointers. No scalar extended value crosses the Windows
C runtime ABI.

The independent original-worker oracle passes all 3,264 hardware cases. A
fresh [prior-suite replay](../../reports/x87-arithmetic/independent-regressions/report.json)
runs 24 previous original/O0/O2 workers and reproduces 4,968 records byte for byte,
including historical failures. Earlier evidence is preserved.

The final [independent verification](../../reports/x87-arithmetic/independent-review/independent-verification.json)
separately decodes all 9,792 canonical records with an independent exact oracle
and finds zero defined mismatches. It reviews compiled exception ordering,
rechecks source/tool/artifact/worker identities, reproduces the archived failure
and preserves all ten earlier G1/G2/x87 milestone bindings. A second read-only
review independently confirms each profile's saved records and full NaN bits.

- Common source digest: `1171023baadd2e832393314aabb101dd7872ba06195af04556a55e55c2eb84ef`.
- Contract SHA256: `9067379ec0394f2100593a97221c8879800aa1e72be2fd6e9dd77cfd907819bf`.
- Comparator SHA256: `638fa74b18ab788dfc997aa9cd233837c1c3f64f79310daa7769ae800fec65b0`.
- Initial failed report SHA256: `b2c41d795a7b3daa9fb5e7f7359b731569cc3ccb9aea5db1bb8b6bf75bd2b067`.
- Prior-suite replay SHA256: `b3f3e18a357720a772329c64b1e5d757a1a9731c5d41a8600d83ffc9f059ee64`.
- Final independent verification SHA256: `309f0f257d12e8a9e380370f0118ab629697e395126576c4245354f921c677c6`.

The [final pins](../../reports/x87-arithmetic/independent-review/final-pins.json)
identify each build/report/corpus. Per-profile directories under
`reports/x87-arithmetic` retain source/tool maps, exact IR, layout checks,
original/native objects and disassemblies, raw results and rejection evidence.
The isolated earlier control-word repair and pinned Remill/LLVM toolchain are
unchanged.

## Replay and next scope

From a fresh PowerShell 7 process in the project root, run:

```powershell
./tools/x87-arithmetic/build_arithmetic.ps1 -RunComparison
```

The recipe assembles both authored instruction sequences, lifts them using the
explicit repaired semantics directory, admits their exact hashes, retargets and
verifies State/bridge layout, compiles original Win32 and native O0/O2 workers,
runs boundary checks and performs the full four-profile comparison. It does not
alter script policy. No game launch is needed.

Next strengthen final-store C1, then define denormal operands and overflow/underflow
contracts and address remaining floating-point exception/status/stack policies. Direct calls, global
data, an observed import bridge and bounded indirect dispatch remain required
before M2 can be completed and the next native game slice selected.
