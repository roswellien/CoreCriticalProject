# Review of Claude's continuation work

Recorded 2026-10-11 at approximately21:29 America/Denver. Documentation/source
review only: no capture, game launch, production checker, policy admission,
active SQLite connection or accepted-count update was performed.

## What was checked

Read Claude's continuation entries in [plan r14](m4-execution-plan-r14.md),
the underlying current141 receipts, the admission-v2 preparation and code delta,
and the draft45-field review. Freshly hashed all15 documented successful
current141 receipt files (14 latest outcomes plus superseded lock25 r1) and
the admission preparation receipt: every hash matches plan r14. Freshly hashed
616 unique declared `.py/.ps1/.cpp/.hpp/.c/.h` source pins: zero mismatches.
The preparation receipt's seven direct pins also match. This is an independent
identity/scope check, not independent semantic reproduction of every probe.
Full exports, all artifact/data pins, the accepted historical union and the
complete source-footprint inventory were not reverified here.

The accepted131 receipt freshly matches SHA256
`aa9462f30bf4fa6c80ef926488928bb8680f207020e4f0aa166968caaf724061`:
`connected_roots=131`, `remaining_inventory_roots=13`; whole M4, native launch,
menu and Training flags are false. No newer acceptance was identified.

## Reusable results and limits

| Work | Receipt under `reports/m4-startup141-paired/` | Checked outcome / remaining limit |
| --- | --- | --- |
| Source original registry schedule | `registry-output141-r1/report.json` |846 phases,666 callback stores,120 growths and full realloc inputs; emits missing source metadata/backings/stores. Not whole-page acceptance. |
| Native registry schedule | `registry-native-schedule141-r2/report.json` |846 entry/cell joins per level and120 growths. Capacity summaries are zero at168 relocated-allocation phases; nonzero capacities match. Per-phase native backing equality is not exported/proved. |
| Final callback vectors | `registry-final-vector141-r1/report.json` |111 callbacks match for six sequences and own unused tails retained; not every-phase backing proof. |
| lock13 | `lock13-counts141-r1/report.json` |111 balanced Enter/Leave pairs per sequence measured; replaces108 only in reviewed current policy. |
| lock25 | `lock25-binding141-r2/report.json` |Own object identity and paired index25 lifetime; r1 lacked lifetime evidence and is superseded. |
| Named imports | `import-cells141-r1/report.json` |144 captured-export resolutions and actual phase15 hook schedule; no whole CRT admission by itself. |
| CRT instruction closure | `mode1-closure141-r1/report.json` |229-PC closure,2,820 current API records within checked sites; current constructor traffic accounted for in this scope. |
| Unused-byte disjointness | `footprint141-r2/report.json` |339 unused bytes;1,839,258 collected source/API operands; none touches those bytes. Collection completeness remains open. |
| Whole CRT policy evaluation | `crt-policy141-eval-r1/report.json` |6,768 two-page evaluations pass; policy admission/completeness remain open. |
| CRT adverse controls | `crt-policy141-controls-r1/report.json` |Seven deliberate mutations rejected; does not admit production policy. |
| Global-page equality/carry | `global5F2000-relation141-r1/report.json` |3,384 paired whole-page checkpoints match; alone cannot exclude transient writes. |
| Global-page source writes | `global5F2000-nowrite141-r1/report.json` |Zero writes in collected ledgers;84 constructor reads. Shares unresolved collection-completeness limit. |
| Original ENV lastwriter | `env-lastwriter141-r3/report.json` |Executed137-139 PCs plus static reachable140/provider paths; ties metadata to phase101 FSTP. Reachability and execution are distinct evidence. |
| Native ENV transport | `env-native-transport141-r2/report.json` |701 source files and53 classified copy/write sites; static no-host-metadata-transport result. Typed relation review/admission remains open. |

All outcomes preserve zero accepted-function credit. Do not promote the table
to a whole141 comparison or assume observed equality proves every ledger complete.
Retained failures/superseded attempts stay available. Claude documented deletion
of two pre-receipt crashed ENV attempts; that deviation remains recorded in r14.

## Controls chain

`root_admit_completed_review_v2.py` adds the stream parser pin omitted by v1.
The inspected delta is the explanatory docstring plus that one pin inherited
from the existing composer admission. The matching
[preparation receipt](../../reports/m4-controls-terminal-composite/completed-review-admission-preparation-r1/report.json)
records the exact inverse and three rejection controls. It is preparation,
not executed admission. Use v2 after actual closed composer output exists.

`root_field_review45_v1.py` is drafted and unexecuted. It requires actual
independent composite review before field measurement. The predicted39 identity
fields and six changes remain predictions until measured from terminal gates.
The retry-loop source check supports equal predicates with a larger retained
inventory; it does not itself prove all386,172 retry comparisons or an allowance.
Source-only cold-load, field-domain and exact allowance review remain required
before executing drafts. Keep all39 gates/841 predicates unchanged.

## Running process snapshot

Composer PID44416 was active, started18:12:38, with only
`whole-ordinary-union.sqlite` and its journal in
`reports/m4-controls-terminal-composite/terminal-composite-r1/`.
The file was7,602,008,064 bytes at21:29:10; that is file activity, not a completion
percentage. No terminal gates were present. Watcher PID40500 was running
`wait44416.ps1` in Claude's scratch area. Neither was modified or terminated.
Recheck process identity/current files before continuation; PID/file observations
are dated and exit alone does not establish success. Claude's154GB read figure
was user-reported and was not independently reproduced in this review.

After successful closed output: admissionv2 -> composite reviewv3 -> actual45
field review -> candidate finalization -> configuration -> independent exact
allowance review -> strict acceptance. Do not automatically launch hours-long
jobs while updating docs or duplicate another review already running.

## Viewer audit and new priority

The [viewer reproducibility audit](m4-vulkan-viewer-reproducibility-audit-r1.md)
is present in commit `5d86c74`. Its build and presentation/self-test observations
were recorded by Claude; they were not rerun for this documentation task. Its
clean-checkout statements refer to its then-current `d20e936` snapshot, not a
fresh assessment of current HEAD. Viewer replay is still not native game rendering.

Claude's work closes useful evidence gaps and should be reused. The next primary
development work follows the [faithful modernization plan](../faithful-modernization-plan.md):
audit the complete application/runtime path and implement its first concrete
execution blocker. Continue existing strict acceptance as a separate lane;
do not make further proof machinery the default queue while waiting on the composer.

Documentation validation: checked552 local Markdown links across25 changed/new
documents; all targets exist. `git diff --check` passes. No build, viewer self-test
or production verifier was rerun, and the composer/watcher were still active at
the final process check. Documentation changes remain uncommitted.
