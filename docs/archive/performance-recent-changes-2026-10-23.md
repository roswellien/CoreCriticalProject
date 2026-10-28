# Recent visual changes and allocation performance (2026-10-23)

The recent weapon, status-preview and monitor work does not show a material
Training regression in matched tests. Two allocation changes remove repeated
CPU storage allocations and GPU buffer growth without changing draw bytes or
captured images. Combat tests reveal repeatable first-use stalls after the recent
visual work; a third change preloads immutable model geometry during loading.
Training FPS changes are small; these are not a large average-FPS fix.
Formal native acceptance remains **131/144**.

## Boundaries and identities

The production interpreter, original-code fallback, translated game module,
gameplay, FP operations, replay behavior and shaders are unchanged. This work
advances resource reuse in the native Direct3D capture and Vulkan buffer paths.
It grants no new native-game acceptance credit.

| Build | Identity |
| --- | --- |
| Before recent visual work | `D:/Projects/MW34Recomp/local/work-ahead/c1m1-surface-investigation-20261023-r1/fix-host/entry_commandline.exe`, SHA-256 `db728475f51f63e34b20b9cb43a338872054d4f8301d8e7d7111fec85df21ba2` |
| Current doubled-missile parent | `D:/MW3MissileGainUpdate-20261023-r1/Runtime/bin/entry_commandline.exe`, SHA-256 `0a787590a4f12f24fd99d0b3e09ccebf1656f43f569bd4dadd98a02865999aa8` |
| Tested allocation candidate, unsigned | `D:/MW3FrameAllocation-20261023-r1/entry_commandline.exe`, SHA-256 `c9581e556ed41878d4d5c15adebee8cdce1fe6bb389c5570a68bdd85b88d7900` |
| Final model-preload candidate, unsigned | `D:/MW3ModelWarmup-20261023-r1/entry_commandline.exe`, SHA-256 `772edeea86cfe9a38c7c69cd97e0a46c24cf570c3a5210346fbc506d762c2b78` |
| Unchanged translated module | SHA-256 `6d6e3c25fef68727113a6d52859253883dbb554958ddaa5a091187667aa8bfa5` |

All comparisons use the same frozen asset bindings and graphics settings:
3440×1440, FXAA, AF16, draw distance1600, fog1100, replay off and monitor off.
All 38 prepared banks, 18 model replacements and 11 environment packs remain
enabled. The Thor/Vulture/Annihilator asset bindings changed in another chat
during this investigation; the timing comparisons deliberately keep the initial
asset set frozen. Deployment must preserve the user's newer asset selections.

## Training measurements

The initial Training blocks use two runs per variant, interleaved ABBA. Values below pool
matching frame intervals, rather than average per-run FPS. Avg FPS is
1000/mean frame time; 1% low is 1000/mean of the slowest ceil(1%) intervals.

| Comparison | Before avg FPS | After avg FPS | Before 1% low | After 1% low | Before mean ms | After mean ms |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Recent visual changes |128.78|129.40|63.91|63.74|7.765|7.728|
| Allocation changes vs doubled-missile parent |129.94|130.57|64.52|65.21|7.696|7.659|
| Allocation changes, heavy phase only |94.07|95.13|62.14|62.83|10.630|10.512|
| Allocation changes, light phase only |182.41|181.62|113.92|116.71|5.482|5.506|

These measurements support no material Training regression from the visual
changes and only a small difference from allocation reuse. There were no warm
frame intervals over 33.33 ms in either final Training variant. They do not prove
that all live-play hitches are fixed or predict performance on another PC.

Evidence root: `D:/MW3PerformanceReview-20261023-r1/`.
`recent-summary.json`, `frame-summary.json` and `frame-queue.json` retain exact
run membership and per-run figures. A scratch-only parent control had a slow
outlier; its apparent 3.7% pooled gain is not used as the final result. A separate
same-binary scratch toggle comparison showed about 1%, prompting the final ABBA.

## Combat measurements

The complete six-run block uses old/current/candidate/candidate/current/old
order. Here candidate means allocation-only, before the additional model preload.

| Build | Avg FPS | 1% low FPS | Mean ms | Worst ms |
| --- | ---: | ---: | ---: | ---: |
| Before recent visuals |106.46|56.83|9.393|29.707|
| Current doubled-missile parent |105.64|47.70|9.466|34.420|
| Allocation changes only |105.98|47.13|9.435|34.238|

Average FPS changes little, but the recent visual work regresses the combat
tail. Frame 1584 repeatedly costs about 34 ms in the current parent versus
about 19 ms before the recent visual work; frame 2076 is also slower. Each
current and allocation-only repeat has one interval over 33.33 ms. Allocation
reuse alone does not fix this. `combat-summary.json` retains all six runs.

The current parent uploads 32 new model buffers (2,810,304 bytes) at frame 1584.
The preload candidate uploads none at that point, while retaining identical
original draw hashes and captured images. This is a concrete first-use resource
lead, not evidence that all combat stalls share one cause.

Final model preload plus allocation changes, against the retained matched
parent controls (two candidate repeats per route, not a fresh interleaved ABBA):

| Workload | Before avg FPS | After avg FPS | Before 1% low | After 1% low | Before mean ms | After mean ms |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
|Training warm|129.94|130.89|64.52|66.26|7.696|7.640|
|Training heavy|94.07|95.32|62.14|64.18|10.630|10.491|
|Combat|105.64|106.74|47.70|52.76|9.466|9.369|
|Late combat|102.16|102.98|59.09|61.76|9.788|9.711|

The model-loading frame drops from 34.42/33.65 ms in the parent repeats to
20.19/19.78 ms in the preload repeats. Combat 1% low improves about 10.6%,
but remains below the 56.83 FPS level before the recent visual work. The
separate frame-2076 stall remains at about 23–24 ms. No measured combat
interval exceeds 33.33 ms in the final two runs; this does not establish that
all gameplay hitches are gone. Average FPS gains remain small.

The first 3D scene takes 11,380.66/11,239.01 ms in the parent and
11,807.17/11,661.56 ms with preload: about 0.42 seconds more loading work in
this route. Staging and device-local geometry memory both remain resident.
Thus the gain trades some loading time and memory for a shorter later stall.

Final run membership, per-run metrics and route equality are retained in
`model-warmup-timing-groups.json`, `model-warmup-training-summary.json` and
`model-warmup-combat-summary.json`. Attribution of the remaining stall to
texture preparation is a lead, not yet isolated by a matching experiment.

## What changed

`DrawVertexScratch` keeps temporary input vertex storage after a merged or
suppressed draw no longer needs it. Queued draws retain their own storage.
The next original guest-vertex copy overwrites every logical byte. Original
logging, validation, capture, suppression, draw ordering and scene barriers
remain in place. Retained spare CPU capacity is bounded to 4 MiB.

The native verification reused 3,872,259 temporary buffers versus 1,224,044 growths:
about 76% of these transient allocation requests reuse storage.

For an already allocated Vulkan streaming buffer below 16 MiB, growth rounds up
to the next 64 KiB boundary. Initial allocations, including immutable model
staging buffers, stay exact. Added logical capacity is less than 64 KiB per grown
buffer; Vulkan's actual memory requirements still apply. Data upload lengths
and draw counts remain unchanged. OOM during reserved creation, allocation,
binding or mapping retries the exact requested size. Mapping failure also
retries exact size. Unknown Vulkan errors remain visible failures.

Matched diagnostic Training runs reduced GPU buffer growth operations from
**97 to 21 overall**, and **25 to 5** in the measured warm interval. These are
growth events, not all GPU allocations, and these capture-enabled runs are not
used for timing claims.

For the allocation-only candidate, exactly four files differ from the signed parent's source composition:
`d3d_provider.inc`, `early_triangle_commands.hpp`, `vk_scene.hpp`, and the new
`buffer_reserve.hpp`. `source-checks.json` pins the tested executable and verifies
the maintained adapters reproduce those sources and apply idempotently.

The final candidate additionally changes `mesh_override_stage.inc` and adds
`model_geometry_warmup.inc`. At the first valid world scene it queues already
loaded immutable geometry for the existing `model_buffer` allocation, upload
and transfer barrier path. It adds no draw, pose calculation or guest call.
Animated donor geometry keeps its original path. The 64 MiB payload budget
admits 824 batches (67,108,704 bytes) in the frozen profile and skips 939 over
budget. Remaining geometry uploads normally on first use. Device-local and
retained staging allocations both consume memory, plus Vulkan allocation
requirements; the 64 MiB budget is not a total VRAM or process-memory cap.
`MW34_MODEL_GEOMETRY_PREWARM=0` disables this preload for diagnosis.

## Validation

- Training: all 2800 original draw rows and seven 3440×1440 captures are
  byte-identical to the parent, with buffer reserve enabled and disabled.
- Combat: all 2100 original draw rows and five 3440×1440 captures are byte-identical
  to the doubled-missile parent. Both runs exercise original missile creation
  and doubled exhaust/light settings.
- Actual extracted Vulkan `ensure` implementation: 618,688 checks pass, including
  capacity bounds, initial exact allocation, allocation/map failure retry and
  visible unknown-error propagation.
- Vertex scratch: 64,226 checks pass for full vertex bytes, queued ownership,
  nested capture and reuse. Existing early-triangle batching: 96,028 checks pass.
- Timed runs have no capture, profiler or growth tracing. Frame IDs, scene counts
  and guest clock timestamps match across variants.
- Final preload candidate: all 4900 original draw counts/hashes and twelve
  full-resolution captures match. Resource counters intentionally differ because
  uploads move earlier. Its actual stage include passes 76 load-phase, ownership
  and budget checks; an invalid setting fails visibly in a separate check.

Native fidelity receipts are `frame-fidelity.json` and `combat-fidelity.json`.
The final candidate adds `model-warmup-fidelity.json` and its own source checks.
Buffer tests extract the actual candidate source; they do not reimplement its
allocation routine. Original media and generated native game code stay local.

## Measurement controls and limits

Runs use visible, uncapped Vulkan presentation with no VSync and the same
learned pipeline cache. Training has 2800 presentation frames, virtual clock
16.666667 ms and surface detail time fixed at 0. The warm interval is 1050–2549,
heavy 1050–1694 and light 1695–2549. The first 3D frame is 206; retained older
scripts inserted 150 menu frames, so their absolute bins cannot be reused.

The combat route has 2100 presentation frames, virtual clock 50 ms, fixed detail
time 0 and the retained Thor/Vulture LRM/PPC input. Its measured interval is
1300–2099; late combat is 1600–2099. Scripted clocks give matching simulation,
not an estimate of real-time mission duration. Diagnostic logs routed to NUL
retain common formatting overhead. Average results apply to these workloads.

Game/render process identities are checked before and during runs. Timing
interrupted by foreign Blender/game/video jobs is excluded and retried. No
other chat's jobs were terminated; trailer work was allowed to finish first.
The expected frame-budget stop is exit 1 with a verified swapchain-frame marker,
not an unqualified successful game exit. Loading/teardown is excluded from
gameplay timing and CPU sampling.

## Updated bottleneck diagnosis and rejected experiments

A separate diagnostic clone of the current parent bounds sampling to heavy
gameplay frames 1050–1694. GPU timestamp spans and CPU recording times are
instrumented separately; nested GPU pass spans must not be summed with their
parent scene span. The diagnostic source is not shipped.

| Heavy-phase work | Measured ms per presentation frame |
| --- | ---: |
| Whole GPU scene span |0.665|
| GPU FXAA |0.133|
| GPU resident presentation |0.030|
| CPU renderer total, inclusive |1.416|
| CPU fixture-shadow preparation, within renderer total |0.330|
| CPU fixture-shadow recording, within renderer total |0.055|
| CPU scene fence waiting |0.075|

Evidence: `bounded-current-profile/attribution-summary.json` and the bounded
profile under `D:/MW3CurrentAttribution-20261023-r2/`. The uninstrumented heavy
frame is about 10.6 ms. The much older shadow-cost report describes a pre-R6
composition; its approximately 3.7 ms shadow CPU estimate is not the current
bottleneck. The present evidence points to CPU work outside Vulkan as the next
larger opportunity, rather than reducing lighting/shadow quality.

Bounded samples include substantial time in the unchanged translated module;
hot export regions include 0x51DFA0, 0x57EA20, 0x53F2E0 and 0x547740. These are a
starting point for narrower timing, not proof of a particular safe replacement.
The original adaptive geometry/lighting subdivision also produces fog, UV,
alpha, queue and initialization effects. Existing projection-bypass failures
remain relevant. No original computation is skipped in this update.

A fixture-face reuse prototype passed exact-output audits but produced only
about 0.7% FPS difference and was not adopted. An immutable model-bound cache
was not adopted because the current expensive caster route is predominantly TL
geometry. Both prototypes and their checks are archived privately.

An early hypothesis that replay-off still incurred rolling guest-memory history
was disproved on this hardware route: the suspected hook is not reached. The
user was corrected, the prototype was rejected, and replay behavior is unchanged.

## Update delivery

Signed R7 is selected in `local/remaster/launcher.json`, with source verification
enabled. The signed executable SHA-256 is
`26b4767532758230ebb315887b2b1e43417540c62269b45dbcd25bcf4bb67270`.
The dev launch preflight passes. A semantic comparison against the immediately
previous profile verifies that only the native executable/source paths and two
allocation/preload flags change; newer asset bindings and all preferences remain.

Private bundle: `D:/MW3PerformanceUpdate-20261023-r7/CoreCriticalGameUpdate.zip`
(35,947,862 bytes). It contains signed `mw3-performance-20261023-r7.mw3update`,
its matching payload ZIP and import instructions. Sequence 2026102313;
minimum launcher 1.0.27. The runtime executable has a valid timestamped artifact
signature; the update envelope is signed with the existing private playtest key.
The translated module hash remains unchanged. No original media, generated source
contents or signing private key is included, and no client code generation is needed.

The launcher's real update checks pass from both the 1.0.28 installer runtime
and the doubled-missile runtime: signature verification, installation, activation,
validation and rollback. The update preserves full-bank storage/seek fixes,
R6 batching, compact monitor, upgraded status models, PPC gain and doubled
missile effects. Replay remains off. This is a game runtime `.mw3update`;
the launcher application version does not change. No public upload or Git
commit was made in this turn.

For future builds, apply the existing R6 `apply_early_triangle_commands.py`
composition first, then `apply_draw_vertex_scratch.py` and
`apply_buffer_reserve.py` to that pinned host source. Reapplying the R6 adapter
after the scratch adapter is not the supported order. Do not replace the full
selected composition with older maintained stage snapshots. The two new
adapters fail visibly when their original capture/allocation anchors change.
Apply `apply_model_geometry_warmup.py` after those allocation adapters to obtain
the final preload composition.

The next substantial optimization should first time the hot translated CPU
regions over the same heavy window, then remove duplicate work only where
all original outputs and required effects can be retained. No FPS saving is
claimed for that follow-up before a matching benchmark exists.
