# CRT control setting carried through selected initializers

The bounded control-to-initializer gate is accepted on 2026-10-07. The actual
game wrapper at `0x5AC5A0`, its import thunk and complete staged `_controlfp`
provider run before the same 26 selected integer/FP initializers. One admitted
r9 image, CPU, 3,504-byte State and checked memory persist through each sequence.
The control result reaches subsequent numerical operations without injecting
an expected CW or resetting their state.

The [independent raw model](../reports/m4-crt-control-carry/independent-native-carry-r3/report.json)
checks 648 original and 1,296 native phases, 1,248 native State carry boundaries,
16,800 ordered initializer accesses, 480 helper routes and 624 control phase
events. All eleven pages, defined CPU bits, complete native State, original
hardware FX512 and separate legacy ENV28 agree within the declared domain.
The reviewer rejects 1,128 observer corruptions and accepts two coherent
isolated undefined-AF representations. Subsequent carry remains mandatory.
The separate [original source/carry model](../reports/m4-crt-control-carry/independent-original-carry-r1/report.json)
checks the actual control instructions and 624 original carry boundaries.

The [independent source and compiled closure](../reports/m4-crt-control-carry/independent-source-r1/closure-r3/report.json)
passes 2,016 compiled checks across 84 scenarios, reverses 29 shared source
derivatives and three control derivatives, and freshly inspects 34 COFF objects.
All 5,857 physical evidence bindings were rehashed for this status update.
Earlier failed builds, fixture assertions and reviewer versions remain saved.
The [author recipe](m4-crt-control-carry-experiment.md) records the fresh builds
and exact local inputs.

The twelve masked incoming CW words use empty TOP0/SW0/FTW0 and the installed
image's default operands, with two repetitions. The actual wrapper selects
double precision while preserving rounding and exception masks. This does
not admit live-stack or unmasked numerical execution. Original numerical
results, condition bits and dead raw80 storage are hardware observations;
this review does not supply an independent numerical architecture oracle.

The actual FXSAVE capability DWORD is `0x2FFFF`. Both resident State and
RuntimeFX retain that exact value. Two integer adapters require it and map
only offset 28 of a temporary validator Request to the earlier fixture's zero
representation. Neither resident FP state nor any CW, MXCSR, status or result
is canonicalized. The prior runtime and accepted service bodies are unchanged.

Original control returns to `0x5AC436` before an explicit capture jump to
`0x410A80`; native control returns to `0x5AC436`. The next caller setup changes
only the same return-word location to `0x410A80`. Full original CRT table
orchestration is not executed. Host FX bytes 0–415 and all ENV28 restore;
FXSAVE's uninitialized reserved tail 416–511 is outside that observation.
Source/tool/SDK hashes establish post-build identity associations, rather
than an execution-time process trace. Borrowers and mappings remain stable
and serial under this contract.

There are still 118 initializer roots outside the connected gate. Full CRT,
SEH, application, required services, native window/menu/input and the complete
M4 acceptance requirements remain open.
