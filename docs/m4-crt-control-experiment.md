# Measured native CRT control providers

This additive gate executes the installed `_controlfp` and `_control87`
provider bodies and compares their statically compiled native translations.
It covers both entry points, their two shared conversion helpers and all
148 instruction addresses in the exact hot and cold control-flow graph.
The private provider image is admitted by its SHA-256 identity. Public
sources contain addresses and hashes; derived vendor bytes remain in private
research and build evidence.

The admitted provider is `local/mw3-staged/Shared_DLLs/MSVCRT.DLL`, SHA-256
`2d5670881a6d13a100e37da297f6eeb876f68b63073a28eb5d650625c60f9bf7`.
The complete source ranges are `0x780042E1` for 303 bytes and `0x7801129B`
for 125 bytes. Four actual Remill definitions are compiled at O0 and O2.
Their integer, branch, stack, direct CALL and RET instructions remain in the
compiled control-flow graph. There is no successful substitute callback or
invented logical return value.

Three exact instruction lowerings replace unsafe host operations: FWAIT
checks the bounded guest pending/empty-state contract, FNSTCW stores guest
CW, and FLDCW loads guest CW through the independently accepted
[typed guest-CW transfers](m4-guest-cw-contract.md). The lowerings do not
consume host exception flags or change host rounding. Their instruction
PCs remain attached to the original graph. The guest and host complete
Remill `State` layouts both contain 3,504 bytes.

The original worker executes only these copied provider bodies at their
exact guest addresses, with RX code and an owned RW guest stack. It calls
no provider loader, DllMain or game entry. Its assembly continuation captures
actual registers, FX512, legacy ENV28 and all 4,096 stack bytes before host
code resumes, then restores the actual host environment. Native workers
consume the original before-state and input tags. They do not read original
after-state as an execution oracle. The comparator separately reads the
actual original after-state.

The accepted experiment domain is empty physical x87 tags, TOP0, SW0 and
MXCSR `0x1F80`, with matching normalized State/FX CW. Twelve masked incoming
control words cover the directed precision and rounding modes. Each entry
receives 68 directed `(new, mask)` pairs twice: query, all-bit clear/set,
a mixed pair, and each individual bit set/clear. This produces 3,264 actual
original observations and 6,528 native observations. Nonzero raw 80-bit
storage, XMM storage and distinct legacy FP metadata make preservation
observable. Unsupported pending, nonempty or mismatched states are rejected
and never reset into this domain.

The operation may leave newly unmasked guest exception controls. No numerical
x87 instruction follows within this gate. Deferred exceptions, occupied live
stacks and numerical host-CW synchronization remain outside its acceptance.

The final comparison has zero differences in complete guest CPU, all FLAGS
bits except architecturally undefined AF, full State storage, separate FX
and legacy metadata, and complete guest stack. Native logical-operation AF
is deterministically zero; the gate makes no original AF equivalence claim.
Actual host FX512 and ENV28 before/after captures must match. Native entry
and return hooks observe 45,696 real CALL/RET events, including checked
original CALL bytes, exact guest continuation words, ESP cleanup and
nonvolatile preservation. There are 24 actual worker admission controls,
178 rejected observer corruptions and two explicit undefined-AF exclusion
controls.

The first native context tests exposed a real host escape defect. The
readonly-stack case faults on the provider's first PUSH at guest address
`0x200017FC`; `Context::deny` was declared `noexcept` while invoking Windows
`longjmp`. The pinned MSVC header declares `longjmp` as `noexcept(false)`.
The literal build terminated with `0xC0000409`. A diagnostic that changed
only this declaration, while linking the same frozen guest object, passed
all 27 controls. The baseline, positive streams, failed tests and both
diagnostics were preserved before removing `noexcept`. Fresh O0 and O2
context builds pass the same 27 controls each, and the complete positive
guest records remain byte-identical to the earlier baseline. The checked
memory catch finishes before `longjmp`; the Context and caller's active
`jmp_buf` remain alive. The host IR's required entries and bridges carry
neither `nounwind` nor `willreturn`. Object unwind records are supplemental
evidence, not a generic exception-unwind guarantee.

Final evidence is [comparison-r3](../reports/m4-crt-control/comparison-r3/report.json),
[native-build-r3](../reports/m4-crt-control/native-build-r3/build.json) and
[context-build-r2](../reports/m4-crt-control/context-build-r2/build.json).
The [author aggregate](../reports/m4-crt-control/author-review-r1/report.json)
rehashes physical evidence and the accepted guest-CW prerequisite. Its
durable map uses literal preservation copies for changed historical source
paths. The original execution, earlier positive streams and failed
attempts remain immutable. Independent review is still required.

Reproduce with fresh private report and derived-build directories. The
original frozen capture and exact research IR are consumed by these steps:

```powershell
pwsh.exe -NoProfile -File tools/m4-crt-control/build_native.ps1 `
  -OutputDirectory D:/Projects/MW34Recomp/reports/m4-crt-control/native-replay-new `
  -ResearchDirectory D:/Projects/MW34Recomp/reports/m4-crt-control/research-r1
pwsh.exe -NoProfile -File tools/m4-crt-control/build_context.ps1 `
  -OutputDirectory D:/Projects/MW34Recomp/reports/m4-crt-control/context-replay-new `
  -NativeBuildDirectory D:/Projects/MW34Recomp/reports/m4-crt-control/native-replay-new
C:/Python314/python.exe tools/m4-crt-control/run_native.py `
  reports/m4-crt-control/native-replay-new/build.json `
  reports/m4-crt-control/native-capture-new
C:/Python314/python.exe tools/m4-crt-control/compare_repaired.py `
  reports/m4-crt-control/native-capture-new/report.json `
  reports/m4-crt-control/comparison-new
```

The recipe admits the exact research IR and guest-CW independent map, records
literal sources, compiler/tool identities and command logs, and refuses
existing report/build directories. Tool identity evidence is a current
hash plus recorded command/log association; it is not complete execution
attestation. Workers require exact pack and actual-original identity and
preserve existing ordinary output files or directories. Publication scope
is sequential workers in fresh private ordinary directories; concurrent
writers, reparse points and dangling links are excluded.

This component assumes a stable, valid nonnull trusted Context whose
lifetime spans each call. Callers propagate its required faults; arbitrary
host mutation or raw memory-fault swallowing is outside this experiment.
It does not provide a general thread-owned or one-use Runtime callback API.
It implements state transfers without synchronizing host CW for active
numerical operations. The accepted shared runtime r9, earlier gate sources
and provider service registry remain unchanged. A fresh runtime/provider
integration, data-import admission, wider FP states, complete CRT startup,
SEH dispatch/unwind, all remaining initializers and the actual frontend
remain required. M4 is open; this isolated provider gate is not menu or
whole-game startup completion.
