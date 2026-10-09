# Numeric-max shared integration: preserved failure

The shared-r9 numeric-max candidate `native-build-r5` is not accepted. Its
guest State, memory, call routes and numerical output pass the bounded
comparisons, but a direct caller-boundary test reproduces host floating-point
state corruption on both success and an entered output-write fault.

The independent root models match 864 persistent native phases and 14,688
replays against frozen original inputs. They check all 3,504 State bytes,
four memory pages, provider-return checkpoints and ordered events/routes.
The separate independent compiled review passes 14,985 checks per optimization
level across 238 scenarios, including actual faults, poisoned retries,
ownership and borrowing. Those results establish their stated guest-side
scope; they do not establish numerical host isolation.

The original candidate's test harness restores the host before recording its
after-FX/ENV buffers. Those buffers prove explicit test cleanup. Twelve new
direct records, captured before cleanup, show that the caller's precision
exception bit is cleared and its legacy x87 instruction/data metadata changes.
The caller's control word, TOP, tag and two live raw80 values remain intact.
Volatile SIMD changes have a separate ABI scope.

The defect and all passing observations remain frozen. The independent
closure report is
`reports/m4-fp-numeric-max-integration/independent-session-closure-r4/report.json`,
SHA-256
`79739233be7de2f5dba36e42e0ed90eea8286ff366e2609da5270a127ec54720`.
The direct boundary report is
`reports/m4-fp-numeric-max-integration/independent-direct-host-r1/report.json`,
SHA-256
`49a5d97801d3f6827a9d46e87b1f25e107961f9208ac905a3cf42417d649abaa`.
The root's separate raw confirmation is bound in
`reports/m4-crt-entry/root-preparation-checkpoint-r1/report.json`, SHA-256
`f764d2020f1875e4b54461f9c28c165480bf9c3a4b61761673ee2723044b46af`.

A new derivative must provide an owned outer numerical invocation boundary.
It must capture the caller, complete exception handling and diagnostics, then
restore numerical state before returning a failure status. A callback-only
guard cannot cover failures before callback entry or later exception transport.
Direct success, early dispatcher failure, entered memory faults and denied
reuse must be observed before any harness cleanup. This repair is in progress.

Connecting numeric-max as the 27th initializer also requires a separately
reviewed state-domain extension. Its actual table position follows an
initializer that can leave sticky precision status and C1 set. The r5 guard
does not admit those carried states, and its provider translation does not
clear incoming C1 correctly. Hardware instruction-unit evidence and a new
derivative are being prepared; the old candidate and accepted ancestor stay
unchanged. The connected count remains 26 of 144 nonzero initializer roots.

The complete CRT entry, application services and usable native menus remain
required by [the full M4 plan](m4-startup-plan.md).
