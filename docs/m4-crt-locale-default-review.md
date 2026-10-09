# Default locale lock-allocation prerequisite review

The bounded native experiment executes literal original source for the default
locale selector and refuses at its first genuine allocation dependency. The
source stub `78003DD2` pushes selector `-3`, CALLs `_setmbcp` at `78003DDB`,
which CALLs `_lock(25)` at `78001055`. The observed zero lock slot
`7803708C` selects its lazy allocation branch. The actual CALL
`7800107B → 780012B3` preserves argument 24 and return word `78001080`.
Terminal State has ESP `20001810`, EBP `20001820`, EAX 25 and ESI `7803708C`.
The allocator body and allocation result are unexecuted.

The bootstrap is explicitly host-scheduled at the healthy `mainargs-before`
boundary. It stores one external return word at `2000185C` and changes only
the carried State EIP/ESP to the default stub and that frame. Generic Runtime
CPU remains at the real mainargs service slot/frame; its actual CALL records
receive no invented locale call. This is not evidence that original DllMain or
process attach scheduled the bootstrap. The earlier command-line producer,
filename service, mainargs provider and parser remain unused in this gate.

The compiled source is exactly 9 bytes of stub, 169 bytes of `_setmbcp` hot
body and 43 bytes of lock prefix ending immediately after the genuine malloc
CALL: 221 new source bytes across three O0/O2 object pairs. The full 91-byte
lock body remains guarded identity, for 269 new identity bytes and 1,856 total
source identity bytes. Full lock lifting exceeded a bounded timeout; failed
attempts are retained. No instruction or artificial RET was appended. The
current source executes 20 PCs and completes 15 ordered DWORD accesses.

The native binding owns an immutable parent Context and a private active
authority. Dispatch retains that authority even if a public owner token is
cleared or corrupted. Exact source operands and values are checked before
committing PUSH/CALL stack writes. First diagnostics survive partial faults,
observer exceptions, terminal token republishing and poisoned retries. Parent
mainargs provider admission remains unused; only its known first diagnostic is
set by the locale refusal.

| Evidence | Result |
| --- | --- |
| Production O0/O2 workers | 48 ordinary runs and 24 fault controls passed |
| Root original-BEFORE/source comparison | 48 ordinary runs, 83,423 checks |
| Independent affine source/model/native-observation audit | 48 rows, 5,376 comparisons |
| Changed-byte controls against complete storage validator | 960 denials |
| Independent compiled O0/O2 corpus | 132 scenarios, 4,838 assertions |
| Actual rich host boundary captures | 264 raw80/full legacy-tag pairs |
| Unchanged hardware validator corruption controls | 548 denials |
| Independent exact case/request/inventory controls | 14 denials |
| Preserved guest state | Full 3,504-byte State, 512-byte FX and 17 pages |

Root independently derives expected guest effects from the original FDIV BEFORE
capture and literal source. The declared native FDIV OS query is an external
witness; candidate AFTER State/pages/CPU do not seed expected machines. A
separate affine source-ledger audit checks all 48 seam/final states against the
complete frozen mainargs model and original source. Root makes no full causal
source-model claim for fault controls; the independently authored compiled
corpus supplies that evidence.

Independent source/ABI review checks all six new AMD64 objects, their 3,504-byte
named State layout and unwind metadata. Sixteen earlier guest objects and both
FDIV libraries remain byte-identical. One additional literal RX source page
`78003000` extends the prior sixteen mappings; all other bytes remain carried.
The 257-byte raw lead-byte table remains unchanged and supplies no initialized
classification credit.

Production native stages were performed by the delegated author, and independent
fixture stages by the reviewer. Root verifies their actual commands, exit codes,
timings and sealed archives. The production receipt inherited a field named
`native_executed_by_root`; that field does not establish a second execution or
independent root executor credit. Four strict archives bind complete inventories.
Packing and execution are separate measured stages. No new speed comparison or
project completion estimate is claimed.

The current preparation is r4, build r2, production execution r2, root model r3,
independent source audit r1 and hardware/inventory check r3. Earlier failed
full-body lifting and the initial missing locale malloc dispatch route remain
historical evidence. The latter was repaired before the fresh successful build
and native runs. Checker-only inventory/name repairs required no candidate
change or native rerun. Historical accepted/failed reports are SHA-bound anchors
and their older flat inventories are not expanded into the current closure.

No source RET, allocator result, lock publication, initialized locale table,
codepage API, full parser sizing, argv/environment output, original attach or
complete CRT startup is proved. Selected initializer coverage remains 27/144;
M4 is unfinished. The [allocator source workahead](../tools/m4-crt-locale-allocation-recovery/README.md)
identifies original attach's heap initializer `780039BF → HeapCreate` as the
next priority. It must produce the real heap handle and source-selected mode.
An optional malloc prologue gate can stop before its first SEH-chain read at
`780012F2`, but cannot establish successful allocation without those heap/lock
prerequisites. This workahead is static source evidence and grants no native
execution credit.

The current closed receipt is
[root acceptance](../reports/m4-crt-locale-default-root/root-acceptance-r1/report.json).
The implementation and observer workflows are described in the
[author contract](../tools/m4-crt-locale-default/README.md) and
[root model contract](../tools/m4-crt-locale-default-root/README.md).
