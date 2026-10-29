# First MW3 function: sub_00409ED0

Static contract reviewed on 2026-10-06. **G2 passed on 2026-10-07:** 16,609 actual
original-x86 inputs match generated native x64 at O0/O2, with zero mismatches
and 49 rejection controls. See the [experiment record](../../../docs/archive/mw3-leaf-experiment.md).
This function computes an address; its gameplay role
and original source name are unknown. The selected slice has no API, global,
floating-point, exception, or indirect-call dependency.

## Identity and boundary evidence

| Field | Reviewed value |
| --- | --- |
| Profile | `mw3-us-1-2-retail` |
| Image SHA-256 | `95bc2c114c9b2e5c5ada8e40ca78cc79470f862e45313ffad0d1e8e6d4d916bf` |
| Label / entry VA | `sub_00409ED0` / `0x00409ED0` |
| Entry RVA / file offset | `0x00009ED0` / `0x000092D0` |
| Extent | 22 bytes, VA `[0x00409ED0, 0x00409EE6)` in read/execute `.text` |
| Slice SHA-256 | `560c17c210dd7fedd7de601f42570c2a0473fa71962c13cfa85a005509a77c65` |
| Decoding | LLVM 21.1.8 and Remill 6.0.1 using XED v2025.06.08 |
| Instruction lengths | 4, 3, 3, 2, 7, 3 bytes; complete 22-byte coverage |
| Flow | One straight-line guest block, one return at VA `0x00409EE3` |

**Observed:** the direct call at VA `0x0040516E` targets this entry. The caller
starts at `0x00405160`, saves ECX, passes a zero stack argument, restores ECX for
the call, then consumes EAX as an address. The return cleans the argument.
The preceding routine returns at `0x00409EC7`, followed by padding through
`0x00409ECF`; padding also separates this slice from the next routine at
`0x00409EF0`. There are no calls, interior branches or shared tails in the slice.

The local linear disassembly contains one direct call to this entry and no
decoded direct jumps into its interior. A separate search found no literal
four-byte entry VA in the image. Neither establishes complete incoming-reference
recovery: computed references and misdecoded data remain possible elsewhere.
The isolated experiment admits only the reviewed entry, not interior entries.

**Inferred:** ECX supplies a base/object address and the single stack argument
is an index. A base plus fixed offset and stride is consistent with a member-array
address helper. Object type, valid application index bounds and gameplay purpose
are **unknown**; do not assign a gameplay name from this inference.

## Exact isolated execution contract

Let `n` be the little-endian 32-bit word at entry `ESP + 4`, `b` be entry ECX,
and `s` be entry ESP. All arithmetic below is modulo `2^32`.

| State | Return behavior |
| --- | --- |
| EAX | `b + 188*n + 312` |
| EDX | `47*n` |
| ECX, EBX, EBP, ESI, EDI | Preserved bit for bit |
| ESP | `s + 8`: return address and one argument consumed |
| EIP | Entry stack return address; require the harness capture sentinel |
| Memory reads | Four bytes at `s + 4`, then four bytes at `s` on return |
| Memory writes | None; compare the entire initialized guest payload |
| Segment assumptions | Flat 32-bit Windows stack, SS base zero |
| FP/vector state | No x87, MMX or SSE instruction in the reviewed slice |
| Calls and static data | None; the computed EAX is not dereferenced by this slice |

The original ABI is consistent with an x86 member helper using ECX and callee
argument cleanup. This is not a host x64 C++ ABI: the comparison must initialize
the guest registers and stack explicitly. EDX is observably clobbered even if a
caller ignores it. All 32-bit `n` and `b` values are admissible for **isolated
arithmetic testing** because neither is dereferenced here; that does not establish
valid object/index values for subsequent game code.

Final CF, PF, AF, ZF, SF and OF come from 32-bit subtraction of `n` from
`t = (48*n) mod 2^32`, giving `r = (t-n) mod 2^32`. The independent oracle must
check CF as `t < n`, AF as bit 4 of `t xor n xor r`, ZF as `r == 0`, SF as bit 31
of `r`, PF as even parity of its low byte, and OF as bit 31 of
`(t xor n) & (t xor r)`. Subsequent address calculation and return preserve these
flags. DF is preserved; comparison keeps the existing safe entry-flag policy.

The harness domain requires `s` in initialized read/write guest payload
`[0x20001000, 0x20002000)`, with at least 16 bytes of margin at both ends;
unaligned `s` is allowed. The return word at `s` must point to the recorded
capture stub in the read/execute guest code reservation. Entry EFLAGS contains
fixed bits `0x202` plus only bits in mask `0xCD5` (the six arithmetic flags and
DF); trap and other control flags are not admitted. All other GPR inputs may
vary freely. This leaf has no explicit failure branch; an unreadable stack,
invalid return target or unavailable code reservation is a harness admission
failure or hardware fault, never a successful case.

The earlier shift has architecturally undefined intermediate AF/OF. They are
overwritten by the subtraction before return; there is no intervening branch,
call or read of those values. No return arithmetic flag is undefined.
Remill emits two `__remill_undefined_8` calls for those intermediates. The explicit
`mw3-helper` adapter profile proves that both values feed only the exact AF/OF
byte stores, then are overwritten along one unconditional block chain before
observation. Only after that proof does it supply an arbitrary zero intermediate.
Loads, aliases, tainted overwrites, State escapes, unknown calls and alternate
paths fail. All six final arithmetic flags remain defined and compared. An
independently authored shift fixture exercises the same policy at O0/O2.

## Completed native comparison

The original Win32 worker executes the admitted bytes at `0x00409ED0`, in the
committed read/execute page `0x00409000` inside a fixed guest reservation. The
reference host's preferred base is `0x18000000`, retaining relocation metadata
for Windows host compatibility; guest allocation collisions still fail. The
flag-preserving return stub occupies a separate code page at sentinel
`0x10000100`. Capture scratch storage is outside the compared payload.

Both x64 workers statically link Remill-generated LLVM objects, without an
interpreter/JIT path. The adapter verifies unchanged State storage, 32-bit guest
addresses, reviewed external helpers and the actual guest entry. Full image,
slice, source and generated-artifact identities bind the experiment.

The 16,609-case corpus contains 6,608 directed cases, 10,000 random cases with
seed `0x3434`, and one recorded Training index/base pair. All 128 safe entry
flag patterns occur, each final flag has set/clear outcomes, and 12,153 stacks
are unaligned. Independent contract checks validate original and native results
before full pairwise comparison: eight GPRs, six arithmetic flags, DF, return
EIP, ESP +8, termination and every byte of the 4,096-byte payload. All 49
admission, comparator and worker rejection controls pass.

Offline verification independently regenerates the corpus and revalidates the
saved original/O0/O2 outputs and provenance. The Training pair supplies only
`n` and ECX; remaining entry state is authored. This is sampled isolated-leaf
equivalence, not whole-game x64 execution or floating-point validation.

The fallback shortlist is `sub_00409850` (read a word through ECX and add eight)
and `sub_00409D80` (store an argument and its square). The first is simpler but
requires pointed-to data; the second introduces multiplication and undefined
final flags. Neither has an executed comparison or an admitted extraction record.

## Local evidence and reproduction

The public [slice identity](../symbols/sub_00409ed0.json) contains no game bytes.
Run the following from the repository root:

```powershell
C:/Python314/python.exe tools/analysis/extract_mw3_leaf.py MW3/Mech3.exe
```

This writes only to ignored research storage, preserving the installed game.
Changed image bytes, entry RVA, length, slice digest and a public output directory
were rejected in six local admission controls, with no new output directories.
Evidence is in `reports/mw3-recon/review.json`, `slice.json`, `leaf-with-bytes.txt`
and `sub_00409ed0-guest.ll`; proprietary slices and generated IR stay private.
The extraction record itself performs no execution. Its immutable admission
metadata retains the initial static-review label; the separate G2 verification
records subsequent native execution. The [G2 recipe and evidence summary](../../../docs/archive/mw3-leaf-experiment.md)
describe `build_mw3_leaf.ps1 -RunComparison` and the frozen result identities.

## Authored x86 replacement experiment (verified 2026-10-07)

The user selected a behavior-preserving replacement of this helper with verified
call logging. The separate [in-game hook tool](../../../tools/in-game-hook/README.md)
now implements the reviewed arithmetic in authored C++ with a MASM entry/return
bridge. It installs a process-local jump in the original Win32 game, preserving
the installed executable. This experiment is **not** the native x64 G2 test above.

The Win32 Release build passes MSVC `/W4 /WX`. Its latest offline run compares
10,400 original-x86 versus authored-x86 cases, rejects seven comparison
corruptions, and passes 64 actual-thunk cases including preserved FP/vector
state and caller-owned memory. Exact source, DLL, launcher and image identities
are recorded in `reports/mw3-in-game/20261007-060648-615224-95ac7622/build.json`.

The same admitted DLL passed those gates inside MW3 and logged installation
before the game entry point. **One actual game call is now verified**, from
reviewed return site `0x00405173`, in process 7476. The strict verifier accepted
the source/binary hashes, original/reference comparison, register and defined
flag checks, return stack delta and isolated payload checks with zero mismatches.
The captured input has index `n=0`; only one distinct live input is represented.
The user separately confirmed full launch into Training. This satisfies the
narrow first-function replacement test, without establishing an extended
gameplay soak or native x64 execution.

Private frozen evidence is in
`reports/mw3-in-game/20261007-060648-615224-95ac7622/verified-snapshot/`:
the build record, offline self-tests, actual game trace, and `verification.json`
including the user's observation. The live passive collector session is
`reports/mw3-monitor/20261007-060648-8c372706/`. The default observer debugger
was removed after its attached session exited at the menu with invalid-handle
status; passive retries reached the menu and Training.

Earlier hooked sessions on 2026-10-06 lacked actual call evidence. The first
of those sessions (process 3468) showed a blank capture
and was closed. A controlled second launch (process 15056, evidence directory
`reports/mw3-in-game/20261006-200016-925/`) used `OutputAPI=d3d11warp` with the
same DLL. Its loaded `D3D10Warp.dll` and main-thread sample with game return
`0x0058FDC2` show software rendering selected and the original message loop
reached. Its capture remained blank and did not prove visible gameplay or a
graphics fix. The exact original graphics file was restored for future launches.

The expected real return site is `0x00405173`. In each actual call, the reference
executes the original leaf on captured inputs in isolated memory before authored
outputs are returned to the game. Logged memory equality covers that shadow
payload; it is not a comparison of every live game-process byte. Logging adds
scratch stack use and synchronous I/O, so this probe is not a performance fix.

Further local caller review found the direct call supplies constant index zero.
The enclosing caller is reached while selecting/loading a map image. Mission
loading is therefore the next discriminating trigger; the precise object type
and any indirect-call paths remain unproven.
