# Native geometry and call-routing investigation

This follows the [precompiled performance update](precompiled-performance-updates-2026-10-22.md).
The October 23 successor improves controlled warmed Training throughput by 4.7%
and 1% lows by 5.5%, with unchanged captured output. The development launcher
selects the signed runtime, and a precompiled `.mw3update` is published. No
original geometry or lighting producer has been removed.

## Confirmed before and after

Primary comparison: the same executable with the routing flag off/on/on/off,
two 2,800-frame visible runs per condition. This isolates the enabled shortcut
from compiler/layout changes. Warm window is frames 1200–2699, 3,000 intervals
per condition. Profiling and image readbacks are disabled for timing.

| Warm Training metric | Off | On |
| --- | ---: | ---: |
| Presented FPS | 89.55 | 93.79 |
| 1% low FPS | 43.58 | 46.00 |
| High FPS | 198.97 | 199.12 |
| Mean interval | 11.17 ms | 10.66 ms |
| Worst interval | 26.51 ms | 24.02 ms |

Both enabled repeats are faster than both disabled repeats. High FPS is
effectively unchanged. Across frames 400–2699, including first-use work,
averages are 80.72 → 85.09 FPS and 1% lows 35.96 → 37.62 FPS; remaining hitches
are not eliminated. Conditions: Ryzen 7 9700X, Radeon RX 9070, 3440×1440, FXAA,
AF16, draw 1600/fog 1100, full existing lighting/shadows, replay/monitor off.
Real host presentation intervals measure performance; the diagnostic guest
clock is fixed at 16.666667 ms. Interactive simulation timing is unchanged.

The earlier different-build ABBA gives 86.83 → 94.38 FPS and 40.67 → 47.96 FPS
for 1% lows. Its baseline repeats vary more (83.59 and 90.33 FPS); retain those
results but use the same-build comparison above for the claimed gain. The
original disabled control is retained too. These are development-system Training
results, not campaign/combat or other-machine guarantees.

## Why this boundary

The prior [terrain perspective experiment](terrain-cpu-removal-2026-10-17.md)
already measured its admitted mesh subset at about 0.23 ms/frame and found no
net benefit from the narrow projection bypass. Repeating that bypass would not
address the broader Training bottleneck.

The current resident-world bridge still executes the original mesh routine.
However, a geometry call includes host adapters and nested callbacks, not just
vertex arithmetic. An earlier diagnostic's 13,368 samples include 689 leaves
inside the photo/replay, aiming and remaster wrapper chain (5.15%). Those are
historical samples, and include handled calls that this candidate cannot skip.
They are not a forecast of its performance gain. One current 2,800-frame run
records 208,452,548 translated body entries, including startup/loading.

## Private implementation

`apply_geometry_breakdown.py` instruments a fresh current host. Exclusive nested
timers separate original mesh bodies with/without an active retained-world scope,
material lighting at 0x545720, adaptive lighting subdivision at 0x547740,
fog at 0x555A70, matrix work at 0x51FB30, body 0x51DFA0,
API work, draw capture, world binding, sun/effect capture, scene building and
shadow work. It reuses the deeper native sampler and correlates the last
published guest PC while the main thread is suspended. That PC is not an
instruction-exact timing measurement. Original producers are unchanged, and
the translated module is reused without rebuilding it.

`apply_body_dispatch.py` prepares a separate candidate for native call routing.
All CALL/RET/SEH validation and HUD interception in `enter()` remain in front
of this route. The four complete adapter bodies are pinned and reviewed for
target-guarded effects. All 73 handled targets retain the full original adapter
chain. Other targets call their original translated body directly after an
initial ordinary call traverses the adapters to retain lazy launch-setting
initialization and validation failures. No original game body is omitted.

The candidate is opt-in with `MW34_BODY_DISPATCH=1`; disabled mode remains
available for an unchanged-code control. Adapter changes invalidate the source
contract and require another review before applying the patch. The source
patch checks all contracts before writing.

## Larger producer boundary found

Independent retained-IR/original-byte inspection identifies 0x547740 as a
special light-driven polygon subdivision path. It inverse-projects existing TL
coordinates through 0x523590, tests nearby light/object influence, refines
triangles through 0x547160 for up to six passes, then projects the generated
vertices through 0x523540 and emits callbacks. Its successful return suppresses
the ordinary mesh callback. These are static code observations, not proof that
every scene executes every branch.

The saved Training stack profile contains 1,801/13,368 samples with this routine
in the captured stack (13.47%, inclusive). Of these, 1,264 have 0x57EA20 as the
closest original routine. Its own native instructions are the sample leaf in
only 137 cases. Thus timing only its arithmetic would miss much of the downstream
submission work. The 16-frame stack limit can omit ancestors; these counts are
neither exact wall time nor draw frequency, and predate the latest optimizations.

The earlier projection omission must continue excluding this path: subdivision
numerically consumes the supposedly redundant TL coordinates. Capturing its
final emitted triangles can establish ownership but saves no earlier refinement
work by itself. Removing that work requires preserving the inverse projection,
light selection, adaptive refinement, interpolation, lighting and callback queue
contracts. Sending only the coarse original polygon changes tessellation and
could change fog/UV interpolation, reconstructed normals or fallback lighting.
Its equivalence is unproven. No such bypass has been added.

Frozen-shader inspection identifies a more specific opportunity: resident sun-world
draws neutralize legacy diffuse RGB and zero specular RGB; textured lit TL
receivers also neutralize those channels. The TL sky and untextured branches,
and the fallback world shader, preserve diffuse RGB. Alpha remains observable.
The subdivision split decisions found in the retained code depend on geometry,
light distance/range and edges, rather than RGB error. Legacy RGB calculation
may therefore be redundant for a much larger authenticated lit subset.

This does not authorize zeroing all CPU colors. The transparent flush at
0x57E110 compares the first full diffuse DWORD against 0xFF000000 and can change
the texture color operation based on RGB. Other geometry, fog, UV interpolation,
normal reconstruction, CPU-state and fallback contracts still apply. Initially
exclude that transparent queue, sky, untextured and fallback draws. The current
candidate only changes call routing; it skips none of these calculations.

The downstream 0x57EA20 callback can submit immediately or fill original tagged
and transparent queues; their order and limits remain required. REA's current
Ghidra analysis decompiles this callback, but does not identify procedures at
0x57D690/0x57CE20. Those negative results are retained; the latter routines are
inspected through existing lifts/original-byte disassembly instead of assigning
them guessed Ghidra function bodies. REA evidence ID:
`ev_a57b56f0df9ab61788032686247ce2513ba15ee8d48f9b7845cfde6fc36c5eaa`.

The fresh exclusive/inclusive CPU timers confirm that 0x547740 averages 9.07
calls/frame and 2.63 ms/frame inclusive of downstream work; its exclusive body
time is 0.49 ms. Its associated 0x57EA20 path averages 829.98 callbacks/frame,
with 0.32 ms exclusive and 1.41 ms inclusive. Inclusive times overlap and must
not be added. Mesh bodies with an active retained-world scope total only
0.20 ms/frame inclusive. The instrumented frame averages about 13.00 ms and
has measurement overhead; do not substitute it for the uninstrumented timings.
This identifies the next larger boundary without claiming all 2.63 ms is
removable or that every subdivision draw is eligible for RGB-work removal.

## Checks and measurement status

Both private hosts compile and link against the unchanged translated module.
The authored routing fixture passes 2,097,672 membership checks, including
unaligned addresses and unsigned boundary cases. Profiling checks exercise
nested exception unwinding and preservation of FP control/status, MXCSR and
Win32 error state. Both source patches reproduce their private snapshots and
reject duplicate application and changed source contracts before writes.

Private evidence roots are `D:/MW3GeometryBreakdown-20261022-r1` and
`D:/MW3BodyDispatch-20261022-r1`. The serialized investigation completed after
the model/cinematic jobs finished. No other worker was stopped or modified.
The later same-build comparison ran while those jobs were also idle.

Separate baseline/candidate runs match all 2,800 complete draw records and
seven full-resolution images byte for byte. The instrumented host independently
matches those records and images. All non-timing world-counter rows match across
both sets of four timing runs. Every bounded run reaches 2,800 Vulkan swapchain
presentations and the intentional budget exit 1; this is not normal quit or
mission completion. Source-patch reproduction and rejection checks, all 12
prepared-pack fixtures and the complete launcher fixtures pass.

## Delivery

[Download the October 23 performance update](https://playtest.corecritical.dev/updates/mw3-performance-20261023-r1/MW3PerformanceUpdate.zip).
Extract it and import the `.mw3update` through Settings & Steam → Game Updates,
keeping the matching payload ZIP beside it. Launcher 1.0.24 or newer is required.
Both Setup catalogs list it; the prior update remains available. No feed or
launcher self-update is enabled.

Signed native host SHA-256:
`3aae1c6eb38fe299904823f082754f1339628e2ef6dbf338f8a935bc63aed5c0`.
Signing records the exact tested unsigned host `ae2ed758…`; the translated
module remains `6d6e3c25…`. The runtime enables only `MW34_BODY_DISPATCH=1` in
addition to selecting the new host. Exact reviewed host admissions retain their
predecessors and add this hash only where the predecessor was admitted.

The signed update verifies originals, copies 649 precompiled runtime files,
validates, activates and rolls back successfully in an isolated installed
baseline. The first trial had no bundled baseline for rollback; that test setup
failure is retained, and the corrected installed-baseline trial passes. Local
Python byte caches found beside the predecessor were excluded from delivery;
the preliminary archive remains private. Full R2 readbacks of every published
artifact and both catalogs match local bytes. Sequence is 2026102302.

The development profile now selects this signed runtime with matching source
metadata, unchanged graphics/other preferences and the same translated module.
Portable runtime integrity remains enforced by the signed update/file pins;
development source-snapshot verification remains enabled. Testers do not
regenerate native game code. Formal acceptance remains 131/144; nothing committed.
