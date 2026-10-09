# Required startup floating-point research

M4 remains active. This experiment captures original hardware behavior of ten
complete, import-free startup roots. It grants no native floating-point
equivalence, connected CRT initialization, or menu completion credit.

The exact admitted MW3 1.2 image supplies the complete code slices and input
constant/BSS bytes. Only reviewed slices are copied into executable pages;
other code-page bytes contain `INT3`. Constants are read-only, output and
stack pages are writable, and unused pages in the reserved regions remain
uncommitted. One owner manages each 64 KiB reservation. A suspended x86 worker
receives those reservations before its CRT starts.

The roots are `0x4133C0`, `0x4ADB50`, `0x4B5AF0`, `0x4B7020`, `0x4C78F0`,
`0x4C79D0`, and `0x4CE5A0` through `0x4CE600` at stride 32. Their required
operations include FLD, FMUL, FDIV, FILD, FSTP to binary32, FSQRT, FSIN, FCOS,
FPATAN, and FXCH. They contain no outgoing call or unresolved branch in the
reviewed direct graph. Other startup FP roots still need service closure.

The probe captured 480 actual original records: ten roots, twelve masked
precision/rounding control words, empty x87 input with TOP 0 or 7, and two
repeats. It records CPU entry/return, full FX512 snapshots, legacy ENV28,
host restoration snapshots, and all nine input/output/stack pages. All 240
repeat pairs have identical guest observations. CPU/return, host restoration,
input identity, and exact allowed write spans pass. Eighteen observer
corruptions reject for their intended causes. Six actual worker controls
check SHA known answers, CLI, changed pack/image, missing input and existing
output preservation. Output staging uses `CREATE_NEW` and owns only a newly
created file; existing evidence is retained.

Every record demonstrates a distinction between the two actual FP snapshots
on this machine. `FNSTENV` records nonzero last-instruction/opcode/data/segment
fields, while `FXSAVE` records zero instruction/opcode/data pointers. For
example, `0x4133C0` finishes with legacy FIP `0x4133DC`, FOP `0x11D` and FDP
`0x604E40`. These are measurements of this worker/hardware configuration,
not universal assumptions about every x86 processor. Both snapshots must
remain separate in the native observation model. An adapter must preserve
legacy State metadata when overlaying a zero-metadata FX view.

The first observer-control attempt rejected correctly but expected the wrong
diagnostic for a changed FX control word; its literal source and failure are
retained. One sandbox worker-control attempt failed at pre-CRT address
reservation, before its intended changed-pack rejection. That failure is
retained and receives no causal-control credit. The same compiled worker and
unmodified control script passed all six intended checks in normal Windows.
The original 480-record run succeeded in the sandbox.

Private evidence resides in `reports/m4-fp-startup/research-r1`, `build-r1`,
and `run-r1`. Public source is `tools/m4-fp-startup`; controls are in
`tests/m4-fp-startup`. The build recipe requires an exact private extraction
and fresh build/report directories, and retains source/tool/artifact bindings.

Remaining proof includes actual compiled native FP execution, output rounding,
status and stack-storage comparisons, metadata serialization, protected complete
State and checked events, connected initializer ordering, nonempty/alternate
input domains, unmasked exception handling, and other supported hardware
configurations. The probe does not compute expected FP values, and matching
repeat observations do not establish native equivalence.
