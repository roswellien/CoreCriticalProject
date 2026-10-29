# Big Lake Instant Action: virtual surface arena exhaustion

The October 19 player run `20261019-061824-687` exited with a typed
"Virtual surface arena exhausted" fault at service VA 0x380028F0 and address
0xEFFCA000. It used the photo/water repair build, SHA-256
`112f4308525f969de216a24129deeac4e231c4b53af1b04270f9d48162d208f4`.
The session reached 60,589 presented frames, with live mech draws before the
later scene load failed. This is separate from the earlier photo-mode marker
and composition defects.

## Cause and repair boundary

The virtual DirectDraw provider allocates surface pixel pages monotonically.
Final COM release retires the surface identity, but previously left its pixel
mapping allocated. Moving between scenes can therefore exhaust the address
arena even when many older surfaces have been released. A fresh Big Lake run
can succeed while a later load in a longer session fails.

The provider now collects retired pixel mappings under allocation pressure and
reuses their pages through a checked free list. Adjacent retired ranges coalesce;
best-fit allocation splits a larger range. COM identities are never recycled.
Collection protects interfaces with live references, provider device targets and
textures, queued draws, resident targets, locked pixels and transitive attached
surfaces. Retired surface records lose their pixel address and cannot be looked
up as usable surfaces. Mapping, permissions and content initialization still use
the existing guest-memory implementation. The arena limits are unchanged; a
genuinely unsatisfied request still fails visibly.

Source integration is available through
`tools/remaster-launcher/apply_surface_page_pool.py`. It installs the free-list
header and narrowly replaces the allocation/retirement block in a composed
private host. Other rendering, photo, material and model work is preserved.

## Checks and limits

- Native C++ free-list checks cover coalescing, splitting, best fit, overlap and
  overflow rejection, plus 100,000 reuse cycles.
- A focused fixture compiles the actual production collector/allocation functions
  with memory/COM test doubles. It checks released-page reuse, live references,
  retained references, locks, device textures/targets, queued draws, resident
  buffers, transitive attachments, exhaustion and overflow.
- The rebuilt native host launches Big Lake Instant Action through its original
  menus and completes a bounded 2,600-frame run with current materials/models.
- A separate private pressure build churns 1,022 real virtual-surface
  Create/Release provider calls before scene loading. With the allocation cursor
  at 0xF0000000, production collection retires 1,024 surfaces and reclaims
  2,144,518,144 bytes. Loading and rendering then complete 2,600 Vulkan frames.
  All draw triples match the normal native control. The private stress hook is
  absent from the installed source.
- The exact preceding player actions from the 60,589-frame session were not
  replayed. The pressure test establishes the exhausted-arena recovery path,
  not a complete long-duration or whole-campaign stability claim.

The Material Normal Preview profile/source snapshot is the installation lane;
the separate standard launcher is not promoted. Evidence, build identities,
source pins and screenshots are indexed in
`reports/surface-lifetime-fix-20261019/verification.json`, on the Games-drive
report archive. The preceding photo/water repairs, normal strengths, all model
registrations and replay-video default remain intact. Formal acceptance stays
131/144; no commit, push, original media publication or native-game credit is
made by these focused tests.

The installed release SHA-256 is
`a94144c0d8e0967e87c9835da424204274e817ba830049c8bc0591cef7c763d6`.
A final 2,600-frame Big Lake repeat using that release matches both earlier
native draw streams. The profile/source pins and launcher check pass. Restart
with `Play MW3 - Material Normal Preview.cmd` to use this build.
