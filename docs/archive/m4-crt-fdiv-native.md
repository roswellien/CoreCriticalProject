# FDIV startup writer: native prerequisite

The new native-only gate executes the translated MSVCRT `_adjust_fdiv` initialization writer at `0x78004254`. It obtains a real borrowed KERNEL32 module, looks up `IsProcessorFeaturePresent`, calls the returned function for feature zero, and stores that actual BOOL in owned guest data at `0x78037C2C`. The six preceding pointer stores, complete `_controlfp`/`_control87` integer CFG and final typed FNCLEX run in their actual order. It borrows the accepted r9 Runtime's persistent 3,504-byte State and checked guest memory. Shared r9 is unchanged.

This is an author-tested native prerequisite awaiting independent closure. It has no original dynamic-writer execution or differential equivalence credit, no complete DLL process attach, no whole CRT entry, and no startup/menu completion. The complete original arithmetic fallback is recovered and lifted, but its native entry stops with a required unresolved fault before arithmetic.

The frozen original source recovery is [source-recovery-r1](../../reports/m4-crt-fdiv/source-recovery-r1/report.json). The author submission is [author-review-r1](../../reports/m4-crt-fdiv/author-review-r1/report.json), with physical and historical associations in its [pins](../../reports/m4-crt-fdiv/author-review-r1/pins.json).

## Source and routing contract

The staged provider is exactly 266,293 bytes, SHA-256 `2d5670881a6d13a100e37da297f6eeb876f68b63073a28eb5d650625c60f9bf7`, PE32 x86 at preferred base `0x78000000`. The game import is the actual named MSVCRT data-IAT slot `0x5BB508`. The file's zero at the exported data address is admitted source identity; it does not count as initialized state. The source callback global `0x78037C28` contains the writer's actual address. Its parent's real `CALL EAX` at `0x78004230` pushes return `0x78004232`; the bounded worker supplies that exact frame without executing the parent or DllMain.

The provider source pack owns seven exact pages, with checked source RX, imports/names/constants RO, and data RW. Raw game/provider IAT words remain unchanged. The external typed registry projects only the two exact owning import loads into its semantic routes. It does not register provider slots as invented game IATs or truncate host pointers into guest addresses.

| Actual source call | Typed route | Literal return | Cleanup |
| --- | --- | --- | --- |
| `0x780042A8`, GetModuleHandleA | `0x11000100` | `0x780042AE` | stdcall 4 |
| `0x780042BC`, GetProcAddress | `0x11000200` | `0x780042C2` | stdcall 8 |
| `0x780042CC`, returned feature function | `0x11000300` | `0x780042CE` | stdcall 4 |

Module token `0x11001000` is issued only for a real non-null borrowed KERNEL32 handle. The function route is issued only for its actual named lookup result. Records preserve each host result, the returned module's mapped image/base/path/current file hash, the actual named API target, and the mapped code owner before and after invocation. KERNEL32 may forward to KernelBase; those module identities remain distinct. Only exact names and feature argument zero are admitted. Microsoft identifies feature zero as `PF_FLOATING_POINT_PRECISION_ERRATA`; the implementation records the actual BOOL rather than guessing it from the current machine. [GetModuleHandleA](https://learn.microsoft.com/en-us/windows/win32/api/libloaderapi/nf-libloaderapi-getmodulehandlea), [GetProcAddress](https://learn.microsoft.com/en-us/windows/win32/api/libloaderapi/nf-libloaderapi-getprocaddress), [IsProcessorFeaturePresent](https://learn.microsoft.com/en-us/windows/win32/api/processthreadsapi/nf-processthreadsapi-isprocessorfeaturepresent).

The two actual NULL branches select `0x7802C070`; that entry raises `unsupported_fallback`. Neither NULL path was observed from these actual successful OS lookups. A private authored negative fixture verifies the fallback bridge rejects, and static CFG proof retains both real NULL edges. It grants no successful fallback execution credit.

After every actual function return, the registry validates the guest return word, exact stack cleanup and nonvolatile guest registers. Source/image/IAT integrity is rechecked at each routed operation. Required faults retain their first reason/address/PC and become terminal. Data resolution becomes available only after the actual six pointer stores, real query BOOL write, complete control helper and FNCLEX return. The initialized value can then be exposed as owned guest address `0x78037C2C` for the declared game data-IAT; the game consumer at `0x5AC408` remains a future integration.

## State and FP domain

The full writer admits twelve masked, normalized incoming control words: precision encodings 0, 2 or 3, each rounding mode, IC clear, empty tags, TOP zero and status zero. It requires coherent separate guest FX and State status/control/MXCSR, flat DS/SS, the actual guest FS base, DF clear, and the exact private stack frame. It preserves opaque State storage and distinct legacy metadata in State versus the separate Runtime FX view.

The complete control CFG keeps the accepted typed FNSTCW/FLDCW/FWAIT lowering. The writer selects 53-bit precision through its actual `new=0x10000, mask=0x30000` call. The measured guest-CW normalization preserves its accepted canonicalization; raw reserved bit 6 is not invented as a direct source helper output. No numerical x87 operation follows in this gate.

Typed FNCLEX clears defined status mask `0x80FF` coherently in State and the separate FX status word, including IE/DE/ZE/OE/UE/PE, SF/ES/B. It preserves CW, TOP, tags, complete raw80 storage, MXCSR, legacy metadata and other State bytes. C0–C3 are architecturally undefined; preserving their incoming values is this native representative, not a defined preservation promise or original measured policy. [Intel instruction reference](https://www.intel.com/content/dam/www/public/us/en/documents/manuals/64-ia-32-architectures-software-developer-vol-2a-manual.pdf).

Primitive controls exhaust all 65,536 coherent status words, including nonzero sticky flags, ES/SF/B, all TOPs, condition-code sentinels and live tag/raw80 storage. Twelve incoherent-view cases reject without mutation. These controlled native primitive cases do not expand the full writer's empty TOP0/SW0 admission.

The dynamic Windows ABI permits volatile ECX/EDX/flags. This native representative preserves them at the service boundary. Source `_control87` copies the high half of post-query ECX into two residual stack halfwords at `[writerSP-34, writerSP-32)` and `[writerSP-42, writerSP-40)`. Future original measurements must retain their actual observations and make any defined-equivalence projection explicit. The present gate claims its own native representative exactly, not portable original/native equality for those bytes. Final writer EAX is the abstract control result; the initialized data BOOL comes from the earlier query.

## Evidence and host boundary

[native-build-r3](../../reports/m4-crt-fdiv/native-build-r3/build.json) compiles and executes O0/O2 against the unchanged r9 source. Each level passes 132,866 authored checks over 59 scenarios: 24 actual successful writer records, the exhaustive FNCLEX primitive, 23 early causal admission/state/source/memory faults, and 12 private authored route/fallback/FNCLEX denials. The private active-query fixtures are unit conditions; successful preparation uses real OS lookups, and denied services never manufacture a lookup/result. They do not stand in for completed compiled writer execution.

The author source-instruction model validates all 48 actual writer records, all 97 ordered events per record, three stdcall frames, entire 3,504-byte State, nine complete pages and separate FX512. It reaches 174 actual source PCs from the preserved 204-instruction dependency union. It rejects 720 output/provenance/event corruptions; a separate before-only model checks every literal source/IAT/data page, dirty State/FX/stack fixture and 624 input corruptions. These author models import no independent/root oracle. [Source model](../../reports/m4-crt-fdiv/native-validation-r1/report.json), [entry model](../../reports/m4-crt-fdiv/native-entry-validation-r1/report.json).

The primary `host_before`/`host_after` records are internal full FX512/ENV28 restoration checkpoints inside `Registry.initialize()`. They precede its final cleanup and C++ return. They are not a full volatile SIMD preservation claim across the whole public call.

The separate [native-boundary-r3](../../reports/m4-crt-fdiv/native-boundary-r3/build.json) links those exact frozen libraries. An authored assembly wrapper captures immediately before and after the actual C++ call, before harness FP cleanup. It passes positive writer and real RO-data fault returns at O0/O2: complete observed ENV28, x87 CW/SW/FTW/all physical raw80, MXCSR and seeded nonzero ABI XMM6–15 are preserved. Volatile XMM0–5 remain observations with no equality requirement. Forty architectural/ABI corruptions reject; four volatile-SIMD changes remain admissible. [Boundary validation](../../reports/m4-crt-fdiv/native-boundary-validation-r1/report.json).

The [tooling supplement](../../reports/m4-crt-fdiv/native-tooling-r1/report.json) binds 411 actual compiler-reported headers, generated rules and current provider hashes. It distinguishes primary direct-tool hashes captured before invocation from supplementary post-build hashes of indirect compiler/archive/link/RC/MT/Ninja providers. The RC wrapper argument is observed; no RC child execution is asserted without an actual resource artifact. Named SDK link-library paths are current configured candidates, not an unrecorded historical resolution trace.

## Reproduction and preserved attempts

Use new immediate private report/build directories. Existing output/build directories are rejected before the recipes mutate them. Native raw outputs use `CREATE_NEW`; a failed partial output remains a failed observation. There is no concurrent atomic publisher or general replay replacement contract.

```powershell
pwsh.exe -NoProfile -File tools/m4-crt-fdiv/build_native.ps1 `
  -OutputDirectory D:/Projects/MW34Recomp/reports/m4-crt-fdiv/native-replay-new `
  -ResearchDirectory D:/Projects/MW34Recomp/reports/m4-crt-fdiv/native-derived-r1
```

The final gate binds every earlier literal attempt. Three static adapter attempts exposed RETURN_PC bookkeeping, internal FP branch and reachable-block filtering assumptions; they failed before execution. Native build r1 failed at two mixed-type C++ `auto` declarations. The successful r2 baseline was preserved before narrowing IC admission and adding returned-module metadata/route units. Boundary r1 failed because an empty successful assembly log had not been created; boundary r2's C++ helper honored the ABI and restored the nonvolatile SIMD seed before capture, so its required sentinel assertion failed. Boundary r3 seeds, captures and restores those caller nonvolatile registers in assembly. These failures remain failures, with their exact source copies, objects, logs and observations retained.

This bounded registry assumes serial execution, a stable live Runtime/State borrower, trusted ordinary mapped pages and stable loaded host modules. It is not a general Windows module-loader API, concurrent unload protection, arbitrary hotpatch detector, general thread state/SEH dispatcher, numerical FP synchronization layer or production publisher. General raw mutable GuestMemory fault-swallowing limits of accepted r9 remain explicit. Complete fallback arithmetic, original dynamic writer comparison, provider callback-table orchestration, game consumer integration and full CRT startup remain open.
