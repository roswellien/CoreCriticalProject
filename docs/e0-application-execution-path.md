# E0: application execution path and first blocker

Recorded 2026-10-11 under the faithful modernization plan (local reference: `docs/faithful-modernization-plan.md`).
Static candidates and executed routes are labelled separately. Accepted M4 stays
**131/144**; nothing here grants accepted-function, startup, menu or Training credit.

Update 2026-10-13: the integrated native host has now executed the live animated
menu, Training 1 rendering through Vulkan with the game HUD, interactive startup
and walking, and normal Quit -> confirm shutdown to exit code 0. The recompiled
Indeo IV50 codec decoded in hidden-window runs. The
[session summary](session-summary-2026-10-13-native-host.md) is the latest scope
record. The dated path table and early blockers below remain historical evidence;
their "not reached" and "static only" statuses do not describe current execution.

## Route decision: retail translated entry

The game's own CRT entry (`0x5AC3A0`, PE entry point) already runs natively through
five accepted service gates and the command-line producer, so the production host
follows that retail route instead of a host bootstrap that would skip it. A host
bootstrap would still have to reproduce every effect listed below; no evidence shows
it would remove a dependency. The remaining structural gap is that every native
chain still starts from **captured original BEFORE state** (provider DLL attach and
process state). Replacing that seed with host-built, contract-equivalent provider
state is the integration work of E1, not a reason to bypass translated entry.

## Path map (Mech3.exe U.S. 1.2, staged MSVCRT/MFC42)

| Stage | Source PCs / calls | Native status (2026-10-11) | Class |
| --- | --- | --- | --- |
| Image admission, guest memory, FS/TEB, SEH chain, dispatch | `tools/m4-startup`, `tools/m4-runtime` | Implemented runtime; `--startup` faults on any unregistered translation | host runtime |
| Provider DLL attach (MSVCRT `_CRTDLL_INIT`: heap, TLS, `_acmdln`, environment, `_mbctype`, stdio; MFC42 module/thread state) | OS loader before entry | **MSVCRT attach: executed natively end to end (2026-10-12, see the next row)**, at the `__getmainargs` service on a declared projection frame. **MFC42 attach: executed natively end to end (2026-10-12, `tools/m4-crt-heap-carry` MFC42 stage)**: `_DllMainCRTStartup` -> RawDllMain, `_CRT_INIT` (63 initializers), DllMain -> RET TRUE, run after MSVCRT attach on the same projection frame; 836 lifted bodies, 289 real host services, loader-model import binding | observable legacy internals (guest-visible globals/objects) |
| CRT entry prefix: SEH frame `5AC586`, `__set_app_type`, `_fmode`/`_commode`, `_adjust_fdiv`, `_controlfp`, `__setusermatherr(51E7B0)`, `_initterm5E0248,5E024C)` | `5AC3A0`-`5AC440` | Executed natively (accepted bounded gates) | translated game + translated provider leaves |
| `__getmainargs` -> ordinary builder `7800BBBC` -> `GetModuleFileNameA` | `5AC468`, `7800BBD0` | Executed natively; real OS filename service | translated provider + host service |
| `_acmdln` load, `_pgmptr`, builder argument setup | `7800BBD6`-`7800BBF7` | Executed natively | translated provider |
| **Parser counting pass** | `7800BC48` | **Executed natively (this change)**; returns to `7800BBFC` | translated provider (lifted) |
| MSVCRT `_CRTDLL_INIT` entry -> RET TRUE (GetVersion, `_heap_init`, version globals, `_mtinit` locks/TLS/per-thread data, `_ioinit` stdio table, environment strings/`_aenvptr`; carry `_acmdln` writer; resume: `_wcmdln`, `__initmbctable`/`_setmbcp` with lazy lock 25 and SBCS tables, `_setenvp` -> native `_environ`, `_cinit`: MSVCRT initializers incl. onexit table, FDIV callback carried from the accepted registry), then `malloc` of the argv/args block | `780017FD`-`78001820`; `7800BC06 -> 780012B3` | **Executed natively (2026-10-12, `tools/m4-crt-heap-carry`)**, scheduled at the `__getmainargs` service on a declared projection frame; 152-185 real attach APIs, with the carry running the `_acmdln` writer in true attach order, then the source malloc closure to real `HeapAlloc`. MSVCRT attach complete; MFC42 attach still absent | translated provider + host services |
| Parser filling pass, `__argc/__argv/_environ` publication, return to `5AC46E` | `7800BC2D`-`7800BC47`, `7800BA9E`- | **Executed natively (2026-10-12)**; argv equals an independent parse; `_environ` native (`_setenvp`) | translated provider |
| Main `_initterm[5E0000,5E0244)` (144 nonzero roots) | `5AC47B` | **Roots 1-15 (`40FFE0`..`410440`) executed natively in the entry host (2026-10-12): container and derived-class ctors, ID-registered objects (IDs 10000/10001 found by walking root 1's native list through a virtual `GetID`), MFC42 `operator new`/`delete` -> real heap, `atexit` into the native onexit table. Since the MFC42 stage (2026-10-12): the whole `_initterm` call runs in the generic native stage after native MSVCRT+MFC42 attach, and roots 1-17 complete, including root 16 (`5AE3E4`, the `CWinApp`-derived application object `7365A4`). Latest (`mfc-run-92`, 2026-10-12): all 144 initializer roots, then the entry continuation, `WinMain` -> `AfxWinMain` -> `InitInstance` run natively: hooks (real thread hooks with guest trampolines), DirectPlay lobby check, window class + main window `Mech3Class`/"Zipper Interactive" created through the window-procedure bridge (MFC CBT subclassing, `AfxWndProc`, marshalled messages), CPUID/RDTSC calibration, QPC timing, DirectSound on the real x64 provider, message tables, registry, data files, CD check (F: video), menus; 38,477 lifted bodies and 8,082 real services. Typed stop: the recovered video contract `SetCooperativeLevel(hwnd, 0x13)` (exclusive full-screen) at the presentation-provider decision. The real x64 system DirectDraw has no Direct3D3 (the game's D3D QI returns E_NOINTERFACE), so the faithful 3D path needs the project's Vulkan provider behind the same guest COM proxy.** 141 roots execute natively in the joint startup141 worker from a captured bootstrap; not yet connected to the entry chain. Not executed natively: application `47F760`, version `4AF240`, HYPOT `4B5910` | translated game |
| Command-line skip, `GetStartupInfoA`, `GetModuleHandleA`, `WinMain 5AE390` | `5AC48E`-`5AC4EA` | Not reached natively; static path in [WinMain/InitInstance analysis (local reference: `docs/winmain-initinstance-analysis.md`) | translated game + host services |
| `AfxWinMain` (MFC42 ordinal 1576 via IAT `5BB438`) -> app vtable `5C3F80` slots `+8C,+58,+5C,+70` | `5AE3F4` | Static only. Receiver model `runtime/mfc/app_receiver_state.*` is a fixture, not live dispatch | observable legacy internals (MFC objects inside game data) |
| InitInstance candidate `480000`: `detail.zrd`/reader fallback, frame `47FF90 -> 482D10`, resource147 menu; services `480570` | static map | Static only | translated game + services |
| Run `58FD70`, startup object `608F58`, MAINMENU `486990 -> 486260` (`dialog.zrd`), render/input `486D40 -> 48ED30` | static map | Static only; host archive/tree parser agrees on MAINMENU tokens | translated game + reader/widget/video contracts |
| DirectDraw/COM creation and presentation -> Vulkan | `runtime/graphics/direct_draw_creation.*`, presenter work | Contracts/prototypes only; graphics lane owned by other writers | replaceable host service via recovered contracts |

Sources: [application workahead](m4-application-workahead.md) and its inventory,
[CRT next plan](m4-crt-next-plan.md), [mainargs](m4-crt-entry-mainargs-review.md),
[filename](m4-crt-filename-review.md) and [command-line carry](m4-crt-commandline-carry-review.md)
reviews, and the current141 receipts in [plan r14](m4-execution-plan-r14.md).

## Execution reached: live menu and Training (2026-10-12/13)

This was all executed natively in the single native host (`tools/m4-crt-heap-carry`, see its README section "To the live menu and into Training"). These are executed runs only; the accepted count stays **131/144**.

| Boundary | Run | Evidence (local, git-ignored) |
| --- | --- | --- |
| `SetCooperativeLevel(0x13)` → virtual display; D3D3 HAL device on the virtual back buffer | `mfc-run-93`.. | service log |
| Intro sequence (AVI audio, Flip), then menu image loading | ..`121` | service log |
| **Live main menu** (animated; Campaign/Training/…/Quit) | `mfc-run-124` | `reports/m4-crt-attach/live-menu-r1` |
| Training pilot screen → Accept → mission loader thread (`490900`, guest thread) → briefing map | `126`..`132` | frames |
| **Live Training 1 3D frame** (Direct3D scenes rendered by Vulkan; game HUD over them) | `mfc-run-137` | `live-training-r1` |
| Training steps by scripted player input: start-up `S`, turn (Right-Arrow), accelerate (Up-Arrow); the 'Mech walks out of the hangar; objective "Move 'Mech next to Instructor" | `159`..`161` | `live-training-r2`, `r3` |

The player input in those runs comes from `MW34_INPUT_SCRIPT`, at the DirectInput data boundary. Without a script, the real keyboard and mouse drive the game (`play.ps1`).

The current blockers are:
- Frame rate in heavy scenes, about 13 fps. The cost is per-access memory-contract work and the lifted code itself.
- Retest camera/leg behavior after the built FPATAN quadrant fix. The user has already confirmed interactive startup and walking. Flip is presented through a Vulkan swapchain (`mfc-run-171`: 1,100 of 1,100 frames on the adapter that drives the display).
- Interactive validation of the remaining Training steps.
- Visible intro playback after hidden-window decode with the recompiled Indeo codec.
- Weapons and controlled original/native physics, AI and timing comparisons.
- The strict acceptance v6 review/criterion decision; no acceptance criteria change here.

## Change implemented: parser connection

`tools/m4-crt-parser-carry/` (see its README) connects the already-lifted parser
object at `0x7800BC48` inside the existing entry chain, under an exact counting-pass
Stage owner, and moves the truthful stop to the `malloc` CALL. Validation:
O0 (24 ordinary scenarios) and O2 builds run; counts `8/425` and, with a quoted
argument ending in `\\"`, `8/548` equal an independent implementation of the VC CRT
counting algorithm on each run's own command-line bytes; the twelve injected-fault
controls still refuse before the parser. Fidelity limits: BEFORE-pack seeding, no
filling pass, heap, environment or return; undefined AF uses a representative that
the body never consumes.

## Historical blocker queue (2026-10-11/12)

1. **CRT heap and `malloc` (`780012B3`).** Connect the translated malloc closure
   with heap state equivalent to MSVCRT DLL attach (`_heap_init`/HeapCreate result,
   small-block state) instead of captured state. Then run the filling pass and
   publish `__argc/__argv/_environ`.
   Integration finding (2026-10-12): the heap and allocator pieces exist in the
   allocation lineage (`reports/m4-crt-allocation/preparation-r7`, executed in
   `m4-crt-allocation-root/execution-r6`). Its composition already contains the
   command-line/mainargs carry plus the heap-version/mode/create/init/return,
   locale and mode-1 malloc/free owners. But every one of those stages is a
   `[[noreturn]] start(mg::Context&)` launched at the `__getmainargs` entry. That
   entry is a separately authored projection of the attach fragment `7800183C`,
   followed by external cdecl research calls of malloc/free at a fixed guest
   address `0x31000000`, so mainargs and the parser never run there. The parser
   carry runs mainargs and the parser but has no heap. The concrete work is:
   (a) turn the heap chain into a returning stage that creates the real heap
   before the entry chain, at attach position, and publishes `_crtheap`;
   (b) let the parser carry's own `CALL 780012B3` enter the translated malloc
   closure under an allocator owner sized from the parser's `numargs/numchars`,
   returning a checked guest pointer at `7800BC0B`;
   (c) admit the second parser pass with write rules for exactly the argv
   block it fills.
   **Done for the entry route (2026-10-12), in `tools/m4-crt-heap-carry/`:**
   real `HeapCreate`/`GetVersionExA` heap init (mode 1), then the builder's own
   source malloc to real `HeapAlloc`, the filling pass, and `__argv`/`__argc`
   published by original code, then the literal `__getmainargs` tail and RET
   back into the compiled game entry (import record completed). The stop is
   now the game's second `_initterm` CALL for the main initializer table
   (`5AC47B -> 5AC598`, `5E0000..5E0244`), which is blocker 3. O0/O2 pass 36/36
   each, and all 48 argv vectors equal an independent parse. Limits are in that
   README: declared heap-init projection frame, BEFORE seeding, file-initial
   `_environ` (NULL envp).
2. **Provider attach equivalence.** Build the MSVCRT/MFC42 attach effects the game
   observes (globals, heap, TLS, module/thread state) in the host, so the chain no
   longer needs the original BEFORE pack.
3. Join the entry chain to the main `_initterm` table using the 141-root worker's
   components, then the three unexecuted roots (`47F760`, `4AF240`, `4B5910`).
   Findings (2026-10-12):
   - The full141 worker (`reports/m4-startup141-runway/preparation-r2`, compiled,
     never launched) calls the roots through its own `invoke_selected_table`, not
     the provider `_initterm` loop.
   - It starts from a captured original prefix. It relocates five MFC42 attach
     objects from the original heap (manager array, thread, thread array,
     thread object, global object; `0x8D4B80…` to `0x33001000…`) and rewrites six
     pointer cells, three MSVCRT attach cells (lock slot `7803708C`,
     `__lc_codepage` `780379C0`=1252, `78037AE8`=1) and seven import cells.
   - So joining the initializers to the entry host depends on provider-attach
     equivalence (item 2) for those effects, not only on routing calls.
   - Root 1 (`40FFE0`):
     1. ECX=`603FD8`, then the STL container ctor `4C7B80`;
     2. `operator new(12)` via the game's `5ABD26`, which reaches MSVCRT malloc;
        that path is now native;
     3. `atexit(410010)` via `5AC140` → `_onexit` `5AC110`, into the MSVCRT
        onexit/`_lock` path. That path needs the lock table and the attach-time
        onexit table.
   - Only `f_40ffe0`/`f_40fff0` are already lifted (`reports/m4-mfc-source/lifts-r1`).
4. `WinMain -> AfxWinMain` and the application vtable callbacks toward MAINMENU.
