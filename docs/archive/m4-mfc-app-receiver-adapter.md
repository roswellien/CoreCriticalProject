# Controlled MFC application receiver adapter

`runtime/mfc/app_receiver_state.hpp` implements the smallest controlled-fixture
slice of the [receiver lifetime contract](m4-mfc-app-receiver-lifetime-contract.md).
It accepts only the exact staged MFC42 identity and explicitly controlled
fixture evidence. This identity check labels the model's source; it does not
authenticate a loaded DLL. No host pointer conversion, guest-memory writes,
provider execution, callback invocation or host TLS/TEB/SEH operation occurs.

The owned module, thread-slot and application IDs are separate types containing
32-bit guest addresses. An opaque adapter-owned construction ticket saves the
selected module association (`receiver+0x1C`, observed at `0x5F402206`). Explicit
completion publishes the receiver to thread-object `+4` then saved module-state
`+4` (observed at `0x5F40AE5D` and `0x5F40AE75`). Pending construction cannot be
looked up. Callback lookup selects the thread's current module, or an explicitly
supplied fallback when absent, and reads that module's receiver association
(`0x5F40B362`/`0x5F40B36B`). It does not invent a second thread-receiver check.
The fallback factory and TLS-key selection are outside this model.

Publication overwrites only the selected module and thread associations. It
does not destroy the previous application or clear other modules. Switching
and restoring selections can therefore recover another still-owned module's
receiver even when the thread publication differs. Null selection uses the
controlled fallback; null selection plus null fallback yields no receiver.

Failure, explicit destruction, thread teardown and module teardown invalidate
matching associations and pending tickets. Destruction of a replaced receiver
cannot clear the newer receiver. Address reuse needs a new construction ticket.
Module teardown removes selections/fallback references to the retired owner.
These are adapter safety rules required by the contract, **not recovered native
destructor instructions, unwind behavior or implicit allocation semantics**.
Completion while the saved module is no longer current is refused. Calls are
sequential; concurrent access, reentrancy and native ordering/fault fidelity
remain outside this fixture model.

`require_live_dispatch()` always refuses, including after successful fixture
publication. There is deliberately no API to admit live dispatch. Integrating
native callbacks would require an explicit provider strategy and new evidence:
actual loaded/relocated provider identity and imports, initialized module
globals, TLS keys/managers/arrays and slot destructors, factories and matching
allocation/locks, guest exception-chain/unwind operations, complete constructor
success/failure, vtable/ABI capabilities, and callback lifetime/reentrancy.

The static provider-state root check still records
`actual_loaded_mfc_provider: null`. The later
[131-root acceptance](m4-progress-startup131.md) admits a finite current-thread/
codepage fixture with owned TLS/critical-section lifecycles; its zero-index
control refuses before a lazy initialization path. That result does not admit
this complete application construction or callback lifecycle. The active
138-root validation lane is separate and none of its inputs/tools is changed.

`mfc_receiver_lifecycle` covers initialization/identity refusal, publication,
module-authoritative callback lookup, fallback and module switch/restore/null,
failure and ticket ownership/address reuse, replacement/destruction, and owner
teardown. Fixtures contain no game/provider bytes. Run only the new target and
CTest filter in a private build directory:

```powershell
cmake -S . -B build/mfc-receiver -A x64
cmake --build build/mfc-receiver --config Debug --target mw34_mfc_receiver_tests
ctest --test-dir build/mfc-receiver -C Debug -R '^mfc_receiver_lifecycle$' --output-on-failure
```

This adds no initializer/function credit and changes no acceptance ledger or
gate. Live integration remains blocked on the provider/lifetime evidence above.

Verified 2026-10-11 in the private `build/mfc-receiver` directory: MSVC
19.51.36256 x64 Debug build passed with `/W4 /WX`; the focused CTest passed
1/1 (six lifecycle scenarios). Clang-format and whitespace checks passed for
the changed sources. The startup131 acceptance receipt retained SHA-256
`aa9462f30bf4fa6c80ef926488928bb8680f207020e4f0aa166968caaf724061`.
