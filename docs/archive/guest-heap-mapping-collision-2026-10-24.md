# Guest heap / MFC42 address collision

The October 24 08:06 local playtest report stops at `HeapAlloc` service
`0x345c6`, mapping guest address `0x5f3d0000`, while `c3m1` is selected.
The running signed controller-query host is SHA-256
`1feb3c5875e3affe88b6d71cf45748bfa098006b7d1dd771d2686e2fa1b0c034`.

The heap grows upward within `0x50000000..0x70000000`, committing at least
1 MiB at a time. Its failed minimum mapping would extend to `0x5f4d0000`.
MFC42 is already mapped at `0x5f400000..0x5f4ed000`; even the minimum request
therefore overlaps 832 KiB of the required DLL. This is a guest address-space
collision, not evidence of insufficient physical RAM or VRAM. The generic
mapping failure text previously hid the mapper's underlying exception.

## Repair

- `apply_heap_address_space.py` adds an inline read-only gap search to the native
  host's private GuestMemory interface. It searches actual existing mappings,
  uses 64-KiB alignment, observes the arena limit and returns failure when a whole
  allocation cannot fit. It never moves an existing mapping or changes protection.
- Heap allocation commits only a complete free range. Owner isolation, reuse,
  zero-fill semantics and the existing 512-MiB arena bounds remain unchanged.
- Heap containment now checks an actual heap region rather than treating every
  address below the high-water mark as heap. This excludes the skipped DLL/hole
  from the Stage's heap permission shortcut.
- The existing translated fast-gate ABI is unchanged. Its heap limit points to
  the uninterrupted mapped heap prefix; addresses after the first hole fall
  through to the Stage's exact checks. No translated-module rebuild is needed.
- `apply_heap_partitions.py` invokes the repair for subsequent generated hosts;
  the pinned original runtime memory implementation remains unchanged.

Execution boundary advanced: faithful native allocation beyond the MFC42 mapping
without overwriting a required provider or weakening guest memory guards.
No physics, AI, missions, rendering, content packs or controls are changed.
Formal acceptance remains **131/144**.

## Validation and delivery

Evidence and isolated native build: `D:/MW3HeapCollision-20261024-r1`.
Only `heap_partitions.hpp`, `mfc_stage.hpp` and `memory/guest_memory.hpp` differ
from the active controller-query host snapshot. The original translated module
is unchanged. The rebuilt executable has a valid timestamped Windows signature;
signed SHA-256 is
`3cbfab0aa239f29779ce11d3e4de7af6eaecf6a41826da2fc2602111eb869598`.

The real native mapper rejects the failed old range. Seventeen checks cover
the repaired placement, unchanged DLL bytes and read-only protection, multiple
occupied ranges, exact fits, alignment, overflow, exhaustion, commit failure,
heap ownership and reuse. All 2,034 existing partition checks also pass.

An isolated copied-save Training run reaches 500 Vulkan presentations with the
supported controller path and full prepared textures/models. A 2,800-frame
campaign frontend check selects `c3m1` without the mapping fault. The captured
frontend remains at the copied pilot's unallocated-salvage warning; scripted
mission deployment was not completed. These bounded
runs deliberately end with the checked frame-budget marker (exit 1); they do
not establish mission completion or sustained playtest stability. The legacy
controller script attempt stops on its known scripted-data-format limitation
and is retained separately, not counted as a successful game run.

User saves, keyboard/controller profiles and graphics/pack preferences are
preserved. DEV activation changes only native executable/module and matching
source snapshot identities, with a checked previous-profile backup. Public
installer and download-site publication are outside this repair's activation.
