# M4 startup context and routing contract

This new runtime owns one admitted PE image and uses the accepted, unchanged
`GuestMemory` and PE loader. It provides a required startup foundation; it does
not implement the CRT entry, exception dispatch, all initializers, MFC or menus.
No original x86 instructions run in this runtime.

The admitted image remains `mw3-us-1-2-retail`, SHA-256
`95bc2c114c9b2e5c5ada8e40ca78cc79470f862e45313ffad0d1e8e6d4d916bf`.
Actual-image construction owns a stable copy, admits its complete size/hash,
then uses the frozen loader. An explicit separate authored-fixture factory
cannot register actual-game-domain translations or services. Fixtures are
tests of this runtime contract, with no game-execution credit.

## Persistent machine and thread

One `Runtime` retains the complete admitted image, checked stack/data/heap
storage, ten DWORD CPU views, 512-byte FX view and one aligned 3,504-byte
Remill State. It cannot be copied or moved after construction. Translation
adapters seed hidden State once, bind its complete reviewed LLVM layout, set
guest FS base from `fs_base()`, overlay/capture the known CPU/FX views and
preserve other fields across calls. `mark_remill_seeded()` records that first
adapter initialization. This foundation alone does not prove such an adapter;
each compiled game adapter requires actual original/native comparisons.
The original FP research shows FX512 can contain zero metadata while legacy
ENV28 retains last instruction/operand/selector fields. An adapter must retain
those distinct legacy fields in persistent State; a whole-FX overwrite is not
an adequate legacy environment projection.

The initial policy uses an owned 1 MiB guest stack at `0x20000000`, with
unmapped 4 KiB guards below and above, and a bounded 16 MiB private arena at
`0x30000000`. Stack, guards, arena, TIB and image extents must not overlap or
wrap. Mappings contain guest addresses, never host-address guest pointers.
Initial ESP is the stack top. EFLAGS `0x202`, masked CW `0x037F` and MXCSR
`0x1F80` are explicit starting policies, not observed original CRT startup
state. Actual adapters must admit and compare their broader machine domain.

Only the NT_TIB32 exception head at FS+0, StackBase at FS+4, StackLimit at
FS+8 and Self at FS+0x18 are mapped. FS base is guest `0x7FFDE000`; the host's
FS/GS/TEB is never read or changed. Stack bounds and Self are read-only; only
the exception head is writable. Other TIB/TEB fields are unmapped, and the
typed FS API rejects them explicitly. The precise DWORD layout is checked
against SDK 10.0.26100.0 `NT_TIB32`; Microsoft's
[TEB documentation](https://learn.microsoft.com/en-us/windows/win32/api/winternl/ns-winternl-teb)
identifies the thread structure and leaves other fields reserved. PEB, TLS,
thread creation, last-error/errno and complete CRT thread services remain open.

The real entry at `0x5AC3A0` installs an exception registration through
FS:[0] at `0x5AC3B6` and restores it at `0x5AC531`. Its scope table is
`0x5D0F78`, and its `_except_handler3` thunk is `0x5AC586`. The runtime can
store, inspect and unlink a bounded aligned, ascending stack registration
chain ending in `0xFFFFFFFF`. Handlers must be admitted executable addresses.
This is registration storage only: exception dispatch always reports the
fault address and missing `_except_handler3`/`_XcptFilter` scope/unwind contract.
It does not translate a guest exception into host success.

The arena aligns disjoint monotonically allocated spans and records exact
live ownership. Invalid alignment, interior/double release and exhaustion
reject. Release does not reclaim storage or unmap its bytes. It implements
neither imported `malloc`/`new`/`HeapAlloc` semantics nor their failure/locking
behavior; those measured service contracts remain required.

## Routing and return

A stable typed callback has signature `void(Runtime&)`. Translation bindings
declare a guest entry, cdecl/stdcall/thiscall/internal ABI, stack argument
bytes, nonvolatile-register policy and exact source/native/review identities.
Actual game bindings require the admitted image hash, an executable source
span whose hash matches owned image bytes, native artifact hash and reviewed
gate hash. The build and independent review must establish the association
between that static artifact and the callback; a hash string cannot prove it.
Authored callbacks are restricted to the explicit fixture domain.

The registry freezes before execution and rejects later mutation. Direct
calls resolve a registered guest entry. Indirect calls read a checked DWORD
operand; admitted IAT operands route through separate service contracts.
Services bind the actual slot and measured provider/review identity. Original
read-only IAT dwords remain intact. No raw import or guest address is cast to
a host function pointer, and no missing service returns fabricated success.

Admission resolves a route before creating a guest CALL frame. Each admitted
callback receives a checked guest return DWORD. Exit checks require the
declared return PC, exact ESP including RET12/RET20 cleanup where declared,
and EBX/EBP/ESI/EDI preservation when required. Generated adapters capture
their actual return state; authored/service callbacks may use `ret(n)`.
Nested calls retain the same globals, stack, CPU/FX and complete Remill State.
An outer `invoke` uses an explicit external-return token `0xFFFFFFF0`; the
token is never mapped executable or interpreted as original code.

A measured service callback continuation can admit an exact source span from
a hash-bound original PE32 provider. A separate literal-data parser admits
only the exact recovered staged MSVCRT file and verifies section bounds and
that the span is file-backed RX. The frozen game loader remains unchanged and
continues to reject relocatable DLLs. The runtime copies only the reviewed bytes
into an exact read/execute guest mapping and admits one near-CALL return PC.
The actual named game IAT slot owns the continuation. A callback can use it
only from that active registered service and its exact recovered CALL site.
The service and continuation must agree on provider and gate identities in
either registration order; actual-game source ownership also checks the
MSVCRT library name. The bytes are rechecked when routing and at the generic
native exit, including adapters that capture RET directly without `ret()`.
Provider code/data/imports
outside the slice remain unmapped, and no original provider instructions,
imports or DllMain execute. Admitting a continuation does not authorize a game
translation at a provider address or implement that service's behavior.
The host's actual DLL provider choice has not been observed; this explicitly
selected original provider is the source of this measured service contract.
The immediate required case is staged MSVCRT `_initterm` CALL EAX at
`0x7800150E`, returning to `0x78001510` in the full 28-byte body starting
`0x780014F8`. Native service/artifact association still needs its separate gate.

Unknown targets/imports report a typed reason, current guest site and target
address. Typed Runtime routing/state faults during a callback poison the context,
even if the callback catches the fault. Raw `GuestMemory` exceptions poison it
when propagated; a trusted adapter must propagate every required memory fault
or explicitly fail its call. This API does not track a raw memory exception
swallowed by arbitrary callback code. A failed admitted call remains
incomplete and cannot be retried as successful execution. Side effects from
a failed body are preserved for diagnosis; they are not rolled back or used
as a passing comparison. Native exceptions do not supply guest SEH behavior.

## Initializer ordering

The actual CRT uses `[0x5E0248,0x5E024C)` with one zero DWORD, then
`[0x5E0000,0x5E0244)` with 145 DWORD slots and 144 nonzero initializer roots.
The ledger snapshots every slot/target and validates executable nonzero
targets before execution. It records zero sentinels, completed callbacks and
the first fault. Each slot is rechecked before use; changed pointers reject.
An unknown nonzero root is not skipped, and subsequent roots remain pending.
Failed or completed ledgers cannot be rerun, and a ledger belongs to one
runtime instance.

Ledger orchestration is currently external and single-threaded. It does not
implement the imported `_initterm` ABI, CRT ordering/termination, or native
execution of all 144 roots. The diagnostic host has no game translations or
services registered: startup stops at `0x5AC3A0`, and ledger orchestration
stops at the first missing root `0x40FFE0`. Actual image/table/thread inspection
and these precise denials give no startup or menu completion credit.

## Build and proof

The standalone `tools/m4-runtime/CMakeLists.txt` links frozen PE-loader and
guest-memory source files without editing them. A fresh private build recipe
retains literal source snapshots, tool/artifact hashes, actual authored
contract controls and actual admitted-image inspection/causal denials.
M1–M3 and the accepted image/first-initializer source and maps remain unchanged.
Before this new service-continuation extension, runtime r4's fourteen literal
sources and restricted independent review were preserved. The physical durable
aggregate at `reports/m4-runtime/durable-r4-chain-r1` replaces historical live
source paths with those exact copies and retains the old maps as documents.
Runtime object layout changes in this extension: an old compiled chain adapter
must remain with its old runtime; a new integration needs a fresh complete build.

Required remaining proof includes static game adapter association, complete
startup machine state, CRT imports/globals, SEH dispatch/unwind, every reached
initializer and application callback, measured service contracts, resources,
native window/menu creation, graphics/input/audio and end-to-end original
startup/menu comparisons. Full M4 remains open until those requirements pass.
