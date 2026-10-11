# MFC application receiver and callback lifetime contract

This static contract isolates the MFC state needed before the game can call
application callbacks. It is grounded in the admitted game image and the staged
MFC42 candidate; it does not establish that Windows selected this provider or
that any of these objects were initialized at runtime.

## Source-backed publication path

- The game's application constructor at `0x47F7A0` uses the application object
  at `0x608C88` and MFC application vtable `0x5C3F80`. This game-side link is
  recorded in [application workahead](m4-application-workahead.md).
- In staged MFC42 (`SHA-256`
  `5f66a4d221e24c767aadd3f43a981df53d42f3d73bdf05b518120632099e2fc8`),
  constructor `0x5F4021DF` calls `0x5F401083` at `0x5F4021FC` to retrieve the
  current module state, then stores the result at `[ESI+0x1C]` at `0x5F402206`.
  The saved field is therefore a source-observed module-state association for
  the constructed receiver in `ESI`.
- Derived application constructor `0x5F40AE1B` reads that saved state at
  `0x5F40AE4A`, gets the thread object through key holder `0x5F48F848` plus
  offset `0x108C` (`0x5F40AE4D`–`0x5F40AE58`), and publishes `ESI` at
  `[thread_object+4]` (`0x5F40AE5D`) and `[module_state+4]` (`0x5F40AE75`).
- The accessor `0x5F401083` selects the current per-thread module pointer from
  key holder `0x5F4CB03C`; if absent, source control reaches the shared fallback
  holder `0x5F4CB040` and factory `0x5F40B293`. Its local CFG is not the full
  TLS, factory, lock, or exception dependency closure.
- Callback gate `0x5F40B35D` calls the module accessor at `0x5F40B362`, then
  reads the application receiver from module-state `+4` at `0x5F40B36B`.
  Later virtual calls through that receiver are conditional source targets,
  not proof that the receiver is live or its vtable is usable.

The instruction bytes and selected local CFGs are pinned in the
[provider-state inventory](../reports/m4-mfc-provider-state/recovery-r1/inventory.json),
under `source_facts.app_receiver_publication`,
`source_facts.application_callback_gate`, and bodies at the addresses above.
The inventory binds the game image SHA-256
`95bc2c114c9b2e5c5ada8e40ca78cc79470f862e45313ffad0d1e8e6d4d916bf` and
explicitly records `actual_loaded_mfc_provider: null`.

## Required implementation invariant

Treat the application pointer as a guest object association, not as a host
pointer or an eagerly seeded global. A native callback may resolve it only
through the admitted current module/thread state, after successful complete
construction. Construction failure, thread teardown, module-state switching,
and application destruction must prevent a stale `+4` receiver from reaching
the callback gate. Host TEB/TLS/SEH state must remain separate from guest state.

The smallest useful implementation slice is a typed MFC receiver-state adapter
with explicit provider identity, module-state and thread-slot ownership, and a
construction/destruction transition model. Its first tests should cover
uninitialized lookup, current-thread publication, fallback selection, module
switch/restore, construction failure, and teardown invalidation using controlled
fixtures. It must refuse live callback dispatch until those transitions and the
provider identity are admitted.

## Still unknown / blocked

- The actual Windows-loaded MFC provider, image identity, relocated imports,
  and its initialized module globals have not been observed.
- TLS key allocation, manager construction, TLS array growth/publication,
  thread-slot destructor and callback lifetimes are incomplete.
- The `0x118` thread-module and `0x1090` module factory object layouts,
  allocation failure paths, lock ownership, matching destruction, and
  exception/unwind behavior are incomplete.
- The application constructor chain's complete success/failure behavior,
  vtable capability, reentrancy, ABI state, and receiver lifetime through
  callbacks have not been executed or compared.
- Guest `FS:[0]` exception-chain operations and stack-fault ordering are not
  implemented; host FS/TEB bytes cannot stand in for guest state.

Accordingly, this contract grants no initializer, native execution, window, or
menu credit. The provider identity and lifecycle evidence listed above are the
next required inputs before live callback integration.
