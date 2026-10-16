# Live GPU geometry comparison

This development test answers whether the existing replacement-model GPU path
reduces host geometry work at otherwise matching visual settings. It is the
first stage of [the development plan](../../docs/gpu-geometry-development-plan.md),
not a complete world renderer or a lighting/shadow implementation.

Apply `apply_geometry_profile.py <fresh-host-source>` to a private frozen source
snapshot. Build with its existing native build procedure and unchanged translated
object list. Do not apply it to the playable source snapshot in place.
`MW34_GEOMETRY_PROFILE=<csv>` enables per-present QPC CPU scopes and counters;
file-open/QPC-frequency failures are visible. No floating-point profiling math
runs in the guest FP environment. Shader math and original producers are unchanged.

The caller supplies an existing private-save regression harness supporting the
parameters used by `run_geometry_comparison.ps1`; that harness must set the CSV
environment variable to `<run>/geometry.csv`, protect original saves/registry,
guard concurrent game processes and write the existing run/draw/timing records.
The retained local instance is `local/gpu-geometry-test-r1/run-review.ps1`.
The harness and game assets are local prerequisites, not shipped test media.

```powershell
& tools/remaster-launcher/run_geometry_comparison.ps1 `
  -Harness local/gpu-geometry-test-r1/run-review.ps1 `
  -Executable local/remaster/gpu-native-geometry-profile-r1/build/entry_commandline.exe `
  -Assets local/terrain-distance-investigation-r1/current-model-environment.json `
  -InputScript local/seh-dispatch-validation-r1/frozen-inputs/input-ia-13.txt `
  -Prefix geometry-r1 -Frames 1600

python tools/remaster-launcher/analyze_geometry_comparison.py `
  local/gpu-geometry-test-r1/runs --prefix geometry-r1 `
  --output local/gpu-geometry-test-r1/comparison.json

python tools/remaster-launcher/test_geometry_comparison.py
```

CPU/GPU/GPU/CPU timing runs use frames800–1600 after warm-up. Separate 1050-frame
cases capture frame1000 and never enter timing statistics. The analyzer rejects
incomplete budgets, missing frames, wrong CPU/GPU mode, absent original/model
activity, missing GPU execution counters, mismatched build/assets/settings/input,
and divergent original draw or scene/clock streams. Six authored controls exercise
valid data and menu-only, gap, no-GPU, early-fault and wrong-mode rejection.

Metrics:

- `replacement_emit_cpu_ms`: wall time inside host replacement emission, including
  selection/state setup; it is not solely arithmetic time or GPU elapsed time.
- `original_51fb30_inclusive_cpu_ms`: selected original function body scope, with
  original callees; its full semantics remain unclassified. It is not all original
  geometry/engine CPU work and should not be added to overlapping scope totals.
- `cpu_vertices` / `gpu_vertices`: replacement input vertices processed by the CPU
  clip/projection branch or queued through GPU instances. Per-frame values can
  include multiple camera/scoped submissions.
- `tl_bytes`: replacement screen-space vertex bytes generated on the CPU; not
  total PCIe traffic. GPU cache uploads are independently checked in draw records.
- `near_batches`: GPU-enabled batches retaining the existing CPU near-plane
  clipper. Zero does not establish near-plane clipping coverage.
- Presentation deltas include game CPU, driver, GPU, desktop/FIFO pacing and log
  overhead. All slow measured samples remain in the summary. Dedicated GPU
  timestamp queries and a full CPU/GPU critical-path breakdown remain future work.

Inspect image differences; GPU float versus CPU double calculations may differ
around edges. The analyzer reports differences rather than silently declaring
visual equivalence. The current Play profile already enables GPU models, so a
benefit against the CPU control is not a newly delivered Play performance gain.
No acceptance count, production default, timing, save or gameplay change follows
from a bounded benchmark.
