# M4 evidence pipeline

This toolkit provides capture transport, conflict-checked manifest merging,
and command timing for new M4 work. It supplies no game execution or semantic
equivalence by itself. Accepted flat captures and their original observers stay
unchanged. New observers explicitly opt into the bundle reader.

```powershell
C:/Python314/python.exe tools/m4-pipeline/capture_bundle.py pack SOURCE reports/NEW/capture.mwb
C:/Python314/python.exe tools/m4-pipeline/capture_bundle.py verify reports/NEW/capture.mwb --sha256 EXTERNAL_SHA256
C:/Python314/python.exe tools/m4-pipeline/benchmark.py reports/m4-pipeline/NEW-BENCHMARK
```

Use a fresh output name on every attempt. Packing requires a private, quiescent
input tree: concurrent input writers are unsupported. The writer hashes the
inventory, streams and rechecks it, verifies the completed bundle, then publishes
without replacing an existing file. No archive extraction is performed.

`CaptureBundle(path, expected_sha256)` opens an externally pinned bundle,
verifies its whole-file/index/entry hashes and canonical contiguous layout,
and exposes `names()`, `exists(name)` and `read_bytes(name)`. Names are normalized
relative POSIX paths; traversal, Windows reserved names, reparse points and
case collisions are refused. Windows handles deny concurrent write/delete
sharing. A bundle carries the same logical bytes as the flat capture.

`merge_manifests(paths)` merges `{"files": {absolute_path: sha256}}` manifests
using lexical Windows path normalization and rejects conflicting duplicates.
`verify_manifest(files)` reads and hashes each unique dependency. It does not
accept file size or modification time as a content proof. Manifests with other
schemas require an explicit adapter.

`run_stage(argv, fresh_output, timeout_seconds=60, required_outputs=(),
cwd=None, inputs=())` executes a direct argument vector, captures binary logs,
records monotonic elapsed time and pins explicit inputs, executable, runner and
outputs before/after. Fresh required outputs must be distinct, including Windows
case/slash aliases. `verify_stage(directory, external_receipt_sha256)` validates
the receipt, status, timing and physical provenance. Nonzero exit, timeout,
missing output, input mutation or launch failure cannot receive success credit.
Timeout handling terminates the direct child; descendant-tree termination and
process file-open attestation are not claimed. Environment variables are not
dumped into evidence.

The final independent review is
`reports/m4-pipeline-review/review-r4/report.json`: 9,161 checks, including
70 internally rehashed malformed bundles, 2,945 exact frozen-file roundtrips,
manifest tampering, five real Python stage outcomes and failed-publication
controls. Actual junction creation was unavailable in this environment;
controlled reparse predicates and ancestor walks were checked separately.

The final local benchmark is
`reports/m4-pipeline/benchmark-r3/report.json`. Four representative frozen
O0/O2 positive/early-fault/late-fault rows contain 2,945 logical files.
Three alternating warm-read passes measured about 10.7 times faster repeated
bundle reading. Packing and full verification at open are reported separately.
This is a transport measurement, not a compilation or whole-project speedup.
