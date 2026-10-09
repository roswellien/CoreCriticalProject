# Bounded final x87 store C1 repair

Measured 2026-10-07. This separate offline gate passes 3,264 original x86
cases and 6,528 generated Windows x64 O0/O2 comparisons, including the final
FSTP rounding flag C1. It preserves and repairs 160 missing C1 observations
from the preceding arithmetic implementation. M2 remains active.

## Contract and measured results

The [contract](x87-store-c1-contract.md) admits the same two authored sequences
and four fixed input profiles as the preceding arithmetic experiment:
`FLD qword [ECX]; FMUL/FDIV qword [ECX+8]; FSTP qword [EDX]; RET`.
Their complete bytes are `dd01dc4908dd1ac3` and `dd01dc7108dd1ac3`.
Every profile runs all twelve combinations of PC24/53/64 and
nearest/down/up/toward-zero rounding, with masked exceptions, clean entry
status and an empty entry stack.

| Profile | Original cases | Native O0/O2 comparisons | Defined mismatches | Rejection controls | C1 set per worker |
| --- | ---: | ---: | ---: | ---: | ---: |
| Finite multiplication | 1,152 | 2,304 | 0 | 223 | 32 |
| Finite division | 1,152 | 2,304 | 0 | 224 | 48 |
| Multiplication special values | 480 | 960 | 0 | 221 | 0 |
| Division special values | 480 | 960 | 0 | 223 | 0 |
| Total | 3,264 | 6,528 | 0 | 891 | 80 |

This gate observes status mask `0x3aff`, including final-store C1. It also
checks every CPU field, defined integer flags, the entire 4,096-byte guest
page, exact binary64 output, requested control words, return behavior and
final empty tags. C0/C2/C3 and B remain excluded; 32 exclusion controls
demonstrate that policy. Both original and native workers agree with the
exact oracle and with one another.

The finite oracle rounds exact rational multiplication/division first at
guest PC/RC and then at binary64 store precision under RC. C1 is set when
the stored value's magnitude exceeds the full PC-rounded intermediate's
magnitude. This distinguishes negative directed rounding, nearest halfway
stores and double rounding. It also distinguishes an exact final store
from earlier arithmetic precision loss: sticky PE alone does not imply C1.
The selected masked zero, infinity, quieted single-NaN and indefinite stores
all have C1 clear, as measured on original hardware. NaN sign, quiet bit and
payload remain exact observations.

[Intel SDM Volume 2A, FST/FSTP](https://cdrdv2-public.intel.com/812383/253666-sdm-vol-2a.pdf#page=547)
defines destination-width rounding and the C1 rounding indication.
[Volume 1, section 8.5.6](https://cdrdv2-public.intel.com/843827/253665-sdm-vol-1-dec-24.pdf#page=232)
describes the precision exception's significand increment indication.
The rational rule and special-value clearing above are bounded by this
clean-entry hardware matrix; they do not establish arbitrary store behavior.

## Preserved defect and implementation repair

The [123-file baseline snapshot](../reports/x87-store-c1/baseline-failure/manifest.json)
preserves the preceding arithmetic sources, tools, generated code, workers,
input corpora and saved measurements. Its
[failed report](../reports/x87-store-c1/baseline-failure/report.json)
reparses all previous records under the stronger status mask and reproduces
exactly 160 missing C1 flags: 32 multiplication and 48 division cases at
each optimization level. Every other admitted observation matches. The
earlier arithmetic gate retains its original `0x38ff` scope and reports.

The new adapter updates C1 immediately before the final guest-memory store.
It strictly extends the actual stored binary64 value back to 80 bits,
compares its unsigned sign-cleared encoding with the actual full 80-bit
store input, and assigns the resulting flag to State byte 2739. An exponent
guard clears C1 for the admitted nonfinite stores. Assignment is unconditional
so an exact store clears stale C1. Comparing the full intermediate avoids
losing the evidence through premature binary64 truncation.

This adds twelve IR instructions and one strict extension. Removing those
twelve instructions reproduces the preceding host IR byte for byte after
its module comment. The prior signaling-NaN exception-capture repair,
arithmetic, memory bridges and exception tests remain intact. There is no
new external bridge or observer-derived result. Generated O0/O2 objects
contain the integer magnitude/exponent logic and the C1 byte assignment.

The new layout requires one strict multiplication or division, three strict
extensions and one strict truncation, plus the same nine strict quiet
classification comparisons. State remains 3,504 bytes; all six external
bridge names and their site counts remain unchanged. No scalar extended
value crosses the Windows C runtime ABI.

## Validation and preserved evidence

Alongside the 891 comparator, metadata and protocol rejection controls, the
recipe passes 32 altered-IR rejections, 24 object-symbol rejections,
64 memory-bridge checks and 120 host floating-environment checks. Environment
checks cover normal restoration, active-state unwinding and full 64-bit
pending x87 instruction/data pointers. All eight workers preserve the host
x87/vector/MXCSR environment on the admitted boundary paths.

An independent [original-worker check](../reports/x87-store-c1/reference-check/summary.json)
passes all 3,264 hardware cases. A separate signed-floor rational oracle
independently decodes the canonical saved records for
[multiplication](../reports/x87-store-c1/mul64/comparison/read-only-review.json),
[division](../reports/x87-store-c1/div64/comparison/read-only-review.json),
[multiplication special values](../reports/x87-store-c1/mul-special/comparison/read-only-review.json)
and [division special values](../reports/x87-store-c1/div-special/comparison/read-only-review.json).
All 9,792 original/native records match under the stronger mask, with
identical raw status histograms and no defined CPU, memory or output mismatch.

The final [independent verification](../reports/x87-store-c1/independent-review/independent-verification.json)
also decodes all 9,792 records with a separate Fraction oracle, reviews all
eight compiled C1 assignments, and rehashes source/tool/artifact/worker/report
bindings against the final pins. Fresh boundary and adapter controls pass;
all 14 earlier per-profile milestone bindings remain intact. The second
[review summary](../reports/x87-store-c1/independent-review/read-only-review-summary.json)
independently binds its saved-record reviews to those same final identities.

The [prior-suite replay](../reports/x87-store-c1/independent-regressions/report.json)
runs 36 frozen original/O0/O2 workers and reproduces 14,760 saved records
byte for byte, including historical defects. The
[preservation check](../reports/x87-store-c1/independent-review/preservation.json)
retains earlier G1/G2/x87 bindings. Both failure archives remain intact:
151 files preserving the 96 historical signaling-NaN IE defects under
`0x38ff`, and 123 files preserving the 160 C1 defects under `0x3aff`.

- Common source digest: `7249d0c4324fb89177e870e2a391549e06a48e94a5bce8a5d1206ebad07e3c93`.
- Contract SHA256: `2c1f1e3dcd1651bf58cb539bcdfa0481e51d5e111311a16c92cec78f7244d0a6`.
- Comparator SHA256: `c14f133c70f0a42055bedb06bfc855e5ea5094b1e31106d4cf1552b5ac8c8a8a`.
- C1 failed report SHA256: `03eba1e074e3770bb42c2c411e876335f0cef556c9e4dd80d027cc960cd2f586`.
- C1 archive manifest SHA256: `ce06d189c3d2547b7f050623db2281d139c1e9d896d35059c3fa797bcb5b77cb`.
- Prior-suite replay SHA256: `0ce4f967401e92f99344054b08565d0a92fb187aa930bdef2d6d6e3e027bc8e2`.
- Final pins SHA256: `f9beeeb7f81e2e7f4a648e1a7ae727a7da1abb79f4dbbf4684649874ffcb10a3`.
- Independent verification SHA256: `6047f0a64872be62c2cd45f51f2a28535aa15f031e3042cc3b3d69f5276f1468`.
- Second review summary SHA256: `f160c04bf9460a8287a3c4e1090a95320471785199f70f931f8614cbb8ee1041`.

The [final pins](../reports/x87-store-c1/independent-review/final-pins.json)
bind each build, report and corpus. Each profile under
`reports/x87-store-c1` retains source/tool maps, admitted IR, layout checks,
objects and disassembly, raw worker results and rejection evidence. Earlier
authored sources, workers, reports and control-word repair provenance remain
frozen. The current repair affects only this new isolated experiment.

## Replay and next scope

From a fresh PowerShell 7 process in the project root, run:

```powershell
./tools/x87-store-c1/build_store_c1.ps1 -RunComparison
```

The recipe uses the pinned repaired semantics directory and verifies source,
contract, tool, archive, artifact, worker and layout identities before
comparison. It builds the actual Win32 reference and native O0/O2 workers,
runs boundary checks and compares all four complete matrices. It requires
the preserved local failure archives; it does not claim reproduction from
an empty checkout. The recipe does not change script policy or launch MW3.

Next define separate denormal-operand and overflow/underflow contracts,
then address remaining exception/status/stack policies. Arbitrary inputs,
two-NaN selection, live stacks, unmasked traps and exceptional-exit pointer
restoration remain unproven. Direct calls, global data, an observed import
bridge and bounded indirect dispatch are still required before M2 can be
completed and the next native game slice selected.
