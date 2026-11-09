# Heap

How the game allocates and frees memory. It doesn't call the C runtime's
`malloc` and `free` directly for C++ objects: `new` and `delete` in the game
go through two import thunks into `MFC42.DLL`, whose `operator new` and
`operator delete` call `MSVCRT.dll`'s `malloc` and `free` in turn.

Profile `mw3-us-1-2-retail`, image SHA-256
`95bc2c114c9b2e5c5ada8e40ca78cc79470f862e45313ffad0d1e8e6d4d916bf`. Studied
2026-11-04 in Ghidra 12.1.3 with the default analysis. Addresses are virtual
addresses at image base `0x400000`; RVAs are the address minus `0x400000`. To
repeat the work, import that `Mech3.exe` into Ghidra and go to each address; the
[README](README.md) has the details and the section format. Every import slot
named here is checked against
[`../imports-mw3-us-1-2-retail.csv`](../imports-mw3-us-1-2-retail.csv).

Both imports are by number only, so the import CSV gives no name. The number
is mapped to a name by the export list for `mfc42.dll` that ships with Ghidra
12.1.3, `Ghidra/Features/Base/data/symbols/win32/mfc42.exports`, which gives
each export's ordinal and its decorated C++ name.

## sub_005ABD1A

**Name and confidence:** `operator_delete`, confirmed.

**Kind:** import thunk.

**Extent:** `005ABD1A` to `005ABD1F`, 6 bytes.

**Callers:** Ghidra lists 1,307 functions that call it, and 1,634 call sites
in all, some of them in code it hasn't marked as a function. For example
`0058AEC0` and `004BF910` (see [`objects.md`](objects.md)) call it to free a
vector's old buffer after copying it into a bigger one, passing the old
buffer's address as the one stack argument and removing it themselves
afterwards.

**What it does:** one jump through the import slot at RVA `0x1BB4C8`. There
are no branches.

**Reads and writes:** the import slot.

**How the host reaches it:** `tools/m4-crt-heap-carry/host/composition.cpp`
routes calls to it to the heap stage (`heap_stage.hpp`), which lists it among
the helpers it runs for the initializer roots 14 and 15 and maps the slot to
`MFC42.DLL`'s export. The heap-carry
[README](../../../../tools/m4-crt-heap-carry/README.md) ("Roots 14..15") says
the MFC42 routine behind it frees through `MSVCRT.dll`'s `free`. Context only,
not proof.

**Why this name:** the import-thunk rule. The import CSV lists slot RVA
`0x1BB4C8` as `MFC42.DLL` ordinal 825, imported by number. Ghidra's
`mfc42.exports` maps ordinal 825 to `??3@YAXPAX@Z`, the decorated name of
`operator delete(void *)`. As a C identifier that is `operator_delete`. Its
callers pass one pointer and use no result, which fits.

**Still unknown:** nothing.

## sub_005ABD26

**Name and confidence:** `operator_new`, confirmed.

**Kind:** import thunk.

**Extent:** `005ABD26` to `005ABD2B`, 6 bytes.

**Callers:** Ghidra lists 446 functions that call it, and 839 call sites in
all, some of them in code it hasn't marked as a function. For example
`0058AEC0` calls it with 12 to get a list node and with 4 to get a one-slot
buffer, and `004BF910` calls it with a slot count times 4 when it grows a
vector; each passes the size as the one stack argument, removes it afterwards
and uses the returned pointer.

**What it does:** one jump through the import slot at RVA `0x1BB4BC`. There
are no branches.

**Reads and writes:** the import slot.

**How the host reaches it:** `composition.cpp` routes calls to it to the heap
stage, whose initializer path runs it for the main initializer table's roots.
The heap-carry [README](../../../../tools/m4-crt-heap-carry/README.md) ("Main
initializer table") says the MFC42 routine behind it allocates through
`MSVCRT.dll`'s `malloc`. Context only, not proof.

**Why this name:** the import-thunk rule. The import CSV lists slot RVA
`0x1BB4BC` as `MFC42.DLL` ordinal 823, imported by number. Ghidra's
`mfc42.exports` maps ordinal 823 to `??2@YAPAXI@Z`, the decorated name of
`operator new(unsigned int)`. As a C identifier that is `operator_new`. Its
callers pass one size and use the returned pointer, which fits.

**Still unknown:** nothing.
