# Current M4 progress addendum — 2026-10-08

M4 remains active. The x64 CRT startup experiment has advanced from an unresolved
command-line pointer load to the real command-line parser CALL. The ordinary
execution and original BEFORE/source comparisons pass. Independent compiled review
also passed 132 scenarios and 4,878 assertions, with 264 hardware caller pairs and
548 observer corruption refusals. See the [command-line carry review](m4-crt-commandline-carry-review.md)
for evidence and the explicit scheduling limits.

Selected initializer coverage remains **27 of 144**, leaving 117 roots outside
that accepted sequence. This support-service work does not increase that count.
Full CRT startup, the application initializer table, a native window and menus
remain unfinished.

The next executable CRT gate is the real parser prefix, stopping before its first
locale-table read. The [static parser/locale recovery](../tools/m4-crt-locale-workahead/README.md)
locates that read at `0x7800BCE6` for the current measured command line. Full sizing
then needs initialized locale/lead-byte classification, followed by allocation,
argument output and environment ownership. Parallel
application recovery has now identified [eight MFC provider-state prerequisites](m4-mfc-provider-state-workahead.md),
including guest exception handling, TLS and allocation/critical-section-backed
state factories. This inventory supplies static evidence, with no initialized
MFC object or native application execution credit.

The [13 ordered application batches](m4-application-workahead.md) and
[measured evidence workflow](m4-development-workflow-results.md) remain the plan.
In this batch the fresh root native runs took 9.37 seconds for O0 and 9.27 for
O2; capture conversion took 38.08 and 38.76 seconds. The strengthened complete
oracle stage took 4.05 seconds. CPU/source work ran in parallel while capture
and large hash phases were staggered.

The independent fixture tree contains 130,138 physical artifacts. Flat-file I/O
still dominates its review and hashing time; bundling those fixture captures is a
future workflow improvement. Current acceptance physically hashes the complete
unique dependency union, with no metadata-only shortcut.

This new addendum preserves earlier accepted milestone documents and their
hash-bound historical state. It is the current update for the command-line
carry batch. No original game or x86 provider was executed during this batch.
