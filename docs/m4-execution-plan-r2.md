# M4 execution plan: functional batches and direct captures

This update implements the user's request on 2026-10-09 to finish the efficiency changes and make measurable progress toward native startup. Earlier accepted source, reports and plans remain unchanged.

## Changes to enforce

1. **Write captures directly into compact archives.** New native workers use a shared streaming capture sink. They do not create a file for each checkpoint record or require a later capture-tree copy and packing pass. The existing strict reader, content hashes, path rules and archive limits remain the transport contract. Oversized workloads use bounded archive parts with a verified disjoint logical union.
2. **Complete functional units.** Intermediate instruction and API checkpoints remain observable inside one allocation/free batch. They do not become separate submissions unless a new unresolved dependency prevents completion and is reported explicitly.
3. **Run independent work concurrently.** Initially: coordinator and independent transport review; direct-writer implementation; allocator implementation; original source recovery and expected-state modeling. After the writer is ready, that agent independently reviews allocator ownership, failures and host-state preservation. Heavy file work is kept out of competing parallel stages.
4. **Reuse accepted components.** Reuse unchanged translated objects and source contracts. Run targeted regressions for changed transport, routing and ownership. Preserve earlier failed and passing evidence without rerunning unrelated historical suites or expanding archived captures into a flat tree.
5. **Measure functional progress and elapsed costs.** Record native execution plus capture emission, archive finalization, reader verification, source comparison and review separately. Compare the same logical data when measuring transport improvement. A repeated-read benchmark does not establish faster implementation.

## Completed functional batch

The completed unit is a genuine mode-1 allocation/free roundtrip using the same heap established by the accepted source initializer. [Current progress and evidence](m4-progress-allocation.md) record the successful O0/O2 runs and independent source and compiled checks.

- Preserve private heap ownership through the genuine initializer return.
- Execute the original caller's return-value test and argument cleanup, stopping before unrelated attach dependencies.
- Enter the authentic CRT malloc path through a declared external cdecl research caller. Execute normal FS/SEH registration and removal, size rounding, the source mode branch, the real HeapAlloc bridge and the source return.
- Return a checked guest allocation address backed by privately owned full-width native memory. Verify a declared client data pattern through the guest/native bridge.
- Execute the authentic free path through the real HeapFree bridge. Reject invalid and stale ownership, and release the heap after the batch.

The external caller and declared backing are explicit research inputs. They do not establish original attach scheduling, locale completion or original-game execution. Allocation API results remain actual finite witnesses; expected source state is derived from original bytes and BEFORE inputs.

## Completion criteria

The batch is complete when O0 and O2 native execution return a usable allocation, preserve it across client access, release it through the recovered free path, restore the normal SEH chain and retain required caller/host state. Meaningful failure and ownership controls must confirm cleanup and reject invalid operations before an OS call. Independent source and compiled review must agree with the current captures. All new main captures must be emitted directly into strict archives with no per-record physical files.

The transport change is complete when the existing reader accepts directly produced archives, their logical bytes match independent expected data, malformed names and publication failures reject, bounded parts form an exact disjoint union, and a comparable measured workload records emission/finalization/verification costs.

## Next functional units

After allocation ownership is accepted, complete the required critical-section and default-locale path, then parser sizing, argument outputs and environment ownership. Resume game initializer batches as their shared dependencies become executable. MFC/provider-state and archive-reader preparation remains parallel work when a slot becomes available. Native window, retail menu and Training acceptance still require their actual integrated behavior.

Progress reports lead with completed functional behavior, the integrated execution frontier and the next dependency. The separate game initializer count remains a coverage measure and is not an overall completion percentage.

## First implementation of this plan

The shared checked capture writer is implemented and used by both the allocation author and the independent native reviewer. Both publish strict compact archives directly, without a flat capture tree or later packing. Writer compatibility, bounded partitioning, refusal and host-state tests passed. A same-input local transport workload measured about 15 times faster emission/finalization/verification; this is recorded separately from implementation time.

The coordinator, writer/reviewer, allocator author and source-model author worked concurrently. Existing source and object files were reused by physical identity. Only the changed writer, ownership/routing and allocation behavior received new native controls; unrelated historical suites were not rerun. Internal source and API checkpoints remained inside complete functional sequences. Native execution, emission/finalization, strict verification and independent comparison have separate measured costs.

The next implementation unit is the [complete required critical-section/default-locale batch](m4-next-locale-batch.md). Its acceptance must reach an initialized lead-byte table and return to the blocked parser. An intermediate API or instruction checkpoint alone is not that unit's completion.
