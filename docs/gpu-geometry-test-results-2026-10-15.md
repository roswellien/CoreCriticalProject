# First live GPU geometry comparison

Stage 1 of the [development plan](gpu-geometry-development-plan.md) is complete:
the isolated test is built, exercised and retained. It compares the existing
replacement-model CPU projection and resident GPU paths. No world geometry
migration, lighting, normal mapping or shadow feature was added in this stage.

## Result

On the matched Instant Action route, GPU model geometry reduced average
presentation interval from **16.10 ms to 12.07 ms**, about **25.0% less frame
time** (1.33× inverse-mean throughput). This is evidence for the existing model
handoff, not a predicted speedup for terrain or the whole engine. The current
Play profile already enables GPU models, so this test delivers no new production
FPS gain by itself.

| Case, in execution order | Mean presentation ms | Median ms | P95 ms | Host replacement emission ms/frame |
| --- | ---: | ---: | ---: | ---: |
| CPU A | 16.138 | 16.051 | 18.466 | 1.348 |
| GPU A | 13.002 | 11.929 | 19.952 | 0.054 |
| GPU B | 11.148 | 11.014 | 13.191 | 0.043 |
| CPU B | 16.069 | 15.980 | 18.881 | 1.353 |

Each measured frame submits 165,774 replacement input vertices. The CPU control
generates 5,304,768 bytes of replacement screen-space vertices per frame. The GPU
case queues those vertices from persistent buffers, with zero CPU replacement
vertex payload in the measured interval. Its 62 geometry uploads total
5,304,768 bytes, with no further model uploads during frames800–1600. This does
not mean all frame traffic or all original CPU geometry calculations disappear.

## Configuration and correctness

- AMD Ryzen7 9700X, Radeon RX9070; 3440×1440, FXAA, AF16, 1600-unit scenery,
  current local texture pack and seven model bindings. Actual scene includes the
  Madcat player and nearby replacement geometry. Model assets/settings/input
  identities are recorded in the private comparison JSON.
- One frozen development executable, SHA256
  `18e4529838326119656e5f358c8022f0e8ca2c10e1f54236f983ac8e17f45c5c`,
  based on the published Mech Lab canvas build. Only opt-in geometry profiling
  was added. The same37,201 translated object entries are retained.
- Four1600-frame timing runs in CPU/GPU/GPU/CPU order, measuring frames800–1600
  after warm-up. All samples in that interval are retained. Separate1050-frame
  capture runs avoid screenshot stalls in performance statistics.
- Every original draw count/hash record matches across all timing runs and
  corresponding capture prefixes. Original scene counts and virtual-clock
  sequences also match. This is a deterministic fixed-clock rendering test,
  not a real-time simulation/FPS-independence test.
- Captured frame1000 differs in **19 of4,953,600 pixels**, with maximum channel
  difference9. Visual review finds matching scene/composition, consistent with
  existing GPU-float versus CPU-double edge/shading differences; not bit-identical.
- Profiling-disabled original-compatible Training: **116/116 CPU PPMs** match
  the retained r17 baseline. Six authored analyzer controls pass, including
  rejection of menu-only, missing-frame, no-GPU-execution and early-fault cases.
- Each live run ends with its deliberate presentation-budget exception (exit1),
  not normal quit. Private save/registry protection checks pass. Play launcher
  bytes remain unchanged. No whole-mission or strict acceptance credit;131/144.

## Interpretation and next boundary

The repeated GPU means are lower, but the first GPU run has a worse P95 than
the CPU controls. Presentation includes game execution, GPU/driver, desktop/FIFO
pacing and profiling overhead. These are not dedicated GPU timestamps; neither
steady GPU utilization nor a uniform improvement in latency tails is established.
The selected original0x51FB30 timing scope is not a complete engine CPU profile.

No CPU near-plane fallback batches occurred during the measured interval, so
that branch needs its own future coverage. This route also does not cover LOD
transitions, controlled destruction, off-camera shadow casters or terrain
normals. The original render producers continue running in both cases.

The next implementation boundary is **original opaque building/terrain asset →
retained host mesh + instance → GPU vertex shader**, with identical visual
settings first. Recover positions/normals/UV/material ownership and pre-cull
visibility before removing any original CPU work. Dynamic lights and normal
maps follow that shared geometry/material contract; shadows additionally need
casters outside the player's view.

Private evidence: `local/gpu-geometry-test-r1/comparison.json`, `closure.json`,
`source-pins.json`, `runs/geometry-r1-*`, `geometry-comparison.png`, and
`local/mechlab-canvas-r1/runs/geometry-profile-disabled-TrainingCpu`.
Reproduction/tooling: [geometry test instructions](../tools/remaster-launcher/GEOMETRY_TEST.md).
