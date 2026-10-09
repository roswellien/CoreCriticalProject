# Independent allocation review

This namespace independently compiles the frozen preparation-r7 against
build-r9, reusing all 38 accepted ancestor guest COFF objects and adding the
26 literal allocator guest objects without changing their bytes. The generated
private fixture changes observation, host seeding, input requests and directed
control hooks. It does not modify the native binding or any lifted guest body.

The accepted receipts are build-r1, native-r1 and check-r3. Native execution ran
once at O0 and once at O2, with 12 ordinary and 12 independently authored control
rows per level. Twelve ordinary rows combine the six original BEFORE inputs
with requests 0, 1, 24, 31, 32 and 4096 in two pairings. No original provider or
game was executed and no API response was injected.

Actual combined evidence: 48 rows, 96 rich hardware pairs, 338 compiled fixture
assertions, 48 read-only token-alias units and two joined wrong-thread denials.
All 48 measured heaps were released; actual allocation calls were 40, actual
source HeapFree calls 24 and actual fallback cleanup frees 16. The original
queries supplied 1776 checked DWORD output commits. Captures include 1008
complete State/FX/CPU and 21-page milestone sets, plus the original reserved
Runtime heap page. Each level has 44403 logical records and 67417976 payload
bytes in one strict archive and its transport manifest. No loose per-record
files or later copy/packing pass was used.

The hardware checks retain complete ENV28 with nonzero legacy context, CW/SW,
FTW, all eight raw80 registers, MXCSR and XMM6..15, plus LastError and the ABI
direction flag. Volatile XMM0..5 equality is unclaimed. Each native boundary
actively loads the independent rich seed before the assembly observation.

Source/ABI review confirms private full-width HANDLE/pointer ownership, a
separate guest token/backing at 0x31000000, final clone-map preflight after the
control hook, checked original IAT identity, immutable measured API witnesses,
and genuine stdcall return reads. The authenticated mainargs BEFORE seam
records the original source-carried FS chain/upper stack without reseeding.
Normal free and fallback cleanup are separate. HeapDestroy refuses a still
owned allocation, including when an OS cleanup free fails. Current successful
OS calls are measured; unobserved OS failure outcomes receive no execution
credit. HeapAlloc's exact physical Kernel32→NTDLL.RtlAllocateHeap chain is
checked separately from the unchanged packed API identity.

History remains intact: build-preflight-r1 rejected mixed-case duplicate JSON
dependency keys before any compiler ran. fixtures-r2 canonicalized those keys.
check-r1 incorrectly expected nine final intrinsic AF callbacks; the final
ledger has ten, while generated AND at CCA4 stores AF0 without a callback.
check-r2 corrected that count but used ECX instead of EBX's Cpu32 position in
the nonvolatile return check. check-r3 corrects the register position and
checks the exact ten-site intrinsic ledger. These were checker-only repairs;
the native workers and captures were never rerun or modified.

This proof covers the declared mode1 malloc/client/free/free(NULL) batch and
its tested refusal paths. It does not prove general allocation, mode2,
original CRT attach, startup-table roots, full CRT completion or whole M4.
Native execution plus direct emission took 4.15 seconds across both levels;
the independent coordinator including strict reads took 8.77 seconds. These
are this workload's measurements, not a general speedup claim.
