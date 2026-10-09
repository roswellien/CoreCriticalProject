# Denormal and binary64 range experiment

Accepted bounded gate, 2026-10-07. Original x86 multiplication/division and
compiled Windows x64 O0/O2 now match all **3,840 original cases and 7,680 native
comparisons**, including CPU, complete memory, control/status words, C1 and
empty final tags. This closes M2-03 within the [range contract](x87-range-contract.md).
M2 remains active: live stack/tag behavior, consolidated exception policies,
the remaining call/import boundary checks and next-slice acceptance are separate.

Each profile tests 40 finite nonzero binary64 magnitude pairs, four sign
combinations and all twelve masked precision/rounding modes. Cases include
subnormal operands, exact/inexact tiny stores, signed zero, overflow to infinity
or maximum finite, double-rounding witnesses and the tininess boundary where
an extended intermediate rounds to a normal binary64 result. Defined status
uses mask `0x3aff`; undefined condition/status bits have explicit exclusion controls.

## Preserved failure and repair

The initial native workers lost the sticky denormal-operand flag in 3,072 of
7,680 comparisons. Their CPU, result bits, other defined status and memory
matched. The complete authoritative failed source/artifact/worker/result snapshot
contains 91 hash-bound files under
[the failure archive](../reports/x87-range/baseline-failure/report.json).
The report SHA-256 is
`f52847eb4f286ae7e6af20835898981a4ef0f8e7823d3eb46e6b803c6a7320fd`.
Its recorded preliminary-probe limitation remains explicit; the preliminary
worker hashes are historical, while the later canonical failure workers are
preserved and replayable.

The new lowering ORs the existing guest DE flag with each new classification
at the two reviewed arithmetic/store sites. It retains the actual generated
values and original classifications. The host boundary also normalizes guest
MXCSR to `0x1f80` during execution and restores the saved host state afterward,
so host DAZ/FTZ and SSE rounding settings cannot alter subnormal classification.
The earlier NaN-promotion and final-store C1 repairs remain unchanged.

## Acceptance evidence

The canonical comparisons pass with 242 multiplication and 241 division
rejection controls, plus sixteen undefined-status exclusion checks.
Fresh worker checks pass 32 memory, 60 FP-environment and 1,536 MXCSR-isolation
checks. Sixteen altered adapter profiles are rejected; both reviewed profiles
are accepted. Two separate reviewers independently reparsed all 11,520 saved
original/native records with exact rational oracles, rebound the source,
contract, tool, artifact and worker identities, and reproduced only the archived
DE loss in the failed workers.

Earlier evidence remains intact: eighteen G1/G2/x87 entries were rechecked and
48 earlier workers replayed 24,552 records byte for byte.

| Binding | SHA-256 |
| --- | --- |
| Final source digest | `955fe27ff5e5bb9442fb78828f8cdb7e76e09a56cef75413178390d4ba64e1d6` |
| [Final pins](../reports/x87-range/independent-review/final-pins.json) | `11c50568126933468e32ef061c0adf450aa0d61e1e0d01861d6f2d77fe5306d2` |
| [Independent verification](../reports/x87-range/independent-review/independent-verification.json) | `694ac289fd7cba7ed0c2ac5864b85d33f66be31354a206f29437667f450a7e53` |
| [Separate saved-record review](../reports/x87-range/independent-review/read-only-review-summary.json) | `d038de32c74099ef2c3ee2677b641a916ee6aff4d490a0511ca5dbf142bebd81` |

Reproduce in a fresh PowerShell process with `tools/x87-range/build_range.ps1
-RunComparison`. The frozen comparator checks all provenance before executing
workers. These are authored offline probes; no game launch or whole-game
floating-point compatibility is claimed.
