# Complete CRT entry compilation preparation

The admitted game's complete entry code now has native x64 object files at
O0 and O2. These objects require checked memory, call, return, import and
ownership bridges before they can be linked into an executable. No startup
or menu execution is accepted by this preparation.

The exact private source recovery covers 148 unique instructions across
eleven roots. The ordinary entry at `0x5AC3A0` contains 118 reachable
instructions. The filter at `0x5AC502`, handler at `0x5AC517`, handler thunk
at `0x5AC586` and exception-filter thunk at `0x5AC592` remain separate roots;
the ordinary control-flow graph does not dispatch them itself. The other
roots cover `_initterm` and control thunks, the empty helper, the control
wrapper, the four-argument WinMain forwarder and the MFC ordinal thunk.

Preparation verifies source bytes against the admitted image, encoded
relative branch targets, import ownership, complete bounded control flow
and LLVM IR structure. Retargeting independently checks every named State
type's size, alignment and field offsets with LLVM's guest and host data
layouts. Both layouts retain all 3,504 State bytes. The derivative preserves
instruction arithmetic and replaces eight direct calls with an explicit
checked-dispatch requirement. Every root also requires an ownership check.
Native exception propagation is enabled across bridge calls; actual guest
SEH dispatch and unwinding still need implementation and comparison.

| Reached stage | Required integration |
| --- | --- |
| FS exception frame and CRT globals | Owned thread context, correct chain installation/restoration, exception scope table and fault transport. |
| `__set_app_type`, `__p__fmode`, `__p__commode` | Connect the previously reviewed provider bodies with persistent State and their actual returned guest data pointers. |
| `_adjust_fdiv` read at `0x5AC408` | Supply the measured initialized provider result before copying it into `0x9A17E4`. The source-file zero does not establish initialized state. |
| Conditional `__setusermatherr` | Connect the reviewed registration leaf and retain the real guest callback address. Callback execution remains a separate dependency. |
| Control wrapper and `_initterm` | Preserve the actual control result, table order and complete persistent state. The selected connected gate remains 26 of 144 nonzero roots. |
| `__getmainargs` | Implement its five real arguments, output pointer ownership, parser/allocator dependencies and failure behavior. The caller does not test its return value. |
| `_acmdln` and inline command-tail scan | Connect the reviewed native command-line writer, retain its owned buffer and execute both quoted and unquoted branches. |
| Startup information, module handle and MFC handoff | Implement reached Win32 contracts, typed guest handles, application construction and initialization. |
| `exit`, `_exit`, `_except_handler3`, `_XcptFilter` | Implement termination and exception behavior; the static graph conservatively retains post-call code until those contracts establish nonreturning behavior. |

The private preparation report is
`reports/m4-crt-entry/preparation-r2/report.json`, SHA-256
`0c67cae86dad6468e082607ebe9d2b2504094829adb28e37b0c082d6e158d724`.
The native object preparation report is
`reports/m4-crt-entry/native-preparation-r1/report.json`, SHA-256
`4c1174a4a68e6d6ea00c75bb053a4f16f68767d841132be9d6defeaecd5c7ed3`.
Both include exact input/tool/artifact identities. The first preparation
attempt's parser-return mismatch and literal source remain preserved.
Original bytes, disassembly and generated translations stay in ignored
private reports.

The next step is to connect the reviewed provider components through these
checked seams and compare the actual startup path. Native window creation,
the retail menu, input, graphics, audio and orderly shutdown remain required
for full M4 acceptance.
