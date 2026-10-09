# Original CRT service recovery and native model

This new component recovers four complete bodies from the exact staged x86
MSVCRT file, SHA `2d5670881a6d13a100e37da297f6eeb876f68b63073a28eb5d650625c60f9bf7`.
Its provider choice is explicit research input; the provider selected by the
host for the original game has not been observed. Static recovery and authored
native controls alone do not admit actual game CRT execution or finish M4.

`_initterm` is the complete 28-byte body at `0x780014F8`. It saves ESI on the
guest stack, loads begin/end arguments using its cdecl frame, compares unsigned
addresses, reads each DWORD when reached and skips only literal nulls. Each
nonzero target routes through the native registry at the actual provider CALL
site `0x7800150E`, with guest return DWORD `0x78001510`. Unknown targets or
required faults stop the sequence and retain the observed prefix. The original
provider rereads its caller's end argument on every loop and can observe changes
to future table slots. This service therefore uses an ordered visit ledger,
distinct from the runtime's external immutable-snapshot orchestration ledger.

The native model preserves actual callback volatile register results and the
final unsigned CMP flags, then pops the saved ESI and returns without callee
argument cleanup. Empty/reversed ranges perform no table read. The bounded
admitted domain requires aligned arguments and at most 4096 visits per call;
unaligned or extended inputs are rejected rather than counted as equivalence.
TEST's transient AF is undefined; final CMP defines all arithmetic flags.
The original x86 provider comparison is still pending.

`__set_app_type` loads EAX from its cdecl argument and writes the original guest
provider global `0x78038EE8`. `__p__fmode` and `__p__commode` return stable guest
addresses `0x78038EEC` and `0x78038EF0`. Their twelve source data bytes are zero
in the exact recovered RW section. No host pointer is copied into guest state.
These MOV-only bodies preserve flags and the other CPU/FP state.

A `Session` owns those bounded globals, registers the four typed callbacks and
the measured `_initterm` continuation, and records every reached initializer.
The runtime and session are stable, single-thread objects. The session must
outlive service calls; destruction removes its owner, so later calls reject.
Raw guest memory faults propagate into the runtime's required fault path. A
constructor failure can leave an unusable partial registry and requires a fresh
runtime; it cannot be recovered into successful service execution.

This component uses the separately frozen extended runtime r9. Old compiled
chain adapters remain paired with their archived r4 runtime. New integrations
must compile all shared adapters against the new exact header/library; object
layout changes cannot be mixed.

`__getmainargs`, `__setusermatherr`, `_controlfp`, environment and math globals,
termination, allocator/thread/locale services, exception filters/handler dispatch
and unwind remain unresolved. The real CRT entry and all connected initializer,
MFC/frontend/menu requirements remain open. No missing import returns success.
