# Original menu rollover wave restoration

Date: 2026-10-17. Scope: the enhanced native front end, including the normal-map
integration candidate. Acceptance remains **131/144**.

## Defect and execution boundary

The original button hover handler still triggers an expanding radial distortion.
Its rasterizer, original executable VA `0x558DD0`, modifies the front-end canvas
directly through a scratch buffer. The enhanced compositor recorded image blits
at VA `0x55B3C0`, then reconstructed the menu using enhanced artwork and text.
It omitted the direct pixel distortion. The existing tolerant replay comparison
could still accept these frames; acceptance of that comparison did not prove
that the small rollover animation was represented.

Initial investigation also checked sprite-opacity animation. The captured button
opacity remained unchanged; that hypothesis was rejected. The fix does not change
sprite identity, opacity, button hit testing, animation triggers or game clocks.

The advanced boundary is **live original hover rasterization -> enhanced menu
composition**. The original rasterizer continues to execute. Its real parameters
are recorded in draw order and drive a presentation displacement map. The HD
canvas immediately before the effect supplies the distorted colors; subsequent
button text and other original image operations retain their order. The original
handler controls radius, phase, duration, exit and re-entry behavior.

## Implementation

- [Menu wave mapping](../../runtime/graphics/menu_wave.hpp) preserves the original
  float-bit radius estimate, float lookup precision, truncation and absolute
  coordinate copy gates. Enhanced output interpolates the logical displacement
  field and samples the enhanced canvas rather than substituting a low-resolution
  rectangle for the whole wave.
- The clipped original implementation can leave previously populated scratch
  pixels in place. Those pixels have no current-frame source coordinate. The
  adapter reads their actual post-call original values and retains them locally;
  it does not invent a replacement value or alter scratch-buffer behavior.
- [The host installer](../../tools/remaster-launcher/apply_menu_wave.py) adds the
  ordered operation, its replay comparison, post-call clipped pixel capture and
  the dispatch-bitmap entry. Unknown contexts retain the original presentation
  fallback. The operation is restricted to a 640x480, RGB565 menu canvas with
  matching context; world frames remain outside this path.
- Wave source rendering is restricted to the affected rectangle plus its source
  sampling margin. No additional source replay occurs on idle menu frames.
- [The normal-map integration recipe](../../tools/remaster-launcher/integrate_normal_mapping.py)
  includes the fix and carries menu recording/presentation into the current-main
  candidate while retaining its photo/replay callbacks. Existing real-time menu
  scrolling support is carried across where the merge lacked its hooks.

## Evidence and checks

Original user-supplied executable SHA256:
`95bc2c114c9b2e5c5ada8e40ca78cc79470f862e45313ffad0d1e8e6d4d916bf`.
Addresses above are **VAs**, not RVAs. Static analysis used REA with Ghidra
12.1.4; instruction-level review used the installed LLVM 21.1.8 disassembler.
The owned analysis session was closed with a local snapshot.

Private artifacts are under
`C:/Users/jcbla/MW34SunTests/menu-rollover-r1/`. They include executable and input
identities, primitive/call traces, before/after raster buffers, source comparisons,
protected-original hashes and enhanced frame captures. Original media, generated
code, native executables, analysis extracts and captures remain local.

The C++ displacement implementation matched all 307,200 source pixels in each
of three captured original frames (early and expanding waves). A second route
held Instant Action long enough to reach the left screen edge. Its reconstructible
samples also matched exactly; 44 pixels in the clipped frame required the actual
original scratch-pixel handoff, of which 35 differed from the unmodified canvas.
These are captured native-producer comparisons, not a claim of complete menu
or game acceptance.

The authored CTest `menu_wave` checks logical-resolution sampling, untouched
inner areas, completed-wave cleanup, clipping bounds, malformed period rejection,
constant-color HD interpolation and the clipped-pixel handoff. The focused C++
test builds with project warnings treated as errors. Python syntax checks pass.

A matched before/after hover route disabled only the optional real-time scroll
scaling in both test environments, making background positions deterministic.
All **131 original framebuffer captures** were byte-identical. Enhanced captures
at idle/faded frames 72, 74, 78, 84, 96, 120, 170 and 216 were also identical.
Active-wave differences were restricted to the affected button region, including
the second rollover after moving off and back onto Training. This comparison
does not change the published launcher's real-time scrolling setting.

An initial full-canvas implementation cost about 55.9 ms during the short
rollover. Restricting the additional work to the affected region reduced the
observed median to about 27.8 ms, versus about 23.0 ms in the previous compositor;
idle measurements were about 21.3 and 22.2 ms respectively. These are exploratory
menu measurements with frame dumping, not a controlled gameplay benchmark.

The current-main normal-map candidate additionally completed 1,200-frame Training
and Instant Action routes. Both complete extended draw logs match the preceding
normal-map candidate exactly; full-resolution captures at frames 600 and 900 also
match byte for byte. Each run loaded all 30 model normal-map bindings. The separate
Big Lake host completed its 1,200-frame gameplay smoke run with its own asset
configuration. All bounded runs stopped at the intentional presentation budget;
they do not establish mission completion or normal shutdown.

## Local launcher identities

- Big Lake Sun Tests now selects the separate repaired host at
  `C:/Users/jcbla/MW34SunTests/menu-rollover-r1/fixed-host/build/entry_commandline.exe`,
  SHA256 `202aa9e5389d48b6bcbc116587e7aa70faf76f2757153bf4479fe05591bd8965`.
- Normal Mapping Preview selects the current-main integration at
  `C:/Users/jcbla/MW34SunTests/menu-rollover-r1/normal-host/build/entry_commandline.exe`,
  SHA256 `e3ebbfa0f72934b80165016ee0c6f3b62eb8ac5ed5708ae12ec9925ee9c71e7e`.
  Its profile and source snapshot agree and the launcher check passes.
- Previous executables remain available. Before-update profile/snapshot copies
  are retained under the private rollover evidence directory.

## Remaining scope

This restores an omitted original menu effect. It does not complete game-wide
normal-material coverage, campaign validation, terrain CPU removal, other direct
pixel effect coverage or the full acceptance lane. All existing evidence remains
intact. No commit or push is part of this continuation.
