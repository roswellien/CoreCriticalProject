# Native geometry benchmark: 2026-10-16

The current alpha launcher is approximately level with Remaster on the measured
Instant Action route. No reliable net performance gain is established. The newer
CPU-projection-removal experiment fails this run's matching-scene check, so no
valid CPU-removal speedup percentage is reported. Neither launcher changed.

## Valid launcher comparison

Hardware: Ryzen 7 9700X, Radeon RX 9070 (driver 32.0.31035.1003), approximately
32 GB RAM. Both builds use 3440×1440, FXAA, AF16, GPU replacement models/HUD,
the same frozen 39 texture banks/seven model bindings, HUD/music, registry and
ordinary replay input. All game runs use private copies. The script traverses
and turns through Instant Action; the virtual clock advances 50 ms per presented
frame for identical simulation input. Reported FPS is actual host throughput,
not the virtual simulation rate. These are not real-clock gameplay benchmarks.

Two runs per build/settings combination, with reversed order on repetition.
Measure every interval ending at frames 600–1799 inclusive: 1200 samples per run,
2400 per result. Startup and final capture are outside that window. No slow
samples within the window are discarded. FPS is 1000 divided by mean interval;
1% low is the per-run reciprocal mean of its slowest 12 intervals, averaged
across the two runs. Optional investigation/draw/geometry logs are disabled;
the GPU world's required world log remains enabled. Diagnostic platform traces
from the interactive Remaster profile are disabled for the matched benchmark.

| Settings/build | Mean frame time | FPS | FPS change vs same-distance Remaster | 1% low FPS |
| --- | ---: | ---: | ---: | ---: |
| 1200 draw / 1100 fog, Remaster | 11.464 ms | 87.2 | baseline | 38.1 |
| 1200 draw / 1100 fog, alpha GPU world | 11.363 ms | 88.0 | +0.9% | 31.8 |
| Stock 800 draw / authored fog, Remaster | 7.213 ms | 138.6 | baseline | 77.8 |
| Stock 800 draw / authored fog, alpha GPU world | 7.275 ms | 137.5 | −0.9% | 69.7 |

At 1200/1100, individual alpha runs are 89.9 and 86.2 FPS; Remaster runs are
87.5 and 86.9. The mean difference is smaller than this variation. Alpha's
slower-frame results are worse in both tested configurations. This limited route
does not establish whole-game performance or identify CPU/GPU bottlenecks.
All eight launcher-run final native-resolution captures match byte-for-byte
within their distance configuration. This is endpoint agreement, not proof of
every intermediate frame or whole-mission fidelity.

Exact executable SHA-256 identities:

- Remaster: `a7454e3e8ff168f037bd6d49001f47bada8bd425202c738710fc462616bf7f5f`
- Alpha: `067087909f4224a196c6d16602eb3dbacc295edadc7d574ff051c90b7c177824`

## CPU-removal benchmark validation failure

The alpha launcher retains original CPU projection. A separate optimized,
unwatched timing host supplies the partial last-corner projection bypass. Its
object list differs from Remaster in one of 37,201 slots, the original geometry
producer. It remains a private development experiment.

Initial timing used executable `424c34f8f17568d67fc2eb5497bca7e463f5ee077e997089ca6c257f5fa6e03f`.
Later audit records show zero admissions and zero skipped iterations in both
reference and bypass modes. Its roughly 101 FPS/27% deficit therefore does **not**
measure active CPU removal. Those runs are retained and marked invalid for that
claim. The executable predates its current projection helper source (20:29
versus 20:37 on October 15); the source already has the updated `_ftol` ownership
check. This was a stale timing package, not a newly authored ownership repair.

A diagnostic rebuild proves 35,846 omitted iterations by frame 600. A subsequent
clean rebuild removes the added diagnostics and has source contents identical to
the retained current timing host, SHA-256
`da08a4064ce1c9a7f3c421d3929168cc299e449aca8e8cbb0016faa445c760d1`.
Its two 1800-frame validation runs show:

- Reference: 67,659 admitted/consumed draws, zero omitted iterations.
- Bypass: 67,412 admitted/consumed draws, 178,859 omitted iterations.
- First omission: frame 324. First original draw-count difference: frame 489,
  893 reference versus 897 bypass. Counts differ in 1216 frames overall.
- Final native-resolution images differ. The final command counts are 548
  reference versus 542 bypass.

The throughput pipeline stops at this failed matching-scene gate. The logged
validation runs are not quoted as an apples-to-apples FPS comparison. The timing
variant does not observe all flat-memory reads and grants no scratch-safety
credit. Its semantic fold is disabled, so it also supplies no semantic-hash proof.

An additional fully disabled timing-host control produces the same differing
endpoint pixels in one run and the reference endpoint in its repeat. Both
results are retained. This recurring upstream/state divergence remains
unattributed; it is not established as caused by omitted projection. The failure
matches the previously retained frame-489 pattern in the
[differences investigation](gpu-projection-differences-investigation-2026-10-15.md).
No passing-only promotion, fix or speedup is claimed.

## Evidence and execution boundary

Local evidence is retained at
`C:/Users/jcbla/MW34Benchmarks/geometry-20261016-r1/`: `results.json`,
`image-comparison.json`, `active-bypass-validation.json`,
`verified-build-identity.json`, both profile snapshots, scripts, run logs and
captures. The first D-drive working folder was preserved under `retained-d-drive`
after private copies exhausted free workspace space. Moving it recovered about
3.7 GB on D; no benchmark game copy or evidence was deleted. Original absolute
run paths in the relocated metadata retain their original spelling.

Fourteen timing attempts completed, including the stale and disabled diagnostic
controls; only the eight launcher runs form the valid comparison above. An alpha
startup rejected removal of its required world log and one private copy failed
for lack of disk space; neither is included in timing results. Original
pilot/registry/Mission 2 save hashes and both public launcher profiles remain
unchanged. No test game or build is left running.

This measures existing native geometry/presentation paths and exposes a stale
test package plus a recurring matching-scene failure. It advances no new
production CPU-removal boundary. Acceptance remains 131/144; no commit was made.
