# Heap creation review: real API return through mode-selector CALL

The previous gate reached the original `HeapCreate` import and stopped before
calling Windows. This gate admits the verified call frame, performs the actual
API call and lets the same translated provider body continue. It reaches the
genuine mode-selector CALL at `780039E3`, with target `78003A0C`, return word
`780039E8` and State ESP `20001854`.

The full x64 host HANDLE enters a private fixed ownership slot immediately when
`HeapCreate(0, 4096, 0)` returns, before throwing metadata or observer operations.
The independently chosen DWORD token `48450001` represents it within this
bounded one-heap experiment. The token is not a truncated host pointer. Private
owner and lifetime checks reject unknown, stale or closed token lookups.

The finite guest API return model checks the original return word at
`20001848`. It changes only low EAX to the token, ESP to `20001858` and EIP to
`780039D6`, preserving the other carried guest bytes, FX and Runtime CPU.
This declared ABI model does not establish the volatile-register or flag
outcomes of the unexecuted original x86 Windows API implementation.

The original source then executes TEST, MOV to `78035000`, the untaken zero
branch and CALL to the mode selector. Only translated MOV publishes the guest
token; the host performs no guest execution stores. The raw RW heap-global page
is the eighteenth mapping, with all seventeen earlier pages preserved. Its
file zeros supply source identity only. Mode global `78035004` is untouched.

The complete success prefix executes thirteen instruction addresses, ten
original-source memory accesses and three original CALLs. The checked API
return read is recorded separately. Executed source spans cover 48 bytes;
compiled and guarded source remains 84 bytes, with total carried source identity
1940 bytes. All 26 earlier AMD64 guest objects and both FDIV libraries remain
unchanged; no additional lifting or guest-object compilation is needed.

XOR at `780039BF` and TEST at `780039D6` each need a separate exact-site generated
AF representative zero. Neither supplies universal original-CPU AF equivalence.
TEST of the chosen nonzero token defines CF, PF, ZF, SF and OF as zero. MOV,
branch and CALL preserve the resulting flags through the mode boundary.

The real API result, complete 64-bit handle, token, errors and private registry
lifecycle are captured separately from guest state. Every checkpoint includes
the host ownership witness: unused before the experiment, acquired and live at
the source continuation, and closed after cleanup. Actual named API identities
and module hashes are checked before and after creation and destruction.
The real `HeapDestroy` input must equal the original full handle. Failure keeps
ownership until the safeguard attempts release; successful release revokes
token validity and prevents duplicate destruction. This host cleanup does not
execute the original CRT's later HeapDestroy instructions or clear guest globals.

The controlled NULL-result fixture skips the OS call under explicit injected
provenance. It executes the authentic TEST, zero store and branch to `7800CDDC`,
then stops before the cold body: twelve PCs, nine source accesses and no RET.
It validates that source branch without claiming an actual Windows allocation
failure. Other controls target registration rollback, return/read ordering,
publication faults, observer changes and exceptions, token authority and cleanup.

The root model derives ordinary guest expectations from the original captured
BEFORE state and original bytes, plus the declared typed actual API witness.
Candidate AFTER machine state is not an expected-state seed. Independent affine
review checks the same source effects separately. Compiled hostile fixtures
verify faults and cleanup; they do not supply a full causal source-model oracle.
The root claims no separate native rerun and zero fully modeled causal sequences.

The production O0 and O2 corpus passed 72 scenarios: 48 ordinary sequences and
24 controlled faults. It made 70 actual HeapCreate calls and successfully
destroyed all 70 returned full handles. The two injected NULL cases skipped
the OS call. The independent O0/O2 corpus passed 132 cases, 6,198 assertions
and 36 malformed/token denials, with another 70 actual create/release pairs.
Its closed inventory contains 72,083 logical records per level; production
contains 51,626 per level. Strict bundles verify the complete header, canonical
index, external digest and every entry without extracting flat captures.

The independent hardware/inventory review verified 264 writer/entry host-state
pairs, 548 semantic corruption denials and 27 inventory/request denials. The
ordinary root model checked all 31 checkpoints, whole State/FX/RuntimeCPU,
eighteen pages, source identities, source/API ledgers and the typed initial,
live and closed host ownership metadata. Its 116,986 checks include 1,620
selected semantic corruption denials. These model checks are distinct from
native execution and the independent compiled assertion count.

An additional separate fixture seeds nonzero host LastError immediately after
the real mainargs-before checkpoint and before heap scheduling. Its 12 cases
passed 652 assertions and 24 hardware pairs, with ten more actual create/release
pairs. Actual incoming and restored API error reads match the nonzero seed on
success, controlled NULL, after-create exception, cleanup skip and metadata
denial paths. It changes no candidate code, guest State or source memory. The
main corpus legitimately carries zero at that seam; the extra fixture isolates
error preservation instead of assigning an invented nonzero expectation to it.

The final independent affine audit made 9,024 comparisons across all 48
ordinary rows. It checked 1,488 complete checkpoint machine/ownership pairs
and 912 unused older/later job records, and additionally bound both measured
API targets to named exports in the hashed module image. It verifies the
delegated actual outcomes without claiming another native execution.

Current receipts are the [production execution](../../reports/m4-crt-heap-create/execution-r1/report.json),
[root model](../../reports/m4-crt-heap-create-root/observe-r3/report.json),
[independent review seal](../../reports/m4-crt-heap-create-review/sealed-r1/report.json),
[nonzero error fixture](../../reports/m4-crt-heap-create-review/caller-error-r2/report.json),
[final affine audit](../../reports/m4-crt-heap-create-root-audit/final-r1/report.json)
and [root acceptance](../../reports/m4-crt-heap-create-root/root-acceptance-r1/report.json).
The acceptance binds each separate proof domain, successful timed stages,
six strict capture archives and the complete current physical dependency
closure. Superseded model/checker/compile receipts remain history anchors;
they grant no current proof credit and their older flat closures are not reopened.

The mode selector body, mode publication, complete heap-initializer RET,
allocator result, locale completion, parser/argument/environment ownership,
original DLL attachment, standalone menus and complete M4 remain outside scope.
The next source work needs the selector's real stack-probe and OS-query outcomes
before mode-specific allocation can proceed.
