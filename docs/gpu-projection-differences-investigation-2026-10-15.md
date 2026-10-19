# Projection bypass differences and their effects

Follow-up to the [observed projection test](gpu-projection-watch-test-2026-10-15.md).
The first failed run remains retained. Its exact cause is **unresolved**; no
renderer fix or performance improvement is claimed by this investigation.
Both playable launchers remain unchanged and strict acceptance stays 131/144.

## Differences separated by meaning

| Observation | Cause established by evidence | Effect |
| --- | --- | --- |
| Original TL draw-byte hashes differ from first admission, frame 324. | The bypass deliberately leaves the first n−1 screen X/Y/depth values unwritten. The original callback copies those depth values into RHW. | Expected scratch-buffer differences. The admitted Vulkan world path reads raw positions plus current color/fog/UV, rather than these omitted coordinates. These hashes alone cannot test rendered equivalence. |
| The failed run's semantic hash first differs at frame 282, with zero admissions in both runs. | This precedes any skipped CPU iteration. The hash includes device snapshots and texture bindings in addition to original geometry bytes; the exact differing field was not retained in that run. | Establishes a difference before bypass activation, so the failed comparison cannot isolate a regression caused by omitted projection. Whether this early difference causes the later divergence is unproven. |
| Failed-run original draw counts first differ at frame 489: 893 reference versus 897 bypass. Gameplay images differ substantially. | Exact cause not established. Subsequent byte-identical rendering repeats contradict a consistently failing projection-loop transformation. | A meaningful difference in original producer/view behavior, beyond shader rasterization. The frame-600 HUD also displays different speed/distance. Do not infer changes to AI, damage, saves or collision from these captures. |
| Diagnostic register offset 2280 and input-buffer guest addresses vary between matching replays. | Guest allocation addresses can differ; traced keyboard data and timestamps remain identical. | These particular address differences coexist with equal rendering and are not evidence of a movement defect. |

## Reproduction and isolation

Six additional runs use the frozen asset/settings/input set, stock 800-unit range,
3440×1440, FXAA and 16× AF. All match the original reference's per-frame rendering
semantic records and original draw counts over their tested spans:

- A 600-frame reference/bypass diagnostic pair: byte-identical frame-324 and
  native frame-600 captures, 35,846 omitted iterations observed in the bypass.
- An 1,800-frame diagnostic bypass: all six retained captures byte-identical,
  67,659 admitted/consumed draws and 179,499 omitted iterations/depth-copy reads.
- An 1,800-frame bypass with extra draw diagnostics disabled: the same six
  captures and all 1,800 semantic records match, with the same omission counts.
  Thus the diagnostic helper's clearing of FP exceptions is not required for
  the matching result.
- A second 600-frame pair with service tracing and complete FP restoration:
  byte-identical captures and rendering records; matching live projection
  operands, device snapshots, color/fog/UV bytes and scripted keyboard payloads
  and virtual timestamps. Detailed draw records cover frames 282, 324 and 489.

Executable SHA-256 identities, names and individual comparisons are retained in
`local/gpu-projection-watch-r1/difference-investigation.json`. These are private
correctness experiments, not timing measurements or acceptance credit.

Read-only downstream inspection finds the token attaches immutable raw geometry
before scene conversion. Widescreen adaptation uses the model branch; the world
shader ignores the omitted TL coordinates. No stale-coordinate-driven geometry
selection was identified there. No dirty-read or pending-token guard fails in
these completed runs.

## Floating-point checks expanded

The earlier fixture used only power-of-two depths/numerators. That left arbitrary
division and mixed exact/inexact prefixes untested. The authored fixture now
adds arbitrary scenery-like operands and an inexact prefix followed by an exact
last corner, and compares MXCSR as well as complete State, x87 status and allowed
memory outputs. The production optimized watched and unwatched variants each
pass **1,152** cases; the watched variant observes **119,808** writes.

Separate private fixtures also pass 1,008 arbitrary-input cases, 1,300 captured
live-State/control-word replays and 1,008 mixed-prefix cases. They compare MXCSR
too. No FP mismatch was found. These bounded results do not prove every future
polygon or callback path.

The gate's use of owner-based State/token access remains a formal alias-contract
issue for further hardening; the fixtures do not exercise the complete C++ gate.
It has not been demonstrated to cause the historical failure.

## Replay inputs still requiring attribution

Static original-code inspection identifies real desktop data that can enter a
virtual-clock replay: message timestamps/positions, native timers and keyboard
modifier queries outside scripted DirectInput. Original MFC copies message
time/position into its message context; original MW3's `0x51AC2A` keyboard-state
query feeds `ToAscii` at `0x51AC42`. These are actual input contracts, not proof
that they caused this failure.

The traced pair receives physical Windows messages during startup/menu operation,
but still renders identically. Neither run calls the traced keyboard-modifier
services through frame 600, and scripted keyboard event bytes/times match. Do not
assign the failed run to physical keyboard input, timers, or clock drift without
a trace showing that causal difference. Its earlier run did not retain those
details, so the precise initialization difference cannot be recovered from its
hashes alone.

The next useful evidence is a recurrent failure with detailed state/binding and
service records before frame 282 and at the first movement divergence. Preserve
the initial failure alongside matching repeats; do not replace it with a success
claim. No CPU-removal promotion or speedup measurement is performed here.
