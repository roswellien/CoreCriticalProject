# First M3 whole-function comparison

This gate implements the complete observed MW3 function at `0x558290` before
expanding to a connected subsystem. The enclosing M3 milestone still requires
reachable-code and dependency closure, native execution of that subsystem,
and original/native comparison on directed and recorded workloads. One leaf
does not close that milestone.

The private admitted image and complete 43-byte function retain the identities,
incoming edge, section mapping and ABI in the immutable
[M2 next-slice contract](m2-next-slice-context.md). Original bytes and generated
translations stay under ignored local reports. The original game is unchanged.
This experiment does not launch its entry point or execute its caller.

## Exact execution and observations

Both workers use the actual entry `0x558290`, two stack dwords and ECX/EDX.
The original worker executes the admitted bytes at their actual guest address.
The native workers execute their statically generated Remill translation at
O0/O2. All three use the stack page at `0x20001000`, a 12-byte return/argument
frame and the writable zero-filled global page at `0x72C000`. The sole admitted
outer return is the private capture sentinel `0x10000100`; RET8 must advance
ESP by 12. All eight registers, entry flags, final defined flags, return PC and
every byte of both pages are observed before and after.

Final EAX is the signed second argument divided by two toward zero. EDX is
its sign extension; ECX and the nonvolatile registers are preserved. Five
global dwords contain entry ECX, entry EDX, first argument, second argument and
the quotient. A separate Python integer oracle measures these results. It is
never a worker body, memory bridge or result observer.

The final SAR1 defines CF/PF/ZF/SF/OF and preserves DF: observe mask `0xCC5`.
CF comes from the low bit of the value after SUB, not the initial argument.
AF is instruction-undefined. The exact native undefined-AF site may select zero
under a reviewed arbitrary-value policy; neither final AF equality nor its
original hardware value is guaranteed. Entry AF remains observed. Every
excluded observation has a positive exclusion control; defined fields have
corruption controls. No epsilon or fast-math policy is involved.

## Floating and storage preservation

Requests contain an admitted legacy FX512 seed: twelve masked CW modes,
coherent SW/TOP/physical occupancy/full tags, canonical raw80 payloads and eight
XMM128 registers. MXCSR is `0x1F80`. Guest FOP, FIP and FDP must be zero;
nonzero requests are rejected before execution. Original assembly restores that seed,
captures actual original hardware CPU/FX/FNSTENV before and after the function,
then restores the host environment. Native projections serialize actual guest
State and are explicitly labeled as projections, not hardware FXSAVE.

Original hardware and native guest observations cover CW/SW/TOP, physical tags,
occupied ten-byte values, admitted zero pointer/opcode metadata, MXCSR and XMM0..7.
CW/status/occupancy, values, MXCSR and XMM use FXSAVE observations. Guest
FOP/FIP/FDP use actual FNSTENV observations and must match zero before and
after. Native State projections are checked against their actual State bytes.
Raw observations are never rewritten. Reserved FX bytes and MXCSR_MASK are excluded.
Empty slots have no architectural numerical equality claim. Within-worker
before/after captures additionally check unchanged defined FP storage.

The preserved nonzero-metadata trials exposed two distinct host limitations.
FXSAVE reports zero pointers/opcode while FNSTENV can still observe the seeded
values. A later original run lost those three metadata fields in two records.
The [independent scheduling probe](../../reports/m3-subsystem-review/metadata-scheduling-probe/)
reproduces metadata loss during contended integer-only intervals, without an
API call or floating-point instruction between captures, while numerical state
remains unchanged. Arbitrary nonzero guest metadata therefore has no original
hardware preservation guarantee on this environment and is outside this gate.
The stricter zero-input domain preserves the complete numerical/storage matrix;
it does not mask failed fields or change the translated integer function.
The [failed nonzero run](../../reports/m3-slice/canonical-broker/comparison/report.json)
and its exact compiled sources/results remain preserved separately.

The native workers save actual 3504-byte Remill State before/after. Every byte
outside the independently verified integer store ranges must remain unchanged,
including empty logical raw80 storage, FP metadata, 2048 vector bytes and 128
MMX storage bytes. These additional native storage checks do not claim that all
Remill vector/MMX fields are independently represented by original x86 hardware.
Original result State blobs are zero and explicitly unobserved. MMX/x87 alias
execution semantics, SSE instructions and guest exceptions remain outside this
integer-only gate. Each normal result requires verified host restoration.
The first measurement also exposed a host isolation defect: an FX-only backup
on this machine loses observable metadata after FNINIT because its FXSAVE64
image contains zero pointers. The repaired scope must save the real legacy
environment alongside FX64 and restore it after FXRSTOR64, checking both actual
views on normal and contained-error exits. CW/SW/tags, values, XMM/MXCSR and
observable low-32 FIP/FDP plus FOP must match the scope's real saved state.
Separate normal/error controls seed and observe nonzero host metadata. These
checks measure the immediate restore interval; they do not claim that Windows
preserves arbitrary metadata through later scheduling outside that interval.
High-64 pointer metadata is not independently observable through this legacy
environment view and has no preservation guarantee in this gate. Earlier
FX-only probe records remain historical evidence for the fields they actually
observed; they do not establish the newly measured metadata guarantee.
An internally contained bridge error must retain failure status and restore
the host environment through its measured normal error-status exit. Such an
exit is not successful guest execution. Arbitrary Windows C++ exception
unwinding, guest SEH/trap delivery and their pointer restoration remain excluded.

## Corpus and admission

The authored corpus covers signed integer boundaries, all low-byte parity
patterns, negative neighbors, all 128 arithmetic/DF entry combinations, all
2048 TOP/physical-FTW pairs with two canonical raw80 patterns, the twelve CWs,
both DFs, directed sticky status and 10,000 deterministic random inputs.
Frames include unaligned starts and the exact first/last legal spans. The
global page starts entirely zero; the stack outside its frame is patterned.
Exact category counts and the input hash belong to the measured report.

The entire request stream, code/image identity, frame spans, flags, FP seed and
return route must be admitted before any execution output is created. Missing
or changed proprietary input is a failure. Unknown dependencies, targets,
instruction bodies, callbacks, concurrent use, guest traps/SEH/TLS/FS, memory
permissions and arithmetic address wrap are rejected. No original body or
provider is replaced with a result stub. Native host addresses remain private.

The result protocol records actual CPU/page/FP captures, explicitly distinguishes
original hardware from native guest projections, and carries actual native
State snapshots. Source, toolchain, image, IR, layout, object, worker, corpus,
saved result and rejection identities must be pinned before gate acceptance.
Independent result parsing and source/IR review are required. Unsupported
broader timer, virtual, MMX and floating instruction paths stay rejected.
