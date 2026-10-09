# Current M4 progress addendum — parser prefix

The native CRT startup experiment has advanced into the real command-line
parser. It now completes the first 16 source memory accesses and stops before
the required locale-table read at `0x7800BCE6`. Fresh native runs, a separate
original-BEFORE/source comparison and independent source/model audits pass.
See the [parser-prefix review](m4-crt-parser-prefix-review.md) for the admitted
domain, compiled receipts and remaining limits.

M4 remains active. Selected initializer coverage is **27 of 144**, leaving
117 roots outside that accepted sequence. This parser support work does not
increase that count. Complete CRT startup, the application initializer table,
a native window and menus remain unfinished.

The next CRT gate is initialized locale/lead-byte classification, followed by
complete parser sizing, allocation, argument output and environment ownership.
The [eight MFC provider-state prerequisites](m4-mfc-provider-state-workahead.md)
and [13 ordered application batches](m4-application-workahead.md) remain the
parallel application workahead.

The [capture transport improvement](m4-review-bundles-results.md) is now proven
against the previous frozen independent captures. Its matched warm semantic
reader workload is 2.32 times faster; archive packing remains a separate cost.
Source recovery and model review ran concurrently while large capture I/O was
staggered. This result does not establish a project-wide speedup or a completion
date.

This addendum preserves the earlier hash-bound milestone documents. The current
isolated tests execute native research workers; no original game or x86 provider
was launched for this batch.
