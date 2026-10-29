# Independent capture transport results

Independent hardware review can now read byte-verified capture archives while
retaining the previous semantic validator. This removes repeated small-file
opens from the measured review workload. It preserves every logical path,
extent and byte of the externally pinned old fixture capture manifest.

The O0 and O2 archives together contain 130,064 logical records. Publication
verified every original record against the frozen build manifest and compared
every archive byte with its flat source. The root separately reconstructed the
complete expected path/digest set and verified the unchanged validator bodies.
Neither this transport experiment nor its root check runs new native workers.

Both backends perform the same 264 actual hardware caller-pair checks and 548
semantic corruption refusals. Five alternating warm repetitions per backend
gave median reader-workload times of 0.09760 seconds for the strict flat reader
and 0.04201 seconds for the retained strict bundle reader: **2.32 times faster**.
Another 37 transport/inventory corruption controls refused as expected.

The scope of that ratio is the repeated warm semantic reader workload. Fresh
aggregate/inventory verification took 4.03 seconds. Packing the two archives
took 170.79 seconds, and the additional flat/archive comparison took 15.10
seconds. Packing still reads the flat captures. This is not an OS cold-cache or
whole-project speedup measurement. A direct native aggregate writer is future
work and has not been implemented.

Current manifests bind the sealed archive bytes plus all non-capture physical
sources, translated objects, libraries, tools, headers and receipts. They use
full byte hashes and strict logical readers, with no metadata-only cache or
extraction. The preserved flat capture manifest is a historical authority;
its hundreds of thousands of paths are not expanded again as current physical
dependencies after complete archive equivalence is established.

Evidence:

- [Complete archive equivalence](../../reports/m4-review-bundles/preparation-r1/report.json)
- [Matched transport review and timings](../../reports/m4-review-bundles/review-r1/report.json)
- [Independent root verification](../../reports/m4-review-bundles/root-check-r1/report.json)

The new [parser-prefix review](m4-crt-parser-prefix-review.md) uses this transport
with its own independently specified request and phase inventories. Archive
integrity alone grants no instruction-equivalence or gameplay credit.
