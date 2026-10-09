# Independent selected54 provider validation

`observe_connected.py` is an exact derivative of the frozen persistent game
source computation with observation hooks. `source-observation-diff.patch`
records every change. It starts from one genuine registry bootstrap BEFORE per
case, derives source effects, and admits only finite typed API scalar and owned
byte witnesses. It never reseeds from a selected phase or provider AFTER.

The observer checks every captured provider checkpoint after the initial BEFORE:
all 3504 State bytes, 512 Runtime FX bytes, 40 projected CPU bytes, and each entire
captured page or allocation backing. Selected root, replay and API checkpoints
also check the paused Runtime CPU. Source memory, API transport, and owner
research ledgers are checked in order. Allocation, alias and native CS owners are
checked through producer, all 26 registrations, genuine growth and cleanup.

Two explicit source/harness conventions are represented: the sentinel fragment
stops at 5AC3EC, publishing that scheduler PC after its last instruction at
5AC3E2; selected dispatcher return-word stores occur while the provider is
paused, so remain outside its research ledger. Neither convention comes from a
captured AFTER value.

Growth termination is derived from the carried source vector and actual
HeapSize responses. Seven genuine initializer replays append the 33rd callback,
executing real HeapReAlloc from a measured 128-byte capacity to 144 requested
bytes. Growth replays are separate from selected initializer credit. Cleanup
executes original source free, deletes the four native critical sections in
reverse ownership order, and destroys the same private heap HANDLE.

The worker retains a physically verified pre-call HeapDestroy identity and its
actual success/HANDLE lifecycle, but its post-destroy identity record is zero.
This validation expressly leaves worker post-destroy identity stability
unobserved. The separate compiled control receipt must provide the immediate
post-finish physical identity proof for combined admission.

`seal.py` authenticates the completed validation, original/source provenance,
compiled native body and exact successful metrics into a fresh bounded receipt.
It does not alter the accepted initializer count or claim full CRT/game launch.
