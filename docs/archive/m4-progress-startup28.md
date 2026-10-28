# Current M4 progress: 28 connected initializers

Updated 2026-10-09. This supplements the frozen [27-root evidence](../../reports/m4-joint-startup27/root-acceptance-r1/report.json) and [locale/argument-builder progress](m4-progress-locale-argv.md).

**Accepted selected initializer coverage has increased from 27/144 to 28/144.** There are 116 inventory roots remaining. This is initializer coverage, not an overall recompilation percentage. M4 remains active: the project-built executable does not yet present native menus or load native Training.

The added initializer is `0x482CF0`, original table cell `0x5E0110`. Its three literal source bodies contain 22 instructions and 56 original bytes. They were lowered and compiled into six AMD64 objects across the O0/O2 builds. The initializer copies its original 24-byte object template, calls the actual native `SystemParametersInfoA(SPI_GETWORKAREA)` through a typed private RECT, commits the measured output and returns through its recovered source frame.

The initializer runs at phase 14, between the preceding 14 roots and the following 13, on persistent guest State and memory. The test retains the original relative table order and does not reset state between phases. This remains an explicitly selected research sequence; it does not execute the entire original CRT table or DLL attach schedule.

## Completed validation

- Actual original x86: six connected sequences, 168 initializer calls, 17 observed pages and measured stdcall argument cleanup.
- Native O0/O2: 12 connected sequences, 336 initializer calls. Every completed sequence has 31 actual Runtime CALL records and 29 registered translations.
- Independent comparison: 672 full 3,504-byte State comparisons, 4,764 source-access observations, and the complete new SPI source/API access sequence. The SPI phase has 25 literal source accesses and 17 separately identified API transports.
- Independent compiled controls: 34 scenarios and 68 initial/refused-retry attempts across both builds. They cover source and IAT mutation, DF/segment rejection, protected stack/output memory, bad arguments, forged returns, observer exceptions before/after the actual API and after the root return, and preservation of a committed object-copy prefix after a later write fails.
- Outside-return hardware observations preserve full legacy ENV28, raw80 slots, CW/SW/FTW, MXCSR, native XMM6–15 and caller LastError through success and failure. Volatile native SIMD preservation is not claimed.
- The independent SPI observer rejects 216 targeted capture corruptions. New captures were written directly into strict archives; unchanged historical native suites were reused rather than rerun.

The original API's volatile CPU and legacy metadata outputs remain recorded and carried exactly within the original branch. The native service uses explicit representatives for unconsumed fields. The following 13 selected source graphs contain no consumers of those CPU volatile fields; the next floating-point load replaces the relevant legacy metadata. That finding is confined to this selected suffix. Existing 27-root numerical validation retains its accepted measured hardware-oracle scope.

## Current receipts

The coordinator [acceptance-r2](../../reports/m4-joint-startup28-root/acceptance-r2/report.json) is the current acceptance receipt, SHA256 `3f3f1486b94b28e15eb09572965bdd4e861b0a286375db8fbcaf9b0a4902140a`. It physically rechecked 1,525 dependencies and bound actual stages, direct archives, source objects, comparison and controls.

- [Actual original reference](../../reports/m4-joint-startup28-original/execution-r1/report.json)
- [Actual native execution](../../reports/m4-joint-startup28-root/execution-r1/report.json)
- [Independent source comparison](../../reports/m4-joint-startup28-source-review/observation-r3/report.json)
- [Bounded suffix liveness](../../reports/m4-joint-startup28-source-review/liveness-r2/report.json)
- [Independent compiled controls](../../reports/m4-joint-startup28-root/controls-execution-r3/report.json)

Earlier failed compilation and checker versions remain preserved. The corrections included callback symbol names and writer linkage, and fixes to the independent checker/control expectations. The passing candidate is frozen preparation-r4/build-r3; no candidate source revision was needed after its actual execution.

## Next counted unit

Implement the [26-root callback-registration batch](m4-next-registration-batch.md), using the accepted live heap and critical-section ownership. It requires the real CRT registry producer and typed HeapSize/HeapReAlloc services, including growth and failure ownership. Its 26 roots, literal callbacks and required provider spans have been recovered and physically checked. This preparation adds no execution credit.

If all 26 registrations pass, selected coverage reaches **54/144**. Registered callback termination, original CRT scheduling, environment construction, completion of `__getmainargs`, native window/menu behavior and native Training retain their own downstream requirements.
