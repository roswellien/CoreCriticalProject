# Bounded native argument startup prefix

The compiled game CRT entry now executes its real `__getmainargs` call and the
ordinary argument-builder prefix up to the required filename API. All bounded
reviews and the final [root acceptance seal](../reports/m4-crt-mainargs/root-acceptance-r1/report.json)
pass. The seal physically rechecks 453,287 dependency bindings. M4 remains active at **27 of 144 nonzero initializer roots, with
117 remaining**.

Game CALL `0x5AC468` / IAT `0x5BB514` reaches staged MSVCRT `__getmainargs`
at `0x7800BA5E`. The actual wildcard and startupinfo DWORDs are zero. The
provider performs its real startup-mode store, then CALL `0x7800BA99` enters
the ordinary builder at `0x7800BBBC`, with return `0x7800BA9E`. Complete literal
66-byte and 140-byte bodies are statically compiled into O0/O2 objects; the
admitted execution covers **19 source PCs, 16 accesses and four typed routes**.

The builder pushes null module, guest buffer `0x7803B3F0`, and length 260. Its
actual CALL at `0x7800BBD0` reads the uniquely owned provider
`KERNEL32.dll!GetModuleFileNameA` slot `0x7802E018`, raw value `0x343B0`, and
writes return `0x7800BBD6` before publishing ESP/PC. The typed supervisor then
throws a public unresolved-import Fault. This deterministic refusal occurs
before API execution or the following command-line load. No filename result,
argc/argv/environment output, provider RET, main-table callback or menu execution
is supplied by this gate.

The same Runtime, State3504, separate FX512 and sixteen complete owned pages
persist through the accepted FDIV/math-error/control/first-null prefix. No page
is mapped again or reseeded. Every checkpoint retains 1,140 source identity
bytes. The provider's internal CALL uses a strict current-owner supervisor on
the same State; its import authority comes from the exact provider PE. Generic
Runtime registration covers the game IAT only. RuntimeCPU remains at that game
service frame while compiled State carries the deeper source frames. Nine of
eleven Runtime records complete; the root and mainargs service remain incomplete.

The [root execution](../reports/m4-crt-mainargs/root-execution-r1/execution.json)
and [BEFORE-only source proof](../reports/m4-crt-mainargs/root-model-r2/report.json)
pass **48 positives and 120 causal cases** across O0/O2. Of the causal cases,
118 have architectural source predictions; two preserve the earlier mode43
artifact-specific observer contract and receive no generalized x86/noalias
equivalence credit. Whole-State/page/FX carry, source effects, first faults and
terminal retries pass, with **330 ordinary host boundary pairs and 88,806
corruption denials**. An [independent root-model audit](../reports/m4-crt-mainargs/independent-root-model-audit-r2/report.json)
confirms the scope and source ordering.

The [independent source/build review](../reports/m4-crt-mainargs/independent-contract-r4/report.json)
verifies complete source bodies, reversible ABI naming, unchanged preceding
objects and Session, strict typed dispatch, actual header/COFF/unwind and link
associations. The [compiled review](../reports/m4-crt-mainargs/independent-compiled-review-r1/report.json)
passes **2,078 checks over 64 scenarios, 128 rich host pairs and 420 malformed
token denials**. Its [observer controls](../reports/m4-crt-mainargs/independent-compiled-observer-controls-r1/report.json)
reject **548 corruptions**. The [data prerequisite audit](../reports/m4-crt-mainargs/independent-data-r2/report.json)
keeps initialized argc/argv/environment production separate from raw file zeros.
The [author observer](../reports/m4-crt-mainargs/author-observer-r1/report.json)
and [author submission](../reports/m4-crt-mainargs/author-submission-r1/report.json)
provide additional full-buffer checks and physical bindings.

The guest FP domain remains the preceding twelve masked, empty-stack inputs.
Independent rich caller fixtures exercise populated x87 storage and legacy
metadata, TOP/live depths, MXCSR and preserved ABI XMM6–15 across the encompassing
exception boundary; arbitrary guest FP traps or volatile XMM0–5 equality are
not admitted. Exact staged source selection does not prove the provider chosen
by an ordinary running game. Tool, object, include and SDK library-search
identities are bound; exhaustive SDK linker-file-open or historical process
attestation is not asserted. Failed preparations and review revisions remain
preserved, and prior accepted tool artifacts are unchanged.

Next implement the filename service with native-host module identity and checked
guest buffer effects. Carry the reviewed command-line producer into these
existing mappings without duplicate mappings or reseeding, then close
locale/parser, allocator, argv ownership and environment contracts before
successful provider return and the main initializer table. The ordinary game
does not need to run for this isolated native/source/host review. Native menus
and Training remain later M4/M5 work. See the [root replay recipe](../tools/m4-crt-mainargs-root/README.md).
