# Live native rendering: surface command recovery

Strategy update, 2026-10-11: this graphics lane supplies contracts and diagnostic
evidence to the [faithful modernization plan](../faithful-modernization-plan.md).
Its original-process transport and capture replay stages remain separately
labelled; the production target is live commands from recompiled game producers.
Existing implementation ownership and recorded scopes below are preserved.

Updated 2026-10-11. First close observed frame semantics, then moving-frame
resource persistence, live x86-game-to-x64-Vulkan transport, and finally connect
recompiled game producers. The current work is the first step.

Current compiled validation: `reports/graphics-trace/20261011-172341-666`
contains a successful `/W4 /WX` Release build/selftest. `surface-controls.json`
checks ten authored API observations, one exact CPU pixel change, 19 malformed
observation controls, six unsupported depth-command profiles and four unsupported
CPU-command profiles. GPU verification at
`reports/vulkan-probe/observer-surface-commands-20261011-r2/verification.json`
passes four D16/D32 and 1x/3x cases, 80 exact pixels and zero validation messages.
It proves clear/draw/copy order, unchanged pixel preservation and depth retention
for the authored fixture. It does not establish live-frame equivalence.

The earlier 1,272-draw flip-interval replay retains HUD omissions and world/depth
differences. Its comparison is diagnostic, not complete-frame equivalence. The
existing observer excluded Z-buffer caps from surface discovery.

The updated graphics tracer observes `DDSCAPS_ZBUFFER` through the existing
DirectDraw4 creation, attached-surface and Surface4 QueryInterface paths. Its
Surface4 hooks now forward Lock/Unlock and GetDC/ReleaseDC, preserving provider
results. Observer snapshot locks are excluded through a thread-local scope.
The observed D16 zero-depth fill is recorded only for the actual attached
depth object, exact DEPTHFILL flag and bounded rectangles. Successful full-target
RGB565 WAIT locks have snapshots at Lock return and just before Unlock; unchanged
draw/scene counters and the same thread/owner are required across that span.
Unsupported locks, GDI access and other transfers still refuse capture.

For the selected presentation interval, `surface-operations.jsonl` records
pre-call destination/source descriptors, raw rectangles/effects, API flags and
coordinates, followed by the actual HRESULT and bounded successful Lock/GetDC
outputs. It continues to the next Flip even after payload capture refuses an
unsupported operation. Its limit is 4,096 API observations. Missing footer,
changed thread/surface, failed closing flip or logging failure prevents a closed
interval claim. The additive `surface-pixels/writes.jsonl` and content-addressed
payloads retain the observed write-capable RGB565 spans. Unobserved interface
aliases, other rendering commands and a moving sequence remain open.

`inspect_surface_operations.py` decodes the pinned Win32 SDK layouts and reports
depth-fill requests without granting renderer coverage. `check_surface_operations.py`
checks the actual authored fixture log and 19 malformed/overstated controls.
Fixtures exercise depth-only discovery, successful/failed access forwarding,
retained failed output cells, exact depth-fill effects and exclusion of a real
snapshot through cloned Lock/Unlock slots. The verifier and packager retain
surface command order against draw ordinals. SCN4 clears carry the observed
zero depth; CPU writes become row-span opaque copies of changed pixels only.
These snapshots are renderer-transfer inputs, not proof of recompiled HUD
producers. No final-frame image is used as a rendered output seed.

Use a separate build directory while another tracer is loaded:

```powershell
./tools/graphics-trace/build.ps1 -BuildDirectory build/graphics-trace-depth-observer-r2 -Launch -CapturePresentation -CaptureSkipFlips 300
python tools/graphics-trace/inspect_surface_operations.py reports/graphics-trace/<run>/surface-operations.jsonl
python tools/graphics-trace/inspect_cpu_surface_writes.py reports/graphics-trace/<run>/surface-pixels
```

The first instrumented session is `reports/graphics-trace/20261011-171109-106`,
game PID 43496, with passive monitor
`reports/mw3-monitor/20261011-171114-94895a6f`. Its frozen tool/source snapshots
precede subsequent fixture descriptor flag and menu-timeline fixes. The user
confirmed Training, movement/turning/firing and normal quit. The hash-bound
draw/provider verification and passive monitor pass, with exit code 0, zero
alerts and zero dropped segments. `live-verification.json`,
`surface-inspection.json` and `user-training-confirmation.json` retain those
distinct scopes. Its payload capture refused at the first depth fill and is
not replayable.

The closed surface interval observed two successful DEPTHFILL requests on a
640x480 D16 depth surface, both with fill value zero: rectangles
`[0,0,640,480]` and `[530,370,605,470]`. Between/after them are two successful
full RGB565 backbuffer WAIT Lock/Unlock pairs. The first revision retained API
parameters but no pixel snapshots or draw counters. Actual changed pixels and
precise placement against draws require the next capture; HUD attribution is a
working inference, not recovered CPU instructions.

That session exhausted the old 2,048-entry presentation timeline on menu-only
operations before any 3D scenes. The new source skips menu records until a
successful scene has completed. The original session and its frozen DLL are retained.
Selected interval capture and its independent surface diagnostic log use their
own budgets. Do not claim the older timeline gate passed for this session.

Next: extend capture to consecutive flips with persistent resources and compare
each moving frame against its own original target. Full native startup and live
native gameplay remain separate integration work.

The second Training session was launched after the user's confirmation:
`reports/graphics-trace/20261011-184016-446`, PID 40144, with passive monitor
`reports/mw3-monitor/20261011-184023-55cc6870`. Current authored controls pass
against this build's actual fixture export. The prior 1,272-draw diagnostic still packages with SCN3
SHA256 `5b485c6408dd20ce28b408168520a9cd54edec9243f0d4947e2b45f8f68aa7fc`;
the existing six diagnostic rejection controls also passed regression.

## Second genuine interval and same-frame comparison

The second capture closes five scene intervals and 1,082 draws, two D16 zero-depth
fills and two full RGB565 Lock/Unlock spans. The first span changes no pixels.
The second changes 8,486 pixels, mapped to 2,077 horizontal copy regions.
`capture-verification.json`, `surface-inspection.json` and
`cpu-write-inspection.json` retain the bounded observation gates. The draw/provider
identity gate also passes. The general trace reaches its 1,024-record limit;
it does not supply unlimited session-wide API/error coverage.

The user confirmed normal Training, movement/turning/firing and quit. Passive
monitoring records exit code 0 and zero dropped segments. One unresponsive-window
warning at 18:40:57 Denver time was followed by `window_responsive_again` at
18:41:38. The existing strict no-alert monitor gate remains unpassed. The
corrected `monitor-summary-r2.json` and original raw monitor events retain this;
the earlier summary omitted the recovery because it selected the wrong event
name. This does not invalidate the separate captured-frame/image comparison.

The ordered Vulkan replay and a deliberately draw-only baseline use the exact
same capture, reference target, executable, shaders, 0.5 pixel offset, D32 depth,
RGBA8 target and 1x size. Source copies, command packages, payload hashes, GPU
images and comparisons are retained separately in:

- `reports/vulkan-probe/present-surface-comparison-20261011-r2/`
- `reports/vulkan-probe/present-surface-draws-only-20261011-r2/`
- `reports/vulkan-probe/surface-command-paired-comparison-20261011/`

| Measurement | Draw-only baseline | Ordered surface commands |
| --- | ---: | ---: |
| Pixels within eight levels in every RGB channel | 260,672 / 307,200 (84.85%) | 304,161 / 307,200 (99.01%) |
| Pixels exceeding that tolerance | 46,528 | 3,039 |
| Mean absolute channel error | 5.8565 | 2.0344 |
| Exactly equal pixels | 51,695 | 41,620 |

Large pixel errors fall by 93.47%. Exact equality does not improve: the corrected
depth/rendering path changes more retained pixels, and substantial small channel
differences remain. Both GPU replays complete with zero Vulkan validation
messages. The updated image visibly restores HUD elements absent from the
draw-only replay; remaining world/HUD differences and all unobserved aliases
still need investigation. This is one diagnostic frame, not complete command
closure, a moving sequence or a playable native renderer.

![Original, draw-only replay, and ordered-command replay](../../reports/vulkan-probe/surface-command-paired-comparison-20261011/comparison.png)
