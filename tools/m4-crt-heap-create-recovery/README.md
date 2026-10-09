# HeapCreate return and source continuation recovery

This static recovery freshly decodes the exact staged CRT and executes only
the disassembler. It does not execute the game, original provider, native test,
HeapCreate or HeapDestroy. All accepted earlier namespaces remain frozen.

The next bounded success experiment admits the already reached named
HeapCreate call with arguments `[0, 4096, 0]`. A real nonzero host HANDLE remains
full width in a private ownership registry. Only an opaque nonzero guest DWORD
token enters EAX. The reviewed return bridge reads the original `780039D6`
return word at `20001848` and applies the original x86 stdcall cleanup, advancing
ESP by 16 to `20001858`. This is an explicit finite bridge contract; it does not
prove every possible original Win32 volatile-register or flag outcome.

The genuine source continuation is TEST at `780039D6`, token store to
`78035000` at `780039D8`, untaken JE at `780039DD`, and CALL at `780039E3`.
The CALL pushes `780039E8` at `20001854` and reaches `78003A0C`, before any mode
selector instruction executes. These add four source PCs and two source
memory accesses: thirteen PCs and ten accesses including the earlier prefix.
The bridge's checked return-word read is separate from these original-source
counts. Mode `78035004` remains unproduced. The raw RW page at `78035000` becomes
the eighteenth mapping; file zeros establish initial source identity only.

TEST defines CF/OF zero, ZF from token equality to zero, SF from token bit 31,
and PF from even parity of its low byte. AF is undefined at this new exact
source PC, requiring a separate qualified compiled representative. The MOV,
branch and CALL preserve those flags. No fixed token value or mode is assumed.

A zero HeapCreate outcome stores zero and branches to `7800CDDC`. The minimum
bounded zero experiment stops there before the unadmitted cold body: twelve
source PCs and nine source accesses, with ESP `20001858` and no source RET.
Static decoding also recovers the later `XOR EAX,EAX; RET`. If separately
admitted, this returns to `78001843` with ESP `2000185C`,
leaving the cdecl argument for its caller. That path has fourteen source PCs
and ten source accesses, including the earlier prefix, and requires a further
undefined-AF qualification at `7800CDDC`. It invokes no HeapDestroy. A synthetic
zero fixture can test that branch but cannot establish an actual API failure.

The report separates actual success, real NULL, forced API refusal, failed
registration rollback, later host resource cleanup, and the original unrun
HeapDestroy branch. Destroying an experiment-owned host resource does not
execute original cleanup instructions or clear guest globals. Actual results,
full handle identity, registry lifecycle and cleanup failures must remain
observable. The unfinished mode selector and mode-specific allocators remain
future dependencies.

Primary API references: [HeapCreate](https://learn.microsoft.com/en-us/windows/win32/api/heapapi/nf-heapapi-heapcreate),
[HeapDestroy](https://learn.microsoft.com/en-us/windows/win32/api/heapapi/nf-heapapi-heapdestroy),
and [x86 stdcall](https://learn.microsoft.com/en-us/cpp/cpp/stdcall?view=msvc-170).

Run with a fresh receipt name:

```powershell
& C:/Python314/python.exe tools/m4-crt-heap-create-recovery/recover.py recovery-r1
```

The JSON receipt schema is `mw34-m4-heap-create-static-recovery-v1`. Source
spans, import descriptors, lookup/name bytes, raw IATs, source page, commands
and all physical dependencies are pinned. Documentation references describe
ABI/API contracts; they are not evidence that an API or original body ran.
