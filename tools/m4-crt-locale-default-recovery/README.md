# Default CRT locale source frontier

This is fresh static recovery from the exact staged `MSVCRT.DLL`. It executes
the LLVM disassembler only. It grants no original provider, DLL attachment,
allocator, lock, locale initialization, parser return or native game credit.
The accepted parser-prefix files and receipts remain frozen.

The original initializer at `78003DD2` pushes selector `-3` and calls `_setmbcp`.
Before resolving that selector, `_setmbcp` calls `_lock(25)`. The source-file
lock slot at `7803708C` is zero, so the lock helper calls original `malloc(24)`.
The first useful bounded native gate is this real nested CALL frontier at
`7800107B → 780012B3`, retaining return word `78001080`. A generic successful
allocation or a nonzero source-file critical-section pointer cannot close it.

With initializer entry ESP `S`, that prefix executes 20 source instructions
and completes 15 source memory accesses. The actual malloc frame has
`ESP=S−76`, `EBP=S−60`, argument `24`, `EAX=25` and `ESI=7803708C`.
The report records every source store/read and all nested return words.
No code-page API, locale-table access, allocator body or source RET is reached.

An explicit initializer subexperiment must borrow a fresh healthy carried
State and its existing mappings. Its scheduling contract must be declared.
The original attach CALL `780018A1` follows the still-unexecuted helper at
`78001897`; scheduling the initializer directly does not prove those earlier
attach operations or original DLL attachment. The accepted parser stop is
poisoned and cannot be resumed by clearing its fault or seeding a new State.

After this frontier, the default path still needs allocation and SEH, lock
initialization/publication/entry, actual code-page outcomes and classification
helper ownership. The import-free reset at `7800E648` is recorded as a separate
static alternative only. It needs an explicit C/single-byte domain and `DF=0`;
it does not establish the default ANSI code page and does not clear `78037AE8`.
The original source also calls it conditionally at `7800E5DE` for a resolved
zero code page or a failed default-selector `GetCPInfo` query. Those source
branches require the earlier lock, resolver and actual API lifecycle.

The current evidence is [recovery-r2/report.json](../../reports/m4-crt-locale-default-recovery/recovery-r2/report.json)
and its [physical pins](../../reports/m4-crt-locale-default-recovery/recovery-r2/pins.json).
The first receipt is preserved; the second corrects only the reset helper's
conditional source reachability, with the native-prefix contract unchanged.
Source zeros prove file identity only. Selected initializer coverage remains
27 of 144.

Run from the project root with a fresh output name:

```powershell
& C:/Python314/python.exe tools/m4-crt-locale-default-recovery/recover.py recovery-r3
```

The script checks every decoded byte against the exact PE, requires each
selected span to be complete and contiguous, records its actual file-backed
permissions and unique API import owners, and hashes every current physical
dependency before and after recovery. Historical receipts are SHA anchors;
their old capture inventories are not recursively expanded.
