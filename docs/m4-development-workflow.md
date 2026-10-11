# M4 development workflow

Updated 2026-10-10. The immediate work remains native startup and menus.
The faster workflow groups related dependencies, uses shared evidence tooling,
and prepares later services while the current CRT integration is verified.
Acceptance still requires source, ABI, state and dependency evidence.

## Four concurrent roles

The current session supports four active agents including the coordinator.
Use one coordinator for integration and independent source predictions, one
implementation owner for a bounded service batch, one independent compiled
reviewer for ownership/failure/floating-point behavior, and one work-ahead
owner for the next application dependency. Each writer owns a separate new
tools/reports namespace. Work-ahead uses exact existing static records; it does
not claim execution until a later native comparison passes.

More agents cannot bypass unresolved dependencies or serialized integration.
Measure time spent in recovery/lifting, compilation, native capture,
observation, physical hash closure and review before choosing another
optimization. Independent work may run together; shared mutation, admission
and acceptance remain ordered.

## Evidence transport and timing

The [pipeline tools](../tools/m4-pipeline/README.md) add deterministic,
externally SHA-bound capture bundles, normalized manifest merging and
monotonic stage receipts. Existing native writers can retain their flat output;
a verified bundle provides direct logical reads to a new observer without
changing old receipts. An observer must independently predict values from
original pre-execution state and source bytes, then compare full storage.
Changing transport cannot create an equivalence proof.

Each new command has a fresh output directory, explicit input/tool hashes,
stdout/stderr, exit status, timeout outcome, artifact hashes and elapsed time.
Failures remain available; they cannot overwrite a passing attempt or inherit
success from stale output. Dependency sets merge once with conflict rejection;
every unique physical dependency is still hashed, including same-size,
same-time modifications. No metadata-only cache is admitted.

Independent [pipeline review](../reports/m4-pipeline-review/review-r4/report.json)
passes 9,161 checks. The [transport benchmark](../reports/m4-pipeline/benchmark-r3/report.json)
compares 2,945 unchanged files in four representative frozen rows. Warm repeated
reads were about 10.7 times faster through the bundle reader on this machine;
pack conversion and reader verification are separate costs. This does not
predict whole-project throughput or a completion date.

## Dependency batches

The [application work map](m4-application-workahead.md) orders 13 preparation
batches with source pointers, exact bytes, call frontiers and unresolved
dependencies. Its [root check](../reports/m4-application-workahead/root-check-r1/report.json)
validates 90 selected bodies, 1,012 outgoing call records and 14 corruption
controls. The projection retains 203 unresolved indirect edges and eight
missing bodies. Runtime loops remain marked separately from implementation
prerequisites. The map is actionable static preparation, not full call closure.

While CRT filename/command-line/environment work progresses, prioritize narrow
MFC module/TLS/object lifetime contracts and the archive reader ABI. The reader
is required before the first bounded frame/window path. Localization/config,
widget properties, graphics and input/audio contracts can be prepared in
parallel as their source dependencies permit. Retail menu acceptance still
requires the real application state transition, widget receivers, backends,
message/input loop and shutdown.

Use batches that share data ownership and service contracts rather than
counting tiny independent helpers as whole-game progress. The current selected
initializer gate accepts [131 of 144](m4-progress-startup131.md), with 13 remaining.
[Plan r14](m4-execution-plan-r14.md) groups the remaining MFC, numeric,
constructor, font, version and registry/loader closures. Use small genuine
provider probes before connected family integration, and serialize heavy
archive reads. Initializer acceptance still leaves complete CRT startup,
argv/environment and native menus open.
