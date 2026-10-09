# Four cosine startup initializers

The complete roots at `0x4CE5A0`, `0x4CE5C0`, `0x4CE5E0` and `0x4CE600`
now compile to native x64 objects. Each loads its original binary64 constant,
computes cosine, stores binary32 and returns. The original instructions remain
private user data. The native program executes statically compiled LLVM code
and an authored FCOS primitive through owned ten-byte pointer arguments.

The [directed measurements](../reports/m4-fp-transcendental/directed-repaired-comparison-r1/report.json)
match 6,144 actual original records and 12,288 native O0/O2 comparisons. The
[complete State check](../reports/m4-fp-transcendental/repaired-full-comparison-r1/report.json)
also matches every seeded/returned 3,504-byte native State, all nine observed
pages, actual native access events and 3,072 original guest repeat pairs.
Default-input measurements add 192 original records and 384 comparisons.
The corpus contains 32 authored binary64 inputs, twelve masked CW settings,
empty x87 tags, TOP 0/7 and two repeats, including denormals, signed zero,
NaNs, infinities and inputs around the FCOS range boundary.

The baseline had 48 default-input status differences and 2,112 directed
status differences per optimization level. Directed differences were 768 DE,
576 C1, 672 C2 and 96 combined C1/C2 records. Numerical values, CPU, memory,
raw80 payloads and pointers matched throughout. The exact measured repair
preserves prior DE at two overwrites, captures actual C1 after the final
binary32 store and captures actual FCOS C2 before its raw80 transport store.
Numerical LLVM operations remain unchanged. Failing captures and literal
sources remain available beside the repaired captures.

Native State's FX/legacy projections and the original hardware FXSAVE/
FNSTENV observations retain separate provenance. Original State and access
events were not captured. Dead raw80 payloads and final C0/C2/C3 values have
observation credit only. Final-store C1 architectural credit needs a
conservative per-record argument; cosine's own precision flag cannot by
itself prove a later store was inexact.

Thirty-two cause-specific saved-record controls, fifteen actual worker
identity/output-preservation denials and 32 actual compiled context controls
at each optimization level pass. The earlier observer used wrong bit masks
for three named flag checks; its run/source is retained and those named
checks receive no specific-flag credit. The corrected run records each mask.
A sandbox fixed-address collision during an original denial check is also
retained; that check subsequently passed in an isolated normal Windows
worker before any additional original game body executed.

Independent review remains open. These standalone experiments do not
register FP callbacks in the shared Runtime, execute connected initializer
order, support occupied stacks/unmasked traps, establish another machine's
undefined status observations or complete native menus.

With the admitted private input evidence and pinned toolchain present, replay
the repaired native observations into fresh report/build directories:

```powershell
pwsh -NoProfile -ExecutionPolicy Bypass -File tools/m4-fp-cosine-repair/build_repair.ps1 -OutputDirectory D:/Projects/MW34Recomp/reports/m4-fp-transcendental/FRESHLEAF
```

The adapter, hardware capture, comparison and controls have separate recipes
under `tools/m4-fp-transcendental`, `tools/m4-fp-cosine-repair` and
`tests/m4-fp-transcendental`. The ordinary game was not launched for this gate.
