# First measured use of the new M4 workflow

The [workflow](m4-development-workflow.md) is now used by the filename root
composition rather than only a transport benchmark. Four roles produced the
implementation, independent compiled review, independent source/work-ahead
review and root BEFORE-only comparison. The strict bundle reader preserves
the complete evidence while reducing repeated small-file reads.

The representative benchmark measured about 10.7 times faster warm reads of
2,945 existing logical files. This is a repeated-read measurement. Legacy
capture conversion still requires inventory checks and multiple physical byte
passes, so it must be accounted for before predicting overall throughput.

The current [root receipts](../../reports/m4-crt-filename/root-execution-r2/report.json)
measure the actual stages separately:

| Stage | Seconds | Scope |
| --- | ---: | --- |
| O0 native execution | 20.03 | Verified successful stage adopted from the retained earlier attempt |
| O2 native execution | 6.71 | Fresh isolated worker |
| O0 bundle conversion | 52.93 | 39,090 retained flat files |
| O2 bundle conversion | 27.45 | 39,090 retained flat files |
| Root source comparison | 3.81 | Both bundles, all 72 sequences, units and final 736-input physical closure |

These stages had different cache and competing-I/O conditions. Their times
are observations, not an optimization ratio. The recovery took 92.06 seconds,
excluding the already completed O0 execution. The earlier conversion hit its
120-second limit under concurrent file work and is retained as failed. The
successful recovery reuses only the verified completed stage, then creates
fresh bundles with a bounded 600-second conversion limit.

The author submission spent 183.83 seconds merging/resolving/hashing 80,486
physical bindings. The new final root closure uses lexical normalized keys,
rejects conflicting duplicates and hashes each unique dependency once.
Its measured closure time is recorded in the final acceptance receipt.
This eliminates repeated path resolution without accepting size/mtime as proof.

The next throughput improvement should target capture emission: produce a
validated aggregate directly in new native writers so bulk capture avoids
tens of thousands of filesystem creates and later flat-to-bundle conversion.
That requires a separately reviewed writer/reader equivalence gate. For now,
keep heavy capture/conversion/hash phases staggered while source recovery,
ABI review and later dependency preparation run together. Additional agents
alone do not remove this measured file-handling cost.

The filename service gate advanced the actual compiled startup path to the
command-line producer dependency. It did not change the selected 27/144
initializer count or satisfy native startup/menu acceptance.
