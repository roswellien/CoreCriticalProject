# Capture-sharing pilot

Updated 2026-10-09. The additive shared-record format passed its [sealed pilot](../reports/m4-capture-shared/seal-r1/report.json) and [independent review](../reports/m4-fs-review/capture-pilot-r1/report.json). Production startup evidence still uses the existing canonical format.

The pilot keeps every logical name and complete byte vector while storing equal payloads once within each part. Equality requires full bytes after hash/size matching. A new format marker, canonical blob/reference index, immutable owned payloads, atomic publication and held Windows read handles make sharing explicit and verifiable. The existing reader rejects the new format.

Validation includes 32,000 exact logical-record comparisons, 120 measured hardware pairs, 54 writer refusals, 63 malformed-format refusals and 12 held-file mutation refusals. The independent review also rechecks 120,660,218 bytes and adds ten malformed-count refusals. Hardware scope covers the measured x87 state and 28-byte environment, MXCSR, nonvolatile XMM registers, ABI-cleared direction flag and LastError. Volatile XMM equality and incoming DF=1 are excluded.

One retained-subset benchmark measured 93.36% smaller bundles. O2 writing took 0.2252 to 0.0845 seconds; reader startup took 0.3373 to 0.0950 seconds; three access passes took 0.2688 to 0.1903 seconds. Peak working set fell from 78.6 to 37.6 MB. These are one uncontrolled-cache trial on that subset, not a measured full startup or investigation speedup. See the [benchmark receipt](../reports/m4-capture-shared/benchmark-r2/report.json) and [reader measurements](../reports/m4-capture-shared/reader-measure-r1/report.json).

Adoption still requires an explicit adapter for existing consumers: their metadata APIs and private extent lookups differ from the pilot. Run unchanged source, paired, ownership and fault consumers on an identical retained capture before using sharing for new acceptance evidence. Preserve canonical evidence and failed attempts. Part bounds apply to unique physical payload, with separate limits for logical records and index size.
