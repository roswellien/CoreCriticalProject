# Next initializer batch: 26 callback registrations

Prepared 2026-10-09 alongside the selected 28-root work. This unit adds the exact **26 remaining initializer roots whose normal direct closures require only `_onexit` / `__dllonexit`**. Every selected root has a decoded normal closure without FS instructions or unresolved controls. It can be implemented alongside environment construction; complete original CRT scheduling remains a later integration requirement.

The [static recovery](../../reports/m4-onexit-batch-recovery/recovery-r3/report.json) pins all 26 original table cells, 26 literal registered callback addresses, 63 normal game body entries and 579 unique normal instructions covering 1,894 original bytes. Registered callbacks are separate: 51 body entries, 1,549 unique instructions and 4,349 original bytes. These counts describe source preparation, not native execution or accepted initializer coverage. The [physical source check](../../reports/m4-onexit-batch-recovery/check-r1/report.json) passed 4,641 literal row checks and rehashed 81 current bindings.

Recovery SHA is `7195aa825cde0c1d47279f285f66604b2fcd0eb66e1d88419d9eb4e7360170ee`; check SHA is `10b820bd8f4979764982e953fcf0fd8dc99836464cbbf29731804e47cfc9f6ff`. Existing accepted evidence is unchanged. The earlier r2 detailed extension failed its exact end-boundary check; r3 corrects that boundary and is the current preparation.

## Establish the real registry

Carry a fresh, live accepted heap and critical-section owner. Execute the original game sentinel stores at `5AC3D8` / `5AC3E2`, setting `9A17EC` and `9A17F0` to minus one. Record any explicitly scheduled source fragment as research invocation; do not publish these values from the host or resume cleaned captures.

The actual CRT producer is `78004482`, referenced by original initialization-table cell `78037C18`. Its original malloc CALL requests 128 bytes, publishes the owned begin pointer at `7800448F` into `7803788C`, zeroes the first DWORD at `7800449A`, publishes next at `780044A2` into `78037888`, and returns at `780044A7`. Initial malloc failure publishes begin zero and reaches `_amsg_exit` at `7801E2D4`; that fatal dependency must refuse until implemented.

Game wrapper `5AC110` selects `_onexit` through IAT `5BB52C` when the source-established game begin is minus one. Otherwise it passes the callback and addresses of game begin/next through `5AC580` and IAT `5BB530` to `__dllonexit`. Zero PE globals are insufficient input for either an initialized callback vector or the alternate table path.

## Complete one functional registration batch

Reuse the actual mode-1 heap/malloc/free, normal FS frame handling, native critical-section ownership and direct strict capture transport. `_onexit` acquires lock 13, including its genuine lazy initialization. Typed native **HeapSize** at `780015B5` / IAT `7802E1DC` supplies actual capacity; requested allocation size must not substitute for that witness.

Execute the 26 original roots in their actual relative table order on persistent State, FX, pages and owners. Each root passes its literal guest callback address to `5AC140`. Verify source constructor/global writes, ordered callback appends, begin/next updates, real CALL/RET frames, return EAX and arithmetic flags. Provider success returns the callback; the game wrapper derives zero or minus one. Registration failure retains preceding source writes and does not invent rollback.

Growth requests actual `_msize` capacity plus 16 through original realloc `780019F1`. The mode-1 path rounds size and invokes typed native **HeapReAlloc** at `78011C27` / IAT `7802E0B4`. A real successful move must commit full native backing and checked guest alias ownership together; null retains the old allocation and bytes. Source code relocates begin/next and preserves existing callbacks. Actual HeapSize may exceed 128, so the 26 roots may not trigger growth. A directed replay of original roots can cross measured capacity and is labeled research replay rather than original startup.

The initial domain is source-established mode 1, newmode zero, an owned nonnull table and bounded positive growth. Mode 2/3, new-handler calls, realloc null-input/zero-size behavior and unsupported fatal termination remain explicit dependencies. The [whole-batch contract](../../reports/m4-onexit-batch-recovery/recovery-r3/whole-batch-contract.json), [selected mode-1 spans](../../reports/m4-onexit-batch-recovery/recovery-r3/mode1-selected-spans.json) and [new API contracts](../../reports/m4-onexit-batch-recovery/recovery-r3/new-api-contracts.json) supply exact source boundaries.

## Acceptance and remaining cleanup

Require O0/O2 native registration and growth, independent original-BEFORE source comparisons, whole State/FX/pages/ordered accesses, and owner cleanup. Target wrong/stale/foreign aliases, source/IAT/callback identity, permissions, partial relocation, premature cleanup and poisoned retry. Actual API failures and authored fault refusals retain separate evidence scopes. After observing the live ordered vector, release its allocation through the genuine free owner before destroying the heap.

Successful registration stores callback addresses; it does not execute them. The [separate callback inventory](../../reports/m4-onexit-batch-recovery/recovery-r3/callback-dependencies.json) includes MFC deallocation, virtual destructors and unresolved dispatch. Callback `4C49C0` alone reaches 1,138 conditional instructions and 13 unresolved sites. Original reverse dispatch at `78005560`, full exit/flush behavior and callback execution remain later contracts. Guest callback values must never be passed to Windows as native function pointers.

If selected 28-root acceptance and all 26 registrations pass, the selected initializer target becomes **54/144**. This preparation adds zero acceptance credit and establishes no original DLL attach, full startup, native window/menu or gameplay.
