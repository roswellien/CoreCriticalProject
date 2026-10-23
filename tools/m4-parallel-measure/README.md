# Ordered parallel whole-file measurement

`ordered_pool.ordered_map` runs only the unchanged per-file measurement (stat, full
SHA-256, stat, compare) in worker threads. SQLite access, registration, counters,
progress and the pre-open row checks stay in the calling thread, in input order, and
the earliest failure in row order is the one reported (same as the serial loops).

Parallel-capable versioned copies (each differs from its predecessor only in the
measurement loop and an optional `mapper` argument; `mapper=None` is the old serial
behaviour):

| New file | Predecessor | Used by |
| --- | --- | --- |
| `tools/m4-controls-terminal-composite/expand_composite_inventory_v4.py` | v3 | reviewer v5, acceptance v5 |
| `tools/m4-138-controls-review/expand_proof_inventory_v2.py` | v1 | acceptance v5 |
| `tools/m4-138-controls-review/acceptance138_storage_v3.py` | storage v2 (`Union.verify`) | acceptance v5 |
| `tools/m4-controls-strict-bridge/acceptance138_v5.py` | acceptance v4 (exact byte inverse checked) | strict acceptance |
| `tools/m4-controls-terminal-composite/review_completed_composite_v5.py` | reviewer v4 (exact byte inverse checked) | any future reviewer rerun |

`check_parallel_v1.py` (receipt `reports/m4-parallel-measure/check-r1`) runs serial and
parallel paths on synthetic inventories built to the real schemas: identical
registration order/results and refusals for corrupt hashes, capture suffixes and
mixed failures, plus pool ordering and failure-priority controls (12 controls). Real
composite-inventory files (average about 4 KB) measured 948 files/s serial and 5,019
files/s with 8 threads through `Union.verify`, while another reviewer was running.
Processes were no faster than threads: per-file filesystem cost is the ceiling.
`MW34_MEASURE_WORKERS` overrides the default of 8.

GPU offload was evaluated and rejected for this workload: SHA-256 runs at about
2.4 GB/s on one core, so hashing 4 KB files uses under 1% of a core even at 5,000
files/s; the time is spent in open/stat/read syscalls, which a GPU cannot perform.

Admission note: acceptance v5 and reviewer v5 load the pool and new expanders by
exact identity; the independent configuration review (or a reviewer admission) must
pin those files before they run.
