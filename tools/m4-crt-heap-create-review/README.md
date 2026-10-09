Independent HeapCreate ownership review
======================================

This gate borrows the same 3504-byte State, separate 512-byte FX image, real mainargs boundary and eleven Runtime call records. The explicitly authored scheduler changes only State EIP to the original attach fragment. It maps one additional literal raw RW page at 78035000, while retaining all seventeen prior pages. It does not execute original attach or DllMain.

The four heap COFF objects and the other twenty-two guest objects are unchanged. The success path executes 48 original bytes at thirteen source PCs and ten source DWORD accesses. A separately recorded API return-word read supports the finite Win32 stdcall model; the same provider body then performs the genuine token store and mode-selector CALL. The gate stops before the mode-selector body at 78003A0C. Full heap initialization and allocator admission remain incomplete.

The real API uses HeapCreate(0,4096,0). A private eight-byte HANDLE slot acquires ownership immediately. The guest receives the independent token 48450001. Genuine translated source publishes that token; observer metadata cannot authorize native cleanup. Actual HeapDestroy success closes ownership. An injected NULL control skips creation and follows the source TEST/MOV0/JE only to the bounded missing cold block. An injected cleanup skip precedes a successful real fallback release; it is not an observed OS failure.

The independent corpus covers six ordinary original-BEFORE inputs, twelve author controls, and forty-eight additional scenarios per optimization. One additional scenario positively verifies the closed duplicate-cleanup path. Every actually created heap is checked while live using process heap enumeration and HeapValidate, then checked absent after release. Caller hardware, complete State/FX/eighteen pages, first fault, owner cleanup and poisoned retry are verified. These compiled fault controls do not supply a complete causal source-model oracle.

Ordinary snapshot output leaves the actual incoming heap scheduler LastError at zero. A separate six-case fixture per optimization explicitly sets a nonzero host LastError immediately after the real mainargs-before checkpoint and before the unchanged heap scheduler. It changes no guest state or source bytes, and verifies success, injected NULL, post-creation exception, injected cleanup skip and metadata refusal. Both actual API witness error reads and scheduler restoration are checked.

Current evidence:

- [Source contract](../../reports/m4-crt-heap-create-review/source-r1/report.json): independently recovered exact source/import/page facts; no execution credit.
- [Source/ABI/COFF audit](../../reports/m4-crt-heap-create-review/audit-r1/report.json): unchanged twenty-six objects, full named State ABI and exception unwind, private authority and actual error reads.
- [Native corpus](../../reports/m4-crt-heap-create-review/native-r1/report.json): 132 scenarios, 6,198 recorded assertions, 36 token denials, 70 actual creations and 70 successful destructions.
- [Hardware/inventory check](../../reports/m4-crt-heap-create-review/check-r2/report.json): 264 actual rich hardware pairs, 548 hardware corruption denials, 27 inventory/API/ownership denials.
- [Nonzero caller-error fixture](../../reports/m4-crt-heap-create-review/caller-error-r2/report.json): 12 additional scenarios, 652 assertions, 24 hardware pairs, 10 actual creations and 10 successful destructions.

Together the two independent corpora have 144 scenarios, 6,850 assertions, 288 actual hardware pairs and 80 matching actual creation/release pairs. Both native optimizations are covered. Host hardware validation preserves meaningful raw 80-bit x87 values, complete legacy metadata, CW/SW/FTW, MXCSR and nonvolatile XMM6..15 using the unchanged frozen validator.

All current records and source files are frozen after sealing. Failed or superseded compile/check receipts are retained as history-only anchors. The first main checker attempted a nonzero-error expectation that disagreed with the correctly recorded zero value. The separate caller-error checker initially used an unsupported generic path object; its already successful O0 native execution and bundle were reused with the exact frozen LogicalReader, without rerunning the worker.

The API contract follows the Microsoft [HeapCreate](https://learn.microsoft.com/en-us/windows/win32/api/heapapi/nf-heapapi-heapcreate) and [HeapDestroy](https://learn.microsoft.com/en-us/windows/win32/api/heapapi/nf-heapapi-heapdestroy) documentation. No original executable, game session, mode-selector body, initializer RET, allocator body or complete original startup schedule is claimed.
