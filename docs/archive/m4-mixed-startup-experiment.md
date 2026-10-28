# Connected integer and floating-point startup candidate

The fresh x64 diagnostic host runs the 26 import-free initializer table targets
on one admitted image and persistent 3,504-byte Remill State. This includes all
sixteen reviewed integer roots and all ten now independently reviewed standalone
FP roots. The connected gate has zero differences in 1,248 actual original phases
and 2,496 native O0/O2 phases. Independent review of this new integration remains
required. It does not complete the 144-root table, CRT entry or M4.

The [actual native build](../../reports/m4-mixed-startup/native-r3/build.json) and
[connected comparison](../../reports/m4-mixed-startup/original-comparison-r4/report.json)
bind the admitted image, source, compiled objects and raw observations. The
original reference executes only the complete selected bodies and their two
integer callees/shared tail, in an isolated worker. No ordinary game session or
provider DLL was launched for this experiment.

## Connected domain

Each sequence starts with default admitted image operands, an authored A5-filled
4,096-byte stack, clean sticky status, twelve masked precision/rounding control
words and an empty x87 stack with TOP 0 or 7. Two repetitions produce 48 complete
sequences. The full 145-slot table is snapshotted, and the selected 26 nonzero
targets execute in their actual table order. The other 118 nonzero roots remain
unimplemented in this host; the full ledger is explicitly incomplete.

The native Runtime's checked CALL pushes a return dword at `0x20001800` from
caller ESP `0x20001804`. The return PC `0x410A80` is an explicitly authored
reference capture broker outside every required source body. Its instrumentation
JMP is separate from original game instructions. Native code returns to that
admitted RX address through the Runtime's real ABI check and does not execute
the original bytes there.

Each phase carries CPU, image pages, x87 data and sticky status forward. Original
entry restores both actual FX and legacy ENV, preserving nonzero legacy metadata
and empty-register storage that FX alone cannot supply. Native adapters overlay
the externally framed CPU on existing State; they preserve opaque State bytes
and keep the separate Runtime FX projection coherent. Checked FP bridges have
component-specific symbols, dynamic owned call frames and actual numerical x87
primitives. Guest code is statically compiled; there is no interpreter or JIT.

## Observations and controls

Each native phase records all 7,008 entry/exit State bytes, CPU, eleven complete
memory pages, separate guest FX/legacy ENV projections, actual host restoration,
ordered checked events and real internal call/tail routes. The original worker
records actual CPU, hardware FX, legacy ENV and pages. Original State and access
events are unobserved; the native checker reconstructs their allowed source
updates and protected bytes separately.

At each optimization level the comparison checks 1,200 carry boundaries, 16,800
native memory events, 480 internal routes and 48 instances of the actual integer
store at `0x4C7940` feeding the subsequent FILD root at `0x4C79D0`. It compares
defined CPU flags and separately retains observed final C1/C0/C2/C3 and dead
raw80 values. Standalone mathematically proved C1 subsets do not automatically
prove connected final-store flags.

The shared context executes ten positive FP callbacks, rejects ninety invalid
contexts and rejects eighty attempts to reuse a poisoned context per level.
These cover wrong FS, occupied tags, unmasked CW, MXCSR/status outside the domain,
disagreement between persistent State and FX, changed source bytes, unavailable
observed memory and an unadmitted return PC. Twelve further actual worker checks
reject invalid identity/CLI/output ownership before guest execution. Race,
reparse and hardlink publication behavior has not been tested.

## Preserved attempts

The first native run completed, but its records used table indices where the
reference records used table-slot addresses and initialized the stack with zero
rather than the authored A5 fixture. Both streams, their literal build sources
and the failing comparison remain intact. A fresh second build corrected those
fixtures. The final third build adds shared State/FX admission, per-call original
code revalidation and compiled rejection controls.

A primary checker initially expected one clear/test pair for a cosine callback
whose reviewed source uses two. Its exact failing source and report remain
preserved; only that declarative checker count was corrected. Early recipe
parsing/path errors are retained separately. Prior standalone successes and
status/numerical failures remain frozen.

## Remaining M4 work

The ten import-free FP prerequisites are now reviewed. Three additional table
roots reach imported FP services. The smallest recovered provider closure is
MSVCP50 `numeric_limits<float>::max`, a complete FLD/RET leaf with an actual x87
ST0 result and guest continuation. The `_hypot` and onexit-dependent roots need
their measured provider/context contracts. Other roots require allocation,
MFC objects and SEH. CRT entry establishes onexit globals before dispatch; their
PE zero-fill values are not the initialized runtime values.

Complete initializer ordering, CRT/SEH/MFC services, application callbacks,
reader/widget execution, graphics/input/audio backends and native retail menu
observations remain required by the [full M4 plan](m4-startup-plan.md).
