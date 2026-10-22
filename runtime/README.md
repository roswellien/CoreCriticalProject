# Runtime bootstrap

Current integration direction: [faithful modernization](../docs/faithful-modernization-plan.md).
Reuse this memory library and the bounded MFC receiver state in `mw34_runtime`,
plus the separate execution components under `tools/m4-runtime/`, in one native
host. The bootstrap limits below describe the memory component, not absence of
later project components. A complete game runtime remains open.

`mw34_runtime` is a C++20 library containing checked backing storage for a 32-bit
guest address space and bounded MFC application receiver state. This is project-authored infrastructure, not an x86
interpreter or a translation of MechWarrior 3.

## Implemented memory contract

- `mw34::GuestAddress` occupies four bytes and has explicit wrapping addition.
  It has no conversion to a native pointer. A guest pointer in a serialized
  structure must remain a 32-bit field; load it with `load<uint32_t>` and wrap it
  in `GuestAddress` before access.
- `GuestMemory::map` creates owned, zero-initialized storage for an exact address
  range. It rejects empty, overlapping, and wrapping ranges. Mapping the final
  byte at `0xffffffff` works. Address zero is unmapped unless explicitly mapped.
- Loads and stores accept unsigned scalar types of up to eight bytes and encode
  little-endian bytes explicitly. Unaligned accesses work without relying on
  host alignment, aliasing, or byte order. Signed, floating-point, and structure
  layouts need explicit serialization and evidence-backed guest layout rules.
- Read and write permissions are enforced. Failed nonempty writes validate the
  entire transfer first and leave storage unchanged. Empty transfers are no-ops.
- `protect` and `unmap` require the exact beginning of a mapping. The execute bit
  is retained as metadata; this library has no instruction execution or indirect
  call dispatcher, so setting execute never makes host memory executable.
- Guest arithmetic and host access bounds are separate: `wrapping_add` wraps,
  while a transfer whose extent crosses `2^32` fails with `MemoryFault`.

## Current limits

Each access must fit entirely within one mapping, including when two mappings
are adjacent. Cross-mapping x86 accesses will need explicit support before
loading realistic images; the current helper fails loudly instead of silently
changing behavior. Mappings use independent byte vectors and an ordered lookup,
not a reserved contiguous 4 GiB host address range. Large mappings allocate real
backing storage and may throw a host allocation exception.

The memory container itself supplies no PE loader, allocator, stack setup, ABI bridge, threading model,
exception translation, or x87/MMX/SSE state. The memory container is not thread
safe. Its C++ exceptions are harness diagnostics, not emulation of Windows
structured exceptions. No memory is exposed as a persistent raw host pointer.
Map/protect/unmap errors use standard C++ argument errors; memory accesses use
`MemoryFault` with a reason enum.

`tests/runtime_tests.cpp` verifies serialization, unaligned access, the top of
the 32-bit address space, mapping overlap, permission failures, unmapped access,
and failed writes preserving existing bytes. These tests use synthetic data.

## Planned function replacement boundary

Once a controlled function establishes the translated ABI, build an explicit
registry keyed by the original guest entry address (`uint32_t`). Each entry
should contain the default generated function and an optional project-authored
replacement with the same agreed host signature. A dispatcher selects the
replacement when present, otherwise the default. Register replacements with a
version/hash-bound target and documented evidence, and reject duplicates and
unknown targets. An unresolved indirect target must stop with diagnostics.

Translated guest function pointers and vtable/jump-table entries remain guest
addresses in memory. Translate them through that registry; never cast a guest
integer to a native function pointer. The controlled execution experiment must
first establish register/flags state, guest stack arguments and cleanup,
return values, callback re-entry, and floating-point state requirements. This
boundary is the original bootstrap proposal. Later dispatch/ABI experiments live
under `tools/m4-runtime/` and have separately scoped evidence; the complete
application integration is not implemented by this memory component.
