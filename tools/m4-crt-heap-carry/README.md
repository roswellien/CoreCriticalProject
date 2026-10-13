# Integrated native MW3 host (retail entry route)

Current status, 2026-10-13: this experimental x64 host has executed the live
animated main menu, Vulkan-rendered Training 1 with the game HUD, startup and
walking, and normal Quit -> confirm shutdown with exit code 0. The intro's
recompiled Indeo IV50 codec decoded in hidden-window runs. Heavy Training scenes
reached about 13 fps on the development system. These are executed runs, not
formal acceptance; the accepted count stays **131/144**.

See the [session summary](../../docs/session-summary-2026-10-13-native-host.md)
for the full source/evidence record and limitations. Camera flip and leg animation
were observed in interactive play; the built FPATAN quadrant correction in 57
re-lifted functions awaits a play retest. Visible intro playback, remaining
Training, weapons and original/native physics, AI and timing comparisons are
still open. Strict acceptance v6 remains a separate review/criterion decision.

## Local build and launch

```powershell
powershell -File tools/m4-crt-heap-carry/build.ps1 -Levels O2
Play-MW3.cmd
```

These commands require the prepared development environment. `build.ps1` uses
the parser-carry CMake cache, pinned local toolchains/headers, prior reviewed
objects and the generated MFC object list. `play.ps1` requires the user's game
installation, staged provider images and local input packs. Codec support also
depends on the locally repaired/pinned MMX semantics and generated codec lifts.
There is no self-contained clean-checkout build or downloadable native binary.

The authored host sources, shaders and tooling are public. Generated game and
codec translations, `mfc_entries.inc`, `mfc_routers.inc`, `mfc_objects.txt`,
staged DLLs, captures and builds remain local. Regenerate dispatch metadata with
`gen_mfc_dispatch.py` from admitted local lift report directory/hash pairs before
building; the generator's usage is documented in its header. No game files go
into CI. The earlier development stages below retain their dated scopes; their
old stop points are superseded by the live execution section near the end.

## Historical heap/parser connection

Execution boundary advanced: the parser carry stopped at the builder's `malloc` CALL
(`0x7800BC06 -> 0x780012B3`). This host now runs, natively and in source order:

- MSVCRT `_CRTDLL_INIT(78000000, DLL_PROCESS_ATTACH, reserved)` from its real entry
  `0x780017FD` up to the `_acmdln` writer (`0x7800188C`), which the command-line carry then
  executes in its true attach position. It makes 25 real API calls:
  - `GetVersion`, which feeds the `_osver/_winver/_winmajor/_winminor` stores;
  - `_heap_init(1)` with `HeapCreate` and `GetVersionExA`. The source `__heap_select`
    picks mode 1 (platform 2, version 6.2);
  - `_mtinit`: `_mtinitlocks`' four `InitializeCriticalSection` calls on the static lock
    objects, `TlsAlloc`, a zeroed `HeapAlloc` for the per-thread data, `TlsSetValue`,
    `_initptd` and `GetCurrentThreadId`;
  - `_ioinit`: a source-malloc'd 32-entry ioinfo table, `GetStartupInfoA` converted to the
    x86 layout (strings copied into a provider-owned guest page; handles must fit in 32
    bits), `GetStdHandle`/`GetFileType` for the three standard handles (the source sets
    FDEV/FPIPE from the real types), and `SetHandleCount(32)`. The cold `GetFileType` path
    re-enters the loop through lifted tail objects (entries `78003CAC`/`78003CB0`).
  - `__crtGetEnvironmentStringsA`: a guest copy of the real `GetEnvironmentStringsW` block,
    two `WideCharToMultiByte(CP_ACP)` calls (size, then fill) into a source-malloc'd block,
    `FreeEnvironmentStringsW` (which also releases the guest copy), and the `_aenvptr` store.
- After the carry's `_acmdln` writer, `_CRTDLL_INIT` resumes at `0x78001897`. The saved
  end-of-attach registers and live frame are restored, with EAX holding the writer's result.
  It runs up to the `_setenvp` CALL (`0x780018A6`), using 26 more real APIs (51 attach APIs
  in total):
  - the wide command line (two `GetCommandLineW` calls returning one guest copy), then the
    `_wcmdln` store;
  - `__initmbctable` → `_setmbcp(-3)`:
    - lazy `_lock(25)`: a source malloc, `Enter`/`LeaveCriticalSection` on the static
      lock-table lock, and `InitializeCriticalSection`;
    - `GetACP` through the source's tail `JMP`, then `GetCPInfo`;
    - `setSBUpLow`, with `__crtGetStringTypeA` and `__crtLCMapStringA` (`MultiByteToWideChar`,
      `GetStringTypeW`, `LCMapStringW`, `WideCharToMultiByte`, `_chkstk` buffers, `memset`);
    - `_unlock(25)`.

  Each guest `CRITICAL_SECTION`'s x86-visible LockCount/RecursionCount/OwningThread fields
  mirror its real host section. `_lock` is lifted as head, tail and enter objects, because
  the full span's recursive self-call stalls the lifter.
- Then `_setenvp`: `_environ` is built with one source malloc per variable (`strlen`,
  `strcpy`), and `free(_aenvptr)` goes through the reviewed mode-1 free objects to real
  `HeapFree`, which also unmaps the guest block.
- Then `_cinit`:
  - Its FDIV callback CALL (`[78037C28]` = `78004254`) is the call the accepted FDIV registry
    already executed natively at the BEFORE point. It is not run twice; its result (EAX = the
    flag it stored) is carried.
  - `_initterm` runs over MSVCRT's own tables (lifted locally; the existing provider object's
    symbol is redirected with `llvm-objcopy --redefine-sym`) and their four initializers:
    - `__initstdio`: a source `calloc` of 512 stream pointers, then the standard streams
      classified from the native ioinfo handles;
    - `__onexitinit`: a source malloc of the onexit table, which root 1's `atexit` needs;
    - the clock base, from real `GetSystemTimeAsFileTime` and `_allmul`;
    - `SetUnhandledExceptionFilter(7800B322)`, registered in the host-owned guest runtime
      model. The host process filter is untouched, and the previous guest filter of a fresh
      process is none.
  - Finally the `proc_attached` increment and the attach epilogue `RET 0Ch` with TRUE.

  **MSVCRT DLL attach now runs natively from entry to return.**

  Lifted with `lift_attach.py` into `reports/m4-crt-attach/lifts-r1` (generated code
  stays local). Guest `CRITICAL_SECTION`s are their 24-byte guest objects, each backed
  by a real host critical section. The TLS slot and sections are owned and released
  per run.
- the builder's own `malloc(numchars + 4*numargs)` through the source malloc, size check,
  worker, mode-1 rounding and `HeapAlloc(_crtheap, 0, rounded)` closure on that heap,
  including the worker's FS exception-record install/restore.
- the builder's TEST/branch, the second (filling) parser pass into the returned block,
  and its stores of `__argv` and `__argc`.
- the builder RET, then the literal `__getmainargs` tail: it stores `__argc`, `__argv` and
  `_environ` into the game's `&argc/&argv/&envp` locals and RETs to the game CRT entry
  (`0x5AC46E`). The runtime accepts the import's return contract (PC, ESP and
  nonvolatiles).

The compiled game entry then runs `ADD ESP,14` and pushes the table bounds. It stops at
its second `_initterm` CALL, for the main C++ initializer table (`0x5AC47B -> 0x5AC598`,
table `0x5E0000..0x5E0244`), with a typed `unresolved_translation` fault.

This is a versioned copy of `tools/m4-crt-parser-carry`. No new lift: it links the already
lifted, independently reviewed objects `reports/m4-crt-heap-{init,mode,version}/preparation-r2`
and `reports/m4-crt-allocation/lifts-r1` (fragment, provider, selector, probe, branch, mode1,
epilogue, caller, malloc, size, worker, round, alloc_tail, worker_epilogue).

Changes:

- `heap_stage.hpp` (new): `HostHeap` owns the real heap and its blocks. `Stage` (attach or
  call) admits only the source DWORD accesses (its stack window, IAT words, heap globals,
  `_newmode`, FS:0), source helper CALL/RET pairs, source continuations and the three
  imports with their exact source arguments. Everything else is refused, including the
  environment-variable, SBH/V5, NULL/new-handler and lock paths.
- `parser_stage.hpp`: a filling-pass constructor. It stores only into `argv[0..numargs)`,
  `args[0..numchars)` and the argv slot, plus the read-modify-write reads of those exact
  stores. It must return to `0x7800BC32` and reproduce the counting-pass counts.
- `carry_binding.inc`/`carry.hpp`:
  - `malloc_call` replaces `malloc_stop` (same preconditions);
  - exact table-driven builder load/store sequences through `__argc`;
  - the post-malloc `TEST ESI,ESI` AF representative (`JNE` reads ZF only; `DEC` redefines AF);
  - a typed `builder_return` frontier.
- `mainargs_context.hpp`/`mainargs_binding.inc`: stage 3 adds the exact tail load/store
  table and `finish` (RET to `0x5AC46E` with frame+4 and restored nonvolatiles). The
  adapter then hands the source CPU back to the runtime.
- `composition.cpp`: the entry Context turns the second `_initterm` CALL into the typed
  frontier. It also routes intrinsics to the active heap Stage and defines
  `__remill_missing_block`, the helper `sub_*` routes, AF representatives and `heap_attach`.
- `main_v2.inc`:
  - maps the literal `.data` pages `0x78035000` and `0x78038000` (around the Session's
    12-byte `_app_type` block);
  - runs the attach heap projection for every scenario;
  - ordinary scenarios require the new frontier, the real heap/allocation counts, and a
    NULL-terminated contiguous argv covering exactly numchars bytes, written to
    `row-*/argv.txt`.
- `build.ps1` (new): builds `build/m4-crt-heap-carry-<level>` with the parser carry's cached
  objects/flags plus the heap objects.

Observed 2026-10-12, before the attach entry change (heap init only):
- **O0:** 36/36 scenarios pass. All 24 ordinary scenarios give `numargs=8,numchars=422`
  (path length differs from earlier runs), a request rounded to 464 and `argc=7`. Every
  ordinary scenario ends at `0x5AC47B -> 0x5AC598`, with the `__getmainargs` import
  record completed. The 12 injected-fault controls still refuse earlier.
- **O2:** 36/36 pass. The output path contains spaces and ends in `\`, so the command line
  ends with `\\"`: `numchars=544`, request 576.
- **Independent check:** for all 48 ordinary rows, every guest argv equals an independent
  Python rendering of the documented VC CRT `parse_cmdline` rules applied to that row's
  own command-line bytes.

Fidelity limits:
- The run is still seeded from the frozen BEFORE pack. That pack has no attach frame,
  and the accepted FDIV registry needs the MSVCRT data page to be literal until the
  entry's data read (`5AC408`). So attach runs at the `__getmainargs` service, on a
  declared projection frame (ESP `0x20001810` plus the page below), as the reviewed
  allocation lineage did. The captured State, CPU and stack page are restored
  afterwards.
- The attach effects (heap, version globals, locks, TLS) commute with the entry prefix,
  which uses none of them, but true attach order is not reproduced.
- MFC42 attach (module/thread state) is still absent, and so is everything else the BEFORE
  pack supplies.
- The FDIV callback ran in the accepted registry job before attach (BEFORE point); its
  effect commutes with the earlier attach steps.
- The guest unhandled-exception filter is registered but not dispatched (SEH dispatch is
  unimplemented). An inherited CRT
  handle table (`cbReserved2`) is refused.
- Guest heap bytes live in mapped guest pages at `0x31000000+`, initialized from the real
  block's initial bytes. The real block is the allocation identity.
- `_environ`/`envp` now come from native `_setenvp` (see below).
- No accepted-function, startup or menu credit.

Observed 2026-10-12 with `_CRTDLL_INIT` from its entry: O0 and O2 (quoted path) each pass
36/36 scenarios. Every ordinary scenario reports `GetVersion=0x23F00206`, TLS index 1, four
initialized static locks and 11 attach API calls. The per-thread block is at `0x31000000`
and the argv block at `0x31001000`. All 48 argv vectors still equal the independent
parse, and the stop is still `0x5AC47B -> 0x5AC598`.

With `_ioinit` (attach lifts-r3): O0 and O2 each pass 36/36 with 20 attach APIs, the ioinfo
table at `0x31001000` and the argv block at `0x31002000`. The stdio entries match the real
handle types: O0 under PowerShell gives stdin char device `0xC1` and stdout/stderr pipes
`0x89`; O2 with NUL stdin gives `0xC1` too. All 48 argv vectors still equal the
independent parse.

With environment strings (attach lifts-r4): O0 and O2 each pass 36/36 with 25 attach APIs.
In every ordinary scenario the source-converted `_aenvptr` block equals the host's
`GetEnvironmentStringsA` block, an independent API path. All 48 argv vectors still equal
the independent parse.

With the attach resume and `__initmbctable` (attach lifts-r8): O0 and O2 each pass 36/36
with 51 attach APIs. In every ordinary scenario:
- `__mbcodepage` equals the host `GetACP` and `78037AE8`=1;
- lock 25 is a real heap block backed by a real host section, released after use;
- the source-built `_mbctype` and `_mbcasemap` equal a host computation with the
  independent ANSI APIs (`GetStringTypeA`/`LCMapStringA`).

These are the three MSVCRT cells the full141 worker previously projected from the
original. All 48 argv vectors still equal the independent parse.

With `_setenvp` (attach lifts-r9): O0 and O2 each pass 36/36. Depending on the
environment, attach makes 152–185 real API calls, most of them per-variable `HeapAlloc`.
In every ordinary scenario, `_environ` equals the host ANSI environment without
`=`-prefixed entries, `_aenvptr` is freed and zeroed, and the game's `envp` local equals
the native `_environ`. All 48 argv vectors still equal the independent parse.

With `_cinit` (attach lifts-r11): O0 and O2 each pass 36/36. Depending on the environment,
attach makes 157–190 real API calls. In every ordinary scenario:
- `_CRTDLL_INIT` returns TRUE to its declared token with `proc_attached`=1;
- the onexit table and the 512-entry `__piob` exist on the real heap (`__piob` points at
  the 20 static `_iob` entries);
- the clock base is at or before the host time;
- the FDIV result equals the registry's stored flag.

All 48 argv vectors still equal the independent parse.

## Main initializer table: root 1 (2026-10-12)

The game's second `_initterm` CALL (`0x5AC47B -> 0x5AC598`, table `5E0000..5E0244`) now runs
under the heap Stage instead of stopping:
- The game thunk's `JMP [5BB510]` resolves the game's `_initterm` import to the MSVCRT body.
- Root 1 (`40FFE0`) runs natively:
  - the STL container constructor `4C7B80` on `603FD8`;
  - MFC42 `operator new` (ordinal 823, through the thunk `5ABD26`), which reaches MSVCRT
    `malloc` via MFC42's IAT cell `5F49814C` and then real `HeapAlloc`. That cell is mapped
    with its loader binding (`MSVCRT!malloc` -> `780012B3`; MFC42 has no bound-import
    directory, and the file holds a stale binding);
  - `atexit(410010)` → game `_onexit` → MSVCRT `_onexit`: `_lockexit` (`EnterCriticalSection`
    on static lock 13), `_msize` (real `HeapSize`), a store into the native onexit table, and
    `_unlockexit`.
- The next table root, `410030`, is the typed frontier (`7800150E -> 410030`).

Lifted with `lift_attach.py`, which now also takes SHA-pinned spans from `Mech3.exe` and
MFC42 (`lifts-r12`).

Observed: O0 and O2 each pass 36/36. Every ordinary scenario checks:
- the head node on the real heap with `next == prev == node`, and size 0;
- the onexit table's first entry `410010`, with end = begin+4.

All 48 argv vectors still equal the independent parse.

Limits:
- The main-table CALL bypasses the runtime's call-record ledger (it runs inside the entry
  Context).
- MFC42 attach is still not native. Root 1's fast path reads only MFC42's `malloc` IAT cell
  and one literal `.rdata` word.
- Roots 2..144 are unconnected; the 141-root worker's components are not yet joined.

### Roots 2..7

Roots 2–7 (`410030`, `410080`, `4100D0`, `410120`, `410170`, `4101C0`) share root 1's shape.
Each is a CALL to a ctor thunk (`MOV ECX,object; JMP ctor`), then a JMP to an atexit thunk
(`PUSH A+30; CALL 5AC140`). They build containers at `603FE8`, `603FF8`, `604048`, `604078`,
`603F90` and `604038` with ctor `4D8540` (vtable `5CD0D4`, flag byte, a 12-byte head node from
MFC42 `operator new`).

The heap Stage now uses a table of these shape roots (`lifts-r13`): roots must run in table
order, and each ctor, allocation and exit registration is bound to the active root. The
typed frontier is root 8 (`410210`, ctor `4105D0`).

Observed: O0 and O2 each pass 36/36. Every ordinary scenario checks:
- six containers with vtable `5CD0D4` and an empty head node on the real heap;
- seven onexit entries, `A+30` for each root in table order.

### Roots 8..13

Roots 8–13 (`410210`..`4103A0`) are derived constructors (`4105D0`, `410610`, `410630`,
`4C8750`, `410650`, `410680`). Each calls the base ctor `4C8600` (vtable `5CB180`, field `+8`
cleared, flag bit 0 cleared) and then stores its own vtable. None of them allocates. They
are in the shape table with "no node" (`lifts-r14`). The typed frontier is root 14
(`4103F0`, ctor `4C0310`).

Observed: O0 and O2 each pass 36/36. Every ordinary scenario checks each derived vtable,
the cleared field, the cleared flag bit, no allocation, and 13 onexit entries in table order.

### Roots 14..15

Roots 14 (`4103F0`, ctor `4C0310`, object `604008`) and 15 (`410440`, ctor `4C0570`, object
`603FB8`) are ID-registered objects:
- The base ctor `4BF910` takes an ID chosen by `58B1C0` from `[10000, 10100)`, starting at the
  game global `5F2A48`=10000. The search walks root 1's list through each object's virtual
  `GetID` (vtable slot `+18` = `40A850`).
- `58AEC0` inserts the object into root 1's list (head `603FDC`, size `603FE0`).
- Each ctor pushes a pointer to another root's object (root 11's `604068` and root 9's
  `604058`) into its own vector. The vector growth uses MFC42 `operator new` and
  `operator delete` (ordinal 825 → MSVCRT `free` through MFC42's IAT cell `5F498148`,
  mapped with its loader binding `78001390` → real `HeapFree`, which also unmaps the guest
  block).

Lifted in `lifts-r16`; the static closure (18 functions) came from a recursive-descent
research walk. The typed frontier is root 16 (`5AE3E4`).

Observed: O0 and O2 each pass 36/36. Every ordinary scenario checks:
- both vtables (`5BCC68`, `5CAB60`);
- root 1's list with two heap nodes, linked back to its head, whose payloads are `604008`
  then `603FB8`;
- source-allocated IDs 10000 and 10001;
- 15 onexit entries in table order.

So root 14 reads root 1's native list, and root 15 reads root 14's registration through the
virtual call.

### MFC42 DLL attach (in progress)

Root 16 (`5AE3E4`) calls `AfxGetModuleState` (MFC42 ordinal 1168), so it needs MFC42's own
`DLL_PROCESS_ATTACH`. The real loader runs that after MSVCRT's attach and before the game entry.
`run_resume` runs it right after the native MSVCRT attach completes, on the same declared
projection frame: `_DllMainCRTStartup(5F400000, DLL_PROCESS_ATTACH, reserved != 0)` from
`5F4052A2`.

Pipeline (all source-only except the run):
- `mfc_closure.py` builds a static recursive-descent closure. Roots are:
  - the entry, RawDllMain `[5F4CD0A4]`, `_CRT_INIT` and DllMain;
  - the 63 static initializers in `[5F4CD1E8, 5F4CD2E8)`;
  - extra roots for targets reached only dynamically (`5F4053FE`).

  The closure follows direct calls and jumps, immediates that address the image's code
  (callbacks), and any operand naming an MSVCRT-bound IAT cell into the staged MSVCRT export
  body. The current closure (`mfc-closure-r4`) has 721 functions: 483 MFC42 and 238 MSVCRT.
- `lift_closure.py` lifts every function with `lift_attach.py`'s exact lifter, semantics and
  lowering:
  - Self-recursive functions are cut before their first self-call, with continuation objects.
    The lifter does not terminate when a call target equals the entry inside the lifted bytes.
  - Every direct call is renamed into the private `mw34_mfc_sub_<addr>` namespace.
  - `__remill_error` (DIV #DE) and `__remill_atomic_begin/end` (LOCK) are admitted bridges.
- `gen_mfc_dispatch.py` writes `mfc_entries.inc` (an address-sorted body table) and
  `mfc_routers.inc` (direct-call routers and undefined-flag representatives). No closure
  instruction consumes AF (no LAHF/SAHF/PUSHF/POPF/DAA/DAS/AAA/AAS/AAM/AAD), so the
  representatives return 0.
- `mfc_stage.hpp`, `map_image()`: the loader model. MFC42 is placed at its preferred base
  with literal headers and sections, then its imports are bound:
  - MSVCRT imports go to the staged MSVCRT export addresses. The binding reproduces the earlier
    free/malloc cells and the literal `5F498970`.
  - Every other import gets a per-import service token.
  - MSVCRT's own IAT stays literal (raw hint/name words), and the stage resolves those words by
    name.
- `mf::Stage` uses the heap stage's discipline:
  - Every CALL pushes its return word, and every RET must return to it.
  - Indirect calls, JMPs and continuations resolve only to lifted entries or service tokens.
  - Memory contract: the stage's own frame, the image (writes to `.data` only), MSVCRT
    `.rdata`/`.data` reads, real heap/local/global blocks, and the TEB exception-list word.
  - Unknown targets stop with `unresolved_translation` and unimplemented services with
    `unresolved_import`. A #DE stops with `unimplemented_seh_dispatch`.
- Host services are real Win32 calls with guest projection:
  - CRT heap on the real CRT heap (`HeapAlloc/Free/Size/ReAlloc`).
  - `LocalAlloc/ReAlloc/Free` and `GlobalAlloc/Lock/Unlock/Handle/ReAlloc/Size/Free`: a real
    block per guest block, guest handle tokens for moveable memory, contents in guest pages.
  - TLS, critical sections, code pages, system metrics/colors, DC caps, stock objects, system
    cursors, `Register*` names, `GetCursorPos` and pseudo-handles.
  - `GetProcessVersion` is answered from Mech3.exe's header (4.0), not the host worker.
  - `GetModuleFileNameA` reports the real host paths of the images actually loaded.
    `LoadLibraryA` of a module absent from the loader search path returns NULL with
    `ERROR_MOD_NOT_FOUND`, as the real loader does. An existing unmodelled module stops typed.

Over-approximated closures, lifted once and merged:
- MFC42: `mfc-closure-r5`, made with `all` plus two dynamic roots: 13,418 functions (12,846 MFC42
  and 572 MSVCRT). Lifted in 8 partitions (`lifts-r26-p0..7`; the single-process `lifts-r25` was
  stopped early and abandoned).
- Game: `game-closure-r2` holds every main initializer root: 829 functions (`lifts-r27-p0..3`).
  `game-closure-r3` (`game all`) adds every game `.rdata`/`.data` word addressing game `.text`:
  12,010 more functions (`lifts-r28-p0..9`).
- Lifting is tolerant: failures are recorded in each report and stop typed if reached.
  `fp_lowering.py` adds the x87/FP lowering contract of `tools/m4-mfc-source/lift.py`
  (f32/f64/64-bit bridges, host x87 exception clear/test, the exact empty FP ordering barrier).
  Its `retry=` re-lifts recovered 15 of 31 game failures (`lifts-r29`) and 91 of 96 MFC42/MSVCRT
  failures (`lifts-r30`). The remaining failures need a reviewed contract for x87
  transcendental, 80-bit memory, rounding or `fpclass` operations.

The stage is generalized to two kinds:
- `attach`: MFC42's DllMain.
- `initterm`: the game's main `_initterm` CALL through its import thunk `5AC598`, after native
  MSVCRT and MFC42 attach.
  - Game IAT words stay raw, as the runtime models them. Each raw word is unique across the
    game's 474 imports and resolves by name (`bind_game`): MFC42 ordinals and MSVCRT names go to
    lifted export bodies, everything else to host services.
  - The memory contract is process-wide: every mapped image readable, writable sections of
    game, MSVCRT and MFC42 writable, real blocks, TEB words.
  - The original process has a 1 MB stack while the runtime keeps one page, so the stage maps a
    stack extension `[1FF01000, 20001000)` for its duration.

Observed (O2, scenario 0, `mfc-run-23`):
- **MFC42 `DLL_PROCESS_ATTACH` completes natively**: RawDllMain, `_CRT_INIT` with its 63
  initializers, and DllMain return TRUE through RET 0Ch with callee-saved registers restored.
  836 lifted bodies, max depth 9, 289 real host services.
- **The main initializer table then runs natively through roots 1..17**, including root 16
  (`5AE3E4`, the game's `CWinApp`-derived application object at `7365A4`).
- Typed stop: root 18 (`40E250`), an indirect CALL to the pointer-only game function `59FF00`
  (covered by `game-closure-r3`).
- The MFC42/initterm stops propagate out of the entry, so scenario 0's earlier recorded
  expectation (roots 1..15, frontier `5AE3E4`) no longer describes the run. It will be replaced
  once the frontier settles; the last 36/36 result above predates the MFC42 stage.

Latest (O2 scenario 0, `mfc-run-33`):
- MSVCP50 is mapped and attached by the same module loader model, after MFC42. Its attach
  completes natively: 639 bodies, 280 services.
- Main initializer roots 1-66 complete natively.
- Root 67 (`47F760`) reads the real registry in the 32-bit view, read-only (writes stop typed).
  `Software\Zipper\MechWarrior3.0` is absent on this host (status 2), and the game handles it.
- Next typed stop: `LoadLibraryA("mech3Msg.dll")`. Mech3Msg is lifted (`lifts-r35`, 13
  functions), but dynamic module loading (map, bind, nested DllMain call) is not implemented.
- About 300 lift failures remain that need reviewed x87 contracts: `fpclass`, transcendental
  functions, `fpu_set_rounding`, `nearbyint`, `sync_hyper_call`.
- Scenario 0's old recorded expectation and the 36-scenario controls have not been re-baselined.

### Into InitInstance (2026-10-12, `mfc-run-92`)

After the main `_initterm` the stage continues the entry natively (`5AC480`, data imports bound at
the hand-off) into `WinMain` -> `AfxWinMain` -> `InitInstance`. New platform services:
- Real thread hooks (`WH_MSGFILTER`, `WH_CBT`) with host trampolines that marshal into guest
  scratch memory. Faults never cross the Windows callback boundary; they are re-thrown when the
  host API returns.
- Window classes and windows (`win_bridge.inc`): real classes with the trampoline window
  procedure, per-window guest procedures through `Get`/`SetWindowLongA(GWL_WNDPROC)`, host
  procedure tokens, and marshalled pointer messages with copy-back. `DefWindowProc` and
  `CallWindowProc` receive the original host parameters. Unknown host pointers become opaque
  tokens.
- Dynamic loading of staged modules (`Mech3Msg.dll`) with a nested DllMain call, and
  `FormatMessageA` from guest message tables.
- DirectDraw (version probe, enumeration, caps, modes) and DirectSound on the real x64 system
  providers through guest COM proxies. DirectPlay lobby is a project-implemented service: the
  process was not lobby-launched, so `GetConnectionSettings` returns `DPERR_NOTLOBBIED`.
- A read-only real registry (32-bit view; writes stop typed). Files on paths resolved against a
  guest current directory (the game folder); writes are confined to it. Guest standard handles,
  timing, CPUID/RDTSC, `GlobalMemoryStatus` (non-LAA clamping), drives and volumes.
- Exact x87 raw80 bridges (`x87_bridges.py`): the literal host `fsin`/`fcos`/`fsqrt`/`fpatan`/
  `fyl2x`/`fptan`/`f2xm1`/`frndint`. Rounding is mirrored into the host x87 control word and
  MXCSR while a stage runs.

Typed stop: `IDirectDraw4::SetCooperativeLevel(hwnd, 0x13)`, the recovered video contract's
exclusive full-screen call. It stops on purpose: performing it would take over the host display,
and the real x64 DirectDraw has no Direct3D3. The presentation provider (Vulkan) is the next
decision.

### To the live menu and into Training (2026-10-12/13, `mfc-run-93`..`161`)

These are executed runs, not acceptance. The accepted count stays 131/144.

**Execution reached.**
- `mfc-run-124`: the original main menu, live and animated, presented through the virtual display.
- `mfc-run-137`: live Training 1 3D frames, rendered by Vulkan.
- `mfc-run-159`..`161`: scripted player input completes three Training steps:
  1. start-up (`S`);
  2. turning (Right-Arrow);
  3. acceleration (Up-Arrow).

  The 'Mech then walks out of the hangar into the rain, and Training advances to "Move 'Mech next to Instructor".

  Frames are kept in `reports/m4-crt-attach/live-menu-r1`, `live-training-r1`..`r3`, which is git-ignored.

**Presentation and graphics.**
- Virtual display: the exclusive level and display modes are emulated, and the host display is never taken over.
- Virtual surfaces live in guest memory, including flip chains, z-buffers and 565/1555/4444 textures. Blt/BltFast, colour keys, clippers and palettes are supported.
- Flip goes through the Vulkan swapchain presenter (`vk_scene.hpp`, a second instance of the renderer class). The front buffer is uploaded as R5G6B5 and blitted to a FIFO swapchain, so Flip waits for the vertical blank as `DDFLIP_WAIT` did.
  - The swapchain lives on a host-owned child window covering the game window's client area. The child is disabled, hit-test transparent and sends no parent notifications, so the game's messages and input are unchanged.
  - The presenter picks the adapter that can present to the window. On this hybrid machine that is the integrated GPU, while scenes render on the discrete RX 9070. Frames reach both through guest memory.
  - Guest thread hooks (MFC's CBT subclassing) are suspended while host rendering or presentation runs, so driver helper windows stay host-only.
  - GDI remains for 8-bit frames and for `MW34_PRESENT=gdi`.
- The virtual `SetDisplayMode` makes the cooperative window visible, with a client area of the mode size (integer-scaled to fit), as exclusive DirectDraw did. Scripted runs do not activate it, and `MW34_HIDE_WINDOW=1` keeps it hidden.
- `d3d_provider.inc` is a Direct3D 6 HAL provider. It covers Direct3D3, Device3, Viewport3, Material3 and Texture2, and devices start from the Direct3D 6 default render and texture-stage states. Legacy texture states are translated to stage 0, as the DX6 runtime does.
- Scenes are rendered by `vk_scene.hpp` (adapted from `tools/vulkan-probe/replay.cpp`). It loads the Vulkan loader at run time and keeps a persistent device:
  - Colour is R5G6B5 and depth is D16, matching the game's own surface formats. Both are uploaded from guest memory and read back into it, so the game's 2D HUD and Flip keep working on the same memory.
  - Fixed function lives in `d3d_scene.vert/.frag`, which are compiled to `d3d_scene_*.h`. It covers one texture stage (ops 1-14, arguments with complement/alpha-replicate), flat or Gouraud shading, perspective or affine UV, specular, vertex fog and alpha test.
  - Pipelines are cached per blend/depth/cull state.
  - Any render state that differs from its default and is not interpreted stops typed.
  - Clears outside a scene fill the guest target and z-buffer directly.

**Input.**
- Real DirectInput: keyboard and mouse, data formats, buffered data, properties and cooperative levels.
- `MW34_INPUT_SCRIPT=<file>` stands in for the player. Device objects and cooperative levels stay real; only the data comes from the script, and every read is tagged `(scripted ...)`. Line formats:
  - `FRAME mouse DX DY BUTTONS`: relative motion, delivered once.
  - `FRAME key SCANCODE(hex) down|up`: keyboard. It is delivered both as buffered records and in the 256-byte immediate state the mission reads.

  Under a script the system cursor is virtual, so the host cursor is never moved.
- `play.ps1` runs the built host with the real keyboard and mouse, or with `-Script`.

**Platform services.**
- `CreateThread` runs a guest thread to completion on a full context switch:
  - own State, x87 state, host CW/MXCSR, stack, TEB exception list, TLS values and last error;
  - `DLL_THREAD_ATTACH`/`DETACH` for MSVCRT, MFC42, MSVCP50 and Mech3Msg;
  - the thread object is a real event.

  Mutex ownership is tracked per guest thread. A thread that would block, waits on another thread's mutex, retrieves messages, or triggers window procedures stops typed. The game's mission loader (`490900`) runs this way.
- Also added: AVIFile/VfW, WINMM mixer, MCI CD audio, `DuplicateSoundBuffer`, `CreateDirectoryA` (confined to the game folder), and `CloseHandle` on a search handle (fails with `ERROR_INVALID_HANDLE`, as Windows does).

**Lifting and runtime fixes.**
- `mfc_closure.py` jump tables: an unreachable slot 0 and negative indices (the MSVCRT memcpy/memmove tables). Repairs: `repair-closure-r2..r4`, `lifts-r51..r53`.
- Direct tail JMPs to function entries are lifted as tail calls through the CALL router. `enter()` recognises them by stack slot and binds no second return word.
- Guest accesses that span two mapped regions are split into bytes.
- The x87 exp2 bridge computes FSCALE factors (integral exponents) exactly with the host FSCALE.
- Teardown releases COM proxies children-first.

**Performance.** The 3D phase went from about 2.6 to about 13 fps. A full 700-frame Training run went from 9 min 41 s to 51 s.
- The memory-contract check has exact fast paths gated by arena.
- Guest copies are bulk and page-chunked.
- The service log is bounded.
- Draws share state snapshots.
- Textures are versioned through every API write path.
- `guest_memory_cached.cpp` is a native-host implementation of `GuestMemory` with a direct-mapped page→region cache. The interface and every fault are unchanged. The pinned `runtime/memory/guest_memory.cpp` is untouched.
- `MW34_PROFILE=<file>` (optionally with `MW34_PROFILE_FROM=<frame>`) samples the main thread. The link now emits a PDB.

**Fidelity limits.**
- The intro video decodes with the game's own staged Indeo IV50 codec. `Ir50_32.dll` is rebased to 0x11000000 by `rebase_image.py`, lifted (2,583 functions), and driven through its `DriverProc` with msvfw32's ICM protocol. Disable it with `MW34_STAGED_CODEC=0`.
  - Supporting services: guest virtual memory, named page-file sections, guest heaps, moveable local memory, and the CRT startup services.
  - Its MMX `PADDUSB`/`PADDUSW` needed `MW34_SEMANTICS=mmx`: the repaired remill semantics with four added MMX encodings (`local/tools/remill-mmx-build`). The rebuild procedure reproduces the pinned semantics byte for byte, and re-lifted game functions compare identical.
  - remill's MMX/x87 aliasing values take the zero representative.
- x87 `FPATAN` and `FPREM` are exact. remill lowered FPATAN to atan(y/x), losing the quadrant (camera and angles 180 degrees off). The bridge now runs the host `fpatan` on both operands, and `fprem` until C2 clears.
- FYL2X and F2XM1 carry one extra rounding.
- The game writes `MW3/mech3.out` and `mech3.err`.
- Real mixer volume changes affect only this process's audio session.
- Dithering on 16-bit targets is not reproduced.
- Cull-mode winding is not yet verified against a scene that culls.
- Guest threads run to completion and are not preempted.
- About 13 fps in the heaviest Training scenes.
- Presentation copies each frame from guest memory once per Flip, with no frames kept in flight.
