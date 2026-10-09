# M4: native startup and menus

Status: active, updated 2026-10-08. M1–M3 retain their accepted scopes and frozen
technical evidence. M4 is complete only when a project-built x64 executable
loads admitted user data, initializes required services, presents correct
menus and responds to input. Required file/configuration, graphics, input and
audio dependencies need explicit implementations; unresolved paths must fail
visibly. An image loader or a passing initializer alone cannot satisfy M4.

The [complete CRT entry preparation](m4-crt-entry-preparation.md) now produces
native x64 objects for all eleven recovered entry/helper roots, covering 118
ordinary-entry instructions and 148 instructions across the separate paths.
The [three-service entry prefix](m4-crt-entry-three-service-prefix.md) now
executes 26 game instructions at O0/O2, installs its guest exception frame
and returns through the first three measured CRT services. It stops explicitly
at the unconnected initialized FDIV data import; guest exception dispatch and
complete CRT integration remain open. The [FDIV writer](m4-crt-fdiv-native.md)
passes independent native source/state/API/failure review. An isolated original
x86 capture has also completed 48 runs, with direct and debugger observations
kept separate. The [bounded FDIV replay and entry review](m4-fdiv-replay-and-entry-prerequisites.md) now passes for the
retained direct-before corpus, with original XMM0 and real-stack differences
preserved. The [initialized-data entry composition](m4-crt-entry-data-review.md)
now connects the actual FDIV producer to compiled CRT entry without reseeding.
It consumes the data and executes the translated RET helper. The later
[actual math-error caller composition](m4-crt-entry-matherr-review.md) now
completes `__setusermatherr` (`0x5AC428`, owning IAT `0x5BB50C`) and reaches the
required control wrapper (`0x5AC431` -> `0x5AC5A0`). Its 48 positive / 48 causal
cases pass independent source review. Rich caller fixtures exposed and repaired
legacy FP metadata loss across C++ failure handling; 68 deliberately populated
hardware boundary pairs pass. Original full entry and remaining CRT/SEH
dependencies stay open.
The later [actual control composition](m4-crt-entry-control-review.md) completes
the game wrapper, thunk and complete `_controlfp` provider on the same fourteen
pages, State and Runtime FX. Its 48 positive / 72 causal cases and 144 rich
hardware caller boundary pairs pass independent review. Entry now reaches CALL
`0x5AC440` -> `_initterm` thunk `0x5AC598`, after pushing interval bounds
`0x5E024C` / `0x5E0248`. That first interval contains only a null pointer;
the actual main initializer-table caller remains a later dependency.
The [actual first-null composition](m4-crt-entry-initterm-review.md) now executes
that thunk and complete provider, reads the real table cell and returns.
Compiled game continuation sets up four argument pointers and the wildcard
flag, then stops at
`__getmainargs`, source `0x5AC468` / IAT `0x5BB514`. Its 48 positive / 96 fault
cases pass independent review across State3504, FX512, sixteen captured pages
and 934 source bytes. Independent compiled review adds 124 rich host pairs;
two injected observer mutations have separately reviewed O0/O2 operand
contracts and do not receive architectural source-equivalence credit.

The new [bounded mainargs composition](m4-crt-entry-mainargs-review.md) now
connects game CALL `0x5AC468` to the complete compiled 66-byte `__getmainargs`
export at `0x7800BA5E`, then the real ordinary builder at `0x7800BBBC`.
Its full 140-byte builder is compiled; execution covers nineteen source PCs,
sixteen accesses and four typed routes before the actual filename import CALL
at `0x7800BBD0` / IAT `0x7802E018`. The real arguments are null module,
buffer `0x7803B3F0` and length 260. It deterministically refuses before API
execution, keeping complete State3504/FX512, sixteen pages and 1,140 source
identity bytes. The 48 positives and 120 causal cases pass review: 118 causal
cases have source predictions and two retain the prior mode43 artifact scope.
Root review checks 330 ordinary host pairs and 88,806 corruption denials;
independent compiled review adds 2,078 checks, 64 scenarios, 128 rich host pairs,
420 malformed-token denials and 548 observer denials. The final
[root seal](../reports/m4-crt-mainargs/root-acceptance-r1/report.json) passes.
No argc/argv/environment outputs, provider RET, main-table callback or native
menu execution are credited.

The later [actual filename service](m4-crt-filename-review.md) executes the
named native API, publishes the checked guest buffer and stdcall return, then
refuses before `MOV EAX,[0x78037174]` at `0x7800BBD6`. All 48 normal / 24 causal
sequences and eight API units pass the original-BEFORE source model; independent
compiled review adds 90 scenarios and 180 rich host pairs. The
[new development workflow](m4-development-workflow.md) supplies reviewed
bundles and stage timings, and the [application work map](m4-application-workahead.md)
orders 13 batches. These additions do not increase the selected initializer
count or complete startup/menu behavior.

The shared numeric-max candidate exposed a caller floating-point state defect,
preserved in the [integration limitations](m4-fp-numeric-max-integration-limits.md).
A [canonical component repair](m4-fp-numeric-max-canonical-acceptance.md) is now
accepted after independent raw checks across 57,024 native phases and compiled
failure/ownership/admission review. It restores caller numerical state, rejects
non-Boolean shadow flags and handles the separately tested incoming PE/C1
domain. The [selected 27-root joint gate](m4-joint-startup27-review.md) now passes
actual preceding-root carry, original/native comparisons, provider checkpoints
and independent terminal failure review. Its optimized caller legacy ENV
failure and additive host-boundary repair are preserved. The joint count is
27 of 144 nonzero roots; 117 remain outside the selected gate.

## Recovered startup boundary

The admitted MW3 1.2 executable has SHA-256
`95bc2c114c9b2e5c5ada8e40ca78cc79470f862e45313ffad0d1e8e6d4d916bf`.
Its entry at `0x5AC3A0` installs an x86 FS-relative exception frame, performs
CRT initialization and calls a four-argument wrapper at `0x5AE390`. That
wrapper reaches the MFC42 ordinal-1576 import through `0x5AE3F4` and IAT slot
`0x5BB438`. Complete startup requires this environment and its actual
application callbacks; the earlier isolated-function context cannot supply it.

The CRT initializer interval `[0x5E0000,0x5E0244)` contains 144 nonzero
function-pointer roots and null entries. Each required root must be recovered,
implemented and routed with the correct ABI and initialization order. A
separate initializer interval is empty. The preserved
[startup recovery](../reports/m4-startup/recovery/report.json) records exact
image bytes, CFGs, scopes, table entries, direct calls and unresolved targets.
Recovered CFG call fallthroughs conservatively retain code after CRT
`exit`/`_exit` calls until their service contracts establish nonreturning
behavior. These static edges and SEH handler roots are separate from actual
execution coverage.

Static recovery links initializer slot `0x5E010C` to construction of the
application object at `0x608C88`, its vtable at `0x5C3F80`, and these callback
candidates:

| Vtable slot | Target | Evidence and remaining work |
| --- | --- | --- |
| `+0x58` | `0x480000` | Application initialization candidate: 236 branch-reachable instructions and 51 call sites. Required callees, failure paths and service contracts remain unresolved. |
| `+0x5C` | `0x58FD70` | Run-loop candidate: 261 branch-reachable instructions and 26 call sites. Message, callback, timing and termination behavior require recovery. |
| `+0x70` | `0x47FA10` | Exit candidate: 37 branch-reachable instructions and 13 call sites. Cleanup and object lifetimes require recovery. |
| `+0x8C` | `0x5ABE82` | MFC import thunk; provider-specific semantics remain required. |

These role labels are interpretations of exact static linkage, rather than
observed runtime calls. The staged MFC42 provider and current system provider
have different exact identities. The staged provider demonstrates how its
constructor stores the application object in module state and how its startup
entry retrieves that object before virtual dispatch. The actual provider used
by a running game has not been observed. Ordinal resolution alone does not
establish an API contract or grant execution admission. See the
[application linkage](../reports/m4-startup/services/application-chain-report.json).

The image contains 47 resource leaves, including three menu templates and
38 dialogs. One conditional application/frame path reaches `LoadMenuA` with
resource ID 147 and then `SetMenu`; a linked frame message table has 82 entries.
Other resources include debug/editor labels, so their presence does not prove
the game's retail frontend route. Correct native menus require the reached
creation, handler and renderer paths, plus original reference observations.
See the [menu/resource linkage](../reports/m4-startup/services/menu-resource-links.json).

Further recovery identifies a conditional retail path: the application service
callback at `0x480570` removes resource menu 147 and initializes the game
services. The run loop dispatches the startup state, then its default next
state reaches `0x486990` and the menu composite constructor `0x486260`.
That constructor loads `dialog.zrd/MAINMENU` and binds Instant Action, New
Campaign, Multiplayer, Training, Options, Credits and Quit callbacks. These
are exact static links, with virtual receivers and service execution still
requiring observation. The [retail handoff](../reports/m4-application-closure/handoff.json)
records the path, critical failure branches and remaining dynamic sites.
Menu 147 is an intermediate Windows frame resource, not sufficient proof of
the retail frontend.

## First implementation gates

The first foundation is a separately built native x64 image host in
`tools/m4-startup`. It admits the exact image before creating owned checked
guest storage. Preferred guest addresses remain 32-bit values; host backing
uses ordinary owned storage. Headers and sections have reviewed page-rounded
extents, raw padding, zero fill and guest permissions. Unsupported directories,
structural inconsistencies and malformed imports reject before a loaded image
is published. The resource directory span is checked; the loader does not yet
interpret resource trees for native UI creation.

All 474 imports remain unresolved, with original IAT dwords preserved. No
original code is executed, no host function pointers enter guest structures,
and no familiar API gets an invented success result. `--inspect-image` reports
the mapped image. `--image` stops at the unimplemented startup address with a
reason and exit code 3. This diagnostic executable does not display menus.

The native foundation's five regions and all 6,246,400 mapped bytes match both
an independent file model and Windows' passive image view. The latter uses
`SEC_IMAGE_NO_EXECUTE`, does not run original instructions or resolve imports,
and is a separate reference observation. The
[PE specification](https://learn.microsoft.com/en-us/windows/win32/debug/pe-format)
defines the structures; Microsoft's
[file-mapping documentation](https://learn.microsoft.com/en-us/windows/win32/api/winbase/nf-winbase-createfilemappinga)
defines the passive image option. A passive view does not reproduce CRT/DLL
initialization or a running process's patched IAT.

The first accepted actual-code gate is the complete initializer wrapper at `0x410910`
and loop body at `0x410920`. The real startup-table pointer at `0x5E0058`
reaches this operation. It clears 167 byte fields at stride 20 in a reviewed
zero-filled data page, preserves surrounding storage and returns. The first
native implementation comes from the exact static lift. It passes 5,320
original cases and 10,640 native O0/O2 comparisons with zero defined differences,
including full defined flags, memory, protected native State, admitted
noninteger state, actual checked events and all 66 causal admission controls.
Independent source/raw-record review and a separate root oracle pass. See the
[initializer measurement and repair record](m4-initializer-experiment.md).
This gate remains separate from execution of all 144 initializers.

The complete adjacent initializer and its two callees now pass the
[connected graph gate](../reports/m4-initializer-chain/independent-review/r6/report.json):
10,640 original records and 21,280 native comparisons. The fourteen other
import-free integer roots pass their
[independent batch review](../reports/m4-integer-startup/independent-review/r3/report.json):
8,512 original records and 17,024 native comparisons. A separately reviewed
[fresh r9 integration](m4-integer-integration-r9-contract.md) runs all sixteen
selected table targets in original order on one persistent image/State.
Its final CPU/page checks and seed-retention controls do not replace the
component gates' complete raw State/FP/events observations.

A new shared [startup context and routing runtime](m4-runtime-contract.md)
retains the admitted image, checked stack/arena, recovered FS fields and a
persistent complete 3,504-byte State. Its authored routing/order controls and
actual-image denials pass independent replay; no game translation is registered
in that diagnostic host. Its typed failures and propagated memory exceptions
cannot become successful calls. A callback that catches a raw GuestMemory
exception requires separate adapter fault-propagation proof; broader checked
memory tracking remains required before arbitrary callback admission.

The all-initializer [workload inventory](../reports/m4-initializer-inventory/r1/report.json)
covers 145 slots/144 nonzero roots and 363 direct graph nodes. Thirteen table
roots reach floating-point operations and 31 reach FS-relative operations.
Indirect/callback/SEH/service closure remains separate. Original-only
[FP startup captures](m4-fp-startup-research.md) now expose required operations
and the distinction between actual legacy ENV metadata and FX metadata;
their native equivalence remains open.

The [first compiled FP experiment](m4-fp-first-experiment.md) now has 2,016
actual original directed records and 4,032 native comparisons with zero
observed differences after retaining and repairing two status defects.
Final independent review passes; other required FP routines,
incoming live-stack/state domains and connected startup order remain open.
The [two additional FP roots](../reports/m4-fp-simple-batch/independent-review-r1/report.json)
pass 5,952 original / 11,904 native directed measurements and independent
review. The [four cosine roots](m4-fp-cosine-review.md) pass 6,144 original /
12,288 native directed measurements and
[independent review](../reports/m4-fp-transcendental/independent-review-r1/author-association-r1/report.json).
The square-root root passes 5,760 original / 11,520 native directed records and
independent review; the two remaining import-free trigonometric roots pass
9,024 original / 18,048 native directed records and independent review. All ten
import-free FP roots now have reviewed standalone native execution. A
[reviewed connected 26-root gate](m4-mixed-startup-review.md) matches 1,248
original / 2,496 native phases on one persistent image/State per sequence.
Its independent integration review passes. Another 118 roots remain outside
this connected gate. Three FP table roots reach imported services. One now has
an independently reviewed [standalone numeric-max closure](m4-fp-numeric-max-review.md):
14,688 original / 29,376 native records with actual checkpoints, complete State
and ordered memory/call observations. Its shared Runtime/MSVCP50 integration,
the other imported FP services and the full initializer ledger remain open.
An exhaustive [guest CW hardware observation](m4-crt-cw-research.md) captures
all 65,536 input words twice; its typed native State/FX transfer now passes
independent review across all 131,072 pairs at both optimization levels.
The complete [CRT control provider component](m4-crt-control-review.md) now
passes 3,264 original / 6,528 native observations and independent source-model
review within its measured empty-stack domain. The complete
[game wrapper/thunk/provider route](m4-crt-control-integration-review.md) now
passes independent connected review of 192 original / 384 native records through
unchanged r9. The [control-result carry gate](m4-crt-control-carry-review.md)
now independently matches 648 original / 1,296 native phases through the
selected 26 callbacks. It preserves resident State/RuntimeFX and passes 2,016
independent compiled checks. Broader startup integration remains open.
The [CRT command-line reference ownership gate](m4-crt-data-review.md) also
passes independent original writer and typed ownership review. The separate
[native command-line writer](m4-crt-commandline-native-review.md) passes
independent review of 384 original and 768 native records with actual OS bytes,
complete State/pages and 638 compiled checks. Its bounded writer stops before
complete DLL attach; broader production initialized data and `_adjust_fdiv`
remain unresolved. The latter's exact 204-instruction writer/dependency closure
is now [statically recovered](../reports/m4-crt-fdiv/source-recovery-r1/report.json),
including a dynamic Windows query, x87 fallback and complete control dependency.
This recovery supplies no initialized-value or native execution credit.
The [Windows work-area service](m4-spi-workarea-review.md) passes independent
review of its bounded handwritten caller and actual typed host query: 144
original and 288 native records, full mapped pages/State and actual x86
argument-cleanup observations. Connected startup admission remains open. The
isolated [CRT math-error registration leaf](m4-crt-matherr-review.md) passes
independent review of 1,536 original and 3,072 native records, with coherent
paired FP inputs, whole State/pages/events and 462 compiled assertions.
It stores guest callback data; callback execution and the complete CRT caller
remain untested.
The [isolated CRT provider gate](m4-crt-provider-experiment.md) and its
[independent review](../reports/m4-crt/independent-review-r1/report.json) pass
1,728 original / 3,456 native comparisons with authored callback fixtures.
This gate does not establish actual game-table execution, complete CRT/SEH
initialization or the host provider selected by a running game.
The [native asset parser](m4-assets-contract.md) independently matches all
178 archive entries and 14,925 tokens in four payloads; guest reader/widget
execution remains a separate dependency.

## Full milestone acceptance

| ID | Required proof | Current state |
| --- | --- | --- |
| M4-01 | Exact startup, application, provider and callback identities; complete reachable CFGs and dependency boundary for the required startup/menu path. | Partial static recovery; outgoing dependency closure remains open. |
| M4-02 | Checked fixed-base image/data/resource mappings, permissions, zero fill and import-slot layout; admitted user assets/configuration loaded with bounds and lifetimes. | Executable-image foundation and bounded archive/token parser pass; guest resource use, configuration and reader/widget ABI remain open. |
| M4-03 | Correct guest startup/thread context, CRT initialization/termination, initializer ordering, FS-relative state, SEH/unwinding and relevant failure behavior. | Selected 27-root carry and bounded startup/mainargs/filename prefix pass review. The real builder returns from the native filename API and stops before the command-line producer load. Another 117 nonzero roots, successful arguments/environment, CRT/SEH/termination and the full ledger remain open. |
| M4-04 | Actual native compilation and routing of every required game function/callback, with no interpreter, JIT, expected-value execution or unresolved required branch. | Sixteen integer, ten import-free FP and imported numeric-max roots pass selected connected review. Remaining required routing/functions/full path stay open. |
| M4-05 | Explicit contracts and implementations for every reached import, dynamic load, ordinal, guest handle/object and callback; unsupported requests fail with address/reason. | Provider continuation registry r9, game control routing, bounded command-line writer/data route and isolated CRT/work-area prerequisites pass review. The filename adapter now executes the exact native API with checked guest buffer and return ownership. Shared command-line producer carry, broader initialized data and services remain open. |
| M4-06 | Native window and menu creation, resource use, message dispatch, input responses, focus/acquisition and shutdown match the original required path. | Conditional service/intro/MAINMENU path and seven callbacks recovered; native execution and original comparison remain open. |
| M4-07 | Recovered and implemented graphics/presentation, input and audio requirements needed to reach and use correct menus, including formats and COM object lifetimes where observed. | Required API families inventoried; reached contracts/backends remain open. |
| M4-08 | Correct CPU/ABI, stack, defined flags, guest memory, admitted floating-point/vector state and observable host isolation across the entire required path. | M2/M3 preserved; selected 27-root and bounded startup/mainargs/filename carry pass review. Filename source review preserves State3504/FX512, sixteen pages and 1,140 source bytes with 146 ordinary and 180 independently populated hardware pairs. The twelve masked empty-stack guest inputs and original native API volatile behavior remain bounded. Broader incoming guest state and full-path forms remain open. |
| M4-09 | Hash-bound actual original startup/menu observations and representative directed/replayed input scenarios with complete provenance. | Static recovery, passive mapping and isolated original FP captures are available; live startup/menu recordings remain open. |
| M4-10 | Differential checks for required functions/services and end-to-end native menu behavior, including failure paths, repeated input and orderly termination. | Image, selected 27-root original/native review, bounded startup/mainargs/filename source review and separate command-line/math-error/work-area comparisons pass. The latest gate stops before the required command-line pointer read; full required service and end-to-end menu comparisons remain open. |
| M4-11 | Meaningful identity/metadata/routing/structure/observer controls, appropriate ordinary regressions and independent full-scope review with no unexplained differences. | Foundation/connected/batch/asset/runtime/FP/CRT/reference-data/work-area prerequisite controls and independent reviews pass. Full-scope review remains open. |
| M4-12 | Reproducible asset-free native x64 build/run recipe, source/tool/artifact pins, preserved prior successes/failures and explicit supported configurations/exclusions. | Separate foundation recipe exists; native menu recipe and full acceptance remain open. |

## Next dependency work

The adjacent initializer at `0x410940` and its callees `0x40DAF0` / `0x40DB30`
now have native connected comparisons and independent review. Continue from
the reviewed 27-root host into the remaining
initializers, preserving real callback ordering and complete persistent state.
The first null-only `_initterm` call and bounded `__getmainargs`/ordinary-builder
prefix are now connected, including the actual native filename API and checked
guest buffer/stdcall return. Carry the reviewed command-line producer into
the same Runtime and mappings without duplicate mappings or reseeding existing
State/FX/data. Establish locale/parser, allocation, argv lifetime and environment
producer contracts before successful argument copyout or provider RET.
Then continue to the main initializer interval, preserving actual table reads,
callback ordering and terminal failures. The selected 27-root gate has not yet
executed through that main-table caller.
Use the [verified workflow](m4-development-workflow.md) for new stages and
the [13 application batches](m4-application-workahead.md) for dependency work.
The pre-frame archive reader ABI and MFC provider-state contracts have priority.
In parallel, recover the complete application
constructor and initialization callback at `0x480000`, including every reached
callee and failure path. Establish explicit CRT/MFC environment contracts and
the runtime's guest handle, object, callback and import routing rules before
allowing that path to execute. The run callback, frame/menu creation and actual
message handlers then need original references and native comparisons.

The active work includes compiling/comparing the remaining required FP roots,
implementing measured CRT contracts, and connecting the bounded
`reader.zbd` / `dialog.zrd` parser to the required guest reader/widget ABI.
Assets feed the reached custom menu/widget path; parsing alone does not prove
widget behavior, graphics, input or audio. Keep these dependencies in the
full M4 work queue until the native executable reaches and uses the retail
menu through the implemented startup path.

The previous game installation remains the original reference. Running that
game successfully is separate from M4's project-built executable. Any future
live recording will be identified explicitly and arranged when the required
instrumentation is ready. No new game launch is needed for the current isolated
native prefix, source-model and compiled host/fault reviews.
