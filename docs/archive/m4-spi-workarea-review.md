# Windows work-area service independent review

The [independent review](../../reports/m4-spi-workarea/independent-review-r1/report.json)
accepts the bounded 22-instruction game caller and typed native
`SystemParametersInfoA(SPI_GETWORKAREA)` service experiment. Its independent
source model checks 144 original records and 288 native O0/O2 records, all three
mapped pages, complete 3,504-byte native State and 9,792 ordered native events.
Actual x86 provider stack observations prove the callee's 16-byte argument
cleanup separately from the authored guest-stack projection.

The service uses a host-owned RECT and checked copies into guest memory. It
never passes a guest pointer to the Windows API. The actual work-area result
matches across these original/native recordings. Original volatile CPU/SIMD
observations and the native representative policy are checked separately;
the source caller does not consume those service outputs.

The independent observer rejects 126 corruptions and permits ten coherent
changes to unconsumed or discarded service outputs. A separate compiled harness
passes 68 checks across 29 scenarios at each optimization level, covering signed
RECT values, unusual nonzero BOOL, authored false replies, fault retention,
ownership and cleanup. These fixtures establish no actual Windows false-return
capture. Corrected pre-entry guard failures can subsequently execute; failures
after entry retain a poisoned context and reject reuse.

All 1,249 author bindings, seven historical literal source replacements and
recorded map associations are checked physically. Six actual COFF objects are
freshly decoded, and all 1,312 independent
[bindings](../../reports/m4-spi-workarea/independent-review-r1/pins.json) were rehashed
at root acceptance. Initial reviewer failures and their literal sources remain
preserved.

The caller is a bounded handwritten native translation. This experiment adds
no Remill lift or connected initializer-table execution. The named API,
post-load USER32 disk identity and compiled call provide bounded provenance;
the actual export target pointer was not serialized separately. It assumes
one worker thread and stable owned memory. Full startup integration, generic
concurrency, native window/menu behavior and M4 acceptance remain open.
