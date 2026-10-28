# M4 reader bridge research — 2026-10-10

This is a static implementation note for work that can proceed independently
of the selected 144-root initializer gate. It does not change initializer
credit, run the original executable, or prove a native startup.

## What the current evidence establishes

The existing host parser in `tools/m4-assets` already handles the reader.zbd
archive footer and 0x94-byte directory records. Its contract deliberately
keeps archive entries and typed ZRD tokens host-owned; it does not model the
game's HANDLE, cursor, registry, or guest allocations. The binary identity and
parser coverage are recorded in `reports/m4-assets/recovery-r2` and
`reports/m4-assets/parser-r1`.

Ghidra analysis of the admitted x86 `MW3/Mech3.exe` shows a concrete guest
object seam:

| Address | Static behavior observed |
| --- | --- |
| `0x557320` | Allocates a 0x18-byte reader object, initializes it, opens the supplied path, registers the object on success, and destroys/frees it on failure. |
| `0x5764E0` | Initializes object fields: path `+0x00`, file handle `+0x04` (invalid sentinel `-1`), dirty flag `+0x08`, entry count `+0x0C`, capacity `+0x10`, and entry-table pointer `+0x14`. |
| `0x576520` | Opens the path read-only with `CreateFileA`, sharing read access; on success loads the directory and duplicates the path. Its failure branch obtains/formats the Win32 error and frees the format buffer. |
| `0x5767B0` | Reads the final eight bytes, requires version `1`, obtains the entry count, loads `count * 0x94` bytes from immediately before the footer, and seeks back to file offset zero. |
| `0x576690` | Grows the entry table using `realloc`, doubling capacity or sizing to the requested entry count. |
| `0x576A80` | Performs `_stricmp` lookup against each 64-byte entry name and returns its zero-based index or `-1`. |
| `0x576AE0` | Validates an entry index, returns the record's payload byte count when requested, seeks to its payload offset, and returns the file handle. |
| `0x576650`, `0x576720`, `0x5766D0`, `0x576500` | Dirty objects write the directory, version, and count; cleanup closes the handle and frees owned table/path allocations. The outer destructor then frees the 0x18-byte object. |

The archive record layout in the existing host parser is: payload offset at
`+0x00`, payload byte count at `+0x04`, 64-byte name at `+0x08`, an opaque
DWORD at `+0x48`, and 72 opaque metadata bytes at `+0x4C`. These observations
are static Ghidra results cross-checked against the bounded host format parser;
they are not runtime traces of the original reader.

## Next implementation slice

Build a separately testable guest-facing reader adapter that preserves the
original x86 object layout and Win32 return/error conventions while using the
verified host archive storage underneath. Keep host pointers and handles
outside guest memory; expose only 32-bit guest addresses/handles through the
existing runtime boundary. Start with object initialization, open, lookup,
payload seek/read, and close, and compare their return values, cursor changes,
owned allocations, and failure behavior against the x86 routines.

Before connecting it to startup, resolve the remaining boundary details:

- registry ownership and exact lifetime at the `0x557320` callers;
- the actual read/copy wrapper and how callers consume `0x576AE0`'s returned
  handle and byte count;
- partial `ReadFile`/`WriteFile`, allocation failure, oversized count, and
  malformed footer behavior, since several original helper return values are
  not checked in the decompiled path;
- mutation/write semantics for dirty archives, which are outside the initial
  read-only startup path and should not be silently treated as immutable;
- guest address ownership and cleanup through the runtime memory bridge.

This reader work can advance before all 144 initializers are accepted, but
window creation still depends on the full initializer table, CRT environment,
provider state, localization/configuration, this reader boundary, and the
frame/application contracts. Passing this reader slice alone does not earn
initializer credit or establish menu readiness.
