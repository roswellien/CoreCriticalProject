# Alpha performance regression investigation

The large slowdown comes from the development build of the original CPU
geometry producer. Disabling the projection bypass did not restore that
producer's production optimization recipe. It remained in the alpha package.
The measured compiler-recipe difference is about4.13ms/frame, enough to explain
the earlier3.99ms/frame alpha-versus-normal gap.

## Controlled results

Same RX9070/Ryzen7 9700X,1800-frame IA movement/yaw route and settings as the
[launcher comparison](gpu-launcher-performance-comparison-2026-10-15.md):
3440x1440,FXAA,AF16,800distance, original fog repair, current models/HUD/music.
Measure1000 warm intervals per run, frames801–1800, with no capture readbacks
or investigation tracing. The three causal controls below each have two runs.

| Control | Mean frame time | Average FPS |
| --- | ---: | ---: |
| Same alpha host; slower CPU recipe; experimental gate removed | 11.431ms | 87.48 |
| Same alpha host; original optimized CPU object restored | 7.299ms | 137.01 |
| GPU scenery host without the projection experiment | 7.296ms | 137.07 |

The earlier published alpha measured11.285ms/88.61FPS; normal measured
7.292ms/137.14FPS. A fresh normal control measured7.209ms/138.72FPS.
The small differences between the fast controls are within run variability;
they do not establish a new GPU scenery speedup.

The restored-object control changes exactly one of37,201 object-list entries.
Its C++ host source is byte-identical to published alpha: it retains the memory
observers, original GPU scenery shaders, fast binding, world counters and geometry
profiling. The original CPU projection bypass remains off. The no-gate control
uses the identical host and the slower compilation recipe without injecting the
experimental gate. It stays slow. This isolates the producer compilation recipe
as the dominant cause; removing the hook alone does not fix the slowdown.

Both repeats of the restored-object and experiment-free GPU controls execute
the same134,755 GPU scenery draws and build435 resident geometries. All seven
isolation runs reach1800frames and have identical scene/virtual-clock sequences,
script and copied registry bytes. Both causal object controls use the same
staged executable path. The initial normal reference used a different staging
basename; it is a corroborating reference, not the causal object comparison.

## Why the CPU routine became slower

The affected original routine is `sub_53F2E0`, which still performs required
CPU geometry, lighting/color, clipping/culling and callback work. GPU scenery
submission does not authorize removing all those effects.

The projection experiment rebuilt its object with x87 merging and O2, but
omitted the retained production cleanup/strict-FP lowering, flat-memory lowering
and additional optimization passes. In particular, the experiment's memory
observer was intended to see out-of-line memory bridges. Retained production
objects instead contain direct guest-memory access; that observation mismatch
is documented in the [bypass test](gpu-projection-bypass-test-2026-10-15.md).

Linker-symbol inspection confirms the resulting code difference:

| Original geometry object | File bytes | Memory bridge imports | FP exception bridge imports |
| --- | ---: | ---: | ---: |
| Retained optimized original | 128,130 | 0 | 0 |
| Published experimental producer | 485,679 | 9 | 2 |
| Slower recipe, original IR without gate | 484,414 | 9 | 2 |

These are object-file sizes and import inventories, not executed instruction
counts. The live controls establish their performance effect. Individual
compiler passes, memory bridges and FP bridges were not separately timed.

The alpha was packaged with that slower object after the bypass was disabled.
The fix is to keep the already optimized original producer in interactive
GPU builds and retain the unfinished removal experiment in a separate private
host. It does not require lowering quality, removing fog, increasing the
simulation clock, disabling GPU scenery or weakening a safety admission rule.

## Corrected package

The corrected GPU host restores the complete optimized original object list
and removes the inactive projection-removal experiment from the interactive
host. Shader, replacement-model, Mech Lab, zoom, marker and fog-repair sources
match the previous alpha. GPU scenery and fast binding remain enabled.

A separate matched full-profile1000-frame comparison against the published
alpha has identical original draw counts/hashes on every frame. Target captures
600/900 and the logical framebuffer readback1000 are byte-identical. These
correctness runs are separate from the seven timing runs.

Corrected executable SHA256:
`e2110c19e7ef69ee89e906a9d2cb1a010c3166a88ed6ed43e6890e91acc91b1c`.
Source/build: `local/remaster/gpu-native-perf-clean-r1/`.

The focused original-compatible Training check also matches all116 retained
framebuffers over1150frames. The alpha launcher now selects this corrected
executable with GPU scenery/fast binding, stock800distance and the original fog
repair retained. Normal Remaster remains unchanged. Timing receipts were frozen
before publication; `publication.json` records the update and validation.

## Evidence and scope

`local/gpu-regression-isolation-r1/` retains frozen executables, object/source
checks, import inventories, private builds, run metadata and analysis/results.
`object-contracts.json` pins each object. `results.json` pins the timing runs.
The controls reuse the retained original IR without modifying original source
or object trees. Repeated tests use protected private save/settings copies.

The execution boundary remains original optimized CPU producers plus the
existing GPU scenery handoff. This repair grants no new CPU-work-removal credit.
Native strict acceptance
remains131/144. Whole-campaign correctness, replacement-model fog and the
historical intermittent divergence remain separate issues.
