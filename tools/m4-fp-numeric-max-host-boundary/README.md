# Numeric-max outer numerical boundary

This derivative keeps the exact game/provider lifted IR, narrow guest domain,
shared r9 runtime and all earlier reports unchanged. The r5 host buffers prove
explicit harness cleanup only. Its direct independent success/FSTP-fault probe
demonstrated a numerical host state leak; the frozen r5 candidate therefore
does not establish Session-owned host restoration.

The new required `Session::invoke(target, return_pc, acquire_borrow)` API owns
the numerical host boundary around the entire checked Runtime invocation.
It catches internal C++ exceptions before restoring caller x87 raw80 values,
CW/status/TOP/tags, the separate legacy ENV and MXCSR. It returns a boolean
completion status after restoration and performs no external rethrow. The
first guest access error and poisoned Runtime remain available for inspection.
Ordinary raw `Runtime::call_direct` calls bypass this boundary. Constructors,
standalone borrower acquisition and external exceptions have no preservation
claim. A full native startup host will need an outer boundary of the same kind.

Every positive/replay and existing actual entered fault/retry test uses this
API. Its observer seeds two occupied caller values with PE/C1 and nonzero
legacy metadata, captures BEFORE and AFTER directly, then performs harness
cleanup in a later destructor. Volatile SIMD registers and reserved FX storage
remain raw observations, outside the numerical preservation claim.

The admitted guest corpus is still the standalone measured twelve masked CWs,
TOP0/7, depth0/1/7 and sticky0/DE/DE+PE domain. No carried C1/PE expansion,
connected27 sequence, original-process execution or full M4 credit is included.

Fresh replay (bundled PowerShell7):

```
pwsh -NoProfile -ExecutionPolicy Bypass -File tools/m4-fp-numeric-max-host-boundary/build.ps1 -OutputDirectory D:/Projects/MW34Recomp/reports/m4-fp-numeric-max-host-boundary/native-build-new
python tools/m4-fp-numeric-max-host-boundary/observe.py reports/m4-fp-numeric-max-host-boundary/native-build-new reports/m4-fp-numeric-max-host-boundary/comparison-new
```

The recipe rejects any existing report or derived O0/O2 build directory before
mutation. Sequential ordinary private directories and stable owned byte
containers are required; concurrent publication and reparse paths are excluded.
All earlier draft derivations/build failures and their exact literal versions
are retained. The final author seal and separate peer review are required before
using this as an accepted integration boundary.
