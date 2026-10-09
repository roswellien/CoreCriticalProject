# Connected CRT math-error registration

This isolated AMD64 research worker runs the unchanged FDIV writer, then the
actual translated game CRT entry through `MSVCRT!__setusermatherr`. The provider
leaf at guest address `0x7800B38F` clears its source-valued global `0x780392B8`
and stores the game callback DWORD `0x51E7B0` at `0x7803B0C4`. The callback is
registered as guest data; this worker does not invoke it.

The existing persistent Runtime, 3,504-byte Remill State, floating-point image,
provider pages, CRT globals and game exception frame carry through the entire
sequence. Only the declared outer ESP/EIP transition and source operations
change them. Three additional provider pages have disjoint ownership:
`7800B000` is RX and `78039000`/`7803B000` are RW. All three contain complete
literal raw source pages. The last data page includes source padding beyond
the `.data` virtual extent, retained explicitly from the aligned raw extent.

The frozen O0/O2 matherr leaf objects use an exact token dispatcher to reach a
private derivative of the reviewed paired Context. That derivative removes
the original standalone global bridges and adds one observation callback
inside the existing exception-safe execution block. The actual leaf objects,
shared r9 Runtime, FDIV Registry and prior game entry objects remain unchanged.

The next source call is the actual control wrapper `0x5AC5A0` at `0x5AC431`.
It remains an explicit unresolved translation. Native menu startup is not
provided by this bounded worker.

The current frozen submission is `preparation-r3`, `build-r3` and
`execution-r3` under `reports/m4-crt-entry-matherr`. Each optimization level
executes the same 24 direct original FDIV BEFORE inputs, followed by 24 causal
negative scenarios. The author observer checks the full matherr leaf and
caller continuation, but independent full source and compiled review are
required before acceptance.

Capture phases include writer before/after, entry before invocation/projected,
matherr before projection/projected/after, final entry fault and poisoned retry.
Each phase saves State, Runtime and State CPU, floating-point image, all 14
complete pages, CRT globals, three owned NT_TIB fields and literal source bytes.
`matherr-events.bin` contains five `(address,value,width,write)` records;
`matherr-job.bin` contains slot, original IAT word, frame, return, argument,
step, used, active, failed, complete, first fault PC and first fault address.

New controls 13–24 change leaf source, raw matherr IAT, zero/callback write
permissions, callback argument after its real PUSH, return word after the
callback store, EBX, EAX, event order, initial zero/callback page integrity,
and a throwing observation callback. Controls 1–12 retain the previous FDIV
and CRT prefix cases. Every entered failure retains its prefix and rejects a
poisoned retry. Direct caller checks cover legacy ENV28, x87 CW/SW/tags and
physical raw80, MXCSR and seeded Windows ABI XMM6–15. Volatile XMM0–5 are
observed without an equality claim. The required callable entry boundary is
`data_boundary_initialize`: it saves FX64 and legacy ENV28 before execution,
catches the required startup stop or fault, then restores the saved caller
state before returning its Boolean result. This guard is part of the callable
implementation. An inner Context guard provides additional restoration during
unwind; it does not replace the outer guard. Independent tests additionally
exercise nonzero FIP/FDP/CS/DS/FOP and live host x87 stacks.

Build using bundled `pwsh.exe -NoProfile -ExecutionPolicy Bypass -File
tools/m4-crt-entry-matherr/build_v3.ps1 -OutputDirectory <fresh private directory>`.
`run.py <build-name> <fresh-run-name>` executes both pinned workers;
`observe.py <run-name> <fresh-observation-name>` checks raw captures. An
independent C++ harness can define `MW34_ENTRY_MATHERR_NO_MAIN` and include the
frozen prepared composition without its terminal command-line main.
