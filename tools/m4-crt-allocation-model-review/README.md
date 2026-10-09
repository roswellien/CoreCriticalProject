# Independent functional allocation model review

This fresh namespace reads the frozen allocation recovery/model and the accepted
heap-return source predictor. `predict.py` derives genuine caller cleanup, the
complete mode-1 malloc/free source effects, and the independently decoded
`free(NULL)` normal branch. Research caller frames and the client byte pattern
are explicit external inputs/effects with separate ledgers. Actual finite
HeapCreate/GetVersionExA/HeapAlloc/HeapFree witnesses supply API outcomes; captured
AFTER State, FX, RuntimeCPU or page bytes never supply an expected-machine seed.

The forthcoming observer compares complete 3504-byte State, 512-byte FX,
40-byte RuntimeCPU and all 21 carried pages plus the temporary owned allocation
page at source/API/SEH/export-return checkpoints. It verifies source ledgers,
real CALL/RET frames, actual pointer ownership and same-pointer release, and that
NULL free adds no HeapFree call. Mutable guest stack aliases are derived from
committed source/external writes; historical version-query scratch witnesses
remain immutable evidence of that earlier API invocation.

No native worker or Windows API is executed by this observer. Normal source
SEH registration/removal does not prove handler dispatch or exceptional unwind.
The declared lower stack and allocation page padding are research inputs, with
no original stack-growth or original API-internals equivalence claim. Directed
terminal failures carry their actual partial source state and keep diagnostic
cleanup calls separate from authentic source API calls.
