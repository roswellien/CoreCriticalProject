# Startup

The Microsoft C runtime startup that Windows runs first in `Mech3.exe`. It sets
up the runtime, runs the program's initializers and hands over to MFC's
`WinMain` at `005AE390`, which passes its arguments on to `AfxWinMain` in
`MFC42.DLL` (ordinal 1576, import slot RVA `0x1BB438`). It also covers the
runtime's `atexit` and `_onexit`, which the program's initializers use to
register the functions that destroy global objects at exit. This is library code
linked into every Visual C++ 6 GUI program that uses `MSVCRT.dll`, not the
game's own code, though `005AC5C0`'s one-instruction body is most likely
shared with some of the game's own empty functions.

Profile `mw3-us-1-2-retail`, image SHA-256
`95bc2c114c9b2e5c5ada8e40ca78cc79470f862e45313ffad0d1e8e6d4d916bf`. Studied
2026-11-04 in Ghidra 12.1.3 with the default analysis. Addresses are virtual
addresses at image base `0x400000`; RVAs are the address minus `0x400000`. To
repeat the work, import that `Mech3.exe` into Ghidra and go to each address; the
[README](README.md) has the details and the section format. Every import slot
named here is checked against
[`../imports-mw3-us-1-2-retail.csv`](../imports-mw3-us-1-2-retail.csv).

## sub_005AC110

**Name and confidence:** `_onexit`, confirmed.

**Kind:** statically linked Microsoft C runtime: `_onexit` from Visual C++ 6's
`atonexit.c`, built for programs that use `MSVCRT.dll`. Its name is also the
name of the `MSVCRT.dll` routine it calls; that import has no thunk of its own
and no row in the table.

**Extent:** `005AC110` to `005AC13F`, 48 bytes.

**Callers:** one function, [`005AC140`](#sub_005ac140), from `005AC145`.

**What it does:** takes one stack argument, a pointer to a function to run at
exit, and returns a pointer: that function on success, 0 on failure.

1. If the word at `009A17F0` is -1, it calls `MSVCRT.dll`'s `_onexit` through
   the import slot at RVA `0x1BB52C` with the argument, removes the argument
   and returns that call's result.
2. Otherwise it calls [`005AC580`](#sub_005ac580) (`__dllonexit`) with the
   argument, the address `009A17F0` and the address `009A17EC`, removes the
   three arguments and returns that call's result.

The caller removes its own argument. `__dllonexit` takes the function, then
pointers to the table's start and end, so `009A17F0` is the start
(`__onexitbegin` in `atonexit.c`) and `009A17EC` the end (`__onexitend`).
[`005AC3A0`](#sub_005ac3a0) sets both to -1 before any initializer runs, so in
this program step 1 always runs and the second branch is never taken.

**Reads and writes:** reads the word at `009A17F0` and the two import slots;
the called routine updates whichever exit-function table it uses.

**How the host reaches it:** `tools/m4-crt-heap-carry/host/composition.cpp`
routes calls to it to the heap stage (`heap_stage.hpp`), whose initializer
path runs it when a main-table root registers its exit function. The heap-carry
[README](../../../../tools/m4-crt-heap-carry/README.md) ("Main initializer
table") describes the same chain: `atexit`, then the game's `_onexit`, then
`MSVCRT.dll`'s `_onexit`. Context only, not proof.

**Why this name:** the library-code rule. `atonexit.c`'s `_onexit` checks
whether `__onexitbegin` is -1; if it is, the program uses the runtime DLL's
exit table and it passes the function to the DLL's `_onexit`; otherwise it
calls `__dllonexit(func, &__onexitbegin, &__onexitend)`. The two branches
above match, in order and with the same arguments. Its one caller is `atexit`,
as in `atonexit.c`.

**Still unknown:** nothing.

## sub_005AC140

**Name and confidence:** `atexit`, confirmed.

**Kind:** statically linked Microsoft C runtime: `atexit` from Visual C++ 6's
`atonexit.c`.

**Extent:** `005AC140` to `005AC154`, 21 bytes.

**Callers:** Ghidra lists 116 functions that call it, and 125 call sites in
all, three of them in code it hasn't marked as a function. They include the
exit-registration stub of every root in the main initializer table (for
example `00410000` and `00410050`; see [`globals.md`](globals.md)), each of
which passes it a small function that runs one global object's destructor and
then removes the argument.

**What it does:** passes its one stack argument, a function pointer, to
[`005AC110`](#sub_005ac110) (`_onexit`) and removes it. It returns 0 if that
call returned a non-zero pointer and -1 if it returned 0, using a branch-free
sequence of negate, subtract-with-borrow, negate and decrement. There are no
other steps.

**Reads and writes:** only its stack.

**How the host reaches it:** `composition.cpp` routes calls to it to the heap
stage, whose initializer path runs it for each main-table root; the heap-carry
[README](../../../../tools/m4-crt-heap-carry/README.md) records the exit-table
entries those calls leave. Context only, not proof.

**Why this name:** the library-code rule. `atonexit.c`'s `atexit` returns 0
when `_onexit(func)` succeeds and -1 when it returns null, which is exactly
the result above. Its callers pass a function and nothing else; the
initializer roots use it to register their objects' destructors, which is
how Visual C++ 6 destroys global objects at exit.

**Still unknown:** nothing.

## sub_005AC3A0

**Name and confidence:** `WinMainCRTStartup`, confirmed.

**Kind:** statically linked Microsoft C runtime: the GUI startup routine from
Visual C++ 6's `crtexe.c`, built for programs that use `MSVCRT.dll`.

**Extent:** `005AC3A0` to `005AC54D`, 430 bytes. Ghidra's function body leaves
out the two exception blocks at `005AC502` to `005AC523`, which sit inside this
range; counting them, the routine is one piece.

**Callers:** none. It is the program's entry point: the PE header's
`AddressOfEntryPoint` is RVA `0x1AC3A0`, so Windows starts the process here.

**What it does,** in order:

1. Builds a structured exception frame whose handler is `_except_handler3`
   (thunk `005AC586`, slot RVA `0x1BB528`) and whose scope table at `005D0F78`
   names a filter at `005AC502` and a handler at `005AC517`.
2. Calls `__set_app_type` (slot `0x1BB5A4`) with 2, which marks a GUI program.
3. Sets the two words at `009A17EC` and `009A17F0` to -1: the end and start of
   the program's own exit-function table, left empty because `MSVCRT.dll` keeps
   the real one ([`005AC110`](#sub_005ac110) shows which is which).
4. Copies the program's `_fmode` (`007365A0`) and `_commode` (`0073659C`) into
   the runtime's copies, through `__p__fmode` (slot `0x1BB57C`) and
   `__p__commode` (slot `0x1BB504`).
5. Copies the runtime's `_adjust_fdiv` (slot `0x1BB508`) into `009A17E4`.
6. Calls `005AC5C0` from `005AC415`, where `crtexe.c` calls `_setargv`. See
   [`sub_005AC5C0`](#sub_005ac5c0).
7. If the word at `009A17E8` is zero, passes the program's `_matherr` at
   `0051E7B0` to `__setusermatherr` (slot `0x1BB50C`). That word is the flag
   `crtexe.c` uses to say the default math error handler is in use. Ghidra's
   default analysis doesn't mark `0051E7B0` as a function, since it is only
   reached through this pointer; it reads an `_exception` record, as a
   `_matherr` does.
8. Calls `005AC5A0` from `005AC431`. See [`sub_005AC5A0`](#sub_005ac5a0).
9. Runs the C initializer table `005E0248` to `005E024C` through `005AC598`,
   called from `005AC440`.
10. Calls `__getmainargs` (slot `0x1BB514`) with the new-handler mode from
    `00736598` and the wildcard flag from `00736594`, which fills in the
    argument count, argument list and environment.
11. Runs the C++ initializer table `005E0000` to `005E0244` through `005AC598`,
    called from `005AC47B`. This runs the constructors of the program's global
    objects.
12. Reads the command line from `_acmdln` (slot `0x1BB518`) and skips the
    program name: through the closing quote if it starts with a quote, otherwise
    up to the first character at or below a space. It then skips the spaces
    after it.
13. Calls `GetStartupInfoA` (slot `0x1BB170`). If the `STARTF_USESHOWWINDOW`
    flag is set, it takes the show-window value from it; otherwise it uses 10
    (`SW_SHOWDEFAULT`).
14. Calls `005AE390` (`WinMain`) with `GetModuleHandleA(NULL)` (slot
    `0x1BB16C`), 0 for the previous instance, the rest of the command line and
    the show-window value.
15. Passes `WinMain`'s result to `exit` (slot `0x1BB5C0`), which doesn't
    return.

If code under this frame raises an exception, the filter at `005AC502` saves
the exception code and asks `_XcptFilter` (thunk `005AC592`, slot `0x1BB51C`)
what to do. If it says to handle it, the handler at `005AC517` restores the
stack and calls `_exit` (slot `0x1BB520`) with that code.

**Reads and writes:** the globals and import slots named in the steps, and
its own stack frame.

**How the host reaches it:** `tools/m4-crt-heap-carry/host/composition.cpp`
starts the program by running it, and its `direct()` checks each direct call
it makes to `005AC5C0`, `005AC5A0` and `005AC598` against the expected call
site and return address. Context only, not proof.

**Why this name:** the library-code rule. Each of the steps above matches, in
order, the GUI path of `WinMainCRTStartup` in Visual C++ 6's `crtexe.c`,
including the `__except` path through `_XcptFilter` and `_exit`, and every call
it makes goes to the runtime routine `crtexe.c` names at that point. Nothing
else calls it, as expected for an entry point.

**Still unknown:** nothing about the name. What the two initializer tables run
is outside this routine.

## sub_005AC580

**Name and confidence:** `__dllonexit`, confirmed.

**Kind:** import thunk.

**Extent:** `005AC580` to `005AC585`, 6 bytes.

**Callers:** one function, [`005AC110`](#sub_005ac110), from `005AC137`, on
its branch for a program that keeps its own exit-function table. That branch
never runs in this program.

**What it does:** one jump through the import slot at RVA `0x1BB530`. The
imported routine adds a function to the exit-function table whose start and
end pointers it is given.

**Reads and writes:** the import slot.

**How the host reaches it:** `composition.cpp` routes calls to it to the heap
stage. Context only, not proof.

**Why this name:** the import-thunk rule. The import CSV lists slot RVA
`0x1BB530` as `MSVCRT.dll` `__dllonexit`, imported by name.

**Still unknown:** nothing.

## sub_005AC598

**Name and confidence:** `_initterm`, confirmed.

**Kind:** import thunk.

**Extent:** `005AC598` to `005AC59D`, 6 bytes.

**Callers:** one function, [`005AC3A0`](#sub_005ac3a0), twice: from `005AC440`
for the C initializers and from `005AC47B` for the C++ initializers.

**What it does:** one jump through the import slot at RVA `0x1BB510`. The
imported routine calls, in order, every non-null function pointer between its
two arguments.

**Reads and writes:** the import slot.

**How the host reaches it:**
`tools/m4-crt-heap-carry/host/initterm_context.hpp` and `initterm_binding.inc`
run it, and `composition.cpp`'s `direct()` checks both calls to it. Context
only, not proof.

**Why this name:** the import-thunk rule. The import CSV lists slot RVA
`0x1BB510` as `MSVCRT.dll` `_initterm`, imported by name.

**Still unknown:** nothing.

## sub_005AC5A0

**Name and confidence:** `_setdefaultprecision`, confirmed.

**Kind:** statically linked Microsoft C runtime.

**Extent:** `005AC5A0` to `005AC5B2`, 19 bytes.

**Callers:** one function, [`005AC3A0`](#sub_005ac3a0), from `005AC431`.

**What it does:** calls `005AC5D6`, a jump through the `_controlfp` import slot
(RVA `0x1BB578`), with the new value `0x10000` and the mask `0x30000`, then
removes the two arguments and returns. Those are the runtime's `_PC_53` and
`_MCW_PC`: set the x87 FPU's precision control to 53 bits and change nothing
else. There are no branches.

**Reads and writes:** the import slot; the call changes the x87 control word.

**How the host reaches it:** `tools/m4-crt-heap-carry/host/control_context.hpp`
runs it and checks that its call passes `0x10000` and `0x30000`;
`composition.cpp`'s `direct()` checks the call from startup. Context only, not
proof.

**Why this name:** the library-code rule. The runtime's `_setdefaultprecision`
is exactly one call to `_controlfp(_PC_53, _MCW_PC)`, and `crtexe.c` calls it
at this point in startup, right after setting up the math error handler.

**Still unknown:** nothing.

## sub_005AC5C0

**Name and confidence:** `Stub_Return`, confirmed.

**Kind:** a merged body that stands for several functions.

**Extent:** `005AC5C0`, 1 byte.

**Callers:** Ghidra lists 57 functions that refer to it. 53 reach it
directly: 48 call it, for example `005AC3A0` (from `005AC415`), `0040E4B0` and
`00414F40`, and 5 end by jumping to it: `004D4C70`, which adjusts the object
pointer first, `004E6240`, which stores a table pointer in the object and then
adjusts it, and three exception cleanup blocks the compiler made (at
`005B5220`, `005B5240` and `005B6C50`). The other 4 use its address:
`004F7630` and `004F7650` set the function pointers at `005EA510` and
`005EA514` and put it there when given none (both pointers also start out
holding it), `004F5910` calls through those two pointers, and `00579F50` takes
its address too. Ghidra also finds 8 call sites in code it hasn't marked as a
function: 7 calls (at `0044D7E7`, `0044DA75`, `004542DE`, `00454321`,
`0045726B`, `004737D4` and `004D4765`) and one jump at `004D8D23`, which
adjusts the object pointer first. Data tables from `005BCC94` onward also point
at it (likely empty slots in virtual-function tables).

**What it does:** returns at once. Its only instruction is `RET`. There are no
branches, reads or writes.

**Reads and writes:** none.

**How the host reaches it:** `composition.cpp` registers it as a translated
leaf and runs it through its leaf adapter, and its `direct()` checks the call
from startup at `005AC415`. Context only, not proof.

**Why this name:** the merged-body rule in the [README](README.md): its whole
behaviour is one instruction, so it is fully described. Startup calls it where
`crtexe.c` calls `_setargv`, whose default version is empty, so Microsoft's
empty `_setargv` is one of the functions merged into it. The other callers are
unrelated, so the linker most likely folded several identical empty functions
into this one body. No single official name
fits them all, so it gets an `Area_Action` name that says what it does. The
section gives a few examples instead of all 57 functions, because the one
instruction already settles what every caller gets.

**Still unknown:** which empty functions, other than `_setargv`, were merged
into it.
