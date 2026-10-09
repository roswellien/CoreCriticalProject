# Current M4 progress addendum: default locale allocation prerequisite

The native startup experiment now executes the original default locale stub,
its `_setmbcp` entry and the lazy lock-25 prefix. The real source path requests
`malloc(24)`. The test stops before the allocator body with its authentic
argument and return word preserved. This resolves the next dependency boundary
behind the earlier parser's required lead-byte classification.

The bounded gate passed 72 production sequences and 132 independent compiled
scenarios. Root compared 48 ordinary runs against the original-BEFORE/source
model, including the complete State, FX and 17 mapped pages. The
[default locale review](m4-crt-locale-default-review-r2.md) records the source
scope, independent checks and remaining limits.

M4 remains active. Selected initializer coverage remains **27 of 144**, with
117 roots outside that accepted sequence. This prerequisite work does not add
initializer roots. Complete CRT startup, application initialization, a native
window and menus remain unfinished.

The next priority is authentic heap initialization: original attach calls the
heap initializer `780039BF`, which invokes `HeapCreate` and stores its real
handle. The allocator's raw heap globals are zero and supply no initialized
ownership. The [allocator source workahead](../tools/m4-crt-locale-allocation-recovery/README.md)
also identifies an optional bounded malloc prologue test stopping before its
first SEH-chain read. Locale completion needs allocation, the native
critical-section lifecycle and source codepage/table updates. Then we can resume complete parser sizing,
argument allocation/output and environment ownership. The existing MFC provider
state and application workahead remain useful parallel work.

This batch used isolated x64 research workers. The game was not launched.
Earlier accepted reports and milestone documents remain frozen; this addendum
provides the current status.
