# GPU geometry development plan

Authorized 2026-10-15. Preserve the recompiled game simulation; modernize its
rendering handoff. The immediate deliverable is an isolated, repeatable live
CPU/GPU geometry comparison, not a production renderer switch.

## Stages and completion criteria

1. **Measure the existing model handoff.** Use the same executable, deterministic
   input, private game copy, assets, resolution, AA/AF and scenery distance.
   Compare CPU replacement projection against resident GPU model transforms.
   Add opt-in host geometry timing/counts; alternate CPU/GPU run order and
   distinguish correctness captures from timing runs. Require actual model
   draws, matching original draw records, inspected image differences, protected
   save hashes and intentional bounded termination. Report presentation timing
   separately from CPU scope timings; neither is a GPU timestamp measurement.
   No initial claim about whole-world savings: this path is already partly GPU.
2. **Recover the earlier world handoff.** Identify terrain and opaque building
   asset ownership, local geometry/normals/UVs, per-instance transforms, camera
   provenance and lifetimes before projection/culling. Build one retained mesh
   cache and a bounded terrain/building draw prototype. Unknown contracts stop
   visibly. Keep original producers until their side effects are accounted for.
3. **Move proven render work.** GPU vertex transformation and clipping replace
   redundant CPU work only where state/side-effect comparisons justify it.
   Compare the same visuals and original game state first. Test destruction,
   LOD, near clipping, zoom, cockpit, Lab, mission unload and original mode.
4. **Add lighting/materials.** One per-pixel directional light and a bounded
   moving point light; add verified normal-map/tangent bindings. Original AI,
   physics, damage and animation decisions remain CPU-owned. Separate options
   and settings; do not infer material relief from painted texture shading.
5. **Add shadows.** Collect casters independently of player-camera visibility,
   prove a mech/building shadow on terrain, then consider stable outdoor
   cascades. Shadow distance/quality remain independent of 1600-unit scenery.
   Most transient lights initially remain unshadowed.

## First experiment

Use the published Mech Lab build as the frozen source base. A development-only
copy adds profiling without changing shader math or original producers.
`MW34_GEOMETRY_PROFILE` enables a CSV with per-present counts and host timings.
`MW34_GPU_MODELS=0/1` selects the existing CPU/GPU replacement paths. Both retain
the original game's own render calculations, so measured savings isolate
replacement geometry; removing original CPU geometry work belongs to stage 3.

Test 3440×1440, FXAA, AF16, 1600 scenery with current local model/texture assets.
Use warm scene frames only, with at least two runs per path in alternating
order. Capture a separate matched frame to assess GPU-float/CPU-double edge
differences. Validate unchanged original draw records and that GPU upload counts
stabilize. Record CPU clipping fallback explicitly. Do not discard slow samples
without reporting them. FIFO presentation may hide throughput improvements.

The first test can establish a useful boundary and bound replacement-model
cost. It cannot establish full-world geometry speedup, GPU occupancy, FPS cap
independence, terrain normals, dynamic lighting or shadow support.

## Integration policy

Keep the playable launcher unchanged during development. Original media,
generated code and captured evidence stay local. Preserve concurrent work and
existing evidence. No commits, new runtime dependency, interpreter fallback,
gameplay timing change or acceptance-count increase is part of this plan.
Performance conclusions must name the route, hardware, build and measured scope.

Context: [lighting/shadows investigation](dynamic-lighting-shadows-investigation-2026-10-15.md).

Stage1 completed2026-10-15: [bounded live comparison results](gpu-geometry-test-results-2026-10-15.md).
The initial model comparison averages25% less presentation time on the GPU
control; Play already uses this path. Stage2 world geometry recovery is next.

Stage2 initial prototype completed2026-10-15:
[original-world GPU geometry bridge](gpu-world-geometry-prototype-2026-10-15.md).
A bounded scenery subset now uses cached raw mesh data and GPU projection with
matching original colors/fog. All1400 original records match; lifetime eviction,
broader classification and normal/tangent validation remain open before production.
Next implementation work removes prototype matching and establishes direct
polygon/instance ownership before bypassing proven redundant CPU render work.

Stage3 direct-binding step completed2026-10-15:
[direct polygon binding and guarded metadata cache](gpu-world-direct-binding-2026-10-15.md).
Matched-route mean frame time improves4.72% against the search prototype, with
unchanged comparison captures. Original CPU projection remains because clipping
and material callbacks consume its output. One divergent disabled-control run
is retained; two unchanged repeats match. No production/acceptance promotion.

Stage3 bridge-cost follow-up:
[cached world triangles and bounded audit removal](gpu-world-fast-binding-2026-10-15.md).
Retain triangle lists per source revision and omit the bridge's repeated CPU
projection only for proven unchanged textured polygons. Original CPU producers
still execute. Their material callback can queue copies of projected TL vertices;
that consumer must be owned before the original perspective loop can be removed.

Stage3 original-producer experiment:
[first CPU perspective bypass test](gpu-projection-bypass-test-2026-10-15.md).
A bounded lit-scenery path now conditionally omits the first n-1 original
projection iterations. The 550-frame pair matches; the longer test matches
1,254 completed frames and four captures, then stops on a scratch-read alert.
Investigation found retained flat-memory consumers outside the current dirty
observer, so live scratch safety is unproven and the alert may reflect missed
writes. Expand observation before promoting the bypass or claiming a speedup.
Both playable launchers remain unchanged.

Performance follow-up:
[alpha regression isolation](gpu-alpha-regression-investigation-2026-10-15.md)
finds that the disabled projection experiment still carried a slower CPU
producer object. Restoring its production optimization recipe recovers the
normal launcher's approximate137FPS with GPU scenery retained. Keep original
CPU-removal instrumentation in its private safety-test host; disabling its
runtime branch does not restore the optimized object or prove zero overhead.
The alpha launcher now selects the corrected optimized GPU package after
matched draw/capture and original-compatible Training checks. Normal Play is
unchanged; the corrected alpha is approximately level with normal performance
on this bounded route, not a newly established GPU geometry FPS gain.

The next CPU-removal safety step is tracked in
[the observed projection test](gpu-projection-watch-test-2026-10-15.md).
The optimized original-loop and host observer fixtures pass, including explicit
State/token arguments under the original noalias contract. All 37,201 watched
objects now compile/link and the disabled control matches 1,000 original draws
and four captures. The 1,800-frame bypass actually omits 178,859 iterations with
matching permitted depth-copy observations and no dirty-read guard failure,
but fails gameplay image equivalence and changes original draw counts from
frame 489. Resolve this regression before timing or promotion; neither playable
launcher changes and no new speedup is established.

The [differences investigation](gpu-projection-differences-investigation-2026-10-15.md)
finds that the failed run already differs before the first bypass admission.
Subsequent 1,800-frame repeats match all semantic records and six captures, but
the exact earlier initialization/movement divergence remains unresolved. Expanded
optimized FP fixtures pass 1,152 cases in both watched and unwatched pipelines.
Retain the failure and trace recurrence before attributing a cause or promoting.
