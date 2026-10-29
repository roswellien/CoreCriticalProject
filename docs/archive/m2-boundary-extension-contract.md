# M2 stack argument and selected timer provider extension

This distinct authored offline gate closes two limitations of the frozen
[call integration](m2-call-integration-contract.md). It preserves every earlier
source, binary and report. No game process is started. The supported scope is
one synchronous, bounded eight-block chain and one zero-argument DWORD timer.

The exact 1,313-byte authored fixture has SHA-256
`61b236a2a8402d96c48a28340203ae08f1351cf7b3f095ab4b4b817e38e6c667`.
Entry reads and pushes its argument, sets EAX to `0xa5a5f00d`, then CALLs
the generated callee. The callee reads `[ESP+4]`, adds ECX, and returns with
RET4. A full-page global records argument + ECX + global, so computing from
poisoned EAX fails the final oracle even when later code reloads the argument.
The original x86 executes those instructions; the native O0/O2 workers call only
the eight separately lifted and statically compiled blocks through a guest32
registry. The generated direct shim and generated indirect CALL share admission.

Continuations are `0x1000000f`, `0x10000020` and `0x1000002d`.
The direct callee at `0x10000200` pops its four-byte argument; the timer
at `0x10000300` takes no argument; the add/sub indirect callee leaves argument
cleanup to the caller. Actual instruction-written traces capture all three
return PCs and callee stack pointers. Outer RET reaches `0x10000100` with
ESP advanced by four. Every GPR, six arithmetic flags and DF, the return PC,
and all 8,192 stack/global bytes are compared.

The private host Context admits exactly one timer provider before freezing:
`deterministic-uint32` or `WINMM.timeGetTime`. The selected timer bridge calls
that provider once, returns its actual DWORD in EAX, and records one bridge
and provider invocation in both host counters and guest trace words. The actual
returned value is then consumed by the translated indirect add/sub callee.
Provider function/cookie pointers remain private host fields; native guest IAT
and return words remain 32-bit admitted addresses. Unknown/conflicting/null
providers, mutation after freezing, bad callers/targets/frames and unsupported
selectors are rejected. There is no asynchronous callback or arbitrary import.

The controlled corpus uses 4,592 records: the previous 121 edge pairs and 1,024
seeded pairs, plus three arguments at/adjacent to poisoned EAX, each with two
indirect choices and both DF values. The original uses the authored timer thunk
to return the controlled global; the same selected native bridge calls its
controlled provider. These complete records have exact equality.

The separate live corpus uses eight admitted DF0 records with unused timer input
zero. Each worker executes the full authored chain through its IAT and selected
bridge/context. The original Win32 IAT points to a trusted shim that forwards
to the actual Winmm provider on the saved host stack, preserving the declared
guest bridge registers without leaking host scratch frames into guest memory.
The native IAT remains `0x10000300`; its frozen provider calls the actual Winmm
API through the same selected bridge. Actual invocation counts are one per
record; return values are captured independently of request data. Each live
record is checked against its observed provider return, including every CPU,
flag, trace and memory byte. Original and native clocks are measured in separate
processes, so their numerical values need not coincide. The single original
IAT shim address is separately recorded and bound to its executable. All other
memory remains fully specified. Its actual loaded base may differ from the
preferred PE base; the shim RVA is independently bound to the link map. Eight calls separated by 40 ms establish
unsigned DWORD progress; architecture-correct System32/SysWOW64 provider module paths/file hashes and PE imports
are recorded. This is provider/ABI integration evidence, not game timing fidelity.

`timeGetTime` returns an unsigned DWORD millisecond count since Windows startup,
which wraps after 2^32 milliseconds. Progress uses unsigned differences; no
precision-changing multimedia timer request is made. [Microsoft API contract](https://learn.microsoft.com/en-us/windows/win32/api/timeapi/nf-timeapi-timegettime).

Protocol: 24-byte header (`MW34BEXQ`/`MW34BEXR`, version 1), request 60 bytes
(ten CPU words plus argument/global/timer/choice/seed), result 8,256 bytes
(ten CPU words, status/calls/returns/provider-calls/bridge-calls/provider-return,
then two complete pages). Both workers validate the entire matrix and exact
fixture before execution or result creation. Live requires exactly eight
DF0/timer-zero requests. Invalid extent, trailing records, flags, frames,
selectors and fixture identity are rejected with diagnostics and no result bytes.

Logical guest x87/MMX/SIMD State storage remains byte-for-byte unchanged across
the integer/API chain in 96 seeded tests per native. This does not validate
guest floating instructions or hardware FP restoration; those are separate
accepted x87 gates. Callbacks, guest SEH/TLS/threading, additional imports,
unbounded indirect targets, mutable image registries and arbitrary native
function addresses remain unsupported. The selected provider is synchronous;
no address or request field is used as a host function pointer.

The actual MW3 image/import CSV and two static timeGetTime CALL sites are
hash-admitted privately. Only their identity/address metadata is published;
no proprietary machine bytes are embedded in the new tools. Original game
reachability and behavior are not inferred from the authored fixture.

Two initial live-verifier diagnostics are preserved in ignored reports before
their correction: a preferred-base assumption rejected an actually relocated
reference image, and a file-handle path API was unavailable in this environment.
Neither is presented as a CPU/ABI compatibility failure or hidden by removing
an observation. The final verifier checks the actual linked shim RVA and the
architecture-correct loaded system-provider path/PE machine.

The controls exercise eleven rejected IR/profile mutations, 77 rejected worker
admission/routing cases, 18 saved-record corruptions, twelve provenance mutations
and nine live observation/provider/progress corruptions. Eight exact admitted
blocks adapt positively. Each native passes 27 compiled context/provider controls
and 96 whole-chain logical FP/SIMD storage checks. No test is skipped for missing
private image or toolchain evidence; those are explicit failures for this gate.

Reproduce in a fresh PowerShell/Visual Studio process:
`pwsh -NoProfile -File tools/m2-boundary-extension/build.ps1 -RunComparison`.
Replay the saved controlled and live observations with `compare.py --replay`,
`live.py --replay` and `verify.py`. The last verifier uses a separate ordered
stack and signed/nibble flag oracle without importing either comparator.
