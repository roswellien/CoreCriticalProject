# Bounded native guest control-word transfers

The new `tools/m4-guest-cw` component implements typed C ABI calls for guest
FNSTCW and FLDCW transfers. It uses the frozen checked `GuestMemory` and pinned
Remill 6, 3,504-byte `State` layout. It does not change the accepted runtime r9,
the old Remill semantics, or any earlier gate.

`Context` borrows one stable complete `State`, one separate 512-byte FX view,
and an explicitly owned guest operand range. The compiler adapter must pass a
valid, nonnull context whose lifetime covers every call, check its retained
`fault()` after every helper, and propagate any required fault. A null context
returns null; that return is not successful execution. This prerequisite has
no runtime poisoning or automatic Remill instruction-lowering claim.

Admission requires matching, already normalized State/FX CW, SW zero in both
representations, TOP zero, empty physical tags, guest MXCSR 1F80, and zero
defined Remill status-shadow fields. Pending exceptions, occupied stacks,
other TOP values, mismatched views, and unreadable/unwritable or out-of-owned
operands are denied. A denial persists in the context, with its first operand
address; retry cannot turn it into success. Denial does not reset an
unsupported state into an accepted one.

FNSTCW writes exactly two checked guest bytes from guest State CW. FLDCW first
reads both checked guest bytes, then applies the normalization measured on the
actual hardware corpus: `(requested & 0x1F3F) | 0x0040`. It changes only the CW
in State and the separate FX view. Full State storage, raw 80-bit slots, XMM,
segments, registers, status and legacy IP/CS/DP/DS/FOP metadata are retained.
Nonzero legacy metadata in State is deliberately distinct from the observed
zero FX metadata; copying FX metadata over legacy State is not permitted.

The actual hardware evidence is
`reports/m4-crt-cw/closure-r1/report.json`. Its 131,072 records contain every
16-bit request twice, in empty TOP0/SW0 state. `reports/m4-guest-cw/build-r1`
separately compiles O0 and O2 helper implementations and passes 28 authored
controls each. `run-r1` records 65,536 native calls per optimization, with
actual complete State, separate FX, legacy ENV and eight guest bytes before
and after. Workers consume only hardware before-state/input tags. The raw
comparator reads actual hardware after-state, accepts 131,072 differential
records with zero differences, and rejects 114 observer corruptions in
`comparison-r2`. Fourteen actual worker controls check intended diagnostics,
hashes, missing/changed input, and preservation of existing outputs. These
tests execute authored native helpers; no game/provider body is executed.

The first comparator attempt is preserved in `comparison-r1`: its independent
State reconstruction placed SS at the ES offset and failed before credit.
Correcting that observer offset left the compiled helpers and all actual
original/native streams unchanged.

Reproduction requires fresh private report and derived-build directories:

```powershell
pwsh.exe -NoProfile -File tools/m4-guest-cw/build_probe.ps1 -OutputDirectory D:/Projects/MW34Recomp/reports/m4-guest-cw/build-new
C:/Python314/python.exe tools/m4-guest-cw/run_replay.py reports/m4-guest-cw/build-new/build.json reports/m4-guest-cw/run-new
C:/Python314/python.exe tools/m4-guest-cw/compare.py reports/m4-guest-cw/run-new/report.json reports/m4-guest-cw/comparison-new
```

This is an empty-state transfer prerequisite on the measured host. It is not
active numerical execution, universal CPU behavior, CRT `_controlfp` or
`_control87` equivalence, or full startup/menu acceptance. Numerical execution
still requires actual host-CW synchronization and exact host restoration,
supported precision/rounding/exception contracts, and an original/native
complete-provider comparison. Reserved precision arithmetic and pending
exceptions remain unresolved. Production integration must preserve runtime
sources and rebuild all consuming adapters against a fresh admitted version.
Execution and publication here use sequential workers and fresh ordinary
private directories; concurrent writers and reparse/dangling-link paths are
outside this experiment's scope.
