# M2 next real slice: reviewed context and dependencies

This contract selects a complete statically observed MW3 function for the next
offline execution experiment. It completes the M2-11 dependency/context planning
requirement; it does not claim M3 native execution or a game subsystem working.
`tools/m2-slice-admission` admits the proposed context and **always rejects execution**
until the exact translated function and original/native comparison are reviewed.

## Image and full-function selection

The only admitted image is MW3 U.S. retail1.2, SHA-256
`95bc2c114c9b2e5c5ada8e40ca78cc79470f862e45313ffad0d1e8e6d4d916bf`.
Its PE32/i386 preferred base is0x400000 and image size0x5F5000. The local image
check reparses section mappings and freshly disassembles the actual complete
image using pinned LLVM21.1.8. Missing or different input fails before evidence
is written. Proprietary bytes and full disassembly remain in ignored reports.

The selected complete function is **sub_00558290**, range
`[0x558290,0x5582BB)`,43 bytes,11 instructions, file offset0x157690, SHA-256
`fd939ea8ce1dc550fd08e7f2c2a2178ff063435cc7a8f5c5aafbf13eff32feaa`.
It has one straight-line basic block, no CALL, no branch, no object dereference,
no import and no outgoing indirect target. Its last instruction is RET8 at
0x5582B8. Padding after that RET is excluded. Address-based naming preserves the
evidence boundary; this review does not assign a gameplay purpose.

The real incoming direct CALL at0x5995DD in the fully inspected
sub_005995B0 targets0x558290 and returns to0x5995E2. The original caller supplies
ECX and EDX plus two pushed dwords. The chosen function is a complete observed
dependency, not a convenient prefix of a larger function.

## Why the timer wrapper is deferred

The initially considered full wrapper is `[0x5996D0,0x599704)`,52 bytes,
SHA-256`c9a83047c5d0758f496132c425fa619e569800f2e5aeb64e584f6f54033dc1a9`.
It calls WINMM.timeGetTime through IAT0x5BB75C at0x5996D6, combines returned
EAX with an explicitly zero high dword, performs FILD m64int, FMUL m32real and
FSTP m64real, then passes the resulting eight bytes to sub_005995B0.
Those exact floating instruction forms are **not admitted by the earlier gates**.
Binary64 arithmetic or raw80 transport evidence does not validate this sequence.

The scale operand at0x5CF838 is four file-backed read-only `.rdata` bytes,
file offset0x1CEC38, binary32 bits0x3A83126F, approximately
0.0010000000474974513. Fresh whole-image linear decoding finds its two direct
FMUL operand references at0x5996F1 and0x599731 and no direct write operand.
This does not prove absence of aliased runtime writes; an admitted mapping must
remain read-only. Static timer scaling does not establish live timing fidelity.

Its complete callee `[0x5995B0,0x599612)`,98 bytes, SHA-256
`923f7a471c6ad95f20a1b39762cc505a6da78b1d94765647f95e2d991abc5522`,
has a branch at0x5995B8 to0x5995C0. An empty object field+0x18 produces
AL=0 and RET8 at0x5995BD. The other path calls0x576DB0,0x576DA0,0x576D90,
0x576D80,0x558290,0x56F520 and0x51A300, writes object dwords+8 and+12,
loads object+0x18, reads that object's vtable, and calls its slot+8 with two
zero stack arguments. It then sets AL=1 and RET8 at0x59960F. ECX is the incoming
object pointer, saved through ESI; ESI and EDI are restored. The minimum directly
accessed outer object extent is0x1C, but complete object/vtable ownership and target
sets remain unresolved. The call using ECX=0x5F4650 introduces another global
object whose complete layout and effects are unreviewed. Upper EAX is not a
reviewed boolean return value merely because AL is set.

Those unresolved bodies and the virtual slot block the full timer slice. No
timeGetTime or body return is substituted to conceal them. The sibling wrapper
0x599710 and its complete callee0x599620 are recorded for comparison only, and
are not selected routes or execution permissions.

## Exact register and stack contract

All guest addresses/registers are unsigned32. The selected ABI is the observed
ECX/EDX plus two-stack-dword, callee-cleanup contract; no compiler calling
convention is inferred from a familiar-looking prologue.

| Field | Entry requirement / resulting behavior to validate in M3 |
| --- | --- |
| EIP | Exact0x558290; code identity bound to the admitted image |
| ECX / EDX | Two full32-bit register inputs; ECX preserved, EDX becomes sign extension of second stack argument |
| Stack | `[ESP]` return PC, `[ESP+4]` first dword, `[ESP+8]` second dword; all12 readable bytes within one checked guest mapping |
| EAX | First overwritten by stack arguments, finally signed second argument divided by2 with truncation toward zero |
| EBX / EBP / ESI / EDI | Preserved full32-bit values, including all subregister bits |
| ESP / return | RET8 yields entryESP+12 and the exact captured guest32 return PC |
| Guest memory | Only the five global dword writes below; stack and other mapped bytes remain unchanged |
| Integer flags | Final SAR count1 defines CF/PF/ZF/SF/OF; OF=0, DF preserved. Observe mask0xCC5. AF is undefined and needs an explicit translation policy. Other supported entry flag bits are preserved. |

MOV and CDQ do not supply new flag values. SUB flags precede the final SAR and
must not accidentally become its final AF guarantee. Existing SHL5 fixture
acceptance does not validate SAR1. Every exact instruction and the real function
IR need admitted original/native evidence before execution is enabled.

The isolated experiment stack is a byte-backed4096-byte RW mapping at0x20001000
with surrounding inaccessible guards. ESP may be unaligned if its entire frame
fits. The outer return sentinel0x10000100 belongs solely to the authored host
return-capture route; it is not a callable game function or a host pointer in guest
memory. Record the real caller edge0x5995DD→0x558290→0x5995E2 separately. That
edge does not authorize executing the unclosed caller continuation.

## Global, object and import mappings

The function writes `[0x72C1E4,0x72C1F8)`,20 bytes: ECX at+0, original EDX at+4,
first stack dword at+8, second at+12, and its signed half at+16. The encompassing
page `[0x72C000,0x72D000)` lies wholly in the writable `.data` virtual zero-fill
tail. Its initial4096 bytes must be explicitly zero-filled, not read from an
unrelated file offset. The20-byte initial digest is
`de47c9b27eb8d300dbb5f2c353e632c393262cf06340c4fa7f1b40c4cbd36f90`.
Fresh disassembly also records other functions that directly read or initialize
those globals; they are not executed by this isolated slice.

Map the page RW with checked guest32 accesses and compare every byte before/after,
so overlapping/partial/out-of-range writes cannot pass. Selected code is RX in
the execution recipe and immutable. No selected object or IAT/import mapping is
needed; unexpected object/import dependencies are rejected. The deferred timer
contract would separately require read-only guest IAT identity, a frozen
WINMM.timeGetTime route, its real32-bit return/stack semantics, and live API
checks outside a deterministic oracle. This selection does not claim that work.

## Floating, vector and host context

Each isolated guest thread owns its complete3504-byte Remill State, logical
raw80 slots, x87 CW/SW/TOP/physical abridged FTW, independently coherent full
physical tags, vector2048 bytes, MMX128 bytes and byte-backed mappings. Logical
ST(i) maps to physical(TOP+i)&7. Preserve every logical80 payload byte, including
empty payload storage, and all FP/status/tag/vector/MMX fields through this
integer-only function. MMX/x87 alias semantics are not inferred from separate
storage preservation and must be reviewed before admitting MMX instructions.

Planning admission permits twelve masked CWs (PC0/2/3, RC0..3), coherent TOP0..7
and arbitrary physical occupancy holes. Occupied raw80 inputs are restricted to
canonical normals, signed zeros, infinities and quiet NaNs. Extended signaling
NaNs, subnormals and unsupported encodings remain rejected; empty raw80 storage
has no numerical claim. Entry SW masks exclude ES/busy, carries the requested
TOP and preserves sticky/status bits. Full tags must agree with actual occupied
raw80 classification. Guest x87 pointer/opcode/control metadata must remain
unchanged through this integer slice. Further FP instruction admission requires
the relevant exact instruction/status/exception policies.

Native entry uses the Win64 host ABI with explicit State*, guest32 PC and checked
memory owner, while guest calling/return semantics stay32-bit. Host pointers
exist only in host code and mapping owners. No guest integer is cast into native
code. Save and restore host x87/SIMD environment on every normal/error exit;
guest sticky FP state is separate from host FPU state. Root's earlier authored
context-preservation gate supplies storage precedent, not execution of this body.

## Routing, isolation and hard failures

Bind the route to `(image SHA, entry VA, complete code SHA, translation/source/tool
identity)` before freezing. Generated and explicit original routes have distinct
identities; an authored replacement must not silently recursively select itself.
All direct/indirect dispatch uses the same registry decision. This selected
function has an **empty outgoing target set**. Any discovered CALL/indirect
target, altered body, wrong return PC/cleanup or unreviewed helper fails before
execution. Register the return-capture route before execution and validate its
edge before entering a callee. The real incoming edge remains separately pinned.

One host owner controls each guest thread's State/stack/global snapshot and frozen
registry; context identities cannot be reused concurrently. Registry mutation,
shared writable globals and concurrent execution require a new synchronization
and guest scheduling contract. Proposed context admission rejects callbacks,
reentrancy, SEH, TLS/FS, concurrent execution, host pointers in guest data, unknown
metadata fields and claimed translation evidence. No guest SEH/TLS/process/DLL
loader, callback API, system/privileged instruction, unsupported FP/SIMD family
or exception delivery is admitted by this contract.

## Evidence and reproduction

`inspect_image.py --image MW3/Mech3.exe` executed against the actual admitted image
and records complete function hashes, instruction boundaries, CFG/call/return
edges, global file/zero-fill mappings, import identity and tool/source hashes.
Asset-free tests exercise wrong image/code/global/target/return/state/route,
unsupported dependencies, malformed storage, all2048 TOP/FTW mappings and twelve
CW/twoDF preservation contexts. Missing/wrong private input is tested as failure.
Execution is explicitly blocked without an exact validated translation; a fake
"passed" metadata object is also rejected. Existing runtime and prior gates are
unchanged. M3 must supply the real slice translation, original/native O0/O2
comparisons, full register/live-flag/memory/FP preservation and rejection controls
before replacing this admission-only status with execution acceptance.
