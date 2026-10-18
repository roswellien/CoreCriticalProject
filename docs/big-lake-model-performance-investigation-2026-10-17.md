# Big Lake model performance investigation — 2026-10-17

The 30-model integration lost the model-path and candidate-name caches from
`tools/remaster-launcher/apply_perf_env_cache.py`. Restoring those caches in a
private candidate roughly doubled throughput on the controlled route, with the
same models, lighting, original draw hashes and scene pixels. The user then
authorized promotion; the fixed host and profile are now installed as recorded
below. Acceptance remains **131/144**.

## Observed live regression

Latest run: `C:/Users/jcbla/MW34SunTests/big-lake-r1/play-runs/20261017-172211-383`.
Its executable matches profile SHA256
`f84f567eaf8b9c973c1609fe22f31f7ddd9f7180ea29e85f0ae7e2ba71a5cee6`.

Frame-time column two is an elapsed timestamp: adjacent differences give frame
durations. World counters are cumulative; use differences between **present**
records, excluding interspersed geometry/mesh records. Mission samples here are
frames with increasing sun world/TL/model counters; they can include load spikes.

| Run | Mission samples | Mean ms / FPS | Median ms | p95 ms | Frames >33.33 ms |
| --- | ---: | ---: | ---: | ---: | ---: |
| Latest, 17:22 | 8,807 | 20.28 / 49.3 | 18.65 | 31.01 | 211 |
| Earlier, 16:52 | 22,024 | 11.51 / 86.9 | 11.15 | 15.92 | 9 |

These are different live play sessions, not an isolated before/after test.
Average replacement-part draws rose from 36.9 to 70.3 per mission frame, while
sun TL draws fell from 1,090.0 to 887.2. Slow latest-run stretches also occur with
few model parts, so visible triangle count alone does not explain the regression.

## Concrete defect and candidate

In the current private host's `host-source/mesh_override_stage.inc`:

- `override_begin` calls `getenv` for every model slot, then scans every enabled
  roster to determine whether each submitted node name could be a mech part.
  This executes during ordinary scene traversal, including non-mech nodes.
- `override_validate_root` also repeatedly looks up each slot's environment path.
- With 30 slots and more environment entries, both the number of lookups and the
  environment search length grow. The installed UCRT's `env/getenv.cpp` confirms
  that lookup scans the environment under a lock.

The existing performance installer already provides `override_mesh_env` and
`override_candidate_name` to cache this process-fixed configuration. The expanded
adapter no longer contains these helpers, although the installer's cached sky
debug/shadow-audit lookups are still present. Restore the model cache after roster
integration; do not reapply the whole installer blindly to an already patched host.

The candidate copies the current host and changes only `mesh_override_stage.inc`:
the existing cache helpers plus the two lookup call sites. It retains all 30 slots,
identity/damage tests, roster contents, donor solving, assets, shaders and settings.
Source comparison confirmed exactly one changed host source file.

Candidate executable SHA256:
`2a3531ac06224fb90495609c5badb977f1d9823931591742a2476fe6191f28bf`.
Clang-CL/Ninja build succeeded; compiler warnings are retained in the build log.

## Controlled checks

Evidence root, entirely local:
`C:/Users/jcbla/MW34SunTests/big-lake-r1/performance-review-20261017-173410/`.
It contains baseline logs, `candidate-host/`, `candidate-change.diff`, build log,
`candidate-run/`, `candidate-check/` and `baseline-check/`.

Both pairs use the existing `shadow-r1/stand-still.txt` script, 50 ms virtual
clock, 3440×1440, FXAA, AF16, draw 1200/fog 1100, sunset, shadows and normal maps.
Despite its name the script includes turning and movement. This is route
throughput, not a prediction of every live combat scene.

| Pair / window | Current mean ms / FPS | Cache candidate mean ms / FPS | p95 current → candidate |
| --- | ---: | ---: | ---: |
| Current then candidate; profiled, frames 400–1600 | 28.05 / 35.6 | 12.92 / 77.4 | 43.53 → 19.43 ms |
| Candidate then current; unprofiled, frames 400–1000 | 23.18 / 43.1 | 12.14 / 82.4 | 37.67 → 19.57 ms |

The second pair excludes frames 600/601/900/901 around screenshot readbacks.
Sampling/geometry instrumentation is enabled equally in the first pair and
disabled in the second. First-pair UCRT samples fall from 11,196/22,892 (48.91%)
to 417/10,890 (3.83%). Baseline replacement emission averages 0.293 ms/frame,
so the donor solver is not supported as the main cause of this regression.

Correctness checks:

- All 1,600 first-pair and 1,000 second-pair present records match in every
  recorded world/render counter except the two CPU timing counters.
- All 1,000 second-pair original frame/draw/hash triples match exactly.
  Extended draw logs differ in the cumulative mip-level upload counter; whole
  extended-log equality is not claimed.
- At frames 600 and 900, 3440×1440 screenshots differ only inside the performance
  overlay, bounding box `[98, 7, 679, 34)`, where FPS/timing text changes. Every
  pixel outside that box matches exactly. Full screenshot hashes differ.
- All bounded tests stop at the explicit frame-budget fault, exit 1, as expected.
  These are not normal-quit or mission-completion tests.
- Current playable executable hash still matches the profile. No game/build
  processes remained at completion; protected Python PIDs 6536/5196 were untouched.

## Recommendation and remaining costs

The cache restoration was selected for the playable Big Lake host, with its build
identity/profile updated after validation. It removes redundant host bookkeeping
at the same live native render boundary; it does not reduce model or lighting
quality, skip original game producers, or add acceptance credit. Initial private
experiments and subsequent promotion are recorded separately below.

Afterward, profile a representative fight again before choosing further work.
Original primitive submission (`0x53F2E0`), general material lighting
(`0x545720`), memory access/dispatch and fog remain identifiable CPU hotspots.
These general routines do not establish terrain-only attribution. Terrain has
a partial GPU geometry bridge, but CPU work removal is
unfinished. `MW34_GPU_TERRAIN=1` also admits names starting with `bwg` through
`is_admitted_world_name` in `world_geometry_stage.inc`, in addition to the
existing `ter`/`wall`/`healthy` names. The latest live run contains 276 cached
`bwg` polygon geometry records, out of 930 total geometry records. These are
geometry records, not distinct terrain tiles or a coverage percentage.

That bridge still wraps and calls the original `0x53F2E0` body, then captures
its already submitted TL draws in `world_capture` and replaces admitted draws
with resident geometry. It does not bypass the CPU producers. The additional
`terrain_stage.inc` wrappers also call the original bodies, including
`0x545720`; its `terrain_gpu_enabled` helper is unused. Other opaque terrain TL
draws receive GPU sun/normal/shadow shading through `sun_capture_tl`, after CPU
transformation. `MW34_GPU_PROJECTION` remains 0.

Thus neither "all terrain is off the CPU" nor "the terrain flag does nothing"
describes the current host. Some terrain geometry is retained on the GPU and
lighting is modernized; per-frame CPU terrain transformation, original lighting/
fog, clipping and submission still execute. This corrects the investigation's
initial overly broad inference from the unused diagnostic helper.

The live model logs also show Bushwacker LOD1 queuing the same 34,438 triangles as
LOD0 in the sampled full-model snapshots. Genuine visual LOD reduction is a later
GPU-cost opportunity requiring its own silhouette/damage checks. No benefit is
measured here, and sampling the main CPU thread does not measure GPU shader time.

No files were committed. Original media and generated code remain local. No new
milestone or whole-game fidelity claim is made.

## Promotion after user authorization

The user said to proceed. Restored the same cache in
`C:/Users/jcbla/MW34SunTests/big-lake-r1/shadow-r1/host/host-source/mesh_override_stage.inc`
and rebuilt with that host's existing Clang-CL/Ninja build script. The original
source, profile and executable are retained under the evidence root's
`promotion/`. The root launcher now resolves the rebuilt executable through its
existing profile, with SHA256:

`709fcac6625d6646356b32566259fdc69679b36ad348f894eb780e27619fcb08`.

The rebuilt host passed another 1,000-frame check against `baseline-check`:
all original frame/draw/hash triples and all non-timing world counters match.
Frame-600/900 captures match outside the same changing FPS-overlay rectangle.
Frames 400–1000, excluding capture/readback frames as above, average **12.18 ms
(82.1 FPS)**, median 11.09 ms and p95 19.30 ms. The corresponding original-build
check averaged 23.18 ms (43.1 FPS). The bounded run ends at its expected frame
budget fault; sustained user gameplay remains to be checked. Evidence:
`promotion/smoke/`, `promotion/build.log`, `promotion/result.json`.

`tools/remaster-launcher/apply_perf_env_cache.py` now exposes `--models-only`.
This mode validates all model anchors before writing, accepts an already cached
adapter without rewriting it, and leaves renderer/HUD edits alone. Checks against
the actual original/candidate sources reproduced the validated candidate exactly;
an altered source anchor was rejected. Reapplying the mode to the installed host
also succeeds without further changes. Use it after roster/adapter replacement
to retain this optimization; it adds no hooks or dispatch addresses.

The profile retains all assets and graphics values; only its executable hash
changed. No interpreter fallback, projection bypass, model reduction or lighting
reduction was introduced. Native execution reaches the same live Instant Action
render boundary with less host bookkeeping. Terrain CPU work removal remains
unfinished as described above; no acceptance count changed and no commit was made.
