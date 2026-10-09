# Next functional batch: environment acquisition and mainargs return

The next unit extends a **fresh live locale/parser run** from the genuine builder return at `7800BA9E`. It acquires the actual process environment, builds the original CRT environment vector and strings, then executes the remaining `__getmainargs` output stores and return. Heap, critical-section and builder allocations remain owned throughout; a cleaned final capture cannot be resumed.

The current locale candidate is [preparation-r9](../reports/m4-crt-locale-batch/preparation-r9/report.json), [build-r9](../reports/m4-crt-locale-batch/build-r9/build.json) and [execution-r7](../reports/m4-crt-locale-batch-root/execution-r7/report.json). Build SHA is `61668f2713b3a7ac2bd9cbc8d610f806c9fcc977fe9574d784e66f98bf56f88a`. The corrected execution passed 36 tests across O0/O2; ordinary rows have 30 actual API calls at each level. Independent admission is still pending when this plan was written. Earlier r8/r6 evidence contains the rejected deferred-lambda capture defect and receives no semantic completion credit.

## Recovered source closure

[Environment recovery-r2](../reports/m4-crt-environment-recovery/recovery-r2/report.json) pins 13 exact spans, **1,170 source bytes and 427 decoded instructions**, their branch targets, imports, data words, jump tables and original PE permissions. Report SHA is `59402e52a2459b4e9765f6edc7b64e32f1eb5e5b1466ab1934e751174ea4abf2`; [pins](../reports/m4-crt-environment-recovery/recovery-r2/pins.json) SHA is `d2a4176c5b17e7031e72d28362f5d451a2794783a88669854a12acfde2a2147a`. [The source contract](../reports/m4-crt-environment-recovery/recovery-r2/source-contract.json) includes source operands and implicit stack/string accesses. This is static recovery: no source execution, API invocation, lift or new compiled object is credited.

All ranges below are half-open and have base `78000000`.

| Original unit | Exact recovered ranges | Bytes |
|---|---|---:|
| Environment acquisition, W/ANSI alternatives | `3CF1..3D9A`, `F0E5..F180` | 324 |
| Environment vector, strings and sentinel | `4187..4227` | 160 |
| `strlen`, `strcpy` and its shared cold body | `2F32..2FAB`, `2FAB..2FE5`, `3664..36BE` | 269 |
| ANSI disjoint forward `memcpy` domain | `160E..16F5`, `10F05..10F71` | 339 |
| Remaining mainargs outputs/RET and builder-return JMP | `BA76..BA99`, `BA9E..BAA0` | 37 |
| Authentic acquisition/publication and vector CALL fragments | `1882..188C`, `18A6..18AB` | 15 |
| Fatal vector/string allocation branch | `BDFC..BE16` | 26 |

The acquisition function uses actual `GetEnvironmentStringsW`, then `WideCharToMultiByte` with the original arguments; a genuine W failure takes its ANSI alternative. The exact imported ANSI acquisition name is **`GetEnvironmentStrings`**, without an A suffix. Release imports are `FreeEnvironmentStringsW` and `FreeEnvironmentStringsA`. Bind the physically measured requested export, forwarding/alias chain, owner and image for each native call; do not infer the acquisition spelling from its release partner.

## One functional execution

At the live builder boundary, keep the existing mainargs frame and all ownership active. Record an explicit research **EIP-only schedule** to `78001882`. Its original CALL to `78003CF1` supplies the real helper return frame; the helper returns to `78001887`, where the original MOV publishes the acquired ANSI malloc block to `78037178`. Stop that fragment at `7800188C` before unrelated command-line startup work.

Record a second EIP-only schedule to `780018A6`. Its original CALL invokes `78004187`: count entries, exclude strings whose first byte is `=`, allocate the vector and each string through the current genuine mode-1 malloc bridge, and copy through original `strlen`/`strcpy`. The original store at `780041BD` publishes `78037C04`; source code frees the acquired malloc block, clears `78037178` at `78004219`, writes the vector NULL sentinel at `78004220`, and returns at `78004226` to `780018AB`.

Finally schedule back to the carried `7800BA9E`. Execute its real JMP to `7800BA76`, the argc/argv/environ output stores, POP EBP and RET at `7800BA98`. The actual mainargs caller return word is `005AC46E`. Validate and unwind that retained source frame naturally; stop before the game caller executes its next instruction. These three scheduling records do not add guest return words or publish globals from the host. They establish a research invocation sequence, not original DLL attach ordering.

## Integration and ownership

Reuse the actual live heap and allocation bridge. Add separately typed ownership for native W/ANSI environment blocks: retain the full host pointer, a checked guest alias, the measured complete double-NUL block and the exact matched release API. API transport is declared separately from original source accesses. Release failure retains ownership and its diagnostic; no truncated pointer, guessed block, host-written CRT vector or synthetic successful conversion is admitted.

The allocator must support the acquired converted block, environment vector and every individual string alongside the lock and argv allocation. Derive a bounded allocation/API/capture budget from the measured block length and entry count; the current fixed 16-allocation budget cannot represent an ordinary environment with more entries. Preserve actual requested and rounded extents. Logical strings and vector writes must stay within their requested regions; original DWORD string lookahead may use an owned rounded extent only when the actual native initial bytes are witnessed. The immutable API block/output witness is historical evidence, while mutable guest aliases and stack guards advance only with committed declared/source writes.

For ANSI acquisition, enforce nonoverlapping source/destination ownership before the original memcpy call. Its original backward-copy target `78010F71` remains outside this selected domain. The source jump tables at `780016F4`, `78001704` and `78001728`, including the signed-index use from `78001669`, must be resolved from original bytes and source-derived bounds. Reuse current normal SEH, State/FX/Runtime CPU preservation, actual LastError restoration and compact direct capture transport. Cleanup releases native environment blocks once, then owned environment/argv/lock allocations and critical sections in their valid lifetime order, and finally the real heap.

## Acceptance and targeted controls

The functional result requires actual environment acquisition and conversion witnesses; genuine source construction of every retained entry and final NULL; original publication/clear stores; genuine mainargs output stores and RET; and the full live ownership checkpoint before cleanup. An independent source model must derive the final State, FX, CPU, mutable pages, vector/string bytes and frame effects from the original BEFORE, measured API witnesses and explicit scheduling records. It may not seed from the resulting capture. Execute O0/O2 with actual responses driving their paths; do not require API responses to match by assumption.

Use a compact positive corpus and focused controls:

- Exceptions immediately after native acquisition/conversion and before source release, proving retained ownership and eventual matched cleanup.
- Wrong acquisition kind, forged/stale pointer, wrong runtime/thread and duplicate release, rejected before any native release call.
- Partial output transport and source vector/string/sentinel permission failures, preserving exact committed effects and first fault.
- Missing double-NUL or requested-boundary violations in explicitly labeled initial fixtures, without claiming an actual malformed OS response.
- Premature heap cleanup and a final mainargs RET observer exception, proving old and new allocations stay valid until their final checkpoint.

Observe real NULL/failure outcomes if they occur. Counterfactual failure formulas or separately labeled host diagnostics do not establish execution of the original failure branch. No forced-success API responses are needed.

## Remaining dependencies and limit

`7800BADB` (`_amsg_exit`) is still unrecovered; actual fatal allocation branches must refuse at that genuine call until its full termination contract exists. The backward/overlap memcpy path is excluded by the disjoint-copy domain rather than claimed complete. The selected normal environment unit otherwise has recovered source closure, reusing accepted genuine malloc/free and current conversion dependencies.

This batch completes the researched mainargs return. It does not establish full attach/TLS helper `78003B98`, file/CRT helper `78003C1D`, later initializer `78004227`, original DLL attach execution, complete CRT startup, a project-built game menu or Training launch.
