# M2 call, globals, import and indirect routing contract

This is a separate authored offline gate, established 2026-10-07. It does not
execute game startup, replace earlier frozen gates, or establish a native game
menu. The fixture is project-authored x86, with a machine-code SHA-256 of
`edc5e8b32eb6fd28b3520a36c6e65ab36fc11cc20136df284ed6851f40f1d6d4`.
Eight admitted blocks are lifted by pinned Remill v6.0.1 and compiled by LLVM
21.1.8 at O0 and O2. Native instruction semantics come from those compiled
blocks; there is no interpreter or runtime translation fallback.

## Observed import and evidence boundary

The admitted MW3 U.S. 1.2 executable has SHA-256
`95bc2c114c9b2e5c5ada8e40ca78cc79470f862e45313ffad0d1e8e6d4d916bf`.
Its ordinary import inventory identifies WINMM `timeGetTime` at IAT RVA
`0x1BB75C`, guest VA `0x5BB75C`. Actual indirect CALL instructions at guest PCs
`0x5996D6` and `0x599716` use that slot. `build.py` checks the complete image
hash, PE VA/file mapping, six-byte instruction identity, import CSV identity,
and records hashes rather than distributing game bytes. Static CALL evidence
does not establish runtime reachability or the game's timing units/update rules.

The selected API boundary is a zero-argument stdcall returning unsigned32
milliseconds in EAX. The differential test uses a deterministic authored x86
timer thunk and an independent host API bridge supplied by the request. A
separate Win32 and native x64 invocations read actual `WINMM.timeGetTime` before/after Sleep;
its changing values are saved independently and are never substituted into the
exact differential oracle. This proves API availability, not timing fidelity.
Each live probe requires a positive unsigned32 elapsed value, so a constant
timer stub fails the progress check.

## Guest state, memory and routing

Each request owns one 3504-byte Remill State and separate checked 4096-byte
stack/global mappings. All guest registers, arguments, IAT slots, code targets,
return PCs and object-like ECX inputs remain unsigned32. Host addresses exist
only in the host registry and memory owner. No guest field contains a native
pointer and no integer is cast to a host code address. Guest memory uses the
existing little-endian checked GuestMemory contract, including unaligned
access, overflow/range and permission rejection.

| Boundary | Admitted behavior |
| --- | --- |
| Outer entry | Guest PC `0x10000000`, one stack argument, cdecl final RET leaves ESP+4 |
| Direct member-shaped call | Target `0x10000200`, ECX input preserved, one pushed argument, callee RET4 removes return+argument |
| API import | IAT slot in guest global page selects `0x10000300`; zero arguments, RET removes return word |
| Indirect call | Guest32 slot selects `0x10000400` or `0x10000500`; one pushed argument, cdecl RET and caller LEA cleanup |
| Continuations | Exact return PCs `0x1000000A`, `0x1000001B`, `0x10000028` |
| Outer return | Exact sentinel `0x10000100`, no duplicate final return |

The registry is configured before execution, bound to the authored image hash,
and then frozen. Duplicate/conflicting entries, conflicting replacements,
registration/selection after freezing, wrong image identities and execution
before freezing are rejected. Every direct and indirect CALL reaches the same
`Context::call` selection. Compiled direct callee symbols are renamed so they
cannot bypass the route shim. Replacements can explicitly invoke the named
original route without selecting themselves again. A native control executes
this path through both direct and indirect entry shims.

CALL instruction semantics in generated blocks push actual guest return words.
The router validates the callee target and admitted continuation before executing
the callee, including the exact caller-to-callee return edge. The return bridge
checks EIP, exact return PC and convention-specific
ESP cleanup. Internal returns return to the generated caller, which routes its
admitted missing-block continuation. Unknown code/return targets report guest
PC and target and fail. A bounded route budget stops unsupported recursion.

Default routes use generated blocks. The timer route explicitly selects the
authored API bridge over its separately compiled original thunk; the active
selection and compiled/original identities are recorded in build evidence.
The bridge's trace/scratch writes are test instrumentation matching the authored
thunk. They are not a claimed part of the real Win32 API's application contract.

## Acceptance and negative controls

Directed operands include zero, sign/carry/overflow boundaries, timer wrap
values, both indirect targets and both DF settings. Seeded cases vary every
register, all entry arithmetic flags, unaligned stack positions and complete
stack/global page patterns. Compare eight GPRs, ESP/EIP, all six defined final
ADD/SUB flags and preserved DF (`0xCD5`), three original instruction-recorded
callee return PCs/SPs, global result, import/target slots, route termination
counts and every one of 8192 mapped bytes. An independent unsigned arithmetic
oracle checks original and each native output separately. Raw saved records
can be replayed without executing either worker.

The adapter admits each exact authored guest IR hash and entry/layout. Unknown
helpers, changed boundaries, altered IR, unsupported floating-point operations,
guest-to-host pointer conversions and indirect host calls are rejected.
Native controls exercise memory bounds/protection, return-frame corruption,
unknown routes, frozen configuration and replacement/original behavior. Worker
controls exercise altered fixture bytes, malformed headers and unknown selector
execution through generated indirect CALL blocks. Source, tool, semantics,
State-header, object, worker, input/output and observed-import identities are
checked before executing comparisons. Live API checks are reported separately.

## Requirements for the next real game slice

Recover each reachable function/block and global range from the admitted image.
Record calling conventions, guest object offsets, exact indirect target sets,
read/write permissions and any IAT requirements. Register translated functions
and selected bridges against `(image hash, guest VA)` before freezing. Retain
one guest context and stack per guest thread when thread execution is added.
The isolated unsigned32 integer registry is reusable, but the experiment is not
a PE loader or a complete Win32 process.

SEH/TLS/FS-relative execution, callbacks/reentrancy, concurrent registry mutation,
host/guest thread scheduling, unbounded computed control flow, overlapping code
entries and guest exceptions remain unsupported. Floating-point exceptions,
stack/tag semantics and instruction-specific status policies remain governed by
the separate M2 floating-point contracts, not inferred from this integer gate.
The native integer/API chain additionally carries seeded logical binary80 stack
slots, all twelve PC/RC control modes, eight TOP settings, nonempty physical FTW,
selected existing exception/status bits, vector and MMX bytes. Exact byte checks
assert these logical guest fields remain unchanged. This is a native storage
preservation control; it does not compare original hardware floating state or
establish floating instruction/exception compatibility.
Select M3's subsystem from verified reachable dependencies without assigning
gameplay purpose to an address-only function.

Reproduce with `tools/m2-integration/build.ps1`, then
`C:/Python314/python.exe tools/m2-integration/compare.py` and
`C:/Python314/python.exe tools/m2-integration/compare.py --replay`.
