# Genuine heap initializer source frontier

This fresh static recovery executes only the LLVM disassembler. The exact
staged CRT source first needs `HeapCreate`; no provider, native worker, game or
API is executed here. All earlier accepted code and receipts remain frozen.

The explicit experiment schedules the real seven-byte fragment at
`7800183C`: `PUSH 1; CALL 780039BF`. Only carried State EIP changes at the host
seam; ESP, RuntimeCPU, prior CALL records and all 17 mappings remain carried.
The source creates the initializer frame at `20001858` with argument one and
return `78001843`. Executing this fragment does not establish its original
GetVersion/attach predecessors or DLL attachment.

The initializer prefix executes seven instructions and six memory accesses.
Together with the fragment, this is **nine instructions and eight accesses**.
The genuine indirect CALL at `780039D0` reads the named original
`KERNEL32.dll!HeapCreate` slot `7802E0A8`, whose raw source value is `3461E`,
and pushes return `780039D6`. The frame is `20001848`, with arguments
`[flags=0, initial=1000h, maximum=0]`. The next gate refuses there before the API.

The XOR at `780039BF` needs one narrowly qualified undefined-AF representative.
The later CMP of argument one against zero defines every arithmetic flag
before the API boundary. The report records both effects, every access, and
the exact source CALL frames.

No heap global is accessed before this stop, so mapping `78035000` is not
needed for this gate. Its source RW bytes remain static identity only. Future
source work stores the actual HeapCreate outcome, resolves the heap mode,
runs mode-specific allocation/initialization and may call HeapDestroy on
failure. Those are separate dependencies, as are allocator SEH and locale
classification.

Current evidence is [recovery-r1/report.json](../../reports/m4-crt-heap-init-recovery/recovery-r1/report.json)
and [physical pins](../../reports/m4-crt-heap-init-recovery/recovery-r1/pins.json).
Reproduce with a fresh output name:

```powershell
& C:/Python314/python.exe tools/m4-crt-heap-init-recovery/recover.py recovery-r2
```

Selected initializer coverage stays 27 of 144. Source-file zeros establish
neither initialized heap ownership nor a selected heap mode.
