# Guest x87 control-word measurements

The authored hardware probe loaded every exact 16-bit FLDCW input word twice,
capturing 131,072 actual records with zero hardware faults. On this host in the
measured empty-tag, zero-exception state, the resulting CW was:

```text
actual CW = (requested word & 0x1F3F) | 0x0040
```

Bit 6 became one; bit 7 and bits 13–15 became zero. The hardware preserved the
precision, rounding, exception-mask and infinity-control bits. This is a
measured transfer contract, including reserved precision-bit transfers. It does
not establish arithmetic with reserved precision or unmasked pending
exceptions. The [raw analysis](../reports/m4-crt-cw/analysis-r1/report.json)
derives each bit's classification from every actual input/result pair and
checks the formula against all pairs. No input word was sanitized, retried or
replaced before the hardware observation.

The original worker executes authored FLDCW/FNSTCW/FXSAVE/FNSTENV instructions
on its own host stack. It executes no vendor DLL or game instructions. The
initial guest state has CW `0x037F`, TOP0, empty physical tags, zero exception
status, nonzero raw 80-bit/XMM bytes and deliberately nonzero legacy metadata.
Each 2,176-byte record contains the exact requested/observed CW, hardware-fault
status, and full actual guest/host FX512 and legacy ENV28 before/after captures.
FNSTCW, FXSAVE and FNSTENV agree on the resulting CW in every record.

All captured non-CW guest FP/legacy bytes persist. All actual host FX and legacy
captures match after restoration. All 65,536 guest repetitions match exactly.
Five actual worker admission controls and 62 observer corruptions pass. The
worker uses the frozen owned `CREATE_NEW` staging helper and publication without
replacement. The new source, compiler, AMD64 MSBuild invocation and compiled
artifact map are separate from all prior frozen CRT/runtime gates.

These results support a future normal ABI guest-CW bridge that writes exactly
two guest bytes for FNSTCW and applies the measured policy to a FLDCW load. The
bridge must preserve guest PC rather than forcing single precision, use guest
RC rather than host rounding, retain separate legacy metadata and leave other
state untouched. It still needs authored native tests, independent review and
actual `_controlfp`/`_control87` provider comparison. Runtime r9 and the pinned
Remill semantics are unchanged. Full CRT/SEH/startup/menu completion remains
open.

```powershell
pwsh.exe -NoProfile -ExecutionPolicy Bypass -File tools/m4-crt-cw/build_probe.ps1 -OutputDirectory reports/m4-crt-cw/fresh-build
C:/Python314/python.exe tools/m4-crt-cw/run_probe.py --build reports/m4-crt-cw/fresh-build/build.json --out reports/m4-crt-cw/fresh-run
C:/Python314/python.exe tools/m4-crt-cw/analyze.py --run reports/m4-crt-cw/fresh-run/report.json --out reports/m4-crt-cw/fresh-analysis
```

The measured machine information is collected after the run and is labeled as
such. This single-host result is not a universal CPU, full instruction-set or
production publication claim.
