# Performance bottleneck evaluation (2026-10-23)

This is an independent, read-only evaluation of where frame time goes in the
current native host, written as a starting point for implementation work. It
reanalyses evidence that has already been retained. No code was changed, nothing
was built or run, and no benchmark was repeated. Formal acceptance remains
**131/144**. Each recommendation below preserves the guest ABI, floating-point
behaviour, initialization effects, validation and visual fidelity.

**Evidence labels**

- **Measured:** derived directly from retained files.
- **Inference:** follows from source plus measurements, but nothing tested it directly.
- **Hypothesis:** unmeasured.

## 1. What actually runs

| Item | Value |
| --- | --- |
| Launcher profile | `local/remaster/launcher.json` |
| Selected executable | `D:\MW3StriderRepair-20261023-r1\entry_commandline.exe` |
| Executable SHA-256 | `f173dc789fbaeb1cc416074bfc628ba2604538c4655732834f7676f264d85b17` |
| Source snapshot | `D:\MW3StriderRepair-20261023-r1\source-snapshot.json` (verification enabled) |
| Host source | `D:\MW3StriderRepair-20261023-r1\host-source\` (delta from the Avatar repair: `mesh_override_stage.inc`) |
| Translated module | unchanged, `6d6e3c25…` |
| Graphics | 3440x1440, FXAA, AF16, draw distance 1600, fog distance 1100, fullscreen windowed |
| Relevant flags | `MW34_BODY_DISPATCH=1`, `MW34_LAZY_RT=1`, `MW34_GPU_HUD/MODELS/WORLD/TERRAIN=1`, `MW34_TL_COMBINE=1`, `MW34_FIXTURE_SHADOWS=1`, `MW34_FIXTURE_SHADOW_SIZE=256`, `MW34_SUN_SHADOWS=0`, `MW34_EFFECT_LIGHT_LIMIT=64`, `MW34_TEXTURE_STAGING=1`, `MW34_PIPELINE_WARMUP=1`; `MW34_VSYNC` unset |
| Not selected | Render-state reuse candidate `D:\MW3RenderStateReuse-20261023-r1` (host `3f3b6652…`) |

Unless stated otherwise, every source reference below is relative to
`D:\MW3StriderRepair-20261023-r1\host-source\`. The per-category CPU profile
comes from the instrumented host in `D:\MW3GeometryBreakdown-20261022-r1`. That
host is older than body dispatch and render-state reuse, so read its absolute
values as relative weights.

## 2. Diagnosis

### 2.1 The warmed window contains two different workloads (measured)

The scene count per frame is deterministic: it is identical in every retained
run because the guest clock is fixed. It splits the warmed window, frames
1200–2699, into two phases:

| Phase | Frames | Scenes/frame | Character |
| --- | --- | --- | --- |
| Heavy | 1200–1844 (645 frames) | 8 or 9 | Near fixture lights |
| Light | 1845–2699 (855 frames) | 7 or 10 | Away from fixture lights |

Mean presentation interval per phase in each retained timing run. A
"one-period" frame is shorter than 10.4 ms, about 1.5 × 6.94 ms.

| Evidence | Run | Heavy mean (ms) | Heavy one-period | Light mean (ms) | Light one-period |
| --- | --- | ---: | ---: | ---: | ---: |
| RenderStateReuse | state-off-a | 14.581 | 0.05 | 7.220 | 0.98 |
| RenderStateReuse | state-off-b | 13.946 | 0.08 | 7.021 | 1.00 |
| RenderStateReuse | state-on-a | 13.770 | 0.10 | 7.020 | 1.00 |
| RenderStateReuse | state-on-b | 14.073 | 0.10 | 7.064 | 1.00 |
| RenderStateReuse | confirm-off-a | 14.445 | 0.06 | 7.018 | 1.00 |
| RenderStateReuse | confirm-off-b | 14.985 | 0.02 | 7.081 | 0.99 |
| RenderStateReuse | confirm-on-a | 14.300 | 0.05 | 7.047 | 0.99 |
| RenderStateReuse | confirm-on-b | 14.638 | 0.03 | 7.060 | 0.99 |
| ShadowClip | clip-off-a | 14.066 | 0.10 | 7.109 | 0.99 |
| ShadowClip | clip-off-b | 14.320 | 0.07 | 7.027 | 1.00 |
| ShadowClip | clip-on-a | 14.571 | 0.08 | 7.025 | 1.00 |
| ShadowClip | clip-on-b | 14.382 | 0.03 | 7.174 | 0.99 |
| ShadowSubmission | submit-off-a | 14.028 | 0.08 | 7.054 | 0.99 |
| ShadowSubmission | submit-off-b | 13.801 | 0.10 | 7.033 | 1.00 |
| ShadowSubmission | submit-on-a | 13.818 | 0.06 | 7.053 | 0.99 |
| ShadowSubmission | submit-on-b | 13.286 | 0.10 | 7.042 | 1.00 |
| GeometryBreakdown | baseline-a | 17.916 | 0.00 | 7.472 | 0.94 |
| GeometryBreakdown | baseline-b | 16.181 | 0.00 | 7.214 | 0.97 |
| GeometryBreakdown | flag-off-a | 16.303 | 0.00 | 7.333 | 0.96 |
| GeometryBreakdown | flag-off-b | 16.305 | 0.00 | 7.251 | 0.97 |
| GeometryBreakdown | flag-on-a | 15.404 | 0.01 | 7.148 | 0.97 |
| GeometryBreakdown | flag-on-b | 15.233 | 0.01 | 7.152 | 0.98 |

**What the table shows:**

- **The light phase is pinned at the display cap.** In every run it sits at about
  6.94–7.2 ms, which corresponds to roughly 144 Hz. The refresh rate is inferred:
  the timing runs use FIFO presentation because `MW34_VSYNC` is unset
  (`vk_scene.hpp:3263-3286`). No optimization can register in this phase.
- **Every measured improvement came from the heavy phase.** Those 645 frames hold
  about 60% of the window's time. Whole-window FPS therefore dilutes gains by
  about 40%.
- **Heavy-phase intervals vary continuously.** Examples are consecutive frames at
  10.2–11.9 ms, and the earlier 4-scene segment holding at 11.6 ms. They are not
  multiples of the display period, so they most likely reflect true frame cost.
  Whether the display is variable or fixed refresh is unknown (open item M1).

**Heavy-phase means by experiment**, average of each condition's runs:

| Experiment | Off (ms) | On (ms) | Change (ms) | Outcome |
| --- | ---: | ---: | ---: | --- |
| Render-state reuse (all 8 runs) | 14.49 | 14.20 | −0.29 | retained |
| Shadow submission reuse | 13.92 | 13.55 | −0.36 | rejected |
| Shadow clip corner reuse | 14.19 | 14.48 | +0.28 | rejected |

Run-to-run spread is about 0.5 ms, so none of these is conclusive. The submission
experiment helped the phase that matters as much as the retained candidate did. It
was rejected on whole-window 1% lows.

### 2.2 The heavy phase multiplies CPU-transformed (TL) draws (measured)

Per-frame averages from `confirm-on-a/world.jsonl` (cumulative counters
differenced) and the breakdown profile:

| Per frame | Heavy | Light |
| --- | ---: | ---: |
| Sun-lit TL draws | 2,539 | 474 |
| Resident world draws | 43 | 73 |
| Sun model draws | 6.6 | 26.9 |
| Captured draws | 2,938 | 958 |
| Light subdivision 0x547740 calls | 18.3 | 2.1 |
| 0x57EA20 callbacks | 1,853 | 58 |
| Geometry adapter calls | 19,561 | 2,370 |

The heavy phase is not model-heavy. The original light-driven polygon subdivision
multiplies TL triangles near lights, and every host cost that scales per TL draw
grows with it.

### 2.3 Fixture shadows are about a quarter of the heavy frame (measured)

These are exclusive CPU milliseconds per frame from
`MW3GeometryBreakdown-20261022-r1/verify-diagnostic/geometry.csv`, split by phase.
The instrumented frame is 18.74 ms in the heavy phase and 7.47 ms in the light
phase.

| Category | Heavy | Light | Heavy calls/frame |
| --- | ---: | ---: | ---: |
| shadow_record | 2.721 | 0.092 | 8.3 |
| other | 2.124 | 1.790 | – |
| renderer (includes scene fence waits) | 1.517 | 1.196 | 9.3 |
| host_api | 1.433 | 1.082 | 6,041 |
| geometry_adapter | 1.338 | 0.293 | 19,561 |
| mesh_body_other | 1.127 | 0.800 | 191 |
| scene_build | 1.041 | 0.273 | 8.0 |
| light_subdivision_547740 | 1.030 | 0.036 | 18.3 |
| effect_capture | 0.998 | 0.154 | 2,938 |
| shadow_prepare | 0.981 | 0.255 | 8.3 |
| draw_capture | 0.957 | 0.332 | 2,938 |
| sun_capture | 0.903 | 0.221 | 2,938 |
| callback_57d690 | 0.746 | 0.571 | 827 |
| callback_57ea20 | 0.678 | 0.012 | 1,853 |
| body_51dfa0 | 0.655 | 0.021 | 15,226 |
| material_545720 | 0.255 | 0.176 | 1,096 |

**Reading the profile:**

- **Instrumentation overhead.** The heavy phase runs about 57k QPC scopes per
  frame. The instrumented heavy frame is 18.7 ms against an uninstrumented
  15.2–16.3 ms on hosts of the same era. Most of that overhead falls on the
  high-call categories.
- **Fixture shadows.** `shadow_record` plus `shadow_prepare` take about 3.7 ms.
  They run only about 17 scopes per frame, so that figure is nearly
  overhead-free. That is roughly 25% of the heavy frame.
- **Do not add inclusive timings.** They overlap.

### 2.4 Probably CPU-bound, but the GPU is unmeasured (inference)

- **Wait time is small.** Scene-fence waits sit inside `renderer`, at 1.52 ms or
  less. Present-fence and acquire waits fall in `other`, at 2.12 ms or less. The
  rest of the heavy frame is CPU work on the render thread.
- **No GPU timing exists.** The host has no timestamp queries, so GPU busy time,
  including the fixture-shadow atlas passes, is unknown.

## 3. Ranked opportunities

### O1. Fixture-shadow atlas rebuilt for every scene, one caster per TL triangle

**Locations:**

- `vk_scene.hpp:969-970` and `vk_scene.hpp:1264-1266`: `prepare_fixture_shadows`
  and `record_fixture_shadows` run inside every `render()` call.
- `effect_lighting_stage.inc:234-244`: every world scene in the frame receives the
  light uniform.
- `fixture_shadow_stage.inc:95-97`: casters are kept across scenes and into the
  next frame.
- `fixture_shadow_stage.inc:109-114`: each opaque sun-lit TL draw is
  reconstructed vertex by vertex, FNV-hashed and turned into its own caster.
- `fixture_shadow_stage.inc:121-129`: every scene rebuilds and copies the whole
  retained caster vertex set.
- `fixture_shadow_stage.inc:143-160`: for each light, six faces × every caster,
  with an 8-corner × 6-plane matrix test and a separate `vkCmdDraw` per caster.

**Mechanism:**

- **Redrawn per scene.** The atlas is cleared and redrawn with the full
  accumulated caster set once per world scene. The profile shows 8.3 record calls
  per heavy frame (measured). The number that are world scenes is unmeasured.
- **Not merged.** Casters are mostly single subdivided triangles. The main-pass TL
  combining merges 4.33 M of 5.05 M logical draws (`confirm-on-a/stderr.txt`), but
  it does not apply to casters.
- **Likely duplicates (inference).** TL casters are keyed by a hash of floats
  reconstructed from screen space. While the camera moves, previous-frame copies
  probably survive alongside the current ones.

**Evidence:** 3.70 ms of CPU per heavy frame against 0.35 ms per light frame
(measured). The GPU cost is unknown.

**Potential benefit:** most of the 3.7 ms of CPU, plus an unknown GPU saving.
This is an estimate, not a forecast.

**Exact-output design:** a depth-only shadow pass keeps the minimum depth at each
texel, so draw order does not change the result.

1. Batch casters that share texture, sampler and alpha-test state into one draw
   per light face.
2. Keep each light's six tiles across scenes and frames when its caster set is
   unchanged.
3. When a light's casters are only added, draw just the new ones without clearing
   its tiles.
4. Clear and redraw a light's tiles only when one of its casters is removed or
   changes.

This should produce a bit-identical atlas, provided sampling barriers and
alpha-test behaviour are preserved.

**Risks:** none to gameplay or the guest contract; this is host-only. It must
preserve retention semantics, the alpha-tested caster path, and read-after-write
ordering between atlas sampling and redraw.

**Smallest useful test:** a counter-only build that logs, per frame:
- world scenes with fixture lights;
- casters per scene, split by whether they come from the current or the previous frame;
- shadow `vkCmdDraw` calls.

If redraws per frame are greater than 1 and previous-frame duplicates are common,
proceed with the redesign.

**Delivery:** precompiled `.mw3update`, host rebuild only. Testers regenerate no
code.

**Prior work:** shadow clip-corner reuse and shadow submission reuse each
optimized the per-caster arithmetic or bindings. Neither removed this multiplier.
Do not repeat corner reuse.

### O2. Per-TL-draw host pipeline cost

**Locations:**

- `d3d_provider.inc:73`: per-draw capture copy and state snapshot.
- `d3d_provider.inc:209-266`: per-draw diagnostics, including `std::set` lookups,
  guest loads for ground detection, a loop over ground-normal bindings, and
  `fprintf`/`fflush` on the first use of each texture.
- `d3d_provider.inc:300`: vertices appended one at a time.
- `vk_scene.hpp:990-1059`: each lit draw builds a 912-byte `sun::Uniform`
  (size asserted at `sun_lighting.hpp:271`) and writes it to mapped memory, even
  when `ExactUniformRuns` has already identified it as a repeat.
- `vk_scene.hpp:134-151`: each `Draw` carries a 512-byte `emission_regions` array
  and a `std::function`.

**Evidence:** in the heavy phase, draw, sun and effect capture, world binding and
scene build total about 4.0 ms instrumented over 2,938 draws per frame (measured).
After instrumentation overhead the true figure is probably about 3 ms
(inference).

**Potential benefit:** 1–2 ms per heavy frame (hypothesis), from three exact
changes:
- Write each unique uniform once and reuse its dynamic offset. This saves about
  2.3 MB of mapped-memory writes per heavy frame.
- Make `Draw` smaller.
- Move the diagnostics out of the per-draw path.

**Risks:** low. Uniform bytes, validation, and draw and order records must stay
identical.

**Smallest useful test:** a draw-record and image comparison, plus the heavy-phase
mean across four alternating runs.

**Delivery:** precompiled `.mw3update`.

### O3. Original light subdivision for GPU-lit receivers (largest potential, highest risk)

**Locations:** original routine 0x547740 and its 0x57EA20, 0x57D690 and 0x57E110
paths, described in `docs/native-call-routing-performance-2026-10-22.md`.

**Evidence:** 1.03 ms exclusive and 5.71 ms inclusive in the heavy phase. The
inclusive figure is inflated by overhead and overlaps O1 and O2. Subdivision is
what creates the TL draw multiplication behind O1 and O2.

**Potential benefit:** bounded above by the heavy-minus-light gap of about 7 ms.
It overlaps O1 and O2. No forecast.

**Risks:** high.
- Resident sun-lit receivers neutralize legacy RGB.
- Per-vertex fog and UV interpolation, the RGB comparison in the transparent
  flush at 0x57E110, callback queue order and limits, sky, untextured and fallback
  draws all still depend on subdivision.
- The output would not be bit-exact.
- It needs a stated visual-equivalence criterion before any game test.

**Smallest useful test:** offline, compare subdivided against coarse emission on
the fog and UV channels for authenticated lit receivers only.

**Delivery:** precompiled `.mw3update`, as a host-routed guard like body dispatch,
after a contract review.

### O4. CPU/GPU serialization between scenes

**Locations:**

- `vk_scene.hpp:837-848`: every `render()` waits on the single scene fence before
  recording.
- `vk_scene.hpp:772-791`: `finish_world` waits again before FXAA.
- `vk_scene.hpp:231-235` and `vk_scene.hpp:375-379`: each present waits on the
  previous present fence.
- `vk_scene.hpp:3249-3263`: two-image FIFO swapchain.
- `vdd.inc:345-351`: every DirectDraw clear on the render target or Z-buffer is a
  separate submission.

**Mechanism:** a single command pool, fence, upload buffer, vertex buffer and
descriptor pool. CPU and GPU overlap only between consecutive scenes, and the GPU
idles while each scene is recorded.

**Potential benefit:** at most about 1.5 ms of scene-fence waiting in the heavy
phase (measured upper bound). It could be more if GPU timestamps show long passes.

**Risks:** moderate. Resource lifetimes must be ring-buffered correctly. Do it
only after the M2 GPU timing exists.

**Delivery:** precompiled `.mw3update`.

### O5. First-use hitches and memory

**Locations:**

- `vk_scene.hpp:902-967` and `vk_scene.hpp:1191-1210`: texture conversion, upload
  and mip generation run inside the scene submission.
- `vk_scene.hpp:2677-2698`: one `vkAllocateMemory` per image.
- `vk_scene.hpp:2654`: model staging buffers are never freed.
- `vk_scene.hpp:2740`: a target change triggers `vkDeviceWaitIdle`.
- No memory-budget query and no texture eviction anywhere.

**Evidence:** in frames 400–2699, only five intervals exceed 24 ms in at least
three of four confirmation runs: frames 1051, 1055, 1160, 1163 and 1176. Each one
coincides with 15–282 mip-level uploads, and frame 1160 also has 34 model uploads
(measured, by correlation with `verify-diagnostic/draws.txt`). Warmup reports
215 MB of extra mip data. Total VRAM is unmeasured.

**On the FPS drop pattern:** in Training, "lower, then better, then a sharp drop"
matches the route entering the near-light phase, not memory pressure. Memory may
matter in longer campaign sessions (hypothesis).

**Potential benefit:** removes reproducible first-use spikes and improves 1% lows
in the wider 400–2699 window. Negligible effect on the warmed mean.

**Delivery:** precompiled `.mw3update`.

## 4. Measurement corrections

1. **Report heavy and light phases separately.** Whole-window averages and 1%
   lows mix a refresh-capped half with a CPU-bound half. Treat any whole-window
   delta under about 2% as noise.
2. **Run one confirmation with `MW34_VSYNC=0`** (`vk_scene.hpp:3265`) so the light
   phase gives signal. Record the refresh rate and whether the display is variable
   refresh.
3. **Add GPU timestamps** per scene, shadow atlas, FXAA and present blit, plus
   CPU time inside `vkWaitForFences`, acquire and present. That distinguishes
   CPU-bound, GPU-bound and synchronization-bound frames.
4. **Prefer counters to fine-grained scopes.** About 57k QPC scopes per frame add
   roughly 4 ms and distort the high-call categories.
5. **Turn off diagnostic logs during timing.** `MW34_WORLD_LOG` and
   `MW34_MODELS_LOG` were enabled during the timing runs.
6. **Remember that the virtual clock makes guest `Sleep` free**
   (`mfc_stage.hpp:1382`). Real-play pacing is untested.
7. **Coverage gaps.** Combat (weapon effect lights), campaign missions with many
   fixture lights, rapid camera changes and long sessions are not covered. The
   near-light heavy pattern will likely dominate lit campaign maps (inference).

## 5. Open measurements

| ID | Question | Resolves |
| --- | --- | --- |
| M1 | Display refresh rate and VRR state | How to read the light-phase cap |
| M2 | GPU time per pass, especially the fixture atlas | Whether GPU or synchronization limits; gates O4 |
| M3 | World scenes per frame that redraw the atlas | Size of the O1 multiplier |
| M4 | Fixture casters per scene, current versus previous frame | Whether duplicate retained casters exist |
| M5 | Total and peak VRAM use (`VK_EXT_memory_budget`) | Memory-bound frames in long sessions |
| M6 | Guest `Sleep` calls in real-clock gameplay | Real-play pacing |

## 6. Next actions

1. **Fix the measurement.**
   - Re-report the existing runs by phase.
   - Build one counter-only host for M2–M5.
   - Run one `MW34_VSYNC=0` confirmation.

   *Done when* heavy and light phase means, GPU pass times and atlas redraw
   counts are recorded for the selected host.
2. **Restructure fixture shadows for exact output (O1).**

   *Done when:*
   - the atlas is drawn at most once per light per change;
   - casters are batched;
   - all 2,800 draw records and seven full-resolution images match byte for byte;
   - the heavy-phase mean improves across four alternating runs.
3. **Trim the per-TL-draw host pipeline (O2).** In parallel, evaluate subdivision
   equivalence offline (O3).

   *Done when* uniform writes are deduplicated, `Draw` is smaller and hot-path
   diagnostics are gone, with identical records and images.

**Avoid:**

- repeating shadow clip-corner reuse;
- the GPU projection or terrain perspective bypass (previously about 0.23 ms with
  no net benefit);
- treating the suppressed-draw capture bypass as the main lever, since models are
  only 6.6 sun draws per heavy frame (inference);
- judging changes on whole-window averages;
- any reduction in visual quality. None is needed, because the cost is host
  bookkeeping rather than pixels.
