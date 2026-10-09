# MW3 1.2 API inventory and research backlog

Reviewed 2026-10-06 against the exact image in the [memory map](memory-map.md).
All **18 ordinary imported libraries and 474 entries** are accounted for in the
[metadata-only CSV](imports-mw3-us-1-2-retail.csv): 253 named imports and
221 ordinal imports, each with its IAT RVA. Python and LLVM 21.1.8 outputs agree
entry for entry, including name hints and ordinal numbers. Import presence is
observed; subsystem labels are inferences and do not establish call reachability.

| Library | Entries | Evidence / interpretation |
| --- | ---: | --- |
| VERSION.dll | 3 | File-version resource APIs |
| IFORCE2.dll | 4 | Decorated project/effect load/create/release names; force-feedback role inferred |
| MFC42.DLL | 219 | Ordinals only; names/version-specific ABI unresolved |
| MSVCRT.dll | 93 | Heap, stdio, strings, math, floating-point control and exception handlers |
| KERNEL32.dll | 47 | File/process, timing, dynamic loading, threads and synchronization |
| USER32.dll | 45 | Messages/windows, focus, cursor and keyboard APIs |
| GDI32.dll | 18 | Fonts, drawing, bitmaps and device capabilities |
| comdlg32.dll | 2 | Open/save file dialogs |
| ADVAPI32.dll | 5 | Registry open/create/query/set/close |
| MSVCP50.dll | 3 | Decorated C++ lock/numeric-limits imports |
| ole32.dll | 3 | COM initialization, creation and uninitialization |
| AVIFIL32.dll | 9 | AVI file/stream read and metadata |
| MSVFW32.dll | 4 | Codec location, decompression, messages and close |
| WINMM.dll | 14 | Multimedia time, mixer, auxiliary volume and MCI commands |
| DSOUND.dll | 1 | Ordinal 1, unresolved against a pinned provider |
| DDRAW.dll | 2 | `DirectDrawCreate` and `DirectDrawEnumerateA` |
| DPLAYX.dll | 1 | Ordinal 4, unresolved against a pinned provider |
| DINPUT.dll | 1 | `DirectInputCreateA` |

## Evidence status and next experiments

| Research area | Current evidence and limit | Next experiment |
| --- | --- | --- |
| Graphics / COM | DirectDraw creation imported; indirect calls observed in callers. No named D3D DLL import in this ordinary table. Exact graphics COM interfaces/GUIDs and dynamically acquired D3D behavior unknown. | Follow DirectDraw IAT uses and QueryInterface/GUID/vtable paths; recover interface versions before a bridge. |
| Input / force feedback | DirectInput entry plus keyboard/cursor APIs and IFORCE2 effect names imported. | Follow acquisition/device creation calls and pin requested interfaces/structure sizes. |
| Audio / video | DSOUND ordinal, WINMM mixer/MCI and AVI/codec imports. Provider export identity unresolved. | Hash the actual app-local/system providers, resolve ordinals, then inspect initialization/callbacks. |
| Win32 / CRT | Named allocator, stdio/string/math/error imports; large ordinal MFC surface. Static helper extent unknown. | Resolve ordinals against exact DLL files; distinguish runtime thunks from game routines with caller/CFG evidence. |
| Timing | `GetTickCount`, `QueryPerformanceCounter`, `QueryPerformanceFrequency`, `timeGetTime`, `Sleep` imported. Units, update paths, clock mixing and simulation/render coupling unknown. | Follow timer IAT uses, then measure a repeatable mission at controlled presentation rates. |
| Threads / synchronization | `CreateThread`, priorities, events, mutex, wait and critical-section APIs imported. | Recover thread entry callbacks and shared state before multithreaded translation. |
| Files / registry / dialogs | Kernel and CRT file I/O, five registry APIs, two file dialogs. | Trace asset-open sites and paths; identify formats from bounded reads, not filenames alone. |
| Dynamic resolution | `LoadLibraryA`, `GetProcAddress`, `FreeLibrary`, `CoCreateInstance` imported. | Recover names/GUIDs and call sites; ordinary imports are not a complete dependency list. |
| Networking | DPLAYX ordinal is a networking-family lead; no ordinary Winsock DLL import. Reachability and actual transport unknown. | Resolve provider ordinal, follow session/COM creation, inspect callbacks and any dynamic networking load. |
| CPU / floating point | LLVM view at VA `[0x004011BE, 0x004011D8)` decodes x87 loads, subtraction, exchange and stores in coherent surrounding code. Selected integer leaf has none. MMX/SSE use elsewhere not reviewed. | Cross-decode and bound floating-point routines; run authored x87 fidelity tests after G2. No raw-byte instruction-family claims. |
| Exceptions / TLS | Entry `[0x005AC3A0, 0x005AC3BD)` installs an FS-relative frame; CRT handler imports. PE TLS directory absent. DLL TLS, callbacks and thread-state details unknown. | Recover startup/SEH registration and exception paths; inspect actual provider TLS separately. |
| C++ / control flow | Caller near VA `0x004051C2` dereferences an object table and calls an indirect slot; vtable interpretation inferred. Full RTTI, tables, shared tails and indirect target sets unresolved. | Analyze a SHA-keyed Ghidra project for cross-references and types when expanding beyond this bounded leaf. |
| Globals / structures / formats | Caller uses absolute addresses; selected leaf computes a base + fixed offset + stride. Object identity and file/asset formats unknown. | Track accesses and construction, then write bounded structure/format contracts for the next slice. |
| Reference compatibility | User reported training playable with dgVoodoo2 and a geometry issue apparently resolved at 30 FPS. Cause and broad stability unmeasured. | Preserve config and perform frame/time measurements; do not infer a game timing fix from the report. |

This inventory satisfies a bounded reconnaissance review: each requested category
has evidence or an explicit unresolved experiment. It is not complete program
recovery. Ghidra has not been run for whole-image analysis; detailed instruction,
cross-reference and type recovery outside the reviewed slice remains queued.
The immediate execution work is the [first-function comparison](first-function.md),
before timing changes, renderer work or higher-resolution texture integration.
