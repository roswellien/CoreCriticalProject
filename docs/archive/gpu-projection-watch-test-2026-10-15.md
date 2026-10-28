# Observed original projection-removal test

This private experiment follows the missing flat-memory coverage identified in
[the first projection test](gpu-projection-bypass-test-2026-10-15.md). Neither
playable launcher changes. No new FPS gain or native acceptance credit is
established by the fixtures below.

Follow-up: [differences investigation](gpu-projection-differences-investigation-2026-10-15.md)
separates expected scratch-byte changes from the intermittent failed comparison.
Two subsequent 1,800-frame bypass replays match every semantic record and all six
captures, including one with added draw diagnostics disabled. The first failure
is retained and its precise cause remains unproven; no launcher is promoted.

The execution boundary under test is the original lit polygon perspective loop
at `0x540985`: a narrowly admitted GPU draw omits its first n−1 iterations and
retains its last original iteration. Original transformation, clipping,
simulation and unsupported materials continue on the CPU.

## Observation and compiler contract

`flat_projection_watch.py` wraps the existing flat-memory lowering. Every
generated guest load is observed before access and every guest store after
access, only when its byte range intersects `[0x72F41C,0x73041C)`. LLVM inlines
the range helper and maintains branch/PHI edges. End arithmetic uses 64 bits.
The range helper and external observer receive both State and the exact guest
memory token explicitly. Original `noalias` parameter contracts remain intact;
tests require the actual per-instruction State PC to remain visible after O2.
The observer has ordinary memory effects and can unwind; it is not marked
`nounwind`. State loads/stores are not guest-memory accesses. Raw80 bridge
payloads remain byte-preserving. Unsupported remaining memory calls fail the
build rather than silently remaining outside observation.

`build_projection_watch.py` takes the retained launcher's ordered 37,201-object
list and resolves every original host-IR source, including additional closure
bodies and the timing-preserving codec object. It writes a separate tree and
pins the recipe and per-object source/output identities. The recipe retains
cleanup, simplifycfg/x87 merging, annotation, strict FP, flat memory, O2, the
additional DSE/GVN/instcombine/simplifycfg passes and recorded symbol renames.
Exception tracking remains enabled. Safety instrumentation itself is not a
performance candidate.

The host patch also observes scalar fast paths and common GuestMemory transfers.
The C observer preserves hardware FP state on both normal and exceptional exits.
`harden_projection_watch.py` closes audited direct-host gaps:

- Common transfers identify the GuestMemory instance and retain 64-bit sizes.
- Active guest address-space copy/move stops visibly.
- Direct FTOL stack accesses reject a scratch overlap or address wrap before
  their first raw access, including the differential snapshot path.
- Raw80 host scratch pointers cannot alias the active flat guest reservation.

The previous exact callback depth-copy exceptions remain bounded to the pending
token, instruction, offset and width. Unknown reads still stop the experiment.
The callback audit also follows the copied depth through EAX/ECX. It reaches
only the RHW stores and temporary registers that are overwritten before texture
submission/return. Some known calls receive these temporaries as unused incoming
register state: the owned `_ftol` ignores their incoming values, and state-setting
services take their arguments from the guest stack. Admission and submission now
validate the original thunk bytes and immutable IAT cell, resolve its raw word
through the host's game-import map, and require the owned `_ftol` implementation
at `0x78002551` without a higher-priority direct body. The host deliberately
retains raw game IAT words; an initial direct-address check rejected all
candidates and was corrected before any CPU-removal claim.

## Completed focused checks

- `test_flat_projection_watch.py`: scalar widths, raw80, boundary/overflow
  classification, State exclusion, PHI control flow, load/store ordering,
  ordinary memory effects and dirty-read exception unwinding pass.
- `test_projection_optimized.py`: **1,008** source-bound original lit-loop
  full-versus-last cases pass through the complete optimization recipe, with
  counts through **128**, all tested precision/rounding combinations, complete
  State, allowed memory footprint and hardware status comparisons. The
  FP-preserving observer executed **104,832** watched writes while deliberately
  changing FP settings internally.
- The same **1,008** cases also pass with `--unwatched`, using the production
  flat-memory/optimization pipeline without safety observers. This is a
  separate compiler-contract check for the proposed timing copy.
- `test_projection_host_watch.py`: the actual C observer wrappers restore FP
  state normally and during unwinding; memory-instance identity, transfer-size
  rejection and direct stack-span boundaries pass.
- All **37,201** watched objects compile and link, with **635,744** observed
  flat reads and **540,274** observed flat writes. The raw80 paths include
  **34** reads and **13** writes; no unsupported memory operation remains.
- The complete watched host with bypass disabled matches the frozen original
  control's **1,000** draw hashes/counts and all four PPM captures.
- A fresh unchanged-launcher control completes 1,000 frames at stock 800-unit
  distance with the current fog/settings. A second control using frozen asset
  inputs matches all 1,000 original draw counts/hashes and all four captured
  PPM files, including the native frame-1000 readback. These correctness runs
  overlap compilation and do not supply performance measurements.

The first partial watched-object compilation was stopped before any game run
when review identified the missing explicit-pointer ABI. Its output under
`all-objects/` is superseded and must not be linked as the safety candidate.
The corrected build writes `all-objects-v2/`; the private host is
`local/remaster/gpu-native-projection-watch-r2/`.

An independent manifest inventories **147** linked objects outside the main
list. Retained IR and bridge inspection found no additional direct guest
pointer access; native boundary capture uses host storage and the FDIV adapter
uses common GuestMemory transfers. The manifest pins objects and sources and
states the limits of the source-to-object recipe audit explicitly.

## Live result: rendering equivalence failed

The complete watched reference and bypass hosts each finish the same private
1,800-frame Instant Action movement/turn sequence at stock 800-unit distance,
3440×1440, FXAA and 16× AF, with frozen assets/settings and the same executable
SHA-256 (`a7536ffc313d005546cbf2b57c1e8e01502ab3bf907e84aa32661fe64ed92d93`).
Reference admits/consumes **67,659** draws. Bypass admits/consumes **67,412**,
omits **178,859** original perspective iterations, and observes exactly
**178,859** permitted callback depth-copy reads. No dirty-read or pending-token
guard fails. This establishes exercised observation, not rendering equivalence.

Rendering equivalence **fails**: all five gameplay capture files differ,
including native frame 1000. Original draw counts first differ at frame **489**
(893 reference versus 897 bypass); cumulative admissions first differ at **507**.
Original TL byte hashes differ from the first admitted frame **324**, which
alone is expected when those coordinates are omitted. The semantic hash also
differs at frame **282**, before any admission, so that earlier hash difference
cannot be attributed to skipped projection. The frame-time log's other counters
are not evidence that the original draw counts match.

Read-only inspection finds both modes attach the same kind of immutable raw
geometry token before scene conversion; widescreen handling and the world shader
do not select geometry using stale TL coordinates. No cause for the changed
original producer behavior is established. The next investigation must isolate
guest state/FP and camera behavior around the first skipped iteration, while
accounting for the pre-admission semantic-hash difference.

The experiment is **not promoted**. Neither launcher changes. No timing comparison
is run against a candidate with failed image equivalence, and no FPS gain is
claimed. The separate unobserved timing package remains unused and is not a
safety or gameplay result. Full live evidence, including the failed comparison,
is retained under `local/gpu-projection-watch-r1/`.

Evidence stays under `local/gpu-projection-watch-r1/` and the existing private
loop fixture directories. Original media/generated code remain local. Strict
acceptance remains **131/144**; no commit or acceptance promotion is performed.
