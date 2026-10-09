# Complete mode-1 allocation and free source recovery

This static gate freshly decodes the exact staged MSVCRT (SHA `2d5670881a6d13a100e37da297f6eeb876f68b63073a28eb5d650625c60f9bf7`). It preserves the accepted heap-return gate and every older namespace. It runs no original code, game, native candidate, or Windows API.

The original caller at `78001843` tests the real initializer result, removes its cdecl argument, and proceeds to `7800184C`. Later original attach instructions reach unrelated version/global services; this recovery does not claim that attach scheduled malloc. The proposed allocation experiment declares two external research cdecl frames at `20001858`: malloc uses return `FFFFFFE0` and size24; free uses distinct return `FFFFFFD0` and the admitted guest allocation pointer `30000000`. These frame stores and scheduling effects are recorded separately from original source instructions. The same actual private heap remains owned across initializer return, malloc, usable memory, free, and final cleanup.

Eight complete source spans total **469 bytes**. The ordinary malloc path executes **49 source PCs/39 DWORD accesses**, rounds24 to32, registers its real previous FS:[0] chain, calls HeapAlloc, restores that chain, and returns through all three source RETs. Free executes **33 PCs/25 accesses**, calls HeapFree with the same owned heap and allocation, restores its own FS chain, and genuinely returns. Caller cleanup adds three PCs/one access. Two stdcall return reads remain separate API-effect evidence. Source exception-frame installation/removal establishes normal lifecycle only; dispatch, handler execution, and exceptional unwind remain open.

The source HeapAlloc import is uniquely KERNEL32.dll, IAT `7802E094`, raw slot `345C6`, hint409. HeapFree is uniquely KERNEL32.dll, IAT `7802E090`, raw slot `345BA`, hint415. Source requests flags0. The usable extent must use the actual full-width allocation with a checked guest address; neither host pointers nor heap handles may be truncated. Allocation bytes start with the complete measured native allocation contents, not assumed zeros. A real write/read comparison before release establishes usability. Pointer ownership is revoked only after actual successful release; duplicate, foreign, interior, expired, or wrong-owner requests reject before an unsafe host free.

[HeapAlloc](https://learn.microsoft.com/en-us/windows/win32/api/heapapi/nf-heapapi-heapalloc) returns an allocation pointer or NULL with flags0 and does not supply extended LastError on failure. [HeapFree](https://learn.microsoft.com/en-us/windows/win32/api/heapapi/nf-heapapi-heapfree) succeeds with nonzero BOOL and requires the corresponding heap/allocation. Source free's public return type is void; its genuine RET alone cannot turn BOOL0 into successful release. These finite API witnesses do not prove universal original API internals, volatile registers, or flags.

`model.py` is an independent affine predictor. It takes complete independently derived BEFORE State/FX/CPU/owned memory and finite validated API outcomes. It derives every source access, flag, frame, and normal return; it never imports a candidate expected model or seeds from native AFTER State. `recover.py` uses clearly authored static arithmetic inputs to check size0/1/24/31/32/4096 and NULL/nonzero result formulas. These formula controls are not native evidence. Captured memory aliases must be derived from owned address storage rather than treated as extra mappings.

Run from the project root with a fresh output name:

```powershell
& C:/Python314/python.exe tools/m4-crt-allocation-recovery/recover.py recovery-r1
```

The receipt binds exact instructions, source span binaries, imports, scope metadata, reusable model, source ledgers, and prior accepted identities. Other allocator modes, new-handler retry, source SEH dispatch, persistent application ownership, locale integration, argument parsing, full CRT startup, menus, and whole M4 remain open.
