# Compound cosine initializer: Runtime test

The literal initializer at `4B64F0` now runs through the x64 Runtime dispatcher
at O0 and O2. It contains three `FLD`/`FCOS`/`FSTP` operations and seven scalar
stores. The physical default double inputs, original 121-byte entry extent,
borrowed guest return frame, flat segments, empty x87 stack and six observed
CW/TOP cases are admitted explicitly. The source recovery covers nineteen
executed instructions; the gap in that extent remains part of code admission.

The [Runtime source and controls receipt](../reports/m4-cosine-native/runtime-fixture-verification-r1/report.json)
passes these measured checks:

| Check | Measured result |
| --- | --- |
| Genuine dispatcher positive cases | 12, covering all six cases at both levels |
| Complete literal source State/CPU | 12 × State3504 and CPU40 |
| Whole source pages and operand values | 516 page effects and 168 complete operands |
| Original finite numerical joins | 36 observed single-precision results |
| Actual corruption controls | 20 rejected attempts: code, each of three inputs, DS, FS, CW, MXCSR, FTW and output permission |
| Unchanged retry | 32 complete State/CPU/FX and route ledgers, with 89,568 private and page records compared |
| Caller numerical environment | 96 architectural hardware and whole ENV28 pairs |
| Resource cleanup | 32 completed cleanups |

The numerical source seam is explicit: it uses the three current original F32
results, original x87 status and raw80 observations for the exact default inputs
and CW/TOP cases. Integer operations, complete page changes, CPU effects,
unchanged State bytes, operand order and final x87 metadata are reconstructed
from literal instructions and the measured BEFORE state. No whole original or
candidate AFTER State, CPU or page is used as a worker input. This test does
not independently predict trigonometry or admit arbitrary FCOS inputs.

Actual negative probes exposed an inherited cleanup issue. When the dispatcher
poisons Runtime after an external callback failure, the registry must release
its owned resources through fault cleanup. Running its ordinary source-free
continuation with rejected segment or floating-point state can fail again.
The additive test library now propagates that Runtime poison before selecting
cleanup. Separate immediate invocation observations verify the dispatcher
boundary before diagnostic work, and complete outside-return observations
verify the diagnostic boundary and cleanup. Earlier failures remain preserved.

The [current callback preparation](../reports/m4-cosine-native/runtime-preparation-r2/report.json),
[fixture preparation](../reports/m4-cosine-native/runtime-fixture-preparation-r4/report.json),
[actual build](../reports/m4-cosine-native/runtime-fixture-build-r4/build.json) and
[execution](../reports/m4-cosine-native/runtime-fixture-execution-r3/report.json)
are frozen separately. This is an isolated candidate test over the accepted
bootstrap. It adds zero initializer credit. The authoritative inventory remains
**125/144** until the expanded connected schedule, full persistent source and
provider lifecycle, independent review and physical dependency acceptance pass.
