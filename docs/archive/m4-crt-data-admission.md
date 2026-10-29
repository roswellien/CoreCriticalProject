# CRT command-line observation and reference data admission

The staged provider's process-attach fragment at `0x7800188C` calls the real
`GetCommandLineA` import, returns through `0x78001892`, and stores EAX into
`_acmdln` at `0x78037174`. The isolated original probe executes these eleven
source bytes and an explicitly identified capture jump. Its 192 observations
cover twelve masked control words, all eight TOP values, and two repeats. It
records the actual OS target module, borrowed source pointer, checked readable
allocation, owning byte copy, complete CPU/stack/FX/legacy environment and host
restoration. The command line belongs to this probe process. The complete
process-attach path remains unexecuted.

The [original analysis](../../reports/m4-crt-data/commandline-analysis-r3/report.json)
binds the actual stream and 24 observer controls. The initial observer rejected
region-extent growth caused by probe allocations even though the pointer,
allocation, readable coverage and bytes stayed valid. Both that failure and the
diagnostic are retained. The final observer records actual post-call extents and
requires stable allocation/protection and complete bounded NUL coverage. The
x86 worker's System32 view is explicitly resolved to its measured SysWOW64 file
when the AMD64 analyzer verifies the module identity.

`DataImportRegistry` is a separate **reference projection** fixture. It borrows
the frozen Runtime r9 and admits the unique named MSVCRT `_acmdln` IAT at
`0x5BB518`. It preserves the image's original IAT DWORD. It binds the exact
provider file and writer identity, retains the observed original pointer as
metadata, copies the declared measured bytes into owned guest storage in
`[0x32000000,0x33000000)`, and creates a four-byte provider-global projection.
This authored fixture store does not execute the translated initialization
writer. A reference load of the IAT returns the provider-global guest address;
the subsequent checked DWORD load yields the explicitly projected buffer
address. Original and native process pointers need not be equal.

The zero source DWORD establishes file identity only. It does not establish
initialized `_acmdln` or `_adjust_fdiv` values. `_adjust_fdiv`, unknown slots,
unadmitted loads, changed IAT/global/buffer bytes, unreadable mappings, duplicate
admission and ownership collisions fault. The first typed fault is retained;
the registry cannot be reused after it. Partial admission never becomes ready.
The registry releases only mappings it acquired and preserves preexisting
ordinary mappings. Its Runtime borrower must outlive it; trusted callers must
not replace the owned mappings. General concurrent access, adversarial host
unmap/remap, arbitrary swallowed raw GuestMemory exceptions and general Runtime
data-import routing are outside this bounded API.

The public authored controls use fixtures to exercise these ownership and
denial paths, plus one admitted actual game-image association. That association
uses the frozen original raw stream as an explicitly declared reference input.
It is not original execution performed by the data registry and is not native
implementation of the Windows command-line service. Records always declare
`reference_projection_only=true` and `production_initialized_service=false`.

A production initialized data service still needs its own host command-line
input or declared logical user arguments, owning guest buffer creation, actual
translated writer execution, measured callback and data-IAT integration, and
the required process-attach dependencies. Full CRT startup, SEH, the complete
initializer ledger and a native menu remain open M4 requirements.
