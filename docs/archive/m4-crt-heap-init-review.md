# Heap initializer review: first HeapCreate CALL

This bounded gate executes the original caller fragment at `7800183C` and the
heap initializer entry at `780039BF`. Host scheduling changes only the carried
State's low EIP. The source `PUSH 1` and direct `CALL` create their own argument
and return word; the host writes no guest stack words. State ESP and the generic
Runtime CPU/call records are preserved at the scheduling seam.

The source executes nine instruction addresses and eight DWORD memory accesses,
including two actual source CALLs. The second CALL at `780039D0` reads import
slot `7802E0A8`, whose original raw token is `0003461E`. The terminal State has
EIP `0003461E`, ESP `20001848` and EAX zero. Its return word is `780039D6` and its
`HeapCreate` arguments are flags zero, initial size 4096 and maximum size zero.
The typed unresolved-import fault names the source CALL and import slot.

The new compiled and guarded source is 84 bytes: the seven-byte caller fragment
plus the complete 77-byte initializer body. Only the first 30 bytes across those
two spans execute in this experiment. Four new AMD64 guest objects cover O0/O2;
22 earlier guest objects and two FDIV libraries remain unchanged. Total carried
source identity is 1940 bytes. All 17 earlier mappings remain intact, and the
future heap-global page at `78035000` is not mapped for this API boundary.

`XOR EAX,EAX` has architecturally undefined AF. This build admits its generated
representative zero at the one exact source site `780039BF`. That is not a
universal original-CPU AF equivalence claim. The subsequent successful
`CMP 1,0` defines all six arithmetic flags as zero at the ordinary terminal.

The production author executed 72 native sequences. Root's original-BEFORE
observer checked 48 ordinary sequences with 81,977 checks and rejected 840
selected semantic byte corruptions. It compared all 3504 State bytes, 512 FX
bytes, 40 Runtime CPU bytes, every mapped page and all 27 checkpoints. The
independent compiled corpus covers 132 fault and cleanup scenarios with 5034
assertions. These compiled scenarios validate refusal and cleanup behavior;
they do not provide a full causal source-model oracle. Root claims zero fully
modeled causal sequences and no separate native execution of the corpus.
The independent hardware review verified 264 actual snapshot pairs, rejected
548 semantic corruptions and rejected 14 closed-inventory violations. A
separate affine audit checked all 48 current ordinary rows with 6672 comparisons
and 672 exact unused-service records.

Current evidence is kept under
[source recovery](../../reports/m4-crt-heap-init-recovery/recovery-r1/report.json),
[source contract](../../reports/m4-crt-heap-init-review/source-r3/report.json),
[production build](../../reports/m4-crt-heap-init/build-r1/build.json),
[production execution](../../reports/m4-crt-heap-init/execution-r1/report.json),
[original-BEFORE observer](../../reports/m4-crt-heap-init-root/observe-r2/report.json)
and [source/ABI audit](../../reports/m4-crt-heap-init-review/audit-r1/report.json).
The [independent native corpus](../../reports/m4-crt-heap-init-review/native-r1/report.json),
[hardware review](../../reports/m4-crt-heap-init-review/check-r1/report.json) and
[affine model audit](../../reports/m4-crt-heap-init-root-audit/final-r1/report.json)
provide the remaining current proof domains.
The final root acceptance receipt binds the independent compiled/hardware
review, independent affine model audit, completed timed stages, strict capture
archives, documents and current physical dependency hashes.

No host `HeapCreate` call or API return executed. No heap handle or mode was
published, allocator result produced, initializer RET reached, locale table
initialized or parser completed. Original DllMain/attach/GetVersion scheduling,
complete CRT startup, argument/environment ownership, standalone menus and M4
completion remain outside the accepted scope.

The next source continuation stores the real heap handle at `780039D8` and calls
the mode selector. It requires the future raw RW heap-global page, real handle
ownership and source-dependent OS/PE/environment outcomes. A host x64 handle
must not be truncated into a guest DWORD. The next bridge must use an opaque
guest handle registry and clean up owned heaps on failure and exit.
