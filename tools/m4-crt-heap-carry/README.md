# Integrated native MW3 host (retail entry route)

Current status, 2026-10-13: this experimental x64 host has executed the live
animated main menu, Vulkan-rendered Training 1 with the game HUD, startup and
walking, and normal Quit -> confirm shutdown with exit code 0. The intro's
recompiled Indeo IV50 codec decoded in hidden-window runs. Training 1 runs at about
19 fps falling to 12 fps as the mech walks outdoors (menus 40+ fps) on the
development system. Instant Action (Big Lake) was played interactively by the user for about a
minute and exited through the native shutdown. Scripted Instant Action runs fired
weapons with the original default bindings (Space = trigger, keypad Enter = alpha
strike): laser beams, hits on buildings, and an overheat explosion ran natively. Scene point lists
(`D3DPT_POINTLIST`, drawn after targeting) render as one-pixel points; line
primitives still stop visibly. These are executed runs, not
formal acceptance; the accepted count stays **131/144**.

See the [session summary](../../docs/session-summary-2026-10-13-native-host.md)
for the full source/evidence record and limitations. Camera flip and leg animation
were observed in interactive play; the built FPATAN quadrant correction in 57
re-lifted functions awaits a play retest. Visible intro playback, remaining
Training, weapons and original/native physics, AI and timing comparisons are
still open. Strict acceptance v6 remains a separate review/criterion decision.

## Local build and launch

### Reading the host source

This directory retains several dated execution stages. Read their names and
contracts before interpreting a historical stop point as the current game state.
The current launcher's selected executable/profile and matching private source
snapshot determine the active host; this checkout alone is not that build receipt.

| File / type | Responsibility | Ownership and interpretation |
| --- | --- | --- |
| `composition.cpp` | Connect translated entries, service contexts and provider attach stages | Generated bodies/dispatch tables stay local; an absent admitted route must fault |
| `parser_stage.hpp`, `heap_stage.hpp` | Earlier connected CRT boundaries | Preserve their recovered order and side effects; later MFC/game stages build on them |
| `mfc_stage.hpp` / `Host` | Long-lived provider modules, handles and service bookkeeping | Host pointers live in host records; guest-visible handles/addresses remain 32-bit tokens |
| `mfc_stage.hpp` / `map_image` | Map admitted provider bytes and bind imports | Mapping data does not execute provider code or complete attach |
| `mfc_stage.hpp` / `Stage` | Active translated call/return state and API dispatch | `run`, `called`, `missing` and `deny` are the routing/failure path to follow first |
| `win_bridge.inc` | Guest-facing Windows window/callback bridge | Marshal structures and callbacks; do not cast guest addresses to host pointers |
| `vk_scene.hpp` and authored shaders | Render submitted scene state | Renderer/GPU ownership is distinct from guest surface memory and simulation state |
| `../remaster-launcher/native-overrides/` | Later authored overlays and repairs | Read the applicator order and matching build snapshot; this is not a universal replacement tree |

Follow one service from its import token through argument decoding, real host
call, guest-visible output writes, status and stack cleanup. Preserve failure
writes and last-error behavior as well as the success path. For callbacks, follow
the return token and active owner through re-entry; a similarly named guest
function is not enough to establish a safe native call signature.

`State` carries translated guest register/FP state. Runtime memory owns guest
bytes; `Host` owns native objects; `Stage` scopes active dispatch. FP guards must
restore the host environment on both normal and exceptional exit. Rendering and
audio may use host threads, but this does not make guest state concurrently safe.
Read each component's threading/ownership comments before moving work between them.

Keep frozen source versions intact when adding explanatory notes. Reformatting a
receipt-bound host or applicator changes its identity even when generated code
appears equivalent. Put a reviewed successor in the actual build chain and retain
the previous version rather than silently rewriting accepted evidence. The
[code guide](../../docs/code-guide.md) identifies the maintained launch/editor
interfaces and the separate readability and functional-review work.

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
  - The presenter picks a discrete GPU that can present to the window, and otherwise any GPU that can. On the dev machine both rendering and presentation run on the RX 9070 (`mfc-run`, 2026-10-13 06:14). An earlier run fell back to the integrated GPU only because the monitor on the RX 9070 was switched off. Frames reach the presenter through guest memory, so either adapter works.
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
- 2026-10-13, second pass (measured with `MW34_FRAME_TIMES`, aligned to the first 3D scene): Training 1 went from about 15 -> 9 fps to about 19 -> 12 fps over its first 36 seconds.
  - The stage's own stack frame, the game image/.data and the guest heap (about 99% of mission accesses; about 2.9 million accesses per frame) are checked inline before the full contract predicate. These are leading disjuncts of the same predicate, so nothing new is admitted. The region cache (`guest_memory_fast.hpp`) is inline, and the thread guard reads the thread id from the TEB.
  - Scene readback buffers prefer host-cached memory. Uncached readback had cost about 8% of mission time in `memcpy`.
  - Not changed: the per-instruction x87 exception clear/test (about 14%). Some lifted sites branch on the fresh exception result, for example integer-indefinite conversions, so a lazy clear would not be exact.
- `MW34_FRAME_TIMES=<file>` writes one line per presented frame: frame number, host milliseconds and the 3D scene count.
- `MW34_VIRTUAL_CLOCK=<ms>` (scripted runs only; refused without `MW34_INPUT_SCRIPT`) makes a scripted run deterministic.
  - Every guest time source (`timeGetTime`, `GetTickCount`, `QueryPerformanceCounter`/`Frequency`, the system/local time and `+MS` script timing) reads one virtual clock.
  - The clock advances by `<ms>` at each presented frame and by 1 us per query, so polling loops progress. `Sleep(n)` advances it by n ms and does not block.
  - The date starts at 2000-01-01 UTC. Interactive play never uses the virtual clock.
  - Two runs of the same Training script compared 24 of 24 dumped frames byte-identical; two runs of the same Instant Action weapons script compared 131 of 131 byte-identical, with laser shots at 0:21 and 0:28 in both.
  - Replay determinism (2026-10-14). Visible replays used to split, about 1 in 4, into two stable variants from frame 10 (the main-menu background pixel pattern). A buffered service trace (`MW34_TRACE_SERVICES=<file>`, optionally `MW34_TRACE_ONLY=name,...`, covering frames 0-12) located the split at a DirectSound `GetCurrentPosition` poll from the game's audio streaming (`0x575690`, caller `0x59ad70`). Under the virtual clock the host now virtualises three real-time inputs:
    1. Sound buffers: play and write positions and the playing/looping status come from virtual time since `Play`/`SetCurrentPosition`/`SetFrequency`, times the buffer's byte rate. The real calls still run.
    2. `RDTSC`: virtual microseconds × 3000. The game's start-up CPU-speed measurement (`0x5988c0`, part of the hardware-detection routine `0x597fc0`) now yields a fixed value.
    3. Desktop messages: real-cursor mouse moves, the undocumented system message 0x0060 and `WM_DWMNCRENDERINGCHANGED` are removed from the queue before the game sees them.
    - Interactive play is unchanged.
    - Result: 6 of 6 replays were byte-identical. The baseline was re-recorded from the unmodified normal O2 build (`input-training-t8000-v2`). Against it, full merge-r3 and full strict-x87 were each identical 2 of 2, and so was the strict play build.
  - `MW34_VIRTUAL_CLOCK_BASE_MS=<tick>` starts the virtual clock at that tick instead of 1000 ms, for example a real host uptime, to replay the engine-clock rounding described below.
- Guest tick clock (2026-10-13). The engine clock is `0x575a00`, called once per main-loop pass. It reads `GetTickCount`, stores "now" as float32 seconds (`0x5f096c`), and sets the frame step `0x72c52c` = now - previous float (times a one-shot scale `0x5f0970`), clamped to 0.125 s (`0x5f0960`/`0x5f0964`). Game time `0x72c530` accumulates the step. About 100 game sites consume the step; the simulation is variable-step, and no frame limiter was found (the only `Sleep(30)` runs once, at scene start in `0x480df0`).
  - Defect under raw uptime: float32 seconds lose resolution as Windows uptime grows. At 7 days (603,594,948 ms) the resolution is 62.5 ms, so every frame step is off by up to +/-31 ms, and steps can be zero or negative. A PC booted hours before, as in 1999, had about 1 ms.
  - Fix: `GetTickCount`, `timeGetTime`, message times (`MSG.time`, `GetMessageTime`) and DirectInput buffered timestamps now read one guest clock: milliseconds since the host started, plus 60,000, taken from the performance counter (1 ms steps instead of `GetTickCount`'s 15.6 ms). Host stamps passed back in (`MSG` arguments) are mapped to the host domain. `QueryPerformanceCounter` is unchanged; the game uses it only to calibrate CPU speed.
  - `MW34_GUEST_CLOCK=uptime` restores raw host uptime. The virtual clock is unchanged, and under it message/input stamps stay host stamps, as before.
  - Evidence (`reports/m4-crt-attach/guest-clock-r1`): the Training replay at the virtual-clock base equal to this PC's 7-day uptime ends in MISSION FAILURE, with the mech destroyed against the bunker, while the default base and the 60 s base complete the steps.
  - Step-size check (the above-30-fps question): the same script at 50, 25 and 12.5 ms steps (20/40/80 game fps) ends its 8 s turn at a compass heading of 195.0, 192.2 and 190.8 degrees. The difference halves with the step, which is convergent first-order behaviour. Objectives and mission progress match at 0:22, 0:31 and 0:45. Higher frame rates need no engine change; the step was always hardware-dependent in the original.
- Inlined bridge fast paths (opt-in build, 2026-10-13): `inline_objects.py <out>` rebuilds all 37,172 recompiled MFC-stage objects from their existing `-host.ll` with the hot bridges (`__remill_{read,write}_memory_{8,16,32,64,f32,f64}`, `__remill_fpu_exception_{clear,test}`) redirected to the always-inline fast paths in `fast_bridges.cpp`; `build.ps1 -Levels O2 -Inline <out>` links them into `build/m4-crt-heap-carry-O2-inline` (`play.ps1 -Build O2-inline`). Original lift reports and objects are untouched.
  - Exactness: a fast path succeeds only when every check of the out-of-line bridge holds (Stage owner/token/thread/active/complete from the `fast_gate.hpp` gate published by `Stage::run`, `read_fast`/`write_fast`, the GuestMemory region cache); otherwise it calls that bridge unchanged. The fast-path bitcode is header-free so no C runtime directives enter the objects; `mfc_stage.hpp` static_asserts the cache-entry mirror layout. Disassembly shows fnclex before and fnstsw after each x87 operation, as before.
  - Validation: deterministic replays (MW34_VIRTUAL_CLOCK=50) of the Instant Action weapons script and the Training walk-out script gave byte-identical frames to the normal build (116 of 116 each).
  - Cost and gain: the executable grows from about 153 MB to 513 MB (the worker-identity and input read bounds were raised to 1 GB for it). Interleaved deterministic benchmarks on an idle machine (Training script, MW34_VIRTUAL_CLOCK=50, two runs each) gave 59.9-60.0 versus 62.7-63.5 ms per frame for frames 300-700 and 65.4-66.0 versus 69.4-69.8 for frames 700-1150: about 5-6% faster. The remaining cost is the x87 status serialisation and the access checks themselves, not the call boundary. The Vulkan scene path (upload, draw, fence wait, readback) is not the bottleneck either: in the deterministic Training benchmark it took 1,764 ms for 2,635 scenes, about 0.67 ms per scene and 2.9% of the 60 s of 3D wall time. The remaining frame time is the recompiled game code itself, including remill state traffic, x87 brackets and contract checks.
- Host-side dispatch (2026-10-13, both builds):
  - COM method imports go straight to the COM dispatch instead of walking the Win32/CRT service chain. Every test skipped this way is keyed on a name or prefix that no modelled interface method has; GetDC/ReleaseDC, the only shared names, are used before the shortcut.
  - `__remill_fpu_set_rounding` executes the serializing `fldcw`/`ldmxcsr` only when the mode changes.
  - Lifted-body lookups go through a direct-mapped cache over the fixed entry tables.
  - Deterministic replays stay byte-identical. The only Instant Action difference was the pilot screen's "Player kills" counter, 7 to 8, from the user's fight saved in the registry overlay.
  - Benchmark: normal build 60-62 / 66 ms per frame (was 62.7-63.5 / 69.4-69.8); inline build 56-58.6 / 61.5-63.5 (was 59.9-60.0 / 65.4-66.0). Inline plus dispatch is about 11% faster than the original normal build.
- Merged x87 exception tracking (2026-10-13, user-approved semantics): `merge_x87.py`, enabled by `inline_objects.py --merge-x87`. The tool runs each object's `host.ll` through `opt -passes=simplifycfg` and then this pass.
  - What it removes: remill brackets every x87 operation with clear/op/test and seven sticky OR updates of the guest exception bytes. A sample-level profile showed that tracking (`fnclex`, `fnstsw` and the dependent `orb` chain on offsets 2745-2757) at about a third of game-code time.
  - The rewrite: within a straight-line run (one block, or a single-entry/single-exit acyclic region such as remill's denormal-check diamond), only the first bracket clears, the interior status reads become 0 (their updates fold away at O2), and the last bracket ORs the union in.
  - A run ends at: a bracket whose result has any other use (for example integer-indefinite conversions) or a non-127 mask; any call other than the memory bridges, llvm intrinsics or remill's pure undefined-value helpers; any load of an exception byte; any store to one other than remill's single denormal assignment directly before a clear (a guest FCLEX or FNSTSW therefore always ends a run); or a region with other entries or exits.
  - Semantics: identical for IE, ZE, OE, UE, PE and SF. Within a run, DE now stays set from earlier operations, which is the hardware's sticky behaviour, where remill's per-instruction denormal assignment would have reset it. The user approved this.
  - Coverage: 38,788 of 70,940 brackets merged, in 15,127 runs across all 37,172 objects (`reports/m4-crt-attach/inline-r3/report.json`).
  - Validation: deterministic replays are byte-identical to the normal build (Training walk-out 116/116; Instant Action weapons 48/48 against a same-overlay reference).
  - Benchmark (Training script, MW34_VIRTUAL_CLOCK=50, frames 700-1150): 46.7-47.5 ms per frame, against 61.2-61.6 (inline, unmerged) and 66.3-66.5 (normal); frames 300-700: 45.0-45.1. That is about 21 fps in the heaviest stretch, from 14.4 before this work.
  - merge-r2 (2026-10-13; `Play-MW3.cmd`'s build): runs may also span remill `__remill_flag_computation_*`/`__remill_compare_*` calls that the object defines as the identity (`ret i1 %0`). Coverage: 40,888 brackets in 15,824 runs (`reports/m4-crt-attach/merge-r2/report.json`), with the guest tick clock linked in. The Training replay is byte-identical to the reference (116/116, visible window). The Instant Action weapons replay matches 110/116; the other 6 are pilot-screen frames whose only difference is the 9x10-pixel "Player kills" digit (7 to 8, from the user's fight saved in the registry overlay). Every in-mission frame is identical.
  - merge-r2 benchmark (input-training-8, two alternating runs per build, visible window, steps over 1 s excluded): frames 300-700 took 48.9/49.3 ms, against 63.4/60.9 for the normal build; frames 700-1150 took 53.5/55.4 against 67.7/70.0. That is 0.79x the normal build's frame time, against 0.77x for merge-r1 earlier, so the extra merges give no measurable gain. Both builds were about 7% slower than the earlier hidden-window runs. Note that this script holds Right Arrow 1.5 s too long, so the mech turns into the bunker wall in every build; use `input-training-t8000` for walk-out checks.
- Code-quality investigation and exact cleanup (2026-10-13, `ir_cleanup.py`, `inline_objects.py --cleanup`).
  - Finding: one hot game function (`0x545720`, about 1,000 x86 instructions) compiled to about 40,400 host instructions with 1,508 calls, roughly 30 host cycles per guest instruction.
    - remill materialises every flag, the PC, the x87 status/last-instruction fields and a denormal check on every instruction.
    - It shifts the eight-register x87 stack with 10-byte memcpys.
    - 734 of the calls went to do-nothing helpers: variadic identity `__remill_flag_computation_*`/`__remill_compare_*`, and the always-0 undefined representative.
    - Every memory bridge may throw, so LLVM keeps State in memory around each call.
    - Profile (merge-r2, heavy Training): page-permission checks are about 3% (so a page cache was skipped); memory bridges about 16%; outside the executable about 23% (fence waits and readback memcpy).
  - `--cleanup` does four things, all exact for guest-visible values:
    1. Replaces identity helper calls with their argument and undefined representatives with 0.
    2. Turns 10-byte x87 slot memcpys into `i80` load/store.
    3. After the x87 merge, declares the memory and x87-exception bridges `nounwind memory(inaccessiblemem: readwrite)` and gives bodies `uwtable`. Bridges never touch State, and a throw from one is always a run-ending deny.
    4. Adds a second optimisation round (`opt default<O2>`, then `dse,gvn,dse,instcombine<no-verify-fixpoint>,simplifycfg,dse`, then `clang -O2`).
    - Only non-speed effect: a deny message may quote a State value from before the failing access.
  - Effect on `0x545720`: 31,643 host instructions (−22%) and 774 calls (−49%).
  - Measured with the 99 profiled hot functions rebuilt (`merge-r3-mix`, `build.ps1 -Suffix -clean`), Training `input-training-t8000`, `MW34_VIRTUAL_CLOCK=50`, two alternating rounds, visible window: frames 300-700 took 40.7/42.0 ms against 47.0/48.7 for merge-r2 (−13.6%); frames 700-1150 took 23.0/23.0 against 26.1/26.0 (−11.7%). All four runs were byte-identical to the reference (116/116). The full rebuild is `reports/m4-crt-attach/merge-r3`.
  - Full rebuild `merge-r3` (all 37,172 objects; exe 96 MB, down from 155 MB) is `Play-MW3.cmd`'s build. On 2026-10-14, input-training-t8000, two alternating rounds per build (ms per frame, frames 300-700 / 700-1150):

    | Build | 300-700 | 700-1150 |
    |---|---|---|
    | 99-function mix | 35.2 | 19.5 |
    | full merge-r3 | 33.5 | 18.2 |
    | `--strict-x87` on the 99 hot functions, rest merge-r2 (`O2-strict`) | 31.9 | 17.8 |
    | strict + inlined memory fast paths (`O2-strictinl`) | 39.0 | 21.3 |

    - Inlining is slower (code bloat) and was dropped. Strict x87 is the full rebuild `merge-r4` (`--cleanup --strict-x87`).
    - Every build was byte-identical in at least one run. The misses were all the frame-10 menu-fade replay noise described under the overlay.
  - `--strict-x87` (ir_cleanup.strict_x87):
    - Every FP operation becomes a constrained intrinsic (`round.dynamic`, `fpexcept.strict`) in a `strictfp` body, so it stays ordered against the inaccessible-memory bridges, and remill's `~{memory}` fences are removed.
    - The denormal-classification compares (against 0, infinity and the smallest normal, evaluated before each operation's exception clear) become integer tests on the bit pattern. These were checked against hardware x87/SSE compares and LLVM's optimised form on all 2^32 float patterns and 240 80-bit class patterns (0 mismatches).
    - A module whose FP operations cannot all be converted is left unchanged; none of the 99 hot functions needed that (64 converted, 35 have no FP).
    - In converted bodies, `__remill_fpu_exception_clear(127)` and `_test(127)` become inline `fnclex` and `fnstsw & 127`, whose only declared effect is the FP environment (inaccessible memory, so they stay ordered against the constrained operations).
      - Profile (1 kHz, strict build): the two out-of-line bridges were 11.3% of samples.
      - Measured on the 99 hot functions over merge-r4, deterministic: 4/4 byte-identical to the baseline; frames 300-700 took 29.6 against 31.2 ms, frames 700-1150 took 16.9 against 17.6 ms.
      - Full rebuild: `merge-r5`.
  - `--x87-noexc` (with `--strict-x87`; ir_cleanup step 7): no x87 exception tracking in the game's own bodies (`0x401000-0x5bb000`).
    - Basis: all 3,733 FNSTSW sites in Mech3.exe test only AH (C0/C2/C3), and it has no FNSTENV, FNSAVE or FNCLEX.
    - In those bodies, exception brackets and exception-byte stores are removed, and constrained operations use `fpexcept.ignore`, which still orders them against rounding-mode changes.
    - CRT and MFC bodies keep full tracking. The game calls `_CIacos`/`_CIasin`/`_CIpow`/`_CIsqrt`/`_CIfmod`/`_hypot`/`floor`/`ceil`/`_ftol` and installs `__setusermatherr`.
    - Code size: `0x545720` went from 30,751 to 15,742 host instructions; stack spills from 7,228 to 4,058.
    - Measured on the 99 hot functions over merge-r4: byte-identical to the Training baseline (2/2) and the Instant Action baseline (1/1, fight with CRT math). Frames 300-700 took 25.1 against 35.4 ms (−29%), frames 700-1150 16.6 against 21.4 ms (−23%), with a background rebuild running.
    - Full rebuild: `merge-r6`.
  - Flat guest memory (2026-10-14; `--flat-mem`, ir_cleanup step 8; user-approved host-only fork).
    - Storage: `memory/guest_memory.hpp` in this directory forks the runtime header. It is first on the host include path; the runtime file and the pinned `runtime/memory/guest_memory.cpp` are unchanged. `guest_memory_cached.cpp` implements it flat: one 4 GiB (+64 KiB guard) reservation per guest space, each region at `flat_base() + guest address`. Pages are committed while any region touches them, with host protection from the union of those regions' permissions; regions stay exact and zero-initialised, and host transfers keep the exact checks, faults and region cache.
    - The fdiv registry sources (`registry.cpp`, `runtime.cpp`, `image_loader.cpp`, plus the writer object) are now compiled into the host (`native/CMakeLists.txt`) instead of linked from `fdiv_registry.lib`, whose copies used the runtime layout.
    - Stage tokens are the flat base (`stage_token`). A vectored handler turns a hardware fault inside the active Stage's reservation into its typed deny.
    - The IR rewrite turns every `__remill_read/write_memory_*` call into `load/store (token + zext address)`. Guest code thus gets page-level protection, as on Windows; the finer per-access memory contract still applies to host-service arguments.
    - Validation: the unmodified O2 build on the flat backend is byte-identical to the baseline (116/116). The 99 hot functions with `--flat-mem` over merge-r4 are byte-identical on Training (2/2) and Instant Action (1/1).
    - `0x545720`: 15,742 to 12,495 host instructions, 596 to 9 calls.
    - Benchmark (quiet machine): frames 300-700 took 13.2 against 19.2 ms (−31%), frames 700-1150 8.5 against 11.5 ms (−26%).
    - Full rebuild: `merge-r7` (`--cleanup --strict-x87 --x87-noexc --flat-mem`), about 30 min with 14 jobs. It is the play build since 2026-10-14.
      - Byte-identical on Training (3 runs, one with the overlay) and Instant Action (1 run).
      - Training: 7.4-7.6 ms in frames 300-700 and 6.9 ms in 700-1150 (about 130-145 fps). merge-r4 measured about 30 / 17 ms.
      - Instant Action: 7.5 / 7.1 ms.
  - Host-built startup seed (2026-10-14; `MW34_SEED=host`, the `play.ps1` default; `MW34_SEED=before` selects the original projection).
    - The run no longer reads the original BEFORE pack. Its registers and FP contents were authored patterns; its stack page was residue of the original process.
    - The host builds the state at the FDIV writer itself: zero registers (ESP/EIP/EFLAGS as the projection), a new Win32 thread's x87/SSE state (FCW `0x27F`, MXCSR `0x1F80`), and a zeroed stack page with the normalized outer return word.
    - Identical on Training (3 runs) and Instant Action (1 run); frame time unchanged.
    - Details and remaining limits are in `docs/e0-application-execution-path.md`.
  - Scene fingerprint for original/native comparisons (2026-10-14; `MW34_DRAW_LOG=<file>`, host-only).
    - At each presented frame the host writes the frame number, the count of `DrawPrimitive`/`DrawIndexedPrimitive` calls, and an FNV-1a 64 hash over each call's primitive type, vertex count, the game-computed TL vertex bytes and indices, in call order.
    - The game transforms and lights everything itself, so the hash carries its physics, AI, animation and camera results without any structure addresses.
    - Deterministic: two Training replays gave identical lines for all 1,150 frames (about 1,600-1,750 draws per heavy frame). It is also a stricter exactness check than the every-10th-frame PPMs.
    - Original side (not yet built): a separate injected x86 DLL must give the original process the same virtual clock (GetTickCount/timeGetTime/QPC and message/input stamps), scripted DirectInput, DirectSound positions/status, `rdtsc` emulation for the CPU-speed test and desktop-message filtering as this host, plus the same hash over `IDirect3DDevice3::DrawPrimitive`. Provider caps (display modes, texture formats, device description) must also match, or the game's own choices diverge.
    - Every time query under the virtual clock advances it by 1 µs (`vclock_query`). The original side must therefore virtualize exactly the guest modules' calls (Mech3.exe, MSVCRT, MFC42, MSVCP50 imports) and no system-DLL calls.
    - Runtime mismatch found 2026-10-14: `MSVCRT` is a KnownDLL on this Windows, so the original `Mech3.exe` always loads Windows' current System32 `msvcrt.dll` (and System32 `mfc42.dll`/`msvcp50.dll`). The native host runs the CD's 1998 MSVCRT/MFC42/MSVCP50 (`local/mw3-staged/Shared_DLLs`). CRT math (`_CIpow`, `_CIsqrt`, …), `rand` and heap behaviour can differ between those versions.
    - A same-runtime comparison needs the original process to bind the staged DLLs. The obvious ways all fail or overstep: an app-local copy loses to KnownDLLs; changing the KnownDLLs registry is not allowed; swapping after entry would mix CRT heaps. What remains is import renaming in local research copies, which changes the admitted image hash. Alternatively, compare against today's runtime and attribute the CRT-version divergences explicitly. That design decision comes before building the original-side DLL.
    - Decision (user, 2026-10-14): compare on the 1998 runtime. `tools/mw3-compare/prepare_runtime.py OUT` builds the research copy (`local/compare-r1`):
      - Mech3.exe, Mech3Msg.dll and the CD MFC42/MSVCP50 import `MSVCRZ.dll`. Each patch changes only the import name string, checked byte for byte against the source; the sources match the native pins.
      - `MSVCRZ.dll` is the CD MSVCRT.DLL. dgVoodoo is set windowed in the copy (no display takeover); pilots/configs are copied and zbd is a junction.
      - Observed in a smoke launch: MSVCRZ at `0x78000000`, MSVCP50 at `0x780C0000`, MFC42 at `0x5F400000` and IFORCE2 at `0x10000000`, all from the copy. System msvcrt.dll also loads for Windows' own DLLs, but the game, MFC and MSVCP no longer bind it.
      - Original side, built 2026-10-14: `tools/mw3-compare/compare_hook.cpp` with `compare_launcher.cpp` (Win32, CMake), injected at the entry.
        - Mirrors the native scripted environment: virtual clock (+1 µs per query, file time, `Sleep`); `rdtsc` ×3000 at the three Mech3.exe sites; scripted DirectInput; virtual DirectSound positions; desktop-message drop; virtual cursor.
        - Mirrors the native host model: the registry overlay (`MW34_REG_OVERLAY`; real registry never written), `MW34_STAGED_CODEC=0` (no IV50 decoder) and guest threads run to completion in `CreateThread`.
        - Diagnostics: back-buffer PPMs, per-draw detail with caller stack, `.data` dumps; optionally the native texture formats and video memory (`MW34_NATIVE_CAPS`).
      - Result on the Training script:
        - The virtual clocks agree on every frame, so both sides make the same number of time queries.
        - The full draw-stream fingerprints are bit-identical for frames 1-250 and 700-1150 (about 1,500-2,000 draws per 3D frame).
        - Frames 251-699: the original draws 4-7 more particle quads per frame (same render path, `0x4F71F0` ← `0x5493E6` ← `0x4F7A6E`); every other draw is identical.
        - Ruled out: the clock, the game's FYL2X/F2XM1 sites (exact here), uninitialized large heap blocks, native depth write-back, and provider texture formats/video memory. Open.
      - Native defect found and fixed: `GetFileVersionInfo*A("mech3.exe")` resolved against the host process directory, so the menu showed 1.2.0.0. It now resolves the guest application directory first (1.2.22.0). Draw streams are unchanged; new baselines `input-training-t8000-v3` / `input-ia-13-v3`.
      - Provider differences seen: dgVoodoo offers more texture formats and 256 MB of video memory; native offers three 16-bit formats and passes through the host's 3-4 GiB. Native formats need not match 1999 hardware (user, 2026-10-14). Choose them for performance; the gameplay comparison stays the test.
  - True loader order (2026-10-14; `MW34_STARTUP=loader`, the `play.ps1` default; `MW34_STARTUP=accepted` keeps the accepted bounded entry chain).
    - Order: MSVCRT attach, the `_acmdln` writer (guest copy of the real command line at `0x33000000`), resume, MFC42 and MSVCP50 attach, then the game's CRT entry `0x5AC3A0` whole in the generic stage (`Kind::initterm` started at the entry, `from_entry`).
    - New bodies: `lifts-r63`, the 25 CRT-entry/`__getmainargs` functions the generic set lacked; dispatch regenerated with it appended. The play build links `reports/m4-crt-attach/merge-r7-entry`.
    - Identical on Training (3 runs) and Instant Action (1 run). The accepted chain on the same build is identical too.
  - Host service dispatch (2026-10-14). Training issues about 3,700 guest services per frame, nearly all `IDirect3DDevice3::SetTexture`/`DrawPrimitive` pairs. The host costs per call, all now removed, were:
    - linear searches over every import (`by_bound`), every COM object ever created (`com_object`, several per call) and every provider surface (`vsurface`); these are now first-match indexes over the same append-only vectors (COM tokens come from a bump allocator and are never reused, and a dead object still takes the original scan);
    - a freshly concatenated service-log label (now built once per import and prefix);
    - case-insensitive compares that upper-cased string copies (`same`, `Host::same_name`), and `std::string` temporaries in `com::is_d3d`/`is_lobby`;
    - about 20 name compares before the two hot Direct3D methods (now selected first, by a selector resolved once per import; every other branch keys on a different name).
    - Result: identical on the Training baseline (3 runs); about −13% per frame on the hot-set build (host services fell from 17% to 7% of samples).
  - Tried and removed: lean inline memory paths. Precomputed host windows for stack, heap slices and image/data, behind a generation check. Exact (4/4), but 30% slower: each inline site's checks and slow-path call bloated the code. Removing the bridge cost needs a flat guest mapping (one add plus load per access, no per-site checks), which changes `GuestMemory`'s region storage in the runtime header.
  - Profiler: `MW34_PROFILE` now samples at a real 1 kHz (high-resolution waitable timer; `Sleep(1)` woke only every ~15.6 ms) and writes the complete address histogram.
  - Measured but not adopted, because it is not exact as is: relaxing remill's FP memory fences (−37% statically). Doing that exactly needs strict-FP intrinsics plus integer denormal classification.
  - GPU-resident scenes allocate no host pixel buffers (2026-10-14).
    - The profile of the play setup (mode 7, GPU frame and HUD, fit window) showed 22% of samples zero-filling width×height `color`/`depth` vectors. They were allocated in every `render_scene`, `gpu_fill` and `hud_flush`, although a resident scene uploads and reads back nothing.
    - They are now sized only for an upload or a readback; `Renderer::render` checks their size only then.
    - Result: Training draw stream identical (1150/1150, mode 7); CPU path 116/116. Uncapped, frames 150-1150 went from 7.67 to 4.98 ms per frame; frames 300-700 from 9.46 to 6.63 ms; frames 700-1150 from 7.34 to 4.14 ms.
    - With the default FIFO presentation, frames 700-1150 now meet the 144 Hz display limit (6.93 ms).
  - `MW34_PRESENT_MODE=fifo|mailbox|immediate` (default `fifo`, matching `DDFLIP_WAIT`). Uncapped presentation is an explicit setting for benchmarks and VSync-off play; an unsupported mode keeps FIFO with a notice. Measure host speed uncapped: under FIFO a frame faster than the display waits for it.
  - Profiler diagnostics: samples outside the executable also record the first executable frame up to 24 frames up (`%%` lines: leaf module+offset, calling host frame). `MW34_VK_LOG=1` logs scene-target recreations.
  - MSVCRT `_ftol` host body (2026-10-14; `mfc_stage.hpp` `ftol_core`/`ftol_body`, installed by `find_uncached`; `MW34_FTOL_FAST=0` disables it).
    - The game calls `_ftol` about 11,000 times per Training frame. The lifted body runs two rounding-mode bridges (serializing `fldcw`/`ldmxcsr`), two FWAIT exception clears, an `frndint` bridge and an `fnclex` around one `fistp`.
    - For a finite normal or zero ST0 with |ST0| < 2^63, the host body produces the lifted body's exact effect, using its own State offsets:
      - stack words and the 64-bit result;
      - EAX:EDX, EBP, ESP, EIP and EFLAGS;
      - the x87 pop and TOP, the last-instruction fields, the DE/PE/IE status rules;
      - the host rounding mode and the cleared host exception flags.
    - Every other operand takes the lifted body.
    - `MW34_FTOL_CHECK=1` runs both bodies on every call and stops on any difference in State, stack bytes or host x87 CW/SW and MXCSR.
      - Training passed: 12.6 million calls identical, 12 lifted fallbacks, frames 116/116.
      - Instant Action passed: 17.8 million identical; the fast IA run matches the checked run on 116/116 frames.
    - With it: Training CPU path 116/116; mode-7 GPU draw stream 1150/1150.
    - Uncapped per frame: frames 300-700 from 6.63 to 5.53 ms, frames 700-1150 from 4.14 to 3.45 ms, average of frames 150-1150 from 4.98 to about 4.27 ms. `_ftol` fell from about 15% of samples to 2.6%.
  - Next measured costs, uncapped:
    - Per-scene `vkQueueSubmit`, fence wait and driver GPU-memory frees: about 15%. Each scene, fill and HUD flush shares one command buffer, descriptor pool and vertex buffer, so the CPU waits for the previous scene. A small ring of per-slot resources would remove that wait.
    - Presentation: about 0.35 ms per frame. A prototype removes the x87 stack shuffling (3,242 to 24 80-bit moves), but out-of-line bridge calls still force x87 spills, so that path also needs inline fast paths. This is the next recompiler step.
- Performance overlay (2026-10-13, off by default): `MW34_PERF_OVERLAY=1`, `play.ps1 -Overlay`, `Play-MW3.cmd -Overlay` or `Play-MW3-Overlay.cmd`.
  - The Vulkan presenter draws presented frames per second, plus the mean and worst time between presents over the last second, refreshed four times a second.
  - It draws in a small built-in font into its host upload copy of each flipped frame. Guest memory and frame dumps are unchanged.
  - The GDI fallback presenter shows no overlay.
  - Deterministic replays: since the 2026-10-14 harness fixes (virtual DirectSound positions, RDTSC and desktop-message filtering, see the virtual clock), overlay-on replays are byte-identical to the baseline (2/2), so the overlay can stay on. History: before those fixes, 4 of 7 overlay-on replays diverged from frame 10. The difference was the main-menu fade-in level (every non-black pixel slightly brighter or darker), i.e. a virtual-clock offset, not changed content.
    - The overlay's pixels cannot reach guest memory: separate buffers, and a trace found no window-DC `BitBlt`/`StretchBlt`/`GetPixel`.
    - A bisect found the full changing text was required; timing only, formatting only and short static text stayed identical. A plain 5 ms present delay also stayed identical.
    - So it perturbs how many virtual-clock queries occur before the menu fades in. That is a sensitivity of the replay harness, which advances the clock per query; game logic is not changed.
- `ShowOwnedPopups` is passed through to Win32. It is reached from the game's `WM_CLOSE` handler when the window is closed (title-bar X or Alt+F4); before this the host stopped with "Unimplemented host service".
- `WH_CBT` `HCBT_CLICKSKIPPED` (x86 MOUSEHOOKSTRUCT, 20 bytes) and `HCBT_MOVESIZE` (RECT) are marshalled. A click on the visible game window during a scripted run had stopped the host with "WH_CBT code not modelled: 6".
- `WM_HELP` (sent by DefWindowProc for F1) is marshalled as the x86 HELPINFO; previously an F1 press stopped the host visibly ("Pointer message without marshalling: 83").
  - Host-speed benchmark: the virtual clock makes every frame's game work identical across builds, so wall time per frame (from MW34_FRAME_TIMES) measures host speed alone. On 2026-10-13, with the Training script from training-failure-r1 at MW34_VIRTUAL_CLOCK=50, frames 300-700 took 62.6 ms per frame and frames 700-1150 took 69.0 ms per frame (14.5 fps).

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
- About 12 fps in the heaviest Training scenes measured so far (outdoors, Training 1).
- Presentation copies each frame from guest memory once per Flip, with no frames kept in flight.
