# Native startup after the opening video

2026-10-16. Fixed the reported crash after the opening video and installed the
repaired host in Play MW3Remaster. Selected executable:
`local/remaster/gpu-native-heap-isolation-r1/build/entry_commandline.exe`
SHA256 `110c0ae83f7954074a0e99743f2e1f47fb855692ae07c66666eea631e7857519`.

The final build retains all 15 model registrations (14 MW5 chassis plus the
detailed Strider), 29 close/distance bindings, 39 cumulative texture banks,
3440x1440, FXAA, AF16, 1200 scenery/1100 fog, current HUD and local music.
The parked STL Avatar stays excluded. Latest photo/replay source changes remain;
the original translated object list is unchanged (37,201 objects).

## Fault and cause

Both actual failed launches, `local/remaster/runs/20261016-204224-454` and
`20261016-204251-863`, report a guest read fault at PC 0x00489c93, target
0x385f8bac, on the all-model host 8bf6e08e. A copied-current-pilot reproduction
with ordinary scripted DirectInput Escape reproduces the same call chain.
Native fault disassembly identifies the actual failing table read at original
0x00489d19; the reported PC is the last published continuation.

The menu's constructor calls back into campaign selection before assigning the
campaign-list index fields at context offsets 0x16f9c/0x16fa0/0x16fa4. With the
larger launch environment, the packed allocator places this object over recently
freed video-codec data. The codec's separate HeapCreate handle and the main CRT
incorrectly shared both free blocks and the remaining tail of the current region.
No replacement geometry had loaded when this fault occurred.

The retained diagnostic shows a codec allocation at 0x503443e0 of size 0x1d1e8,
its release, then the CRT menu allocation at 0x50346aa0 of size 0x17730 overlapping
that codec-owned region. The early menu callback reads nonzero residual values
and calculates an out-of-range table address. Source instructions and faulting
native instruction were inspected locally, using LLVM 21.1.8.

## Code and integration

- Authored `tools/remaster-launcher/native-overrides/heap_partitions.hpp` keeps
  immutable heap ownership on mapped regions. Allocation searches only that
  heap's free list entries and parks a different heap's unused region tail.
  Same-heap reuse, requested sizes, 16-byte alignment and explicit zero flags
  remain. Overflow/exhaustion return allocation failure.
- `apply_heap_partitions.py` connects CRT imports to the CRT token, codec/private
  HeapCreate imports to their actual handle, and service-owned allocations to
  their own pool. It rejects cross-heap CRT frees/resizes. CRT HeapDestroy ends
  only the CRT's live blocks instead of clearing every heap's metadata.
- Photo/replay captures and restores region ownership and the correct allocation
  tail limit. The experimental file format is MW3RPLY2; ambiguous older files
  reject instead of being restored without ownership. Existing mapped-region
  ownership is retained when rewinding within the same session.
- The independent photo/replay build selected during this investigation still
  contained only the older 13 mesh/LOD bindings despite its launcher advertising
  15 chassis. The live Black Hawk test caught this before publication. Merged the
  seven validated all-model adapter files and donor-header include into that
  newer host; its renderer/photo changes remain. The failed 13-binding test stays.
- `play_remaster.py` now supports an enabled source-snapshot identity/model-list
  check. The installed profile enables it, tying the selected executable and
  advertised chassis to matching publication metadata. Older unguarded profiles
  remain compatible; the new selected profile is checked on both launchers.

No campaign fields are seeded, no index is clamped, no blanket allocation clearing
is added, and no host environment variables are hidden from the guest. The
original movie decoder, constructor/callback instructions and gameplay remain.

## Validation and actual execution

The final merged executable above passes:

- Current copied pilot/settings, all model bindings, ordinary video skip at
  frame 48, and an additional 8,192-character environment variable: 180 native
  presentations through the video-to-menu transition without the fault.
- Complete unskipped 2,737-frame IV50 movie, real clock and empty input script:
  3,000 presentations through the Vulkan swapchain and stable original main
  menu. The native framebuffer capture after the video was visually inspected.
- All 29 mesh/LOD and current texture sidecars load. Black Hawk renders with
  positive GPU batches in a bounded 1,800-frame Instant Action case at the full
  selected graphics profile. This catches the stale seven-chassis host above.
- Original-compatible Training CPU images 116/116 identical, original mode-7
  GPU draw records 1150/1150 identical, IA CPU images 116/116 identical against
  the preserved turret-aim host. Actual 3D gameplay was reached in each case.
- Actual allocator helper: 2,034 checks, zero failures. Covers the decoded-pixel
  reuse case across heaps, same-heap stale bytes, zero flags, coalescing, isolated
  destruction, overflow/OOM, alignment and non-overlap across alternating heaps.
- Existing photo/replay math/serialization tests pass against the modified
  private header, extended with ownership round-trip and old-file rejection.
  The private patch recipe reproduces compiled sources; the compiled heap helper
  and formatted repository version differ only by clang-format whitespace.
- Both actual .cmd launcher checks pass with the installed executable and source
  snapshot. Deliberate mismatched executable and chassis metadata reject early.

The gameplay/startup budgets intentionally exit with code 1 and an explicit
presentation-budget message. This is not normal shutdown or mission completion.
Earlier heap-only candidate checks and the failed 13-binding model test are kept
separately; final validation refers to the merged executable above.

## Scope and continuation

Execution advanced from the reproduced video-to-frontend fault to the complete
original opening, live main menu, and native model-rendered IA. Private proofs,
editable build, failed cases and copied state are in
`C:/Users/jcbla/.codex/workspace-storage/MW34Recomp/post-intro-crash-r1`.
Published source pins are beside the installed executable. The previous launcher
is backed up as `local/remaster/launcher.before-heap-isolation-20261016.json`.
Keep the existing C: asset workspace referenced by the model registry as well.

Mapped guest heap reservations remain bounded by the existing 512-MiB arena and
are retained until host shutdown; fragmentation/exhaustion under extended play
has not been measured. The source's early uninitialized read remains unchanged;
this repair restores isolation between independently owned heaps. Full Win32
heap conformance and extended campaign/replay behavior are not established.
Full model damage/debris/LOD/muzzle/performance checks and native normal mapping
remain open. Next work is sustained campaign/model combat testing on this host.

Original pilot/save/registry content was hashed and preserved; tests used copies
and overlays. Protected composer/watcher and other rendering jobs were left
alone. No desktop screenshots, commit, original-code fallback or new acceptance
credit. Strict acceptance remains paused at 131/144.
