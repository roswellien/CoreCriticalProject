# Precompiled MW3 performance updates

The [October 23 call-routing successor](native-call-routing-performance-2026-10-22.md)
adds a measured 4.7% warmed Training throughput improvement with identical
captured output. Its precompiled update is now the latest Setup download;
the first update's results and delivery evidence below remain retained.

Owner direction, October 22: game/performance updates must be deliverable through
`.mw3update` packs. Launcher self-updates remain `.ccupdate`. The private
precompiled delivery exception in [legal policy](../legal.md) applies; original
executables, provider images, media and optional content packs are not included.

## Delivery through the existing launcher

`build_precompiled_update.py` packages a complete validated Runtime plus the
project-authored `InstallPrecompiledRuntime.exe`. It uses the already supported
`mw3-local-runtime-v1` native-preparer contract, requiring launcher 1.0.24. The
preparer copies existing compiled files; it does not regenerate any game code.
No new update protocol, compiler installation or launcher replacement is needed.

The builder checks complete runtime file closure and pins, package/input path
separation, package size limits and source stability. The launcher verifies the
RSA-PSS signature, original executable identity, package and all member hashes
before starting the native copier. The copier rejects input/output overlap and
reparse paths, writes only the new output and leaves the previous version alone.
The launcher then validates the complete runtime before atomically selecting it.
Existing rollback and monotonic sequence handling apply.

The `.mw3update` and companion ZIP have matching basenames. For a download that
browsers recognize, an outer ordinary ZIP may contain both. Extract that download
and import the `.mw3update` through Settings & Steam → Game Updates. Keep its
matching payload ZIP beside it. These remain manual updates; no feed is enabled.

## First performance changes

The baseline is the signed 1.0.24 split host. The candidate retains its large
texture archive repair and reuses the same translated native module. Rendering,
shaders, asset quality, lighting, shadow coverage and simulation cadence remain
unchanged. Replay and the performance monitor are disabled in the benchmark.
The execution boundary improved is native host-service bookkeeping.

The old host copied every service label into a string and periodically removed
200,000 records from a vector on the game thread. The selected replacement shares
stable host-owned labels, records annotations separately and reuses a bounded
ring of 400,000 entries. It retains the exact total count and chronological
recent history. Error diagnostics can materialize text on demand. A first
string-copy ring trial is retained privately; an early comparison of an
incomplete window was corrected before the final analysis.

Four complete visible Training runs use baseline/candidate/candidate/baseline
order, 3440×1440, FXAA, AF16, draw distance 1600, fog 1100 and full existing
lighting/shadows. Each has independent copied pilot/registry inputs, the same
script and a fixed 16.666667 ms diagnostic guest clock. Performance uses real
host presentation intervals, not the guest clock. Both candidate repeats are
faster than either baseline repeat. Peak FPS does not improve.

| Warm Training, frames 1200–2699, two runs each | Before | After |
| --- | ---: | ---: |
| Presented FPS | 88.40 | 90.00 |
| 1% low FPS | 40.89 | 44.79 |
| Mean frame interval | 11.31 ms | 11.11 ms |
| Worst interval | 28.21 ms | 26.74 ms |

This is about 1.8% higher throughput and 9.5% better 1% lows on this route.
Across frames 400–2699, including first-use work, averages are 79.23 → 81.04 FPS,
1% lows 33.77 → 36.35 FPS and worst intervals 63.80 → 53.40 ms. These are windows
of the same runs, not additional repetitions. All 2,800 non-timing world-counter
rows match across the four runs. This is a modest improvement; it does not
establish the user's target range across campaign or combat.

Startup preparation also had a concrete cache defect. The complete host profile,
including a fresh `launch_session_directory`, participated in the cache key.
Every normal launch therefore selected a different cache despite unchanged
textures/lighting. The corrected key uses selected resources, their producers,
host identity and the consumed catalog budget. Cached resource paths are merged
with fresh launch bindings so current controls, logs and settings remain current.
Admission, integrity checks, interrupted-attempt handling and writer exclusion
remain. First preparation after an update can still be necessary.

Private evidence is under `D:/MW3PerformanceUpdate-20261022-r1`. Service-history
fixtures pass 9,982 checks, startup-cache fixtures pass seven tests, and native
copy/package fixtures pass six tests. Formal acceptance remains 131/144. Captured
image, signed package installation/rollback and delivery results are recorded
below when complete; fixture success alone does not establish native gameplay.

## Completed delivery checks

The two dedicated fidelity runs match all 2,800 complete draw records and seven
3440×1440 captures byte for byte. The complete launcher fixture suite passes.
The actual signed update passes original verification, extraction, native copy,
complete runtime validation, activation and rollback in an isolated application
and data store. The prior runtime and monotonic update sequence are retained.
There is no code generation in this delivery path.

A real six-pack resource preparation test fully verifies 210 installed files in
15.20 seconds (this trial has no reusable verification receipts). Initial merged
resource preparation takes 128.59 seconds. A second call with a new session path
reuses those actual generated resources in 0.0097 seconds and retains the new
session's frame-log binding. These timings cover resource preparation only;
they are not total launcher startup or remote-machine measurements. Changed
content/producer/host identities and corrupted outputs still require preparation.

Signed host SHA-256:
`dee5e15e02ae18539a3f5b7a89f1e1abac55a2afd964717c28fb900351f85f0a`.
The development profile selects this host with a matching source snapshot and
native module pin; saved settings are unchanged. Frozen predecessor profiles,
sources, measurements and the first candidate remain available privately.

## Download

[MW3 performance update download](https://playtest.corecritical.dev/updates/mw3-performance-20261022-r1/MW3PerformanceUpdate.zip)
contains the signed `.mw3update`, its matching precompiled payload ZIP and
instructions. Both Setup catalogs list it alongside the 1.0.24 full installer.
The payload is 35,766,928 bytes, SHA-256
`305369ceeccd120c2f75c54e63ff034c8b91846de74b9aa74fae2fc878c04372`.
Complete R2 readbacks of wrapper, payload and signed metadata match the tested
local files. Sequence is 2026102301; no automatic update feed is configured.
