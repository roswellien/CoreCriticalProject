# Actual native filename service and startup continuation

The final additive `preparation-r8/build-r7` gate resolves the actual
`KERNEL32!GetModuleFileNameA` call at provider PC `7800BBD0`, IAT `7802E018`.
Its original arguments are NULL module, guest buffer `7803B3F0` and capacity 260.
The API obtains the actual AMD64 research worker's filename; it does not
fabricate the admitted x86 game's module path or claim full x86 API behavior.

The service seeds all 260 native scratch bytes from owned guest memory and
records the immediate real result/LastError. It validates actual named export,
forwarded executable image owner and worker module identity before/after,
then transfers the entire scratch through checked GuestMemory before publishing
EAX, ESP `20001844` and PC `7800BBD6`. Other software State/FX fields remain the
declared representative policy. The enclosing host caller's LastError and
floating-point state survive normal and exceptional exits.

The next literal instruction is `MOV EAX,[78037174]`. That `_acmdln` producer
has not been connected to this persistent runtime. Execution therefore refuses
BEFORE this load with `unresolved_translation`, preserving all carried storage
and terminal cleanup. Filename success supplies no argc/argv/environment,
mainargs/builder RET, DLL attach, main-table callback or native menu credit.

## Evidence

- [Author submission](../../reports/m4-crt-filename/author-submission-r2/report.json):
  48 positive sequences, 24 causal sequences, eight real capacity units,
  146 ordinary host pairs and 616 selected observer denials.
- [Independent source and build audit](../../reports/m4-crt-filename/independent-contract-r2/report.json):
  exact compiler/header/AMD64 COFF association and private admission/return
  closure. Twelve original guest objects, two FDIV libraries and eleven
  ancestor components remain unchanged.
- [Root execution](../../reports/m4-crt-filename/root-execution-r2/report.json) and
  [independent BEFORE model](../../reports/m4-crt-filename/root-observer-r3/report.json):
  72 complete sequences, 107,306 checks, State3504/FX512, sixteen pages and
  1,140 source bytes. The model reads two strict bundles containing 78,180
  logical files. Its 952 shared-validator rejections cover 680 distinct
  selected byte locations. Actual OS output is an explicit service witness;
  native guest AFTER storage never seeds architectural expectations.
- [Compiled review](../../reports/m4-crt-filename/independent-compiled-review-r1/report.json):
  90 actual O0/O2 scenarios, 3,012 assertions, 28 malformed-token denials and
  180 deliberately populated direct hardware boundary pairs.
  The [independent hardware observer](../../reports/m4-crt-filename/independent-compiled-observer-r1/report.json)
  rejects 548 meaningful corruptions and checks raw80/legacy tags.
- [Root-model audit](../../reports/m4-crt-filename/independent-root-model-audit-r1/report.json)
  separately verifies source independence, captured schemas, stage association,
  full partial effects and the explicitly reused successful O0 execution.
- [Final root acceptance](../../reports/m4-crt-filename/root-acceptance-r1/report.json)
  merges only current final dependencies and performs complete physical rehashing.

Review repaired mutable actual-witness/progress fields, stale side-binding
attribution and a mutable public frame that could publish the wrong return ESP.
The final adapter checks a private admitted frame and exact lifecycle at every
observer point, private post-RET State/FX, and literal source integrity before
the next read. Exceptions after API, checked buffer copy and RET retain their
real partial effects; they cannot receive later completion credit. Superseded
builds and failed fixture/transport/model attempts remain available.

The hardware domain remains directed and bounded. Full original Windows
callee volatile CPU/flag equality, guest TEB LastError publication, arbitrary
SEH dispatch and arbitrary concurrency are unproven. The selected initializer
gate remains 27/144; full native CRT/application/menu execution remains open.
The preservation snapshot begins after admission hook1; denial of arbitrary
hook1 GPR/FX mutations is outside this directed proof domain.

## Next batch

Connect the already reviewed [native command-line writer](m4-crt-commandline-native-review.md)
on the same persistent runtime, with explicit borrowed mappings and an owned
guest buffer. Its actual 11-byte source at `7800188C` calls GetCommandLineA and
stores EAX at `78037174`; its authored stop at `78001897` supplies no original
RET or full DllMain proof. Reuse the measured OS-byte/ownership contract while
preserving incoming State, existing mappings and both raw IATs. Prove the
producer-to-consumer load before admitting later locale/parser, allocator,
environment and main-table paths. Keep MFC provider-state and archive-reader
contracts moving in parallel using the [application work map](m4-application-workahead.md).
