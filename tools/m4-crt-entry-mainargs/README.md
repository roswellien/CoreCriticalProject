# Bounded compiled argument startup prefix

This additive native research worker extends the accepted CRT startup chain
through the literal 66-byte staged MSVCRT `__getmainargs` export and its full
140-byte ordinary argument builder. Actual source CALL `0x7800BA99` enters the
builder at `0x7800BBBC`; the original builder prepares `[NULL,0x7803B3F0,260]`
and executes its real import CALL at `0x7800BBD0`. The typed supervisor verifies
the unique source `KERNEL32.dll!GetModuleFileNameA` slot `0x7802E018`, raw value
`0x343B0`, actual argument words and CALL return word `0x7800BBD6`, then throws
the public unresolved-import Fault. No OS filename result or argument-parser
return is substituted.

The source objects are prepared in `../m4-crt-mainargs-recovery/recover.py`.
Their instruction bodies retain the literal CFG, including all later parser,
allocator, error and copyout paths. Each exported root has one reversible ABI
name change. Exact direct source helper declarations remain typed supervisor
boundaries. The integration links only the export and ordinary builder O0/O2
objects from `reports/m4-crt-mainargs/recovery-r3`; the wildcard builders/parsers
are static dependency research without execution admission.

The worker reuses all accepted compiled entry, math-error, control, initterm and
FDIV objects and the frozen Runtime/Session implementation. Sixteen existing
pages are borrowed without mapping or reseeding. The same State3504 and
separate FX512 carry through the source E8 frame. Generic Runtime registration
covers only the actual game `__getmainargs` IAT. Provider internal routing and
the provider import refusal use their own strict current-owner Context, not
generic Runtime provider translation or import registration. RuntimeCPU stays
at the game service frame while compiled State carries the deeper provider
frames. First diagnostics survive exception cleanup and terminal retries.

The stable candidate is `preparation-r2` / `build-r2`, with `execution-r1`
passing 48 positive bounded prefixes and 120 causal denials across O0/O2.
Positive paths record 16 source accesses, four provider routes, eleven Runtime
records (nine completed), and the named provider import stop. Captures include
all sixteen pages, both CPU views, FX512 and 1,140 source identity bytes.
Twelve new controls exercise source/IAT integrity, actual partial PUSH/store
failures, nested return-word closure, an actual nonzero startup-mode store
followed by domain refusal, a real wildcard CALL refusal, malformed ownership,
observer unwind, and the nested builder PUSH. Artificial StateESP mutation is
not introduced in the new controls.

`observe.py` separately checks complete source-owned State/page effects,
opaque-state and FX carry, direct host boundaries and terminal retries. Final
acceptance requires the root instruction oracle plus independent source and
compiled rich-host reviews. Successful argc/argv/environment production needs
filename API, owned command-line and environment initialization, parser and
allocator gates. The accepted selected-initializer count remains 27; full CRT,
main-table callbacks and native menus remain open.

Use fresh private immediate report names with `derive.py`, `build.ps1`,
`run.py`, `observe.py` and `seal.py`. `materialize.py` is a retained one-time
source derivative, not a command to rerun over the final reviewed files.
