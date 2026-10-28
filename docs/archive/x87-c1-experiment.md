# Finite FISTP32 C1 repair experiment

Measured 2026-10-07. The previously missing conversion C1 flag now matches
original x86 execution in all 384 admitted cases at both native optimization
levels. The unchanged 240-case spill corpus also passes with the new adapter
and workers. M2 remains active; these are authored offline tests.

| Measurement | Original cases | Native O0/O2 comparisons | Mismatches |
| --- | ---: | ---: | ---: |
| Frozen conversion baseline, now observing C1 | 384 | 768 | 222 C1-only |
| Repaired finite conversion, including C1 | 384 | 768 | 0 |
| Explicit-spill regression | 240 | 480 | 0 |

The [contract](x87-c1-contract.md) keeps the earlier exact vectors and twelve
masked precision/rounding modes. It strengthens the conversion status mask
from 0x38FF to 0x3AFF, adding C1. It still excludes C0/C2/C3 and busy; the
spill regression retains its previous mask. Registers, admitted integer flags,
return/stack effects, the complete guest memory page, CW, defined SW, empty
final stack observations and protocol fields remain checked.

The conversion executes the authored five bytes `DD01DB1AC3`:
`FLD qword [ECX]; FISTP dword [EDX]; RET`. All 32 inputs round to valid
signed32 results under every admitted RC mode. They include both signs,
signed zero, fractions, odd/even ties, integers and signed32 endpoints.
No invalid, nonfinite or subnormal conversion is admitted.

For this subset, C1 is set when rounding increases the operand's magnitude:
`abs(rounded_integer) > abs(exact_input)`. Nearest -1.5 becomes -2 and sets
C1; nearest -2.5 becomes -2 and clears it. A signed-direction comparison
would disagree with hardware in 144 cases. Intel specifies the rounding
condition and clearing behavior in [FIST/FISTP, SDM Volume 2A](https://cdrdv2-public.intel.com/812383/253666-sdm-vol-2a.pdf#page=509).
The magnitude interpretation is independently checked against the original
for every admitted vector, rather than inferred for arbitrary x87 values.

Each original/native conversion run now has 111 set and 273 clear C1 results,
with 37 set at each precision setting. Nearest/down/up/zero modes contribute
39/36/36/0 sets. Precision status remains 288 inexact and 96 exact results.
The exact rational/integer oracle supplies both integer and status expectations;
neither execution worker contains it.

The repair adds six reviewed LLVM IR lines at the pinned FISTP exit: take
the absolute values of the already rounded operand and the exact loaded
operand, compare them, extend the boolean and assign `state.sw.c1` at byte
2739 before the integer memory write. The assignment also clears C1 when
appropriate. The native worker already packed that byte into status bit9,
so it does not calculate or substitute the expected flag.

Unoptimized and optimized generated code retain the actual C1 store. O2
reuses an existing absolute-value calculation. Independent disassembly finds
the magnitude comparison and byte assignment in both objects. No new bridge,
scalar80 ABI boundary or semantic-overlay change was needed. The previously
checked raw80 pointer rounding bridge and constrained conversions remain in use.
The [adapter](../../tools/x87-c1/adapt_c1.py) admits only the exact reviewed input
IR and records the new status lowering separately from existing bridges.

The original C1 omission is preserved in `reports/x87-c1/baseline-failure/`.
Fresh executions of the frozen prior workers reproduce 111 C1-only failures
per native build; every other admitted observation matches. Its report binds
the prior sources, metadata, binaries, inputs and outputs. The original
reference executable is archived alongside it. The new comparison gate
requires this proof, rechecks its identities and reparses the failure records.
Earlier evidence remains untouched.

The comparison reports contain 191 spill and 217 conversion rejection controls,
with ten and eight excluded-status checks respectively. Conversion includes
24 targeted C1 corruption regressions. Each profile rejects eight changed
guest IR inputs. Each native object passes three symbol rejection controls;
each native worker passes twelve memory and fifteen FP environment checks.
The conversion workers also pass 24 signed raw80 rounding-bridge checks each.

The frozen earlier bootstrap, both control-repair fixtures, first numerical
gate and both spill/conversion profiles were replayed in 18 worker runs.
All 3,096 new records are byte-identical to their saved results, including
the intentionally failing old bootstrap and conversion observations. New
regression evidence is `reports/x87-c1/independent-regressions/report.json`.
This replay preserves historical failures; it does not count them as newly
passing compatibility tests.

Replay with the pinned local tools from a fresh PowerShell 7 process:

```powershell
& 'D:/Projects/MW34Recomp/tools/x87-c1/build_c1.ps1' -RunComparison
```

The recipe assumes the archived baseline proof exists in this workspace.
The [contract](x87-c1-contract.md) describes its prerequisite replay and
independent reference-check script. Per-kind build metadata and comparison
reports are under `reports/x87-c1/<kind>/`. They bind source, contract,
toolchain/repair, instructions, IR, layout, objects, workers, corpus, outputs
and baseline identities. Independent review is saved separately.

Separate rational/integer oracles independently reparsed all 1,872 new
original/native records, with zero differences through each reviewed boundary.
Conversion raw status histograms also match: 96 zero, 177 PE and 111 PE+C1.
Per-kind `comparison/read-only-review.json` files bind that review to the final
reports and sources. Its replay script is
`reports/x87-c1/independent-read-only-review.py`.
The independent worker, object and provenance verification is
`reports/x87-c1/independent-review/independent-verification.json`, with its
replay script and pinned identities beside it. It confirms the generated
C1 stores, fresh boundary checks, archived failures and unchanged earlier
G1/G2/control/repair/numeric/expansion evidence.

| Frozen identity | SHA-256 |
| --- | --- |
| Shared authored source digest | `2ecb2bfaabf1a3104749a2002c62718b27d22b623975bd89263aa6c1a65e99ba` |
| Spill build metadata | `ab1675a23a8ecce436d976aad585431f1ef65b015ce279693775e56a4e0256b7` |
| Conversion build metadata | `9f724c96208eca697c74ed283a16db9ac46a45591e0f179d4f21eaaf9a62f72b` |
| Spill comparison report | `defe0108a3586b406fd49c465d8a79709d294a5ecb37df1153d65644e8dd246e` |
| Conversion comparison report | `8556c411496993fa0a605f7e84da5bed55d46493a944662f19a706f4dec9b906` |
| Preserved C1 failure report | `8eba6d35ec2e1053281610e264c0e27b37316b9e4de60faaf0798659b4956f74` |
| Earlier x87 regression replay | `981354dec5b03446a6375a219611ce7e76da377ab25ef77ccf78ea6111cd06fa` |
| Independent worker/provenance verification | `756e585b3159770c982a42f32748c61452a6781022a2f597858c7739688b8e4c` |

This closes C1 fidelity for the admitted finite FISTP32 corpus. C1 for other
instructions, other entry stacks/status, invalid conversions, exceptional
values, unmasked traps and general tags remain open. Multiplication/division
and explicit exceptional-value contracts are next before another game slice.
The [milestone register](../project-milestones.md) keeps M2's broader requirements.
