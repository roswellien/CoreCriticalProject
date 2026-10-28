# M4 native parser-prefix review

The isolated x64 startup path now executes the original command-line parser's
real prefix on the frame produced by the preceding translated CALL. The current
gate stops before the first read of the uninitialized CRT lead-byte table. This
advances the [accepted command-line carry](m4-crt-commandline-carry-review.md).

The complete 436-byte parser translation is reused at O0 and O2. Its admitted
input is the actual worker command line beginning with an unquoted `D`. The CALL
at `0x7800BBF7` supplies ESP `0x2000182C`, return `0x7800BBFC` and arguments
`[0x33000000, 0, 0, 0x20001850, 0x2000184C]`. The prefix visits 23 instruction
addresses, completes 16 source memory accesses, saves four registers and leaves
both sizing count locals equal to one. At `0x7800BCE6`, the next required byte is
`0x78037A25`. The gate refuses before that load; it leaves the table unread.

The root ran 48 ordinary sequences and 24 fault sequences in fresh native
workers. Its separate original-BEFORE/source model passed 146,113 comparisons
and rejected 2,648 selected semantic corruptions. It checks all 3,504 State
bytes, 512 FX bytes, 16 existing mappings, 1,587 source bytes, owned command-line
bytes and the prior and new ledgers. The independent source/ABI audit and the
separate audit of this model passed. The root model covers the ordinary rows;
it does not claim a full independent model of the 24 fault sequences.

Independently authored compiled fixtures exercise six carried inputs, twelve
authored controls and 48 further controls per optimization. They check partial
stores, malformed tokens, stale side bindings, observer exceptions, first-fault
ownership, terminal cleanup, poisoned retry and actual host LastError/FP
preservation. The compiled corpus passed 132 scenarios and 4,886 assertions.
Its hardware review requires 264 actual caller pairs, 548 unchanged semantic
corruption refusals and 14 additional inventory/request refusals. The final
compiled and hardware receipts below govern admission.
The root executed the prepared fixtures after the review agent's service error.
Fixture corrections addressed command-line quoting, an intentionally changed
runtime PC and parent-owned diagnostics; they changed no frozen parser code.

The captured evidence uses complete archives with explicit per-case requests,
phase inventories, logical extents and SHA hashes. Flat files remain preserved.
The [bundle transport review](m4-review-bundles-results.md) explains the separate
performance measurement and its limits.

Current evidence:

- [Root native execution](../../reports/m4-crt-parser-prefix/root-execution-r1/report.json)
- [Original-BEFORE/source model](../../reports/m4-crt-parser-prefix/root-observer-r1/report.json)
- [Source and ABI audit](../../reports/m4-crt-parser-prefix/source-contract-r2/report.json)
- [Independent model audit](../../reports/m4-crt-parser-prefix/independent-root-model-audit-r1/report.json)
- [Compiled fixture review](../../reports/m4-crt-parser-prefix/independent-compiled-r5-review/report.json)
- [Hardware and inventory review](../../reports/m4-crt-parser-prefix/independent-compiled-r5-hardware/report.json)
- [Final current dependency seal](../../reports/m4-crt-parser-prefix/root-acceptance-r1/report.json)

The current gate grants no parser RET, completed sizing, argc/argv/environment,
allocator, locale initialization, original DLL attachment, complete CRT, native
game window or full M4 credit. Selected initializer coverage stays 27 of 144.
Quoted inputs and other initial bytes remain outside the executed domain.

The next executable dependency is initialized locale/lead-byte classification.
The [static locale recovery](../../tools/m4-crt-locale-workahead/README.md) identifies
the original default initialization path and its allocation/locking needs. File
zeros are not proof of initialization. After classification is established, the
next gates are full sizing, allocation, argument output and environment ownership.
