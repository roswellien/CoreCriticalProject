# G1: authored integer fixture suite

Latest regression: 2026-10-07. **G1 passed for the reviewed ADD, branch, memory
and shift leaves.**
Each fixture passed 10,144 original x86 cases and matched compiled native x64 at
O0 and O2. That is 40,576 valid cases and 81,152 native comparisons, with zero
unexplained mismatches. The separate [G2 comparison](mw3-leaf-experiment.md) now
also passes one actual MW3 integer leaf.

## Contracts and results

| Fixture | Input and behavior | Observable effects |
| --- | --- | --- |
| `fixture_add` | Two 32-bit stack arguments; wrapping ADD | EAX result; ESP +4; six arithmetic flags; all other GPRs, DF and mapped memory preserved |
| `fixture_branch` | Signed comparison of two stack arguments; return signed maximum | EAX result; CMP flags; less path writes CL=`0x11`, greater/equal path writes CX=`0x2233`, preserving the other ECX bits; ESP +4 |
| `fixture_memory` | Stack arguments are buffer address and increment; add into word 0 and copy word 1 into word 2 | EAX/ECX sum, EDX copied word; ADD flags; only bytes `[buffer,buffer+4)` and `[buffer+8,buffer+12)` may change; ESP +12 (`ret 8`) |
| `fixture_shift` | Shift the first stack argument left by five, then subtract the second | EAX wrapping result; final SUB flags; ESP +4; all other GPRs, DF and memory preserved |

All fixtures also compare EIP at the fixed return sentinel, every declared GPR,
preserved registers and DF, and the complete 4,096-byte mapped payload, including
the return frame and bytes outside permitted outputs. Only architecturally
defined arithmetic flags are compared. The capture trampoline remains outside
that payload, and guard pages surround the original x86 allocation.

The branch corpus covered 5,035 less cases, 5,109 greater/equal cases and 12 equal
operand cases. Path-specific register markers make both outcomes observable.
The memory corpus included 6,199 unaligned buffer cases and 18 placements,
including offset 0 and offset 4,084, where its 12-byte buffer ends exactly at the
page boundary. ESP alignment also varies. Each fixture has 144 directed edge
pairs and 10,000 deterministic random pairs, seed `0x3434`.

The reference worker executes actual reviewed machine bytes in a Win32 process.
The translated worker runs Remill-generated, LLVM-compiled native x64 code.
Independent Python specifications validate the original measurements before
comparison. No handwritten ADD, branch, memory or shift-function implementation is
used as the translated result. The native executables contain no interpreter
or JIT fallback.

The request/result wire format remains version 1. Fixture identity selects the
input interpretation; the native worker's compiled fixture ID must match the
supplied machine bytes. Memory input initializes buffer word 0 from entry EDX
and word 1 from entry ESI; the rest of the payload uses the documented seed
pattern. Return-frame arguments are buffer address and increment. The buffer
must fit fully in the writable payload and must not overlap the return frame.
Each case resets the entire state and mapped payload.

## Failure checks and scope

There are 135 recorded rejection/bridge check entries: 30 for ADD, 31 for branch,
44 for memory and 30 for shift. Of those, 133 are explicit rejections and two entries each
contain seven checked memory-bridge failure probes. Each fixture also has three
comparator corruption checks for a preserved register, carry flag and mapped
memory byte.

Both workers reject malformed/truncated/trailing input, unsafe flags, invalid
entry/stack addresses and changed code identities. Native workers additionally
reject bytes for a different compiled fixture. Memory tests reject unmapped,
page-crossing and 32-bit-wrapping buffer extents, and return-frame aliases before
execution. These are contract checks, not claims of matching hardware exception
behavior for arbitrary original code.

The actual native read/write bridges are separately exercised at O0/O2: valid
unaligned accesses succeed, while unmapped, crossing and overflowing reads and
writes set the failure latch. Read-only writes fail too. Failed writes preserve
every mapped byte. The latch causes a guest run to fail instead of accepting the
fallback value returned through Remill's nonthrowing intrinsic boundary.

A separate diagnostic changes JGE's displacement to an out-of-range destination.
Remill emits `__remill_missing_block`; the adapter explicitly rejects it. This
diagnostic is never executed as original or translated code. Unsupported external
helpers, changed State layouts, incompatible entry widths and pointer/integer
casts are also rejected. Instruction identities and reviewed control-flow ranges
are fixed; this gate establishes the bounded integer-leaf pipeline, not arbitrary
x86, x87, imports, indirect dispatch or whole-game compatibility.

The shift fixture adds an explicit policy for two undefined intermediate AF/OF
values. A bounded straight-line SSA proof requires exact flag stores followed
by defined overwrites before observation. The default profile rejects this
helper; the opt-in shift profile rejects alternate control flow, overlapping
loads, State aliases, extra uses and missing/tainted overwrites. All final SUB
flags are compared at both optimization levels. Fourteen focused adapter tests
pass, including an opt-in LLVM test with 11 mutated-module rejections and two
incompatible-profile rejections.

## Reproduction and evidence

With the pinned local tools from [dependencies](dependencies.md), run:

```powershell
./tools/lifting/run_fixture_suite.ps1
```

That assembles/disassembles each authored source, checks exact bytes against the
catalog, lifts with Remill, validates all State storage layouts and bridge
signatures, compiles O0/O2, executes the differential corpus and rejection checks,
then verifies source, corpus, worker, output and generated-artifact hashes.
It accepts `LLVMRoot`, `RemillRoot`, `VSRoot` and `Python` overrides. Ordinary
CMake builds remain independent of these opt-in dependencies and game files.

Individual fixtures can be replayed with:

```powershell
./tools/lifting/build_fixture.ps1 -FixtureKind branch -RunComparison
./tools/lifting/build_fixture.ps1 -FixtureKind memory -RunComparison
./tools/lifting/build_fixture.ps1 -FixtureKind shift -RunComparison
```

Local ignored evidence:

- `reports/fixture-suite/report.json`: verified G1 summary and individual report hashes.
- `reports/fixture-{add,branch,memory,shift}-differential/report.json`: corpus identity,
  exact commands, reference self-test, O0/O2 comparisons, coverage and build provenance.
- `reports/fixture-{add,branch,memory,shift}-lift/controls.json`: rejection and bridge results.
- The same `*-lift` directories: original/native disassembly, LLVM guest/host IR,
  O0/O2 objects, layout records and build hashes.
- `reports/fixture-branch-lift/bad-target-guest.ll`: minimized unresolved-target diagnostic.
- `reports/fixture-suite-build-20261007.log`: latest complete suite log.

Earlier Smart App Control blocks and the user-resolved setting change are
recorded in [the original ADD experiment](fixture-add-experiment.md). The current
suite needs no game launch. The reviewed MW3 integer-leaf experiment now passes
G2 on the same authored source digest. Next are separately contracted x87 and
call/import probes.
